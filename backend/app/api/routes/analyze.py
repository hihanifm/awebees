"""API routes for analysis execution."""

from typing import List, AsyncGenerator, Optional
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
from app.services.ai_service import get_ai_service
from app.core.config import AIConfig

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
    execution_time: float = 0.0  # Execution time in seconds


class AnalysisResponse(BaseModel):
    """Response with analysis results."""
    results: List[AnalysisResultItem]
    total_time: float = 0.0  # Total execution time in seconds
    insights_count: int = 0  # Number of insights executed


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
    start_time = time.time()
    
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
                insight_start_time = time.time()
                result = await insight.analyze_with_ai(
                    request.file_paths,
                    cancellation_event=task.cancellation_event,
                    progress_callback=progress_callback
                )
                insight_elapsed = time.time() - insight_start_time
                results.append(AnalysisResultItem(
                    insight_id=insight_id,
                    result=result,
                    execution_time=insight_elapsed
                ))
                
                # Emit insight complete event
                await progress_queue.put(ProgressEvent(
                    type="insight_complete",
                    message=f"{insight.name} completed in {insight_elapsed:.2f}s",
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
        total_elapsed = time.time() - start_time
        await progress_queue.put(ProgressEvent(
            type="analysis_complete",
            message=f"Analysis complete in {total_elapsed:.2f}s",
            task_id=task_id
        ))
        task_manager.update_task_status(task_id, "completed")
        
        return AnalysisResponse(
            results=results,
            total_time=total_elapsed,
            insights_count=len(request.insight_ids)
        )
        
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
            result = await insight.analyze_with_ai(request.file_paths, cancellation_event=None)
            insight_elapsed = time.time() - insight_start_time
            logger.info(f"Analyze API: Completed '{insight.name}' in {insight_elapsed:.2f}s")
            
            results.append(AnalysisResultItem(
                insight_id=insight_id,
                result=result,
                execution_time=insight_elapsed
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
    return AnalysisResponse(
        results=results,
        total_time=total_elapsed,
        insights_count=len(request.insight_ids)
    )


# ============================================================================
# AI Analysis Endpoints
# ============================================================================

class AIAnalyzeRequest(BaseModel):
    """Request for AI analysis."""
    content: str
    prompt_type: str = "explain"  # summarize, explain, recommend, custom
    custom_prompt: Optional[str] = None
    variables: Optional[dict] = None


class AIConfigUpdate(BaseModel):
    """Request to update AI configuration."""
    enabled: Optional[bool] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


@router.post("/ai/analyze")
async def ai_analyze_result(request: AIAnalyzeRequest):
    """
    Analyze content with AI and stream the response.
    
    Returns SSE stream of AI analysis.
    """
    logger.info(f"AI Analyze API: Starting analysis (prompt_type: {request.prompt_type})")
    
    if not AIConfig.is_configured():
        raise HTTPException(
            status_code=503,
            detail="AI service is not configured. Please set OPENAI_API_KEY and enable AI_ENABLED=true"
        )
    
    # Limit content to 150 lines to control API costs and token usage
    # Reduced for models with smaller context windows (e.g., phi-4-mini: ~2K-4K tokens)
    MAX_LINES = 150
    lines = request.content.split('\n')
    if len(lines) > MAX_LINES:
        logger.info(f"AI Analyze API: Limiting content from {len(lines)} to {MAX_LINES} lines")
        limited_content = '\n'.join(lines[:MAX_LINES])
        limited_content += f"\n\n[... {len(lines) - MAX_LINES} more lines truncated ...]"
    else:
        limited_content = request.content
    
    async def stream_ai_response() -> AsyncGenerator[str, None]:
        """Generate SSE stream from AI service."""
        try:
            ai_service = get_ai_service()
            
            # Send initial event
            yield _format_sse_event({
                "type": "ai_start",
                "message": "AI analysis starting..."
            })
            
            # Stream AI response
            full_response = []
            async for chunk in ai_service.analyze_stream(
                content=limited_content,
                prompt_type=request.prompt_type,
                custom_prompt=request.custom_prompt,
                variables=request.variables
            ):
                full_response.append(chunk)
                yield _format_sse_event({
                    "type": "ai_chunk",
                    "content": chunk
                })
            
            # Send completion event
            yield _format_sse_event({
                "type": "ai_complete",
                "message": "AI analysis complete",
                "full_content": "".join(full_response)
            })
            
            logger.info("AI Analyze API: Analysis complete")
        
        except Exception as e:
            logger.error(f"AI Analyze API: Error during analysis: {e}", exc_info=True)
            yield _format_sse_event({
                "type": "ai_error",
                "message": str(e),
                "error": True
            })
    
    return StreamingResponse(
        stream_ai_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/ai/config")
async def get_ai_config():
    """
    Get current AI configuration (without sensitive data).
    
    Returns configuration with masked API key.
    """
    logger.info("AI Config API: Fetching configuration")
    return AIConfig.to_dict(include_sensitive=False)


@router.post("/ai/config")
async def update_ai_config(config: AIConfigUpdate):
    """
    Update AI configuration.
    
    Changes are automatically persisted to the .env file and will
    survive application restarts.
    """
    logger.info("AI Config API: Updating configuration")
    logger.debug(f"AI Config API: Received config: {config.dict()}")
    
    try:
        # Convert to dict and filter None values
        config_dict = {k: v for k, v in config.dict().items() if v is not None}
        
        # Update configuration
        AIConfig.update_from_dict(config_dict)
        
        # Log the updated config
        logger.info(f"AI Config API: Updated - base_url={AIConfig.BASE_URL}, model={AIConfig.MODEL}")
        
        # Reset AI service to pick up new config
        from app.services.ai_service import reset_ai_service
        reset_ai_service()
        logger.info("AI Config API: AI service singleton reset")
        
        logger.info("AI Config API: Configuration updated successfully")
        return {"status": "success", "message": "AI configuration updated"}
    
    except Exception as e:
        logger.error(f"AI Config API: Error updating configuration: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error updating AI configuration: {str(e)}"
        )


@router.post("/ai/test")
async def test_ai_connection():
    """
    Test connection to AI service using saved configuration.
    
    Returns success status and message.
    """
    logger.info("AI Test API: Testing connection with saved config")
    logger.debug(f"AI Test API: Current config - base_url={AIConfig.BASE_URL}, api_key={'set' if AIConfig.API_KEY else 'not set'}")
    
    if not AIConfig.is_configured():
        return {
            "success": False,
            "message": "AI service not configured (missing API key or disabled)"
        }
    
    try:
        ai_service = get_ai_service()
        logger.debug(f"AI Test API: Using service with base_url={ai_service.base_url}")
        success, message = await ai_service.test_connection()
        
        logger.info(f"AI Test API: Test {'successful' if success else 'failed'}: {message}")
        return {
            "success": success,
            "message": message
        }
    
    except Exception as e:
        logger.error(f"AI Test API: Error testing connection: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Test failed: {str(e)}"
        }


@router.post("/ai/test-config")
async def test_ai_connection_with_config(config: AIConfigUpdate):
    """
    Test connection to AI service with provided configuration (without saving).
    This allows testing settings before saving them.
    
    Returns success status and message.
    """
    logger.info("AI Test API: Testing connection with provided config")
    logger.debug(f"AI Test API: Test config - base_url={config.base_url}, model={config.model}")
    
    # Validate required fields
    if not config.base_url or not config.api_key:
        return {
            "success": False,
            "message": "Base URL and API key are required for testing"
        }
    
    try:
        # Create a temporary AI service instance with the provided config
        from app.services.ai_service import AIService
        
        test_service = AIService(
            base_url=config.base_url,
            api_key=config.api_key,
            model=config.model or "gpt-4o-mini",
            max_tokens=config.max_tokens or 2000,
            temperature=config.temperature or 0.7,
            timeout=60
        )
        
        logger.debug(f"AI Test API: Created test service with base_url={test_service.base_url}")
        success, message = await test_service.test_connection()
        
        logger.info(f"AI Test API: Test {'successful' if success else 'failed'}: {message}")
        return {
            "success": success,
            "message": message
        }
    
    except Exception as e:
        logger.error(f"AI Test API: Error testing connection with config: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Test failed: {str(e)}"
        }


@router.post("/ai/models")
async def get_available_models(config: AIConfigUpdate):
    """
    Fetch available models from AI server (proxy for CORS).
    Creates a temporary AI service with provided config and fetches models.
    This acts as a proxy when direct frontend connection fails due to CORS.
    
    Returns:
        List of available model IDs
    """
    logger.info("AI Models API: Fetching available models via proxy")
    logger.debug(f"AI Models API: Using base_url={config.base_url}")
    
    # Validate required fields
    if not config.base_url:
        return {"models": []}
    
    try:
        # Create a temporary AI service instance with the provided config
        from app.services.ai_service import AIService
        
        temp_service = AIService(
            base_url=config.base_url,
            api_key=config.api_key or "dummy-key",  # Some servers don't require key for /models
            model=config.model or "gpt-4o-mini",
            max_tokens=config.max_tokens or 2000,
            temperature=config.temperature or 0.7,
            timeout=10
        )
        
        models = await temp_service.get_available_models()
        
        logger.info(f"AI Models API: Found {len(models)} models")
        return {"models": models}
    
    except Exception as e:
        logger.error(f"AI Models API: Error fetching models: {e}", exc_info=True)
        return {"models": []}

