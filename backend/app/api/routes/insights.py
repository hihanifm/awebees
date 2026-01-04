"""API routes for insights."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import logging

from app.core.plugin_manager import get_plugin_manager
from app.core.models import InsightMetadata

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/insights", tags=["insights"])


class InsightsResponse(BaseModel):
    """Response with list of available insights."""
    insights: List[InsightMetadata]


@router.get("", response_model=InsightsResponse)
async def list_insights():
    """Get list of all available insights."""
    plugin_manager = get_plugin_manager()
    insights = plugin_manager.list_insights()
    
    return InsightsResponse(insights=insights)

