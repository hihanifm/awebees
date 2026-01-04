"""API routes for file selection."""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from app.services.file_handler import validate_file_path, list_files_in_folder
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])


class FileSelectRequest(BaseModel):
    """Request to select files/folders."""
    paths: List[str]


class FileSelectResponse(BaseModel):
    """Response with selected files."""
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

