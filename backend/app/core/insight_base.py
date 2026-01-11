"""Base interface for insights."""

from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Awaitable
import asyncio
import logging
from pathlib import Path
from app.core.models import InsightResult, ProgressEvent

logger = logging.getLogger(__name__)


class Insight(ABC):
    """Base class for all insights."""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for this insight (auto-generated from file path)."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @abstractmethod
    async def analyze(
        self,
        user_path: str,
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> InsightResult:
        pass
    
    def _get_path_files(self, user_path: str) -> List[str]:
        """
        Get files for a single user path (if folder, list recursively; if file, use directly).
        
        Args:
            user_path: User input path (file or folder)
            
        Returns:
            List of file paths
        """
        path_obj = Path(user_path)
        if not path_obj.exists():
            logger.warning(f"{self.__class__.__name__}: Path does not exist: {user_path}")
            return []
        
        if path_obj.is_file():
            return [str(path_obj.resolve())]
        elif path_obj.is_dir():
            files = [str(p.resolve()) for p in path_obj.rglob("*") if p.is_file()]
            return sorted(files)
        else:
            return []
    
    @property
    def ai_enabled(self) -> bool: return True
    
    @property
    def ai_auto(self) -> bool: return False
    
    @property
    def ai_prompt_type(self) -> str:
        # One of: "summarize", "explain", "recommend", "custom" (default: "explain")
        return "explain"
    
    @property
    def ai_custom_prompt(self) -> Optional[str]: return None
    
    @property
    def ai_prompt_variables(self) -> Optional[dict]: return None
    
    async def analyze_with_ai(
        self,
        user_path: str,
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> InsightResult:
        """
        Wrapper around analyze() that automatically triggers AI analysis if ai_auto is True.
        """
        # Call regular analyze
        result = await self.analyze(user_path, cancellation_event, progress_callback)
        
        # Set AI metadata on result
        result.ai_enabled = self.ai_enabled
        result.ai_auto = self.ai_auto
        result.ai_prompt_type = self.ai_prompt_type
        result.ai_custom_prompt = self.ai_custom_prompt
        
        # Check if AI should auto-run
        if self.ai_auto and self.ai_enabled:
            logger.info(f"AI Auto-trigger: Checking if AI should auto-run for insight (ai_auto={self.ai_auto}, ai_enabled={self.ai_enabled})")
            
            from app.services.ai_service import AIService
            from app.core.config import AIConfig
            
            logger.info(f"AI Auto-trigger: AIConfig.is_configured()={AIConfig.is_configured()}, ENABLED={AIConfig.ENABLED}, API_KEY={'set' if AIConfig.API_KEY else 'not set'}")
            
            if AIConfig.is_configured():
                try:
                    logger.info(f"AI Auto-trigger: Starting auto-analysis with prompt_type={self.ai_prompt_type}")
                    ai_service = AIService()
                    
                    # Run AI analysis
                    ai_result = await ai_service.analyze(
                        content=result.content,
                        prompt_type=self.ai_prompt_type,
                        custom_prompt=self.ai_custom_prompt
                    )
                    
                    # Add to result
                    result.ai_analysis = ai_result
                    logger.info(f"AI Auto-trigger: Auto-analysis completed successfully")
                except Exception as e:
                    # Log error but don't fail the entire analysis
                    # Store error message so frontend can display it
                    error_msg = str(e)
                    result.ai_analysis_error = error_msg
                    logger.warning(f"AI auto-analysis failed: {error_msg}", exc_info=True)
            else:
                logger.warning(f"AI Auto-trigger: AI is not configured - skipping auto-analysis")
                result.ai_analysis_error = "AI is not configured. Please enable AI in settings."
        
        return result