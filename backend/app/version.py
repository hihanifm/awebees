"""Version information for Awebees backend."""

import os
from pathlib import Path


def get_version() -> str:
    """Get the application version from VERSION file."""
    # Get the project root (two levels up from this file: backend/app/ -> backend/ -> root/)
    project_root = Path(__file__).parent.parent.parent
    version_file = project_root / "VERSION"
    
    if version_file.exists():
        with open(version_file, "r", encoding="utf-8") as f:
            version = f.read().strip()
            return version
    
    # Fallback if VERSION file doesn't exist
    return "0.0.0-dev"


__version__ = get_version()

