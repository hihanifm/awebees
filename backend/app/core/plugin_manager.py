"""Plugin manager for discovering and registering insights."""

import importlib
import inspect
import os
from pathlib import Path
from typing import Dict, List
import logging

from app.insights.base import Insight
from app.core.models import InsightMetadata

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages insight plugins by discovering and registering them."""
    
    def __init__(self):
        self._insights: Dict[str, Insight] = {}
        self._insight_folders: Dict[str, str] = {}  # Maps insight_id to folder name
    
    def discover_insights(self, insights_dir: str = None) -> None:
        """
        Discover and register all insights in the insights directory (recursively).
        
        Args:
            insights_dir: Path to insights directory (defaults to app/insights)
        """
        if insights_dir is None:
            # Get the insights directory relative to this file
            current_dir = Path(__file__).parent.parent
            insights_dir = str(current_dir / "insights")
        
        insights_path = Path(insights_dir)
        if not insights_path.exists():
            logger.warning(f"Insights directory not found: {insights_dir}")
            return
        
        # Recursively discover insights in root and subdirectories
        self._discover_insights_recursive(insights_path, insights_path)
    
    def _discover_insights_recursive(self, root_path: Path, current_path: Path) -> None:
        """
        Recursively discover insights in a directory and its subdirectories.
        
        Args:
            root_path: Root insights directory path
            current_path: Current directory being scanned
        """
        # Get all Python files in current directory (except __init__.py and base.py)
        python_files = [
            f for f in current_path.iterdir()
            if f.is_file() and f.suffix == ".py" 
            and f.stem != "__init__" and f.stem != "base"
        ]
        
        # Determine folder name (relative to root_path)
        if current_path == root_path:
            folder_name = None  # Root-level insights have no folder
        else:
            # Get relative path from root, use first component as folder name
            relative_path = current_path.relative_to(root_path)
            folder_name = str(relative_path.parts[0]) if relative_path.parts else None
        
        # Process Python files in current directory
        for file_path in python_files:
            try:
                # Build module name based on folder structure
                if folder_name is None:
                    # Root-level: app.insights.{file_stem}
                    module_name = f"app.insights.{file_path.stem}"
                else:
                    # Nested: app.insights.{folder_name}.{file_stem}
                    module_name = f"app.insights.{folder_name}.{file_path.stem}"
                
                module = importlib.import_module(module_name)
                
                # Find all Insight subclasses in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, Insight) and 
                        obj is not Insight and 
                        obj.__module__ == module_name):
                        try:
                            instance = obj()
                            self.register_insight(instance, folder_name)
                            logger.info(f"Registered insight: {instance.id} ({instance.name}) in folder: {folder_name or 'root'}")
                        except Exception as e:
                            logger.error(f"Failed to instantiate insight {name}: {e}")
            except Exception as e:
                logger.error(f"Failed to import module {file_path.stem}: {e}")
        
        # Recursively process subdirectories
        subdirs = [d for d in current_path.iterdir() if d.is_dir() and not d.name.startswith('__')]
        for subdir in subdirs:
            self._discover_insights_recursive(root_path, subdir)
    
    def register_insight(self, insight: Insight, folder: str = None) -> None:
        """
        Register an insight instance.
        
        Args:
            insight: Insight instance to register
            folder: Folder name where the insight is located (None for root-level)
        """
        if insight.id in self._insights:
            logger.warning(f"Insight {insight.id} is already registered, overwriting")
        self._insights[insight.id] = insight
        self._insight_folders[insight.id] = folder
    
    def get_insight(self, insight_id: str) -> Insight:
        """
        Get an insight by ID.
        
        Args:
            insight_id: Unique identifier of the insight
            
        Returns:
            Insight instance
            
        Raises:
            KeyError: If insight not found
        """
        if insight_id not in self._insights:
            raise KeyError(f"Insight not found: {insight_id}")
        return self._insights[insight_id]
    
    def list_insights(self) -> List[InsightMetadata]:
        """
        Get metadata for all registered insights.
        
        Returns:
            List of insight metadata with folder information
        """
        return [
            InsightMetadata(
                id=insight.id,
                name=insight.name,
                description=insight.description,
                folder=self._insight_folders.get(insight.id)
            )
            for insight in self._insights.values()
        ]
    
    def get_all_insights(self) -> Dict[str, Insight]:
        """Get all registered insights as a dictionary."""
        return self._insights.copy()


# Global plugin manager instance
_plugin_manager: PluginManager = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager

