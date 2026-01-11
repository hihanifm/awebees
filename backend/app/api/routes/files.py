"""API routes for file selection."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import os

from app.services.file_handler import validate_file_path
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
    
    normalized = path.strip()
    
    if len(normalized) >= 2:
        first = normalized[0]
        last = normalized[-1]
        
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
    and returns them as-is. Folder expansion and filtering
    happens in the insight processing layer.
    """
    import time
    start_time = time.time()
    logger.info(f"Files API: Received file selection request for {len(request.paths)} path(s)")
    
    validated_paths = []
    
    for path_idx, path in enumerate(request.paths, 1):
        logger.debug(f"Files API: Processing path {path_idx}/{len(request.paths)}: {path}")
        
        normalized_path = normalize_path(path)
        
        if not validate_file_path(normalized_path):
            logger.warning(f"Files API: Invalid or inaccessible path: {normalized_path}")
            continue
        
        resolved_path = str(Path(normalized_path).resolve())
        validated_paths.append(resolved_path)
        logger.debug(f"Files API: Validated path: {resolved_path}")
    
    seen = set()
    unique_paths = []
    for path in validated_paths:
        if path not in seen:
            seen.add(path)
            unique_paths.append(path)
    
    duplicates_removed = len(validated_paths) - len(unique_paths)
    if duplicates_removed > 0:
        logger.debug(f"Files API: Removed {duplicates_removed} duplicate path(s)")
    
    elapsed = time.time() - start_time
    logger.info(f"Files API: File selection complete - {len(unique_paths)} unique path(s) validated in {elapsed:.2f}s")
    
    return FileSelectResponse(
        files=unique_paths,
        count=len(unique_paths)
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
    
    all_samples = discover_all_samples()
    samples = [sample.to_dict() for sample in all_samples]
    
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

