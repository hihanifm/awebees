# Unit Tests for filter_base.py

## Overview

Comprehensive unit tests for `app/core/filter_base.py`, covering all core classes:
- `FilterResult` - Result storage and aggregation
- `FileFilter` - File filtering and expansion
- `LineFilter` - Line filtering with multiple reading modes
- `FilterBasedInsight` - Abstract base class for filter-based insights
- `ReadingMode` - Enum for reading modes

## Test Coverage

The test suite includes:
- **74 test functions** covering all major functionality
- Unit tests for all public methods
- Edge case handling (empty inputs, invalid patterns, errors)
- Async operation testing (cancellation, progress callbacks)
- Mocking of external dependencies (file system, ripgrep)

## Setup

1. Install test dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Ensure you're in the backend directory or have PYTHONPATH set correctly.

## Running Tests

Run all tests:
```bash
cd backend
pytest tests/ -v
```

Run tests for filter_base.py only:
```bash
pytest tests/app/core/test_filter_base.py -v
```

Run with coverage:
```bash
pytest tests/app/core/test_filter_base.py --cov=app/core/filter_base --cov-report=term-missing
```

Run specific test class:
```bash
pytest tests/app/core/test_filter_base.py::TestFilterResult -v
```

Run specific test:
```bash
pytest tests/app/core/test_filter_base.py::TestFilterResult::test_add_line_to_new_file -v
```

## Test Structure

- `tests/conftest.py` - Shared fixtures (temp directories, mock objects)
- `tests/app/core/test_filter_base.py` - Main test file (all test classes)
- `tests/pytest.ini` - Pytest configuration

## Test Classes

1. **TestFilterResult** - Tests for FilterResult class
2. **TestFileFilter** - Tests for FileFilter class  
3. **TestLineFilter** - Tests for LineFilter class
4. **TestFilterBasedInsight** - Tests for FilterBasedInsight abstract class
5. **TestReadingMode** - Tests for ReadingMode enum
6. **TestEdgeCases** - Edge case and error handling tests

## Key Test Scenarios

### Happy Paths
- Simple file filtering and line matching
- Multiple files processed successfully
- All reading modes (LINES, CHUNKS, RIPGREP) work correctly
- Progress events emitted correctly

### Error Handling
- Invalid regex patterns (should not crash)
- Missing files (should continue with others)
- Ripgrep unavailable (should fall back)
- File read errors (should continue)
- Cancellation during processing

### Edge Cases
- Empty file lists
- Files with no matches
- Very long file paths
- Special regex characters in patterns
- Unicode file names

## Coverage Goals

Target: **90%+ code coverage** for `filter_base.py`

To check current coverage:
```bash
pytest tests/app/core/test_filter_base.py --cov=app/core/filter_base --cov-report=term-missing --cov-report=html
```

The HTML report will be in `htmlcov/index.html`.
