import os
from typing import Dict, Any, Optional
from app.utils.env_persistence import update_env_file

# Module-level AIConfigsManager instance (singleton pattern)
_manager_instance = None

def _get_manager():
    """Get or create AIConfigsManager instance."""
    global _manager_instance
    if _manager_instance is None:
        from app.core.ai_configs_manager import AIConfigsManager
        _manager_instance = AIConfigsManager()
    return _manager_instance


class AIConfig:
    """AI configuration that reads from AIConfigsManager."""
    
    # Class variables (updated from manager)
    ENABLED: bool = False
    BASE_URL: str = "https://api.openai.com/v1"
    API_KEY: Optional[str] = None
    MODEL: str = "gpt-4o-mini"
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.7
    TIMEOUT: int = 60
    DETAILED_LOGGING: bool = os.getenv("AI_DETAILED_LOGGING", "true").lower() in ("true", "1", "yes")
    STREAMING_ENABLED: bool = True
    
    @classmethod
    def _update_from_manager(cls) -> None:
        """Update class variables from manager."""
        manager = _get_manager()
        # Get active config from the configs dict
        active_config_name = manager.get_active_config_name()
        active_config = None
        if active_config_name and active_config_name in manager._configs:
            active_config = manager._configs[active_config_name]
        
        if active_config:
            cls.ENABLED = active_config.get("enabled", False)
            cls.BASE_URL = active_config.get("base_url", "https://api.openai.com/v1")
            cls.API_KEY = active_config.get("api_key")
            model = active_config.get("model", "gpt-4o-mini")
            cls.MODEL = model.strip() if model else "gpt-4o-mini"
            cls.MAX_TOKENS = active_config.get("max_tokens", 2000)
            cls.TEMPERATURE = active_config.get("temperature", 0.7)
            cls.TIMEOUT = active_config.get("timeout", 60)
            cls.STREAMING_ENABLED = active_config.get("streaming_enabled", True)
        else:
            # Use defaults if no active config
            cls.ENABLED = False
            cls.BASE_URL = "https://api.openai.com/v1"
            cls.API_KEY = None
            cls.MODEL = "gpt-4o-mini"
            cls.MAX_TOKENS = 2000
            cls.TEMPERATURE = 0.7
            cls.TIMEOUT = 60
            cls.STREAMING_ENABLED = True
    
    
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
        """Check if AI is configured (has API key and is enabled)."""
        return bool(cls.API_KEY) and cls.ENABLED
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert AIConfig to dictionary. API keys are included as-is (no masking)."""
        return {
            "enabled": cls.ENABLED,
            "base_url": cls.BASE_URL,
            "api_key": cls.API_KEY,
            "model": cls.MODEL,
            "max_tokens": cls.MAX_TOKENS,
            "temperature": cls.TEMPERATURE,
            "timeout": cls.TIMEOUT,
            "detailed_logging": cls.DETAILED_LOGGING,
            "streaming_enabled": cls.STREAMING_ENABLED,
            "is_configured": cls.is_configured()
        }
    
    @classmethod
    def reload(cls) -> None:
        """Reload configuration from JSON file."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Reload manager to get fresh data
        global _manager_instance
        _manager_instance = None
        manager = _get_manager()
        manager.load()
        
        # Update class variables from manager
        cls._update_from_manager()
        
        logger.info(f"Reloaded AIConfig from JSON - enabled={cls.ENABLED}, model={cls.MODEL}, is_configured={cls.is_configured()}")
    
    @classmethod
    def update_from_dict(cls, config: Dict[str, Any], persist: bool = True) -> None:
        """Update active config from dictionary."""
        import logging
        logger = logging.getLogger(__name__)
        
        manager = _get_manager()
        active_name = manager.get_active_config_name()
        
        if not active_name:
            raise ValueError("No active config name found.")
        
        # Get active config from the configs dict
        active_config = None
        if active_name in manager._configs:
            active_config = manager._configs[active_name]
        
        if not active_config:
            raise ValueError("No active config found. Please create or activate a config first.")
        
        # Log current values before update
        logger.info(f"AIConfig.update_from_dict: Current values - MODEL={cls.MODEL}, BASE_URL={cls.BASE_URL}, ENABLED={cls.ENABLED}, MAX_TOKENS={cls.MAX_TOKENS}, TEMPERATURE={cls.TEMPERATURE}")
        logger.info(f"AIConfig.update_from_dict: Updating active config '{active_name}' with - {config}")
        
        # Merge updates into active config
        updated_config = active_config.copy()
        for key, value in config.items():
            if value is not None:  # Only update non-None values
                if key == "model" and isinstance(value, str):
                    value = value.strip()
                    if not value:
                        value = "gpt-4o-mini"
                updated_config[key] = value
        
        # Ensure name is preserved
        updated_config["name"] = active_name
        
        # Update the config
        if persist:
            manager.update_config(active_name, active_name, updated_config)
            logger.info(f"AIConfig.update_from_dict: Updated active config '{active_name}' in JSON")
            
            # Reload to get fresh values
            cls.reload()
            
            logger.info(f"AIConfig.update_from_dict: Final values - MODEL={cls.MODEL}, BASE_URL={cls.BASE_URL}, ENABLED={cls.ENABLED}, MAX_TOKENS={cls.MAX_TOKENS}, TEMPERATURE={cls.TEMPERATURE}")


class AppConfig:
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "34001"))
    
    # Frontend settings
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:34000")
    SERVE_FRONTEND: bool = os.getenv("SERVE_FRONTEND", "false").lower() == "true"
    
    # Logging - default to DEBUG for now (even in production)
    # Can be overridden with LOG_LEVEL env var (e.g., LOG_LEVEL=INFO to reduce verbosity)
    _default_log_level = "DEBUG"  # Always DEBUG for now
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", _default_log_level)
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:34000",
        "http://127.0.0.1:34000",
        FRONTEND_URL
    ]
    
    # Enable profiling
    ENABLE_PROFILING: bool = os.getenv("ENABLE_PROFILING", "false").lower() == "true"
    
    # HTTP request/response logging (logs all HTTP requests and responses)
    HTTP_LOGGING: bool = os.getenv("HTTP_LOGGING", "true").lower() in ("true", "1", "yes")
    
    # Insight file limit - maximum number of files allowed per insight analysis
    MAX_FILES: int = int(os.getenv("INSIGHT_MAX_FILES", "20"))
    
    # Result display limit - maximum number of lines to display in result windows (in-memory only)
    RESULT_MAX_LINES: int = 500
    
    # Valid log levels
    VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    @classmethod
    def get_log_level(cls) -> str: return cls.LOG_LEVEL.upper()
    
    @classmethod
    def update_log_level(cls, log_level: str, persist: bool = True) -> None:
        # Valid log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
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
    def get_result_max_lines(cls) -> int:
        """Get the current result max lines limit."""
        return cls.RESULT_MAX_LINES
    
    @classmethod
    def set_result_max_lines(cls, value: int) -> None:
        """Set the result max lines limit (in-memory only, no persistence)."""
        import logging
        logger = logging.getLogger(__name__)
        
        if value < 1:
            raise ValueError("Result max lines must be at least 1")
        if value > 100000:
            raise ValueError("Result max lines cannot exceed 100000")
        
        old_value = cls.RESULT_MAX_LINES
        cls.RESULT_MAX_LINES = value
        logger.info(f"Updated RESULT_MAX_LINES: {old_value} -> {value}")
    
    @classmethod
    def _persist_to_env(cls, updates: Dict[str, Any]) -> None:
        key_mapping = {
            "log_level": "LOG_LEVEL"
        }
        update_env_file(updates, key_mapping)


class ZipSecurityConfig:
    """Configuration for zip file security and extraction limits."""
    
    # Size limits (in bytes, converted from MB/GB)
    MAX_FILE_SIZE: int = int(os.getenv("ZIP_MAX_FILE_SIZE", str(500 * 1024 * 1024)))  # 500 MB default
    MAX_TOTAL_SIZE: int = int(os.getenv("ZIP_MAX_TOTAL_SIZE", str(5 * 1024 * 1024 * 1024)))  # 5 GB default
    
    # Other limits
    MAX_COMPRESSION_RATIO: int = int(os.getenv("ZIP_MAX_COMPRESSION_RATIO", "1000"))
    MAX_RECURSION_DEPTH: int = int(os.getenv("ZIP_MAX_RECURSION_DEPTH", "3"))
    MAX_FILES: int = int(os.getenv("ZIP_MAX_FILES", "1000"))
    
    @classmethod
    def reload_from_env(cls) -> None:
        """Reload configuration from environment variables."""
        import logging
        from dotenv import load_dotenv
        logger = logging.getLogger(__name__)
        
        load_dotenv(override=True)
        
        cls.MAX_FILE_SIZE = int(os.getenv("ZIP_MAX_FILE_SIZE", str(500 * 1024 * 1024)))
        cls.MAX_TOTAL_SIZE = int(os.getenv("ZIP_MAX_TOTAL_SIZE", str(5 * 1024 * 1024 * 1024)))
        cls.MAX_COMPRESSION_RATIO = int(os.getenv("ZIP_MAX_COMPRESSION_RATIO", "1000"))
        cls.MAX_RECURSION_DEPTH = int(os.getenv("ZIP_MAX_RECURSION_DEPTH", "3"))
        cls.MAX_FILES = int(os.getenv("ZIP_MAX_FILES", "1000"))
        
        logger.debug(f"Reloaded ZipSecurityConfig from .env - MAX_FILE_SIZE={cls.MAX_FILE_SIZE / (1024*1024):.0f}MB, MAX_TOTAL_SIZE={cls.MAX_TOTAL_SIZE / (1024*1024*1024):.0f}GB")


class SafeModeConfig:
    """Configuration for safe mode - prevents loading external insights and samples."""
    
    # Read from environment variable on startup
    ENABLED: bool = os.getenv("SAFE_MODE", "false").lower() in ("true", "1", "yes")
    FROM_ENV: bool = os.getenv("SAFE_MODE", "false").lower() in ("true", "1", "yes")
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if safe mode is currently enabled."""
        return cls.ENABLED
    
    @classmethod
    def start(cls) -> None:
        """Set safe mode enabled (in-memory only, requires restart to take effect)."""
        import logging
        logger = logging.getLogger(__name__)
        cls.ENABLED = True
        logger.info("Safe mode enabled (in-memory). Restart required for changes to take effect.")
    
    @classmethod
    def stop(cls) -> None:
        """Set safe mode disabled (in-memory only, requires restart to take effect)."""
        import logging
        logger = logging.getLogger(__name__)
        cls.ENABLED = False
        logger.info("Safe mode disabled (in-memory). Restart required for changes to take effect.")


# Initialize AIConfig from manager when module is imported
AIConfig._update_from_manager()

# Export config classes
__all__ = ["AIConfig", "AppConfig", "ZipSecurityConfig", "SafeModeConfig"]

