import os
from typing import Dict, Any, Optional

# Module-level AIConfigsManager instance (singleton pattern)
_manager_instance = None

def _get_manager():
    """Get or create AIConfigsManager instance."""
    global _manager_instance
    if _manager_instance is None:
        from app.core.ai_configs_manager import AIConfigsManager
        _manager_instance = AIConfigsManager()
    return _manager_instance

# Module-level AppConfigManager instance (singleton pattern)
_app_config_manager_instance = None

def _get_app_config_manager():
    """Get or create AppConfigManager instance."""
    global _app_config_manager_instance
    if _app_config_manager_instance is None:
        from app.core.app_config_manager import AppConfigManager
        _app_config_manager_instance = AppConfigManager()
    return _app_config_manager_instance


class AIConfig:
    """AI configuration that reads from AIConfigsManager."""
    
    # Class variables (updated from manager)
    # Note: ENABLED removed - use global AppConfig.AI_PROCESSING_ENABLED instead
    BASE_URL: str = "https://api.openai.com/v1"
    API_KEY: Optional[str] = None
    MODEL: str = "gpt-4o-mini"
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.7
    TIMEOUT: int = 60
    # Note: DETAILED_LOGGING moved to AppConfig - use AppConfig.get_detailed_logging() instead
    DETAILED_LOGGING: bool = True  # Will be synced from AppConfig
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
            # Note: ENABLED is no longer part of configs - use global AppConfig.AI_PROCESSING_ENABLED
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
            cls.BASE_URL = "https://api.openai.com/v1"
            cls.API_KEY = None
            cls.MODEL = "gpt-4o-mini"
            cls.MAX_TOKENS = 2000
            cls.TEMPERATURE = 0.7
            cls.TIMEOUT = 60
            cls.STREAMING_ENABLED = True
        
        # Always sync DETAILED_LOGGING from AppConfig (regardless of active config)
        cls.DETAILED_LOGGING = AppConfig.get_detailed_logging()
    
    
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
        """Check if AI is configured (has API key and AI processing is globally enabled)."""
        from app.core.config import AppConfig
        # Ensure AppConfig is initialized to load from config.json
        AppConfig._initialize()
        return bool(cls.API_KEY) and AppConfig.get_ai_processing_enabled()
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert AIConfig to dictionary. API keys are included as-is (no masking)."""
        from app.core.config import AppConfig
        return {
            "base_url": cls.BASE_URL,
            "api_key": cls.API_KEY,
            "model": cls.MODEL,
            "max_tokens": cls.MAX_TOKENS,
            "temperature": cls.TEMPERATURE,
            "timeout": cls.TIMEOUT,
            "detailed_logging": cls.DETAILED_LOGGING,
            "streaming_enabled": cls.STREAMING_ENABLED,
            "is_configured": cls.is_configured(),
            # Note: enabled is now a global setting (AppConfig.AI_PROCESSING_ENABLED)
            "ai_processing_enabled": AppConfig.get_ai_processing_enabled()
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
        
        from app.core.config import AppConfig
        logger.info(f"Reloaded AIConfig from JSON - ai_processing_enabled={AppConfig.get_ai_processing_enabled()}, model={cls.MODEL}, is_configured={cls.is_configured()}")
    
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
        from app.core.config import AppConfig
        logger.info(f"AIConfig.update_from_dict: Current values - MODEL={cls.MODEL}, BASE_URL={cls.BASE_URL}, AI_PROCESSING_ENABLED={AppConfig.get_ai_processing_enabled()}, MAX_TOKENS={cls.MAX_TOKENS}, TEMPERATURE={cls.TEMPERATURE}")
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
            
            from app.core.config import AppConfig
            logger.info(f"AIConfig.update_from_dict: Final values - MODEL={cls.MODEL}, BASE_URL={cls.BASE_URL}, AI_PROCESSING_ENABLED={AppConfig.get_ai_processing_enabled()}, MAX_TOKENS={cls.MAX_TOKENS}, TEMPERATURE={cls.TEMPERATURE}")


class AppConfig:
    """
    Application configuration.
    
    Settings are loaded from ~/.lensai/config.json (user settings) with fallback to .env (build-time defaults).
    User-modifiable settings are persisted to config.json, not .env.
    """
    
    # Server settings (read-only from .env)
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "34001"))
    
    # Frontend settings (read-only from .env)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:34000")
    SERVE_FRONTEND: bool = os.getenv("SERVE_FRONTEND", "false").lower() == "true"
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:34000",
        "http://127.0.0.1:34000",
        FRONTEND_URL
    ]
    
    # Enable profiling (read-only from .env)
    ENABLE_PROFILING: bool = os.getenv("ENABLE_PROFILING", "false").lower() == "true"
    
    # Insight file limit (read-only from .env)
    MAX_FILES: int = int(os.getenv("INSIGHT_MAX_FILES", "20"))
    
    # User-modifiable settings (loaded from config.json, fallback to .env defaults)
    _default_log_level = "DEBUG"
    LOG_LEVEL: str = _default_log_level
    HTTP_LOGGING: bool = True
    AI_PROCESSING_ENABLED: bool = True
    RESULT_MAX_LINES: int = 500
    
    # Valid log levels
    VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    _initialized: bool = False
    
    @classmethod
    def _initialize(cls) -> None:
        """Initialize AppConfig by loading from config.json (with .env fallback)."""
        if cls._initialized:
            return
        
        import logging
        logger = logging.getLogger(__name__)
        
        # Get config manager
        manager = _get_app_config_manager()
        
        # Load settings from config.json (with .env fallback for defaults)
        cls.LOG_LEVEL = manager.get("log_level", os.getenv("LOG_LEVEL", cls._default_log_level))
        cls.HTTP_LOGGING = manager.get("http_logging", os.getenv("HTTP_LOGGING", "true").lower() in ("true", "1", "yes"))
        cls.AI_PROCESSING_ENABLED = manager.get("ai_processing_enabled", os.getenv("AI_PROCESSING_ENABLED", "true").lower() in ("true", "1", "yes"))
        cls.RESULT_MAX_LINES = manager.get("result_max_lines", 500)
        cls.DETAILED_LOGGING = manager.get("detailed_logging", os.getenv("AI_DETAILED_LOGGING", "true").lower() in ("true", "1", "yes"))
        
        # Apply log level immediately
        numeric_level = getattr(logging, cls.LOG_LEVEL.upper(), logging.DEBUG)
        logging.getLogger().setLevel(numeric_level)
        
        logger.info(f"AppConfig._initialize(): Loaded from config.json - LOG_LEVEL={cls.LOG_LEVEL}, HTTP_LOGGING={cls.HTTP_LOGGING}, AI_PROCESSING_ENABLED={cls.AI_PROCESSING_ENABLED}, RESULT_MAX_LINES={cls.RESULT_MAX_LINES}, DETAILED_LOGGING={cls.DETAILED_LOGGING}")
        
        cls._initialized = True
    
    @classmethod
    def get_log_level(cls) -> str:
        cls._initialize()
        return cls.LOG_LEVEL.upper()
    
    @classmethod
    def update_log_level(cls, log_level: str, persist: bool = True) -> None:
        """Update log level and persist to config.json."""
        cls._initialize()
        import logging
        
        log_level = log_level.upper()
        if log_level not in cls.VALID_LOG_LEVELS:
            raise ValueError(f"Invalid log level: {log_level}. Must be one of {cls.VALID_LOG_LEVELS}")
        
        # Update class variable
        cls.LOG_LEVEL = log_level
        
        # Update root logger level
        numeric_level = getattr(logging, log_level)
        logging.getLogger().setLevel(numeric_level)
        
        # Persist to config.json if requested
        if persist:
            manager = _get_app_config_manager()
            manager.set("log_level", log_level, save=True)
    
    @classmethod
    def get_result_max_lines(cls) -> int:
        """Get the current result max lines limit."""
        cls._initialize()
        return cls.RESULT_MAX_LINES
    
    @classmethod
    def get_detailed_logging(cls) -> bool:
        """Get AI detailed logging setting."""
        cls._initialize()
        return cls.DETAILED_LOGGING
    
    @classmethod
    def set_detailed_logging(cls, enabled: bool, persist: bool = True) -> None:
        """Set AI detailed logging and persist to config.json."""
        cls._initialize()
        import logging
        logger = logging.getLogger(__name__)
        old_value = cls.DETAILED_LOGGING
        
        # Update class variable
        cls.DETAILED_LOGGING = enabled
        
        # Also update AIConfig for backward compatibility
        AIConfig.DETAILED_LOGGING = enabled
        
        # Persist to config.json if requested
        if persist:
            manager = _get_app_config_manager()
            manager.set("detailed_logging", enabled, save=True)
        
        logger.info(f"Updated DETAILED_LOGGING: {old_value} -> {enabled}")
    
    @classmethod
    def set_result_max_lines(cls, value: int) -> None:
        """Set the result max lines limit and persist to config.json."""
        cls._initialize()
        import logging
        logger = logging.getLogger(__name__)
        
        if value < 1:
            raise ValueError("Result max lines must be at least 1")
        if value > 100000:
            raise ValueError("Result max lines cannot exceed 100000")
        
        old_value = cls.RESULT_MAX_LINES
        cls.RESULT_MAX_LINES = value
        
        # Persist to config.json
        manager = _get_app_config_manager()
        manager.set("result_max_lines", value, save=True)
        
        logger.info(f"Updated RESULT_MAX_LINES: {old_value} -> {value}")
    
    @classmethod
    def set_ai_processing_enabled(cls, enabled: bool) -> None:
        """Set AI processing enabled (global setting) and persist to config.json."""
        cls._initialize()
        import logging
        logger = logging.getLogger(__name__)
        old_value = cls.AI_PROCESSING_ENABLED
        cls.AI_PROCESSING_ENABLED = enabled
        
        # Persist to config.json
        manager = _get_app_config_manager()
        manager.set("ai_processing_enabled", enabled, save=True)
        
        logger.info(f"Updated AI_PROCESSING_ENABLED: {old_value} -> {enabled}")
    
    @classmethod
    def get_ai_processing_enabled(cls) -> bool:
        """Get AI processing enabled (global setting)."""
        cls._initialize()
        return cls.AI_PROCESSING_ENABLED
    
    @classmethod
    def get_http_logging(cls) -> bool:
        """Get HTTP logging setting."""
        cls._initialize()
        return cls.HTTP_LOGGING
    
    @classmethod
    def set_http_logging(cls, enabled: bool) -> None:
        """Set HTTP logging and persist to config.json."""
        cls._initialize()
        import logging
        logger = logging.getLogger(__name__)
        old_value = cls.HTTP_LOGGING
        cls.HTTP_LOGGING = enabled
        
        # Persist to config.json
        manager = _get_app_config_manager()
        manager.set("http_logging", enabled, save=True)
        
        logger.info(f"Updated HTTP_LOGGING: {old_value} -> {enabled}")


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

