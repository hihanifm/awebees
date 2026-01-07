"""Pydantic models for insight results and API requests/responses."""

from typing import Literal, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class InsightResult(BaseModel):
    """Result from an insight analysis."""
    result_type: Literal["text", "file", "chart_data"]
    content: str  # Text content, file path, or JSON string for charts
    metadata: Optional[Dict[str, Any]] = None
    ai_enabled: bool = False  # Whether AI processing is enabled for this insight
    ai_summary: Optional[str] = None  # AI-generated summary (populated after AI analysis)


class InsightMetadata(BaseModel):
    """Metadata for an insight (returned by GET /api/insights)."""
    id: str
    name: str
    description: str
    folder: Optional[str] = None  # Folder name where insight is located (None for root-level)
    ai_enabled: bool = True  # Whether insight supports AI analysis (default: True)
    ai_auto: bool = False  # Whether to automatically trigger AI after analysis (default: False)
    ai_prompt_type: str = "explain"  # Default AI prompt type: summarize, explain, recommend, custom


class ProgressEvent(BaseModel):
    """Progress event for real-time analysis updates."""
    type: str  # file_verification, insight_start, file_open, file_chunk, insight_progress, insight_complete, analysis_complete, cancelled, error
    message: str
    task_id: str
    insight_id: Optional[str] = None
    file_path: Optional[str] = None
    file_index: Optional[int] = None
    total_files: Optional[int] = None
    chunk_info: Optional[str] = None
    lines_processed: Optional[int] = None  # Number of lines processed so far
    file_size_mb: Optional[float] = None  # File size in MB
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorEvent(BaseModel):
    """Error event for backend errors (discovery, import, instantiation failures)."""
    type: str  # duplicate_id, import_failure, instantiation_failure
    message: str
    severity: str  # warning, error, critical
    details: Optional[str] = None  # Additional error details
    folder: Optional[str] = None  # Folder where error occurred
    file: Optional[str] = None  # File where error occurred
    insight_id: Optional[str] = None  # Insight ID if applicable
    timestamp: datetime = Field(default_factory=datetime.utcnow)

