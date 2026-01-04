"""API routes for analysis execution."""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from app.core.plugin_manager import get_plugin_manager
from app.core.models import InsightResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


class AnalysisRequest(BaseModel):
    """Request to execute analysis."""
    insight_ids: List[str]
    file_paths: List[str]


class AnalysisResultItem(BaseModel):
    """Result item for a single insight."""
    insight_id: str
    result: InsightResult


class AnalysisResponse(BaseModel):
    """Response with analysis results."""
    results: List[AnalysisResultItem]


@router.post("", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """
    Execute selected insights on selected files.
    
    Runs the specified insights on the provided file paths
    and returns the results.
    """
    plugin_manager = get_plugin_manager()
    results = []
    
    for insight_id in request.insight_ids:
        try:
            insight = plugin_manager.get_insight(insight_id)
            result = await insight.analyze(request.file_paths)
            results.append(AnalysisResultItem(
                insight_id=insight_id,
                result=result
            ))
        except KeyError:
            logger.warning(f"Insight not found: {insight_id}")
            raise HTTPException(status_code=404, detail=f"Insight not found: {insight_id}")
        except Exception as e:
            logger.error(f"Error executing insight {insight_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error executing insight {insight_id}: {str(e)}"
            )
    
    return AnalysisResponse(results=results)

