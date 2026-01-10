"""Utility for running insights standalone (outside of the FastAPI server)."""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import List
from app.core.insight_base import Insight
from app.core.models import InsightResult

logger = logging.getLogger(__name__)


def check_venv_and_reexecute():
    """
    Check if we're in a venv, and if not, try to re-execute with venv Python.
    
    This allows insights to be run without manually activating the venv.
    """
    # Check if we're already in a venv
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return  # Already in a venv
    
    # Try to find venv Python relative to this file
    # This file is in backend/app/utils/, so venv should be in backend/venv/
    current_file = Path(__file__).resolve()
    backend_dir = current_file.parent.parent.parent  # backend/app/utils -> backend
    venv_python = backend_dir / "venv" / "bin" / "python"
    
    if venv_python.exists():
        # Re-execute with venv Python
        import subprocess
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)
    else:
        # Provide helpful error message
        print("Error: Virtual environment not found or not activated.", file=sys.stderr)
        print(f"Expected venv at: {venv_python}", file=sys.stderr)
        print("\nPlease either:", file=sys.stderr)
        print("  1. Activate the venv: source backend/venv/bin/activate", file=sys.stderr)
        print(f"  2. Use venv Python directly: {venv_python} -m app.insights.<insight_name>", file=sys.stderr)
        sys.exit(1)


def print_progress(message: str, verbose: bool = False):
    if verbose:
        print(f"[PROGRESS] {message}", file=sys.stderr)
    else:
        # Only print important progress updates
        if any(keyword in message.lower() for keyword in ["complete", "error", "cancelled", "starting"]):
            print(f"[PROGRESS] {message}", file=sys.stderr)


async def run_insight_standalone(
    insight: Insight,
    user_path: str,
    verbose: bool = False,
    show_progress: bool = True
) -> InsightResult:
    # Run an insight standalone (outside of FastAPI server) for a single path
    import os
    if not os.path.exists(user_path):
        raise FileNotFoundError(f"Path not found: {user_path}")
    
    print(f"\n{'='*70}", file=sys.stderr)
    print(f"Running: {insight.name} ({insight.id})", file=sys.stderr)
    print(f"Path: {user_path}", file=sys.stderr)
    print(f"{'='*70}\n", file=sys.stderr)
    
    # Simple progress callback for standalone execution
    async def progress_callback(event):
        if show_progress:
            print_progress(event.message, verbose=verbose)
    
    try:
        # Run the insight analysis for this path
        result = await insight.analyze(
            user_path=user_path,
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


async def run_insight_with_ai_standalone(
    insight: Insight,
    user_path: str,
    verbose: bool = False,
    show_progress: bool = True
) -> InsightResult:
    # Similar to run_insight_standalone but calls analyze_with_ai() which auto-triggers AI if ai_auto=true
    import os
    if not os.path.exists(user_path):
        raise FileNotFoundError(f"Path not found: {user_path}")
    
    print(f"\n{'='*70}", file=sys.stderr)
    print(f"Running: {insight.name} ({insight.id})", file=sys.stderr)
    print(f"Path: {user_path}", file=sys.stderr)
    print(f"{'='*70}\n", file=sys.stderr)
    
    # Simple progress callback for standalone execution
    async def progress_callback(event):
        if show_progress:
            print_progress(event.message, verbose=verbose)
    
    try:
        # Call analyze_with_ai for this path
        result = await insight.analyze_with_ai(
            user_path=user_path,
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


def main_standalone(insight: Insight, user_path: str, verbose: bool = False, check_venv: bool = True):
    # Main entry point for standalone insight execution (handles async execution and result display)
    import sys
    
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
    
    # Run the insight for this path
    try:
        result = asyncio.run(run_insight_standalone(insight, user_path, verbose=verbose))
        
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

