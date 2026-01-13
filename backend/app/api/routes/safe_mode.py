from fastapi import APIRouter
from pydantic import BaseModel
import logging

from app.core.config import SafeModeConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/safe-mode", tags=["safe-mode"])


class SafeModeResponse(BaseModel):
    enabled: bool
    from_env: bool
    message: str = ""


@router.get("", response_model=SafeModeResponse)
async def get_safe_mode():
    """Get current safe mode state."""
    try:
        return SafeModeResponse(
            enabled=SafeModeConfig.is_enabled(),
            from_env=SafeModeConfig.FROM_ENV
        )
    except Exception as e:
        logger.error(f"Failed to get safe mode: {e}")
        raise


@router.post("/start")
async def start_safe_mode():
    """Set safe mode enabled (requires restart to take effect)."""
    try:
        SafeModeConfig.start()
        return {
            "enabled": SafeModeConfig.is_enabled(),
            "from_env": SafeModeConfig.FROM_ENV,
            "message": "Safe mode enabled. Please restart the app for changes to take effect."
        }
    except Exception as e:
        logger.error(f"Failed to start safe mode: {e}")
        raise


@router.post("/stop")
async def stop_safe_mode():
    """Set safe mode disabled (requires restart to take effect)."""
    try:
        SafeModeConfig.stop()
        return {
            "enabled": SafeModeConfig.is_enabled(),
            "from_env": SafeModeConfig.FROM_ENV,
            "message": "Safe mode disabled. Please restart the app for changes to take effect."
        }
    except Exception as e:
        logger.error(f"Failed to stop safe mode: {e}")
        raise
