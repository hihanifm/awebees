"""Base interface for insights."""

from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Awaitable
import asyncio
from app.core.models import InsightResult, ProgressEvent


class Insight(ABC):
    """Base class for all insights."""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for this insight."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Display name for this insight."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this insight does."""
        pass
    
    @abstractmethod
    async def analyze(
        self,
        file_paths: List[str],
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> InsightResult:
        """
        Analyze the provided log files.
        
        Args:
            file_paths: List of file paths to analyze
            cancellation_event: Optional asyncio.Event to check for cancellation
            progress_callback: Optional async callback to emit progress events
            
        Returns:
            InsightResult with the analysis results
            
        Raises:
            CancelledError: If the operation is cancelled
        
        """
        pass
    
    @property
    def ai_enabled(self) -> bool:
        """
        Whether AI processing is supported for this insight.
        
        Returns:
            True if AI can analyze this insight's results (default: True)
        """
        return True
    
    @property
    def ai_auto(self) -> bool:
        """
        Whether to automatically trigger AI after analysis.
        
        Returns:
            True to auto-trigger AI, False for manual only (default: False)
        """
        return False
    
    @property
    def ai_prompt_type(self) -> str:
        """
        Default AI prompt type for this insight.
        
        Returns:
            One of: "summarize", "explain", "recommend", "custom" (default: "explain")
        """
        return "explain"
    
    @property
    def ai_custom_prompt(self) -> Optional[str]:
        """
        Custom AI prompt for this insight (if ai_prompt_type is "custom").
        
        Returns:
            Custom prompt string or None
        """
        return None
    
    @property
    def ai_prompt_variables(self) -> Optional[dict]:
        """
        Variables for AI prompt substitution.
        
        Returns:
            Dictionary of variables or None
        """
        return None
    
    async def analyze_with_ai(
        self,
        file_paths: List[str],
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> InsightResult:
        """
        Analyze files and optionally trigger AI analysis.
        
        This is a wrapper around analyze() that:
        - Calls analyze() to get filtered results  
        - If ai_auto is true, automatically calls AI analysis
        - Returns InsightResult with ai_analysis field populated
        
        Args:
            file_paths: List of file paths to analyze
            cancellation_event: Optional asyncio.Event to check for cancellation
            progress_callback: Optional async callback to emit progress events
            
        Returns:
            InsightResult with analysis results and optional AI analysis
        """
        # Call regular analyze
        result = await self.analyze(file_paths, cancellation_event, progress_callback)
        
        # Set AI metadata on result
        result.ai_enabled = self.ai_enabled
        result.ai_auto = self.ai_auto
        result.ai_prompt_type = self.ai_prompt_type
        result.ai_custom_prompt = self.ai_custom_prompt
        
        # Check if AI should auto-run
        if self.ai_auto and self.ai_enabled:
            from app.services.ai_service import AIService
            from app.core.config import AIConfig
            
            if AIConfig.is_configured():
                try:
                    ai_service = AIService()
                    
                    # Run AI analysis
                    ai_result = await ai_service.analyze(
                        content=result.content,
                        prompt_type=self.ai_prompt_type,
                        custom_prompt=self.ai_custom_prompt
                    )
                    
                    # Add to result
                    result.ai_analysis = ai_result
                except Exception as e:
                    # Log error but don't fail the entire analysis
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"AI auto-analysis failed: {e}")
        
        return result