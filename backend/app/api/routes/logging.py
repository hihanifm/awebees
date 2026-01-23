from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from typing import Literal
import logging

from app.core.config import AppConfig, AIConfig

router = APIRouter(prefix="/api/logging", tags=["logging"])

logger = logging.getLogger(__name__)


class LoggingConfigUpdate(BaseModel):
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    @validator("log_level")
    def validate_log_level(cls, v):
        return v.upper()


class LoggingConfigResponse(BaseModel):
    log_level: str
    available_levels: list[str]


class ResultMaxLinesConfigResponse(BaseModel):
    result_max_lines: int


class ResultMaxLinesConfigUpdate(BaseModel):
    result_max_lines: int
    
    @validator("result_max_lines")
    def validate_result_max_lines(cls, v):
        if v < 1:
            raise ValueError("Result max lines must be at least 1")
        if v > 100000:
            raise ValueError("Result max lines cannot exceed 100000")
        return v


class HTTPLoggingConfigResponse(BaseModel):
    http_logging: bool


class HTTPLoggingConfigUpdate(BaseModel):
    http_logging: bool


class AIDetailedLoggingConfigResponse(BaseModel):
    detailed_logging: bool


class AIDetailedLoggingConfigUpdate(BaseModel):
    detailed_logging: bool


class AIProcessingEnabledConfigResponse(BaseModel):
    ai_processing_enabled: bool


class AIProcessingEnabledConfigUpdate(BaseModel):
    ai_processing_enabled: bool


@router.get("/config", response_model=LoggingConfigResponse)
async def get_logging_config():
    logger.debug("Getting logging configuration")
    return LoggingConfigResponse(
        log_level=AppConfig.get_log_level(),
        available_levels=AppConfig.VALID_LOG_LEVELS
    )


@router.put("/config", response_model=LoggingConfigResponse)
async def update_logging_config(config: LoggingConfigUpdate):
    try:
        logger.info(f"Updating log level to: {config.log_level}")
        AppConfig.update_log_level(config.log_level, persist=True)
        logger.info(f"Log level updated successfully to: {config.log_level}")
        
        return LoggingConfigResponse(
            log_level=AppConfig.get_log_level(),
            available_levels=AppConfig.VALID_LOG_LEVELS
        )
    except ValueError as e:
        logger.error(f"Failed to update log level: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating log level: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update log level: {str(e)}")


@router.get("/result-max-lines", response_model=ResultMaxLinesConfigResponse)
async def get_result_max_lines_config():
    """Get the current result max lines configuration."""
    logger.debug("Getting result max lines configuration")
    return ResultMaxLinesConfigResponse(
        result_max_lines=AppConfig.get_result_max_lines()
    )


@router.put("/result-max-lines", response_model=ResultMaxLinesConfigResponse)
async def update_result_max_lines_config(config: ResultMaxLinesConfigUpdate):
    """Update the result max lines configuration and persist to config.json."""
    try:
        logger.info(f"Updating result max lines to: {config.result_max_lines}")
        AppConfig.set_result_max_lines(config.result_max_lines)
        logger.info(f"Result max lines updated successfully to: {config.result_max_lines}")
        
        return ResultMaxLinesConfigResponse(
            result_max_lines=AppConfig.get_result_max_lines()
        )
    except ValueError as e:
        logger.error(f"Failed to update result max lines: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating result max lines: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update result max lines: {str(e)}")


@router.get("/http-logging", response_model=HTTPLoggingConfigResponse)
async def get_http_logging_config():
    """Get the current HTTP logging configuration."""
    logger.debug("Getting HTTP logging configuration")
    return HTTPLoggingConfigResponse(
        http_logging=AppConfig.get_http_logging()
    )


@router.put("/http-logging", response_model=HTTPLoggingConfigResponse)
async def update_http_logging_config(config: HTTPLoggingConfigUpdate):
    """Update the HTTP logging configuration."""
    try:
        logger.info(f"Updating HTTP logging to: {config.http_logging}")
        AppConfig.set_http_logging(config.http_logging)
        logger.info(f"HTTP logging updated successfully to: {config.http_logging}")
        
        return HTTPLoggingConfigResponse(
            http_logging=AppConfig.get_http_logging()
        )
    except Exception as e:
        logger.error(f"Unexpected error updating HTTP logging: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update HTTP logging: {str(e)}")


@router.get("/ai-detailed-logging", response_model=AIDetailedLoggingConfigResponse)
async def get_ai_detailed_logging_config():
    """Get the current AI detailed logging configuration."""
    logger.debug("Getting AI detailed logging configuration")
    return AIDetailedLoggingConfigResponse(
        detailed_logging=AIConfig.DETAILED_LOGGING
    )


@router.put("/ai-detailed-logging", response_model=AIDetailedLoggingConfigResponse)
async def update_ai_detailed_logging_config(config: AIDetailedLoggingConfigUpdate):
    """Update the AI detailed logging configuration."""
    try:
        logger.info(f"Updating AI detailed logging to: {config.detailed_logging}")
        AIConfig.DETAILED_LOGGING = config.detailed_logging
        logger.info(f"AI detailed logging updated successfully to: {config.detailed_logging}")
        
        return AIDetailedLoggingConfigResponse(
            detailed_logging=AIConfig.DETAILED_LOGGING
        )
    except Exception as e:
        logger.error(f"Unexpected error updating AI detailed logging: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update AI detailed logging: {str(e)}")


@router.get("/ai-processing-enabled", response_model=AIProcessingEnabledConfigResponse)
async def get_ai_processing_enabled_config():
    """Get the current AI processing enabled configuration (global setting)."""
    logger.debug("Getting AI processing enabled configuration")
    return AIProcessingEnabledConfigResponse(
        ai_processing_enabled=AppConfig.get_ai_processing_enabled()
    )


@router.put("/ai-processing-enabled", response_model=AIProcessingEnabledConfigResponse)
async def update_ai_processing_enabled_config(config: AIProcessingEnabledConfigUpdate):
    """Update the AI processing enabled configuration (global setting)."""
    try:
        logger.info(f"Updating AI processing enabled to: {config.ai_processing_enabled}")
        AppConfig.set_ai_processing_enabled(config.ai_processing_enabled)
        logger.info(f"AI processing enabled updated successfully to: {config.ai_processing_enabled}")
        
        return AIProcessingEnabledConfigResponse(
            ai_processing_enabled=AppConfig.get_ai_processing_enabled()
        )
    except Exception as e:
        logger.error(f"Unexpected error updating AI processing enabled: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update AI processing enabled: {str(e)}")


class AppConfigResponse(BaseModel):
    """Unified response for all config.json settings."""
    log_level: str
    ai_processing_enabled: bool
    http_logging: bool
    result_max_lines: int


@router.get("/app-config", response_model=AppConfigResponse)
async def get_app_config():
    """Get all config.json settings in one call (for caching)."""
    logger.debug("Getting all app configuration")
    return AppConfigResponse(
        log_level=AppConfig.get_log_level(),
        ai_processing_enabled=AppConfig.get_ai_processing_enabled(),
        http_logging=AppConfig.get_http_logging(),
        result_max_lines=AppConfig.get_result_max_lines()
    )

