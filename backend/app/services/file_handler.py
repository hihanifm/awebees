"""Service for handling file operations."""

import os
from pathlib import Path
from typing import List
import logging
import re

logger = logging.getLogger(__name__)


async def read_file(file_path: str) -> str:
    """
    Read file content asynchronously.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File content as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file is not readable
    """
    if not validate_file_path(file_path):
        raise ValueError(f"Invalid or inaccessible file path: {file_path}")
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


async def list_files_in_folder(folder_path: str, recursive: bool = True) -> List[str]:
    """
    List all files in a folder.
    
    Args:
        folder_path: Path to the folder
        recursive: If True, list files recursively
        
    Returns:
        List of file paths
        
    Raises:
        NotADirectoryError: If path is not a directory
        PermissionError: If directory is not accessible
    """
    if not validate_file_path(folder_path):
        raise ValueError(f"Invalid or inaccessible folder path: {folder_path}")
    
    folder = Path(folder_path)
    if not folder.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {folder_path}")
    
    files = []
    try:
        if recursive:
            files = [str(p) for p in folder.rglob("*") if p.is_file()]
        else:
            files = [str(p) for p in folder.iterdir() if p.is_file()]
    except Exception as e:
        logger.error(f"Error listing files in {folder_path}: {e}")
        raise
    
    return sorted(files)


def is_logcat_file(file_path: str) -> bool:
    """
    Detect if a file is in Android logcat format.
    
    Logcat format typically includes:
    - Timestamps (e.g., "01-01 12:00:00.000")
    - Log levels (V/D/I/W/E/F)
    - Process IDs and thread IDs
    - Tags and messages
    
    Example line: "01-01 12:00:00.000  1234  1234 I Tag: message"
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file appears to be logcat format
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            # Read first few lines to check format
            lines = [f.readline() for _ in range(10)]
            
            logcat_pattern = re.compile(
                r"^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+[VDIWEF]"
            )
            
            matching_lines = sum(1 for line in lines if logcat_pattern.match(line.strip()))
            # If at least 3 out of 10 lines match, consider it logcat format
            return matching_lines >= 3
    except Exception:
        return False


def validate_file_path(file_path: str) -> bool:
    """
    Validate that a file path exists and is accessible.
    
    Security: This checks that the path exists and is readable,
    but doesn't prevent directory traversal. Additional security
    measures should be implemented at the API level if needed.
    
    Args:
        file_path: Path to validate
        
    Returns:
        True if path is valid and accessible
    """
    try:
        path = Path(file_path).resolve()
        # Check if path exists
        if not path.exists():
            return False
        # Check if readable (file or directory)
        if path.is_file():
            return os.access(path, os.R_OK)
        elif path.is_dir():
            return os.access(path, os.R_OK)
        return False
    except Exception:
        return False

