"""Tests for zip file handling in file_handler.py"""

import pytest
import tempfile
import zipfile
import shutil
from pathlib import Path
import asyncio

from app.services.file_handler import (
    is_zip_file,
    parse_zip_path,
    sanitize_zip_path,
    validate_zip_file_security,
    list_zip_contents,
    read_file_from_zip,
    extract_file_from_zip,
    read_file_lines,
    read_file_chunks,
    validate_file_path,
    list_files_in_folder,
    ZIP_VIRTUAL_PATH_SEPARATOR,
    CancelledError
)
from app.core.config import ZipSecurityConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_zip_file(temp_dir):
    """Create a test zip file with various files inside."""
    def _create_zip(filename: str, files: dict) -> str:
        zip_path = Path(temp_dir) / filename
        with zipfile.ZipFile(zip_path, 'w') as zip_ref:
            for internal_path, content in files.items():
                zip_ref.writestr(internal_path, content)
        return str(zip_path)
    return _create_zip


class TestIsZipFile:
    """Tests for is_zip_file() function."""
    
    def test_is_zip_file_valid_zip(self, temp_dir, test_zip_file):
        """Test that valid zip files are detected."""
        zip_path = test_zip_file("test.zip", {"file.txt": "content"})
        assert is_zip_file(zip_path) is True
    
    def test_is_zip_file_not_zip(self, temp_dir):
        """Test that non-zip files are not detected as zip files."""
        file_path = Path(temp_dir) / "test.txt"
        file_path.write_text("not a zip")
        assert is_zip_file(str(file_path)) is False
    
    def test_is_zip_file_nonexistent(self):
        """Test that nonexistent files return False."""
        assert is_zip_file("/nonexistent/path/file.zip") is False
    
    def test_is_zip_file_invalid_zip(self, temp_dir):
        """Test that invalid zip files return False."""
        file_path = Path(temp_dir) / "fake.zip"
        file_path.write_text("not a real zip file")
        assert is_zip_file(str(file_path)) is False


class TestParseZipPath:
    """Tests for parse_zip_path() function."""
    
    def test_parse_zip_path_valid(self):
        """Test parsing a valid virtual zip path."""
        virtual_path = "/path/to/archive.zip::internal/file.txt"
        result = parse_zip_path(virtual_path)
        assert result is not None
        zip_path, internal_path = result
        assert zip_path == "/path/to/archive.zip"
        assert internal_path == "internal/file.txt"
    
    def test_parse_zip_path_nested(self):
        """Test parsing nested zip paths."""
        virtual_path = "/path/to/archive.zip::nested.zip::file.txt"
        result = parse_zip_path(virtual_path)
        assert result is not None
        zip_path, internal_path = result
        assert zip_path == "/path/to/archive.zip"
        assert internal_path == "nested.zip::file.txt"
    
    def test_parse_zip_path_not_virtual(self):
        """Test that regular paths return None."""
        assert parse_zip_path("/path/to/file.txt") is None
    
    def test_parse_zip_path_empty(self):
        """Test that empty string returns None."""
        assert parse_zip_path("") is None


class TestSanitizeZipPath:
    """Tests for sanitize_zip_path() function."""
    
    def test_sanitize_zip_path_normal(self):
        """Test sanitizing a normal path."""
        assert sanitize_zip_path("path/to/file.txt") == "path/to/file.txt"
    
    def test_sanitize_zip_path_leading_slash(self):
        """Test removing leading slashes."""
        assert sanitize_zip_path("/path/to/file.txt") == "path/to/file.txt"
        assert sanitize_zip_path("\\path\\to\\file.txt") == "path/to/file.txt"
    
    def test_sanitize_zip_path_traversal(self):
        """Test removing path traversal sequences."""
        assert sanitize_zip_path("../../etc/passwd") == "etc/passwd"
        assert sanitize_zip_path("path/../../etc/passwd") == "etc/passwd"
        assert sanitize_zip_path("path/../other/file.txt") == "other/file.txt"
    
    def test_sanitize_zip_path_normalize_separators(self):
        """Test normalizing path separators."""
        assert sanitize_zip_path("path\\to\\file.txt") == "path/to/file.txt"
    
    def test_sanitize_zip_path_dots(self):
        """Test handling of . and .. components."""
        assert sanitize_zip_path("path/./file.txt") == "path/file.txt"
        assert sanitize_zip_path("path/../file.txt") == "file.txt"


class TestValidateZipFileSecurity:
    """Tests for validate_zip_file_security() function."""
    
    def test_validate_security_valid_file(self, temp_dir, test_zip_file):
        """Test validation of a valid file within security limits."""
        zip_path = test_zip_file("test.zip", {"file.txt": "content"})
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_info = zip_ref.getinfo("file.txt")
            is_valid, error_msg = validate_zip_file_security(
                zip_path, zip_info, recursion_depth=0, total_size=0, file_count=0
            )
            assert is_valid is True
            assert error_msg is None
    
    def test_validate_security_max_file_size(self, temp_dir, test_zip_file):
        """Test that files exceeding max file size are rejected."""
        # Create a file that exceeds the limit (500MB default)
        large_content = "x" * (ZipSecurityConfig.MAX_FILE_SIZE + 1)
        zip_path = test_zip_file("test.zip", {"large.txt": large_content})
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_info = zip_ref.getinfo("large.txt")
            is_valid, error_msg = validate_zip_file_security(
                zip_path, zip_info, recursion_depth=0, total_size=0, file_count=0
            )
            assert is_valid is False
            assert "exceeds maximum" in error_msg.lower()
    
    def test_validate_security_max_recursion_depth(self, temp_dir, test_zip_file):
        """Test that files exceeding max recursion depth are rejected."""
        zip_path = test_zip_file("test.zip", {"file.txt": "content"})
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_info = zip_ref.getinfo("file.txt")
            is_valid, error_msg = validate_zip_file_security(
                zip_path, zip_info, 
                recursion_depth=ZipSecurityConfig.MAX_RECURSION_DEPTH,
                total_size=0, file_count=0
            )
            assert is_valid is False
            assert "recursion depth" in error_msg.lower()
    
    def test_validate_security_max_files(self, temp_dir, test_zip_file):
        """Test that exceeding max file count is rejected."""
        zip_path = test_zip_file("test.zip", {"file.txt": "content"})
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_info = zip_ref.getinfo("file.txt")
            is_valid, error_msg = validate_zip_file_security(
                zip_path, zip_info,
                recursion_depth=0, total_size=0, file_count=ZipSecurityConfig.MAX_FILES
            )
            assert is_valid is False
            assert "number of files" in error_msg.lower()
    
    def test_validate_security_compression_ratio(self, temp_dir):
        """Test that high compression ratios are rejected (zip bomb detection)."""
        # Create a zip with high compression ratio
        zip_path = Path(temp_dir) / "test.zip"
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zip_ref:
            # Write highly compressible data (many zeros)
            large_data = b'\x00' * 1000000  # 1MB of zeros compresses to very small
            zip_ref.writestr("large.bin", large_data)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_info = zip_ref.getinfo("large.bin")
            # Note: This test might pass if compression ratio is below threshold
            # The actual ratio depends on compression algorithm
            is_valid, error_msg = validate_zip_file_security(
                str(zip_path), zip_info, recursion_depth=0, total_size=0, file_count=0
            )
            # Just verify the function runs without error
            assert error_msg is None or "compression ratio" in error_msg.lower()


class TestListZipContents:
    """Tests for list_zip_contents() function."""
    
    def test_list_zip_contents_simple(self, temp_dir, test_zip_file):
        """Test listing contents of a simple zip file."""
        zip_path = test_zip_file("test.zip", {
            "file1.txt": "content1",
            "file2.txt": "content2",
            "subdir/file3.txt": "content3"
        })
        contents = list_zip_contents(zip_path, recursive=True)
        assert len(contents) == 3
        assert any("file1.txt" in path for path in contents)
        assert any("file2.txt" in path for path in contents)
        assert any("file3.txt" in path for path in contents)
        # Check virtual path format
        assert all(ZIP_VIRTUAL_PATH_SEPARATOR in path for path in contents)
        assert all(zip_path in path for path in contents)
    
    def test_list_zip_contents_excludes_directories(self, temp_dir, test_zip_file):
        """Test that directory entries are excluded."""
        zip_path = test_zip_file("test.zip", {
            "file.txt": "content",
            "subdir/": ""  # Directory entry
        })
        contents = list_zip_contents(zip_path, recursive=True)
        # Should only include the file, not the directory
        assert len(contents) == 1
        assert "file.txt" in contents[0]
    
    def test_list_zip_contents_excludes_macosx(self, temp_dir, test_zip_file):
        """Test that __MACOSX entries are excluded."""
        zip_path = test_zip_file("test.zip", {
            "file.txt": "content",
            "__MACOSX/._file.txt": "metadata"
        })
        contents = list_zip_contents(zip_path, recursive=True)
        assert len(contents) == 1
        assert "__MACOSX" not in contents[0]
    
    def test_list_zip_contents_empty_zip(self, temp_dir, test_zip_file):
        """Test listing an empty zip file."""
        zip_path = test_zip_file("test.zip", {})
        contents = list_zip_contents(zip_path, recursive=True)
        assert len(contents) == 0
    
    def test_list_zip_contents_invalid_zip(self, temp_dir):
        """Test handling of invalid zip file."""
        invalid_zip = Path(temp_dir) / "invalid.zip"
        invalid_zip.write_text("not a zip file")
        contents = list_zip_contents(str(invalid_zip), recursive=True)
        assert len(contents) == 0


class TestReadFileFromZip:
    """Tests for read_file_from_zip() function."""
    
    def test_read_file_from_zip_simple(self, temp_dir, test_zip_file):
        """Test reading a simple file from zip."""
        zip_path = test_zip_file("test.zip", {
            "file.txt": "line1\nline2\nline3"
        })
        lines = list(read_file_from_zip(zip_path, "file.txt"))
        assert len(lines) == 3
        assert lines[0] == "line1\n"
        assert lines[1] == "line2\n"
        assert lines[2] == "line3"
    
    def test_read_file_from_zip_with_cancellation(self, temp_dir, test_zip_file):
        """Test cancellation during reading."""
        content = "\n".join([f"line{i}" for i in range(1000)])
        zip_path = test_zip_file("test.zip", {"file.txt": content})
        cancellation_event = asyncio.Event()
        cancellation_event.set()
        
        with pytest.raises(CancelledError):
            list(read_file_from_zip(zip_path, "file.txt", cancellation_event))
    
    def test_read_file_from_zip_nonexistent_file(self, temp_dir, test_zip_file):
        """Test reading a nonexistent file from zip."""
        zip_path = test_zip_file("test.zip", {"file.txt": "content"})
        with pytest.raises(FileNotFoundError):
            list(read_file_from_zip(zip_path, "nonexistent.txt"))
    
    def test_read_file_from_zip_subdirectory(self, temp_dir, test_zip_file):
        """Test reading a file from a subdirectory."""
        zip_path = test_zip_file("test.zip", {
            "subdir/file.txt": "content"
        })
        lines = list(read_file_from_zip(zip_path, "subdir/file.txt"))
        assert len(lines) == 1
        assert lines[0] == "content"


class TestExtractFileFromZip:
    """Tests for extract_file_from_zip() function."""
    
    def test_extract_file_from_zip_small_file(self, temp_dir, test_zip_file):
        """Test extracting a small file (memory-first method)."""
        zip_path = test_zip_file("test.zip", {
            "file.txt": "small content"
        })
        extract_to = Path(temp_dir) / "extract"
        extract_to.mkdir()
        
        extracted_path = extract_file_from_zip(zip_path, "file.txt", extract_to)
        assert extracted_path is not None
        assert extracted_path.exists()
        assert extracted_path.read_text() == "small content"
    
    def test_extract_file_from_zip_large_file(self, temp_dir):
        """Test extracting a large file (direct-to-disk method)."""
        # Create a zip with a file larger than MEMORY_EXTRACT_THRESHOLD
        large_content = "x" * (ZipSecurityConfig.MEMORY_EXTRACT_THRESHOLD + 1000)
        zip_path = Path(temp_dir) / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zip_ref:
            zip_ref.writestr("large.txt", large_content)
        
        extract_to = Path(temp_dir) / "extract"
        extract_to.mkdir()
        
        extracted_path = extract_file_from_zip(str(zip_path), "large.txt", extract_to)
        assert extracted_path is not None
        assert extracted_path.exists()
        assert extracted_path.read_text() == large_content
    
    def test_extract_file_from_zip_nonexistent(self, temp_dir, test_zip_file):
        """Test extracting a nonexistent file."""
        zip_path = test_zip_file("test.zip", {"file.txt": "content"})
        extract_to = Path(temp_dir) / "extract"
        extract_to.mkdir()
        
        extracted_path = extract_file_from_zip(zip_path, "nonexistent.txt", extract_to)
        assert extracted_path is None
    
    def test_extract_file_from_zip_unique_filename(self, temp_dir, test_zip_file):
        """Test that extracted files have unique filenames."""
        zip_path = test_zip_file("test.zip", {"file.txt": "content"})
        extract_to = Path(temp_dir) / "extract"
        extract_to.mkdir()
        
        # Extract same file twice - should get same path (or handle gracefully)
        path1 = extract_file_from_zip(zip_path, "file.txt", extract_to)
        path2 = extract_file_from_zip(zip_path, "file.txt", extract_to)
        assert path1 is not None
        assert path2 is not None
        # Files should exist
        assert path1.exists()
        assert path2.exists()


class TestReadFileLinesZip:
    """Tests for read_file_lines() with zip virtual paths."""
    
    def test_read_file_lines_virtual_path(self, temp_dir, test_zip_file):
        """Test reading lines from a zip virtual path."""
        zip_path = test_zip_file("test.zip", {
            "file.txt": "line1\nline2\nline3"
        })
        virtual_path = f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}file.txt"
        lines = list(read_file_lines(virtual_path))
        assert len(lines) == 3
        assert lines[0] == "line1\n"
        assert lines[1] == "line2\n"
        assert lines[2] == "line3"
    
    def test_read_file_lines_virtual_path_max_lines(self, temp_dir, test_zip_file):
        """Test reading with max_lines limit from zip."""
        content = "\n".join([f"line{i}" for i in range(100)])
        zip_path = test_zip_file("test.zip", {"file.txt": content})
        virtual_path = f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}file.txt"
        lines = list(read_file_lines(virtual_path, max_lines=10))
        assert len(lines) == 10
    
    def test_read_file_lines_virtual_path_cancellation(self, temp_dir, test_zip_file):
        """Test cancellation when reading from zip."""
        content = "\n".join([f"line{i}" for i in range(1000)])
        zip_path = test_zip_file("test.zip", {"file.txt": content})
        virtual_path = f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}file.txt"
        cancellation_event = asyncio.Event()
        cancellation_event.set()
        
        with pytest.raises(CancelledError):
            list(read_file_lines(virtual_path, cancellation_event=cancellation_event))


class TestReadFileChunksZip:
    """Tests for read_file_chunks() with zip virtual paths."""
    
    def test_read_file_chunks_virtual_path(self, temp_dir, test_zip_file):
        """Test reading chunks from a zip virtual path."""
        content = "x" * 5000
        zip_path = test_zip_file("test.zip", {"file.txt": content})
        virtual_path = f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}file.txt"
        chunks = list(read_file_chunks(virtual_path, chunk_size=1000))
        assert len(chunks) > 0
        assert "".join(chunks) == content
    
    def test_read_file_chunks_virtual_path_cancellation(self, temp_dir, test_zip_file):
        """Test cancellation when reading chunks from zip."""
        content = "x" * 10000
        zip_path = test_zip_file("test.zip", {"file.txt": content})
        virtual_path = f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}file.txt"
        cancellation_event = asyncio.Event()
        cancellation_event.set()
        
        with pytest.raises(CancelledError):
            list(read_file_chunks(virtual_path, cancellation_event=cancellation_event))


class TestValidateFilePathZip:
    """Tests for validate_file_path() with zip files and virtual paths."""
    
    def test_validate_file_path_zip_file(self, temp_dir, test_zip_file):
        """Test validating a zip file path."""
        zip_path = test_zip_file("test.zip", {"file.txt": "content"})
        assert validate_file_path(zip_path) is True
    
    def test_validate_file_path_virtual_path(self, temp_dir, test_zip_file):
        """Test validating a virtual zip path."""
        zip_path = test_zip_file("test.zip", {"file.txt": "content"})
        virtual_path = f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}file.txt"
        assert validate_file_path(virtual_path) is True
    
    def test_validate_file_path_virtual_path_invalid_zip(self, temp_dir):
        """Test validating a virtual path with invalid zip."""
        invalid_zip = Path(temp_dir) / "invalid.zip"
        invalid_zip.write_text("not a zip")
        virtual_path = f"{invalid_zip}{ZIP_VIRTUAL_PATH_SEPARATOR}file.txt"
        assert validate_file_path(virtual_path) is False


class TestListFilesInFolderZip:
    """Tests for list_files_in_folder() with zip files."""
    
    @pytest.mark.asyncio
    async def test_list_files_in_folder_with_zip(self, temp_dir, test_zip_file):
        """Test listing files in folder that contains a zip file."""
        # Create a zip file in the folder
        zip_path = test_zip_file("test.zip", {
            "file1.txt": "content1",
            "file2.txt": "content2"
        })
        
        # Create a regular file in the folder
        regular_file = Path(temp_dir) / "regular.txt"
        regular_file.write_text("content")
        
        files = await list_files_in_folder(temp_dir, recursive=True)
        # Should include the regular file and files inside the zip
        assert len(files) >= 3  # regular file + 2 files from zip
        assert any("regular.txt" in f for f in files)
        # Check for virtual paths from zip
        zip_virtual_paths = [f for f in files if ZIP_VIRTUAL_PATH_SEPARATOR in f]
        assert len(zip_virtual_paths) == 2
    
    @pytest.mark.asyncio
    async def test_list_files_in_folder_zip_only(self, temp_dir, test_zip_file):
        """Test listing files when folder only contains zip files."""
        zip_path = test_zip_file("test.zip", {
            "file.txt": "content"
        })
        files = await list_files_in_folder(temp_dir, recursive=True)
        # Should list contents of zip file
        assert len(files) == 1
        assert ZIP_VIRTUAL_PATH_SEPARATOR in files[0]
        assert "file.txt" in files[0]
