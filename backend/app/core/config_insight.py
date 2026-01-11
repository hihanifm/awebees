"""Config-based insight implementation for declarative insight definitions."""

import re
import logging
import hashlib
from pathlib import Path
from typing import List, Optional, Callable, Awaitable, Dict, Any
import asyncio

from app.core.insight_base import Insight
from app.core.filter_base import (
    FilterBasedInsight, FilterResult, FileFilter, LineFilter, ReadingMode,
    ExecutionGraph, FileFilterConfig, LineFilterConfig
)
from app.core.models import InsightResult, ProgressEvent
from app.services.file_handler import CancelledError

logger = logging.getLogger(__name__)


class ConfigBasedInsight(FilterBasedInsight):
    """
    Insight implementation that loads configuration from a dictionary.
    
    This class allows users to define insights declaratively using INSIGHT_CONFIG
    dictionaries instead of writing full Python classes.
    
    Example:
        INSIGHT_CONFIG = {
            "metadata": {
                # ID is auto-generated from file path - no need to specify
                "name": "My Insight",
                "description": "Detects something interesting",
                "folder": "general"
            },
            "filters": {
                "file_patterns": [r"\\.log$"],  # Optional
                "line_pattern": r"ERROR",       # Required
                "regex_flags": "IGNORECASE",    # Optional
                "reading_mode": "ripgrep",      # Optional: "ripgrep" (default, 10-100x faster), "chunks", or "lines"
                "chunk_size": 1048576           # Optional (only for chunks mode)
            }
        }
        
        # Optional post-processing function
        def process_results(filter_result):
            return {
                "content": "formatted output",
                "metadata": {"key": "value"}
            }
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        process_results_fn: Optional[Callable[[FilterResult], Dict[str, Any]]] = None,
        module_name: Optional[str] = None,
        file_path: Optional[Path] = None,
        insights_root: Optional[Path] = None,
        source: str = "built-in"
    ):
        # Initialize FilterBasedInsight
        super().__init__()
        
        # file_path and insights_root are used for auto-generating ID from file path
        self._config = config
        self._process_results_fn = process_results_fn
        self._module_name = module_name or "ConfigBasedInsight"
        
        # Validate config structure
        self._validate_config()
        
        # Extract metadata
        metadata = config.get("metadata", {})
        
        # Warn if ID is provided (deprecated)
        if "id" in metadata:
            logger.warning(
                f"ID field in config is deprecated and will be ignored. "
                f"ID is auto-generated from file path. Found ID: '{metadata.get('id')}'"
            )
        
        # Generate ID from file path if available, otherwise use fallback
        if file_path and insights_root:
            self._id = self._generate_id_from_path(file_path, insights_root, source)
        else:
            # Fallback: try to use ID from config if provided (for backward compatibility during transition)
            self._id = metadata.get("id", "unknown_insight")
            if self._id == "unknown_insight":
                logger.warning(
                    f"Could not generate ID from file path (file_path or insights_root not provided). "
                    f"Using fallback ID. Please ensure file_path and insights_root are passed to constructor."
                )
        
        self._name = metadata.get("name")
        self._description = metadata.get("description", "")
        self._folder = metadata.get("folder")
        
        # Extract file filters configuration (optional - if not present, insight processes all files)
        self._file_filter_configs = config.get("file_filters", [])
        
        # Extract processing functions
        processing_config = config.get("processing", {})
        self._final_level_processing = processing_config.get("final_level")  # Optional final processing function
        
        # Build execution graph as objects
        self.execution_graph = self._build_execution_graph(config)
        
        # Extract AI configuration
        ai_config = config.get("ai", {})
        self._ai_enabled = ai_config.get("enabled", True)  # Default: AI enabled
        self._ai_auto = ai_config.get("auto", False)  # Default: manual trigger
        self._ai_prompt_type = ai_config.get("prompt_type", "explain")  # Default: explain
        self._ai_custom_prompt = ai_config.get("prompt")  # Optional custom prompt
        self._ai_model = ai_config.get("model")  # Optional model override
        self._ai_max_tokens = ai_config.get("max_tokens")  # Optional max_tokens override
        self._ai_temperature = ai_config.get("temperature")  # Optional temperature override
        
        logger.info(f"ConfigBasedInsight initialized: {self._id} from {self._module_name}")
        logger.debug(f"ConfigBasedInsight: {len(self._file_filter_configs)} file filter config(s)")
        if self._ai_enabled:
            logger.debug(f"ConfigBasedInsight AI: enabled={self._ai_enabled}, auto={self._ai_auto}, prompt_type={self._ai_prompt_type}")
    
    def _validate_config(self) -> None:
        if not isinstance(self._config, dict):
            raise ValueError("Config must be a dictionary")
        
        if "metadata" not in self._config:
            raise ValueError("Config must contain 'metadata' section")
        
        metadata = self._config["metadata"]
        if "name" not in metadata:
            raise ValueError("Config metadata must contain 'name'")
        
        # file_filters is optional - if not present, insights handle filtering themselves
        # Only validate if file_filters is specified
        if "file_filters" in self._config:
            file_filters = self._config["file_filters"]
            if not isinstance(file_filters, list):
                raise ValueError("Config file_filters must be a list if specified")
            
            if len(file_filters) == 0:
                raise ValueError("Config file_filters must be a non-empty list if specified")
            
            # Validate each file filter config
            for idx, file_filter_config in enumerate(file_filters):
                if not isinstance(file_filter_config, dict):
                    raise ValueError(f"File filter config at index {idx} must be a dictionary")
                
                if "line_filters" not in file_filter_config:
                    raise ValueError(f"File filter config at index {idx} must contain 'line_filters' (list)")
                
                line_filters = file_filter_config["line_filters"]
                if not isinstance(line_filters, list) or len(line_filters) == 0:
                    raise ValueError(f"File filter config at index {idx} must have non-empty 'line_filters' list")
                
                # Validate each line filter
                for line_idx, line_filter in enumerate(line_filters):
                    if not isinstance(line_filter, dict):
                        raise ValueError(f"Line filter at index {line_idx} in file filter {idx} must be a dictionary")
                    if "pattern" not in line_filter:
                        raise ValueError(f"Line filter at index {line_idx} in file filter {idx} must contain 'pattern'")
    
    @staticmethod
    def _normalize_for_id(text: str) -> str:
        # Normalize text for use in ID: lowercase, alphanumeric + underscores only
        return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')
    
    @staticmethod
    def _generate_id_from_path(
        file_path: Path,
        insights_root: Path,
        source: str
    ) -> str:
        # Get relative path from insights root
        try:
            relative_path = file_path.relative_to(insights_root)
        except ValueError:
            # File not under root (external), use absolute path
            relative_path = file_path
        
        # Remove .py extension
        relative_stem = relative_path.with_suffix('')
        
        # Convert path parts to ID components
        if source == "built-in":
            # Built-in: use all path components
            parts = [p for p in relative_stem.parts if p != '.']
            normalized_parts = [ConfigBasedInsight._normalize_for_id(p) for p in parts]
            return '_'.join(normalized_parts) if normalized_parts else 'insight'
        else:
            # External: include source hash for uniqueness
            source_hash = hashlib.md5(source.encode()).hexdigest()[:8]
            parts = [p for p in relative_stem.parts if p != '.']
            normalized_parts = [ConfigBasedInsight._normalize_for_id(p) for p in parts]
            base_id = '_'.join(normalized_parts) if normalized_parts else 'insight'
            return f"ext_{source_hash}_{base_id}"
    
    def _parse_regex_flags(self, flags_str: str) -> int:
        # Parse comma-separated flag names (e.g., "IGNORECASE,MULTILINE") to integer flags
        if not flags_str:
            return 0
        
        flags = 0
        for flag_name in flags_str.split(","):
            flag_name = flag_name.strip().upper()
            if hasattr(re, flag_name):
                flags |= getattr(re, flag_name)
            else:
                logger.warning(f"Unknown regex flag: {flag_name}")
        
        return flags
    
    def _parse_reading_mode(self, mode_str: str) -> ReadingMode:
        # Parse reading mode string ("lines", "chunks", or "ripgrep") to ReadingMode enum
        mode_str = mode_str.lower()
        if mode_str == "lines":
            return ReadingMode.LINES
        elif mode_str == "chunks":
            return ReadingMode.CHUNKS
        elif mode_str == "ripgrep":
            return ReadingMode.RIPGREP
        else:
            logger.warning(f"Unknown reading mode: {mode_str}, defaulting to 'ripgrep'")
            return ReadingMode.RIPGREP
    
    def _build_execution_graph(self, config: Dict) -> ExecutionGraph:
        """Build execution graph as objects from config."""
        file_filters_config = config.get("file_filters", [])
        
        if not file_filters_config:
            # No file_filters specified - use default file filter with default line filter
            default_line_filter = LineFilterConfig(
                pattern=".*",  # Match all lines
                reading_mode=ReadingMode.RIPGREP
            )
            default_file_filter = FileFilterConfig(
                file_patterns=None,  # None = default dummy (all files)
                line_filters=[default_line_filter],
                processing=None
            )
            return ExecutionGraph(
                file_filters=[default_file_filter],
                final_processing=self._final_level_processing
            )
        
        # Build graph from config
        file_filter_objects = []
        for file_filter_config in file_filters_config:
            file_patterns = file_filter_config.get("file_patterns", [])
            line_filters_config = file_filter_config.get("line_filters", [])
            processing_config = file_filter_config.get("processing", {})
            processing = processing_config.get("file_filter_level")
            
            # Build line filter objects
            line_filter_objects = []
            for line_filter_config_dict in line_filters_config:
                line_filter_obj = LineFilterConfig(
                    pattern=line_filter_config_dict["pattern"],
                    reading_mode=self._parse_reading_mode(line_filter_config_dict.get("reading_mode", "ripgrep")),
                    chunk_size=line_filter_config_dict.get("chunk_size", 1048576),
                    regex_flags=self._parse_regex_flags(line_filter_config_dict.get("regex_flags", "")),
                    context_before=line_filter_config_dict.get("context_before", 0),
                    context_after=line_filter_config_dict.get("context_after", 0),
                    processing=line_filter_config_dict.get("processing")  # Optional line-filter level processing
                )
                line_filter_objects.append(line_filter_obj)
            
            # Build file filter object
            file_filter_obj = FileFilterConfig(
                file_patterns=file_patterns if file_patterns else None,  # None = dummy
                line_filters=line_filter_objects,
                processing=processing  # Optional file-filter level processing
            )
            file_filter_objects.append(file_filter_obj)
        
        # Build final execution graph
        return ExecutionGraph(
            file_filters=file_filter_objects,
            final_processing=self._final_level_processing
        )
    
    @property
    def id(self) -> str: return self._id
    
    @property
    def name(self) -> str: return self._name
    
    @property
    def description(self) -> str: return self._description
    
    @property
    def folder(self) -> Optional[str]: return self._folder
    
    @property
    def ai_enabled(self) -> bool: return self._ai_enabled
    
    @property
    def ai_auto(self) -> bool: return self._ai_auto
    
    @property
    def ai_prompt_type(self) -> str: return self._ai_prompt_type
    
    @property
    def ai_custom_prompt(self) -> Optional[str]: return self._ai_custom_prompt
    
    @property
    def ai_prompt_variables(self) -> Optional[dict]:
        # These will be populated at runtime from the analysis result
        return {
            "insight_name": self._name,
            "insight_description": self._description
        }

