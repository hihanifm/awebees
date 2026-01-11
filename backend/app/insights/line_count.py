from typing import List, Optional, Callable, Awaitable
import logging
import asyncio
import os
from app.core.insight_base import Insight
from app.core.models import InsightResult, ProgressEvent
from app.services.file_handler import read_file_lines, CancelledError

logger = logging.getLogger(__name__)


class LineCount(Insight):
    @property
    def name(self) -> str: return "Line Count"
    
    @property
    def description(self) -> str: return "Counts total lines, empty lines, and non-empty lines in log files"
    
    async def analyze(
        self,
        user_path: str,
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> InsightResult:
        import time
        start_time = time.time()
        
        file_paths = self._get_path_files(user_path)
        if not file_paths:
            logger.warning(f"LineCount: No files found for path: {user_path}")
            return InsightResult(
                result_type="text",
                content=f"No files found for path: {user_path}",
                metadata={"user_path": user_path}
            )
        
        logger.info(f"LineCount: Starting analysis of path '{user_path}' with {len(file_paths)} file(s)")
        
        file_results = []
        total_lines = 0
        total_empty = 0
        total_non_empty = 0
        
        for file_idx, file_path in enumerate(file_paths, 1):
            if cancellation_event and cancellation_event.is_set():
                logger.info(f"LineCount: Analysis cancelled")
                raise CancelledError("Analysis cancelled")
            
            file_start_time = time.time()
            logger.info(f"LineCount: Processing file {file_idx}/{len(file_paths)}: {file_path}")
            
            file_size_mb = 0.0
            try:
                file_size_bytes = os.path.getsize(file_path)
                file_size_mb = file_size_bytes / (1024 * 1024)
            except Exception:
                pass
            
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
                
                for line in read_file_lines(file_path, cancellation_event=cancellation_event):
                    line_count += 1
                    if not line.strip():
                        empty_count += 1
                    else:
                        non_empty_count += 1
                    
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
        logger.info(f"LineCount: Analysis complete for path '{user_path}' - {total_lines:,} total lines across {len(file_paths)} file(s) in {total_elapsed:.2f}s")
        
        result_text = f"Line Count Summary\n"
        result_text += f"{'=' * 50}\n\n"
        result_text += f"Path: {user_path}\n"
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
                "user_path": user_path,
                "total_lines": total_lines,
                "total_empty": total_empty,
                "total_non_empty": total_non_empty,
                "files_analyzed": len(file_paths)
            }
        )
