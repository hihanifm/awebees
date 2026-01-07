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
  folder?: string; // Folder name where insight is located (undefined for root-level)
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
  execution_time: number; // Execution time in seconds
}

export interface AnalysisResponse {
  results: AnalysisResultItem[];
  total_time: number; // Total execution time in seconds
  insights_count: number; // Number of insights executed
}

export type ProgressEventType =
  | "file_verification"
  | "insight_start"
  | "file_open"
  | "file_chunk"
  | "insight_progress"
  | "insight_complete"
  | "analysis_complete"
  | "cancelled"
  | "error"
  | "result";

export interface ProgressEvent {
  type: string;
  message: string;
  task_id: string;
  insight_id?: string;
  file_path?: string;
  file_index?: number;
  total_files?: number;
  chunk_info?: string;
  lines_processed?: number; // Number of lines processed so far
  file_size_mb?: number; // File size in MB
  timestamp: string;
  data?: any; // For result event
}

export interface ErrorEvent {
  type: string; // duplicate_id, import_failure, instantiation_failure
  message: string;
  severity: string; // warning, error, critical
  details?: string; // Additional error details
  folder?: string; // Folder where error occurred
  file?: string; // File where error occurred
  insight_id?: string; // Insight ID if applicable
  timestamp: string; // ISO format string
}

