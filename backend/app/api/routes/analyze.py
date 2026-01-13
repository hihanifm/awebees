from typing import List, AsyncGenerator, Optional, Dict, Any
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
    insight_ids: List[str]
    file_paths: List[str]
    custom_params: Optional[Dict[str, Any]] = None


class AnalysisResultItem(BaseModel):
    insight_id: str
    results: List[InsightResult]
    execution_time: float = 0.0


class AnalysisResponse(BaseModel):
    results: List[AnalysisResultItem]
    total_time: float = 0.0
    insights_count: int = 0


def _format_sse_event(data: dict) -> str:
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
    from app.core.task_manager import set_analysis_context
    
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    
    # Store custom_params in task for backup/reference
    if request.custom_params:
        task.custom_params = request.custom_params
    
    # Set analysis context with task_id and custom_params
    set_analysis_context(task_id, request.custom_params)
    
    plugin_manager = get_plugin_manager()
    results = []
    start_time = time.time()
    
    try:
        await progress_queue.put(ProgressEvent(
            type="file_verification",
            message=f"Verifying {len(request.file_paths)} file(s)...",
            task_id=task_id,
            total_files=len(request.file_paths)
        ))
        
        for insight_idx, insight_id in enumerate(request.insight_ids, 1):
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
            
            await progress_queue.put(ProgressEvent(
                type="insight_start",
                message=f"Running {insight.name}...",
                task_id=task_id,
                insight_id=insight_id
            ))
            
            async def progress_callback(event: ProgressEvent) -> None:
                event.insight_id = insight_id
                event.task_id = task_id
                await progress_queue.put(event)
            
            try:
                insight_start_time = time.time()
                path_results = []
                total_elapsed = 0.0
                
                for user_path in request.file_paths:
                    if task.cancellation_event.is_set():
                        await progress_queue.put(ProgressEvent(
                            type="cancelled",
                            message="Analysis cancelled",
                            task_id=task_id
                        ))
                        task_manager.update_task_status(task_id, "cancelled")
                        raise CancelledError("Analysis cancelled")
                    
                    path_start_time = time.time()
                    path_result = await insight.analyze_with_ai(
                        user_path,
                        cancellation_event=task.cancellation_event,
                        progress_callback=progress_callback
                    )
                    path_elapsed = time.time() - path_start_time
                    total_elapsed += path_elapsed
                    
                    path_results.append(path_result)
                    
                    await progress_queue.put(ProgressEvent(
                        type="path_result",
                        message=f"Completed analysis for path: {user_path}",
                        task_id=task_id,
                        insight_id=insight_id,
                        file_path=user_path,
                        data=path_result.model_dump()
                    ))
                
                insight_elapsed = time.time() - insight_start_time
                results.append(AnalysisResultItem(
                    insight_id=insight_id,
                    results=path_results,
                    execution_time=insight_elapsed
                ))
                
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
        
        total_elapsed = time.time() - start_time
        await progress_queue.put(ProgressEvent(
            type="analysis_complete",
            message=f"Analysis complete in {total_elapsed:.2f}s",
            task_id=task_id
        ))
        task_manager.update_task_status(task_id, "completed")
        
        # Clean up temporary directory for extracted zip files
        task_manager.cleanup_task_temp_dir(task_id)
        
        return AnalysisResponse(
            results=results,
            total_time=total_elapsed,
            insights_count=len(request.insight_ids)
        )
        
    except CancelledError:
        task_manager.update_task_status(task_id, "cancelled")
        # Clean up temporary directory on cancellation
        task_manager.cleanup_task_temp_dir(task_id)
        raise
    except Exception as e:
        task_manager.update_task_status(task_id, "error")
        # Clean up temporary directory on error
        task_manager.cleanup_task_temp_dir(task_id)
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
    try:
        yield _format_sse_event(ProgressEvent(
            type="analysis_started",
            message=f"Starting analysis of {len(request.file_paths)} file(s) with {len(request.insight_ids)} insight(s)...",
            task_id=task_id,
            total_files=len(request.file_paths)
        ).model_dump())
        await asyncio.sleep(0)
        
        analysis_task = asyncio.create_task(
            _run_analysis_with_progress(task_id, request, progress_queue)
        )
        
        final_result = None
        while True:
            try:
                event = await asyncio.wait_for(progress_queue.get(), timeout=0.1)
                yield _format_sse_event(event.model_dump())
                await asyncio.sleep(0)
                
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
        
        if final_result:
            yield _format_sse_event({
                "type": "result",
                "task_id": task_id,
                "data": final_result.model_dump()
            })
            await asyncio.sleep(0)
        
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
            
            path_results = []
            total_elapsed = 0.0
            
            for user_path in request.file_paths:
                logger.info(f"Analyze API: Executing '{insight.name}' (ID: {insight_id}) on path: {user_path}")
                path_start_time = time.time()
                path_result = await insight.analyze_with_ai(user_path, cancellation_event=None)
                path_elapsed = time.time() - path_start_time
                total_elapsed += path_elapsed
                path_results.append(path_result)
            
            insight_elapsed = time.time() - insight_start_time
            logger.info(f"Analyze API: Completed '{insight.name}' in {insight_elapsed:.2f}s")
            
            results.append(AnalysisResultItem(
                insight_id=insight_id,
                results=path_results,
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


# AI Analysis Endpoints

class AIAnalyzeRequest(BaseModel):
    content: str
    prompt_type: str = "explain"  # summarize, explain, recommend, custom
    custom_prompt: Optional[str] = None
    variables: Optional[dict] = None


class AIConfigUpdate(BaseModel):
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
    
    # Limit to 150 lines to control API costs and token usage
    MAX_LINES = 150
    lines = request.content.split('\n')
    if len(lines) > MAX_LINES:
        logger.info(f"AI Analyze API: Limiting content from {len(lines)} to {MAX_LINES} lines")
        limited_content = '\n'.join(lines[:MAX_LINES])
        limited_content += f"\n\n[... {len(lines) - MAX_LINES} more lines truncated ...]"
    else:
        limited_content = request.content
    
    async def stream_ai_response() -> AsyncGenerator[str, None]:
        try:
            ai_service = get_ai_service()
            
            yield _format_sse_event({
                "type": "ai_start",
                "message": "AI analysis starting..."
            })
            
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
            
            yield _format_sse_event({
                "type": "ai_complete",
                "message": "AI analysis complete",
                "full_content": "".join(full_response)
            })
            
            logger.info("AI Analyze API: Analysis complete")
        
        except Exception as e:
            logger.error(f"AI Analyze API: Error during analysis: {e}", exc_info=True)
            
            # Format error message to be more user-friendly
            error_message = str(e)
            
            # Remove technical prefixes if present
            if error_message.startswith("AI API error: "):
                error_message = error_message.replace("AI API error: ", "", 1)
            elif error_message.startswith("AI API connection error: "):
                error_message = error_message.replace("AI API connection error: ", "", 1)
            
            # Provide helpful hints for common errors
            if "endpoint" in error_message.lower() or "unexpected" in error_message.lower():
                if "/v1" not in error_message:
                    error_message = (
                        f"{error_message}\n\n"
                        f"💡 Tip: Make sure your AI Base URL includes '/v1' at the end "
                        f"(e.g., https://api.openai.com/v1 or http://localhost:1234/v1)"
                    )
            elif "401" in error_message or "unauthorized" in error_message.lower():
                error_message = (
                    f"{error_message}\n\n"
                    f"💡 Tip: Check that your API key is correct and has the necessary permissions."
                )
            elif "404" in error_message or "not found" in error_message.lower():
                error_message = (
                    f"{error_message}\n\n"
                    f"💡 Tip: Verify that your AI Base URL is correct and the endpoint exists."
                )
            elif "connection" in error_message.lower() or "timeout" in error_message.lower():
                error_message = (
                    f"{error_message}\n\n"
                    f"💡 Tip: Check your network connection and ensure the AI service is accessible."
                )
            
            yield _format_sse_event({
                "type": "ai_error",
                "message": error_message,
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
        config_dict = {k: v for k, v in config.dict().items() if v is not None}
        logger.info(f"AI Config API: Config dict to update: {config_dict}")
        
        AIConfig.update_from_dict(config_dict)
        
        logger.info(f"AI Config API: Updated - enabled={AIConfig.ENABLED}, base_url={AIConfig.BASE_URL}, model={AIConfig.MODEL}, is_configured={AIConfig.is_configured()}")
        
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
    
    if not config.base_url or not config.api_key:
        return {
            "success": False,
            "message": "Base URL and API key are required for testing"
        }
    
    try:
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
    
    if not config.base_url:
        return {"models": []}
    
    try:
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

