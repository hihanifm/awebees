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
