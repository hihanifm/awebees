"""
Ripgrep utility for fast pattern matching in log files.
Provides a Python interface to ripgrep (rg) command.
"""

import subprocess
import logging
import shutil
from typing import Optional, Iterator
from pathlib import Path

logger = logging.getLogger(__name__)

def is_ripgrep_available() -> bool:
    """Check if ripgrep is installed and available."""
    return shutil.which("rg") is not None

def ripgrep_search(
    file_path: str,
    pattern: str,
    case_insensitive: bool = True,  # Always True by default
    max_count: Optional[int] = None,
    context_before: int = 0,
    context_after: int = 0
) -> Iterator[str]:
    """
    Search for pattern in file using ripgrep.
    
    Note: Case-insensitive search is always enabled for log file analysis.
    
    Args:
        file_path: Path to the file to search
        pattern: Regex pattern to search for
        case_insensitive: Ignored (always case-insensitive)
        max_count: Maximum number of matches (None for unlimited)
        context_before: Number of lines to show before match
        context_after: Number of lines to show after match
        
    Yields:
        Lines matching the pattern
        
    Raises:
        FileNotFoundError: If ripgrep is not installed
        subprocess.CalledProcessError: If ripgrep fails
    """
    if not is_ripgrep_available():
        raise FileNotFoundError("ripgrep (rg) is not installed")
    
    # Build ripgrep command
    # Always use --ignore-case for log file analysis (ERROR, Error, error should all match)
    cmd = ["rg", pattern, file_path, "--no-heading", "--no-line-number", "--text", "--ignore-case"]
    
    if max_count:
        cmd.extend(["--max-count", str(max_count)])
    
    if context_before > 0:
        cmd.extend(["--before-context", str(context_before)])
    
    if context_after > 0:
        cmd.extend(["--after-context", str(context_after)])
    
    logger.info(f"Running ripgrep: {' '.join(cmd)}")
    
    try:
        # Run ripgrep and stream output
        # Use binary mode and decode manually to handle non-UTF-8 characters
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=-1  # Use system default buffering (line buffering only works in text mode)
        )
        
        for line in process.stdout:
            # Decode with error handling for non-UTF-8 bytes (common in binary files)
            decoded_line = line.decode('utf-8', errors='replace').rstrip('\n')
            yield decoded_line
        
        process.wait()
        
        if process.returncode not in [0, 1]:  # 0 = matches found, 1 = no matches
            stderr = process.stderr.read().decode('utf-8', errors='replace')
            logger.error(f"Ripgrep failed: {stderr}")
            raise subprocess.CalledProcessError(process.returncode, cmd, stderr=stderr)
            
    except Exception as e:
        logger.error(f"Ripgrep error: {e}")
        raise

