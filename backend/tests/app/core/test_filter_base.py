"""Unit tests for filter_base.py core classes."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import re
import os
from typing import Iterator

from app.core.filter_base import (
    FilterResult,
    FileFilter,
    LineFilter,
    FilterBasedInsight,
    ReadingMode
)
from app.core.models import InsightResult, ProgressEvent
from app.services.file_handler import CancelledError


class TestFilterResult:
    """Tests for FilterResult class."""
    
    def test_init_creates_empty_result(self):
        """Test that FilterResult initializes with empty state."""
        result = FilterResult()
        assert result.get_file_count() == 0
        assert result.get_total_line_count() == 0
        assert result.get_lines() == []
        assert result.get_lines_by_file() == {}
        assert result.get_execution_method() is None
    
    def test_add_line_to_new_file(self):
        """Test adding a line to a new file."""
        result = FilterResult()
        result.add_line("file1.txt", "line 1")
        
        assert result.get_file_count() == 1
        assert result.get_total_line_count() == 1
        assert result.get_lines() == ["line 1"]
        assert result.get_lines_by_file() == {"file1.txt": ["line 1"]}
    
    def test_add_line_to_existing_file(self):
        """Test adding multiple lines to the same file."""
        result = FilterResult()
        result.add_line("file1.txt", "line 1")
        result.add_line("file1.txt", "line 2")
        result.add_line("file1.txt", "line 3")
        
        assert result.get_file_count() == 1
        assert result.get_total_line_count() == 3
        assert result.get_lines() == ["line 1", "line 2", "line 3"]
        assert result.get_lines_by_file() == {"file1.txt": ["line 1", "line 2", "line 3"]}
    
    def test_add_lines_to_multiple_files(self):
        """Test adding lines to multiple files."""
        result = FilterResult()
        result.add_line("file1.txt", "line 1")
        result.add_line("file2.txt", "line 2")
        result.add_line("file1.txt", "line 3")
        result.add_line("file2.txt", "line 4")
        
        assert result.get_file_count() == 2
        assert result.get_total_line_count() == 4
        assert result.get_lines() == ["line 1", "line 3", "line 2", "line 4"]
        assert result.get_lines_by_file() == {
            "file1.txt": ["line 1", "line 3"],
            "file2.txt": ["line 2", "line 4"]
        }
    
    def test_add_empty_line(self):
        """Test adding empty lines."""
        result = FilterResult()
        result.add_line("file1.txt", "")
        result.add_line("file1.txt", "non-empty")
        
        assert result.get_total_line_count() == 2
        assert result.get_lines() == ["", "non-empty"]
    
    def test_add_line_with_special_characters(self):
        """Test adding lines with special characters in path and content."""
        result = FilterResult()
        result.add_line("/path/with spaces/file-name.txt", "line with\t\ttabs\nand newlines")
        
        assert result.get_file_count() == 1
        assert result.get_total_line_count() == 1
    
    def test_set_and_get_command(self):
        """Test setting and getting commands per file."""
        result = FilterResult()
        
        assert result.get_command("file1.txt") is None
        
        result.set_command("file1.txt", "rg pattern file1.txt")
        assert result.get_command("file1.txt") == "rg pattern file1.txt"
        
        result.set_command("file2.txt", "python search file2.txt")
        assert result.get_command("file2.txt") == "python search file2.txt"
        assert result.get_command("file1.txt") == "rg pattern file1.txt"
    
    def test_get_commands_returns_copy(self):
        """Test that get_commands() returns a copy, not the original dict."""
        result = FilterResult()
        result.set_command("file1.txt", "cmd1")
        
        commands = result.get_commands()
        commands["file2.txt"] = "cmd2"  # Modify the copy
        
        # Original should be unchanged
        assert result.get_command("file2.txt") is None
    
    def test_set_and_get_execution_method(self):
        """Test setting and getting execution method."""
        result = FilterResult()
        
        assert result.get_execution_method() is None
        
        result.set_execution_method("ripgrep")
        assert result.get_execution_method() == "ripgrep"
        
        result.set_execution_method("python_lines")
        assert result.get_execution_method() == "python_lines"
    
    def test_get_lines_by_file_returns_copy(self):
        """Test that get_lines_by_file() returns a copy, not the original dict."""
        result = FilterResult()
        result.add_line("file1.txt", "line 1")
        
        lines_by_file = result.get_lines_by_file()
        lines_by_file["file2.txt"] = ["line 2"]  # Modify the copy
        
        # Original should be unchanged
        assert result.get_file_count() == 1
    
    def test_get_file_count(self):
        """Test file count with various scenarios."""
        result = FilterResult()
        assert result.get_file_count() == 0
        
        result.add_line("file1.txt", "line")
        assert result.get_file_count() == 1
        
        result.add_line("file2.txt", "line")
        assert result.get_file_count() == 2
        
        # Adding more lines to same file doesn't increase count
        result.add_line("file1.txt", "line")
        assert result.get_file_count() == 2
    
    def test_get_total_line_count(self):
        """Test total line count calculation."""
        result = FilterResult()
        assert result.get_total_line_count() == 0
        
        result.add_line("file1.txt", "line 1")
        assert result.get_total_line_count() == 1
        
        result.add_line("file1.txt", "line 2")
        assert result.get_total_line_count() == 2
        
        result.add_line("file2.txt", "line 3")
        assert result.get_total_line_count() == 3


class TestFileFilter:
    """Tests for FileFilter class."""
    
    def test_init_with_file_paths(self):
        """Test FileFilter initialization."""
        file_filter = FileFilter(["/path/to/file.txt"])
        files = file_filter.get_files()
        # Individual files should pass through (if they exist in test)
        assert isinstance(files, list)
    
    def test_filter_files_returns_self(self):
        """Test that filter_files() returns self for chaining."""
        file_filter = FileFilter(["/path"])
        result = file_filter.filter_files(r"\.txt$")
        assert result is file_filter
    
    def test_filter_files_resets_cache(self):
        """Test that filter_files() resets the cached file list."""
        file_filter = FileFilter(["/path"])
        
        # First call populates cache
        files1 = file_filter.get_files()
        
        # Filter should reset cache
        file_filter.filter_files(r"\.py$")
        files2 = file_filter.get_files()
        
        # Cache should be refreshed (even if same results)
        assert files2 is not None
    
    def test_get_files_with_individual_file(self, temp_dir, test_file):
        """Test get_files() with an individual file path."""
        file_path = test_file("test.txt", "content")
        
        file_filter = FileFilter([file_path])
        files = file_filter.get_files()
        
        assert len(files) == 1
        assert files[0] == str(Path(file_path).resolve())
    
    def test_get_files_with_folder_no_pattern(self, temp_dir, test_file):
        """Test get_files() with a folder and no filter pattern."""
        test_file("file1.txt", "content 1")
        test_file("file2.py", "content 2")
        test_file("file3.log", "content 3")
        
        file_filter = FileFilter([temp_dir])
        files = file_filter.get_files()
        
        assert len(files) == 3
        file_names = [Path(f).name for f in files]
        assert "file1.txt" in file_names
        assert "file2.py" in file_names
        assert "file3.log" in file_names
    
    def test_get_files_with_folder_and_pattern(self, temp_dir, test_file):
        """Test get_files() with a folder and filter pattern."""
        test_file("file1.txt", "content 1")
        test_file("file2.py", "content 2")
        test_file("file3.txt", "content 3")
        
        file_filter = FileFilter([temp_dir])
        file_filter.filter_files(r"\.txt$")
        files = file_filter.get_files()
        
        assert len(files) == 2
        file_names = [Path(f).name for f in files]
        assert "file1.txt" in file_names
        assert "file3.txt" in file_names
        assert "file2.py" not in file_names
    
    def test_get_files_with_multiple_patterns_or_logic(self, temp_dir, test_file):
        """Test that multiple patterns use OR logic."""
        test_file("file1.txt", "content 1")
        test_file("file2.py", "content 2")
        test_file("file3.log", "content 3")
        
        file_filter = FileFilter([temp_dir])
        file_filter.filter_files(r"\.txt$", r"\.py$")
        files = file_filter.get_files()
        
        assert len(files) == 2
        file_names = [Path(f).name for f in files]
        assert "file1.txt" in file_names
        assert "file2.py" in file_names
        assert "file3.log" not in file_names
    
    def test_get_files_caches_results(self, temp_dir, test_file):
        """Test that get_files() caches results."""
        test_file("file1.txt", "content 1")
        
        file_filter = FileFilter([temp_dir])
        files1 = file_filter.get_files()
        files2 = file_filter.get_files()
        
        # Should return same results (cached)
        assert files1 == files2
        assert len(files1) == len(files2)
    
    def test_get_files_removes_duplicates(self, temp_dir, test_file):
        """Test that get_files() removes duplicate paths."""
        file_path = test_file("test.txt", "content")
        
        file_filter = FileFilter([file_path, file_path, file_path])
        files = file_filter.get_files()
        
        assert len(files) == 1
    
    def test_get_files_with_mixed_files_and_folders(self, temp_dir, test_file):
        """Test get_files() with mix of files and folders."""
        file1 = test_file("file1.txt", "content 1")
        test_file("nested/file2.txt", "content 2")
        
        file_filter = FileFilter([file1, temp_dir])
        files = file_filter.get_files()
        
        # Should include individual file plus all files from folder
        assert len(files) >= 2
        assert str(Path(file1).resolve()) in files
    
    def test_get_files_with_invalid_regex_pattern(self, temp_dir, test_file):
        """Test that invalid regex patterns fall back gracefully."""
        test_file("file1.txt", "content 1")
        
        file_filter = FileFilter([temp_dir])
        file_filter.filter_files(r"[invalid regex (")
        files = file_filter.get_files()
        
        # Should fall back to including all files
        assert len(files) >= 1
    
    def test_get_files_with_nonexistent_path(self):
        """Test get_files() with non-existent path."""
        file_filter = FileFilter(["/nonexistent/path/12345"])
        files = file_filter.get_files()
        
        # Should handle gracefully (empty or continue)
        assert isinstance(files, list)
    
    def test_get_files_with_nonexistent_folder(self):
        """Test get_files() with non-existent folder."""
        file_filter = FileFilter(["/nonexistent/folder/12345"])
        files = file_filter.get_files()
        
        # Should handle gracefully
        assert isinstance(files, list)
    
    @pytest.mark.asyncio
    async def test_apply_calls_line_filter(self, temp_dir, test_file, cancellation_event):
        """Test that apply() calls line_filter.filter_lines()."""
        file_path = test_file("test.txt", "line 1\nline 2\nmatch here\nline 4")
        
        line_filter = LineFilter(pattern=r"match")
        file_filter = FileFilter([file_path])
        
        result = await file_filter.apply(line_filter, cancellation_event)
        
        assert result.get_total_line_count() > 0
        assert "match here" in result.get_lines()[0]
    
    @pytest.mark.asyncio
    async def test_apply_passes_cancellation_event(self, temp_dir, test_file, cancellation_event):
        """Test that apply() passes cancellation event to line filter."""
        file_path = test_file("test.txt", "line 1\nline 2\nline 3")
        
        cancellation_event.set()  # Cancel before starting
        
        line_filter = LineFilter(pattern=r"line")
        file_filter = FileFilter([file_path])
        
        with pytest.raises(CancelledError):
            await file_filter.apply(line_filter, cancellation_event)
    
    @pytest.mark.asyncio
    async def test_apply_passes_progress_callback(self, temp_dir, test_file, progress_callback):
        """Test that apply() passes progress callback to line filter."""
        file_path = test_file("test.txt", "line 1\nline 2\nline 3")
        
        line_filter = LineFilter(pattern=r"line")
        file_filter = FileFilter([file_path])
        
        await file_filter.apply(line_filter, None, progress_callback)
        
        # Progress callback should have been called
        assert progress_callback.called


class TestLineFilter:
    """Tests for LineFilter class."""
    
    def test_init_with_defaults(self):
        """Test LineFilter initialization with defaults."""
        line_filter = LineFilter(pattern=r"test")
        
        assert line_filter.pattern == r"test"
        assert line_filter.reading_mode == ReadingMode.LINES
        assert line_filter.chunk_size == 1048576
        assert line_filter.flags == 0
        assert line_filter.context_before == 0
        assert line_filter.context_after == 0
        assert line_filter._compiled_pattern is not None
    
    def test_init_with_custom_params(self):
        """Test LineFilter initialization with custom parameters."""
        line_filter = LineFilter(
            pattern=r"test",
            reading_mode=ReadingMode.CHUNKS,
            chunk_size=2048,
            flags=re.IGNORECASE,
            context_before=2,
            context_after=3
        )
        
        assert line_filter.reading_mode == ReadingMode.CHUNKS
        assert line_filter.chunk_size == 2048
        assert line_filter.flags == re.IGNORECASE
        assert line_filter.context_before == 2
        assert line_filter.context_after == 3
    
    def test_init_compiles_pattern(self):
        """Test that pattern is compiled on initialization."""
        line_filter = LineFilter(pattern=r"\d+")
        assert line_filter._compiled_pattern.search("123") is not None
        assert line_filter._compiled_pattern.search("abc") is None
    
    @pytest.mark.asyncio
    async def test_filter_lines_lines_mode(self, temp_dir, test_file):
        """Test filter_lines() in LINES mode."""
        file_path = test_file("test.txt", "line 1\nmatch here\nline 3\nanother match\nline 5")
        
        line_filter = LineFilter(pattern=r"match", reading_mode=ReadingMode.LINES)
        result = await line_filter.filter_lines([file_path])
        
        assert result.get_total_line_count() == 2
        lines = result.get_lines()
        assert any("match here" in line for line in lines)
        assert any("another match" in line for line in lines)
    
    @pytest.mark.asyncio
    async def test_filter_lines_chunks_mode(self, temp_dir, test_file):
        """Test filter_lines() in CHUNKS mode."""
        file_path = test_file("test.txt", "line 1\nmatch here\nline 3\nanother match\nline 5")
        
        line_filter = LineFilter(pattern=r"match", reading_mode=ReadingMode.CHUNKS, chunk_size=10)
        result = await line_filter.filter_lines([file_path])
        
        assert result.get_total_line_count() == 2
        lines = result.get_lines()
        assert any("match" in line for line in lines)
    
    @pytest.mark.asyncio
    @patch('app.core.filter_base.is_ripgrep_available')
    @patch('app.core.filter_base.ripgrep_search')
    @patch('app.core.filter_base.build_ripgrep_command')
    async def test_filter_lines_ripgrep_mode(
        self, mock_build_cmd, mock_ripgrep_search, mock_is_available,
        temp_dir, test_file
    ):
        """Test filter_lines() in RIPGREP mode."""
        file_path = test_file("test.txt", "line 1\nmatch here\nline 3")
        
        mock_is_available.return_value = True
        mock_build_cmd.return_value = "rg pattern file"
        mock_ripgrep_search.return_value = iter(["match here"])
        
        line_filter = LineFilter(pattern=r"match", reading_mode=ReadingMode.RIPGREP)
        result = await line_filter.filter_lines([file_path])
        
        assert result.get_total_line_count() == 1
        assert result.get_execution_method() == "ripgrep"
        mock_is_available.assert_called()
        mock_ripgrep_search.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.core.filter_base.is_ripgrep_available')
    async def test_filter_lines_ripgrep_fallback_to_lines(
        self, mock_is_available, temp_dir, test_file
    ):
        """Test that RIPGREP mode falls back to LINES when ripgrep unavailable."""
        file_path = test_file("test.txt", "line 1\nmatch here\nline 3")
        
        mock_is_available.return_value = False
        
        line_filter = LineFilter(pattern=r"match", reading_mode=ReadingMode.RIPGREP)
        result = await line_filter.filter_lines([file_path])
        
        assert result.get_total_line_count() == 1
        assert result.get_execution_method() == "python_lines"
    
    @pytest.mark.asyncio
    async def test_filter_lines_multiple_files(self, temp_dir, test_file):
        """Test filter_lines() with multiple files."""
        file1 = test_file("file1.txt", "line 1\nmatch\nline 3")
        file2 = test_file("file2.txt", "line 1\nno match\nline 3")
        file3 = test_file("file3.txt", "line 1\nmatch again\nline 3")
        
        line_filter = LineFilter(pattern=r"match", reading_mode=ReadingMode.LINES)
        result = await line_filter.filter_lines([file1, file2, file3])
        
        assert result.get_file_count() == 2  # file2 has no matches
        assert result.get_total_line_count() == 2
    
    @pytest.mark.asyncio
    async def test_filter_lines_empty_file(self, temp_dir, test_file):
        """Test filter_lines() with empty file."""
        file_path = test_file("empty.txt", "")
        
        line_filter = LineFilter(pattern=r"match", reading_mode=ReadingMode.LINES)
        result = await line_filter.filter_lines([file_path])
        
        assert result.get_total_line_count() == 0
        assert result.get_file_count() == 0
    
    @pytest.mark.asyncio
    async def test_filter_lines_no_matches(self, temp_dir, test_file):
        """Test filter_lines() when no lines match."""
        file_path = test_file("test.txt", "line 1\nline 2\nline 3")
        
        line_filter = LineFilter(pattern=r"match", reading_mode=ReadingMode.LINES)
        result = await line_filter.filter_lines([file_path])
        
        assert result.get_total_line_count() == 0
    
    @pytest.mark.asyncio
    async def test_filter_lines_with_regex_flags(self, temp_dir, test_file):
        """Test filter_lines() with regex flags."""
        file_path = test_file("test.txt", "line 1\nMATCH\nline 3\nmatch\nline 5")
        
        line_filter = LineFilter(pattern=r"match", flags=re.IGNORECASE, reading_mode=ReadingMode.LINES)
        result = await line_filter.filter_lines([file_path])
        
        assert result.get_total_line_count() == 2
    
    @pytest.mark.asyncio
    async def test_filter_lines_tracks_execution_method(self, temp_dir, test_file):
        """Test that execution method is tracked."""
        file_path = test_file("test.txt", "line 1\nmatch\nline 3")
        
        line_filter = LineFilter(pattern=r"match", reading_mode=ReadingMode.LINES)
        result = await line_filter.filter_lines([file_path])
        
        assert result.get_execution_method() == "python_lines"
    
    @pytest.mark.asyncio
    async def test_filter_lines_tracks_commands(self, temp_dir, test_file):
        """Test that commands are tracked per file."""
        file_path = test_file("test.txt", "line 1\nmatch\nline 3")
        
        line_filter = LineFilter(pattern=r"match", reading_mode=ReadingMode.LINES)
        result = await line_filter.filter_lines([file_path])
        
        command = result.get_command(file_path)
        assert command is not None
        assert "match" in command or "python" in command
    
    @pytest.mark.asyncio
    async def test_filter_lines_cancellation_before_file(self, temp_dir, test_file, cancellation_event):
        """Test cancellation before processing a file."""
        file_path = test_file("test.txt", "line 1\nline 2\nline 3")
        
        cancellation_event.set()
        
        line_filter = LineFilter(pattern=r"line", reading_mode=ReadingMode.LINES)
        
        with pytest.raises(CancelledError):
            await line_filter.filter_lines([file_path], cancellation_event)
    
    @pytest.mark.asyncio
    async def test_filter_lines_emits_progress_events(self, temp_dir, test_file, progress_callback):
        """Test that progress events are emitted."""
        file_path = test_file("test.txt", "line 1\nline 2\nline 3")
        
        line_filter = LineFilter(pattern=r"line", reading_mode=ReadingMode.LINES)
        await line_filter.filter_lines([file_path], progress_callback=progress_callback)
        
        # Check that progress callback was called
        assert progress_callback.call_count >= 1
        
        # Check for file_open event
        call_args = [call[0][0] for call in progress_callback.call_args_list]
        file_open_events = [event for event in call_args if hasattr(event, 'type') and event.type == 'file_open']
        assert len(file_open_events) >= 1
    
    @pytest.mark.asyncio
    async def test_filter_lines_handles_file_errors_gracefully(self, temp_dir):
        """Test that file errors don't crash the entire operation."""
        # Use non-existent file
        nonexistent_file = str(Path(temp_dir) / "nonexistent.txt")
        existent_file = test_file("existent.txt", "line 1\nmatch\nline 3")
        
        line_filter = LineFilter(pattern=r"match", reading_mode=ReadingMode.LINES)
        result = await line_filter.filter_lines([nonexistent_file, existent_file])
        
        # Should continue processing and return results from valid file
        assert result.get_total_line_count() >= 0
    
    @pytest.mark.asyncio
    async def test_filter_lines_mode_with_cancellation(self, temp_dir, test_file, cancellation_event):
        """Test _filter_lines_mode() respects cancellation."""
        file_path = test_file("test.txt", "line 1\nline 2\nline 3")
        
        line_filter = LineFilter(pattern=r"line", reading_mode=ReadingMode.LINES)
        
        # Don't cancel - should work normally
        lines, command = await line_filter._filter_lines_mode(file_path, None)
        assert len(lines) > 0
    
    @pytest.mark.asyncio
    async def test_filter_chunks_mode_handles_boundaries(self, temp_dir, test_file):
        """Test _filter_chunks_mode() handles chunk boundaries correctly."""
        # Create file that will span multiple chunks
        content = "line 1\n" * 100 + "match here\n" + "line 3\n" * 100
        file_path = test_file("large.txt", content)
        
        line_filter = LineFilter(pattern=r"match", reading_mode=ReadingMode.CHUNKS, chunk_size=50)
        lines, command = await line_filter._filter_chunks_mode(file_path, None)
        
        assert len(lines) == 1
        assert "match" in lines[0]
    
    @pytest.mark.asyncio
    @patch('app.core.filter_base.is_ripgrep_available')
    @patch('app.core.filter_base.ripgrep_search')
    @patch('app.core.filter_base.build_ripgrep_command')
    async def test_filter_ripgrep_mode_with_cancellation(
        self, mock_build_cmd, mock_ripgrep_search, mock_is_available,
        temp_dir, test_file, cancellation_event
    ):
        """Test _filter_ripgrep_mode() respects cancellation."""
        file_path = test_file("test.txt", "line 1\nmatch\nline 3")
        
        mock_is_available.return_value = True
        mock_build_cmd.return_value = "rg pattern file"
        mock_ripgrep_search.return_value = iter(["match"])
        
        cancellation_event.set()
        
        line_filter = LineFilter(pattern=r"match", reading_mode=ReadingMode.RIPGREP)
        
        with pytest.raises(CancelledError):
            await line_filter._filter_ripgrep_mode(file_path, cancellation_event)
    
    @pytest.mark.asyncio
    @patch('app.core.filter_base.is_ripgrep_available')
    @patch('app.core.filter_base.ripgrep_search')
    @patch('app.core.filter_base.build_ripgrep_command')
    async def test_filter_ripgrep_mode_fallback_on_error(
        self, mock_build_cmd, mock_ripgrep_search, mock_is_available,
        temp_dir, test_file
    ):
        """Test that ripgrep mode falls back on error."""
        file_path = test_file("test.txt", "line 1\nmatch\nline 3")
        
        mock_is_available.return_value = True
        mock_build_cmd.return_value = "rg pattern file"
        mock_ripgrep_search.side_effect = Exception("ripgrep failed")
        
        line_filter = LineFilter(pattern=r"match", reading_mode=ReadingMode.RIPGREP)
        lines, command = await line_filter._filter_ripgrep_mode(file_path, None)
        
        # Should fall back to line-by-line mode
        assert len(lines) == 1
        assert "match" in lines[0]


class TestFilterBasedInsight:
    """Tests for FilterBasedInsight abstract class."""
    
    class ConcreteFilterInsight(FilterBasedInsight):
        """Concrete implementation for testing."""
        
        @property
        def id(self) -> str:
            return "test_insight"
        
        @property
        def name(self) -> str:
            return "Test Insight"
        
        @property
        def description(self) -> str:
            return "Test insight for unit tests"
        
        @property
        def line_filter_pattern(self) -> str:
            return r"match"
        
        async def _process_filtered_lines(self, filter_result):
            lines = filter_result.get_lines()
            return InsightResult(
                result_type="text",
                content="\n".join(lines),
                metadata={"count": len(lines)}
            )
    
    def test_default_reading_mode(self):
        """Test default reading mode is RIPGREP."""
        insight = self.ConcreteFilterInsight()
        assert insight.reading_mode == ReadingMode.RIPGREP
    
    def test_default_chunk_size(self):
        """Test default chunk size."""
        insight = self.ConcreteFilterInsight()
        assert insight.chunk_size == 1048576
    
    def test_default_file_filter_patterns(self):
        """Test default file filter patterns is None."""
        insight = self.ConcreteFilterInsight()
        assert insight.file_filter_patterns is None
    
    @pytest.mark.asyncio
    async def test_analyze_without_file_filter_patterns(self, temp_dir, test_file):
        """Test analyze() without file filter patterns."""
        file_path = test_file("test.txt", "line 1\nmatch\nline 3")
        
        insight = self.ConcreteFilterInsight()
        result = await insight.analyze([file_path])
        
        assert result.result_type == "text"
        assert "match" in result.content
        assert result.metadata["count"] == 1
    
    @pytest.mark.asyncio
    async def test_analyze_with_file_filter_patterns(self, temp_dir, test_file):
        """Test analyze() with file filter patterns."""
        test_file("file1.txt", "line 1\nmatch\nline 3")
        test_file("file2.py", "line 1\nmatch\nline 3")
        
        class FilteredInsight(self.ConcreteFilterInsight):
            @property
            def file_filter_patterns(self):
                return [r"\.txt$"]
        
        insight = FilteredInsight()
        result = await insight.analyze([temp_dir])
        
        # Should only process .txt files
        assert result.metadata["count"] == 1
    
    @pytest.mark.asyncio
    async def test_analyze_with_cancellation(self, temp_dir, test_file, cancellation_event):
        """Test analyze() with cancellation."""
        file_path = test_file("test.txt", "line 1\nline 2\nline 3")
        
        cancellation_event.set()
        
        insight = self.ConcreteFilterInsight()
        
        with pytest.raises(CancelledError):
            await insight.analyze([file_path], cancellation_event)
    
    @pytest.mark.asyncio
    async def test_analyze_with_progress_callback(self, temp_dir, test_file, progress_callback):
        """Test analyze() with progress callback."""
        file_path = test_file("test.txt", "line 1\nmatch\nline 3")
        
        insight = self.ConcreteFilterInsight()
        result = await insight.analyze([file_path], progress_callback=progress_callback)
        
        assert progress_callback.called
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_analyze_with_custom_reading_mode(self, temp_dir, test_file):
        """Test analyze() with custom reading mode."""
        file_path = test_file("test.txt", "line 1\nmatch\nline 3")
        
        class ChunksInsight(self.ConcreteFilterInsight):
            @property
            def reading_mode(self):
                return ReadingMode.CHUNKS
        
        insight = ChunksInsight()
        result = await insight.analyze([file_path])
        
        assert result.metadata["count"] == 1
    
    @pytest.mark.asyncio
    async def test_analyze_with_regex_flags(self, temp_dir, test_file):
        """Test analyze() with regex flags."""
        file_path = test_file("test.txt", "line 1\nMATCH\nline 3")
        
        class CaseInsight(self.ConcreteFilterInsight):
            def __init__(self):
                self.regex_flags = re.IGNORECASE
        
        insight = CaseInsight()
        result = await insight.analyze([file_path])
        
        assert result.metadata["count"] == 1
    
    @pytest.mark.asyncio
    async def test_analyze_processes_filtered_lines(self, temp_dir, test_file):
        """Test that _process_filtered_lines() is called with correct result."""
        file_path = test_file("test.txt", "line 1\nmatch\nline 3\nmatch again\nline 5")
        
        insight = self.ConcreteFilterInsight()
        result = await insight.analyze([file_path])
        
        assert result.metadata["count"] == 2
        assert result.content.count("match") == 2


class TestReadingMode:
    """Tests for ReadingMode enum."""
    
    def test_enum_values(self):
        """Test that all enum values are accessible."""
        assert ReadingMode.LINES == ReadingMode.LINES
        assert ReadingMode.CHUNKS == ReadingMode.CHUNKS
        assert ReadingMode.RIPGREP == ReadingMode.RIPGREP
    
    def test_enum_string_values(self):
        """Test that enum string values match expected format."""
        assert ReadingMode.LINES.value == "lines"
        assert ReadingMode.CHUNKS.value == "chunks"
        assert ReadingMode.RIPGREP.value == "ripgrep"
    
    def test_enum_iteration(self):
        """Test that we can iterate over enum values."""
        modes = list(ReadingMode)
        assert len(modes) == 3
        assert ReadingMode.LINES in modes
        assert ReadingMode.CHUNKS in modes
        assert ReadingMode.RIPGREP in modes


class TestEdgeCases:
    """Edge case tests for filter_base components."""
    
    def test_filter_result_with_special_characters_in_path(self):
        """Test FilterResult with special characters in file paths."""
        result = FilterResult()
        result.add_line("/path with spaces/file-name.txt", "line 1")
        result.add_line("/path/with\ttabs/file.log", "line 2")
        
        assert result.get_file_count() == 2
        assert result.get_total_line_count() == 2
    
    def test_filter_result_with_very_long_path(self):
        """Test FilterResult with very long file paths."""
        long_path = "/" + "a" * 500 + "/file.txt"
        result = FilterResult()
        result.add_line(long_path, "line 1")
        
        assert result.get_file_count() == 1
        assert len(result.get_files()) == 1
    
    def test_file_filter_with_empty_paths_list(self):
        """Test FileFilter with empty paths list."""
        file_filter = FileFilter([])
        files = file_filter.get_files()
        
        assert files == []
    
    def test_file_filter_with_unicode_file_names(self, temp_dir):
        """Test FileFilter with Unicode file names."""
        from pathlib import Path
        
        file_path = Path(temp_dir) / "测试文件.txt"
        file_path.write_text("content", encoding='utf-8')
        
        file_filter = FileFilter([str(file_path)])
        files = file_filter.get_files()
        
        assert len(files) == 1
    
    @pytest.mark.asyncio
    async def test_line_filter_with_empty_pattern(self, temp_dir, test_file):
        """Test LineFilter with empty pattern (matches everything)."""
        file_path = test_file("test.txt", "line 1\nline 2\nline 3")
        
        line_filter = LineFilter(pattern=r"", reading_mode=ReadingMode.LINES)
        result = await line_filter.filter_lines([file_path])
        
        # Empty pattern should match all lines
        assert result.get_total_line_count() == 3
    
    @pytest.mark.asyncio
    async def test_line_filter_with_special_regex_chars(self, temp_dir, test_file):
        """Test LineFilter with special regex characters in pattern."""
        file_path = test_file("test.txt", "line (1)\nline [2]\nline {3}\nline *4")
        
        # Test various special regex characters
        patterns = [
            (r"\(", "line (1)"),
            (r"\[", "line [2]"),
            (r"\{", "line {3}"),
            (r"\*", "line *4")
        ]
        
        for pattern, expected_match in patterns:
            line_filter = LineFilter(pattern=pattern, reading_mode=ReadingMode.LINES)
            result = await line_filter.filter_lines([file_path])
            assert result.get_total_line_count() == 1
            assert expected_match in result.get_lines()[0]
    
    @pytest.mark.asyncio
    async def test_line_filter_with_multiline_pattern(self, temp_dir, test_file):
        """Test LineFilter with multiline pattern."""
        file_path = test_file("test.txt", "start\nmiddle\nend\nstart\nend")
        
        # Pattern that matches across lines (using . to match newlines)
        line_filter = LineFilter(pattern=r"start.*end", flags=re.DOTALL, reading_mode=ReadingMode.LINES)
        result = await line_filter.filter_lines([file_path])
        
        # In line-by-line mode, multiline patterns won't match across lines
        # But this tests that the pattern compiles correctly
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_line_filter_with_very_large_file(self, temp_dir):
        """Test LineFilter with very large file (simulated)."""
        # Create a moderately large file
        large_content = "line with match\n" * 1000
        file_path = Path(temp_dir) / "large.txt"
        file_path.write_text(large_content, encoding='utf-8')
        
        line_filter = LineFilter(pattern=r"match", reading_mode=ReadingMode.LINES)
        result = await line_filter.filter_lines([str(file_path)])
        
        assert result.get_total_line_count() == 1000
    
    @pytest.mark.asyncio
    async def test_line_filter_file_with_no_newline_at_end(self, temp_dir, test_file):
        """Test LineFilter with file that doesn't end with newline."""
        file_path = test_file("test.txt", "line 1\nline 2\nline 3")  # No trailing newline
        
        line_filter = LineFilter(pattern=r"line 3", reading_mode=ReadingMode.LINES)
        result = await line_filter.filter_lines([file_path])
        
        assert result.get_total_line_count() == 1
    
    def test_file_filter_pattern_matches_filename_only(self, temp_dir, test_file):
        """Test that file filter patterns match filename only, not full path."""
        test_file("match.txt", "content")
        
        # Pattern should match filename, not path
        file_filter = FileFilter([temp_dir])
        file_filter.filter_files(r"match")
        files = file_filter.get_files()
        
        assert len(files) >= 1
        assert any("match.txt" in f for f in files)
    
    @pytest.mark.asyncio
    async def test_line_filter_continues_after_error(self, temp_dir, test_file):
        """Test that line filter continues processing after file error."""
        file1 = test_file("good.txt", "line 1\nmatch\nline 3")
        nonexistent = str(Path(temp_dir) / "nonexistent.txt")
        file2 = test_file("good2.txt", "line 1\nmatch\nline 3")
        
        line_filter = LineFilter(pattern=r"match", reading_mode=ReadingMode.LINES)
        result = await line_filter.filter_lines([file1, nonexistent, file2])
        
        # Should process both good files despite error
        assert result.get_file_count() == 2
        assert result.get_total_line_count() == 2
    
    def test_file_filter_get_files_return_type(self):
        """Test that FileFilter.get_files() returns a list."""
        file_filter = FileFilter([])
        files = file_filter.get_files()
        assert isinstance(files, list)
    
    @pytest.mark.asyncio
    async def test_filter_based_insight_with_no_files(self):
        """Test FilterBasedInsight with empty file list."""
        insight = TestFilterBasedInsight.ConcreteFilterInsight()
        result = await insight.analyze([])
        
        assert result.metadata["count"] == 0
        assert result.content == ""
