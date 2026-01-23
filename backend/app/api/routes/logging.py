from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from typing import Literal, Optional
import logging

from app.core.config import AppConfig, AIConfig

router = APIRouter(prefix="/api/logging", tags=["logging"])

logger = logging.getLogger(__name__)


class AppConfigResponse(BaseModel):
    """Unified response for all config.json settings."""
    log_level: str
    ai_processing_enabled: bool
    http_logging: bool
    result_max_lines: int
    detailed_logging: bool


class AppConfigUpdate(BaseModel):
    """Unified update model for config.json settings (all fields optional)."""
    log_level: Optional[Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]] = None
    ai_processing_enabled: Optional[bool] = None
    http_logging: Optional[bool] = None
    result_max_lines: Optional[int] = None
    detailed_logging: Optional[bool] = None
    
    @validator("log_level")
    def validate_log_level(cls, v):
        if v is not None:
            return v.upper()
        return v
    
    @validator("result_max_lines")
    def validate_result_max_lines(cls, v):
        if v is not None:
            if v < 1:
                raise ValueError("Result max lines must be at least 1")
            if v > 100000:
                raise ValueError("Result max lines cannot exceed 100000")
        return v


@router.get("/app-config", response_model=AppConfigResponse)
async def get_app_config():
    """Get all config.json settings in one call (for caching)."""
    logger.debug("Getting all app configuration")
    return AppConfigResponse(
        log_level=AppConfig.get_log_level(),
        ai_processing_enabled=AppConfig.get_ai_processing_enabled(),
        http_logging=AppConfig.get_http_logging(),
        result_max_lines=AppConfig.get_result_max_lines(),
        detailed_logging=AppConfig.get_detailed_logging()
    )


@router.put("/app-config", response_model=AppConfigResponse)
async def update_app_config(config: AppConfigUpdate):
    """Update config.json settings (all fields optional, only provided fields are updated)."""
    try:
        # Update only provided fields
        if config.log_level is not None:
            logger.info(f"Updating log level to: {config.log_level}")
            AppConfig.update_log_level(config.log_level, persist=True)
        
        if config.ai_processing_enabled is not None:
            logger.info(f"Updating AI processing enabled to: {config.ai_processing_enabled}")
            AppConfig.set_ai_processing_enabled(config.ai_processing_enabled)
        
        if config.http_logging is not None:
            logger.info(f"Updating HTTP logging to: {config.http_logging}")
            AppConfig.set_http_logging(config.http_logging)
        
        if config.result_max_lines is not None:
            logger.info(f"Updating result max lines to: {config.result_max_lines}")
            AppConfig.set_result_max_lines(config.result_max_lines)
        
        if config.detailed_logging is not None:
            logger.info(f"Updating detailed logging to: {config.detailed_logging}")
            AppConfig.set_detailed_logging(config.detailed_logging, persist=True)
        
        # Return updated config
        return AppConfigResponse(
            log_level=AppConfig.get_log_level(),
            ai_processing_enabled=AppConfig.get_ai_processing_enabled(),
            http_logging=AppConfig.get_http_logging(),
            result_max_lines=AppConfig.get_result_max_lines(),
            detailed_logging=AppConfig.get_detailed_logging()
        )
    except ValueError as e:
        logger.error(f"Failed to update app config: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating app config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update app config: {str(e)}")

