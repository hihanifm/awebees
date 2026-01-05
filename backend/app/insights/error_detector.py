"""Insight to detect errors in log files."""

# Check for venv before imports if running as main
if __name__ == "__main__":
    import sys
    import os
    from pathlib import Path
    
    # Always ensure backend directory is in Python path
    current_file = Path(__file__).resolve()
    backend_dir = current_file.parent.parent.parent  # backend/app/insights -> backend
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    # Check if we're in a venv
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        # Try to find venv Python relative to this file
        venv_python = backend_dir / "venv" / "bin" / "python"
        
        if venv_python.exists():
            # Set PYTHONPATH to include backend directory and re-execute with venv Python
            env = os.environ.copy()
            pythonpath = env.get('PYTHONPATH', '')
            if pythonpath:
                env['PYTHONPATH'] = f"{backend_dir}:{pythonpath}"
            else:
                env['PYTHONPATH'] = str(backend_dir)
            
            # Change to backend directory and re-execute
            os.chdir(str(backend_dir))
            os.execve(str(venv_python), [str(venv_python)] + sys.argv, env)

from typing import List, Optional, Callable, Awaitable
import re
import logging
import asyncio
import os
from app.insights.base import Insight
from app.core.models import InsightResult, ProgressEvent
from app.services.file_handler import read_file_lines, CancelledError

logger = logging.getLogger(__name__)


class ErrorDetector(Insight):
    """Detects ERROR and FATAL log lines."""
    
    @property
    def id(self) -> str:
        return "error_detector"
    
    @property
    def name(self) -> str:
        return "Error Detector"
    
    @property
    def description(self) -> str:
        return "Detects ERROR and FATAL log lines in log files"
    
    async def analyze(
        self,
        file_paths: List[str],
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> InsightResult:
        """
        Analyze files for error and fatal log lines.
        
        Uses efficient line-by-line processing to handle large files.
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            InsightResult with error summary
        """
        import time
        start_time = time.time()
        logger.info(f"ErrorDetector: Starting analysis of {len(file_paths)} file(s)")
        
        all_errors = []
        error_pattern = re.compile(r".*\b(ERROR|FATAL)\b.*", re.IGNORECASE)
        max_errors_per_file = 1000  # Limit to prevent overwhelming output
        
        for file_idx, file_path in enumerate(file_paths, 1):
            # Check for cancellation at start of each file
            if cancellation_event and cancellation_event.is_set():
                logger.info(f"ErrorDetector: Analysis cancelled")
                raise CancelledError("Analysis cancelled")
            
            file_start_time = time.time()
            logger.info(f"ErrorDetector: Processing file {file_idx}/{len(file_paths)}: {file_path}")
            
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
                file_errors = []
                line_num = 0
                last_log_time = time.time()
                last_progress_event_time = time.time()
                
                # Process file line by line to handle large files efficiently
                for line in read_file_lines(file_path, cancellation_event=cancellation_event):
                    line_num += 1
                    
                    # Emit progress event every 50k lines or every 2 seconds
                    if progress_callback and (line_num % 50000 == 0 or (time.time() - last_progress_event_time) >= 2.0):
                        elapsed = time.time() - last_log_time
                        await progress_callback(ProgressEvent(
                            type="insight_progress",
                            message=f"Processing {os.path.basename(file_path)}: {line_num:,} lines (errors found: {len(file_errors)})",
                            task_id="",  # Will be set by callback
                            insight_id="",  # Will be set by callback
                            file_path=file_path,
                            file_index=file_idx,
                            total_files=len(file_paths),
                            lines_processed=line_num,
                            file_size_mb=file_size_mb
                        ))
                        last_progress_event_time = time.time()
                    
                    # Log progress for large files every 100k lines
                    if line_num % 100000 == 0:
                        elapsed = time.time() - last_log_time
                        logger.debug(f"ErrorDetector: Processed {line_num:,} lines from {file_path} (errors found: {len(file_errors)}, {line_num/elapsed:.0f} lines/sec)")
                        last_log_time = time.time()
                    
                    if error_pattern.search(line):
                        file_errors.append({
                            "line": line_num,
                            "content": line.strip()[:200]  # Truncate long lines
                        })
                        
                        # Limit errors per file to prevent memory issues
                        if len(file_errors) >= max_errors_per_file:
                            logger.warning(f"ErrorDetector: Reached error limit ({max_errors_per_file}) for {file_path} at line {line_num}")
                            file_errors.append({
                                "line": line_num + 1,
                                "content": f"... (showing first {max_errors_per_file} errors, file continues)"
                            })
                            break
                
                file_elapsed = time.time() - file_start_time
                logger.info(f"ErrorDetector: Completed {file_path} - {line_num:,} lines processed, {len(file_errors)} errors found in {file_elapsed:.2f}s")
                
                if file_errors:
                    all_errors.append({
                        "file": file_path,
                        "count": len(file_errors),
                        "errors": file_errors[:50]  # Limit to first 50 errors per file for output
                    })
            except CancelledError:
                logger.info(f"ErrorDetector: Analysis cancelled while processing {file_path}")
                raise
            except Exception as e:
                logger.error(f"ErrorDetector: Failed to process {file_path}: {e}", exc_info=True)
                all_errors.append({
                    "file": file_path,
                    "error": f"Failed to read file: {str(e)}"
                })
        
        total_elapsed = time.time() - start_time
        total_errors = sum(err.get("count", 0) for err in all_errors if "count" in err)
        logger.info(f"ErrorDetector: Analysis complete - {total_errors} total errors found across {len(file_paths)} file(s) in {total_elapsed:.2f}s")
        
        # Format results
        total_errors = sum(err.get("count", 0) for err in all_errors if "count" in err)
        
        result_text = f"Error Detection Summary\n"
        result_text += f"{'=' * 50}\n\n"
        result_text += f"Total errors found: {total_errors}\n"
        result_text += f"Files with errors: {len([e for e in all_errors if 'count' in e])}\n\n"
        
        for file_result in all_errors:
            if "error" in file_result:
                result_text += f"File: {file_result['file']}\n"
                result_text += f"  Error reading file: {file_result['error']}\n\n"
            else:
                result_text += f"File: {file_result['file']}\n"
                result_text += f"  Errors found: {file_result['count']}\n"
                for err in file_result['errors'][:10]:  # Show first 10 errors per file
                    result_text += f"    Line {err['line']}: {err['content']}\n"
                if file_result['count'] > 10:
                    result_text += f"    ... and {file_result['count'] - 10} more errors\n"
                result_text += "\n"
        
        return InsightResult(
            result_type="text",
            content=result_text,
            metadata={"total_errors": total_errors, "files_analyzed": len(file_paths)}
        )


if __name__ == "__main__":
    # Hardcoded default file paths for quick testing
    # Override by providing CLI arguments
    DEFAULT_FILE_PATHS = [
        # Add your default test file paths here, e.g.:
        # "/path/to/test/logfile.log",
    ]
    
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
    main_standalone(ErrorDetector(), file_paths, verbose=verbose)
