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
        super().__init__()
        
        self._config = config
        self._process_results_fn = process_results_fn
        self._module_name = module_name or "ConfigBasedInsight"
        
        self._validate_config()
        
        metadata = config.get("metadata", {})
        
        if "id" in metadata:
            logger.warning(
                f"ID field in config is deprecated and will be ignored. "
                f"ID is auto-generated from file path. Found ID: '{metadata.get('id')}'"
            )
        
        if file_path and insights_root:
            self._id = Insight._generate_id_from_path(file_path, insights_root, source)
        else:
            self._id = metadata.get("id", "unknown_insight")
            if self._id == "unknown_insight":
                logger.warning(
                    f"Could not generate ID from file path (file_path or insights_root not provided). "
                    f"Using fallback ID. Please ensure file_path and insights_root are passed to constructor."
                )
        
        self._name = metadata.get("name")
        self._description = metadata.get("description", "")
        self._folder = metadata.get("folder")
        self._author = metadata.get("author")
        
        self._file_filter_configs = config["file_filters"]
        
        processing_config = config.get("processing", {})
        self._final_level_processing = processing_config.get("final_level")
        
        self.execution_graph = self._build_execution_graph(config)
        
        ai_config = config.get("ai", {})
        self._ai_enabled = ai_config.get("enabled", True)
        self._ai_auto = ai_config.get("auto", False)
        self._ai_prompt_type = ai_config.get("prompt_type", "explain")
        self._ai_custom_prompt = ai_config.get("prompt")
        self._ai_model = ai_config.get("model")
        self._ai_max_tokens = ai_config.get("max_tokens")
        self._ai_temperature = ai_config.get("temperature")
        
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
        
        if "file_filters" not in self._config:
            raise ValueError("Config must contain 'file_filters' (list)")
        
        file_filters = self._config["file_filters"]
        if not isinstance(file_filters, list):
            raise ValueError("Config file_filters must be a list")
        
        if len(file_filters) == 0:
            raise ValueError("Config file_filters must be a non-empty list")
        
        for idx, file_filter_config in enumerate(file_filters):
            if not isinstance(file_filter_config, dict):
                raise ValueError(f"File filter config at index {idx} must be a dictionary")
            
            if "line_filters" not in file_filter_config:
                raise ValueError(f"File filter config at index {idx} must contain 'line_filters' (list)")
            
            line_filters = file_filter_config["line_filters"]
            if not isinstance(line_filters, list) or len(line_filters) == 0:
                raise ValueError(f"File filter config at index {idx} must have non-empty 'line_filters' list")
            
            for line_idx, line_filter in enumerate(line_filters):
                if not isinstance(line_filter, dict):
                    raise ValueError(f"Line filter at index {line_idx} in file filter {idx} must be a dictionary")
                if "ripgrep_command" not in line_filter:
                    raise ValueError(f"Line filter at index {line_idx} in file filter {idx} must contain 'ripgrep_command'")
    
    
    def _parse_regex_flags(self, flags_str: str) -> int:
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
    
    def _build_line_filter_objects(self, line_filters_config: List[Dict]) -> List[LineFilterConfig]:
        """Build line filter objects from config list."""
        line_filter_objects = []
        for line_filter_config_dict in line_filters_config:
            line_filter_obj = LineFilterConfig(
                pattern=line_filter_config_dict["ripgrep_command"],  # Store ripgrep_command as pattern
                reading_mode=self._parse_reading_mode(line_filter_config_dict.get("reading_mode", "ripgrep")),
                chunk_size=line_filter_config_dict.get("chunk_size", 1048576),
                regex_flags=self._parse_regex_flags(line_filter_config_dict.get("regex_flags", "")),
                processing=line_filter_config_dict.get("processing")
            )
            line_filter_objects.append(line_filter_obj)
        return line_filter_objects
    
    def _build_execution_graph(self, config: Dict) -> ExecutionGraph:
        """Build execution graph as objects from config."""
        file_filters_config = config["file_filters"]
        file_filter_objects = []
        
        for file_filter_config in file_filters_config:
            file_patterns = file_filter_config.get("file_patterns", [])
            line_filters_config = file_filter_config.get("line_filters", [])
            processing_config = file_filter_config.get("processing", {})
            processing = processing_config.get("file_filter_level")
            
            line_filter_objects = self._build_line_filter_objects(line_filters_config)
            
            file_filter_obj = FileFilterConfig(
                file_patterns=file_patterns if file_patterns else None,
                line_filters=line_filter_objects,
                processing=processing
            )
            file_filter_objects.append(file_filter_obj)
        
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
    def author(self) -> Optional[str]: return self._author
    
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
        return {
            "insight_name": self._name,
            "insight_description": self._description
        }

