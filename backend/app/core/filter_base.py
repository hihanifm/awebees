"""Base classes and utilities for filter-based insights."""

from enum import Enum
from typing import List, Optional, Dict, Callable, Awaitable
import re
import logging
import asyncio
import os
from pathlib import Path
from app.core.insight_base import Insight
from app.core.models import InsightResult, ProgressEvent
from app.services.file_handler import read_file_lines, read_file_chunks, CancelledError

logger = logging.getLogger(__name__)


class ReadingMode(Enum):
    """File reading mode for line filtering."""
    LINES = "lines"  # Line-by-line reading using read_file_lines()
    CHUNKS = "chunks"  # Chunk-based reading using read_file_chunks()


class FilterResult:
    """Result of filtering operations with filtered lines grouped by file."""
    
    def __init__(self):
        """Initialize empty filter result."""
        self._lines_by_file: Dict[str, List[str]] = {}
    
    def add_line(self, file_path: str, line: str) -> None:
        """Add a filtered line for a file."""
        if file_path not in self._lines_by_file:
            self._lines_by_file[file_path] = []
        self._lines_by_file[file_path].append(line)
    
    def get_lines(self) -> List[str]:
        """Get all filtered lines as a flat list."""
        all_lines = []
        for lines in self._lines_by_file.values():
            all_lines.extend(lines)
        return all_lines
    
    def get_lines_by_file(self) -> Dict[str, List[str]]:
        """Get filtered lines grouped by file path."""
        return self._lines_by_file.copy()
    
    def get_file_count(self) -> int:
        """Get number of files with matching lines."""
        return len(self._lines_by_file)
    
    def get_total_line_count(self) -> int:
        """Get total number of filtered lines."""
        return sum(len(lines) for lines in self._lines_by_file.values())


class FileFilter:
    """Builder class for filtering files from folders with regex patterns."""
    
    def __init__(self, file_paths: List[str]):
        """
        Initialize file filter with file/folder paths.
        
        Args:
            file_paths: List of file or folder paths
        """
        self._file_paths = file_paths
        self._filtered_files: Optional[List[str]] = None
        self._file_patterns: List[str] = []
    
    def _list_files_sync(self, folder_path: str) -> List[str]:
        """Synchronously list files in a folder (helper for sync contexts)."""
        folder = Path(folder_path)
        if not folder.is_dir():
            return []
        files = [str(p.resolve()) for p in folder.rglob("*") if p.is_file()]
        return sorted(files)
    
    def filter_files(self, *patterns: str) -> 'FileFilter':
        """
        Apply file filtering patterns to folders.
        
        File filtering is only applied when input contains folder paths.
        Individual file paths pass through unchanged.
        Multiple patterns use OR logic - a file matches if it matches any pattern.
        
        Args:
            *patterns: One or more regex patterns for filtering files in folders
            
        Returns:
            Self for chaining
        """
        self._file_patterns = list(patterns)
        self._filtered_files = None  # Reset filtered files
        return self
    
    def get_files(self) -> List[str]:
        """
        Get filtered file list.
        
        Returns:
            List of file paths (filtered if patterns were applied)
        """
        if self._filtered_files is not None:
            logger.debug(f"FileFilter: Returning cached file list ({len(self._filtered_files)} files)")
            return self._filtered_files
        
        logger.info(f"FileFilter: Processing {len(self._file_paths)} input path(s)")
        all_files = []
        
        for path in self._file_paths:
            path_obj = Path(path)
            
            if path_obj.is_file():
                # Individual file paths pass through unchanged
                resolved_path = str(path_obj.resolve())
                logger.debug(f"FileFilter: Added file: {resolved_path}")
                all_files.append(resolved_path)
            elif path_obj.is_dir():
                # Folder paths: expand to files and apply filtering
                try:
                    logger.info(f"FileFilter: Expanding folder: {path}")
                    # Use sync file listing (list_files_in_folder is async but we're in sync context)
                    folder_files = self._list_files_sync(str(path_obj.resolve()))
                    logger.debug(f"FileFilter: Found {len(folder_files)} files in folder {path}")
                    
                    if self._file_patterns:
                        # Apply file filtering patterns (OR logic)
                        logger.info(f"FileFilter: Applying {len(self._file_patterns)} file filter pattern(s): {self._file_patterns}")
                        compiled_patterns = [re.compile(pattern) for pattern in self._file_patterns]
                        matching_files = []
                        for file_path in folder_files:
                            file_name = Path(file_path).name
                            if any(pattern.search(file_name) for pattern in compiled_patterns):
                                matching_files.append(file_path)
                        logger.info(f"FileFilter: {len(matching_files)} files matched filter pattern(s) from {len(folder_files)} total files")
                        all_files.extend(matching_files)
                    else:
                        # No patterns: include all files
                        logger.debug(f"FileFilter: No file filter patterns, including all {len(folder_files)} files")
                        all_files.extend(folder_files)
                except Exception as e:
                    logger.error(f"FileFilter: Error processing folder {path}: {e}", exc_info=True)
                    # Continue with other paths
            else:
                logger.warning(f"FileFilter: Path is neither file nor folder: {path}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for file_path in all_files:
            if file_path not in seen:
                seen.add(file_path)
                unique_files.append(file_path)
        
        logger.info(f"FileFilter: Final file list: {len(unique_files)} unique file(s)")
        self._filtered_files = unique_files
        return self._filtered_files
    
    async def apply(self, line_filter: 'LineFilter', cancellation_event: Optional[asyncio.Event] = None, progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None) -> FilterResult:
        """
        Apply line filter to filtered files.
        
        Args:
            line_filter: LineFilter instance to apply
            cancellation_event: Optional asyncio.Event to check for cancellation
            progress_callback: Optional async callback to emit progress events
            
        Returns:
            FilterResult with filtered lines
        """
        files = self.get_files()
        return await line_filter.filter_lines(files, cancellation_event, progress_callback)


class LineFilter:
    """Filter class for filtering lines within files using regex patterns."""
    
    def __init__(
        self,
        pattern: str,
        reading_mode: ReadingMode = ReadingMode.LINES,
        chunk_size: int = 1048576,
        flags: int = 0
    ):
        """
        Initialize line filter.
        
        Args:
            pattern: Regex pattern for filtering lines
            reading_mode: Reading mode - LINES (default) or CHUNKS
            chunk_size: Chunk size in bytes (only used for CHUNKS mode, default: 1MB)
            flags: Regex flags (e.g., re.IGNORECASE)
        """
        self.pattern = pattern
        self.reading_mode = reading_mode
        self.chunk_size = chunk_size
        self.flags = flags
        self._compiled_pattern = re.compile(pattern, flags)
    
    async def filter_lines(
        self,
        file_paths: List[str],
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> FilterResult:
        """
        Filter lines from files using the configured pattern and reading mode.
        
        Args:
            file_paths: List of file paths to process
            cancellation_event: Optional asyncio.Event to check for cancellation
            progress_callback: Optional async callback to emit progress events
            
        Returns:
            FilterResult with filtered lines
            
        Raises:
            CancelledError: If operation is cancelled
        """
        import time
        result = FilterResult()
        logger.info(f"LineFilter: Starting line filtering with pattern '{self.pattern}' (mode: {self.reading_mode.value}, flags: {self.flags})")
        logger.info(f"LineFilter: Processing {len(file_paths)} file(s)")
        
        for file_idx, file_path in enumerate(file_paths, 1):
            # Check for cancellation at start of each file
            if cancellation_event and cancellation_event.is_set():
                logger.info(f"LineFilter: Analysis cancelled before processing file {file_idx}/{len(file_paths)}")
                raise CancelledError("Analysis cancelled")
            
            file_start_time = time.time()
            logger.info(f"LineFilter: Processing file {file_idx}/{len(file_paths)}: {file_path}")
            
            # Get file size for progress tracking
            file_size_mb = 0.0
            try:
                file_size_bytes = os.path.getsize(file_path)
                file_size_mb = file_size_bytes / (1024 * 1024)
                logger.debug(f"LineFilter: File size: {file_size_mb:.2f} MB ({file_size_bytes:,} bytes)")
            except Exception as e:
                logger.warning(f"LineFilter: Could not get file size for {file_path}: {e}")
            
            # Emit file_open event
            if progress_callback:
                try:
                    await progress_callback(ProgressEvent(
                        type="file_open",
                        message=f"Opening file {file_idx}/{len(file_paths)}: {os.path.basename(file_path)}",
                        task_id="",  # Will be set by callback
                        insight_id="",  # Will be set by callback
                        file_path=file_path,
                        file_index=file_idx,
                        total_files=len(file_paths),
                        file_size_mb=file_size_mb
                    ))
                    logger.debug(f"LineFilter: file_open event emitted for {file_path}")
                except Exception as e:
                    logger.error(f"LineFilter: Error emitting file_open event: {e}", exc_info=True)
            else:
                logger.debug(f"LineFilter: No progress_callback provided, skipping file_open event")
            
            try:
                file_lines = []
                
                if self.reading_mode == ReadingMode.LINES:
                    # Line-by-line reading mode
                    logger.debug(f"LineFilter: Using line-by-line reading mode for {file_path}")
                    file_lines = await self._filter_lines_mode(file_path, cancellation_event)
                elif self.reading_mode == ReadingMode.CHUNKS:
                    # Chunk-based reading mode
                    logger.debug(f"LineFilter: Using chunk-based reading mode (chunk_size: {self.chunk_size:,} bytes) for {file_path}")
                    file_lines = await self._filter_chunks_mode(file_path, cancellation_event)
                
                # Store filtered lines
                for line in file_lines:
                    result.add_line(file_path, line)
                
                file_elapsed = time.time() - file_start_time
                logger.info(f"LineFilter: Completed {file_path} - {len(file_lines)} matching lines found in {file_elapsed:.2f}s ({len(file_lines)/file_elapsed:.1f} lines/sec)")
                
                # Emit progress event after file processing
                if progress_callback:
                    try:
                        await progress_callback(ProgressEvent(
                            type="insight_progress",
                            message=f"Processed {os.path.basename(file_path)}: {len(file_lines)} matching lines",
                            task_id="",  # Will be set by callback
                            insight_id="",  # Will be set by callback
                            file_path=file_path,
                            file_index=file_idx,
                            total_files=len(file_paths),
                            lines_processed=0,  # Not tracking line numbers in simple mode
                            file_size_mb=file_size_mb
                        ))
                        logger.debug(f"LineFilter: Progress event emitted for {file_path}")
                    except Exception as e:
                        logger.error(f"LineFilter: Error emitting progress event: {e}", exc_info=True)
                        
            except CancelledError:
                logger.info(f"LineFilter: Analysis cancelled while processing {file_path}")
                raise
            except Exception as e:
                logger.error(f"LineFilter: Failed to process {file_path}: {e}", exc_info=True)
                # Continue with other files
        
        total_lines = result.get_total_line_count()
        file_count = result.get_file_count()
        logger.info(f"LineFilter: Line filtering complete - {total_lines} total matching lines across {file_count} file(s)")
        return result
    
    async def _filter_lines_mode(
        self,
        file_path: str,
        cancellation_event: Optional[asyncio.Event] = None
    ) -> List[str]:
        """Filter lines using line-by-line reading mode."""
        matching_lines = []
        total_lines_checked = 0
        
        logger.debug(f"LineFilter: Starting line-by-line filtering for {file_path}")
        for line in read_file_lines(file_path, cancellation_event=cancellation_event):
            total_lines_checked += 1
            if self._compiled_pattern.search(line):
                matching_lines.append(line)
        logger.debug(f"LineFilter: Line-by-line filtering complete - {len(matching_lines)} matches from {total_lines_checked:,} lines checked")
        return matching_lines
    
    async def _filter_chunks_mode(
        self,
        file_path: str,
        cancellation_event: Optional[asyncio.Event] = None
    ) -> List[str]:
        """Filter lines using chunk-based reading mode."""
        matching_lines = []
        chunk_buffer = ""  # Buffer for incomplete lines at chunk boundaries
        chunk_count = 0
        total_lines_checked = 0
        
        logger.debug(f"LineFilter: Starting chunk-based filtering for {file_path} (chunk_size: {self.chunk_size:,} bytes)")
        for chunk in read_file_chunks(file_path, chunk_size=self.chunk_size, cancellation_event=cancellation_event):
            chunk_count += 1
            # Combine chunk with buffer (handles lines split across chunks)
            text_to_process = chunk_buffer + chunk
            chunk_buffer = ""  # Clear buffer, will rebuild if needed
            
            # Process chunk line by line
            if text_to_process:
                # Find last newline to determine if chunk ends with complete line
                last_newline_idx = text_to_process.rfind('\n')
                if last_newline_idx == -1:
                    last_newline_idx = text_to_process.rfind('\r')
                
                if last_newline_idx == -1:
                    # No newline in this chunk, entire chunk is incomplete line
                    chunk_buffer = text_to_process
                else:
                    # Split at newlines, keep complete lines
                    complete_text = text_to_process[:last_newline_idx + 1]
                    lines = complete_text.splitlines(keepends=True)
                    # Save any incomplete line after last newline as buffer
                    if last_newline_idx + 1 < len(text_to_process):
                        chunk_buffer = text_to_process[last_newline_idx + 1:]
                    
                    # Apply regex pattern to each complete line
                    for line in lines:
                        total_lines_checked += 1
                        if self._compiled_pattern.search(line):
                            matching_lines.append(line)
        
        # Process any remaining buffer content (last incomplete line if file doesn't end with newline)
        if chunk_buffer.strip():
            total_lines_checked += 1
            if self._compiled_pattern.search(chunk_buffer):
                matching_lines.append(chunk_buffer)
        
        logger.debug(f"LineFilter: Chunk-based filtering complete - {len(matching_lines)} matches from {total_lines_checked:,} lines checked across {chunk_count} chunk(s)")
        return matching_lines


class FilterBasedInsight(Insight):
    """Base class for filter-based insights that simplifies file and line filtering."""
    
    @property
    def file_filter_patterns(self) -> Optional[List[str]]:
        """
        Return file filter patterns for folders.
        
        Returns None to skip file filtering (process all files in folders).
        Return a list of regex patterns to filter files (OR logic).
        
        Returns:
            Optional list of regex patterns for filtering files in folders
        """
        return None
    
    @property
    def line_filter_pattern(self) -> str:
        """
        Return regex pattern for filtering lines.
        
        Returns:
            Regex pattern string for line filtering
        """
        raise NotImplementedError("Subclasses must implement line_filter_pattern")
    
    @property
    def reading_mode(self) -> ReadingMode:
        """
        Return reading mode for file processing.
        
        Returns:
            ReadingMode.LINES (default) or ReadingMode.CHUNKS
        """
        return ReadingMode.LINES
    
    @property
    def chunk_size(self) -> int:
        """
        Return chunk size for CHUNKS reading mode.
        
        Returns:
            Chunk size in bytes (default: 1MB)
        """
        return 1048576
    
    async def _process_filtered_lines(
        self,
        filter_result: FilterResult
    ) -> InsightResult:
        """
        Process filtered lines and return InsightResult.
        
        Subclasses must implement this method to format the filtered lines
        into an InsightResult.
        
        Args:
            filter_result: FilterResult containing filtered lines
            
        Returns:
            InsightResult with formatted output
        """
        raise NotImplementedError("Subclasses must implement _process_filtered_lines")
    
    async def analyze(
        self,
        file_paths: List[str],
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> InsightResult:
        """
        Analyze files using file and line filtering.
        
        Args:
            file_paths: List of file or folder paths to analyze
            cancellation_event: Optional asyncio.Event to check for cancellation
            progress_callback: Optional async callback to emit progress events
            
        Returns:
            InsightResult with analysis results
        """
        import time
        start_time = time.time()
        logger.info(f"{self.__class__.__name__}: Starting analysis of {len(file_paths)} path(s)")
        logger.debug(f"{self.__class__.__name__}: Line filter pattern: '{self.line_filter_pattern}'")
        logger.debug(f"{self.__class__.__name__}: Reading mode: {self.reading_mode.value}")
        if self.reading_mode == ReadingMode.CHUNKS:
            logger.debug(f"{self.__class__.__name__}: Chunk size: {self.chunk_size:,} bytes")
        
        # Create file filter
        file_filter = FileFilter(file_paths)
        
        # Apply file filtering if patterns provided
        file_patterns = self.file_filter_patterns
        if file_patterns:
            logger.info(f"{self.__class__.__name__}: Applying file filter patterns: {file_patterns}")
            file_filter.filter_files(*file_patterns)
        else:
            logger.debug(f"{self.__class__.__name__}: No file filter patterns, processing all files/folders")
        
        # Create line filter with optional regex flags
        regex_flags = 0
        if hasattr(self, 'regex_flags'):
            regex_flags = self.regex_flags if isinstance(self.regex_flags, int) else self.regex_flags()
            logger.debug(f"{self.__class__.__name__}: Using regex flags: {regex_flags}")
        
        line_filter = LineFilter(
            pattern=self.line_filter_pattern,
            reading_mode=self.reading_mode,
            chunk_size=self.chunk_size,
            flags=regex_flags
        )
        
        # Apply line filtering
        try:
            logger.debug(f"{self.__class__.__name__}: Applying line filter to files")
            filter_result = await file_filter.apply(line_filter, cancellation_event, progress_callback)
            logger.info(f"{self.__class__.__name__}: Line filtering complete - {filter_result.get_total_line_count()} matching lines across {filter_result.get_file_count()} file(s)")
        except CancelledError:
            logger.info(f"{self.__class__.__name__}: Analysis cancelled")
            raise
        
        # Process filtered lines
        logger.debug(f"{self.__class__.__name__}: Processing filtered lines")
        result = await self._process_filtered_lines(filter_result)
        
        total_elapsed = time.time() - start_time
        logger.info(f"{self.__class__.__name__}: Analysis complete in {total_elapsed:.2f}s")
        
        return result

