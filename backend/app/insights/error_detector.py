"""Insight to detect errors in log files - Config-based implementation."""

import logging

logger = logging.getLogger(__name__)


# Insight configuration
INSIGHT_CONFIG = {
    "metadata": {
        "id": "error_detector",
        "name": "Error Detector",
        "description": "Detects ERROR and FATAL log lines in log files"
    },
    "filters": {
        "line_pattern": r"\b(ERROR|FATAL)\b"
    }
}


def process_results(filter_result):
    """
    Process filtered error lines and format as error summary.
    
    Args:
        filter_result: FilterResult containing filtered error lines
        
    Returns:
        dict with 'content' (formatted text) and 'metadata' (summary stats)
    """
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
    result_text += f"Total errors found: {total_errors:,}\n"
    result_text += f"Files with errors: {len([e for e in all_errors if 'count' in e])}\n\n"
    
    if all_errors:
        for file_result in all_errors:
            result_text += f"File: {file_result['file']}\n"
            result_text += f"  Errors found: {file_result['count']:,}\n"
            for err_line in file_result['errors'][:10]:  # Show first 10 errors per file
                content = err_line.strip()[:200]  # Truncate long lines
                result_text += f"    {content}\n"
            if file_result['count'] > 10:
                result_text += f"    ... and {file_result['count'] - 10:,} more errors\n"
            result_text += "\n"
    
    return {
        "content": result_text,
        "metadata": {
            "total_errors": total_errors,
            "files_analyzed": len(lines_by_file)
        }
    }


if __name__ == "__main__":
    """Standalone execution support for config-based insight."""
    from app.utils.config_insight_runner import main_config_standalone
    main_config_standalone(__file__)
