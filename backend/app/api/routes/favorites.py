from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import logging

from app.core.favorites_config import FavoritesConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/favorites", tags=["favorites"])

# Singleton instance of FavoritesConfig
_favorites_config: FavoritesConfig = None


def get_favorites_config() -> FavoritesConfig:
    """Get or create the FavoritesConfig singleton."""
    global _favorites_config
    if _favorites_config is None:
        _favorites_config = FavoritesConfig()
    return _favorites_config


class FavoritesResponse(BaseModel):
    favorites: List[str]


class FavoriteStatusResponse(BaseModel):
    is_favorite: bool


@router.get("", response_model=FavoritesResponse)
async def get_favorites():
    """Get list of all favorited insight IDs."""
    logger.debug("Favorites API: Received request to get favorites")
    config = get_favorites_config()
    favorites = config.get_favorites()
    logger.info(f"Favorites API: Returning {len(favorites)} favorite insight(s)")
    return FavoritesResponse(favorites=favorites)


@router.get("/{insight_id}", response_model=FavoriteStatusResponse)
async def check_favorite(insight_id: str):
    """Check if an insight is favorited."""
    logger.debug(f"Favorites API: Received request to check favorite status: {insight_id}")
    config = get_favorites_config()
    is_favorite = config.is_favorite(insight_id)
    return FavoriteStatusResponse(is_favorite=is_favorite)


@router.post("/{insight_id}", response_model=FavoritesResponse)
async def add_favorite(insight_id: str):
    """Add an insight to favorites."""
    logger.debug(f"Favorites API: Received request to add favorite: {insight_id}")
    config = get_favorites_config()
    config.add_favorite(insight_id)
    favorites = config.get_favorites()
    logger.info(f"Favorites API: Added favorite {insight_id}, total favorites: {len(favorites)}")
    return FavoritesResponse(favorites=favorites)


@router.delete("/{insight_id}", response_model=FavoritesResponse)
async def remove_favorite(insight_id: str):
    """Remove an insight from favorites."""
    logger.debug(f"Favorites API: Received request to remove favorite: {insight_id}")
    config = get_favorites_config()
    config.remove_favorite(insight_id)
    favorites = config.get_favorites()
    logger.info(f"Favorites API: Removed favorite {insight_id}, total favorites: {len(favorites)}")
    return FavoritesResponse(favorites=favorites)
