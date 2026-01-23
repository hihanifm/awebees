"""
Manages application configuration in ~/.lensai/config.json

This handles global settings like:
- Log level
- AI processing enabled
- HTTP logging
- Result max lines
- Other app-level settings

The .env file is now read-only for build-time defaults only.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


class AppConfigManager:
    """Manages application configuration in ~/.lensai/config.json"""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize AppConfigManager.
        
        Args:
            config_file: Path to config file (defaults to ~/.lensai/config.json)
        """
        if config_file is None:
            # Use ~/.lensai/config.json (or C:\Users\username\.lensai\config.json on Windows)
            home_dir = Path.home()
            lensai_dir = home_dir / ".lensai"
            config_file = lensai_dir / "config.json"
        
        self.config_file = Path(config_file)
        self._config: Dict[str, Any] = {}
        
        # Load config on initialization
        self.load()
    
    def load(self) -> None:
        """Load config from JSON file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._config = data if isinstance(data, dict) else {}
                logger.info(f"AppConfigManager.load(): Loaded config from {self.config_file}")
                logger.debug(f"AppConfigManager.load(): Config data: {self._config}")
            except json.JSONDecodeError as e:
                logger.error(f"AppConfigManager.load(): Failed to parse JSON from {self.config_file}: {e}", exc_info=True)
                self._config = {}
            except Exception as e:
                logger.error(f"AppConfigManager.load(): Failed to load config from {self.config_file}: {e}", exc_info=True)
                self._config = {}
        else:
            logger.info(f"AppConfigManager.load(): Config file does not exist at {self.config_file}, using defaults")
            self._config = {}
            # Create default config file
            self._create_default_config()
    
    def save(self) -> None:
        """Save config to JSON file."""
        logger.info(f"AppConfigManager.save(): Saving to {self.config_file}")
        try:
            # Ensure parent directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"AppConfigManager.save(): Successfully saved config to {self.config_file}")
        except Exception as e:
            logger.error(f"AppConfigManager.save(): Failed to save config to {self.config_file}: {e}", exc_info=True)
            raise
    
    def _create_default_config(self) -> None:
        """Create default config file with initial values."""
        logger.info(f"AppConfigManager._create_default_config(): Creating default config at {self.config_file}")
        self._config = {
            "log_level": "DEBUG",
            "ai_processing_enabled": True,
            "http_logging": True,
            "result_max_lines": 500,
            "detailed_logging": True,
        }
        self.save()
        logger.info(f"AppConfigManager._create_default_config(): Created default config")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any, save: bool = True) -> None:
        """Set a config value."""
        old_value = self._config.get(key)
        self._config[key] = value
        logger.info(f"AppConfigManager.set(): {key} = {old_value} -> {value}")
        if save:
            self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all config values."""
        return self._config.copy()
    
    def update(self, updates: Dict[str, Any], save: bool = True) -> None:
        """Update multiple config values at once."""
        for key, value in updates.items():
            self._config[key] = value
        logger.info(f"AppConfigManager.update(): Updated keys: {list(updates.keys())}")
        if save:
            self.save()
