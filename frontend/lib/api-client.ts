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
import { loadAllAIConfigs, saveAllAIConfigs, loadAppConfig, saveAppConfig } from "./settings-storage";

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

  return (await response.json()) as T;
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
   * Get list of favorited insight IDs.
   */
  async getFavorites(): Promise<string[]> {
    const response = await fetchJSON<{ favorites: string[] }>("/api/favorites");
    return response.favorites;
  },

  /**
   * Add an insight to favorites.
   * @param insightId The ID of the insight to favorite.
   */
  async addFavorite(insightId: string): Promise<string[]> {
    const response = await fetchJSON<{ favorites: string[] }>(`/api/favorites/${insightId}`, {
      method: "POST",
    });
    return response.favorites;
  },

  /**
   * Remove an insight from favorites.
   * @param insightId The ID of the insight to unfavorite.
   */
  async removeFavorite(insightId: string): Promise<string[]> {
    const response = await fetchJSON<{ favorites: string[] }>(`/api/favorites/${insightId}`, {
      method: "DELETE",
    });
    return response.favorites;
  },

  /**
   * Toggle favorite status for an insight.
   * @param insightId The ID of the insight to toggle.
   * @returns The updated list of favorites and whether the insight is now favorited.
   */
  async toggleFavorite(insightId: string): Promise<{ favorites: string[]; isFavorite: boolean }> {
    // Check current status first
    const statusResponse = await fetchJSON<{ is_favorite: boolean }>(`/api/favorites/${insightId}`);
    const wasFavorite = statusResponse.is_favorite;

    // Toggle the favorite status
    if (wasFavorite) {
      const favorites = await this.removeFavorite(insightId);
      return { favorites, isFavorite: false };
    } else {
      const favorites = await this.addFavorite(insightId);
      return { favorites, isFavorite: true };
    }
  },

  /**
   * Check if an insight is favorited.
   * @param insightId The ID of the insight to check.
   */
  async isFavorite(insightId: string): Promise<boolean> {
    const response = await fetchJSON<{ is_favorite: boolean }>(`/api/favorites/${insightId}`);
    return response.is_favorite;
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

          // Check Content-Type to determine response format
          const contentType = response.headers.get("content-type") || "";
          
          if (contentType.includes("application/json")) {
            // Non-streaming mode: parse JSON response directly
            try {
              const data = await response.json();
              
              if (data.type === "ai_complete" && data.content) {
                // If we have an onChunk callback, call it with the full content
                // (or optionally chunk it for better UX)
                if (onChunk) {
                  // Call onChunk with full content (could also chunk it for progressive display)
                  onChunk(data.content);
                }
                resolve(data.content || data.full_content || "");
              } else if (data.type === "ai_error" || data.error) {
                reject(new Error(data.message || data.detail || "AI analysis failed"));
              } else {
                // Fallback: try to extract content from any field
                resolve(data.content || data.full_content || JSON.stringify(data));
              }
            } catch (e) {
              logger.error("Error parsing JSON response:", e);
              reject(new Error("Failed to parse AI response"));
            }
          } else if (contentType.includes("text/event-stream")) {
            // Streaming mode: handle SSE stream
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
          } else {
            // Unknown content type - try to handle as text
            try {
              const text = await response.text();
              resolve(text);
            } catch (e) {
              logger.error("Error reading response:", e);
              reject(new Error("Failed to read AI response"));
            }
          }
        })
        .catch(reject);
    });
  },

  /**
   * Get AI configuration from backend (active config).
   * Returns the active config from the full configs response.
   */
  async getAIConfig(): Promise<any> {
    const allConfigs = await this.getAllAIConfigs();
    const activeName = allConfigs.active_config_name;
    if (!activeName || !allConfigs.configs || !allConfigs.configs[activeName]) {
      throw new Error("No active config found");
    }
    return allConfigs.configs[activeName];
  },

  /**
   * Get all AI config profiles in the exact file format.
   * API keys are returned as-is (no masking).
   * Automatically uses cache - checks cache first, fetches from API if cache is empty/expired.
   */
  async getAllAIConfigs(): Promise<{ active_config_name: string | null; configs: Record<string, any> }> {
    // Check cache first
    let configs = loadAllAIConfigs();
    
    // If cache miss or expired, fetch from API
    if (!configs) {
      configs = await fetchJSON<{ active_config_name: string | null; configs: Record<string, any> }>("/api/analyze/ai/configs");
      saveAllAIConfigs(configs);
    }
    
    return configs;
  },

  /**
   * Activate an AI config by name.
   */
  async activateAIConfig(name: string): Promise<void> {
    await fetchJSON(`/api/analyze/ai/configs/${name}/activate`, {
      method: "POST",
    });
  },

  /**
   * Create a new AI config.
   */
  async createAIConfig(config: {
    name: string;
    // Note: enabled removed - use global AppConfig.AI_PROCESSING_ENABLED instead
    base_url: string;
    api_key: string;
    model: string;
    max_tokens: number;
    temperature: number;
    timeout: number;
    streaming_enabled: boolean;
  }): Promise<void> {
    await fetchJSON("/api/analyze/ai/configs", {
      method: "POST",
      body: JSON.stringify(config),
    });
  },

  /**
   * Delete an AI config by name.
   */
  async deleteAIConfig(name: string): Promise<void> {
    await fetchJSON(`/api/analyze/ai/configs/${name}`, {
      method: "DELETE",
    });
  },

  /**
   * Update AI configuration (updates specified config or active config if name not provided).
   */
  async updateAIConfig(config: {
    name?: string;
    // Note: enabled removed - use global AppConfig.AI_PROCESSING_ENABLED instead
    base_url?: string;
    api_key?: string;
    model?: string;
    max_tokens?: number;
    temperature?: number;
    timeout?: number;
    streaming_enabled?: boolean;
  }, configName?: string): Promise<void> {
    try {
      // Use provided config name, or get active config name if not provided
      let targetConfigName = configName;
      
      if (!targetConfigName) {
        const activeConfig = await this.getAIConfig();
        targetConfigName = activeConfig?.name;
        
        if (!targetConfigName) {
          throw new Error("No config found. Please specify a config name or ensure there's an active config.");
        }
      }
      
      // Update the specified config (name in config is optional - if not provided, keeps same name)
      await fetchJSON(`/api/analyze/ai/configs/${targetConfigName}`, {
        method: "PUT",
        body: JSON.stringify(config),
      });
    } catch (error: any) {
      // If 404, try to create a default config
      if (error?.status === 404 || error?.message?.includes("404")) {
        throw new Error(`Config '${configName || 'unknown'}' not found. Please create a config first.`);
      }
      throw error;
    }
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
    // Note: enabled removed - use global AppConfig.AI_PROCESSING_ENABLED instead
    base_url: string;
    api_key: string;
    model: string;
    max_tokens?: number;
    temperature?: number;
    streaming_enabled?: boolean;
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
   * Execute playground filter with real-time progress updates via Server-Sent Events.
   * Creates a temporary insight from ripgrep_command and executes it using the same
   * infrastructure as analyze. Returns AnalysisResponse format for reuse of ResultsPanel.
   * @param filePaths List of file paths to analyze
   * @param ripgrepCommand Complete ripgrep command (e.g., "ERROR" or "-i -A 2 ERROR")
   * @param onProgress Callback for progress events
   * @returns Promise that resolves with the analysis results, or rejects if cancelled/errored.
   */
  async executePlayground(
    filePaths: string[],
    ripgrepCommand: string,
    onProgress: (event: ProgressEvent) => void
  ): Promise<AnalysisResponse> {
    const requestBody = { file_paths: filePaths, ripgrep_command: ripgrepCommand };

    return new Promise((resolve, reject) => {
      const streamUrl = API_URL ? `${API_URL}/api/playground/execute/stream` : "/api/playground/execute/stream";
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
                reject(new Error("Playground stream ended unexpectedly"));
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
                    } else if (event.type === "error" && event.message) {
                      // Treat error events as terminal - reject with error message
                      reject(new Error(event.message));
                      return Promise.resolve();
                    }
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
   * Cancel an active playground task.
   * @param taskId Task ID to cancel
   */
  async cancelPlayground(taskId: string): Promise<void> {
    await fetchJSON<{ status: string; task_id: string }>(
      `/api/playground/${taskId}/cancel`,
      {
        method: "POST",
      }
    );
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
   * Get result max lines configuration from backend.
   */
  async getResultMaxLines(): Promise<{ result_max_lines: number }> {
    return fetchJSON("/api/logging/result-max-lines");
  },

  /**
   * Update result max lines configuration in backend (in-memory only).
   * @param value New result max lines value (1-100000)
   */
  async updateResultMaxLines(value: number): Promise<{ result_max_lines: number }> {
    return fetchJSON("/api/logging/result-max-lines", {
      method: "PUT",
      body: JSON.stringify({ result_max_lines: value }),
    });
  },

  /**
   * Get HTTP logging configuration from backend.
   */
  async getHTTPLoggingConfig(): Promise<{ http_logging: boolean }> {
    return fetchJSON("/api/logging/http-logging");
  },

  /**
   * Update HTTP logging configuration in backend.
   * @param enabled Whether to enable HTTP request/response logging
   */
  async updateHTTPLoggingConfig(enabled: boolean): Promise<{ http_logging: boolean }> {
    return fetchJSON("/api/logging/http-logging", {
      method: "PUT",
      body: JSON.stringify({ http_logging: enabled }),
    });
  },

  /**
   * Get AI detailed logging configuration from backend.
   */
  async getAIDetailedLoggingConfig(): Promise<{ detailed_logging: boolean }> {
    return fetchJSON("/api/logging/ai-detailed-logging");
  },

  /**
   * Update AI detailed logging configuration in backend.
   * @param enabled Whether to enable detailed AI interaction logging
   */
  async updateAIDetailedLoggingConfig(enabled: boolean): Promise<{ detailed_logging: boolean }> {
    return fetchJSON("/api/logging/ai-detailed-logging", {
      method: "PUT",
      body: JSON.stringify({ detailed_logging: enabled }),
    });
  },

  /**
   * Get AI processing enabled configuration (global setting).
   */
  async getAIProcessingEnabledConfig(): Promise<{ ai_processing_enabled: boolean }> {
    return fetchJSON("/api/logging/ai-processing-enabled");
  },

  /**
   * Update AI processing enabled configuration (global setting).
   * @param enabled Whether to enable AI processing globally
   */
  async updateAIProcessingEnabledConfig(enabled: boolean): Promise<{ ai_processing_enabled: boolean }> {
    return fetchJSON("/api/logging/ai-processing-enabled", {
      method: "PUT",
      body: JSON.stringify({ ai_processing_enabled: enabled }),
    });
  },

  /**
   * Get app config (log_level, ai_processing_enabled, http_logging, result_max_lines).
   * Automatically uses cache - checks cache first, fetches from API if cache is empty/expired.
   */
  async getAppConfig(): Promise<{ log_level: string; ai_processing_enabled: boolean; http_logging: boolean; result_max_lines: number }> {
    // Check cache first
    let config = loadAppConfig();
    
    // If cache miss or expired, fetch from API
    if (!config) {
      config = await fetchJSON<{ log_level: string; ai_processing_enabled: boolean; http_logging: boolean; result_max_lines: number }>("/api/logging/app-config");
      if (config) {
        saveAppConfig(config);
      }
    }
    
    // If still no config (shouldn't happen, but TypeScript needs this)
    if (!config) {
      throw new Error("Failed to load app config");
    }
    
    return config;
  },

  /**
   * Open a log file in the system default editor.
   * @param logType Type of log file to open ("backend" or "frontend")
   */
  async openLogFile(logType: "backend" | "frontend"): Promise<{ success: boolean; message: string; file_path: string }> {
    return fetchJSON(`/api/logs/open/${logType}`, {
      method: "POST",
    });
  },

  /**
   * Check if ripgrep is available on the backend.
   */
  async checkRipgrepStatus(): Promise<{ available: boolean }> {
    return fetchJSON("/api/ripgrep-status");
  },

  /**
   * Get available models from AI server using hybrid approach.
   * Tries direct connection first, falls back to backend proxy if CORS fails.
   * @param baseUrl AI server base URL
   * @param apiKey API key for authentication
   */
  async getAvailableModels(baseUrl: string, apiKey: string): Promise<{
    models: string[];
    source: 'proxy';
  }> {
    // Use backend proxy only
    const response = await fetchJSON<{ models: string[] }>('/api/analyze/ai/models', {
      method: 'POST',
      body: JSON.stringify({ base_url: baseUrl, api_key: apiKey }),
    });
    
    if (response.models && response.models.length > 0) {
      return { models: response.models, source: 'proxy' };
    }
    
    // Return empty if no models
    return { models: [], source: 'proxy' };
  },

  /**
   * Get current safe mode state.
   */
  async getSafeMode(): Promise<{ enabled: boolean; from_env: boolean }> {
    return fetchJSON("/api/safe-mode");
  },

  /**
   * Start safe mode (requires restart to take effect).
   */
  async startSafeMode(): Promise<{ enabled: boolean; from_env: boolean; message: string }> {
    return fetchJSON("/api/safe-mode/start", {
      method: "POST",
    });
  },

  /**
   * Stop safe mode (requires restart to take effect).
   */
  async stopSafeMode(): Promise<{ enabled: boolean; from_env: boolean; message: string }> {
    return fetchJSON("/api/safe-mode/stop", {
      method: "POST",
    });
  },
};

// Export individual AI functions for easier imports
export const getAIConfig = apiClient.getAIConfig;
export const updateAIConfig = apiClient.updateAIConfig;
export const testAIConnection = apiClient.testAIConnection;
export const analyzeWithAI = apiClient.analyzeWithAI;

