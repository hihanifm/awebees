#!/usr/bin/env python3
"""
Standalone script to run any insight by ID.

Usage:
    python scripts/run_insight.py <insight_id> [file1.log] [file2.log] ...
    python scripts/run_insight.py <insight_id>  # Interactive mode if no files provided

Examples:
    python scripts/run_insight.py error_detector /path/to/logfile.log
    python scripts/run_insight.py line_count  # Will prompt for file paths
"""

import sys
import os

# Get script directory and project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')

# Add backend directory to path so we can import app modules
sys.path.insert(0, BACKEND_DIR)

# Try to use venv Python if available
VENV_PYTHON = os.path.join(BACKEND_DIR, 'venv', 'bin', 'python3')
if os.path.exists(VENV_PYTHON):
    # If we're not already using venv Python, re-execute with it
    if sys.executable != VENV_PYTHON:
        os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

from app.core.plugin_manager import get_plugin_manager
from app.utils.insight_runner import main_standalone


def main():
    """Main entry point for the test runner script."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_insight.py <insight_id> [file1.log] [file2.log] ...", file=sys.stderr)
        print("\nAvailable insights:", file=sys.stderr)
        
        # Show available insights
        try:
            plugin_manager = get_plugin_manager()
            insights = plugin_manager.get_all_insights()
            for insight in insights:
                print(f"  - {insight.id}: {insight.name}", file=sys.stderr)
        except Exception as e:
            print(f"  Error loading insights: {e}", file=sys.stderr)
        
        sys.exit(1)
    
    insight_id = sys.argv[1]
    
    # Get file paths from remaining arguments
    if len(sys.argv) > 2:
        file_paths = [arg for arg in sys.argv[2:] if arg not in ["--verbose", "-v"]]
    else:
        file_paths = []
    
    # Check for verbose flag
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    # Load the insight
    try:
        plugin_manager = get_plugin_manager()
        plugin_manager.discover_insights()
        insight = plugin_manager.get_insight(insight_id)
        
        if not insight:
            print(f"Error: Insight '{insight_id}' not found.", file=sys.stderr)
            print("\nAvailable insights:", file=sys.stderr)
            insights = plugin_manager.get_all_insights()
            for ins in insights:
                print(f"  - {ins.id}: {ins.name}", file=sys.stderr)
            sys.exit(1)
        
        # If no file paths provided, use interactive mode
        if not file_paths:
            print("Enter file paths (one per line, empty line to finish):", file=sys.stderr)
            while True:
                try:
                    line = input().strip()
                    if not line:
                        break
                    file_paths.append(line)
                except (EOFError, KeyboardInterrupt):
                    break
            
            if not file_paths:
                print("No file paths provided. Exiting.", file=sys.stderr)
                sys.exit(1)
        
        # Run the insight
        main_standalone(insight, file_paths, verbose=verbose)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

