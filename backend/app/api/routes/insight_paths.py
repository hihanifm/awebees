from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
from pathlib import Path

from app.core.insight_paths_config import InsightPathsConfig
from app.core.plugin_manager import get_plugin_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/insight-paths", tags=["insight-paths"])


class InsightPathRequest(BaseModel):
    path: str


class InsightPathsResponse(BaseModel):
    paths: List[str]


class InsightSourceInfo(BaseModel):
    insight_id: str
    source: str


class DefaultRepositoryResponse(BaseModel):
    default_repository: Optional[str]


@router.get("/", response_model=InsightPathsResponse)
async def get_insight_paths():
    try:
        config = InsightPathsConfig()
        return InsightPathsResponse(paths=config.get_paths())
    except Exception as e:
        logger.error(f"Failed to get insight paths: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get insight paths: {str(e)}")


@router.post("/add")
async def add_insight_path(request: InsightPathRequest):
    try:
        path = Path(request.path)
        
        if not path.exists():
            raise HTTPException(
                status_code=400, 
                detail=f"Path does not exist: {request.path}"
            )
        
        if not path.is_dir():
            raise HTTPException(
                status_code=400, 
                detail=f"Path is not a directory: {request.path}"
            )
        
        config = InsightPathsConfig()
        config.add_path(str(path.absolute()))
        
        plugin_manager = get_plugin_manager()
        plugin_manager.discover_all_insights()
        
        insights_count = len(plugin_manager.get_all_insights())
        logger.info(f"Added external insight path: {request.path} (total insights: {insights_count})")
        
        return {
            "status": "success", 
            "message": f"Added path: {request.path}",
            "insights_count": insights_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add insight path: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add path: {str(e)}")


@router.post("/remove")
async def remove_insight_path(request: InsightPathRequest):
    try:
        config = InsightPathsConfig()
        config.remove_path(request.path)
        
        plugin_manager = get_plugin_manager()
        plugin_manager.discover_all_insights()
        
        insights_count = len(plugin_manager.get_all_insights())
        logger.info(f"Removed external insight path: {request.path} (total insights: {insights_count})")
        
        return {
            "status": "success", 
            "message": f"Removed path: {request.path}",
            "insights_count": insights_count
        }
    except Exception as e:
        logger.error(f"Failed to remove insight path: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove path: {str(e)}")


@router.post("/refresh")
async def refresh_insights():
    try:
        plugin_manager = get_plugin_manager()
        plugin_manager.discover_all_insights()
        
        insights_count = len(plugin_manager.get_all_insights())
        logger.info(f"Refreshed insights: {insights_count} total")
        
        return {
            "status": "success", 
            "insights_count": insights_count,
            "message": f"Refreshed {insights_count} insight(s)"
        }
    except Exception as e:
        logger.error(f"Failed to refresh insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh insights: {str(e)}")


@router.get("/sources")
async def get_insight_sources():
    try:
        plugin_manager = get_plugin_manager()
        sources = []
        
        for insight_id in plugin_manager.get_all_insights().keys():
            sources.append(InsightSourceInfo(
                insight_id=insight_id,
                source=plugin_manager.get_insight_source(insight_id)
            ))
        
        return sources
    except Exception as e:
        logger.error(f"Failed to get insight sources: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sources: {str(e)}")


@router.get("/default", response_model=DefaultRepositoryResponse)
async def get_default_repository():
    """Get the default insights repository path (JSON config takes precedence over .env)."""
    try:
        config = InsightPathsConfig()
        default_repo = config.get_default_repository()
        return DefaultRepositoryResponse(default_repository=default_repo)
    except Exception as e:
        logger.error(f"Failed to get default repository: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get default repository: {str(e)}")


@router.post("/default")
async def set_default_repository(request: InsightPathRequest):
    """Set the default insights repository path (saves to JSON config only, not .env)."""
    try:
        path = Path(request.path)
        
        if not path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Path does not exist: {request.path}"
            )
        
        if not path.is_dir():
            raise HTTPException(
                status_code=400,
                detail=f"Path is not a directory: {request.path}"
            )
        
        config = InsightPathsConfig()
        config.set_default_repository(str(path.absolute()))
        
        logger.info(f"Set default insights repository: {request.path}")
        
        return {
            "status": "success",
            "message": f"Set default repository: {request.path}",
            "default_repository": str(path.absolute())
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set default repository: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set default repository: {str(e)}")


@router.delete("/default")
async def clear_default_repository():
    """Clear the default insights repository from JSON config (falls back to .env if set)."""
    try:
        config = InsightPathsConfig()
        config.clear_default_repository()
        
        logger.info("Cleared default insights repository from JSON config")
        
        return {
            "status": "success",
            "message": "Cleared default repository from JSON config"
        }
    except Exception as e:
        logger.error(f"Failed to clear default repository: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear default repository: {str(e)}")

