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
from app.services.file_handler import CancelledError

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
        
        # Reject old format explicitly (no backward compatibility)
        if "filters" in self._config and "line_pattern" in self._config.get("filters", {}):
            raise ValueError(
                "Old config format with 'filters.line_pattern' is no longer supported. "
                "Please migrate to new 'file_filters' format. "
                "Example: file_filters: [{file_patterns: [], line_filters: [{pattern: '...'}]}]"
            )
        
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
    
    def _get_path_files(self, user_path: str) -> List[str]:
        """
        Get files for a single user path (if folder, cache recursively; if file, use directly).
        
        Args:
            user_path: User input path (file or folder)
            
        Returns:
            List of file paths
        """
        path_obj = Path(user_path)
        if not path_obj.exists():
            logger.warning(f"{self._module_name}: Path does not exist: {user_path}")
            return []
        
        if path_obj.is_file():
            # Single file - return as list
            resolved_path = str(path_obj.resolve())
            logger.debug(f"{self._module_name}: Path is a file: {resolved_path}")
            return [resolved_path]
        elif path_obj.is_dir():
            # Folder - cache recursively
            logger.debug(f"{self._module_name}: Path is a folder, listing files recursively: {user_path}")
            files = [str(p.resolve()) for p in path_obj.rglob("*") if p.is_file()]
            logger.info(f"{self._module_name}: Found {len(files)} file(s) in folder: {user_path}")
            return sorted(files)
        else:
            logger.warning(f"{self._module_name}: Path is neither file nor folder: {user_path}")
            return []
    
    def _apply_file_filter(self, files: List[str], file_patterns: List[str]) -> List[str]:
        """
        Filter files by file patterns.
        
        Args:
            files: List of file paths
            file_patterns: List of regex patterns to match filenames
            
        Returns:
            List of files that match any pattern
        """
        if not file_patterns:
            return files
        
        import re
        compiled_patterns = [re.compile(pattern) for pattern in file_patterns]
        matching_files = []
        for file_path in files:
            file_name = Path(file_path).name
            if any(pattern.search(file_name) for pattern in compiled_patterns):
                matching_files.append(file_path)
        
        logger.debug(f"{self._module_name}: File filter matched {len(matching_files)} files from {len(files)} total")
        return matching_files
    
    async def _apply_line_filter(
        self,
        file_path: str,
        line_filter_config: Dict[str, Any],
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> FilterResult:
        """
        Apply a line filter to a single file.
        
        Args:
            file_path: Path to the file
            line_filter_config: Line filter configuration dict
            cancellation_event: Optional cancellation event
            progress_callback: Optional progress callback
            
        Returns:
            FilterResult with filtered lines
        """
        pattern = line_filter_config.get("pattern")
        regex_flags_str = line_filter_config.get("regex_flags", "")
        reading_mode_str = line_filter_config.get("reading_mode", "ripgrep")
        chunk_size = line_filter_config.get("chunk_size", 1048576)
        context_before = line_filter_config.get("context_before", 0)
        context_after = line_filter_config.get("context_after", 0)
        
        # Parse regex flags and reading mode
        regex_flags = self._parse_regex_flags(regex_flags_str)
        reading_mode = self._parse_reading_mode(reading_mode_str)
        
        # Create line filter
        line_filter = LineFilter(
            pattern=pattern,
            reading_mode=reading_mode,
            chunk_size=chunk_size,
            flags=regex_flags,
            context_before=context_before,
            context_after=context_after
        )
        
        # Create file filter for single file
        file_filter = FileFilter([file_path])
        
        # Apply line filter
        from app.services.file_handler import CancelledError
        try:
            filter_result = await file_filter.apply(line_filter, cancellation_event, progress_callback)
            return filter_result
        except CancelledError:
            logger.info(f"{self._module_name}: Line filter cancelled for file: {file_path}")
            raise
    
    def _process_line_filter_results(
        self,
        filter_result: FilterResult,
        line_filter_config: Dict[str, Any],
        file_path: str
    ) -> Dict[str, Any]:
        """
        Process results from a single line filter.
        
        Args:
            filter_result: FilterResult from the line filter
            line_filter_config: Line filter configuration (may contain processing function)
            file_path: Path to the file that was filtered
            
        Returns:
            Dict with content and metadata
        """
        line_processing_fn = line_filter_config.get("processing")
        
        if line_processing_fn:
            # Use custom line-level processing
            logger.debug(f"{self._module_name}: Using custom line-level processing for line filter: {line_filter_config.get('id', 'default')}")
            result_data = line_processing_fn(filter_result)
            
            if not isinstance(result_data, dict) or "content" not in result_data:
                raise ValueError("Line filter processing function must return dict with 'content' key")
            
            return {
                "content": result_data["content"],
                "metadata": result_data.get("metadata", {}),
                "line_count": filter_result.get_total_line_count()
            }
        else:
            # Default formatting for line filter results
            lines = filter_result.get_lines()
            return {
                "content": "\n".join(lines) if lines else "",
                "metadata": {
                    "line_count": len(lines),
                    "file_path": file_path
                },
                "line_count": len(lines)
            }
    
    def _process_file_filter_results(
        self,
        file_filter_id: str,
        all_line_filter_results: List[Dict[str, Any]],
        file_filter_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process and aggregate results from all line filters for a file filter.
        
        Args:
            file_filter_id: ID of the file filter
            all_line_filter_results: List of processed line filter results (each contains file_path, line_filter_id, result)
            file_filter_config: File filter configuration (may contain processing.file_filter_level function)
            
        Returns:
            Dict with content and metadata for this file filter
        """
        file_filter_processing = file_filter_config.get("processing", {})
        file_filter_level_fn = file_filter_processing.get("file_filter_level")
        
        if file_filter_level_fn:
            # Use custom file-filter-level processing
            logger.debug(f"{self._module_name}: Using custom file-filter-level processing for: {file_filter_id}")
            result_data = file_filter_level_fn(all_line_filter_results)
            
            if not isinstance(result_data, dict) or "content" not in result_data:
                raise ValueError("File filter level processing function must return dict with 'content' key")
            
            return {
                "content": result_data["content"],
                "metadata": {
                    **result_data.get("metadata", {}),
                    "file_filter_id": file_filter_id,
                    "line_filter_count": len(all_line_filter_results)
                }
            }
        else:
            # Default aggregation: combine all line filter results
            combined_content = []
            total_lines = 0
            
            for line_filter_result in all_line_filter_results:
                line_filter_id = line_filter_result.get("line_filter_id", "default")
                file_path = line_filter_result.get("file_path", "")
                result = line_filter_result.get("result", {})
                content = result.get("content", "")
                
                combined_content.append(f"Line Filter: {line_filter_id}")
                combined_content.append(f"File: {file_path}")
                combined_content.append(content)
                combined_content.append("")
                
                total_lines += result.get("line_count", 0)
            
            return {
                "content": "\n".join(combined_content),
                "metadata": {
                    "file_filter_id": file_filter_id,
                    "line_filter_count": len(all_line_filter_results),
                    "total_lines": total_lines
                }
            }
    
    def _create_insight_result(
        self,
        user_path: str,
        file_filter_results: List[Dict[str, Any]],
        insight_config: Dict[str, Any]
    ) -> InsightResult:
        """
        Create final InsightResult by aggregating all file filter results.
        
        Args:
            user_path: Original user input path
            file_filter_results: List of processed file filter results
            insight_config: Full insight configuration
            
        Returns:
            InsightResult for this path
        """
        if self._final_level_processing:
            # Use custom final-level processing
            logger.debug(f"{self._module_name}: Using custom final-level processing")
            result_data = self._final_level_processing(file_filter_results)
            
            if not isinstance(result_data, dict) or "content" not in result_data:
                raise ValueError("Final level processing function must return dict with 'content' key")
            
            content = result_data["content"]
            metadata = result_data.get("metadata", {})
        else:
            # Default aggregation: combine all file filter results
            combined_content = []
            combined_content.append(f"{self._name}")
            combined_content.append(f"{'=' * 80}")
            combined_content.append(f"Path: {user_path}")
            combined_content.append("")
            
            total_file_filters = len(file_filter_results)
            for file_filter_result in file_filter_results:
                file_filter_id = file_filter_result.get("metadata", {}).get("file_filter_id", "unknown")
                combined_content.append(f"File Filter: {file_filter_id}")
                combined_content.append(f"{'=' * 80}")
                combined_content.append(file_filter_result.get("content", ""))
                combined_content.append("")
            
            content = "\n".join(combined_content)
            metadata = {
                "user_path": user_path,
                "file_filter_count": total_file_filters
            }
        
        # Add user_path to metadata
        if metadata is None:
            metadata = {}
        metadata["user_path"] = user_path
        metadata["file_filter_results"] = file_filter_results
        
        return InsightResult(
            result_type="text",
            content=content,
            metadata=metadata
        )
    
    async def analyze(
        self,
        user_path: str,
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> InsightResult:
        import time
        start_time = time.time()
        logger.info(f"{self._module_name}: Starting analysis of path: {user_path}")
        
        # 1. Check if user_path is a file or folder
        path_obj = Path(user_path)
        is_file = path_obj.is_file()
        is_folder = path_obj.is_dir()
        
        if not path_obj.exists():
            logger.warning(f"{self._module_name}: Path does not exist: {user_path}")
            return InsightResult(
                result_type="text",
                content=f"Path does not exist: {user_path}",
                metadata={"user_path": user_path, "file_filter_results": []}
            )
        
        if not is_file and not is_folder:
            logger.warning(f"{self._module_name}: Path is neither file nor folder: {user_path}")
            return InsightResult(
                result_type="text",
                content=f"Path is neither file nor folder: {user_path}",
                metadata={"user_path": user_path, "file_filter_results": []}
            )
        
        # 2. Process each file filter configuration for this path
        path_file_filter_results = []
        
        if not self._file_filter_configs:
            # No file_filters specified - this insight should use FilterBasedInsight or custom implementation
            logger.debug(f"{self._module_name}: No file_filters specified - this insight should not use ConfigBasedInsight.analyze()")
            return InsightResult(
                result_type="text",
                content=f"Insight '{self._name}' has no file_filters configuration. ConfigBasedInsight requires file_filters. Use FilterBasedInsight or custom implementation instead.",
                metadata={"user_path": user_path, "file_filter_results": []}
            )
        
        # 3. Handle file vs folder differently
        if is_file:
            # User provided a file - skip file filtering, process file directly with all line filters
            logger.debug(f"{self._module_name}: User provided file (not folder) - skipping file filtering, processing file directly")
            file_path = str(path_obj.resolve())
            
            # Process all file_filter_configs, but skip file filtering and apply all line filters to the single file
            for file_filter_config in self._file_filter_configs:
                file_filter_id = file_filter_config.get("id", f"file_filter_{len(path_file_filter_results)}")
                line_filters = file_filter_config.get("line_filters", [])
                
                logger.debug(f"{self._module_name}: Processing file filter: {file_filter_id} with {len(line_filters)} line filter(s) (file filter skipped for single file)")
                
                # Process each line filter for this single file
                all_line_filter_results = []
                for line_filter_config in line_filters:
                    line_filter_id = line_filter_config.get("id", "default")
                    pattern = line_filter_config.get("pattern")
                    
                    logger.debug(f"{self._module_name}: Applying line filter '{line_filter_id}' (pattern: {pattern}) to file: {file_path}")
                    
                    try:
                        # Apply line filter
                        filter_result = await self._apply_line_filter(
                            file_path, line_filter_config, cancellation_event, progress_callback
                        )
                        
                        # EXCLUSIVE: Process line filter results
                        line_processed = self._process_line_filter_results(
                            filter_result, line_filter_config, file_path
                        )
                        
                        # Collect processed line filter result with file context
                        all_line_filter_results.append({
                            "file_path": file_path,
                            "line_filter_id": line_filter_id,
                            "pattern": pattern,
                            "result": line_processed
                        })
                    except CancelledError:
                        logger.info(f"{self._module_name}: Analysis cancelled")
                        raise
                    except Exception as e:
                        logger.error(f"{self._module_name}: Error processing line filter '{line_filter_id}' for file '{file_path}': {e}", exc_info=True)
                        # Continue with other line filters
                
                # Process file filter results (aggregate all processed line filter results)
                file_filter_processed = self._process_file_filter_results(
                    file_filter_id, all_line_filter_results, file_filter_config
                )
                
                path_file_filter_results.append(file_filter_processed)
        
        else:
            # User provided a folder - apply file filtering as normal
            logger.debug(f"{self._module_name}: User provided folder - applying file filtering")
            path_files = self._get_path_files(user_path)
            
            if not path_files:
                logger.warning(f"{self._module_name}: No files found in folder: {user_path}")
                return InsightResult(
                    result_type="text",
                    content=f"No files found in folder: {user_path}",
                    metadata={"user_path": user_path, "file_filter_results": []}
                )
            
            for file_filter_config in self._file_filter_configs:
                file_filter_id = file_filter_config.get("id", f"file_filter_{len(path_file_filter_results)}")
                file_patterns = file_filter_config.get("file_patterns", [])
                line_filters = file_filter_config.get("line_filters", [])
                
                logger.debug(f"{self._module_name}: Processing file filter: {file_filter_id} with {len(file_patterns)} pattern(s) and {len(line_filters)} line filter(s)")
                
                # Apply this file filter's patterns to files from this folder
                # Empty file_patterns list means process all files
                filtered_files = self._apply_file_filter(path_files, file_patterns)
                
                if not filtered_files:
                    logger.debug(f"{self._module_name}: No files matched file filter patterns for: {file_filter_id}")
                    continue
                
                # Process each filtered file through all line filters
                all_line_filter_results = []
                
                for file_path in filtered_files:
                    # Process each line filter for this file
                    for line_filter_config in line_filters:
                        line_filter_id = line_filter_config.get("id", "default")
                        pattern = line_filter_config.get("pattern")
                        
                        logger.debug(f"{self._module_name}: Applying line filter '{line_filter_id}' (pattern: {pattern}) to file: {file_path}")
                        
                        try:
                            # Apply line filter
                            filter_result = await self._apply_line_filter(
                                file_path, line_filter_config, cancellation_event, progress_callback
                            )
                            
                            # EXCLUSIVE: Process line filter results
                            line_processed = self._process_line_filter_results(
                                filter_result, line_filter_config, file_path
                            )
                            
                            # Collect processed line filter result with file context
                            all_line_filter_results.append({
                                "file_path": file_path,
                                "line_filter_id": line_filter_id,
                                "pattern": pattern,
                                "result": line_processed
                            })
                        except CancelledError:
                            logger.info(f"{self._module_name}: Analysis cancelled")
                            raise
                        except Exception as e:
                            logger.error(f"{self._module_name}: Error processing line filter '{line_filter_id}' for file '{file_path}': {e}", exc_info=True)
                            # Continue with other line filters
                
                # EXCLUSIVE: Process file filter results (aggregate all processed line filter results)
                file_filter_processed = self._process_file_filter_results(
                    file_filter_id, all_line_filter_results, file_filter_config
                )
                
                path_file_filter_results.append(file_filter_processed)
        
        # 7. Create final InsightResult for this path (aggregate all file filter results)
        insight_result = self._create_insight_result(
            user_path, path_file_filter_results, self._config
        )
        
        total_elapsed = time.time() - start_time
        logger.info(f"{self._module_name}: Analysis complete for path '{user_path}' in {total_elapsed:.2f}s")
        
        return insight_result
    

