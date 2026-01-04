"""Insight to count lines in log files."""

from typing import List
from app.insights.base import Insight
from app.core.models import InsightResult
from app.services.file_handler import read_file


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
    
    async def analyze(self, file_paths: List[str]) -> InsightResult:
        """
        Analyze files and count lines.
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            InsightResult with line count summary
        """
        file_results = []
        total_lines = 0
        total_empty = 0
        total_non_empty = 0
        
        for file_path in file_paths:
            try:
                content = await read_file(file_path)
                lines = content.split("\n")
                
                line_count = len(lines)
                empty_count = sum(1 for line in lines if not line.strip())
                non_empty_count = line_count - empty_count
                
                file_results.append({
                    "file": file_path,
                    "total": line_count,
                    "empty": empty_count,
                    "non_empty": non_empty_count
                })
                
                total_lines += line_count
                total_empty += empty_count
                total_non_empty += non_empty_count
            except Exception as e:
                file_results.append({
                    "file": file_path,
                    "error": f"Failed to read file: {str(e)}"
                })
        
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

