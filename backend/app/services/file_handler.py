"""Service for handling file operations."""

import os
import mmap
from pathlib import Path
from typing import List, Iterator, Optional
import logging
import re
import asyncio
from app.utils.profiling import profile

logger = logging.getLogger(__name__)


class CancelledError(Exception):
    """Raised when an operation is cancelled."""
    pass


async def read_file(file_path: str) -> str:
    """
    Read file content asynchronously.
    
    For large files (>10MB), this uses memory-mapped files for efficiency.
    For smaller files, reads normally for simplicity.

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
        file_size = os.path.getsize(file_path)
        # Use mmap for files larger than 10MB
        if file_size > 10 * 1024 * 1024:  # 10MB threshold
            return await _read_file_mmap(file_path)
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


async def _read_file_mmap(file_path: str) -> str:
    """
    Read large file using memory-mapped file for efficiency.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File content as string
    """
    try:
        with open(file_path, "rb") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                # Decode the memory-mapped bytes
                return mm.read().decode("utf-8", errors="ignore")
    except Exception as e:
        logger.error(f"Error reading file with mmap {file_path}: {e}")
        raise


@profile(log_interval=1, top_n=20)
def read_file_chunks(file_path: str, chunk_size: int = 1048576, cancellation_event: Optional[asyncio.Event] = None) -> Iterator[str]:
    """
    Read file in chunks for efficient memory usage.
    
    This is a generator that yields chunks of the file, useful for
    processing large files without loading everything into memory.
    
    Uses binary mode for accurate byte-level chunking, then decodes to text.
    This ensures true 1MB (or specified) byte chunks for better performance.
    
    Args:
        file_path: Path to the file
        chunk_size: Size of each chunk in bytes (default: 1MB)
        cancellation_event: Optional asyncio.Event to check for cancellation
        
    Yields:
        String chunks of the file (decoded from bytes)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file is not readable
        CancelledError: If operation is cancelled
    """
    if not validate_file_path(file_path):
        raise ValueError(f"Invalid or inaccessible file path: {file_path}")
    
    # Read in binary mode for accurate byte-level chunking, then decode
    # This is more efficient for large files than text mode
    with open(file_path, "rb") as f:
        while True:
            # Check for cancellation before reading next chunk
            if cancellation_event and cancellation_event.is_set():
                logger.info(f"FileHandler: Reading {file_path} cancelled")
                raise CancelledError(f"File reading cancelled: {file_path}")
            
            chunk_bytes = f.read(chunk_size)
            if not chunk_bytes:
                break
            
            # Check for cancellation after reading chunk (before yielding)
            if cancellation_event and cancellation_event.is_set():
                logger.info(f"FileHandler: Reading {file_path} cancelled")
                raise CancelledError(f"File reading cancelled: {file_path}")
            
            # Decode the bytes to string (handles UTF-8 with error recovery)
            chunk = chunk_bytes.decode("utf-8", errors="ignore")
            yield chunk


def read_file_lines(file_path: str, max_lines: int = None, cancellation_event: Optional[asyncio.Event] = None) -> Iterator[str]:
    """
    Read file line by line efficiently for large files.
    
    This is a generator that yields lines one at a time, preventing
    the entire file from being loaded into memory.
    
    Args:
        file_path: Path to the file
        max_lines: Maximum number of lines to read (None for all lines)
        cancellation_event: Optional asyncio.Event to check for cancellation
        
    Yields:
        Individual lines from the file
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file is not readable
        CancelledError: If operation is cancelled
    """
    import os
    if not validate_file_path(file_path):
        logger.error(f"FileHandler: Invalid or inaccessible file path: {file_path}")
        raise ValueError(f"Invalid or inaccessible file path: {file_path}")
    
    try:
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        logger.debug(f"FileHandler: Opening file for line-by-line reading: {file_path} ({file_size_mb:.2f} MB)")
        
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            count = 0
            for line in f:
                # Check for cancellation more frequently (every 1000 lines) for better responsiveness
                if cancellation_event and count % 1000 == 0 and cancellation_event.is_set():
                    logger.info(f"FileHandler: Reading {file_path} cancelled at line {count}")
                    raise CancelledError(f"File reading cancelled: {file_path}")
                
                yield line
                count += 1
                if max_lines and count >= max_lines:
                    logger.debug(f"FileHandler: Reached max_lines limit ({max_lines}) for {file_path}")
                    break
        
        logger.debug(f"FileHandler: Finished reading {count:,} lines from {file_path}")
    except CancelledError:
        raise
    except Exception as e:
        logger.error(f"FileHandler: Error reading file lines from {file_path}: {e}", exc_info=True)
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
        logger.error(f"FileHandler: Invalid or inaccessible folder path: {folder_path}")
        raise ValueError(f"Invalid or inaccessible folder path: {folder_path}")
    
    folder = Path(folder_path)
    if not folder.is_dir():
        logger.error(f"FileHandler: Path is not a directory: {folder_path}")
        raise NotADirectoryError(f"Path is not a directory: {folder_path}")
    
    logger.debug(f"FileHandler: Listing files in folder: {folder_path} (recursive={recursive})")
    files = []
    try:
        if recursive:
            files = [str(p) for p in folder.rglob("*") if p.is_file()]
        else:
            files = [str(p) for p in folder.iterdir() if p.is_file()]
        logger.debug(f"FileHandler: Found {len(files)} file(s) in {folder_path}")
    except Exception as e:
        logger.error(f"FileHandler: Error listing files in {folder_path}: {e}", exc_info=True)
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

