from typing import List, AsyncGenerator, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
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
from app.core.config import AIConfig, AppConfig

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


def _result_for_progress(result: InsightResult) -> Dict[str, Any]:
    """
    Convert InsightResult to dict for progress events, excluding large AI fields.
    
    Excludes ai_analysis and ai_summary from progress events to reduce payload size
    in the progress windows.
    """
    result_dict = result.model_dump()
    # Remove large AI fields from progress events to reduce payload size
    result_dict.pop("ai_analysis", None)
    result_dict.pop("ai_summary", None)
    return result_dict


def _response_for_progress(response: AnalysisResponse) -> Dict[str, Any]:
    """
    Convert AnalysisResponse to dict for progress events, excluding large AI fields.
    
    Excludes ai_analysis and ai_summary from all InsightResult objects in progress events
    to reduce payload size in the progress windows.
    """
    response_dict = response.model_dump()
    # Filter ai_analysis and ai_summary from all results in all insight items
    for result_item in response_dict.get("results", []):
        for result in result_item.get("results", []):
            result.pop("ai_analysis", None)
            result.pop("ai_summary", None)
    return response_dict


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
                        data=_result_for_progress(path_result)
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
            # Send full result (including ai_analysis) in final event
            # Progress events exclude ai_analysis to reduce payload, but final result should include it
            yield _format_sse_event({
                "type": "result",
                "task_id": task_id,
                "data": final_result.model_dump()  # Full result with ai_analysis included
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
    streaming_enabled: Optional[bool] = None


class AIConfigCreate(BaseModel):
    name: str
    enabled: bool = True
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 60
    streaming_enabled: bool = True


class AIConfigUpdateRequest(BaseModel):
    name: Optional[str] = None  # If provided, renames the config
    enabled: Optional[bool] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    timeout: Optional[int] = None
    streaming_enabled: Optional[bool] = None


class AIConfigsListResponse(BaseModel):
    configs: List[Dict[str, Any]]


@router.post("/ai/analyze")
async def ai_analyze_result(request: AIAnalyzeRequest):
    """
    Analyze content with AI and return the response.
    
    Returns SSE stream of AI analysis if streaming is enabled,
    or JSON response if streaming is disabled.
    """
    logger.info(f"AI Analyze API: Starting analysis (prompt_type: {request.prompt_type})")
    
    if not AIConfig.is_configured():
        raise HTTPException(
            status_code=503,
            detail="AI service is not configured. Please set OPENAI_API_KEY and enable AI_ENABLED=true"
        )
    
    # Limit to configured max lines to control API costs and token usage
    MAX_LINES = AppConfig.get_result_max_lines()
    lines = request.content.split('\n')
    if len(lines) > MAX_LINES:
        logger.info(f"AI Analyze API: Limiting content from {len(lines)} to {MAX_LINES} lines")
        limited_content = '\n'.join(lines[:MAX_LINES])
        limited_content += f"\n\n[... {len(lines) - MAX_LINES} more lines truncated ...]"
    else:
        limited_content = request.content
    
    # Check if streaming is enabled
    streaming_enabled = AIConfig.STREAMING_ENABLED
    
    if streaming_enabled:
        # Streaming mode: return SSE stream
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
    else:
        # Non-streaming mode: return JSON response
        try:
            ai_service = get_ai_service()
            
            logger.info("AI Analyze API: Using non-streaming mode")
            
            # Collect all chunks from analyze_stream (even in non-streaming mode, it yields chunks)
            full_response = []
            async for chunk in ai_service.analyze_stream(
                content=limited_content,
                prompt_type=request.prompt_type,
                custom_prompt=request.custom_prompt,
                variables=request.variables
            ):
                full_response.append(chunk)
            
            content = "".join(full_response)
            logger.info("AI Analyze API: Analysis complete (non-streaming)")
            
            return {
                "type": "ai_complete",
                "message": "AI analysis complete",
                "content": content,
                "full_content": content
            }
        
        except Exception as e:
            logger.error(f"AI Analyze API: Error during analysis: {e}", exc_info=True)
            
            # Format error message to be more user-friendly
            error_message = str(e)
            
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
            
            raise HTTPException(
                status_code=500,
                detail=error_message
            )


# AI Config Profiles Management Endpoints

@router.get("/ai/configs")
async def get_ai_configs():
    """
    Get all AI configs in the exact file format.
    
    Returns: {active_config_name: "...", configs: {...}}
    Matches the structure of ~/.lensai/ai_configs.json exactly.
    API keys are returned as-is (no masking).
    """
    logger.info("AI Configs API: Fetching all configs")
    try:
        from app.core.config import _get_manager
        manager = _get_manager()
        logger.info(f"AI Configs API: Manager has {len(manager._configs)} config(s), active: {manager.get_active_config_name()}")
        result = manager.get_all_configs_dict()
        logger.info(f"AI Configs API: Returning {len(result.get('configs', {}))} config(s)")
        return result
    except Exception as e:
        logger.error(f"AI Configs API: Error fetching configs: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching AI configs: {str(e)}"
        )


@router.post("/ai/configs")
async def create_ai_config(config: AIConfigCreate):
    """
    Create new AI config profile.
    
    Returns 400 error if duplicate name.
    """
    logger.info(f"AI Configs API: Creating config '{config.name}'")
    try:
        from app.core.config import _get_manager
        manager = _get_manager()
        
        config_data = {
            "enabled": config.enabled,
            "base_url": config.base_url,
            "api_key": config.api_key,
            "model": config.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "timeout": config.timeout,
            "streaming_enabled": config.streaming_enabled
        }
        
        manager.create_config(config.name, config_data)
        
        # If this is the first config, make it active and reload AIConfig
        if manager.get_active_config_name() == config.name:
            AIConfig.reload()
            from app.services.ai_service import reset_ai_service
            reset_ai_service()
        
        return {"status": "success", "message": f"Config '{config.name}' created"}
    except ValueError as e:
        logger.warning(f"AI Configs API: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"AI Configs API: Error creating config: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error creating AI config: {str(e)}"
        )


@router.put("/ai/configs/{name}")
async def update_ai_config_by_name(name: str, config: AIConfigUpdateRequest):
    """
    Update existing AI config (can rename).
    
    Returns 400 error if new name exists and differs from current name.
    """
    logger.info(f"AI Configs API: Updating config '{name}'")
    try:
        from app.core.config import _get_manager
        manager = _get_manager()
        
        # Get existing config
        existing_config = manager.get_config(name)
        if existing_config is None:
            raise HTTPException(
                status_code=404,
                detail=f"Config '{name}' not found"
            )
        
        # Merge updates (name is optional - if not provided, keep same name)
        new_name = config.name if config.name is not None else name
        updated_config = existing_config.copy()
        
        if config.enabled is not None:
            updated_config["enabled"] = config.enabled
        if config.base_url is not None:
            updated_config["base_url"] = config.base_url
        if config.api_key is not None:
            updated_config["api_key"] = config.api_key
        if config.model is not None:
            updated_config["model"] = config.model.strip() if config.model.strip() else "gpt-4o-mini"
        if config.max_tokens is not None:
            updated_config["max_tokens"] = config.max_tokens
        if config.temperature is not None:
            updated_config["temperature"] = config.temperature
        if config.timeout is not None:
            updated_config["timeout"] = config.timeout
        if config.streaming_enabled is not None:
            updated_config["streaming_enabled"] = config.streaming_enabled
        
        manager.update_config(name, new_name, updated_config)
        
        # Reload AIConfig if this was the active config
        if manager.get_active_config_name() == new_name:
            AIConfig.reload()
            from app.services.ai_service import reset_ai_service
            reset_ai_service()
        
        return {"status": "success", "message": f"Config '{name}' updated"}
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"AI Configs API: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"AI Configs API: Error updating config: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error updating AI config: {str(e)}"
        )


@router.delete("/ai/configs/{name}")
async def delete_ai_config(name: str):
    """
    Delete AI config profile.
    
    Returns 400 error if active - must switch first.
    """
    logger.info(f"AI Configs API: Deleting config '{name}'")
    try:
        from app.core.config import _get_manager
        manager = _get_manager()
        
        manager.delete_config(name)
        
        return {"status": "success", "message": f"Config '{name}' deleted"}
    except ValueError as e:
        logger.warning(f"AI Configs API: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"AI Configs API: Error deleting config: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting AI config: {str(e)}"
        )


@router.post("/ai/configs/{name}/activate")
async def activate_ai_config(name: str):
    """
    Set config as active.
    """
    logger.info(f"AI Configs API: Activating config '{name}'")
    try:
        from app.core.config import _get_manager
        manager = _get_manager()
        
        manager.set_active_config(name)
        
        # Reload AIConfig to use new active config
        AIConfig.reload()
        from app.services.ai_service import reset_ai_service
        reset_ai_service()
        
        return {"status": "success", "message": f"Config '{name}' activated"}
    except ValueError as e:
        logger.warning(f"AI Configs API: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"AI Configs API: Error activating config: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error activating AI config: {str(e)}"
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
        logger.debug(f"AI Test API: Using service with base_url={AIConfig.BASE_URL}")
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
    logger.debug(f"AI Test API: Test config - base_url={config.base_url}, model={config.model}, streaming_enabled={getattr(config, 'streaming_enabled', None)}")
    
    if not config.base_url or not config.api_key:
        return {
            "success": False,
            "message": "Base URL and API key are required for testing"
        }
    
    try:
        from app.services.ai_service import AIService, get_ai_service
        from app.core.config import AIConfig
        
        # Temporarily update AIConfig for testing
        old_base_url = AIConfig.BASE_URL
        old_api_key = AIConfig.API_KEY
        old_model = AIConfig.MODEL
        old_max_tokens = AIConfig.MAX_TOKENS
        old_temperature = AIConfig.TEMPERATURE
        old_timeout = AIConfig.TIMEOUT
        old_streaming_enabled = AIConfig.STREAMING_ENABLED
        
        try:
            AIConfig.BASE_URL = config.base_url
            AIConfig.API_KEY = config.api_key
            AIConfig.MODEL = config.model or "gpt-4o-mini"
            AIConfig.MAX_TOKENS = config.max_tokens or 2000
            AIConfig.TEMPERATURE = config.temperature or 0.7
            AIConfig.TIMEOUT = 60
            # Use streaming_enabled from config if provided, otherwise default to True
            AIConfig.STREAMING_ENABLED = config.streaming_enabled if config.streaming_enabled is not None else True
            
            # Reset service to pick up new config
            from app.services.ai_service import reset_ai_service
            reset_ai_service()
            
            test_service = get_ai_service()
            logger.debug(f"AI Test API: Created test service with base_url={AIConfig.BASE_URL}, streaming_enabled={AIConfig.STREAMING_ENABLED}")
            success, message = await test_service.test_connection()
        finally:
            # Restore original config
            AIConfig.BASE_URL = old_base_url
            AIConfig.API_KEY = old_api_key
            AIConfig.MODEL = old_model
            AIConfig.MAX_TOKENS = old_max_tokens
            AIConfig.TEMPERATURE = old_temperature
            AIConfig.TIMEOUT = old_timeout
            AIConfig.STREAMING_ENABLED = old_streaming_enabled
            reset_ai_service()
        
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
        from app.services.ai_service import get_ai_service, reset_ai_service
        from app.core.config import AIConfig
        
        # Temporarily update AIConfig for testing
        old_base_url = AIConfig.BASE_URL
        old_api_key = AIConfig.API_KEY
        old_model = AIConfig.MODEL
        old_max_tokens = AIConfig.MAX_TOKENS
        old_temperature = AIConfig.TEMPERATURE
        old_timeout = AIConfig.TIMEOUT
        
        try:
            AIConfig.BASE_URL = config.base_url
            AIConfig.API_KEY = config.api_key or "dummy-key"  # Some servers don't require key for /models
            AIConfig.MODEL = config.model or "gpt-4o-mini"
            AIConfig.MAX_TOKENS = config.max_tokens or 2000
            AIConfig.TEMPERATURE = config.temperature or 0.7
            AIConfig.TIMEOUT = 10
            
            # Reset service to pick up new config
            reset_ai_service()
            
            temp_service = get_ai_service()
            models = await temp_service.get_available_models()
        finally:
            # Restore original config
            AIConfig.BASE_URL = old_base_url
            AIConfig.API_KEY = old_api_key
            AIConfig.MODEL = old_model
            AIConfig.MAX_TOKENS = old_max_tokens
            AIConfig.TEMPERATURE = old_temperature
            AIConfig.TIMEOUT = old_timeout
            reset_ai_service()
        
        logger.info(f"AI Models API: Found {len(models)} models")
        return {"models": models}
    
    except Exception as e:
        logger.error(f"AI Models API: Error fetching models: {e}", exc_info=True)
        return {"models": []}

