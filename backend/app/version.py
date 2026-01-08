"""Version information for Lens backend."""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_version() -> str:
    """Get the application version from VERSION file."""
    # Try multiple possible locations for the VERSION file
    # This handles both development and packaged (Windows) environments
    
    # Calculate paths relative to this file's location
    file_dir = Path(__file__).resolve().parent  # backend/app/
    backend_dir = file_dir.parent  # backend/
    package_root_from_file = backend_dir.parent  # package root (lens-app-*)
    
    # Get current working directory
    # In Windows package, launcher changes to backend/ directory, so cwd.parent = package root
    cwd = Path.cwd().resolve()
    
    # Remove duplicates while preserving order
    possible_paths = []
    seen = set()
    
    # Priority order matters - check most likely locations first
    candidates = [
        # 1. Parent of current working directory (Windows package: backend/ -> package_root/VERSION)
        cwd.parent / "VERSION",
        # 2. Package root calculated from __file__ location
        package_root_from_file / "VERSION",
        # 3. Current working directory (if VERSION is there)
        cwd / "VERSION",
        # 4. Backend directory (unlikely but possible)
        backend_dir / "VERSION",
    ]
    
    for path in candidates:
        path_str = str(path)
        if path_str not in seen:
            seen.add(path_str)
            possible_paths.append(path)
    
    # Try each path
    for version_file in possible_paths:
        if version_file.exists() and version_file.is_file():
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    version = f.read().strip()
                    if version:  # Make sure it's not empty
                        logger.debug(f"Found VERSION file at: {version_file} (version: {version})")
                        return version
            except Exception as e:
                logger.debug(f"Failed to read VERSION file at {version_file}: {e}")
                continue  # Try next path
    
    # Log all attempted paths for debugging (only if not found)
    logger.warning(f"VERSION file not found. Attempted paths:")
    for path in possible_paths:
        logger.warning(f"  - {path} (exists: {path.exists()})")
    logger.warning(f"Current working directory: {cwd}")
    logger.warning(f"__file__ location: {__file__}")
    logger.warning(f"Package root (from __file__): {package_root_from_file}")
    
    # Fallback if VERSION file doesn't exist
    return "0.0.0-dev"


__version__ = get_version()

