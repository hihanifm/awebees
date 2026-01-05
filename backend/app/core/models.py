"""Pydantic models for insight results and API requests/responses."""

from typing import Literal, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class InsightResult(BaseModel):
    """Result from an insight analysis."""
    result_type: Literal["text", "file", "chart_data"]
    content: str  # Text content, file path, or JSON string for charts
    metadata: Optional[Dict[str, Any]] = None


class InsightMetadata(BaseModel):
    """Metadata for an insight (returned by GET /api/insights)."""
    id: str
    name: str
    description: str


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

