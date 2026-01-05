"""Utility for running insights standalone (outside of the FastAPI server)."""

import asyncio
import logging
import sys
from typing import List
from app.insights.base import Insight
from app.core.models import InsightResult

logger = logging.getLogger(__name__)


def print_progress(message: str, verbose: bool = False):
    """Print progress message to console."""
    if verbose:
        print(f"[PROGRESS] {message}", file=sys.stderr)
    else:
        # Only print important progress updates
        if any(keyword in message.lower() for keyword in ["complete", "error", "cancelled", "starting"]):
            print(f"[PROGRESS] {message}", file=sys.stderr)


async def run_insight_standalone(
    insight: Insight,
    file_paths: List[str],
    verbose: bool = False,
    show_progress: bool = True
) -> InsightResult:
    """
    Run an insight standalone (outside of FastAPI server).
    
    Args:
        insight: Insight instance to run
        file_paths: List of file paths to analyze
        verbose: If True, print detailed progress messages
        show_progress: If True, print progress updates to stderr
        
    Returns:
        InsightResult from the analysis
    """
    if not file_paths:
        raise ValueError("No file paths provided")
    
    # Validate file paths exist
    import os
    invalid_paths = [path for path in file_paths if not os.path.exists(path)]
    if invalid_paths:
        raise FileNotFoundError(f"File(s) not found: {', '.join(invalid_paths)}")
    
    print(f"\n{'='*70}", file=sys.stderr)
    print(f"Running: {insight.name} ({insight.id})", file=sys.stderr)
    print(f"Files: {len(file_paths)}", file=sys.stderr)
    print(f"{'='*70}\n", file=sys.stderr)
    
    # Simple progress callback for standalone execution
    async def progress_callback(event):
        if show_progress:
            print_progress(event.message, verbose=verbose)
    
    try:
        # Run the insight analysis
        result = await insight.analyze(
            file_paths=file_paths,
            cancellation_event=None,  # No cancellation for standalone runs
            progress_callback=progress_callback if show_progress else None
        )
        
        return result
    except Exception as e:
        print(f"\n[ERROR] Analysis failed: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        raise


def format_result(result: InsightResult) -> str:
    """
    Format an InsightResult for console output.
    
    Args:
        result: InsightResult to format
        
    Returns:
        Formatted string representation
    """
    output = []
    
    if result.result_type == "text":
        output.append(result.content)
    elif result.result_type == "json":
        import json
        output.append(json.dumps(result.content, indent=2))
    else:
        output.append(str(result.content))
    
    # Add metadata if available
    if result.metadata:
        output.append("\n" + "="*70)
        output.append("Metadata:")
        import json
        output.append(json.dumps(result.metadata, indent=2))
    
    return "\n".join(output)


def main_standalone(insight: Insight, file_paths: List[str], verbose: bool = False):
    """
    Main entry point for standalone insight execution.
    
    Handles async execution and result display.
    
    Args:
        insight: Insight instance to run
        file_paths: List of file paths to analyze
        verbose: Enable verbose output
    """
    import sys
    
    # Run the insight
    try:
        result = asyncio.run(run_insight_standalone(insight, file_paths, verbose=verbose))
        
        # Print results to stdout
        print(format_result(result))
        
        # Exit with success
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n[INFO] Analysis cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

