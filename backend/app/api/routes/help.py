"""API routes for help documentation."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/help", tags=["help"])


@router.get("/", response_class=PlainTextResponse)
async def get_help():
    """
    Get the Quick Start guide markdown content from QUICK_START.md.
    
    Returns:
        The QUICK_START.md file content as plain text.
    """
    try:
        # Get the project root directory
        # From backend/app/api/routes/help.py -> backend/app/api/routes -> backend/app/api -> backend/app -> backend -> project_root
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent.parent
        quickstart_path = project_root / "QUICK_START.md"
        
        logger.info(f"Help API: Reading Quick Start guide from: {quickstart_path}")
        
        if not quickstart_path.exists():
            logger.error(f"Help API: Quick Start file not found at: {quickstart_path}")
            raise HTTPException(
                status_code=404,
                detail=f"Quick Start guide not found at {quickstart_path}"
            )
        
        # Read and return the markdown content
        content = quickstart_path.read_text(encoding="utf-8")
        logger.info(f"Help API: Successfully read Quick Start guide ({len(content)} characters)")
        
        return content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Help API: Error reading Quick Start guide: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read Quick Start guide: {str(e)}"
        )
