"""Config-based insight implementation for declarative insight definitions."""

import re
import logging
import hashlib
from pathlib import Path
from typing import List, Optional, Callable, Awaitable, Dict, Any
import asyncio

from app.core.insight_base import Insight
from app.core.filter_base import FilterResult, FileFilter, LineFilter, ReadingMode
from app.core.models import InsightResult, ProgressEvent

logger = logging.getLogger(__name__)


class ConfigBasedInsight(Insight):
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
        """
        Initialize config-based insight.
        
        Args:
            config: INSIGHT_CONFIG dictionary with metadata and filters
            process_results_fn: Optional function to post-process filtered results
            module_name: Optional module name for logging
            file_path: Path to the insight file (for auto-generating ID)
            insights_root: Root directory of insights (for auto-generating ID)
            source: Source identifier ("built-in" or external path)
        """
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
        
        # Extract filter configuration
        filters = config.get("filters", {})
        self._file_patterns = filters.get("file_patterns")
        self._line_pattern = filters.get("line_pattern")
        self._regex_flags_str = filters.get("regex_flags", "")
        self._reading_mode_str = filters.get("reading_mode", "ripgrep")  # Default to ripgrep for best performance
        self._chunk_size = filters.get("chunk_size", 1048576)
        self._context_before = filters.get("context_before", 0)  # Lines of context before match
        self._context_after = filters.get("context_after", 0)  # Lines of context after match
        
        # Extract AI configuration
        ai_config = config.get("ai", {})
        self._ai_enabled = ai_config.get("enabled", True)  # Default: AI enabled
        self._ai_auto = ai_config.get("auto", False)  # Default: manual trigger
        self._ai_prompt_type = ai_config.get("prompt_type", "explain")  # Default: explain
        self._ai_custom_prompt = ai_config.get("prompt")  # Optional custom prompt
        self._ai_model = ai_config.get("model")  # Optional model override
        self._ai_max_tokens = ai_config.get("max_tokens")  # Optional max_tokens override
        self._ai_temperature = ai_config.get("temperature")  # Optional temperature override
        
        # Parse regex flags
        self._regex_flags = self._parse_regex_flags(self._regex_flags_str)
        
        # Parse reading mode
        self._reading_mode = self._parse_reading_mode(self._reading_mode_str)
        
        logger.info(f"ConfigBasedInsight initialized: {self._id} from {self._module_name}")
        if self._ai_enabled:
            logger.debug(f"ConfigBasedInsight AI: enabled={self._ai_enabled}, auto={self._ai_auto}, prompt_type={self._ai_prompt_type}")
    
    def _validate_config(self) -> None:
        """Validate config structure and required fields."""
        if not isinstance(self._config, dict):
            raise ValueError("Config must be a dictionary")
        
        if "metadata" not in self._config:
            raise ValueError("Config must contain 'metadata' section")
        
        metadata = self._config["metadata"]
        # ID is no longer required - it's auto-generated from file path
        if "name" not in metadata:
            raise ValueError("Config metadata must contain 'name'")
        
        if "filters" not in self._config:
            raise ValueError("Config must contain 'filters' section")
        
        filters = self._config["filters"]
        if "line_pattern" not in filters:
            raise ValueError("Config filters must contain 'line_pattern'")
    
    @staticmethod
    def _normalize_for_id(text: str) -> str:
        """Normalize text for use in ID: lowercase, alphanumeric + underscores only."""
        return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')
    
    @staticmethod
    def _generate_id_from_path(
        file_path: Path,
        insights_root: Path,
        source: str
    ) -> str:
        """
        Generate unique ID from file path.
        
        Args:
            file_path: Full path to insight file
            insights_root: Root of insights directory
            source: "built-in" or external path
            
        Returns:
            Generated unique ID
        """
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
        """
        Parse regex flags from string to int.
        
        Args:
            flags_str: Comma-separated flag names (e.g., "IGNORECASE,MULTILINE")
            
        Returns:
            Combined regex flags as integer
        """
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
        """
        Parse reading mode from string.
        
        Args:
            mode_str: "lines", "chunks", or "ripgrep"
            
        Returns:
            ReadingMode enum value
        """
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
    
    @property
    def id(self) -> str:
        """Return insight ID (auto-generated from file path)."""
        return self._id
    
    @property
    def name(self) -> str:
        """Return insight name from config."""
        return self._name
    
    @property
    def description(self) -> str:
        """Return insight description from config."""
        return self._description
    
    @property
    def folder(self) -> Optional[str]:
        """Return insight folder from config."""
        return self._folder
    
    @property
    def ai_enabled(self) -> bool:
        """Whether AI processing is supported for this insight."""
        return self._ai_enabled
    
    @property
    def ai_auto(self) -> bool:
        """Whether to automatically trigger AI after analysis."""
        return self._ai_auto
    
    @property
    def ai_prompt_type(self) -> str:
        """Default AI prompt type for this insight."""
        return self._ai_prompt_type
    
    @property
    def ai_custom_prompt(self) -> Optional[str]:
        """Custom AI prompt for this insight (if ai_prompt_type is "custom")."""
        return self._ai_custom_prompt
    
    @property
    def ai_prompt_variables(self) -> Optional[dict]:
        """
        Variables for AI prompt substitution.
        
        Returns:
            Dictionary of variables including result metadata and insight info
        """
        # These will be populated at runtime from the analysis result
        return {
            "insight_name": self._name,
            "insight_description": self._description
        }
    
    async def analyze(
        self,
        file_paths: List[str],
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> InsightResult:
        """
        Analyze files using configured filters.
        
        Args:
            file_paths: List of file or folder paths to analyze
            cancellation_event: Optional asyncio.Event to check for cancellation
            progress_callback: Optional async callback to emit progress events
            
        Returns:
            InsightResult with analysis results
        """
        import time
        start_time = time.time()
        logger.info(f"{self._module_name}: Starting analysis of {len(file_paths)} path(s)")
        logger.debug(f"{self._module_name}: Line filter pattern: '{self._line_pattern}'")
        logger.debug(f"{self._module_name}: Reading mode: {self._reading_mode.value}")
        if self._reading_mode == ReadingMode.CHUNKS:
            logger.debug(f"{self._module_name}: Chunk size: {self._chunk_size:,} bytes")
        
        # Create file filter
        file_filter = FileFilter(file_paths)
        
        # Apply file filtering if patterns provided
        if self._file_patterns:
            logger.info(f"{self._module_name}: Applying file filter patterns: {self._file_patterns}")
            file_filter.filter_files(*self._file_patterns)
        else:
            logger.debug(f"{self._module_name}: No file filter patterns, processing all files/folders")
        
        # Create line filter
        line_filter = LineFilter(
            pattern=self._line_pattern,
            reading_mode=self._reading_mode,
            chunk_size=self._chunk_size,
            flags=self._regex_flags,
            context_before=self._context_before,
            context_after=self._context_after
        )
        
        # Apply line filtering
        from app.services.file_handler import CancelledError
        try:
            logger.debug(f"{self._module_name}: Applying line filter to files")
            filter_result = await file_filter.apply(line_filter, cancellation_event, progress_callback)
            logger.info(f"{self._module_name}: Line filtering complete - {filter_result.get_total_line_count()} matching lines across {filter_result.get_file_count()} file(s)")
        except CancelledError:
            logger.info(f"{self._module_name}: Analysis cancelled")
            raise
        
        # Process filtered lines
        logger.debug(f"{self._module_name}: Processing filtered lines")
        if self._process_results_fn:
            # Use custom post-processing function
            logger.debug(f"{self._module_name}: Using custom process_results function")
            result_data = self._process_results_fn(filter_result)
            
            if not isinstance(result_data, dict):
                raise ValueError("process_results() must return a dict with 'content' key")
            if "content" not in result_data:
                raise ValueError("process_results() return dict must contain 'content' key")
            
            content = result_data["content"]
            metadata = result_data.get("metadata", {})
        else:
            # Use default formatting
            logger.debug(f"{self._module_name}: Using default formatting")
            content, metadata = self._default_format(filter_result)
        
        # Add execution command and method to metadata
        commands_by_file = filter_result.get_commands()
        execution_method = filter_result.get_execution_method()
        total_line_count = filter_result.get_total_line_count()
        
        # Get the first command as representative (or combine if multiple files)
        if commands_by_file:
            # If multiple files, show first file's command (or could combine)
            first_file = list(commands_by_file.keys())[0]
            execution_command = commands_by_file[first_file]
            # If multiple files, append note
            if len(commands_by_file) > 1:
                execution_command += f" (+ {len(commands_by_file) - 1} more file(s))"
        else:
            # Fallback: construct command from insight info
            execution_command = f"{self._name}: {self._description or 'Custom insight'}"
        
        # Add to metadata
        metadata["execution_command"] = execution_command
        if execution_method:
            metadata["execution_method"] = execution_method
        metadata["line_count"] = total_line_count
        metadata["pattern"] = self._line_pattern
        
        total_elapsed = time.time() - start_time
        logger.info(f"{self._module_name}: Analysis complete in {total_elapsed:.2f}s")
        
        return InsightResult(
            result_type="text",
            content=content,
            metadata=metadata
        )
    
    def _default_format(self, filter_result: FilterResult) -> tuple[str, Dict[str, Any]]:
        """
        Default formatting for filtered results.
        
        Args:
            filter_result: FilterResult with filtered lines
            
        Returns:
            Tuple of (content string, metadata dict)
        """
        lines_by_file = filter_result.get_lines_by_file()
        total_lines = filter_result.get_total_line_count()
        file_count = filter_result.get_file_count()
        
        # Format results
        result_text = f"{self._name}\n"
        result_text += f"{'=' * 80}\n\n"
        result_text += f"Total matches: {total_lines:,}\n"
        result_text += f"Files analyzed: {file_count}\n\n"
        
        if file_count > 0:
            for file_path, lines in lines_by_file.items():
                result_text += f"{'=' * 80}\n"
                result_text += f"File: {file_path}\n"
                result_text += f"Matches: {len(lines):,}\n"
                result_text += f"{'=' * 80}\n"
                # Show first 100 matches
                for line in lines[:100]:
                    result_text += f"{line.rstrip()}\n"
                if len(lines) > 100:
                    result_text += f"\n... and {len(lines) - 100:,} more matches\n"
                result_text += "\n"
        
        metadata = {
            "total_matches": total_lines,
            "files_analyzed": file_count
        }
        
        return result_text, metadata

