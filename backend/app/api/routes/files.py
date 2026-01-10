"""API routes for file selection."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import os

from app.services.file_handler import validate_file_path, list_files_in_folder
from app.core.constants import SAMPLE_FILES
from app.core.sample_discovery import discover_all_samples
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])


def normalize_path(path: str) -> str:
    """
    Normalize a file path by trimming whitespace and stripping surrounding quotes.
    
    Processing order:
    1. Trim whitespace from both ends
    2. Strip surrounding quotes (single or double) if matched
    
    Args:
        path: Raw path string that may have whitespace or quotes
        
    Returns:
        Normalized path string
    """
    if not path:
        return path
    
    # First trim whitespace
    normalized = path.strip()
    
    # Then strip surrounding quotes if matched
    if len(normalized) >= 2:
        first = normalized[0]
        last = normalized[-1]
        
        # Only strip if both ends have the same quote type
        if (first == '"' and last == '"') or (first == "'" and last == "'"):
            normalized = normalized[1:-1]
    
    return normalized


class FileSelectRequest(BaseModel):
    paths: List[str]


class FileSelectResponse(BaseModel):
    files: List[str]
    count: int


@router.post("/select", response_model=FileSelectResponse)
async def select_files(request: FileSelectRequest):
    """
    Select files and/or folders for analysis.
    
    Accepts a list of file and folder paths, validates them,
    and returns a flat list of all files (expanding folders).
    """
    import time
    start_time = time.time()
    logger.info(f"Files API: Received file selection request for {len(request.paths)} path(s)")
    
    all_files = []
    
    for path_idx, path in enumerate(request.paths, 1):
        logger.debug(f"Files API: Processing path {path_idx}/{len(request.paths)}: {path}")
        
        # Normalize path: trim whitespace and strip surrounding quotes
        path = normalize_path(path)
        
        if not validate_file_path(path):
            logger.warning(f"Files API: Invalid or inaccessible path: {path}")
            continue
        
        path_obj = Path(path)
        
        if path_obj.is_file():
            resolved_path = str(path_obj.resolve())
            logger.debug(f"Files API: Added file: {resolved_path}")
            all_files.append(resolved_path)
        elif path_obj.is_dir():
            try:
                logger.info(f"Files API: Expanding directory: {path}")
                folder_files = await list_files_in_folder(str(path_obj.resolve()), recursive=True)
                logger.info(f"Files API: Found {len(folder_files)} file(s) in directory: {path}")
                all_files.extend(folder_files)
            except Exception as e:
                logger.error(f"Files API: Error listing files in folder {path}: {e}", exc_info=True)
                raise HTTPException(status_code=400, detail=f"Error reading folder {path}: {str(e)}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for file_path in all_files:
        if file_path not in seen:
            seen.add(file_path)
            unique_files.append(file_path)
    
    duplicates_removed = len(all_files) - len(unique_files)
    if duplicates_removed > 0:
        logger.debug(f"Files API: Removed {duplicates_removed} duplicate file path(s)")
    
    elapsed = time.time() - start_time
    logger.info(f"Files API: File selection complete - {len(unique_files)} unique file(s) selected in {elapsed:.2f}s")
    
    return FileSelectResponse(
        files=unique_files,
        count=len(unique_files)
    )


@router.get("/samples")
async def get_sample_files() -> Dict[str, Any]:
    """
    Get information about available sample files.
    
    Returns:
        Dictionary with sample file information including paths and availability.
        Includes samples from built-in directory and all external insight paths.
    """
    logger.info("Files API: Getting sample files information")
    
    # Discover all samples (built-in + external)
    all_samples = discover_all_samples()
    
    # Convert to API response format
    samples = [sample.to_dict() for sample in all_samples]
    
    # Maintain backward compatibility: also include built-in samples from SAMPLE_FILES
    # if they weren't already discovered (fallback)
    discovered_ids = {sample["id"] for sample in samples}
    for sample_id, sample_info in SAMPLE_FILES.items():
        if sample_id not in discovered_ids:
            file_path = sample_info["path"]
            exists = os.path.exists(file_path)
            
            samples.append({
                "id": sample_id,
                "name": sample_info["name"],
                "description": sample_info["description"],
                "path": file_path,
                "size_mb": sample_info["size_mb"],
                "exists": exists,
                "source": "built-in",
                "recommended_insights": sample_info.get("recommended_insights", [])
            })
    
    logger.info(f"Files API: Returning {len(samples)} sample file(s)")
    return {"samples": samples}

