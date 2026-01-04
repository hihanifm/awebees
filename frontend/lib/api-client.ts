/** Typed API client for backend communication. */

import {
  InsightMetadata,
  FileSelectRequest,
  FileSelectResponse,
  InsightsResponse,
  AnalysisRequest,
  AnalysisResponse,
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
   */
  async selectFiles(paths: string[]): Promise<FileSelectResponse> {
    const request: FileSelectRequest = { paths };
    return fetchJSON<FileSelectResponse>("/api/files/select", {
      method: "POST",
      body: JSON.stringify(request),
    });
  },

  /**
   * Execute analysis with selected insights on selected files.
   */
  async analyze(insightIds: string[], filePaths: string[]): Promise<AnalysisResponse> {
    const request: AnalysisRequest = {
      insight_ids: insightIds,
      file_paths: filePaths,
    };
    return fetchJSON<AnalysisResponse>("/api/analyze", {
      method: "POST",
      body: JSON.stringify(request),
    });
  },
};

