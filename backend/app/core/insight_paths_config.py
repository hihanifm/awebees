import json
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class InsightPathsConfig:
    """Manages external insight directory paths."""
    
    def __init__(self, config_file: str = None):
        """
        Initialize insight paths configuration.
        
        Args:
            config_file: Path to config file (defaults to backend/insight_paths.json)
        """
        if config_file is None:
            # Default to backend directory
            backend_dir = Path(__file__).parent.parent.parent
            config_file = str(backend_dir / "insight_paths.json")
        
        self.config_file = Path(config_file)
        self._paths: List[str] = []
        self.load()
    
    def load(self) -> None:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self._paths = data.get("external_paths", [])
                logger.info(f"Loaded {len(self._paths)} external insight path(s) from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load insight paths config: {e}")
                self._paths = []
        else:
            logger.info("No insight paths config file found, starting with empty list")
    
    def save(self) -> None:
        try:
            # Ensure parent directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump({"external_paths": self._paths}, f, indent=2)
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

