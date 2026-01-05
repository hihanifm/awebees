"""Insight to detect and summarize application crashes in log files."""

from typing import List, Optional, Callable, Awaitable, Dict, Any
import logging
import asyncio
import os
from collections import defaultdict
from app.insights.base import Insight
from app.core.models import InsightResult, ProgressEvent
from app.services.file_handler import read_file_chunks, CancelledError

logger = logging.getLogger(__name__)


class CrashDetector(Insight):
    """Detects and summarizes application crashes in log files."""
    
    @property
    def id(self) -> str:
        return "crash_detector"
    
    @property
    def name(self) -> str:
        return "Crash Detector"
    
    @property
    def description(self) -> str:
        return "Detects and summarizes actual application crashes including segmentation faults, fatal exceptions, stack traces, and process termination errors"
    
    def __init__(self):
        """Initialize crash detection - simple string search for 'FATAL EXCEPTION'."""
        pass
    
    def _detect_crash_type(self, line: str, context_lines: List[str]) -> Optional[Dict[str, Any]]:
        """
        Detect crash by searching for 'FATAL EXCEPTION' string.
        
        Args:
            line: Current line being analyzed
            context_lines: Previous lines for context (unused, kept for compatibility)
            
        Returns:
            Dictionary with crash type and details, or None if no crash detected
        """
        # Simple string search for "FATAL EXCEPTION"
        if "FATAL EXCEPTION" in line:
            return {
                "type": "fatal_exception",
                "line_content": line.strip()[:500],  # Truncate long lines
                "timestamp": None,
                "context": "\n".join(context_lines[-3:] + [line])[:1000]  # Last 3 lines + current, max 1000 chars
            }
        
        return None
    
    async def analyze(
        self,
        file_paths: List[str],
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> InsightResult:
        """
        Analyze files for crashes and provide a summary.
        
        Uses efficient line-by-line processing to handle large files.
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            InsightResult with crash summary
        """
        import time
        start_time = time.time()
        logger.info(f"CrashDetector: Starting analysis of {len(file_paths)} file(s)")
        logger.debug(f"CrashDetector: progress_callback provided: {progress_callback is not None}, cancellation_event provided: {cancellation_event is not None}")
        
        all_crashes = []
        crash_summary_by_type = defaultdict(int)
        max_crashes_per_file = 500  # Limit to prevent overwhelming output
        
        for file_idx, file_path in enumerate(file_paths, 1):
            # Check for cancellation at start of each file
            if cancellation_event and cancellation_event.is_set():
                logger.info(f"CrashDetector: Analysis cancelled")
                raise CancelledError("Analysis cancelled")
            
            file_start_time = time.time()
            logger.info(f"CrashDetector: Processing file {file_idx}/{len(file_paths)}: {file_path}")
            
            # Get file size for progress tracking
            file_size_mb = 0.0
            try:
                file_size_bytes = os.path.getsize(file_path)
                file_size_mb = file_size_bytes / (1024 * 1024)
                logger.debug(f"CrashDetector: File size: {file_size_mb:.2f} MB ({file_size_bytes:,} bytes)")
            except Exception as e:
                logger.warning(f"CrashDetector: Could not get file size for {file_path}: {e}")
            
            # Emit file_open event
            if progress_callback:
                logger.debug(f"CrashDetector: Emitting file_open event for {file_path}")
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
                    logger.debug(f"CrashDetector: file_open event emitted successfully")
                except Exception as e:
                    logger.error(f"CrashDetector: Error emitting file_open event: {e}", exc_info=True)
            else:
                logger.warning(f"CrashDetector: No progress_callback provided, skipping file_open event")
            
            try:
                file_crashes = []
                line_num = 0
                context_lines = []  # Keep last few lines for context (preserves across chunks)
                last_log_time = time.time()
                chunk_buffer = ""  # Buffer for incomplete lines at chunk boundaries
                chunk_count = 0
                chunk_start_time = time.time()
                
                logger.debug(f"CrashDetector: Starting chunk processing for {file_path}")
                
                # Step 1: Read file in chunks, then Step 2: Process each chunk line by line
                # This approach handles large files efficiently while maintaining line-by-line processing
                for chunk in read_file_chunks(file_path, chunk_size=1048576, cancellation_event=cancellation_event):  # 1MB chunks
                    chunk_count += 1
                    chunk_read_time = time.time()
                    chunk_size_bytes = len(chunk.encode('utf-8')) if chunk else 0
                    logger.debug(f"CrashDetector: Read chunk {chunk_count} ({chunk_size_bytes:,} bytes, {len(chunk):,} chars) in {(chunk_read_time - chunk_start_time)*1000:.2f}ms")
                    
                    # Check for cancellation at chunk level
                    if cancellation_event and cancellation_event.is_set():
                        logger.info(f"CrashDetector: Analysis cancelled at line {line_num}")
                        raise CancelledError("Analysis cancelled")
                    
                    # Combine chunk with buffer (handles lines split across chunks)
                    text_to_process = chunk_buffer + chunk
                    chunk_buffer = ""  # Clear buffer, will rebuild if needed
                    
                    # Step 2: Process chunk line by line
                    # Split into lines, preserving line endings
                    if text_to_process:
                        # Find last newline to determine if chunk ends with complete line
                        last_newline_idx = text_to_process.rfind('\n')
                        if last_newline_idx == -1:
                            last_newline_idx = text_to_process.rfind('\r')
                        
                        if last_newline_idx == -1:
                            # No newline in this chunk, entire chunk is incomplete line
                            chunk_buffer = text_to_process
                            lines = []
                            logger.debug(f"CrashDetector: Chunk {chunk_count} has no newlines, buffering entire chunk")
                        else:
                            # Split at newlines, keep complete lines (include the newline character)
                            complete_text = text_to_process[:last_newline_idx + 1]
                            lines = complete_text.splitlines(keepends=True)
                            # Save any incomplete line after last newline as buffer
                            if last_newline_idx + 1 < len(text_to_process):
                                chunk_buffer = text_to_process[last_newline_idx + 1:]
                            logger.debug(f"CrashDetector: Chunk {chunk_count} split into {len(lines)} complete lines, buffer size: {len(chunk_buffer)} chars")
                    else:
                        lines = []
                        logger.debug(f"CrashDetector: Chunk {chunk_count} is empty after processing")
                    
                    # Process each line from the chunk - NO overhead except core regex processing
                    lines_start_time = time.time()
                    for line in lines:
                        line_num += 1
                        context_lines.append(line)
                        
                        # Keep only last 10 lines for context
                        if len(context_lines) > 10:
                            context_lines.pop(0)
                        
                        # Detect crashes - core processing only
                        crash_info = self._detect_crash_type(line, context_lines)
                        if crash_info:
                            crash_info["line"] = line_num
                            file_crashes.append(crash_info)
                            crash_summary_by_type[crash_info["type"]] += 1
                            logger.debug(f"CrashDetector: Crash detected at line {line_num}: {crash_info['type']}")
                    
                    lines_process_time = time.time() - lines_start_time
                    logger.debug(f"CrashDetector: Processed {len(lines)} lines from chunk {chunk_count} in {lines_process_time*1000:.2f}ms ({len(lines)/lines_process_time:.0f} lines/sec)")
                    
                    # Check crash limit after chunk processing (not during line processing)
                    if len(file_crashes) >= max_crashes_per_file:
                        logger.warning(f"CrashDetector: Reached crash limit ({max_crashes_per_file}) for {file_path} at line {line_num}")
                        file_crashes.append({
                            "type": "limit_reached",
                            "line": line_num + 1,
                            "line_content": f"... (showing first {max_crashes_per_file} crashes, file continues)",
                            "timestamp": None,
                            "context": None
                        })
                        break
                    
                    # Emit progress event at chunk boundaries (after processing each chunk)
                    # This ensures progress is visible even during long processing
                    if progress_callback:
                        progress_start_time = time.time()
                        logger.debug(f"CrashDetector: Emitting progress event for chunk {chunk_count} (line {line_num:,}, crashes: {len(file_crashes)})")
                        try:
                            await progress_callback(ProgressEvent(
                                type="insight_progress",
                                message=f"Processing {os.path.basename(file_path)}: {line_num:,} lines (crashes found: {len(file_crashes)})",
                                task_id="",  # Will be set by callback
                                insight_id="",  # Will be set by callback
                                file_path=file_path,
                                file_index=file_idx,
                                total_files=len(file_paths),
                                lines_processed=line_num,
                                file_size_mb=file_size_mb
                            ))
                            progress_time = time.time() - progress_start_time
                            logger.debug(f"CrashDetector: Progress event emitted successfully in {progress_time*1000:.2f}ms")
                            # Yield control to event loop to ensure progress events are processed
                            await asyncio.sleep(0)
                        except Exception as e:
                            logger.error(f"CrashDetector: Error emitting progress event: {e}", exc_info=True)
                    else:
                        logger.debug(f"CrashDetector: No progress_callback, skipping progress event for chunk {chunk_count}")
                    
                    # Log progress for large files every 10 chunks
                    if chunk_count % 10 == 0:
                        elapsed = time.time() - last_log_time
                        logger.info(f"CrashDetector: Processed {chunk_count} chunks ({line_num:,} lines) from {file_path} (crashes found: {len(file_crashes)}, {line_num/elapsed:.0f} lines/sec)")
                        last_log_time = time.time()
                    
                    chunk_start_time = time.time()
                
                # Process any remaining buffer content (last incomplete line if file doesn't end with newline)
                if chunk_buffer.strip():
                    line_num += 1
                    context_lines.append(chunk_buffer)
                    if len(context_lines) > 10:
                        context_lines.pop(0)
                    crash_info = self._detect_crash_type(chunk_buffer, context_lines)
                    if crash_info:
                        crash_info["line"] = line_num
                        file_crashes.append(crash_info)
                        crash_summary_by_type[crash_info["type"]] += 1
                
                file_elapsed = time.time() - file_start_time
                logger.info(f"CrashDetector: Completed {file_path} - {line_num:,} lines processed, {len(file_crashes)} crashes found in {file_elapsed:.2f}s")
                
                if file_crashes:
                    # Remove duplicates that are too close together (likely same crash)
                    deduplicated_crashes = []
                    last_crash_line = -100
                    for crash in file_crashes:
                        if crash.get("type") == "limit_reached":
                            deduplicated_crashes.append(crash)
                        elif abs(crash["line"] - last_crash_line) > 5:  # Consider crashes within 5 lines as duplicates
                            deduplicated_crashes.append(crash)
                            last_crash_line = crash["line"]
                    
                    all_crashes.append({
                        "file": file_path,
                        "count": len(deduplicated_crashes),
                        "crashes": deduplicated_crashes[:50]  # Limit to first 50 crashes per file for output
                    })
            except CancelledError:
                logger.info(f"CrashDetector: Analysis cancelled while processing {file_path}")
                raise
            except Exception as e:
                logger.error(f"CrashDetector: Failed to process {file_path}: {e}", exc_info=True)
                all_crashes.append({
                    "file": file_path,
                    "error": f"Failed to read file: {str(e)}"
                })
        
        total_elapsed = time.time() - start_time
        total_crashes = sum(crash.get("count", 0) for crash in all_crashes if "count" in crash)
        logger.info(f"CrashDetector: Analysis complete - {total_crashes} total crashes found across {len(file_paths)} file(s) in {total_elapsed:.2f}s")
        
        # Format results
        result_text = f"Crash Detection Summary\n"
        result_text += f"{'=' * 60}\n\n"
        result_text += f"Total crashes detected: {total_crashes}\n"
        result_text += f"Files with crashes: {len([c for c in all_crashes if 'count' in c])}\n"
        result_text += f"Files analyzed: {len(file_paths)}\n\n"
        
        # Summary by crash type
        if crash_summary_by_type:
            result_text += f"Crash Types Summary:\n"
            result_text += f"{'-' * 60}\n"
            for crash_type, count in sorted(crash_summary_by_type.items(), key=lambda x: x[1], reverse=True):
                type_display = crash_type.replace("_", " ").title()
                result_text += f"  {type_display}: {count}\n"
            result_text += "\n"
        
        # Detailed crash information per file
        result_text += f"Detailed Crash Information:\n"
        result_text += f"{'-' * 60}\n\n"
        
        for file_result in all_crashes:
            if "error" in file_result:
                result_text += f"File: {file_result['file']}\n"
                result_text += f"  Error reading file: {file_result['error']}\n\n"
            else:
                result_text += f"File: {file_result['file']}\n"
                result_text += f"  Total crashes found: {file_result['count']}\n\n"
                
                # Group crashes by type for this file
                crashes_by_type = defaultdict(list)
                for crash in file_result['crashes']:
                    if crash.get("type") != "limit_reached":
                        crashes_by_type[crash["type"]].append(crash)
                
                # Show crashes grouped by type
                for crash_type, crashes in sorted(crashes_by_type.items()):
                    type_display = crash_type.replace("_", " ").title()
                    result_text += f"  {type_display} ({len(crashes)} occurrence(s)):\n"
                    for crash in crashes[:5]:  # Show first 5 of each type
                        result_text += f"    Line {crash['line']}:\n"
                        # Show truncated crash content
                        crash_content = crash.get('line_content', '')
                        if len(crash_content) > 200:
                            crash_content = crash_content[:200] + "..."
                        result_text += f"      {crash_content}\n"
                    
                    if len(crashes) > 5:
                        result_text += f"      ... and {len(crashes) - 5} more {type_display.lower()} crash(es)\n"
                    result_text += "\n"
                
                # Show limit reached message if present
                for crash in file_result['crashes']:
                    if crash.get("type") == "limit_reached":
                        result_text += f"    {crash['line_content']}\n"
                
                result_text += "\n"
        
        # Provide recommendations
        if total_crashes > 0:
            result_text += f"\nRecommendations:\n"
            result_text += f"{'-' * 60}\n"
            result_text += f"  • Review the crash details above to identify patterns\n"
            result_text += f"  • Check for recurring crash types that may indicate systemic issues\n"
            result_text += f"  • Consider crash context (surrounding log lines) for root cause analysis\n"
        
        return InsightResult(
            result_type="text",
            content=result_text,
            metadata={
                "total_crashes": total_crashes,
                "files_analyzed": len(file_paths),
                "crash_summary_by_type": dict(crash_summary_by_type),
                "files_with_crashes": len([c for c in all_crashes if 'count' in c])
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
    main_standalone(CrashDetector(), file_paths, verbose=verbose)

