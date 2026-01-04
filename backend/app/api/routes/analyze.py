"""API routes for analysis execution."""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import time

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
    start_time = time.time()
    logger.info(f"Analyze API: Received request - {len(request.insight_ids)} insight(s), {len(request.file_paths)} file(s)")
    
    plugin_manager = get_plugin_manager()
    results = []
    
    for insight_idx, insight_id in enumerate(request.insight_ids, 1):
        insight_start_time = time.time()
        logger.info(f"Analyze API: Executing insight {insight_idx}/{len(request.insight_ids)}: '{insight_id}'")
        
        try:
            insight = plugin_manager.get_insight(insight_id)
            if not insight:
                logger.warning(f"Analyze API: Insight '{insight_id}' not found in plugin manager")
                raise HTTPException(status_code=404, detail=f"Insight not found: {insight_id}")
            
            logger.info(f"Analyze API: Executing '{insight.name}' (ID: {insight_id}) on {len(request.file_paths)} file(s)")
            result = await insight.analyze(request.file_paths)
            insight_elapsed = time.time() - insight_start_time
            logger.info(f"Analyze API: Completed '{insight.name}' in {insight_elapsed:.2f}s")
            
            results.append(AnalysisResultItem(
                insight_id=insight_id,
                result=result
            ))
        except HTTPException:
            raise
        except Exception as e:
            insight_elapsed = time.time() - insight_start_time
            logger.error(f"Analyze API: Error executing insight '{insight_id}' after {insight_elapsed:.2f}s: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error executing insight {insight_id}: {str(e)}"
            )
    
    total_elapsed = time.time() - start_time
    logger.info(f"Analyze API: Request complete - {len(results)} result(s) in {total_elapsed:.2f}s")
    return AnalysisResponse(results=results)
