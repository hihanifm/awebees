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
    return shutil.which("rg") is not None

def build_ripgrep_command(
    pattern: str,
    file_path: str,
    case_insensitive: bool = True,
    max_count: Optional[int] = None,
    context_before: int = 0,
    context_after: int = 0
) -> str:
    cmd_parts = ["rg", pattern, file_path, "--no-heading", "--no-line-number", "--text"]
    
    if case_insensitive:
        cmd_parts.append("--ignore-case")
    
    if max_count:
        cmd_parts.extend(["--max-count", str(max_count)])
    
    if context_before > 0:
        cmd_parts.extend(["--before-context", str(context_before)])
    
    if context_after > 0:
        cmd_parts.extend(["--after-context", str(context_after)])
    
    return " ".join(cmd_parts)

def ripgrep_search(
    file_path: str,
    pattern: str,
    case_insensitive: bool = True,
    max_count: Optional[int] = None,
    context_before: int = 0,
    context_after: int = 0
) -> Iterator[str]:
    if not is_ripgrep_available():
        raise FileNotFoundError("ripgrep (rg) is not installed")
    
    # Build ripgrep command
    cmd = ["rg", pattern, file_path, "--no-heading", "--no-line-number", "--text"]
    
    # Add case-insensitive flag if requested
    if case_insensitive:
        cmd.append("--ignore-case")
    
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
        
        # Read stdout line by line
        lines_yielded = 0
        for line in process.stdout:
            # Decode with error handling for non-UTF-8 bytes (common in binary files)
            decoded_line = line.decode('utf-8', errors='replace').rstrip('\n')
            yield decoded_line
            lines_yielded += 1
        
        # Wait for process to complete
        process.wait()
        
        # Check return code and read stderr if there was an error
        if process.returncode not in [0, 1]:  # 0 = matches found, 1 = no matches
            stderr = process.stderr.read().decode('utf-8', errors='replace')
            logger.error(f"Ripgrep failed with return code {process.returncode}: {stderr}")
            raise subprocess.CalledProcessError(process.returncode, cmd, stderr=stderr)
            
    except subprocess.CalledProcessError:
        # Re-raise CalledProcessError as-is (it already has stderr)
        raise
    except Exception as e:
        logger.error(f"Ripgrep error: {e}")
        raise

