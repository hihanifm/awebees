"""Utility for running config-based insights standalone."""

import asyncio
import logging
import sys
import os
import importlib.util
from pathlib import Path
from typing import List, Optional
from app.core.config_insight import ConfigBasedInsight
from app.core.models import InsightResult
from app.utils.insight_runner import (
    check_venv_and_reexecute,
    print_progress,
    run_insight_standalone,
    format_result
)

logger = logging.getLogger(__name__)


def load_config_from_file(file_path: str) -> tuple[dict, Optional[callable]]:
    """
    Load INSIGHT_CONFIG and optional process_results function from a Python file.
    
    Args:
        file_path: Path to Python file containing INSIGHT_CONFIG
        
    Returns:
        Tuple of (config dict, process_results function or None)
        
    Raises:
        ValueError: If file doesn't contain INSIGHT_CONFIG
    """
    file_path = Path(file_path).resolve()
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.suffix == ".py":
        raise ValueError(f"File must be a Python file (.py): {file_path}")
    
    # Load the module dynamically
    spec = importlib.util.spec_from_file_location("config_module", file_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Failed to load module spec from: {file_path}")
    
    module = importlib.util.module_from_spec(spec)
    
    # Add parent directory to sys.path temporarily to resolve relative imports
    parent_dir = str(file_path.parent)
    sys.path.insert(0, parent_dir)
    
    try:
        spec.loader.exec_module(module)
    finally:
        # Remove from sys.path
        if parent_dir in sys.path:
            sys.path.remove(parent_dir)
    
    # Extract INSIGHT_CONFIG
    if not hasattr(module, 'INSIGHT_CONFIG'):
        raise ValueError(f"File does not contain INSIGHT_CONFIG: {file_path}")
    
    insight_config = getattr(module, 'INSIGHT_CONFIG')
    
    # Extract optional process_results function
    process_results_fn = getattr(module, 'process_results', None)
    
    return insight_config, process_results_fn


def main_config_standalone(
    file_path: str,
    input_file_paths: Optional[List[str]] = None,
    verbose: bool = False,
    check_venv: bool = True
):
    """
    Main entry point for standalone config-based insight execution.
    
    Args:
        file_path: Path to the config-based insight file
        input_file_paths: Optional list of file paths to analyze (overrides CLI args)
        verbose: Enable verbose output
        check_venv: If True, check for venv and re-execute if needed
    """
    # Configure logging for standalone execution
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s:%(name)s:%(message)s',
        stream=sys.stderr
    )
    
    # Check venv and re-execute if needed (only once, at the start)
    if check_venv:
        try:
            # Try importing a dependency to see if we're in the right environment
            import pydantic
        except ImportError:
            check_venv_and_reexecute()
    
    try:
        # Load config and process_results function from file
        print(f"\n{'='*70}", file=sys.stderr)
        print(f"Loading config-based insight from: {file_path}", file=sys.stderr)
        print(f"{'='*70}\n", file=sys.stderr)
        
        insight_config, process_results_fn = load_config_from_file(file_path)
        
        # Create ConfigBasedInsight instance
        insight = ConfigBasedInsight(
            config=insight_config,
            process_results_fn=process_results_fn,
            module_name=Path(file_path).stem
        )
        
        print(f"Loaded: {insight.name} ({insight.id})", file=sys.stderr)
        print(f"Description: {insight.description}\n", file=sys.stderr)
        
        # Get file paths to analyze
        if input_file_paths is None:
            # Parse from CLI arguments (skip script name and config file path)
            # sys.argv[0] = module, sys.argv[1] = config file, sys.argv[2:] = file paths
            args = sys.argv[2:] if len(sys.argv) > 2 else []
            
            # Check for verbose flag
            if "--verbose" in args or "-v" in args:
                args = [arg for arg in args if arg not in ["--verbose", "-v"]]
            
            # Check if there's a DEFAULT_FILE_PATHS in the config (for convenience)
            default_paths = insight_config.get("default_file_paths", [])
            
            if args:
                input_file_paths = args
            elif default_paths:
                print(f"Using default file paths from config: {len(default_paths)} file(s)", file=sys.stderr)
                input_file_paths = default_paths
            else:
                # Interactive mode
                print("Enter file or folder paths (one per line, empty line to finish):", file=sys.stderr)
                input_file_paths = []
                while True:
                    try:
                        line = input().strip()
                        if not line:
                            break
                        input_file_paths.append(line)
                    except (EOFError, KeyboardInterrupt):
                        break
                
                if not input_file_paths:
                    print("No file paths provided. Exiting.", file=sys.stderr)
                    sys.exit(1)
        
        # Run the insight
        result = asyncio.run(run_insight_standalone(insight, input_file_paths, verbose=verbose))
        
        # Print results to stdout
        print(format_result(result))
        
        # Exit with success
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n[INFO] Analysis cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # If run directly, expect first argument to be the config file path
    if len(sys.argv) < 2:
        print("Usage: python -m app.utils.config_insight_runner <insight_file.py> [file_paths...]", file=sys.stderr)
        sys.exit(1)
    
    config_file = sys.argv[1]
    file_paths = sys.argv[2:] if len(sys.argv) > 2 else None
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    if file_paths:
        file_paths = [fp for fp in file_paths if fp not in ["--verbose", "-v"]]
    
    main_config_standalone(config_file, file_paths, verbose=verbose)

