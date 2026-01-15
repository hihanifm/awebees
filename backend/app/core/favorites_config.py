import json
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class FavoritesConfig:
    """Manages favorite insight IDs in user's home directory."""
    
    def __init__(self, config_file: str = None):
        """
        Initialize favorites configuration.
        
        Args:
            config_file: Path to config file (defaults to ~/.lensai/favorites.json)
        """
        if config_file is None:
            # Use ~/.lensai/favorites.json (or C:\Users\username\.lensai\favorites.json on Windows)
            home_dir = Path.home()
            lensai_dir = home_dir / ".lensai"
            config_file = str(lensai_dir / "favorites.json")
        
        self.config_file = Path(config_file)
        self._favorites: List[str] = []
        self.load()
    
    def load(self) -> None:
        """Load favorites from JSON file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self._favorites = data.get("favorites", [])
                    # Ensure it's a list
                    if not isinstance(self._favorites, list):
                        self._favorites = []
                logger.info(f"Loaded {len(self._favorites)} favorite insight(s) from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load favorites config: {e}")
                self._favorites = []
        else:
            logger.info("No favorites config file found, starting with empty list")
            self._favorites = []
    
    def save(self) -> None:
        """Save favorites to JSON file."""
        try:
            # Ensure parent directory exists (create ~/.lensai if needed)
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {"favorites": self._favorites}
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self._favorites)} favorite insight(s) to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save favorites config: {e}")
            raise
    
    def get_favorites(self) -> List[str]:
        """Get list of favorite insight IDs."""
        return self._favorites.copy()
    
    def add_favorite(self, insight_id: str) -> None:
        """Add an insight to favorites."""
        if insight_id not in self._favorites:
            self._favorites.append(insight_id)
            self.save()
            logger.info(f"Added insight to favorites: {insight_id}")
        else:
            logger.debug(f"Insight already in favorites: {insight_id}")
    
    def remove_favorite(self, insight_id: str) -> None:
        """Remove an insight from favorites."""
        if insight_id in self._favorites:
            self._favorites.remove(insight_id)
            self.save()
            logger.info(f"Removed insight from favorites: {insight_id}")
        else:
            logger.debug(f"Insight not in favorites: {insight_id}")
    
    def is_favorite(self, insight_id: str) -> bool:
        """Check if an insight is favorited."""
        return insight_id in self._favorites
    
    def toggle_favorite(self, insight_id: str) -> bool:
        """
        Toggle favorite status for an insight.
        
        Returns:
            True if insight is now favorited, False if removed from favorites.
        """
        if self.is_favorite(insight_id):
            self.remove_favorite(insight_id)
            return False
        else:
            self.add_favorite(insight_id)
            return True
