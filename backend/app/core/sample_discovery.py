import json
import logging
import os
import zipfile
import gzip
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.insight_paths_config import InsightPathsConfig
from app.core.constants import SAMPLES_DIR

logger = logging.getLogger(__name__)


class SampleInfo:
    """Information about a sample file."""
    
    def __init__(
        self,
        sample_id: str,
        name: str,
        description: str,
        path: str,
        size_mb: float,
        exists: bool,
        source: str,
        recommended_insights: List[str] = None
    ):
        self.id = sample_id
        self.name = name
        self.description = description
        self.path = path
        self.size_mb = size_mb
        self.exists = exists
        self.source = source
        self.recommended_insights = recommended_insights or []
    
    def to_dict(self) -> Dict[str, Any]: return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "path": self.path,
            "size_mb": self.size_mb,
            "exists": self.exists,
            "source": self.source,
            "recommended_insights": self.recommended_insights
        }


def extract_zip_file(zip_path: Path, samples_dir: Path) -> Optional[Path]:
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract only text/log files, skip __MACOSX folder
            for member in zip_ref.namelist():
                if (member.endswith('.txt') or member.endswith('.log')) and not member.startswith('__MACOSX'):
                    extracted_path = samples_dir / member
                    zip_ref.extract(member, samples_dir)
                    
                    # Use the base name of the zip file (without extension) for the extracted file
                    base_name = zip_path.stem
                    target_path = samples_dir / f"{base_name}.txt"
                    
                    # Rename if different
                    if extracted_path.name != target_path.name:
                        if extracted_path.exists():
                            extracted_path.rename(target_path)
                    
                    logger.info(f"✓ Extracted sample: {target_path.name} from {zip_path.name}")
                    return target_path
    except Exception as e:
        logger.error(f"Failed to extract ZIP file {zip_path}: {e}", exc_info=True)
    
    return None


def extract_gz_file(gz_path: Path, samples_dir: Path) -> Optional[Path]:
    try:
        base_name = gz_path.stem
        target_path = samples_dir / f"{base_name}.txt"
        
        if target_path.exists():
            return target_path
        
        with gzip.open(gz_path, 'rb') as gz_ref:
            with open(target_path, 'wb') as out_file:
                out_file.write(gz_ref.read())
        
        logger.info(f"✓ Extracted sample: {target_path.name} from {gz_path.name}")
        return target_path
    except Exception as e:
        logger.error(f"Failed to extract GZ file {gz_path}: {e}", exc_info=True)
    
    return None


def load_sample_metadata(sample_path: Path) -> Optional[Dict[str, Any]]:
    metadata_path = sample_path.parent / f"{sample_path.stem}.json"
    
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load metadata from {metadata_path}: {e}")
    
    return None


def infer_sample_metadata(sample_path: Path) -> Dict[str, Any]:
    name = sample_path.stem.replace('_', ' ').replace('-', ' ').title()
    size_mb = sample_path.stat().st_size / (1024 * 1024) if sample_path.exists() else 0
    description = f"Sample file: {sample_path.name}"
    
    return {
        "name": name,
        "description": description,
        "size_mb": round(size_mb, 1)
    }


def discover_samples_from_path(insight_path: str, source_label: str) -> List[SampleInfo]:
    samples = []
    samples_dir = Path(insight_path) / "samples"
    
    # Skip if samples directory doesn't exist
    if not samples_dir.exists():
        logger.debug(f"No samples directory found at: {samples_dir}")
        return samples
    
    if not samples_dir.is_dir():
        logger.warning(f"Samples path exists but is not a directory: {samples_dir}")
        return samples
    
    # Supported file extensions
    supported_extensions = {'.txt', '.log', '.zip', '.gz'}
    
    try:
        # Track processed sample IDs to avoid duplicates
        processed_ids = set()
        
        # Scan for sample files
        for file_path in samples_dir.iterdir():
            if not file_path.is_file():
                continue
            
            # Skip metadata JSON files
            if file_path.suffix == '.json':
                continue
            
            sample_path = None
            sample_id = None
            
            # Handle compressed files
            if file_path.suffix == '.zip':
                # Extract if not already extracted
                extracted_path = samples_dir / f"{file_path.stem}.txt"
                if not extracted_path.exists():
                    extracted_path = extract_zip_file(file_path, samples_dir)
                    if extracted_path is None:
                        continue
                
                sample_path = extracted_path
                sample_id = file_path.stem.lower().replace(' ', '_').replace('-', '_')
                    
            elif file_path.suffix == '.gz':
                # Extract if not already extracted
                extracted_path = samples_dir / f"{file_path.stem}.txt"
                if not extracted_path.exists():
                    extracted_path = extract_gz_file(file_path, samples_dir)
                    if extracted_path is None:
                        continue
                
                sample_path = extracted_path
                sample_id = file_path.stem.lower().replace(' ', '_').replace('-', '_')
            
            # Handle plain text/log files
            elif file_path.suffix in {'.txt', '.log'}:
                # Check if there's a corresponding zip/gz file
                zip_path = samples_dir / f"{file_path.stem}.zip"
                gz_path = samples_dir / f"{file_path.stem}.gz"
                
                # If compressed version exists, skip this (prefer compressed source)
                if zip_path.exists() or gz_path.exists():
                    continue
                
                sample_path = file_path
                sample_id = file_path.stem.lower().replace(' ', '_').replace('-', '_')
            else:
                # Unsupported extension
                continue
            
            # Skip if already processed
            if sample_id in processed_ids:
                continue
            
            processed_ids.add(sample_id)
            
            # Load metadata if available
            metadata = load_sample_metadata(sample_path)
            
            if metadata:
                name = metadata.get("name", sample_path.stem)
                description = metadata.get("description", f"Sample file: {sample_path.name}")
                size_mb = metadata.get("size_mb", 0)
                recommended_insights = metadata.get("recommended_insights", [])
            else:
                # Infer from filename and file size
                inferred = infer_sample_metadata(sample_path)
                name = inferred["name"]
                description = inferred["description"]
                size_mb = inferred["size_mb"]
                recommended_insights = []
            
            # Check if file exists
            exists = sample_path.exists() and sample_path.is_file()
            
            samples.append(SampleInfo(
                sample_id=sample_id,
                name=name,
                description=description,
                path=str(sample_path.resolve()),
                size_mb=size_mb,
                exists=exists,
                source=source_label,
                recommended_insights=recommended_insights
            ))
            
            logger.debug(f"Discovered sample: {sample_id} from {source_label}")
    
    except PermissionError as e:
        logger.error(f"Permission denied accessing samples directory {samples_dir}: {e}")
    except Exception as e:
        logger.error(f"Error discovering samples from {insight_path}: {e}", exc_info=True)
    
    return samples


def discover_all_samples() -> List[SampleInfo]:
    all_samples = []
    
    # Discover built-in samples
    if SAMPLES_DIR.exists():
        logger.debug(f"Discovering built-in samples from: {SAMPLES_DIR}")
        built_in_samples = discover_samples_from_path(str(SAMPLES_DIR), "built-in")
        all_samples.extend(built_in_samples)
        logger.info(f"Discovered {len(built_in_samples)} built-in sample(s)")
    
    # Discover external samples
    try:
        paths_config = InsightPathsConfig()
        external_paths = paths_config.get_paths()
        
        for external_path in external_paths:
            if not os.path.exists(external_path):
                logger.warning(f"External insight path does not exist: {external_path}")
                continue
            
            logger.debug(f"Discovering samples from external path: {external_path}")
            external_samples = discover_samples_from_path(external_path, f"external: {external_path}")
            all_samples.extend(external_samples)
            
            if external_samples:
                logger.info(f"Discovered {len(external_samples)} sample(s) from {external_path}")
    except Exception as e:
        logger.error(f"Error discovering external samples: {e}", exc_info=True)
    
    logger.info(f"Total samples discovered: {len(all_samples)}")
    return all_samples
