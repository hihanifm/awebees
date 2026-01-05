"""Insight to detect errors in log files."""

from typing import List, Optional, Callable, Awaitable
import logging
from app.insights.filter_base import FilterBasedInsight, FilterResult, ReadingMode
from app.core.models import InsightResult

logger = logging.getLogger(__name__)


class ErrorDetector(FilterBasedInsight):
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
    
    @property
    def file_filter_patterns(self) -> Optional[List[str]]:
        """No file filtering - process all files."""
        return None
    
    @property
    def line_filter_pattern(self) -> str:
        """Regex pattern for ERROR and FATAL log lines."""
        return r".*\b(ERROR|FATAL)\b.*"
    
    @property
    def regex_flags(self) -> int:
        """Regex flags - use IGNORECASE for case-insensitive matching."""
        import re
        return re.IGNORECASE
    
    @property
    def reading_mode(self) -> ReadingMode:
        """Use line-by-line reading mode."""
        return ReadingMode.LINES
    
    async def _process_filtered_lines(
        self,
        filter_result: FilterResult
    ) -> InsightResult:
        """
        Process filtered lines and format as error summary.
        
        Args:
            filter_result: FilterResult containing filtered error lines
            
        Returns:
            InsightResult with error summary
        """
        import re
        
        logger.debug(f"ErrorDetector: Processing filtered lines from {filter_result.get_file_count()} file(s)")
        all_errors = []
        lines_by_file = filter_result.get_lines_by_file()
        max_errors_per_file = 1000  # Limit to prevent overwhelming output
        
        for file_path, lines in lines_by_file.items():
            logger.debug(f"ErrorDetector: Processing {len(lines)} error lines from {file_path}")
            # Limit errors per file
            file_errors = lines[:max_errors_per_file]
            
            if file_errors:
                logger.info(f"ErrorDetector: Found {len(lines)} error(s) in {file_path}")
                all_errors.append({
                    "file": file_path,
                    "count": len(lines),  # Total count (may be more than what we show)
                    "errors": file_errors[:50]  # Limit to first 50 errors per file for output
                })
            else:
                logger.debug(f"ErrorDetector: No errors in {file_path}")
        
        total_errors = sum(err.get("count", 0) for err in all_errors if "count" in err)
        logger.info(f"ErrorDetector: Total errors found: {total_errors} across {len(all_errors)} file(s)")
        
        # Format results
        result_text = f"Error Detection Summary\n"
        result_text += f"{'=' * 50}\n\n"
        result_text += f"Total errors found: {total_errors}\n"
        result_text += f"Files with errors: {len([e for e in all_errors if 'count' in e])}\n\n"
        
        for file_result in all_errors:
            result_text += f"File: {file_result['file']}\n"
            result_text += f"  Errors found: {file_result['count']}\n"
            for err_line in file_result['errors'][:10]:  # Show first 10 errors per file
                content = err_line.strip()[:200]  # Truncate long lines
                result_text += f"    {content}\n"
            if file_result['count'] > 10:
                result_text += f"    ... and {file_result['count'] - 10} more errors\n"
            result_text += "\n"
        
        return InsightResult(
            result_type="text",
            content=result_text,
            metadata={"total_errors": total_errors, "files_analyzed": len(lines_by_file)}
        )


if __name__ == "__main__":
    import sys
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
