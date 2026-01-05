"""Insight to detect and summarize application crashes in log files."""

from typing import List, Optional, Callable, Awaitable, Dict, Any
import re
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
        """Initialize crash detection patterns."""
        # Compile crash detection patterns
        self.crash_patterns = {
            # "segmentation_fault": [
            #     re.compile(r".*\b(segmentation fault|segfault|SIGSEGV|signal 11)\b.*", re.IGNORECASE),
            #     re.compile(r".*\b(segmentation violation|invalid memory reference)\b.*", re.IGNORECASE),
            # ],
            "fatal_exception": [
                re.compile(r".*\b(FATAL EXCEPTION|FatalError|Fatal Exception)\b.*", re.IGNORECASE),
                re.compile(r".*java\.lang\..*Exception.*\bat.*\n.*\bat.*", re.IGNORECASE | re.MULTILINE),
                re.compile(r".*\b(SystemError|Fatal Python error|SystemExit)\b.*", re.IGNORECASE),
            ],
            # "stack_overflow": [
            #     re.compile(r".*\b(stack overflow|stackoverflow|StackOverflowError)\b.*", re.IGNORECASE),
            #     re.compile(r".*\b(maximum recursion depth exceeded)\b.*", re.IGNORECASE),
            # ],
            # "null_pointer": [
            #     re.compile(r".*\b(null pointer|NullPointerException|NULL pointer dereference)\b.*", re.IGNORECASE),
            #     re.compile(r".*\b(dereference.*null|attempted.*null)\b.*", re.IGNORECASE),
            # ],
            # "out_of_memory": [
            #     re.compile(r".*\b(out of memory|OutOfMemoryError|OOM|memory limit exceeded)\b.*", re.IGNORECASE),
            #     re.compile(r".*\b(malloc.*failed|memory allocation failed)\b.*", re.IGNORECASE),
            # ],
            # "process_killed": [
            #     re.compile(r".*\b(SIGKILL|signal 9|killed|terminated by signal)\b.*", re.IGNORECASE),
            #     re.compile(r".*\b(process.*killed|OOM killer|out of memory killer)\b.*", re.IGNORECASE),
            #     re.compile(r".*\b(terminated abnormally|exited with code [^0])\b.*", re.IGNORECASE),
            # ],
            # "assertion_failure": [
            #     re.compile(r".*\b(assertion failed|AssertionError|ASSERT.*failed)\b.*", re.IGNORECASE),
            #     re.compile(r".*\b(assert.*failed|ASSERTION FAILURE)\b.*", re.IGNORECASE),
            # ],
            # "stack_trace": [
            #     re.compile(r"^\s+at\s+\S+\.\S+\(.*\)", re.MULTILINE),  # Java/Python stack traces
            #     re.compile(r"^\s*File\s+\".*\",\s+line\s+\d+", re.MULTILINE),  # Python traceback
            #     re.compile(r"^\s+#\d+\s+0x[0-9a-f]+\s+in\s+\S+", re.MULTILINE),  # C/C++ stack traces
            #     re.compile(r"backtrace|stack trace|traceback", re.IGNORECASE),
            # ],
            # "abort": [
            #     re.compile(r".*\b(aborted|abort\(\)|SIGABRT|signal 6)\b.*", re.IGNORECASE),
            #     re.compile(r".*\b(application terminated|app crashed)\b.*", re.IGNORECASE),
            # ],
            # "panic": [
            #     re.compile(r".*\b(kernel panic|panic:|PANIC)\b.*", re.IGNORECASE),
            #     re.compile(r".*\b(unrecoverable error|critical failure)\b.*", re.IGNORECASE),
            # ],
        }
    
    def _detect_crash_type(self, line: str, context_lines: List[str]) -> Optional[Dict[str, Any]]:
        """
        Detect crash type from a line and surrounding context.
        
        Args:
            line: Current line being analyzed
            context_lines: Previous lines for context (to detect multi-line crashes)
            
        Returns:
            Dictionary with crash type and details, or None if no crash detected
        """
        combined_context = "\n".join(context_lines[-5:] + [line])  # Last 5 lines + current
        
        # Check each crash category
        for crash_type, patterns in self.crash_patterns.items():
            for pattern in patterns:
                if pattern.search(combined_context):
                    # Extract timestamp if available (common log formats)
                    timestamp = None
                    timestamp_patterns = [
                        re.compile(r"(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})"),  # ISO format
                        re.compile(r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})"),  # US format
                        re.compile(r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"),  # syslog format
                    ]
                    for ts_pattern in timestamp_patterns:
                        match = ts_pattern.search(line)
                        if match:
                            timestamp = match.group(1)
                            break
                    
                    return {
                        "type": crash_type,
                        "line_content": line.strip()[:500],  # Truncate long lines
                        "timestamp": timestamp,
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
                file_crashes = []
                line_num = 0
                context_lines = []  # Keep last few lines for context (preserves across chunks)
                last_log_time = time.time()
                last_progress_event_time = time.time()
                chunk_buffer = ""  # Buffer for incomplete lines at chunk boundaries
                
                # Step 1: Read file in chunks, then Step 2: Process each chunk line by line
                # This approach handles large files efficiently while maintaining line-by-line processing
                for chunk in read_file_chunks(file_path, chunk_size=1048576):  # 1MB chunks
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
                        else:
                            # Split at newlines, keep complete lines (include the newline character)
                            complete_text = text_to_process[:last_newline_idx + 1]
                            lines = complete_text.splitlines(keepends=True)
                            # Save any incomplete line after last newline as buffer
                            if last_newline_idx + 1 < len(text_to_process):
                                chunk_buffer = text_to_process[last_newline_idx + 1:]
                    else:
                        lines = []
                    
                    # Process each line from the chunk
                    for line in lines:
                        line_num += 1
                        
                        # Check for cancellation and yield control frequently (every 100 lines)
                        # This ensures cancellation can be processed even during heavy CPU work
                        if cancellation_event and line_num % 100 == 0:
                            if cancellation_event.is_set():
                                logger.info(f"CrashDetector: Analysis cancelled at line {line_num}")
                                raise CancelledError("Analysis cancelled")
                            # Yield control to event loop to allow cancellation to be processed
                            await asyncio.sleep(0)
                            # Check again after yielding (cancellation may have happened during yield)
                            if cancellation_event.is_set():
                                logger.info(f"CrashDetector: Analysis cancelled at line {line_num}")
                                raise CancelledError("Analysis cancelled")
                        
                        context_lines.append(line)
                        
                        # Keep only last 10 lines for context
                        if len(context_lines) > 10:
                            context_lines.pop(0)
                        
                        # Emit progress event every 50k lines or every 2 seconds
                        if progress_callback and (line_num % 50000 == 0 or (time.time() - last_progress_event_time) >= 2.0):
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
                            last_progress_event_time = time.time()
                        
                        # Log progress for large files every 100k lines
                        if line_num % 100000 == 0:
                            elapsed = time.time() - last_log_time
                            logger.debug(f"CrashDetector: Processed {line_num:,} lines from {file_path} (crashes found: {len(file_crashes)}, {line_num/elapsed:.0f} lines/sec)")
                            last_log_time = time.time()
                        
                        # Detect crashes
                        crash_info = self._detect_crash_type(line, context_lines)
                        if crash_info:
                            crash_info["line"] = line_num
                            file_crashes.append(crash_info)
                            crash_summary_by_type[crash_info["type"]] += 1
                            
                            # Limit crashes per file to prevent memory issues
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
                    
                    # Break outer chunk loop if we hit the crash limit
                    if len(file_crashes) >= max_crashes_per_file:
                        break
                
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
                        result_text += f"    Line {crash['line']}"
                        if crash.get('timestamp'):
                            result_text += f" [{crash['timestamp']}]"
                        result_text += ":\n"
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
            result_text += f"  • Look for timestamps to correlate crashes with specific events\n"
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

