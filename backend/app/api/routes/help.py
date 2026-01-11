"""API routes for help documentation."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, FileResponse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/help", tags=["help"])


def get_project_root() -> Path:
    current_file = Path(__file__)
    return current_file.parent.parent.parent.parent.parent


@router.get("/", response_class=PlainTextResponse)
async def get_help():
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


@router.get("/docs/{file_path:path}")
async def get_help_doc(file_path: str):
    try:
        normalized_path = file_path.lstrip('/').lstrip('\\')
        
        # Prevent directory traversal attacks
        if '..' in normalized_path:
            raise HTTPException(
                status_code=400,
                detail="Invalid file path: directory traversal not allowed"
            )
        # Only allow .md files
        if not normalized_path.endswith('.md'):
            raise HTTPException(
                status_code=400,
                detail="Only markdown (.md) files are allowed"
            )
        doc_path = project_root / normalized_path
        resolved_path = doc_path.resolve()
        
        logger.info(f"Help API: Requested file_path: {file_path}")
        logger.info(f"Help API: Normalized path: {normalized_path}")
        logger.info(f"Help API: Resolved full path: {resolved_path}")
        
        # Ensure the file is within the project root (security check)
        try:
            resolved_path.relative_to(project_root.resolve())
        except ValueError:
            logger.error(f"Help API: Path traversal detected - {resolved_path} is outside project root {project_root.resolve()}")
            raise HTTPException(
                status_code=400,
                detail="Invalid file path: file must be within project root"
            )
        
        if not doc_path.exists() or not doc_path.is_file():
            logger.error(f"Help API: Documentation file not found at: {doc_path}")
            logger.error(f"Help API: File exists: {doc_path.exists()}, Is file: {doc_path.is_file() if doc_path.exists() else 'N/A'}")
            raise HTTPException(
                status_code=404,
                detail=f"Documentation file not found: {file_path}"
            )
        # Read and return the markdown content
        content = doc_path.read_text(encoding="utf-8")
        logger.info(f"Help API: Successfully read documentation file '{normalized_path}' ({len(content)} characters, first 100 chars: {content[:100]})")
        
        return PlainTextResponse(content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Help API: Error reading documentation file {file_path}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read documentation file: {str(e)}"
        )


@router.get("/images/{image_name}")
async def get_help_image(image_name: str):
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
