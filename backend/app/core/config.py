"""Configuration settings for the Lens application."""

import os
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
        """Check if AI is properly configured."""
        return bool(cls.API_KEY) and cls.ENABLED
    
    @classmethod
    def to_dict(cls, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Args:
            include_sensitive: Whether to include sensitive data (API key)
        
        Returns:
            Configuration as dictionary
        """
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
    def update_from_dict(cls, config: Dict[str, Any]) -> None:
        """
        Update configuration from dictionary.
        
        Note: This updates runtime config, not environment variables.
        For persistent changes, update .env file.
        
        Args:
            config: Configuration dictionary
        """
        if "enabled" in config:
            cls.ENABLED = bool(config["enabled"])
        
        if "base_url" in config:
            cls.BASE_URL = str(config["base_url"])
        
        if "api_key" in config and config["api_key"]:
            cls.API_KEY = str(config["api_key"])
        
        if "model" in config:
            cls.MODEL = str(config["model"])
        
        if "max_tokens" in config:
            cls.MAX_TOKENS = int(config["max_tokens"])
        
        if "temperature" in config:
            cls.TEMPERATURE = float(config["temperature"])
        
        if "timeout" in config:
            cls.TIMEOUT = int(config["timeout"])


class AppConfig:
    """General application configuration."""
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "34001"))
    
    # Frontend settings
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:34000")
    SERVE_FRONTEND: bool = os.getenv("SERVE_FRONTEND", "false").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:34000",
        "http://127.0.0.1:34000",
        FRONTEND_URL
    ]
    
    # Enable profiling
    ENABLE_PROFILING: bool = os.getenv("ENABLE_PROFILING", "false").lower() == "true"


# Export config classes
__all__ = ["AIConfig", "AppConfig"]

