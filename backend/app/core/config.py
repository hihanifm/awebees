"""Configuration settings for the Lens application."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AIConfig:
    """Configuration for AI-powered analysis."""
    
    # Global AI toggle
    ENABLED: bool = os.getenv("AI_ENABLED", "false").lower() == "true"
    
    # OpenAI API configuration
    BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Request parameters
    MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
    TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    TIMEOUT: int = int(os.getenv("OPENAI_TIMEOUT", "60"))
    
    # Predefined system prompts
    SYSTEM_PROMPTS: Dict[str, str] = {
        "summarize": """You are a log analysis assistant. Summarize the following log analysis results concisely.

Focus on:
- Key findings and patterns
- Critical issues identified
- Important statistics

Keep it brief and actionable, using bullet points.""",
        
        "explain": """You are a log analysis expert. Analyze the following log data and explain:

- What patterns and trends you observe
- What these patterns indicate about system behavior
- Potential root causes of issues
- Technical insights and correlations

Be thorough but concise. Use technical terminology when appropriate.""",
        
        "recommend": """You are a system reliability expert. Based on the following log analysis, provide:

1. **Immediate Actions**: Critical issues requiring immediate attention
2. **Short-term Fixes**: Problems to address soon
3. **Long-term Improvements**: Preventive measures and optimizations
4. **Monitoring Recommendations**: What to watch for

Be specific and practical. Prioritize recommendations by severity."""
    }
    
    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.API_KEY) and cls.ENABLED
    
    @classmethod
    def to_dict(cls, include_sensitive: bool = False) -> Dict[str, Any]:
        config = {
            "enabled": cls.ENABLED,
            "base_url": cls.BASE_URL,
            "model": cls.MODEL,
            "max_tokens": cls.MAX_TOKENS,
            "temperature": cls.TEMPERATURE,
            "timeout": cls.TIMEOUT,
            "is_configured": cls.is_configured()
        }
        
        if include_sensitive:
            config["api_key"] = cls.API_KEY
        else:
            # Mask API key for display
            if cls.API_KEY:
                key_preview = cls.API_KEY[:8] + "..." if len(cls.API_KEY) > 8 else "***"
                config["api_key_preview"] = key_preview
            else:
                config["api_key_preview"] = None
        
        return config
    
    @classmethod
    def _get_env_file_path(cls) -> Path:
        # Start from this file's location and go up to backend directory
        backend_dir = Path(__file__).parent.parent.parent
        return backend_dir / ".env"
    
    @classmethod
    def _persist_to_env(cls, updates: Dict[str, Any]) -> None:
        """
        Persist AI configuration updates to .env file.
        
        Args:
            updates: Dictionary of config updates to persist
        """
        import logging
        import tempfile
        import shutil
        logger = logging.getLogger(__name__)
        
        env_file = cls._get_env_file_path()
        logger.info(f"Persisting AI config to .env file: {env_file}")
        
        # Mapping of config keys to environment variable names
        env_key_mapping = {
            "enabled": "AI_ENABLED",
            "base_url": "OPENAI_BASE_URL",
            "api_key": "OPENAI_API_KEY",
            "model": "OPENAI_MODEL",
            "max_tokens": "OPENAI_MAX_TOKENS",
            "temperature": "OPENAI_TEMPERATURE",
            "timeout": "OPENAI_TIMEOUT"
        }
        
        try:
            # Read existing .env file or create empty dict
            env_vars = {}
            if env_file.exists():
                try:
                    with open(env_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            # Skip empty lines and comments
                            if not line or line.startswith('#'):
                                continue
                            # Parse KEY=VALUE
                            if '=' in line:
                                key, value = line.split('=', 1)
                                env_vars[key.strip()] = value.strip()
                    logger.debug(f"Read {len(env_vars)} existing env vars from .env file")
                except Exception as e:
                    logger.warning(f"Failed to read existing .env file: {e}")
            
            # Update with new values
            updated_keys = []
            for config_key, value in updates.items():
                if config_key in env_key_mapping:
                    env_key = env_key_mapping[config_key]
                    # Convert boolean to string
                    if isinstance(value, bool):
                        env_vars[env_key] = "true" if value else "false"
                    else:
                        env_vars[env_key] = str(value)
                    updated_keys.append(env_key)
                    logger.debug(f"Updated {env_key}={env_vars[env_key]}")
            
            if not updated_keys:
                logger.warning("No AI config keys to update")
                return
            
            # Write to temporary file first, then atomically replace
            # This prevents corruption if hot reload happens during write
            temp_file = None
            try:
                # Create temp file in same directory
                temp_fd, temp_file = tempfile.mkstemp(
                    suffix='.env.tmp',
                    dir=env_file.parent,
                    text=True
                )
                
                with open(temp_fd, 'w') as f:
                    f.write("# Lens AI Configuration\n")
                    f.write("# Auto-generated from settings panel\n\n")
                    
                    # Write AI settings first
                    ai_keys = ["AI_ENABLED", "OPENAI_BASE_URL", "OPENAI_API_KEY", 
                               "OPENAI_MODEL", "OPENAI_MAX_TOKENS", "OPENAI_TEMPERATURE", 
                               "OPENAI_TIMEOUT"]
                    for key in ai_keys:
                        if key in env_vars:
                            f.write(f"{key}={env_vars[key]}\n")
                    
                    # Write other environment variables
                    f.write("\n# Other Settings\n")
                    for key, value in env_vars.items():
                        if key not in ai_keys:
                            f.write(f"{key}={value}\n")
                    
                    # Ensure all data is written to disk
                    f.flush()
                    os.fsync(temp_fd)
                
                # Atomically replace the original file
                shutil.move(temp_file, env_file)
                temp_file = None  # Don't try to delete it
                
                # Ensure the move is synced to disk
                try:
                    os.sync()
                except AttributeError:
                    # os.sync() not available on all platforms (e.g., Windows)
                    pass
                
                logger.info(f"Successfully persisted AI config to .env file (updated: {', '.join(updated_keys)})")
                
                # Verify the write by reading back
                try:
                    with open(env_file, 'r') as f:
                        content = f.read()
                        for key in updated_keys:
                            if f"{key}=" not in content:
                                logger.warning(f"Verification failed: {key} not found in .env file after write")
                            else:
                                logger.debug(f"Verified: {key} is in .env file")
                except Exception as e:
                    logger.warning(f"Failed to verify .env file write: {e}")
                    
            except PermissionError as e:
                logger.error(f"Permission denied writing to .env file: {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to write .env file: {e}", exc_info=True)
                raise
            finally:
                # Clean up temp file if it still exists
                if temp_file and Path(temp_file).exists():
                    try:
                        Path(temp_file).unlink()
                    except Exception:
                        pass
                        
        except Exception as e:
            logger.error(f"Failed to persist AI config to .env file: {e}", exc_info=True)
            raise
    
    @classmethod
    def reload_from_env(cls) -> None:
        """
        Reload configuration from environment variables.
        
        Useful after .env file is updated to ensure class variables
        reflect the latest values from disk.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Reload .env file
        load_dotenv(override=True)
        
        # Update class variables from environment
        old_enabled = cls.ENABLED
        old_api_key_set = bool(cls.API_KEY)
        
        cls.ENABLED = os.getenv("AI_ENABLED", "false").lower() == "true"
        cls.BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        cls.API_KEY = os.getenv("OPENAI_API_KEY")
        cls.MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        cls.MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        cls.TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        cls.TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "60"))
        
        logger.info(f"Reloaded AIConfig from .env - enabled={cls.ENABLED}, is_configured={cls.is_configured()}")
        if old_enabled != cls.ENABLED or old_api_key_set != bool(cls.API_KEY):
            logger.info(f"Config changed: enabled {old_enabled}->{cls.ENABLED}, api_key {'set' if old_api_key_set else 'not set'}->{'set' if cls.API_KEY else 'not set'}")
    
    @classmethod
    def update_from_dict(cls, config: Dict[str, Any], persist: bool = True) -> None:
        """
        Update configuration from dictionary.
        
        Args:
            config: Configuration dictionary
            persist: Whether to persist changes to .env file (default: True)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if "enabled" in config:
            cls.ENABLED = bool(config["enabled"])
            logger.debug(f"Updated ENABLED={cls.ENABLED}")
        
        if "base_url" in config:
            cls.BASE_URL = str(config["base_url"])
            logger.debug(f"Updated BASE_URL={cls.BASE_URL}")
        
        if "api_key" in config and config["api_key"]:
            cls.API_KEY = str(config["api_key"])
            logger.debug(f"Updated API_KEY={'set' if cls.API_KEY else 'not set'}")
        
        if "model" in config:
            cls.MODEL = str(config["model"])
            logger.debug(f"Updated MODEL={cls.MODEL}")
        
        if "max_tokens" in config:
            cls.MAX_TOKENS = int(config["max_tokens"])
            logger.debug(f"Updated MAX_TOKENS={cls.MAX_TOKENS}")
        
        if "temperature" in config:
            cls.TEMPERATURE = float(config["temperature"])
            logger.debug(f"Updated TEMPERATURE={cls.TEMPERATURE}")
        
        if "timeout" in config:
            cls.TIMEOUT = int(config["timeout"])
            logger.debug(f"Updated TIMEOUT={cls.TIMEOUT}")
        
        # Persist to .env file if requested
        if persist:
            cls._persist_to_env(config)
            # Note: Class variables are already updated above
            # The .env file is written for persistence across restarts
            # Hot reload will naturally reload from .env on next module import


class AppConfig:
    """General application configuration."""
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "34001"))
    
    # Frontend settings
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:34000")
    SERVE_FRONTEND: bool = os.getenv("SERVE_FRONTEND", "false").lower() == "true"
    
    # Logging - default to DEBUG in development, INFO in production
    _default_log_level = "DEBUG" if os.getenv("ENVIRONMENT", "development").lower() in ("development", "dev") else "INFO"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", _default_log_level)
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:34000",
        "http://127.0.0.1:34000",
        FRONTEND_URL
    ]
    
    # Enable profiling
    ENABLE_PROFILING: bool = os.getenv("ENABLE_PROFILING", "false").lower() == "true"
    
    # Valid log levels
    VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    @classmethod
    def get_log_level(cls) -> str:
        return cls.LOG_LEVEL.upper()
    
    @classmethod
    def update_log_level(cls, log_level: str, persist: bool = True) -> None:
        """
        Update log level dynamically.
        
        Args:
            log_level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            persist: Whether to persist to .env file (default: True)
        
        Raises:
            ValueError: If log level is invalid
        """
        import logging
        
        log_level = log_level.upper()
        if log_level not in cls.VALID_LOG_LEVELS:
            raise ValueError(f"Invalid log level: {log_level}. Must be one of {cls.VALID_LOG_LEVELS}")
        
        # Update class variable
        cls.LOG_LEVEL = log_level
        
        # Update root logger level
        numeric_level = getattr(logging, log_level)
        logging.getLogger().setLevel(numeric_level)
        
        # Persist to .env file if requested
        if persist:
            cls._persist_to_env({"log_level": log_level})
    
    @classmethod
    def _get_env_file_path(cls) -> Path:
        # Start from this file's location and go up to backend directory
        backend_dir = Path(__file__).parent.parent.parent
        return backend_dir / ".env"
    
    @classmethod
    def _persist_to_env(cls, updates: Dict[str, Any]) -> None:
        """
        Persist configuration updates to .env file.
        
        Args:
            updates: Dictionary of config updates to persist
        """
        env_file = cls._get_env_file_path()
        
        # Mapping of config keys to environment variable names
        env_key_mapping = {
            "log_level": "LOG_LEVEL"
        }
        
        # Read existing .env file or create empty dict
        env_vars = {}
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    # Parse KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        
        # Update with new values
        for config_key, value in updates.items():
            if config_key in env_key_mapping:
                env_key = env_key_mapping[config_key]
                env_vars[env_key] = str(value)
        
        # Write back to .env file
        with open(env_file, 'w') as f:
            f.write("# Lens Configuration\n")
            f.write("# Auto-generated from settings panel\n\n")
            
            # Write AI settings first
            ai_keys = ["AI_ENABLED", "OPENAI_BASE_URL", "OPENAI_API_KEY", 
                       "OPENAI_MODEL", "OPENAI_MAX_TOKENS", "OPENAI_TEMPERATURE", 
                       "OPENAI_TIMEOUT"]
            has_ai_settings = any(key in env_vars for key in ai_keys)
            if has_ai_settings:
                f.write("# AI Configuration\n")
                for key in ai_keys:
                    if key in env_vars:
                        f.write(f"{key}={env_vars[key]}\n")
                f.write("\n")
            
            # Write logging settings
            if "LOG_LEVEL" in env_vars:
                f.write("# Logging Configuration\n")
                f.write(f"LOG_LEVEL={env_vars['LOG_LEVEL']}\n")
                f.write("\n")
            
            # Write other environment variables
            other_keys = [k for k in env_vars.keys() if k not in ai_keys and k != "LOG_LEVEL"]
            if other_keys:
                f.write("# Other Settings\n")
                for key in other_keys:
                    f.write(f"{key}={env_vars[key]}\n")


# Export config classes
__all__ = ["AIConfig", "AppConfig"]

