import os
from typing import Dict, Any, Optional
from app.utils.env_persistence import update_env_file


class AIConfig:
    
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
    def is_configured(cls) -> bool: return bool(cls.API_KEY) and cls.ENABLED
    
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
    def _persist_to_env(cls, updates: Dict[str, Any]) -> None:
        key_mapping = {
            "enabled": "AI_ENABLED",
            "base_url": "OPENAI_BASE_URL",
            "api_key": "OPENAI_API_KEY",
            "model": "OPENAI_MODEL",
            "max_tokens": "OPENAI_MAX_TOKENS",
            "temperature": "OPENAI_TEMPERATURE",
            "timeout": "OPENAI_TIMEOUT"
        }
        update_env_file(updates, key_mapping)
    
    @classmethod
    def reload_from_env(cls) -> None:
        import logging
        from dotenv import load_dotenv
        logger = logging.getLogger(__name__)
        
        load_dotenv(override=True)
        
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
        
        if persist:
            cls._persist_to_env(config)


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


# Export config classes
__all__ = ["AIConfig", "AppConfig", "ZipSecurityConfig", "SafeModeConfig"]

