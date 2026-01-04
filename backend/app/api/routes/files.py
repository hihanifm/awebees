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
    all_files = []
    
    for path in request.paths:
        if not validate_file_path(path):
            logger.warning(f"Invalid or inaccessible path: {path}")
            continue
        
        path_obj = Path(path)
        
        if path_obj.is_file():
            all_files.append(str(path_obj.resolve()))
        elif path_obj.is_dir():
            try:
                folder_files = await list_files_in_folder(str(path_obj.resolve()), recursive=True)
                all_files.extend(folder_files)
            except Exception as e:
                logger.error(f"Error listing files in folder {path}: {e}")
                raise HTTPException(status_code=400, detail=f"Error reading folder {path}: {str(e)}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for file_path in all_files:
        if file_path not in seen:
            seen.add(file_path)
            unique_files.append(file_path)
    
    return FileSelectResponse(
        files=unique_files,
        count=len(unique_files)
    )

