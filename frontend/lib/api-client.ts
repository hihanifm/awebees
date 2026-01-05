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

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:34001";

async function fetchJSON<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`, {
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
      fetch(`${API_URL}/api/analyze/stream`, {
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
   * Stream backend errors via Server-Sent Events.
   * @param onError Callback function to receive error events.
   * @returns A Promise that resolves when the stream closes.
   */
  async streamErrors(onError: (event: ErrorEvent) => void): Promise<void> {
    return new Promise((resolve) => {
      // Use EventSource for SSE
      const eventSource = new EventSource(`${API_URL}/api/errors/stream`);
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
};
