"""API routes for help documentation."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, FileResponse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/help", tags=["help"])


def get_project_root() -> Path:
    """Get the project root directory."""
    # From backend/app/api/routes/help.py -> backend/app/api/routes -> backend/app/api -> backend/app -> backend -> project_root
    current_file = Path(__file__)
    return current_file.parent.parent.parent.parent.parent


@router.get("/", response_class=PlainTextResponse)
async def get_help():
    """
    Get the Quick Start guide markdown content from QUICK_START.md.
    
    Returns:
        The QUICK_START.md file content as plain text.
    """
    try:
        project_root = get_project_root()
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


@router.get("/images/{image_name}")
async def get_help_image(image_name: str):
    """
    Serve images referenced in the help documentation.
    
    Args:
        image_name: Name of the image file (e.g., lens_1.png)
    
    Returns:
        The image file as a FileResponse.
    """
    try:
        project_root = get_project_root()
        image_path = project_root / image_name
        
        logger.info(f"Help API: Serving image: {image_path}")
        
        # Security: Only allow image files and prevent path traversal
        if not image_name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')):
            raise HTTPException(
                status_code=400,
                detail="Only image files are allowed"
            )
        
        if '..' in image_name or '/' in image_name or '\\' in image_name:
            raise HTTPException(
                status_code=400,
                detail="Invalid image path"
            )
        
        if not image_path.exists():
            logger.error(f"Help API: Image not found at: {image_path}")
            raise HTTPException(
                status_code=404,
                detail=f"Image not found: {image_name}"
            )
        
        # Determine media type based on file extension
        media_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.webp': 'image/webp',
        }
        media_type = media_type_map.get(image_path.suffix.lower(), 'image/png')
        
        logger.info(f"Help API: Successfully serving image: {image_name}")
        return FileResponse(
            path=str(image_path),
            media_type=media_type,
            filename=image_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Help API: Error serving image {image_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve image: {str(e)}"
        )
