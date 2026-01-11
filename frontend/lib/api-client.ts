/** Typed API client for backend communication. */

import {
      InsightMetadata,
      FileSelectRequest,
      FileSelectResponse,
      InsightsResponse,
      AnalysisRequest,
      AnalysisResponse,
      ProgressEvent,
      ErrorEvent,
    } from "./api-types";
import { logger } from "./logger";

// Use relative path in production (when served from same origin) or configured URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

async function fetchJSON<T>(endpoint: string, options?: RequestInit): Promise<T> {
  // Use relative path if API_URL is empty (production mode, same origin)
  const baseUrl = API_URL || "";
  const url = baseUrl ? `${baseUrl}${endpoint}` : endpoint;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    throw new Error(`API error: ${response.status} ${errorText}`);
  }

  return response.json();
}

export const apiClient = {
  /**
   * Get list of available insights.
   */
  async getInsights(): Promise<InsightMetadata[]> {
    const response = await fetchJSON<InsightsResponse>("/api/insights");
    return response.insights;
  },

  /**
   * Select files and/or folders for analysis.
   * @param paths List of file or folder paths on the server.
   */
  async selectFiles(paths: string[]): Promise<FileSelectResponse> {
    const requestBody: FileSelectRequest = { paths };
    return fetchJSON<FileSelectResponse>("/api/files/select", {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  },

  /**
   * Execute selected insights on the provided files.
   * @param insightIds List of insight IDs to execute.
   * @param filePaths List of absolute file paths on the server.
   * @param customParams Optional custom parameters (key-value pairs).
   */
  async analyze(
    insightIds: string[],
    filePaths: string[],
    customParams?: Record<string, any>
  ): Promise<AnalysisResponse> {
    const requestBody: AnalysisRequest = { 
      insight_ids: insightIds, 
      file_paths: filePaths,
      custom_params: customParams
    };
    return fetchJSON<AnalysisResponse>("/api/analyze", {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  },

  /**
   * Analyze with real-time progress updates via Server-Sent Events.
   * @param insightIds List of insight IDs to execute.
   * @param filePaths List of absolute file paths on the server.
   * @param onProgress Callback for progress events.
   * @param customParams Optional custom parameters (key-value pairs).
   * @returns Promise that resolves with the analysis results, or rejects if cancelled/errored.
   */
  async analyzeWithProgress(
    insightIds: string[],
    filePaths: string[],
    onProgress: (event: ProgressEvent) => void,
    customParams?: Record<string, any>
  ): Promise<AnalysisResponse> {
    const requestBody: AnalysisRequest = { 
      insight_ids: insightIds, 
      file_paths: filePaths,
      custom_params: customParams
    };

    return new Promise((resolve, reject) => {
      // Use fetch with ReadableStream for SSE
      const streamUrl = API_URL ? `${API_URL}/api/analyze/stream` : "/api/analyze/stream";
      fetch(streamUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const reader = response.body?.getReader();
          const decoder = new TextDecoder();

          if (!reader) {
            throw new Error("Response body is not readable");
          }

          let buffer = "";

          const readChunk = (): Promise<void> => {
            return reader.read().then(({ done, value }) => {
              if (done) {
                // Stream ended without result - this shouldn't happen normally
                reject(new Error("Analysis stream ended unexpectedly"));
                return Promise.resolve();
              }

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\n\n");
              buffer = lines.pop() || ""; // Keep incomplete line in buffer

              for (const line of lines) {
                if (line.startsWith("data: ")) {
                  try {
                    const data = JSON.parse(line.slice(6));
                    const event: ProgressEvent = data;
                    onProgress(event);

                    // Handle terminal events
                    if (event.type === "result" && event.data) {
                      resolve(event.data as AnalysisResponse);
                      return Promise.resolve();
                    } else if (event.type === "cancelled") {
                      reject(new Error("Analysis cancelled"));
                      return Promise.resolve();
                    }
                    // Note: error events are non-terminal (insight-level errors don't stop analysis)
                    // analysis_complete events are also non-terminal (wait for result event)
                  } catch (e) {
                    logger.error("Error parsing SSE event:", e);
                  }
                }
              }

              return readChunk();
            });
          };

          return readChunk();
        })
        .catch(reject);
    });
  },

  /**
   * Cancel an active analysis task.
   * @param taskId Task ID to cancel.
   */
  async cancelAnalysis(taskId: string): Promise<void> {
    await fetchJSON<{ status: string; task_id: string }>(
      `/api/analyze/${taskId}/cancel`,
      {
        method: "POST",
      }
    );
  },

  /**
   * Get profiling status from the backend.
   * @returns Promise that resolves with profiling status.
   */
  async getProfilingStatus(): Promise<{ enabled: boolean }> {
    return fetchJSON<{ enabled: boolean }>("/api/profiling");
  },

  /**
   * Stream backend errors via Server-Sent Events.
   * @param onError Callback function to receive error events.
   * @returns A Promise that resolves when the stream closes.
   */
  async streamErrors(onError: (event: ErrorEvent) => void): Promise<void> {
    return new Promise((resolve) => {
      // Use EventSource for SSE
      const errorsUrl = API_URL ? `${API_URL}/api/errors/stream` : "/api/errors/stream";
      const eventSource = new EventSource(errorsUrl);
      let hasReceivedData = false;
      let isResolved = false;

      eventSource.onmessage = (event) => {
        try {
          const data: ErrorEvent = JSON.parse(event.data);
          hasReceivedData = true;
          onError(data);
        } catch (e) {
          logger.error("Error parsing error event:", e);
        }
      };

      eventSource.onerror = () => {
        // EventSource onerror fires on normal closure too, not just actual errors
        // Only log if we haven't received data and connection was refused
        if (!hasReceivedData && eventSource.readyState === EventSource.CLOSED) {
          // This is expected if backend isn't running - silently ignore
        }
        if (!isResolved) {
          eventSource.close();
          resolve(); // Resolve to clean up
          isResolved = true;
        }
      };

      // Close after a short timeout (errors are sent immediately, stream closes after)
      // In a real-time system, you'd keep this open, but for now we close after receiving
      setTimeout(() => {
        if (!isResolved) {
          eventSource.close();
          resolve();
          isResolved = true;
        }
      }, 1000);
    });
  },

  /**
   * Analyze content with AI and stream the response.
   * @param content Content to analyze
   * @param promptType Type of analysis: summarize, explain, recommend, custom
   * @param customPrompt Optional custom prompt (if promptType is "custom")
   * @param variables Optional variables for prompt substitution
   * @param onChunk Callback for AI response chunks
   * @returns Promise that resolves with full AI response
   */
  async analyzeWithAI(
    content: string,
    promptType: string = "explain",
    customPrompt?: string,
    variables?: Record<string, any>,
    onChunk?: (chunk: string) => void
  ): Promise<string> {
    return new Promise((resolve, reject) => {
      const streamUrl = API_URL ? `${API_URL}/api/analyze/ai/analyze` : "/api/analyze/ai/analyze";
      
      fetch(streamUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content,
          prompt_type: promptType,
          custom_prompt: customPrompt,
          variables,
        }),
      })
        .then(async (response) => {
          if (!response.ok) {
            // Try to read error message from response body
            let errorMessage = `HTTP error! status: ${response.status}`;
            try {
              const errorText = await response.text();
              if (errorText) {
                try {
                  const errorJson = JSON.parse(errorText);
                  errorMessage = errorJson.detail || errorJson.message || errorText;
                } catch {
                  errorMessage = errorText;
                }
              }
            } catch (e) {
              // If we can't read the error, use the default message
            }
            throw new Error(errorMessage);
          }

          const reader = response.body?.getReader();
          const decoder = new TextDecoder();

          if (!reader) {
            throw new Error("Response body is not readable");
          }

          let buffer = "";
          let fullResponse = "";
          let receivedComplete = false;

          const readChunk = (): Promise<void> => {
            return reader.read().then(({ done, value }) => {
              if (done) {
                // If stream ends without ai_complete, check if we have content
                if (!receivedComplete && fullResponse.length > 0) {
                  // We have content but no completion event - resolve anyway
                  logger.warn("AI stream ended without completion event, but content was received");
                  resolve(fullResponse);
                } else if (!receivedComplete) {
                  // No content and no completion - this is an error
                  reject(new Error("AI stream ended unexpectedly without completion event"));
                } else {
                  // We already resolved on ai_complete, but stream ended normally
                  resolve(fullResponse);
                }
                return Promise.resolve();
              }

              buffer += decoder.decode(value, { stream: true });
              // Split on double newline (SSE event separator)
              const events = buffer.split("\n\n");
              // Keep the last incomplete event in buffer
              buffer = events.pop() || "";

              for (const eventText of events) {
                if (!eventText.trim()) continue;
                
                // SSE events can have multiple lines, but we only care about "data: " lines
                const lines = eventText.split("\n");
                for (const line of lines) {
                  if (line.startsWith("data: ")) {
                    try {
                      const data = JSON.parse(line.slice(6));
                      
                      if (data.type === "ai_chunk" && data.content) {
                        fullResponse += data.content;
                        if (onChunk) {
                          onChunk(data.content);
                        }
                      } else if (data.type === "ai_complete") {
                        receivedComplete = true;
                        // Use full_content if provided, otherwise use accumulated response
                        const finalResponse = data.full_content || fullResponse;
                        resolve(finalResponse);
                        return Promise.resolve();
                      } else if (data.type === "ai_error") {
                        receivedComplete = true;
                        reject(new Error(data.message || "AI analysis failed"));
                        return Promise.resolve();
                      } else if (data.type === "ai_start") {
                        // Ignore start event, just log it
                        console.debug("AI analysis started");
                      }
                    } catch (e) {
                      logger.error("Error parsing AI SSE event:", e, "Raw line:", line);
                      // Don't reject on parsing errors, just log and continue
                    }
                  }
                }
              }

              return readChunk();
            });
          };

          return readChunk();
        })
        .catch(reject);
    });
  },

  /**
   * Get AI configuration from backend.
   */
  async getAIConfig(): Promise<any> {
    return fetchJSON("/api/analyze/ai/config");
  },

  /**
   * Update AI configuration.
   */
  async updateAIConfig(config: {
    enabled?: boolean;
    base_url?: string;
    api_key?: string;
    model?: string;
    max_tokens?: number;
    temperature?: number;
  }): Promise<void> {
    await fetchJSON("/api/analyze/ai/config", {
      method: "POST",
      body: JSON.stringify(config),
    });
  },

  /**
   * Test AI connection.
   */
  async testAIConnection(): Promise<{ success: boolean; message: string }> {
    return fetchJSON("/api/analyze/ai/test", {
      method: "POST",
    });
  },

  /**
   * Test AI connection with specific config (without saving).
   * @param config Configuration to test with
   */
  async testAIConnectionWithConfig(config: {
    enabled: boolean;
    base_url: string;
    api_key: string;
    model: string;
    max_tokens?: number;
    temperature?: number;
  }): Promise<{ success: boolean; message: string }> {
    return fetchJSON("/api/analyze/ai/test-config", {
      method: "POST",
      body: JSON.stringify(config),
    });
  },

  /**
   * Get all external insight paths.
   */
  async getInsightPaths(): Promise<string[]> {
    const response = await fetchJSON<{ paths: string[] }>("/api/insight-paths/");
    return response.paths;
  },

  /**
   * Add an external insight path.
   * @param path Directory path to add
   */
  async addInsightPath(path: string): Promise<{ status: string; message: string; insights_count: number }> {
    return fetchJSON("/api/insight-paths/add", {
      method: "POST",
      body: JSON.stringify({ path }),
    });
  },

  /**
   * Remove an external insight path.
   * @param path Directory path to remove
   */
  async removeInsightPath(path: string): Promise<{ status: string; message: string; insights_count: number }> {
    return fetchJSON("/api/insight-paths/remove", {
      method: "POST",
      body: JSON.stringify({ path }),
    });
  },

  /**
   * Refresh insights from all paths.
   */
  async refreshInsights(): Promise<{ status: string; insights_count: number; message: string }> {
    return fetchJSON("/api/insight-paths/refresh", {
      method: "POST",
    });
  },

  /**
   * Get source information for all insights.
   */
  async getInsightSources(): Promise<Array<{ insight_id: string; source: string }>> {
    return fetchJSON("/api/insight-paths/sources");
  },

  /**
   * Get the default insights repository path.
   */
  async getDefaultRepository(): Promise<string | null> {
    const response = await fetchJSON<{ default_repository: string | null }>("/api/insight-paths/default");
    return response.default_repository;
  },

  /**
   * Set the default insights repository path.
   * @param path Directory path to set as default repository
   */
  async setDefaultRepository(path: string): Promise<void> {
    await fetchJSON("/api/insight-paths/default", {
      method: "POST",
      body: JSON.stringify({ path }),
    });
  },

  /**
   * Clear the default insights repository from JSON config.
   */
  async clearDefaultRepository(): Promise<void> {
    await fetchJSON("/api/insight-paths/default", {
      method: "DELETE",
    });
  },

  // Playground API methods
  /**
   * Execute ripgrep filter on a file for playground.
   * @param request Filter request with file path and pattern
   */
  async filterFile(request: import("./api-types").PlaygroundFilterRequest): Promise<import("./api-types").FilterResult> {
    return fetchJSON("/api/playground/filter", {
      method: "POST",
      body: JSON.stringify(request),
    });
  },

  /**
   * Get default AI system prompts from backend config.
   */
  async getAISystemPrompts(): Promise<import("./api-types").AISystemPrompts> {
    const config = await this.getAIConfig();
    // System prompts are in backend config
    return {
      summarize: "You are a log analysis assistant. Summarize the following log analysis results concisely.\n\nFocus on:\n- Key findings and patterns\n- Critical issues identified\n- Important statistics\n\nKeep it brief and actionable, using bullet points.",
      explain: "You are a log analysis expert. Analyze the following log data and explain:\n\n- What patterns and trends you observe\n- What these patterns indicate about system behavior\n- Potential root causes of issues\n- Technical insights and correlations\n\nBe thorough but concise. Use technical terminology when appropriate.",
      recommend: "You are a system reliability expert. Based on the following log analysis, provide:\n\n1. **Immediate Actions**: Critical issues requiring immediate attention\n2. **Short-term Fixes**: Problems to address soon\n3. **Long-term Improvements**: Preventive measures and optimizations\n4. **Monitoring Recommendations**: What to watch for\n\nBe specific and practical. Prioritize recommendations by severity."
    };
  },

  /**
   * Get logging configuration from backend.
   */
  async getLoggingConfig(): Promise<{ log_level: string; available_levels: string[] }> {
    return fetchJSON("/api/logging/config");
  },

  /**
   * Update backend logging configuration.
   * @param logLevel New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   */
  async updateLoggingConfig(logLevel: string): Promise<{ log_level: string; available_levels: string[] }> {
    return fetchJSON("/api/logging/config", {
      method: "PUT",
      body: JSON.stringify({ log_level: logLevel }),
    });
  },

  /**
   * Get available models from AI server using hybrid approach.
   * Tries direct connection first, falls back to backend proxy if CORS fails.
   * @param baseUrl AI server base URL
   * @param apiKey API key for authentication
   */
  async getAvailableModels(baseUrl: string, apiKey: string): Promise<{
    models: string[];
    source: 'direct' | 'proxy' | 'defaults';
  }> {
    // Default models as fallback
    const defaultModels = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'];

    // Try direct connection first
    try {
      const modelsUrl = `${baseUrl.replace(/\/$/, '')}/models`;
      const response = await fetch(modelsUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        // OpenAI format: { object: "list", data: [{id: "model-name", ...}] }
        if (data.data && Array.isArray(data.data)) {
          const models = data.data.map((m: any) => m.id);
          if (models.length > 0) {
            return { models, source: 'direct' };
          }
        }
      }
    } catch (corsError) {
      // CORS or network error, try backend proxy
      console.log('Direct connection failed, trying backend proxy:', corsError);
    }

    // Fallback to backend proxy
    try {
      const response = await fetchJSON<{ models: string[] }>('/api/analyze/ai/models', {
        method: 'POST',
        body: JSON.stringify({ base_url: baseUrl, api_key: apiKey }),
      });
      if (response.models && response.models.length > 0) {
        return { models: response.models, source: 'proxy' };
      }
    } catch (proxyError) {
      console.log('Backend proxy also failed, using defaults:', proxyError);
    }

    // Both failed, use defaults
    return { models: defaultModels, source: 'defaults' };
  },
};

// Export individual AI functions for easier imports
export const getAIConfig = apiClient.getAIConfig;
export const updateAIConfig = apiClient.updateAIConfig;
export const testAIConnection = apiClient.testAIConnection;
export const analyzeWithAI = apiClient.analyzeWithAI;

