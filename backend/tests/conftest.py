"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path
import asyncio
from typing import AsyncGenerator, Callable, Awaitable
from unittest.mock import AsyncMock, Mock
from app.core.models import ProgressEvent


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_file(temp_dir):
    """Create a test file with specified content."""
    def _create_file(filename: str, content: str) -> str:
        file_path = Path(temp_dir) / filename
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        return str(file_path)
    return _create_file


@pytest.fixture
def test_files(temp_dir):
    """Create multiple test files with specified content."""
    def _create_files(files: dict[str, str]) -> list[str]:
        paths = []
        for filename, content in files.items():
            file_path = Path(temp_dir) / filename
            file_path.write_text(content, encoding='utf-8')
            paths.append(str(file_path))
        return paths
    return _create_files


@pytest.fixture
def cancellation_event():
    """Create an asyncio.Event for cancellation testing."""
    return asyncio.Event()


@pytest.fixture
def progress_callback():
    """Create a mock progress callback."""
    return AsyncMock(spec=Callable[[ProgressEvent], Awaitable[None]])


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
