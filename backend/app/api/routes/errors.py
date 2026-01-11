from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import logging
import json
import asyncio
from datetime import datetime

from app.core.plugin_manager import get_plugin_manager
from app.core.models import ErrorEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/errors", tags=["errors"])


def _format_sse_event(data: dict) -> str:
    def json_serial(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    json_data = json.dumps(data, default=json_serial)
    return f"data: {json_data}\n\n"


async def _stream_errors() -> AsyncGenerator[str, None]:
    try:
        plugin_manager = get_plugin_manager()
        errors = plugin_manager.get_errors()
        for error in errors:
            yield _format_sse_event(error.model_dump())
        
        logger.info(f"Errors API: Streamed {len(errors)} error(s)")
        
    except Exception as e:
        logger.error(f"Error in error stream: {e}", exc_info=True)
        yield _format_sse_event({
            "type": "stream_error",
            "message": f"Error streaming events: {str(e)}",
            "severity": "error",
            "timestamp": datetime.utcnow().isoformat()
        })


@router.get("/stream")
async def stream_errors():
    """
    Stream backend errors via Server-Sent Events.
    
    Returns all errors collected during insight discovery.
    Errors include duplicate IDs, import failures, and instantiation failures.
    """
    logger.info("Errors API: Starting error stream")
    
    response = StreamingResponse(
        _stream_errors(),
        media_type="text/event-stream"
    )
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"
    
    return response

