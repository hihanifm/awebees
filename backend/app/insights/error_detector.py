"""Insight to detect errors in log files."""

from typing import List, Optional
import re
import logging
import asyncio
from app.insights.base import Insight
from app.core.models import InsightResult
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
    
    async def analyze(self, file_paths: List[str], cancellation_event: Optional[asyncio.Event] = None) -> InsightResult:
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
            
            try:
                file_errors = []
                line_num = 0
                last_log_time = time.time()
                
                # Process file line by line to handle large files efficiently
                for line in read_file_lines(file_path, cancellation_event=cancellation_event):
                    line_num += 1
                    
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
