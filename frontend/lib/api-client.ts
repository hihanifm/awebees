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
   */
  async analyze(
    insightIds: string[],
    filePaths: string[]
  ): Promise<AnalysisResponse> {
    const requestBody: AnalysisRequest = { insight_ids: insightIds, file_paths: filePaths };
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
   * @returns Promise that resolves with the analysis results, or rejects if cancelled/errored.
   */
  async analyzeWithProgress(
    insightIds: string[],
    filePaths: string[],
    onProgress: (event: ProgressEvent) => void
  ): Promise<AnalysisResponse> {
    const requestBody: AnalysisRequest = { insight_ids: insightIds, file_paths: filePaths };

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
                    console.error("Error parsing SSE event:", e);
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
          console.error("Error parsing error event:", e);
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
          let fullResponse = "";

          const readChunk = (): Promise<void> => {
            return reader.read().then(({ done, value }) => {
              if (done) {
                resolve(fullResponse);
                return Promise.resolve();
              }

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\n\n");
              buffer = lines.pop() || "";

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
                      resolve(fullResponse);
                      return Promise.resolve();
                    } else if (data.type === "ai_error") {
                      reject(new Error(data.message));
                      return Promise.resolve();
                    }
                  } catch (e) {
                    console.error("Error parsing AI SSE event:", e);
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
};

// Export individual AI functions for easier imports
export const getAIConfig = apiClient.getAIConfig;
export const updateAIConfig = apiClient.updateAIConfig;
export const testAIConnection = apiClient.testAIConnection;
export const analyzeWithAI = apiClient.analyzeWithAI;

