"""Plugin manager for discovering and registering insights."""

import importlib
import importlib.util
import inspect
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import logging

from app.core.insight_base import Insight
from app.core.config_insight import ConfigBasedInsight
from app.core.models import InsightMetadata, ErrorEvent

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages insight plugins by discovering and registering them."""
    
    def __init__(self):
        self._insights: Dict[str, Insight] = {}
        self._insight_folders: Dict[str, str] = {}  # Maps insight_id to folder name
        self._insight_sources: Dict[str, str] = {}  # Maps insight_id to source path
        self._errors: List[ErrorEvent] = []  # Track errors during discovery
        self._external_paths: List[str] = []  # External insight paths
    
    def discover_insights(self, insights_dir: str = None) -> None:
        """
        Discover and register all insights in the insights directory (recursively).
        Legacy method for backward compatibility.
        
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
        self._discover_insights_recursive(insights_path, insights_path, source="built-in")
    
    def discover_all_insights(self) -> None:
        """Discover insights from built-in and all external paths."""
        # Clear existing insights
        self._insights.clear()
        self._insight_folders.clear()
        self._insight_sources.clear()
        self._errors.clear()
        
        # Discover built-in insights
        logger.info("Discovering built-in insights...")
        current_dir = Path(__file__).parent.parent
        insights_dir = current_dir / "insights"
        
        if insights_dir.exists():
            self._discover_insights_recursive(insights_dir, insights_dir, source="built-in")
        else:
            logger.warning(f"Built-in insights directory not found: {insights_dir}")
        
        # Discover external insights
        from app.core.insight_paths_config import InsightPathsConfig
        paths_config = InsightPathsConfig()
        self._external_paths = paths_config.get_paths()
        
        for external_path in self._external_paths:
            logger.info(f"Discovering external insights from: {external_path}")
            self._discover_from_external(external_path)
        
        logger.info(f"Total insights discovered: {len(self._insights)} ({len([s for s in self._insight_sources.values() if s == 'built-in'])} built-in, {len([s for s in self._insight_sources.values() if s != 'built-in'])} external)")
    
    def _discover_from_external(self, external_path: str) -> None:
        """
        Discover insights from external directory.
        
        Args:
            external_path: Path to external insights directory
        """
        path = Path(external_path)
        if not path.exists():
            logger.warning(f"External path does not exist: {external_path}")
            self._errors.append(ErrorEvent(
                type="import_failure",
                message=f"External path not found: {external_path}",
                severity="warning",
                details=f"The path '{external_path}' does not exist"
            ))
            return
        
        if not path.is_dir():
            logger.warning(f"External path is not a directory: {external_path}")
            self._errors.append(ErrorEvent(
                type="import_failure",
                message=f"External path is not a directory: {external_path}",
                severity="warning",
                details=f"The path '{external_path}' is not a directory"
            ))
            return
        
        # Add to sys.path temporarily for imports
        sys.path.insert(0, str(path))
        
        try:
            self._discover_external_recursive(path, path, str(path.absolute()))
        finally:
            # Remove from sys.path
            if str(path) in sys.path:
                sys.path.remove(str(path))
    
    def _discover_external_recursive(self, root_path: Path, current_path: Path, source: str) -> None:
        """
        Recursively discover insights in external directory.
        
        Args:
            root_path: Root external directory path
            current_path: Current directory being scanned
            source: Source identifier (absolute path)
        """
        # Get all Python files in current directory (except __init__.py)
        python_files = [
            f for f in current_path.iterdir()
            if f.is_file() and f.suffix == ".py" and f.stem != "__init__"
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
                # Dynamic import without package structure
                module_name = f"external_insight_{file_path.stem}_{id(file_path)}"
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Failed to load spec for {file_path}")
                
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Check for config-based insight (INSIGHT_CONFIG dictionary)
                config_found = False
                if hasattr(module, 'INSIGHT_CONFIG'):
                    config_found = True
                    try:
                        insight_config = getattr(module, 'INSIGHT_CONFIG')
                        process_results_fn = getattr(module, 'process_results', None)
                        
                        # Create ConfigBasedInsight instance
                        instance = ConfigBasedInsight(
                            config=insight_config,
                            process_results_fn=process_results_fn,
                            module_name=module_name
                        )
                        
                        # Override folder from config if specified
                        config_folder = insight_config.get("metadata", {}).get("folder")
                        if config_folder:
                            folder_name = config_folder
                        
                        self.register_insight(instance, folder_name, source)
                        logger.info(f"Registered external config-based insight: {instance.id} ({instance.name}) from {source}")
                    except Exception as e:
                        error_msg = f"Failed to create config-based insight from {file_path.stem}: {e}"
                        logger.error(error_msg)
                        self._errors.append(ErrorEvent(
                            type="instantiation_failure",
                            message=f"Failed to instantiate config-based insight: {file_path.stem}",
                            severity="error",
                            details=str(e),
                            folder=folder_name,
                            file=file_path.name
                        ))
                
                # Find all Insight subclasses in the module (skip if config-based insight found)
                if not config_found:
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, Insight) and 
                            obj is not Insight and 
                            obj.__module__ == module_name and
                            not inspect.isabstract(obj)):  # Skip abstract base classes
                            try:
                                instance = obj()
                                self.register_insight(instance, folder_name, source)
                                logger.info(f"Registered external class-based insight: {instance.id} ({instance.name}) from {source}")
                            except Exception as e:
                                error_msg = f"Failed to instantiate insight {name}: {e}"
                                logger.error(error_msg)
                                self._errors.append(ErrorEvent(
                                    type="instantiation_failure",
                                    message=f"Failed to instantiate insight: {name}",
                                    severity="error",
                                    details=str(e),
                                    folder=folder_name,
                                    file=file_path.name,
                                    insight_id=getattr(instance, 'id', None) if 'instance' in locals() else None
                                ))
            except Exception as e:
                error_msg = f"Failed to import external module {file_path.stem}: {e}"
                logger.error(error_msg)
                self._errors.append(ErrorEvent(
                    type="import_failure",
                    message=f"Failed to import external module: {file_path.stem}",
                    severity="error",
                    details=str(e),
                    folder=folder_name,
                    file=file_path.name
                ))
        
        # Recursively process subdirectories
        subdirs = [d for d in current_path.iterdir() if d.is_dir() and not d.name.startswith('__')]
        for subdir in subdirs:
            self._discover_external_recursive(root_path, subdir, source)
    
    def _discover_insights_recursive(self, root_path: Path, current_path: Path, source: str = "built-in") -> None:
        """
        Recursively discover insights in a directory and its subdirectories.
        
        Args:
            root_path: Root insights directory path
            current_path: Current directory being scanned
            source: Source identifier for the insight
        """
        # Get all Python files in current directory (except __init__.py, base.py, and filter_base.py)
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
                
                # Check for config-based insight (INSIGHT_CONFIG dictionary)
                config_found = False
                if hasattr(module, 'INSIGHT_CONFIG'):
                    config_found = True
                    try:
                        insight_config = getattr(module, 'INSIGHT_CONFIG')
                        process_results_fn = getattr(module, 'process_results', None)
                        
                        # Create ConfigBasedInsight instance
                        instance = ConfigBasedInsight(
                            config=insight_config,
                            process_results_fn=process_results_fn,
                            module_name=module_name
                        )
                        
                        # Override folder from config if specified
                        config_folder = insight_config.get("metadata", {}).get("folder")
                        if config_folder:
                            folder_name = config_folder
                        
                        self.register_insight(instance, folder_name, source)
                        logger.info(f"Registered config-based insight: {instance.id} ({instance.name}) in folder: {folder_name or 'root'}")
                    except Exception as e:
                        error_msg = f"Failed to create config-based insight from {file_path.stem}: {e}"
                        logger.error(error_msg)
                        self._errors.append(ErrorEvent(
                            type="instantiation_failure",
                            message=f"Failed to instantiate config-based insight: {file_path.stem}",
                            severity="error",
                            details=str(e),
                            folder=folder_name,
                            file=file_path.name
                        ))
                
                # Find all Insight subclasses in the module (skip if config-based insight found)
                if not config_found:
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, Insight) and 
                            obj is not Insight and 
                            obj.__module__ == module_name and
                            not inspect.isabstract(obj)):  # Skip abstract base classes
                            try:
                                instance = obj()
                                self.register_insight(instance, folder_name, source)
                                logger.info(f"Registered class-based insight: {instance.id} ({instance.name}) in folder: {folder_name or 'root'}")
                            except Exception as e:
                                error_msg = f"Failed to instantiate insight {name}: {e}"
                                logger.error(error_msg)
                                self._errors.append(ErrorEvent(
                                    type="instantiation_failure",
                                    message=f"Failed to instantiate insight: {name}",
                                    severity="error",
                                    details=str(e),
                                    folder=folder_name,
                                    file=file_path.name,
                                    insight_id=getattr(instance, 'id', None) if 'instance' in locals() else None
                                ))
            except Exception as e:
                error_msg = f"Failed to import module {file_path.stem}: {e}"
                logger.error(error_msg)
                self._errors.append(ErrorEvent(
                    type="import_failure",
                    message=f"Failed to import module: {file_path.stem}",
                    severity="error",
                    details=str(e),
                    folder=folder_name,
                    file=file_path.name
                ))
        
        # Recursively process subdirectories
        subdirs = [d for d in current_path.iterdir() if d.is_dir() and not d.name.startswith('__')]
        for subdir in subdirs:
            self._discover_insights_recursive(root_path, subdir, source)
    
    def register_insight(self, insight: Insight, folder: str = None, source: str = "built-in") -> None:
        """
        Register an insight instance.
        
        Args:
            insight: Insight instance to register
            folder: Folder name where the insight is located (None for root-level)
            source: Source identifier (built-in or external path)
        """
        if insight.id in self._insights:
            warning_msg = f"Insight {insight.id} is already registered, overwriting"
            logger.warning(warning_msg)
            self._errors.append(ErrorEvent(
                type="duplicate_id",
                message=f"Duplicate insight ID: {insight.id}",
                severity="warning",
                details=f"Insight with ID '{insight.id}' was already registered and is being overwritten",
                folder=folder,
                insight_id=insight.id
            ))
        self._insights[insight.id] = insight
        self._insight_folders[insight.id] = folder
        self._insight_sources[insight.id] = source
    
    def get_insight_source(self, insight_id: str) -> str:
        """
        Get the source path for an insight.
        
        Args:
            insight_id: Unique identifier of the insight
            
        Returns:
            Source identifier (built-in or external path)
        """
        return self._insight_sources.get(insight_id, "built-in")
    
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
    
    def get_errors(self) -> List[ErrorEvent]:
        """
        Get all errors collected during insight discovery.
        
        Returns:
            List of error events
        """
        return self._errors.copy()
    
    def clear_errors(self) -> None:
        """Clear all tracked errors."""
        self._errors.clear()


# Global plugin manager instance
_plugin_manager: PluginManager = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager

