"""API routes for analysis execution."""

from typing import List, AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
import time
import json
import asyncio
from datetime import datetime

from app.core.plugin_manager import get_plugin_manager
from app.core.models import InsightResult, ProgressEvent
from app.core.task_manager import get_task_manager
from app.services.file_handler import CancelledError

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


def _format_sse_event(data: dict) -> str:
    """Format data as SSE event."""
    # Convert datetime objects to ISO format strings for JSON serialization
    def json_serial(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    json_data = json.dumps(data, default=json_serial)
    return f"data: {json_data}\n\n"


async def _run_analysis_with_progress(
    task_id: str,
    request: AnalysisRequest,
    progress_queue: asyncio.Queue
) -> AnalysisResponse:
    """Run analysis and emit progress events."""
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    
    plugin_manager = get_plugin_manager()
    results = []
    
    try:
        # Emit file verification event
        await progress_queue.put(ProgressEvent(
            type="file_verification",
            message=f"Verifying {len(request.file_paths)} file(s)...",
            task_id=task_id,
            total_files=len(request.file_paths)
        ))
        
        # Run insights
        for insight_idx, insight_id in enumerate(request.insight_ids, 1):
            # Check for cancellation
            if task.cancellation_event.is_set():
                await progress_queue.put(ProgressEvent(
                    type="cancelled",
                    message="Analysis cancelled",
                    task_id=task_id
                ))
                task_manager.update_task_status(task_id, "cancelled")
                raise CancelledError("Analysis cancelled")
            
            insight = plugin_manager.get_insight(insight_id)
            if not insight:
                await progress_queue.put(ProgressEvent(
                    type="error",
                    message=f"Insight '{insight_id}' not found",
                    task_id=task_id,
                    insight_id=insight_id
                ))
                continue
            
            # Emit insight start event
            await progress_queue.put(ProgressEvent(
                type="insight_start",
                message=f"Running {insight.name}...",
                task_id=task_id,
                insight_id=insight_id
            ))
            
            # Create progress callback function for this insight
            async def progress_callback(event: ProgressEvent) -> None:
                event.insight_id = insight_id  # Ensure insight_id is set
                event.task_id = task_id  # Ensure task_id is set
                await progress_queue.put(event)
            
            try:
                result = await insight.analyze(
                    request.file_paths,
                    cancellation_event=task.cancellation_event,
                    progress_callback=progress_callback
                )
                results.append(AnalysisResultItem(
                    insight_id=insight_id,
                    result=result
                ))
                
                # Emit insight complete event
                await progress_queue.put(ProgressEvent(
                    type="insight_complete",
                    message=f"{insight.name} completed",
                    task_id=task_id,
                    insight_id=insight_id
                ))
            except CancelledError:
                await progress_queue.put(ProgressEvent(
                    type="cancelled",
                    message="Analysis cancelled",
                    task_id=task_id,
                    insight_id=insight_id
                ))
                task_manager.update_task_status(task_id, "cancelled")
                raise
            except Exception as e:
                logger.error(f"Error executing insight '{insight_id}': {e}", exc_info=True)
                await progress_queue.put(ProgressEvent(
                    type="error",
                    message=f"Error: {str(e)}",
                    task_id=task_id,
                    insight_id=insight_id
                ))
        
        # Emit analysis complete event
        await progress_queue.put(ProgressEvent(
            type="analysis_complete",
            message="Analysis complete",
            task_id=task_id
        ))
        task_manager.update_task_status(task_id, "completed")
        
        return AnalysisResponse(results=results)
        
    except CancelledError:
        task_manager.update_task_status(task_id, "cancelled")
        raise
    except Exception as e:
        task_manager.update_task_status(task_id, "error")
        await progress_queue.put(ProgressEvent(
            type="error",
            message=f"Analysis failed: {str(e)}",
            task_id=task_id
        ))
        raise


async def _stream_analysis_events(
    task_id: str,
    request: AnalysisRequest,
    progress_queue: asyncio.Queue
) -> AsyncGenerator[str, None]:
    """Stream analysis progress events as SSE."""
    try:
        # Emit immediate event to signal analysis has started
        yield _format_sse_event(ProgressEvent(
            type="analysis_started",
            message=f"Starting analysis of {len(request.file_paths)} file(s) with {len(request.insight_ids)} insight(s)...",
            task_id=task_id,
            total_files=len(request.file_paths)
        ).model_dump())
        # Yield control to event loop to ensure immediate flushing
        await asyncio.sleep(0)
        
        # Start analysis in background
        analysis_task = asyncio.create_task(
            _run_analysis_with_progress(task_id, request, progress_queue)
        )
        
        # Stream events until analysis completes
        final_result = None
        while True:
            try:
                # Wait for event with timeout to check if analysis is done
                event = await asyncio.wait_for(progress_queue.get(), timeout=0.1)
                yield _format_sse_event(event.model_dump())
                # Yield control to event loop to ensure immediate flushing of SSE event
                await asyncio.sleep(0)
                
                # Check if this is a terminal event
                if event.type in ("analysis_complete", "cancelled", "error"):
                    if analysis_task.done():
                        try:
                            final_result = await analysis_task
                        except CancelledError:
                            pass
                        except Exception as e:
                            logger.error(f"Analysis task error: {e}", exc_info=True)
                    break
                    
            except asyncio.TimeoutError:
                # Check if analysis is done
                if analysis_task.done():
                    try:
                        final_result = await analysis_task
                        break
                    except CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"Analysis task error: {e}", exc_info=True)
                        break
                continue
        
        # Send final result if available
        if final_result:
            yield _format_sse_event({
                "type": "result",
                "task_id": task_id,
                "data": final_result.model_dump()
            })
            await asyncio.sleep(0)  # Yield control to ensure final event is flushed
        
    except Exception as e:
        logger.error(f"Error in event stream: {e}", exc_info=True)
        yield _format_sse_event({
            "type": "error",
            "task_id": task_id,
            "message": f"Stream error: {str(e)}"
        })


@router.post("/stream")
async def analyze_stream(request: AnalysisRequest):
    """
    Execute analysis with real-time progress updates via Server-Sent Events.
    
    Returns an SSE stream with progress events and final results.
    """
    task_manager = get_task_manager()
    task_id = task_manager.create_task()
    
    progress_queue: asyncio.Queue = asyncio.Queue()
    
    logger.info(f"Analyze Stream API: Starting analysis task {task_id} - {len(request.insight_ids)} insight(s), {len(request.file_paths)} file(s)")
    
    return StreamingResponse(
        _stream_analysis_events(task_id, request, progress_queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        }
    )


@router.post("/{task_id}/cancel")
async def cancel_analysis(task_id: str):
    """
    Cancel an active analysis task.
    
    Args:
        task_id: Task ID to cancel
    """
    task_manager = get_task_manager()
    success = task_manager.cancel_task(task_id)
    
    if success:
        logger.info(f"Cancel API: Task {task_id} cancelled")
        return {"status": "cancelled", "task_id": task_id}
    else:
        logger.warning(f"Cancel API: Task {task_id} not found")
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


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
            result = await insight.analyze(request.file_paths, cancellation_event=None)
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
