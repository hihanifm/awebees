"""Base interface for insights."""

from abc import ABC, abstractmethod
from typing import List
from app.core.models import InsightResult


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
    async def analyze(self, file_paths: List[str]) -> InsightResult:
        """
        Analyze the provided log files.
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            InsightResult with the analysis results
        """
        pass

