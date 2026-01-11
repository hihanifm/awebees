"""
Ripgrep utility for fast pattern matching in log files.
Provides a Python interface to ripgrep (rg) command.
"""

import subprocess
import logging
import shutil
import shlex
from typing import Optional, Iterator, List
from pathlib import Path

logger = logging.getLogger(__name__)

def is_ripgrep_available() -> bool:
    return shutil.which("rg") is not None

def build_ripgrep_command(
    ripgrep_command: str,
    file_path: str
) -> str:
    """
    Build ripgrep command string from raw ripgrep command.
    
    Args:
        ripgrep_command: Raw ripgrep command (everything after 'rg')
        file_path: File path to search
        
    Returns:
        Command string for display
    """
    return f"rg {ripgrep_command} {file_path} --no-heading --no-line-number --text"

def ripgrep_search(
    file_path: str,
    ripgrep_command: str
) -> Iterator[str]:
    """
    Execute ripgrep with raw command string.
    
    Args:
        file_path: File path to search
        ripgrep_command: Raw ripgrep command (everything after 'rg', e.g., "-A 10 'ERROR'")
        
    Yields:
        Matching lines
    """
    if not is_ripgrep_available():
        raise FileNotFoundError("ripgrep (rg) is not installed")
    
    # Parse the ripgrep command string
    # If it's a simple pattern (doesn't start with -), pass it directly
    # If it contains flags (starts with -), use shlex.split to parse
    ripgrep_command_stripped = ripgrep_command.strip()
    if ripgrep_command_stripped.startswith('-'):
        # Contains flags, need to parse
        try:
            cmd_parts = shlex.split(ripgrep_command)
        except ValueError:
            # If parsing fails, treat as single argument
            cmd_parts = [ripgrep_command]
    else:
        # Simple pattern - pass directly without parsing (preserves backslashes)
        cmd_parts = [ripgrep_command]
    
    # Build ripgrep command: rg [user_flags] file_path [standard_flags]
    cmd = ["rg"]
    cmd.extend(cmd_parts)
    cmd.append(file_path)
    cmd.extend(["--no-heading", "--no-line-number", "--text"])
    
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
        for line in process.stdout:
            # Decode with error handling for non-UTF-8 bytes (common in binary files)
            decoded_line = line.decode('utf-8', errors='replace').rstrip('\n')
            yield decoded_line
        
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

