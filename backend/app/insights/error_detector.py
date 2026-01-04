"""Insight to detect errors in log files."""

from typing import List
import re
from app.insights.base import Insight
from app.core.models import InsightResult
from app.services.file_handler import read_file


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
    
    async def analyze(self, file_paths: List[str]) -> InsightResult:
        """
        Analyze files for error and fatal log lines.
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            InsightResult with error summary
        """
        all_errors = []
        
        for file_path in file_paths:
            try:
                content = await read_file(file_path)
                lines = content.split("\n")
                
                # Look for ERROR/FATAL lines (case-insensitive)
                error_pattern = re.compile(r".*\b(ERROR|FATAL)\b.*", re.IGNORECASE)
                
                file_errors = []
                for line_num, line in enumerate(lines, start=1):
                    if error_pattern.search(line):
                        file_errors.append({
                            "line": line_num,
                            "content": line.strip()[:200]  # Truncate long lines
                        })
                
                if file_errors:
                    all_errors.append({
                        "file": file_path,
                        "count": len(file_errors),
                        "errors": file_errors[:50]  # Limit to first 50 errors per file
                    })
            except Exception as e:
                all_errors.append({
                    "file": file_path,
                    "error": f"Failed to read file: {str(e)}"
                })
        
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

