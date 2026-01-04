"""Pydantic models for insight results and API requests/responses."""

from typing import Literal, Dict, Any, Optional
from pydantic import BaseModel


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

