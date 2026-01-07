"""API routes for playground experimentation."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import time
import subprocess
from pathlib import Path

from app.utils.ripgrep import ripgrep_search, is_ripgrep_available
from app.services.file_handler import validate_file_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/playground", tags=["playground"])


class PlaygroundFilterRequest(BaseModel):
    """Request to filter a file with ripgrep."""
    file_path: str
    pattern: str
    custom_flags: Optional[str] = None  # Custom ripgrep flags
    case_insensitive: bool = True
    context_before: int = 0
    context_after: int = 0
    max_count: Optional[int] = 1000  # Limit results to prevent memory issues


class FilterResult(BaseModel):
    """Result of a playground filter operation."""
    lines: List[str]
    total_count: int
    truncated: bool
    execution_time: float
    ripgrep_command: str


@router.post("/filter", response_model=FilterResult)
async def filter_file(request: PlaygroundFilterRequest):
    """
    Execute ripgrep filter on a single file.
    
    This endpoint allows users to experiment with ripgrep patterns
    on their files in real-time.
    
    Args:
        request: Filter request with file path and pattern
        
    Returns:
        Filtered results with metadata
        
    Raises:
        HTTPException: If file is invalid or ripgrep fails
    """
    logger.info(f"Playground Filter: pattern='{request.pattern}', file='{request.file_path}'")
    
    # Validate file path
    if not validate_file_path(request.file_path):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid or inaccessible file path: {request.file_path}"
        )
    
    if not Path(request.file_path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {request.file_path}"
        )
    
    # Check if ripgrep is available
    if not is_ripgrep_available():
        raise HTTPException(
            status_code=503,
            detail="Ripgrep (rg) is not installed on the server"
        )
    
    # Build ripgrep command string for display
    cmd_parts = ["rg"]
    
    # Add custom flags first (if provided)
    if request.custom_flags and request.custom_flags.strip():
        # Split custom flags and add them
        custom_flags_list = request.custom_flags.strip().split()
        cmd_parts.extend(custom_flags_list)
    
    # Add pattern and file path
    cmd_parts.extend([request.pattern, request.file_path])
    
    # Add UI helper flags
    if request.case_insensitive:
        cmd_parts.append("--ignore-case")
    if request.context_before > 0:
        cmd_parts.extend(["--before-context", str(request.context_before)])
    if request.context_after > 0:
        cmd_parts.extend(["--after-context", str(request.context_after)])
    if request.max_count:
        cmd_parts.extend(["--max-count", str(request.max_count)])
    
    ripgrep_command = " ".join(cmd_parts)
    
    start_time = time.time()
    
    try:
        # Execute ripgrep
        lines = []
        try:
            for line in ripgrep_search(
                file_path=request.file_path,
                pattern=request.pattern,
                case_insensitive=request.case_insensitive,
                max_count=request.max_count,
                context_before=request.context_before,
                context_after=request.context_after
            ):
                lines.append(line)
        except subprocess.CalledProcessError as ripgrep_error:
            # Re-raise to be caught by outer handler
            raise ripgrep_error
        except Exception as ripgrep_error:
            # Wrap other exceptions
            logger.error(f"Playground Filter: Unexpected error in ripgrep_search: {ripgrep_error}", exc_info=True)
            raise
        
        execution_time = time.time() - start_time
        truncated = request.max_count is not None and len(lines) >= request.max_count
        
        logger.info(f"Playground Filter: Found {len(lines)} lines in {execution_time:.3f}s (truncated: {truncated})")
        
        return FilterResult(
            lines=lines,
            total_count=len(lines),
            truncated=truncated,
            execution_time=execution_time,
            ripgrep_command=ripgrep_command
        )
    
    except subprocess.CalledProcessError as e:
        error_msg = str(e)
        stderr = ""
        if hasattr(e, 'stderr') and e.stderr:
            stderr = e.stderr.decode('utf-8', errors='replace') if isinstance(e.stderr, bytes) else str(e.stderr)
        
        # Check if error is related to invalid regex (common with unescaped special chars)
        # Ripgrep error messages can vary, so check multiple patterns
        error_text = (stderr + " " + error_msg).lower()
        is_regex_error = (
            "regex parse error" in error_text or 
            "invalid pattern" in error_text or 
            "unclosed character class" in error_text or
            "error parsing regex" in error_text or
            "regex error" in error_text
        )
        
        if is_regex_error:
            # Extract problematic characters and suggest escaping
            import re
            special_chars = r'[](){}.*+?^$|\\'
            found_special = [char for char in request.pattern if char in special_chars]
            if found_special:
                escaped_pattern = re.escape(request.pattern)
                unique_special = sorted(set(found_special))
                suggestion = f"Invalid regex pattern. Special characters {', '.join(repr(c) for c in unique_special)} need to be escaped with backslash. Try: {escaped_pattern}"
                logger.error(f"Playground Filter: Regex error - {suggestion}")
                raise HTTPException(
                    status_code=400,
                    detail=suggestion
                )
        
        logger.error(f"Playground Filter: Error executing ripgrep: {error_msg}. stderr: {stderr}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error executing ripgrep: {stderr if stderr else error_msg}"
        )
    except Exception as e:
        logger.error(f"Playground Filter: Error executing ripgrep: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error executing ripgrep: {str(e)}"
        )

