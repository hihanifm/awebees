import json
import logging
import os
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class InsightPathsConfig:
    """Manages external insight directory paths."""
    
    def __init__(self, config_file: str = None):
        """
        Initialize insight paths configuration.
        
        Args:
            config_file: Path to config file (defaults to ~/.lensai/insight_paths.json)
        """
        if config_file is None:
            # Use ~/.lensai/insight_paths.json (or C:\Users\username\.lensai\insight_paths.json on Windows)
            home_dir = Path.home()
            lensai_dir = home_dir / ".lensai"
            config_file = str(lensai_dir / "insight_paths.json")
        
        self.config_file = Path(config_file)
        self._paths: List[str] = []
        self._default_repository: Optional[str] = None
        self.load()
    
    def load(self) -> None:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self._paths = data.get("external_paths", [])
                    # Load default_repository from JSON config
                    self._default_repository = data.get("default_repository")
                logger.info(f"Loaded {len(self._paths)} external insight path(s) from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load insight paths config: {e}")
                self._paths = []
                self._default_repository = None
        else:
            logger.info("No insight paths config file found, starting with empty list")
            self._default_repository = None
    
    def save(self) -> None:
        try:
            # Ensure parent directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {"external_paths": self._paths}
            if self._default_repository is not None:
                data["default_repository"] = self._default_repository
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self._paths)} external insight path(s) to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save insight paths config: {e}")
    
    def get_paths(self) -> List[str]:
        return self._paths.copy()
    
    def add_path(self, path: str) -> None:
        if path not in self._paths:
            self._paths.append(path)
            self.save()
            logger.info(f"Added external insight path: {path}")
        else:
            logger.warning(f"Path already exists: {path}")
    
    def remove_path(self, path: str) -> None:
        if path in self._paths:
            self._paths.remove(path)
            self.save()
            logger.info(f"Removed external insight path: {path}")
        else:
            logger.warning(f"Path not found: {path}")
    
    def clear_paths(self) -> None:
        self._paths.clear()
        self.save()
        logger.info("Cleared all external insight paths")
    
    def get_default_repository(self) -> Optional[str]:
        """
        Get the default insights repository path.
        
        Precedence: JSON config → .env file → None
        """
        # First check JSON config (set via UI)
        if self._default_repository is not None:
            return self._default_repository
        
        # Fall back to .env file
        env_value = os.getenv("DEFAULT_INSIGHTS_REPOSITORY")
        if env_value:
            return env_value
        
        return None
    
    def set_default_repository(self, path: str) -> None:
        """
        Set the default insights repository path (saves to JSON config only).
        
        Args:
            path: Path to the default insights repository directory
        """
        self._default_repository = path
        self.save()
        logger.info(f"Set default insights repository: {path}")
    
    def clear_default_repository(self) -> None:
        """
        Clear the default insights repository from JSON config.
        System will fall back to .env file if set.
        """
        self._default_repository = None
        self.save()
        logger.info("Cleared default insights repository from JSON config")

