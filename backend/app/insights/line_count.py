"""Insight to count lines in log files."""

from typing import List, Optional, Callable, Awaitable
import logging
import asyncio
import os
from app.insights.base import Insight
from app.core.models import InsightResult, ProgressEvent
from app.services.file_handler import read_file_lines, CancelledError

logger = logging.getLogger(__name__)


class LineCount(Insight):
    """Counts lines in log files."""
    
    @property
    def id(self) -> str:
        return "line_count"
    
    @property
    def name(self) -> str:
        return "Line Count"
    
    @property
    def description(self) -> str:
        return "Counts total lines, empty lines, and non-empty lines in log files"
    
    async def analyze(
        self,
        file_paths: List[str],
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> InsightResult:
        """
        Analyze files and count lines.
        
        Uses efficient line-by-line processing to handle large files.
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            InsightResult with line count summary
        """
        import time
        start_time = time.time()
        logger.info(f"LineCount: Starting analysis of {len(file_paths)} file(s)")
        
        file_results = []
        total_lines = 0
        total_empty = 0
        total_non_empty = 0
        
        for file_idx, file_path in enumerate(file_paths, 1):
            # Check for cancellation at start of each file
            if cancellation_event and cancellation_event.is_set():
                logger.info(f"LineCount: Analysis cancelled")
                raise CancelledError("Analysis cancelled")
            
            file_start_time = time.time()
            logger.info(f"LineCount: Processing file {file_idx}/{len(file_paths)}: {file_path}")
            
            # Get file size for progress tracking
            file_size_mb = 0.0
            try:
                file_size_bytes = os.path.getsize(file_path)
                file_size_mb = file_size_bytes / (1024 * 1024)
            except Exception:
                pass
            
            # Emit file_open event
            if progress_callback:
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
            
            try:
                line_count = 0
                empty_count = 0
                non_empty_count = 0
                last_log_time = time.time()
                last_progress_event_time = time.time()
                
                # Process file line by line to handle large files efficiently
                for line in read_file_lines(file_path, cancellation_event=cancellation_event):
                    line_count += 1
                    if not line.strip():
                        empty_count += 1
                    else:
                        non_empty_count += 1
                    
                    # Emit progress event every 50k lines or every 2 seconds
                    if progress_callback and (line_count % 50000 == 0 or (time.time() - last_progress_event_time) >= 2.0):
                        await progress_callback(ProgressEvent(
                            type="insight_progress",
                            message=f"Processing {os.path.basename(file_path)}: {line_count:,} lines",
                            task_id="",  # Will be set by callback
                            insight_id="",  # Will be set by callback
                            file_path=file_path,
                            file_index=file_idx,
                            total_files=len(file_paths),
                            lines_processed=line_count,
                            file_size_mb=file_size_mb
                        ))
                        last_progress_event_time = time.time()
                    
                    # Log progress for large files every 100k lines
                    if line_count % 100000 == 0:
                        elapsed = time.time() - last_log_time
                        logger.debug(f"LineCount: Processed {line_count:,} lines from {file_path} ({line_count/elapsed:.0f} lines/sec)")
                        last_log_time = time.time()
                
                file_elapsed = time.time() - file_start_time
                file_results.append({
                    "file": file_path,
                    "total": line_count,
                    "empty": empty_count,
                    "non_empty": non_empty_count
                })
                
                total_lines += line_count
                total_empty += empty_count
                total_non_empty += non_empty_count
                
                logger.info(f"LineCount: Completed {file_path} - {line_count:,} total lines ({empty_count:,} empty, {non_empty_count:,} non-empty) in {file_elapsed:.2f}s")
            except CancelledError:
                logger.info(f"LineCount: Analysis cancelled while processing {file_path}")
                raise
            except Exception as e:
                logger.error(f"LineCount: Failed to process {file_path}: {e}", exc_info=True)
                file_results.append({
                    "file": file_path,
                    "error": f"Failed to read file: {str(e)}"
                })
        
        total_elapsed = time.time() - start_time
        logger.info(f"LineCount: Analysis complete - {total_lines:,} total lines across {len(file_paths)} file(s) in {total_elapsed:.2f}s")
        
        # Format results
        result_text = f"Line Count Summary\n"
        result_text += f"{'=' * 50}\n\n"
        result_text += f"Files analyzed: {len(file_paths)}\n\n"
        result_text += f"Total across all files:\n"
        result_text += f"  Total lines: {total_lines:,}\n"
        result_text += f"  Empty lines: {total_empty:,}\n"
        result_text += f"  Non-empty lines: {total_non_empty:,}\n\n"
        result_text += f"Per-file breakdown:\n"
        
        for file_result in file_results:
            if "error" in file_result:
                result_text += f"\n{file_result['file']}\n"
                result_text += f"  Error: {file_result['error']}\n"
            else:
                result_text += f"\n{file_result['file']}\n"
                result_text += f"  Total: {file_result['total']:,}\n"
                result_text += f"  Empty: {file_result['empty']:,}\n"
                result_text += f"  Non-empty: {file_result['non_empty']:,}\n"
        
        return InsightResult(
            result_type="text",
            content=result_text,
            metadata={
                "total_lines": total_lines,
                "total_empty": total_empty,
                "total_non_empty": total_non_empty,
                "files_analyzed": len(file_paths)
            }
        )


if __name__ == "__main__":
    # Hardcoded default file paths for quick testing
    # Override by providing CLI arguments
    DEFAULT_FILE_PATHS = [
        # Add your default test file paths here, e.g.:
        # "/path/to/test/logfile.log",
    ]
    
    import sys
    from app.utils.insight_runner import main_standalone
    
    # Get file paths from CLI args, hardcoded defaults, or interactive input
    if len(sys.argv) > 1:
        file_paths = [arg for arg in sys.argv[1:] if arg not in ["--verbose", "-v"]]
    elif DEFAULT_FILE_PATHS:
        file_paths = DEFAULT_FILE_PATHS
    else:
        # Interactive mode
        print("Enter file paths (one per line, empty line to finish):", file=sys.stderr)
        file_paths = []
        while True:
            try:
                line = input().strip()
                if not line:
                    break
                file_paths.append(line)
            except (EOFError, KeyboardInterrupt):
                break
        
        if not file_paths:
            print("No file paths provided. Exiting.", file=sys.stderr)
            sys.exit(1)
    
    # Check for verbose flag
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    # Run the insight
    main_standalone(LineCount(), file_paths, verbose=verbose)
