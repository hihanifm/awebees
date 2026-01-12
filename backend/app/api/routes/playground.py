from typing import List, AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
import time
import asyncio
from pathlib import Path

from app.core.config_insight import ConfigBasedInsight
from app.core.models import ProgressEvent
from app.core.task_manager import get_task_manager
from app.services.file_handler import validate_file_path, CancelledError
from app.api.routes.analyze import (
    AnalysisResponse, 
    AnalysisResultItem,
    _format_sse_event
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/playground", tags=["playground"])


class PlaygroundExecuteRequest(BaseModel):
    file_paths: List[str]  # Support multiple paths like analyze endpoint
    ripgrep_command: str  # Complete ripgrep command (e.g., "ERROR" or "-i -A 2 ERROR")


async def _run_playground_analysis(
    task_id: str,
    request: PlaygroundExecuteRequest,
    progress_queue: asyncio.Queue
) -> AnalysisResponse:
    """Run playground analysis with progress updates."""
    from app.core.task_manager import set_analysis_context
    
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    
    # Set analysis context with task_id (no custom_params for playground)
    set_analysis_context(task_id, None)
    
    # Build temporary insight config
    insight_config = {
        "metadata": {
            "name": "Playground Filter",
            "description": "Temporary playground filter"
        },
        "file_filters": [
            {
                "file_patterns": [],  # Empty = all files (no file filtering)
                "line_filters": [
                    {
                        "ripgrep_command": request.ripgrep_command,
                        "reading_mode": "ripgrep"  # Only ripgrep mode
                    }
                ]
            }
        ]
    }
    
    # Create temporary ConfigBasedInsight
    insight = ConfigBasedInsight(config=insight_config, module_name="playground")
    
    # Temporary insight ID
    temp_insight_id = "playground_temp"
    
    results = []
    start_time = time.time()
    
    try:
        await progress_queue.put(ProgressEvent(
            type="file_verification",
            message=f"Verifying {len(request.file_paths)} file(s)...",
            task_id=task_id,
            total_files=len(request.file_paths)
        ))
        
        await progress_queue.put(ProgressEvent(
            type="insight_start",
            message=f"Running Playground Filter...",
            task_id=task_id,
            insight_id=temp_insight_id
        ))
        
        async def progress_callback(event: ProgressEvent) -> None:
            event.insight_id = temp_insight_id
            event.task_id = task_id
            await progress_queue.put(event)
        
        insight_start_time = time.time()
        path_results = []
        
        for user_path in request.file_paths:
            if task.cancellation_event.is_set():
                await progress_queue.put(ProgressEvent(
                    type="cancelled",
                    message="Analysis cancelled",
                    task_id=task_id
                ))
                task_manager.update_task_status(task_id, "cancelled")
                raise CancelledError("Analysis cancelled")
            
            path_result = await insight.analyze_with_ai(
                user_path,
                cancellation_event=task.cancellation_event,
                progress_callback=progress_callback
            )
            path_results.append(path_result)
            
            await progress_queue.put(ProgressEvent(
                type="path_result",
                message=f"Completed analysis for path: {user_path}",
                task_id=task_id,
                insight_id=temp_insight_id,
                file_path=user_path,
                data=path_result.model_dump()
            ))
        
        insight_elapsed = time.time() - insight_start_time
        results.append(AnalysisResultItem(
            insight_id=temp_insight_id,
            results=path_results,
            execution_time=insight_elapsed
        ))
        
        await progress_queue.put(ProgressEvent(
            type="insight_complete",
            message=f"Playground Filter completed in {insight_elapsed:.2f}s",
            task_id=task_id,
            insight_id=temp_insight_id
        ))
        
        total_elapsed = time.time() - start_time
        await progress_queue.put(ProgressEvent(
            type="analysis_complete",
            message=f"Analysis complete in {total_elapsed:.2f}s",
            task_id=task_id
        ))
        task_manager.update_task_status(task_id, "completed")
        task_manager.cleanup_task_temp_dir(task_id)
        
        return AnalysisResponse(
            results=results,
            total_time=total_elapsed,
            insights_count=1
        )
        
    except CancelledError:
        task_manager.update_task_status(task_id, "cancelled")
        task_manager.cleanup_task_temp_dir(task_id)
        raise
    except Exception as e:
        task_manager.update_task_status(task_id, "error")
        task_manager.cleanup_task_temp_dir(task_id)
        await progress_queue.put(ProgressEvent(
            type="error",
            message=f"Analysis failed: {str(e)}",
            task_id=task_id
        ))
        raise


async def _stream_playground_events(
    task_id: str,
    request: PlaygroundExecuteRequest,
    progress_queue: asyncio.Queue
) -> AsyncGenerator[str, None]:
    """Stream playground execution events similar to analyze endpoint."""
    try:
        yield _format_sse_event(ProgressEvent(
            type="analysis_started",
            message=f"Starting playground analysis of {len(request.file_paths)} file(s)...",
            task_id=task_id,
            total_files=len(request.file_paths)
        ).model_dump())
        await asyncio.sleep(0)
        
        analysis_task = asyncio.create_task(
            _run_playground_analysis(task_id, request, progress_queue)
        )
        
        final_result = None
        task_error = None
        terminal_event_received = False
        
        while True:
            try:
                event = await asyncio.wait_for(progress_queue.get(), timeout=0.1)
                yield _format_sse_event(event.model_dump())
                await asyncio.sleep(0)
                
                if event.type in ("analysis_complete", "cancelled", "error"):
                    terminal_event_received = True
                    # Wait for task to complete if not already done
                    if not analysis_task.done():
                        try:
                            await asyncio.wait_for(analysis_task, timeout=5.0)
                        except asyncio.TimeoutError:
                            logger.warning(f"Playground task {task_id} did not complete within timeout")
                        except Exception:
                            pass  # Task will raise, we'll catch it below
                    
                    if analysis_task.done():
                        try:
                            final_result = await analysis_task
                        except CancelledError:
                            pass
                        except Exception as e:
                            logger.error(f"Playground analysis task error: {e}", exc_info=True)
                            task_error = str(e)
                    break
                    
            except asyncio.TimeoutError:
                if analysis_task.done():
                    try:
                        final_result = await analysis_task
                        break
                    except CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"Playground analysis task error: {e}", exc_info=True)
                        task_error = str(e)
                        break
                continue
        
        # Always send a result event, even on error
        if final_result:
            yield _format_sse_event({
                "type": "result",
                "task_id": task_id,
                "data": final_result.model_dump()
            })
            await asyncio.sleep(0)
        elif task_error:
            # If task failed, send error as result event so frontend can handle it
            yield _format_sse_event({
                "type": "result",
                "task_id": task_id,
                "data": {
                    "results": [],
                    "total_time": 0.0,
                    "insights_count": 0,
                    "error": task_error
                }
            })
            await asyncio.sleep(0)
        elif terminal_event_received:
            # Terminal event received but no result - send empty result
            yield _format_sse_event({
                "type": "result",
                "task_id": task_id,
                "data": {
                    "results": [],
                    "total_time": 0.0,
                    "insights_count": 0
                }
            })
            await asyncio.sleep(0)
            
    except Exception as e:
        logger.error(f"Error in playground event stream: {e}", exc_info=True)
        yield _format_sse_event({
            "type": "error",
            "task_id": task_id,
            "message": f"Stream error: {str(e)}"
        })


@router.post("/execute/stream")
async def execute_playground_stream(request: PlaygroundExecuteRequest):
    """
    Execute playground filter with real-time progress updates via Server-Sent Events.
    
    Creates a temporary insight from ripgrep_command and executes it using the same
    infrastructure as the analyze endpoint. Returns an SSE stream with progress events
    and final results in AnalysisResponse format (same as /api/analyze/stream).
    
    This allows the playground to reuse the same ResultsPanel and ProgressWidget
    components from the main analysis page.
    """
    # Validate file paths
    for file_path in request.file_paths:
        if not validate_file_path(file_path):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid or inaccessible file path: {file_path}"
            )
    
    task_manager = get_task_manager()
    task_id = task_manager.create_task()
    
    progress_queue: asyncio.Queue = asyncio.Queue()
    
    logger.info(f"Playground Execute Stream API: Starting task {task_id} - {len(request.file_paths)} file(s), ripgrep_command='{request.ripgrep_command}'")
    
    return StreamingResponse(
        _stream_playground_events(task_id, request, progress_queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/{task_id}/cancel")
async def cancel_playground(task_id: str):
    """
    Cancel an active playground analysis task.
    
    Args:
        task_id: Task ID to cancel
    """
    task_manager = get_task_manager()
    success = task_manager.cancel_task(task_id)
    
    if success:
        logger.info(f"Cancel Playground API: Task {task_id} cancelled")
        return {"status": "cancelled", "task_id": task_id}
    else:
        logger.warning(f"Cancel Playground API: Task {task_id} not found")
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
