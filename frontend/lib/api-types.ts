/** TypeScript types matching backend Pydantic models. */

export type ResultType = "text" | "file" | "chart_data";

export interface InsightResult {
  result_type: ResultType;
  content: string;
  metadata?: Record<string, any>;
}

export interface InsightMetadata {
  id: string;
  name: string;
  description: string;
}

export interface FileSelectRequest {
  paths: string[];
}

export interface FileSelectResponse {
  files: string[];
  count: number;
}

export interface InsightsResponse {
  insights: InsightMetadata[];
}

export interface AnalysisRequest {
  insight_ids: string[];
  file_paths: string[];
}

export interface AnalysisResultItem {
  insight_id: string;
  result: InsightResult;
}

export interface AnalysisResponse {
  results: AnalysisResultItem[];
}

