# Creating Insights for Lens

This guide explains how to create insights for the Lens application.

## Table of Contents

- [Overview](#overview)
- [Config-Based Insights (Recommended)](#config-based-insights-recommended)
- [Class-Based Insights (Advanced)](#class-based-insights-advanced)
- [When to Use Each Approach](#when-to-use-each-approach)
- [Testing Your Insight](#testing-your-insight)

## Overview

Lens supports two ways to create insights:

1. **Config-Based Insights**: Simple, declarative approach using Python dictionaries (recommended for most use cases)
2. **Class-Based Insights**: Full control with Python classes (for complex logic)

## Config-Based Insights (Recommended)

Config-based insights are perfect for filtering-based analysis. They eliminate boilerplate and let you focus on the logic.

### Minimal Example

```python
"""My simple insight."""

INSIGHT_CONFIG = {
    "metadata": {
        "id": "my_insight",
        "name": "My Insight",
        "description": "Finds interesting patterns"
    },
    "filters": {
        "line_pattern": r"\b(WARNING|ERROR)\b"
    }
}

if __name__ == "__main__":
    from app.utils.config_insight_runner import main_config_standalone
    main_config_standalone(__file__)
```

That's it! This creates a functional insight that:
- Filters lines matching the regex pattern
- Provides default formatting
- Supports standalone execution
- Integrates with the web UI

### Full Example with Custom Formatting

```python
"""Advanced insight with custom post-processing."""

import logging

logger = logging.getLogger(__name__)

INSIGHT_CONFIG = {
    "metadata": {
        "id": "error_summary",
        "name": "Error Summary",
        "description": "Analyzes and summarizes error patterns",
        "folder": "diagnostics"  # Optional: organize in folders
    },
    "filters": {
        "file_patterns": [r"\.log$", r"\.txt$"],  # Optional: filter files in folders
        "line_pattern": r"\b(ERROR|FATAL)\b",      # Required: regex for lines
        "regex_flags": "IGNORECASE",               # Optional: IGNORECASE, MULTILINE, etc.
        "reading_mode": "lines"                     # Optional: "lines" or "chunks" (default: "lines")
    },
    "default_file_paths": [
        # Optional: hardcoded defaults for quick testing
        # "/path/to/test/file.log"
    ]
}


def process_results(filter_result):
    """
    Optional: Custom post-processing of filtered results.
    
    If not defined, a default formatter shows filtered lines with counts.
    
    Args:
        filter_result: FilterResult object with methods:
            - get_lines() -> List[str]: All filtered lines as flat list
            - get_lines_by_file() -> Dict[str, List[str]]: Lines grouped by file
            - get_total_line_count() -> int: Total matching lines
            - get_file_count() -> int: Number of files with matches
    
    Returns:
        dict with required 'content' key (str) and optional 'metadata' key (dict)
    """
    lines_by_file = filter_result.get_lines_by_file()
    total_errors = filter_result.get_total_line_count()
    
    # Custom formatting logic
    content = f"Error Analysis\n"
    content += f"{'=' * 50}\n\n"
    content += f"Total errors: {total_errors:,}\n\n"
    
    for file_path, lines in lines_by_file.items():
        content += f"{file_path}: {len(lines):,} errors\n"
        # Show first 5 lines
        for line in lines[:5]:
            content += f"  {line.strip()[:100]}\n"
        if len(lines) > 5:
            content += f"  ... and {len(lines) - 5:,} more\n"
    
    return {
        "content": content,
        "metadata": {
            "total_errors": total_errors,
            "files": len(lines_by_file)
        }
    }


if __name__ == "__main__":
    from app.utils.config_insight_runner import main_config_standalone
    main_config_standalone(__file__)
```

### Configuration Reference

#### Metadata Section

```python
"metadata": {
    "id": "unique_id",           # Required: Unique identifier (no spaces)
    "name": "Display Name",      # Required: Human-readable name
    "description": "...",        # Required: Short description
    "folder": "category_name"    # Optional: Organize insights into folders
}
```

#### Filters Section

```python
"filters": {
    # Optional: Filter files in folders (None = process all files)
    # Multiple patterns use OR logic
    "file_patterns": [r"\.log$", r"\.txt$"],
    
    # Required: Regex pattern for filtering lines
    "line_pattern": r"\b(ERROR|FATAL)\b",
    
    # Optional: Regex flags (comma-separated string)
    # Available: IGNORECASE, MULTILINE, DOTALL, VERBOSE, ASCII
    "regex_flags": "IGNORECASE",
    
    # Optional: Reading mode
    # "lines" = line-by-line (default, memory efficient)
    # "chunks" = chunk-based (faster for large files)
    "reading_mode": "lines",
    
    # Optional: Chunk size in bytes (only for chunks mode)
    "chunk_size": 1048576  # 1MB default
}
```

#### Optional Features

```python
# Hardcoded default file paths for quick testing
"default_file_paths": [
    "/path/to/test/file1.log",
    "/path/to/test/file2.log"
]
```

## Class-Based Insights (Advanced)

For complex logic that goes beyond filtering, use class-based insights.

### When to Use Class-Based

- Custom counting or aggregation logic
- Multi-pass analysis
- Complex state management
- Non-filtering operations (e.g., statistics, transformations)

### Example

```python
"""Custom insight with complex logic."""

from typing import List, Optional, Callable, Awaitable
import logging
import asyncio
from app.core.insight_base import Insight
from app.core.models import InsightResult, ProgressEvent

logger = logging.getLogger(__name__)


class CustomInsight(Insight):
    """Custom insight with full control."""
    
    @property
    def id(self) -> str:
        return "custom_insight"
    
    @property
    def name(self) -> str:
        return "Custom Insight"
    
    @property
    def description(self) -> str:
        return "Complex custom analysis"
    
    async def analyze(
        self,
        file_paths: List[str],
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> InsightResult:
        """
        Custom analysis logic.
        
        Args:
            file_paths: Files to analyze
            cancellation_event: Check for cancellation
            progress_callback: Emit progress events
            
        Returns:
            InsightResult with analysis results
        """
        # Your custom logic here
        result_text = "Custom analysis results...\n"
        
        return InsightResult(
            result_type="text",
            content=result_text,
            metadata={"custom_key": "custom_value"}
        )


if __name__ == "__main__":
    import sys
    from app.utils.insight_runner import main_standalone
    
    # Parse arguments
    if len(sys.argv) > 1:
        file_paths = [arg for arg in sys.argv[1:] if arg not in ["--verbose", "-v"]]
    else:
        print("Enter file paths (one per line, empty line to finish):", file=sys.stderr)
        file_paths = []
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
    
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    main_standalone(CustomInsight(), file_paths, verbose=verbose)
```

## When to Use Each Approach

### Use Config-Based When:
- ✅ Your insight is primarily filtering lines (ERROR, WARNING, patterns)
- ✅ You want simple, declarative configuration
- ✅ You need file pattern filtering for folders
- ✅ Standard progress and cancellation support is sufficient

### Use Class-Based When:
- ✅ You need complex counting or aggregation
- ✅ You need multi-pass analysis
- ✅ You need custom state management
- ✅ You're doing transformations, not filtering

**Example: `line_count` is class-based** because it counts lines (not filtering), while **`error_detector` is config-based** because it filters ERROR/FATAL lines.

## Testing Your Insight

### 1. Standalone Execution

Run your insight directly:

```bash
# From backend directory
cd backend

# For config-based insights
python -m app.insights.error_detector /path/to/file.log

# For class-based insights
python -m app.insights.line_count /path/to/file.log

# With verbose logging
python -m app.insights.error_detector /path/to/file.log --verbose

# Interactive mode (no file paths provided)
python -m app.insights.error_detector
```

### 2. Using the Test Runner Script

```bash
# From project root
cd scripts

# Run any insight
./run_insight.py error_detector /path/to/file.log

# With verbose output
./run_insight.py error_detector /path/to/file.log --verbose
```

### 3. Via Web UI

1. Start the application: `./scripts/start.sh`
2. Open http://localhost:34000
3. Enter file paths
4. Select your insight
5. Click "Analyze Files"

### 4. Via API

```bash
# Get list of insights
curl http://localhost:34001/api/insights

# Run analysis
curl -X POST http://localhost:34001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "file_paths": ["/path/to/file.log"],
    "insight_ids": ["error_detector"]
  }'
```

## File Organization

Insights are organized in the `backend/app/insights/` directory:

```
backend/app/insights/
├── README.md           # This file
├── error_detector.py   # Config-based insight example
├── line_count.py       # Class-based insight example
└── my_folder/          # Optional: organize insights in folders
    ├── insight1.py
    └── insight2.py
```

Insights in subdirectories are automatically discovered and organized by folder in the UI.

## Best Practices

1. **Start with config-based** - Try the simpler approach first
2. **Use descriptive IDs** - Use snake_case: `error_detector`, not `ErrorDetector`
3. **Write good descriptions** - Help users understand what your insight does
4. **Test standalone first** - Easier to debug than via the web UI
5. **Use logging** - Log progress and debug info to stderr
6. **Handle edge cases** - Empty files, no matches, large files
7. **Limit output** - Don't return millions of lines (use sampling/limits)
8. **Use folders** - Organize related insights together

## Examples

See the existing insights for reference:

- **`error_detector.py`** - Config-based insight with custom formatting (~96 lines)
- **`line_count.py`** - Class-based insight with custom logic (~217 lines)

## Need Help?

- Check existing insights for examples
- Read the inline documentation in base classes
- Test your insight standalone before integrating
- Use `--verbose` flag to see detailed logs

