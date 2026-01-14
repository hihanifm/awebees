from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from typing import Literal
import logging

from app.core.config import AppConfig

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
    """Update the result max lines configuration (in-memory only)."""
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

