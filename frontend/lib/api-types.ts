/** TypeScript types matching backend Pydantic models. */

export type ResultType = "text" | "file" | "chart_data";

export interface InsightResult {
  result_type: ResultType;
  content: string;
  metadata?: Record<string, any>;
  ai_enabled?: boolean;  // Whether AI processing is enabled for this insight
  ai_auto?: boolean;  // Whether AI was auto-triggered for this result
  ai_prompt_type?: string;  // AI prompt type used
  ai_custom_prompt?: string;  // Custom AI prompt if used
  ai_summary?: string;  // AI-generated summary (populated after AI analysis)
  ai_analysis?: string;  // AI analysis result if auto-triggered
  ai_analysis_error?: string;  // AI analysis error message if auto-trigger failed
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
  invalid_paths?: string[];
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
  results: InsightResult[];  // One InsightResult per user path
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
  | "result"
  | "path_result";

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

// Playground types
export interface PlaygroundFilterRequest {
  file_path: string;
  pattern: string;
  custom_flags?: string;
  case_insensitive?: boolean;
  context_before?: number;
  context_after?: number;
  max_count?: number;
}

export interface FilterResult {
  lines: string[];
  total_count: number;
  truncated: boolean;
  execution_time: number;
  ripgrep_command: string;
}

export interface AISystemPrompts {
  summarize: string;
  explain: string;
  recommend: string;
}

export interface SavedPrompt {
  id: string;
  name: string;
  systemPrompt: string;
  userPrompt: string;
  createdAt: string;
}

