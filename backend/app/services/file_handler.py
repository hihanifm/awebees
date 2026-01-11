import os
import mmap
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Iterator, Optional, Tuple
import logging
import re
import asyncio

from app.core.config import ZipSecurityConfig

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
        if file_size > 10 * 1024 * 1024:
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
                return mm.read().decode("utf-8", errors="ignore")
    except Exception as e:
        logger.error(f"Error reading file with mmap {file_path}: {e}")
        raise


def read_file_chunks(file_path: str, chunk_size: int = 1048576, cancellation_event: Optional[asyncio.Event] = None) -> Iterator[str]:
    """
    Read file in chunks for efficient memory usage.
    
    Supports regular file paths and virtual zip file paths (zip_path::internal_path).
    For zip files, reads directly from the archive without extraction.
    
    This is a generator that yields chunks of the file, useful for
    processing large files without loading everything into memory.
    
    Uses binary mode for accurate byte-level chunking, then decodes to text.
    This ensures true 1MB (or specified) byte chunks for better performance.
    
    Args:
        file_path: Path to the file (regular path or virtual zip path)
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
    
    # Check if it's a virtual zip path
    zip_path_info = parse_zip_path(file_path)
    if zip_path_info:
        zip_path, internal_path = zip_path_info
        logger.debug(f"FileHandler: Reading chunks from zip file: {zip_path}::{internal_path}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Sanitize and find file
                sanitized_path = sanitize_zip_path(internal_path)
                try:
                    zip_info = zip_ref.getinfo(sanitized_path)
                except KeyError:
                    # Try case-insensitive search
                    found = False
                    for name in zip_ref.namelist():
                        if sanitize_zip_path(name).lower() == sanitized_path.lower():
                            sanitized_path = name
                            zip_info = zip_ref.getinfo(name)
                            found = True
                            break
                    if not found:
                        raise FileNotFoundError(f"File {internal_path} not found in {zip_path}")
                
                # Validate security
                is_valid, error_msg = validate_zip_file_security(zip_path, zip_info, 0, 0, 0)
                if not is_valid:
                    raise ValueError(f"Security validation failed: {error_msg}")
                
                # Read in chunks
                with zip_ref.open(sanitized_path, 'r') as file_in_zip:
                    while True:
                        if cancellation_event and cancellation_event.is_set():
                            logger.info(f"FileHandler: Reading {file_path} cancelled")
                            raise CancelledError(f"File reading cancelled: {file_path}")
                        
                        chunk_bytes = file_in_zip.read(chunk_size)
                        if not chunk_bytes:
                            break
                        
                        if cancellation_event and cancellation_event.is_set():
                            logger.info(f"FileHandler: Reading {file_path} cancelled")
                            raise CancelledError(f"File reading cancelled: {file_path}")
                        
                        chunk = chunk_bytes.decode("utf-8", errors="ignore")
                        yield chunk
        except CancelledError:
            raise
        except Exception as e:
            logger.error(f"FileHandler: Error reading chunks from zip {file_path}: {e}", exc_info=True)
            raise
        return
    
    # Regular file reading
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
    
    Supports regular file paths and virtual zip file paths (zip_path::internal_path).
    For zip files, reads directly from the archive without extraction.
    
    This is a generator that yields lines one at a time, preventing
    the entire file from being loaded into memory.
    
    Args:
        file_path: Path to the file (regular path or virtual zip path)
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
        # Check if it's a virtual zip path
        zip_path_info = parse_zip_path(file_path)
        if zip_path_info:
            zip_path, internal_path = zip_path_info
            logger.debug(f"FileHandler: Reading from zip file: {zip_path}::{internal_path}")
            
            count = 0
            for line in read_file_from_zip(zip_path, internal_path, cancellation_event):
                yield line
                count += 1
                if max_lines and count >= max_lines:
                    logger.debug(f"FileHandler: Reached max_lines limit ({max_lines}) for {file_path}")
                    break
            
            logger.debug(f"FileHandler: Finished reading {count:,} lines from zip {file_path}")
            return
        
        # Regular file reading
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
    
    If the folder contains zip files, also lists files inside those zip files
    as virtual paths (zip_path::internal_path).
    
    Args:
        folder_path: Path to the folder
        recursive: If True, list files recursively (and recursively list zip contents)
        
    Returns:
        List of file paths (regular paths and virtual zip paths)
        
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
    zip_files = []
    
    try:
        if recursive:
            all_paths = list(folder.rglob("*"))
        else:
            all_paths = list(folder.iterdir())
        
        for p in all_paths:
            if p.is_file():
                file_path_str = str(p)
                # Check if it's a zip file
                if is_zip_file(file_path_str):
                    zip_files.append(file_path_str)
                else:
                    files.append(file_path_str)
        
        # List contents of zip files
        for zip_file in zip_files:
            try:
                zip_contents = list_zip_contents(zip_file, recursive=recursive)
                files.extend(zip_contents)
                logger.debug(f"FileHandler: Found {len(zip_contents)} file(s) inside zip {zip_file}")
            except Exception as e:
                logger.warning(f"FileHandler: Error listing zip contents {zip_file}: {e}")
                # Continue with other files
        
        logger.debug(f"FileHandler: Found {len(files)} file(s) in {folder_path} (including {len(zip_files)} zip file(s))")
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


# Virtual path separator for files inside zip archives
ZIP_VIRTUAL_PATH_SEPARATOR = "::"


def is_zip_file(file_path: str) -> bool:
    """
    Check if a file is a zip archive.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file is a zip archive
    """
    try:
        path = Path(file_path)
        if not path.is_file():
            return False
        # Check extension
        if path.suffix.lower() == '.zip':
            # Also verify it's actually a zip file by trying to open it
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Just check if we can read the zip file list
                    zip_ref.testzip()
                    return True
            except (zipfile.BadZipFile, IOError, OSError):
                return False
        return False
    except Exception:
        return False


def parse_zip_path(virtual_path: str) -> Optional[Tuple[str, str]]:
    """
    Parse a virtual zip file path into zip path and internal path.
    
    Format: zip_path::internal/path/to/file.txt
    
    Args:
        virtual_path: Virtual path with :: separator
        
    Returns:
        Tuple of (zip_path, internal_path) if valid, None otherwise
    """
    if ZIP_VIRTUAL_PATH_SEPARATOR not in virtual_path:
        return None
    
    parts = virtual_path.split(ZIP_VIRTUAL_PATH_SEPARATOR, 1)
    if len(parts) != 2:
        return None
    
    zip_path, internal_path = parts
    if not zip_path or not internal_path:
        return None
    
    return (zip_path, internal_path)


def sanitize_zip_path(internal_path: str) -> str:
    """
    Sanitize an internal zip file path to prevent path traversal attacks.
    
    Removes:
    - Leading slashes
    - Path traversal sequences (..)
    - Normalizes path separators
    
    Args:
        internal_path: Internal path inside zip file
        
    Returns:
        Sanitized path
    """
    # Remove leading slashes
    path = internal_path.lstrip('/').lstrip('\\')
    
    # Normalize path separators (convert backslashes to forward slashes)
    path = path.replace('\\', '/')
    
    # Remove path traversal sequences and normalize dots
    if '..' in path or '/./' in path or path.startswith('./') or path.endswith('/.'):
        # Split and filter out '..' and '.' components
        parts = []
        for part in path.split('/'):
            if part == '..':
                # Go up one level (remove last component if exists)
                if parts:
                    parts.pop()
            elif part and part != '.':
                parts.append(part)
        path = '/'.join(parts)
    
    return path


def validate_zip_file_security(
    zip_path: str,
    zip_info: zipfile.ZipInfo,
    recursion_depth: int,
    total_size: int,
    file_count: int
) -> Tuple[bool, Optional[str]]:
    """
    Validate security constraints for a zip file operation.
    
    Args:
        zip_path: Path to the zip file
        zip_info: ZipInfo object for the file being checked
        recursion_depth: Current recursion depth for nested zips
        total_size: Total uncompressed size accumulated so far
        file_count: Total number of files processed so far
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check recursion depth
    if recursion_depth >= ZipSecurityConfig.MAX_RECURSION_DEPTH:
        return (False, f"Maximum recursion depth ({ZipSecurityConfig.MAX_RECURSION_DEPTH}) exceeded")
    
    # Check file count
    if file_count >= ZipSecurityConfig.MAX_FILES:
        return (False, f"Maximum number of files ({ZipSecurityConfig.MAX_FILES}) exceeded")
    
    # Check individual file size
    uncompressed_size = zip_info.file_size
    if uncompressed_size > ZipSecurityConfig.MAX_FILE_SIZE:
        size_mb = uncompressed_size / (1024 * 1024)
        max_mb = ZipSecurityConfig.MAX_FILE_SIZE / (1024 * 1024)
        return (False, f"File size ({size_mb:.1f} MB) exceeds maximum ({max_mb:.0f} MB)")
    
    # Check total size
    new_total_size = total_size + uncompressed_size
    if new_total_size > ZipSecurityConfig.MAX_TOTAL_SIZE:
        total_gb = new_total_size / (1024 * 1024 * 1024)
        max_gb = ZipSecurityConfig.MAX_TOTAL_SIZE / (1024 * 1024 * 1024)
        return (False, f"Total uncompressed size ({total_gb:.2f} GB) exceeds maximum ({max_gb:.0f} GB)")
    
    # Check compression ratio (zip bomb detection)
    compressed_size = zip_info.compress_size
    if compressed_size > 0:
        compression_ratio = uncompressed_size / compressed_size
        if compression_ratio > ZipSecurityConfig.MAX_COMPRESSION_RATIO:
            return (False, f"Compression ratio ({compression_ratio:.0f}:1) exceeds maximum ({ZipSecurityConfig.MAX_COMPRESSION_RATIO}:1) - possible zip bomb")
    
    return (True, None)


def list_zip_contents(zip_path: str, recursive: bool = True, recursion_depth: int = 0) -> List[str]:
    """
    List all file paths inside a zip archive.
    
    Returns virtual paths in format: zip_path::internal/path/to/file.txt
    Handles nested zips if recursive=True (up to MAX_RECURSION_DEPTH).
    
    Args:
        zip_path: Path to the zip file
        recursive: If True, recursively list contents of nested zip files
        recursion_depth: Current recursion depth (for nested zips)
        
    Returns:
        List of virtual paths (zip_path::internal_path)
    """
    virtual_paths = []
    total_size = 0
    file_count = 0
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for zip_info in zip_ref.infolist():
                # Skip directories
                if zip_info.is_dir():
                    continue
                
                internal_path = sanitize_zip_path(zip_info.filename)
                
                # Skip __MACOSX and other system files
                if internal_path.startswith('__MACOSX') or internal_path.startswith('.DS_Store'):
                    continue
                
                # Validate security constraints
                is_valid, error_msg = validate_zip_file_security(
                    zip_path, zip_info, recursion_depth, total_size, file_count
                )
                
                if not is_valid:
                    logger.warning(f"FileHandler: Skipping {internal_path} in {zip_path}: {error_msg}")
                    continue
                
                # Check if it's a nested zip file
                if recursive and internal_path.lower().endswith('.zip') and recursion_depth < ZipSecurityConfig.MAX_RECURSION_DEPTH:
                    # For nested zips, we need to extract temporarily to list contents
                    # But for now, we'll just include the nested zip as a virtual path
                    # The actual extraction/listing will happen when needed
                    virtual_path = f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}{internal_path}"
                    virtual_paths.append(virtual_path)
                else:
                    # Regular file
                    virtual_path = f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}{internal_path}"
                    virtual_paths.append(virtual_path)
                
                total_size += zip_info.file_size
                file_count += 1
                
                # Check if we've exceeded limits after adding this file
                if file_count >= ZipSecurityConfig.MAX_FILES:
                    logger.warning(f"FileHandler: Reached maximum file count ({ZipSecurityConfig.MAX_FILES}) in {zip_path}")
                    break
                
                if total_size >= ZipSecurityConfig.MAX_TOTAL_SIZE:
                    logger.warning(f"FileHandler: Reached maximum total size in {zip_path}")
                    break
                    
    except zipfile.BadZipFile as e:
        logger.error(f"FileHandler: Bad zip file {zip_path}: {e}")
    except Exception as e:
        logger.error(f"FileHandler: Error listing zip contents {zip_path}: {e}", exc_info=True)
    
    return virtual_paths


def read_file_from_zip(zip_path: str, internal_path: str, cancellation_event: Optional[asyncio.Event] = None) -> Iterator[str]:
    """
    Read a file from inside a zip archive line-by-line.
    
    Reads directly from zip without extraction (for Python reading modes).
    
    Args:
        zip_path: Path to the zip file
        internal_path: Path to file inside the zip (should be sanitized)
        cancellation_event: Optional asyncio.Event to check for cancellation
        
    Yields:
        Lines from the file
        
    Raises:
        FileNotFoundError: If file doesn't exist in zip
        CancelledError: If operation is cancelled
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Sanitize internal path
            sanitized_path = sanitize_zip_path(internal_path)
            
            # Try to find the file (case-insensitive if needed)
            try:
                zip_info = zip_ref.getinfo(sanitized_path)
            except KeyError:
                # Try case-insensitive search
                found = False
                for name in zip_ref.namelist():
                    if sanitize_zip_path(name).lower() == sanitized_path.lower():
                        sanitized_path = name
                        zip_info = zip_ref.getinfo(name)
                        found = True
                        break
                if not found:
                    raise FileNotFoundError(f"File {internal_path} not found in {zip_path}")
            
            # Validate security constraints
            is_valid, error_msg = validate_zip_file_security(zip_path, zip_info, 0, 0, 0)
            if not is_valid:
                raise ValueError(f"Security validation failed: {error_msg}")
            
            # Read file line by line
            with zip_ref.open(sanitized_path, 'r') as file_in_zip:
                count = 0
                for line_bytes in file_in_zip:
                    # Check for cancellation
                    if cancellation_event and cancellation_event.is_set():
                        logger.info(f"FileHandler: Reading from zip {zip_path}::{internal_path} cancelled at line {count}")
                        raise CancelledError(f"File reading cancelled: {zip_path}::{internal_path}")
                    
                    # Decode bytes to string
                    line = line_bytes.decode('utf-8', errors='ignore')
                    yield line
                    count += 1
                    
    except CancelledError:
        raise
    except Exception as e:
        logger.error(f"FileHandler: Error reading file from zip {zip_path}::{internal_path}: {e}", exc_info=True)
        raise


def extract_file_from_zip(zip_path: str, internal_path: str, extract_to: Path) -> Optional[Path]:
    """
    Extract a single file from zip to a directory.
    
    Extracts directly to file using streaming for efficient memory usage.
    
    Args:
        zip_path: Path to the zip file
        internal_path: Path to file inside the zip
        extract_to: Directory to extract the file to
        
    Returns:
        Path to extracted file, or None if extraction failed
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Sanitize internal path
            sanitized_path = sanitize_zip_path(internal_path)
            
            # Try to find the file
            try:
                zip_info = zip_ref.getinfo(sanitized_path)
            except KeyError:
                # Try case-insensitive search
                found = False
                for name in zip_ref.namelist():
                    if sanitize_zip_path(name).lower() == sanitized_path.lower():
                        sanitized_path = name
                        zip_info = zip_ref.getinfo(name)
                        found = True
                        break
                if not found:
                    logger.error(f"FileHandler: File {internal_path} not found in {zip_path}")
                    return None
            
            # Validate security constraints
            is_valid, error_msg = validate_zip_file_security(zip_path, zip_info, 0, 0, 0)
            if not is_valid:
                logger.error(f"FileHandler: Security validation failed for {internal_path} in {zip_path}: {error_msg}")
                return None
            
            # Create extract directory if it doesn't exist
            extract_to.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename to avoid conflicts
            # Use hash of full path or UUID
            import hashlib
            path_hash = hashlib.md5(f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}{sanitized_path}".encode()).hexdigest()[:8]
            file_stem = Path(sanitized_path).stem
            file_suffix = Path(sanitized_path).suffix
            extracted_filename = f"{file_stem}_{path_hash}{file_suffix}"
            extracted_path = extract_to / extracted_filename
            
            # Extract directly to file using streaming
            with zip_ref.open(sanitized_path, 'r') as file_in_zip:
                with open(extracted_path, 'wb') as out_file:
                    shutil.copyfileobj(file_in_zip, out_file)
            
            logger.debug(f"FileHandler: Extracted {internal_path} from {zip_path} to {extracted_path}")
            return extracted_path
            
    except Exception as e:
        logger.error(f"FileHandler: Error extracting file from zip {zip_path}::{internal_path}: {e}", exc_info=True)
        return None


def validate_file_path(file_path: str) -> bool:
    """
    Validate that a file path exists and is accessible.
    
    Supports regular file paths and virtual zip file paths (zip_path::internal_path).
    
    Security: This checks that the path exists and is readable,
    but doesn't prevent directory traversal. Additional security
    measures should be implemented at the API level if needed.
    
    Args:
        file_path: Path to validate (can be regular path or virtual zip path)
        
    Returns:
        True if path is valid and accessible
    """
    try:
        # Check if it's a virtual zip path
        zip_path_info = parse_zip_path(file_path)
        if zip_path_info:
            zip_path, internal_path = zip_path_info
            # Validate the zip file exists and is readable
            if not validate_file_path(zip_path):  # Recursive call for zip file
                return False
            # Validate it's actually a zip file
            if not is_zip_file(zip_path):
                return False
            # Internal path validation is handled during extraction/reading
            return True
        
        # Regular file path validation
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

