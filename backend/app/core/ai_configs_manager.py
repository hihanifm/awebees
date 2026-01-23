import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class AIConfigsManager:
    """Manages AI configuration profiles in ~/.lensai/ai_configs.json"""
    
    def __init__(self, config_file: str = None):
        """
        Initialize AI configs manager.
        
        Args:
            config_file: Path to config file (defaults to ~/.lensai/ai_configs.json)
        """
        if config_file is None:
            # Use ~/.lensai/ai_configs.json (or C:\Users\username\.lensai\ai_configs.json on Windows)
            home_dir = Path.home()
            lensai_dir = home_dir / ".lensai"
            config_file = str(lensai_dir / "ai_configs.json")
        
        self.config_file = Path(config_file)
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._active_config_name: Optional[str] = None
        
        logger.info(f"AIConfigsManager: Initializing with config file: {self.config_file}")
        logger.info(f"AIConfigsManager: File exists: {self.config_file.exists()}")
        
        # If config file doesn't exist, copy from default
        if not self.config_file.exists():
            logger.info(f"AIConfigsManager: Config file does not exist, copying from default")
            self._copy_default_config_file()
        else:
            logger.info(f"AIConfigsManager: Config file exists at {self.config_file}")
        
        self.load()
    
    def _load_defaults(self) -> Dict[str, Any]:
        """Load default values from default_ai_configs.json (checks default insights path first, then built-in)."""
        # First, try to load from default insights repository
        try:
            from app.core.insight_paths_config import InsightPathsConfig
            paths_config = InsightPathsConfig()
            default_repo = paths_config.get_default_repository()
            
            if default_repo:
                defaults_path = Path(default_repo) / "default_ai_configs.json"
                if defaults_path.exists():
                    try:
                        with open(defaults_path, 'r') as f:
                            data = json.load(f)
                            # New format: same as ai_configs.json with "configs" and "active_config_name"
                            if "configs" in data and isinstance(data["configs"], dict):
                                # Get the active config or first config
                                active_name = data.get("active_config_name")
                                if active_name and active_name in data["configs"]:
                                    logger.info(f"Loaded defaults from insights repository: {defaults_path}")
                                    return data["configs"][active_name]
                                elif data["configs"]:
                                    # Use first config if no active specified
                                    first_config = next(iter(data["configs"].values()))
                                    logger.info(f"Loaded defaults from insights repository (first config): {defaults_path}")
                                    return first_config
                    except Exception as e:
                        logger.warning(f"Failed to load defaults from insights repository {defaults_path}: {e}")
        except Exception as e:
            logger.debug(f"Could not check default insights repository: {e}")
        
        # Fallback to built-in default_ai_configs.json
        backend_dir = Path(__file__).parent.parent
        builtin_defaults = backend_dir / "default_ai_configs.json"
        
        if builtin_defaults.exists():
            try:
                with open(builtin_defaults, 'r') as f:
                    data = json.load(f)
                    # New format: same as ai_configs.json with "configs" and "active_config_name"
                    if "configs" in data and isinstance(data["configs"], dict):
                        # Get the active config or first config
                        active_name = data.get("active_config_name")
                        if active_name and active_name in data["configs"]:
                            logger.info(f"Loaded defaults from built-in file: {builtin_defaults}")
                            return data["configs"][active_name]
                        elif data["configs"]:
                            # Use first config if no active specified
                            first_config = next(iter(data["configs"].values()))
                            logger.info(f"Loaded defaults from built-in file (first config): {builtin_defaults}")
                            return first_config
            except Exception as e:
                logger.error(f"Failed to load built-in defaults: {e}")
        
        # Hardcoded fallback defaults
        logger.warning("Using hardcoded defaults - default_ai_configs.json not found")
        return {
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
            "model": "gpt-4o-mini",
            "max_tokens": 2000,
            "temperature": 0.7,
            "timeout": 60,
            "streaming_enabled": True
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default config values (from default_ai_configs.json)."""
        defaults = self._load_defaults()
        # Ensure all required fields are present (name is not stored - it's the dict key)
        # Note: enabled is removed - use global AppConfig.AI_PROCESSING_ENABLED instead
        return {
            "base_url": defaults.get("base_url", "https://api.openai.com/v1"),
            "api_key": defaults.get("api_key", ""),
            "model": defaults.get("model", "gpt-4o-mini"),
            "max_tokens": defaults.get("max_tokens", 2000),
            "temperature": defaults.get("temperature", 0.7),
            "timeout": defaults.get("timeout", 60),
            "streaming_enabled": defaults.get("streaming_enabled", True)
        }
    
    def _copy_default_config_file(self) -> None:
        """Copy default_ai_configs.json to ~/.lensai/ai_configs.json if it doesn't exist."""
        logger.info(f"AIConfigsManager._copy_default_config_file(): Copying default config to {self.config_file}")
        
        # First, try to find default_ai_configs.json in default insights repository
        default_file = None
        try:
            from app.core.insight_paths_config import InsightPathsConfig
            paths_config = InsightPathsConfig()
            default_repo = paths_config.get_default_repository()
            logger.info(f"AIConfigsManager._copy_default_config_file(): Default repo: {default_repo}")
            
            if default_repo:
                defaults_path = Path(default_repo) / "default_ai_configs.json"
                logger.info(f"AIConfigsManager._copy_default_config_file(): Checking {defaults_path}")
                if defaults_path.exists():
                    default_file = defaults_path
                    logger.info(f"AIConfigsManager._copy_default_config_file(): Found default config in insights repository: {defaults_path}")
                else:
                    logger.info(f"AIConfigsManager._copy_default_config_file(): Default config not found in insights repository")
        except Exception as e:
            logger.warning(f"AIConfigsManager._copy_default_config_file(): Could not check default insights repository: {e}", exc_info=True)
        
        # Fallback to built-in default_ai_configs.json
        if default_file is None:
            backend_dir = Path(__file__).parent.parent
            builtin_defaults = backend_dir / "default_ai_configs.json"
            logger.info(f"AIConfigsManager._copy_default_config_file(): Checking built-in defaults at {builtin_defaults}")
            if builtin_defaults.exists():
                default_file = builtin_defaults
                logger.info(f"AIConfigsManager._copy_default_config_file(): Using built-in default config: {builtin_defaults}")
            else:
                logger.warning(f"AIConfigsManager._copy_default_config_file(): Built-in defaults not found at {builtin_defaults}")
        
        # Copy the file if found
        if default_file and default_file.exists():
            try:
                logger.info(f"AIConfigsManager._copy_default_config_file(): Copying from {default_file} to {self.config_file}")
                # Ensure parent directory exists
                self.config_file.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"AIConfigsManager._copy_default_config_file(): Created directory {self.config_file.parent}")
                # Copy the file
                shutil.copy2(default_file, self.config_file)
                logger.info(f"AIConfigsManager._copy_default_config_file(): Successfully copied default config from {default_file} to {self.config_file}")
            except Exception as e:
                logger.error(f"AIConfigsManager._copy_default_config_file(): Failed to copy default config file: {e}", exc_info=True)
                # Fall back to creating default config programmatically
                logger.info(f"AIConfigsManager._copy_default_config_file(): Falling back to programmatic creation")
                self._create_default_config_programmatically()
        else:
            logger.warning(f"AIConfigsManager._copy_default_config_file(): No default_ai_configs.json found, creating default config programmatically")
            # Fall back to creating default config programmatically
            self._create_default_config_programmatically()
    
    def _create_default_config_programmatically(self) -> None:
        """Create default config programmatically if default file is not available."""
        logger.info(f"AIConfigsManager._create_default_config_programmatically(): Creating default config programmatically")
        default_config = self._get_default_config()
        logger.debug(f"AIConfigsManager._create_default_config_programmatically(): Default config: {default_config}")
        config_name = "openai"  # Default name
        self._configs[config_name] = default_config
        self._active_config_name = config_name
        logger.info(f"AIConfigsManager._create_default_config_programmatically(): Saving default config to {self.config_file}")
        self.save()
        logger.info(f"AIConfigsManager._create_default_config_programmatically(): Created default AI config '{config_name}' programmatically")
    
    def load(self) -> None:
        """Load configs from JSON file."""
        logger.info(f"AIConfigsManager.load(): Loading from {self.config_file}")
        logger.info(f"AIConfigsManager.load(): File exists: {self.config_file.exists()}")
        logger.info(f"AIConfigsManager.load(): File absolute path: {self.config_file.absolute()}")
        
        if self.config_file.exists():
            try:
                logger.info(f"AIConfigsManager.load(): Reading file...")
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                logger.info(f"AIConfigsManager.load(): File contents keys: {list(data.keys())}")
                self._configs = data.get("configs", {})
                self._active_config_name = data.get("active_config_name")
                
                # Strip 'enabled' field from all configs (backward compatibility)
                # All configs are enabled by default - errors are shown to user
                for config_name, config in self._configs.items():
                    if isinstance(config, dict) and "enabled" in config:
                        logger.info(f"AIConfigsManager.load(): Removing 'enabled' field from config '{config_name}' (backward compatibility)")
                        config.pop("enabled", None)
                
                logger.info(f"AIConfigsManager.load(): Extracted configs: {list(self._configs.keys())}")
                logger.info(f"AIConfigsManager.load(): Active config name: {self._active_config_name}")
                
                # Ensure configs is a dict
                if not isinstance(self._configs, dict):
                    logger.warning(f"AIConfigsManager.load(): Configs is not a dict: {type(self._configs)}, resetting to empty dict")
                    self._configs = {}
                
                logger.info(f"AIConfigsManager.load(): Successfully loaded {len(self._configs)} AI config(s) from {self.config_file}")
                if self._active_config_name:
                    if self._active_config_name in self._configs:
                        logger.info(f"AIConfigsManager.load(): Active config '{self._active_config_name}' found in configs")
                        logger.debug(f"AIConfigsManager.load(): Active config data: {self._configs[self._active_config_name]}")
                    else:
                        logger.warning(f"AIConfigsManager.load(): Active config name '{self._active_config_name}' not found in configs! Available: {list(self._configs.keys())}")
                else:
                    logger.warning(f"AIConfigsManager.load(): No active_config_name set in file")
            except json.JSONDecodeError as e:
                logger.error(f"AIConfigsManager.load(): Failed to parse JSON from {self.config_file}: {e}", exc_info=True)
                self._configs = {}
                self._active_config_name = None
            except Exception as e:
                logger.error(f"AIConfigsManager.load(): Failed to load AI configs from {self.config_file}: {e}", exc_info=True)
                self._configs = {}
                self._active_config_name = None
        else:
            logger.warning(f"AIConfigsManager.load(): Config file does not exist at {self.config_file}")
            logger.warning(f"AIConfigsManager.load(): Will use empty configs (should have been created in __init__)")
            self._configs = {}
            self._active_config_name = None
        
        logger.info(f"AIConfigsManager.load(): Final state - Configs: {list(self._configs.keys())}, Active: {self._active_config_name}")
    
    def save(self) -> None:
        """Save configs to JSON file."""
        logger.info(f"AIConfigsManager.save(): Saving to {self.config_file}")
        logger.info(f"AIConfigsManager.save(): Configs to save: {list(self._configs.keys())}, Active: {self._active_config_name}")
        try:
            # Ensure parent directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"AIConfigsManager.save(): Directory exists: {self.config_file.parent}")
            
            # Strip 'enabled' field from all configs before saving
            # All configs are enabled by default - errors are shown to user
            configs_to_save = {}
            for name, config in self._configs.items():
                config_copy = config.copy()
                config_copy.pop("enabled", None)
                configs_to_save[name] = config_copy
            
            data = {
                "active_config_name": self._active_config_name,
                "configs": configs_to_save
            }
            
            logger.debug(f"AIConfigsManager.save(): Data to save: {data}")
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"AIConfigsManager.save(): Successfully saved {len(self._configs)} AI config(s) to {self.config_file}")
            logger.debug(f"AIConfigsManager.save(): File saved at {self.config_file.absolute()}")
        except Exception as e:
            logger.error(f"AIConfigsManager.save(): Failed to save AI configs to {self.config_file}: {e}", exc_info=True)
            raise
    
    def get_all_configs_dict(self) -> Dict[str, Any]:
        """Get all configs in the exact file format: {active_config_name: ..., configs: {...}}."""
        # Return configs as-is, no masking - API keys are shown directly
        # Strip 'enabled' field if present (all configs are enabled by default)
        configs_dict = {}
        for name, config in self._configs.items():
            config_copy = config.copy()
            # Remove 'enabled' field if present - all configs are enabled
            config_copy.pop("enabled", None)
            configs_dict[name] = config_copy
        
        return {
            "active_config_name": self._active_config_name,
            "configs": configs_dict
        }
    
    def get_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific config by name."""
        if name not in self._configs:
            return None
        
        # Return config as-is, no masking - API keys are shown directly
        # Strip 'enabled' field if present (all configs are enabled by default)
        config = self._configs[name].copy()
        config.pop("enabled", None)
        return config
    
    def create_config(self, name: str, config_data: Dict[str, Any]) -> None:
        """Create new config. Raises error if name already exists."""
        if name in self._configs:
            raise ValueError(f"Config with name '{name}' already exists. Please use a different name.")
        
        # Remove 'name' field if present (redundant - key is the name)
        config_data.pop("name", None)
        # Remove 'enabled' field - all configs are enabled by default, errors are shown to user
        config_data.pop("enabled", None)
        self._configs[name] = config_data
        
        # If this is the first config, make it active
        if not self._active_config_name:
            self._active_config_name = name
        
        self.save()
        logger.info(f"Created AI config: {name}")
    
    def update_config(self, old_name: str, new_name: str, config_data: Dict[str, Any]) -> None:
        """Update existing config. Can rename. Raises error if new_name exists and differs from old_name."""
        if old_name not in self._configs:
            raise ValueError(f"Config '{old_name}' not found.")
        
        # If renaming to a different name that already exists, error
        if new_name != old_name and new_name in self._configs:
            raise ValueError(f"Config with name '{new_name}' already exists. Please use a different name.")
        
        # Remove 'name' field if present (redundant - key is the name)
        config_data.pop("name", None)
        # Remove 'enabled' field - all configs are enabled by default, errors are shown to user
        config_data.pop("enabled", None)
        
        # If renaming, remove old key and create new one
        if new_name != old_name:
            del self._configs[old_name]
            # Update active config name if it was the active one
            if self._active_config_name == old_name:
                self._active_config_name = new_name
        
        self._configs[new_name] = config_data
        self.save()
        logger.info(f"Updated AI config: {old_name} -> {new_name}")
    
    def delete_config(self, name: str) -> None:
        """Delete config. Raises error if active."""
        if name not in self._configs:
            raise ValueError(f"Config '{name}' not found.")
        
        if self._active_config_name == name:
            raise ValueError("Cannot delete the active config. Please switch to another config first.")
        
        del self._configs[name]
        self.save()
        logger.info(f"Deleted AI config: {name}")
    
    def set_active_config(self, name: str) -> None:
        """Switch active config."""
        if name not in self._configs:
            raise ValueError(f"Config '{name}' not found.")
        
        self._active_config_name = name
        self.save()
        logger.info(f"Set active AI config: {name}")
    
    def get_active_config_name(self) -> Optional[str]:
        """Get active config name."""
        return self._active_config_name
