"""Unit tests for FileFilter handling of virtual zip paths."""

import pytest
from pathlib import Path
from app.core.filter_base import FileFilter
from app.services.file_handler import ZIP_VIRTUAL_PATH_SEPARATOR


class TestFileFilterZipPaths:
    """Test FileFilter.get_files() with virtual zip paths."""
    
    def test_filefilter_virtual_zip_paths(self, tmp_path):
        """Test that FileFilter correctly handles virtual zip paths."""
        # Create some test files
        test_file1 = tmp_path / "test1.txt"
        test_file1.write_text("content1")
        
        test_file2 = tmp_path / "test2.txt"
        test_file2.write_text("content2")
        
        # Create virtual zip paths (simulating files inside a zip)
        zip_path = str(tmp_path / "archive.zip")
        virtual_path1 = f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}internal/file1.txt"
        virtual_path2 = f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}internal/file2.txt"
        virtual_path3 = f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}subdir/file3.txt"
        
        # Create FileFilter with mix of real and virtual paths
        file_paths = [
            str(test_file1),
            virtual_path1,
            virtual_path2,
            str(test_file2),
            virtual_path3,
        ]
        
        file_filter = FileFilter(file_paths)
        result_files = file_filter.get_files()
        
        # All files should be included
        assert len(result_files) == 5
        assert str(test_file1) in result_files
        assert str(test_file2) in result_files
        assert virtual_path1 in result_files
        assert virtual_path2 in result_files
        assert virtual_path3 in result_files
    
    def test_filefilter_virtual_zip_paths_only(self, tmp_path):
        """Test FileFilter with only virtual zip paths."""
        zip_path = str(tmp_path / "archive.zip")
        virtual_paths = [
            f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}file1.txt",
            f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}file2.txt",
            f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}subdir/file3.txt",
        ]
        
        file_filter = FileFilter(virtual_paths)
        result_files = file_filter.get_files()
        
        # All virtual paths should be included
        assert len(result_files) == 3
        assert virtual_paths[0] in result_files
        assert virtual_paths[1] in result_files
        assert virtual_paths[2] in result_files
    
    def test_filefilter_virtual_zip_paths_with_patterns(self, tmp_path):
        """Test FileFilter with virtual zip paths and file patterns."""
        zip_path = str(tmp_path / "archive.zip")
        virtual_paths = [
            f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}dumpstate-log.txt",
            f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}bugreport-data.txt",
            f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}other-file.txt",
        ]
        
        file_filter = FileFilter(virtual_paths)
        # Apply file patterns that should match some files
        file_filter.filter_files(r"dumpstate-", r"bugreport-")
        result_files = file_filter.get_files()
        
        # Only files matching patterns should be included
        assert len(result_files) == 2
        assert virtual_paths[0] in result_files  # dumpstate-log.txt
        assert virtual_paths[1] in result_files  # bugreport-data.txt
        assert virtual_paths[2] not in result_files  # other-file.txt
    
    def test_filefilter_mixed_paths_with_patterns(self, tmp_path):
        """Test FileFilter with mix of real files and virtual paths, with patterns."""
        # Create real files
        real_file1 = tmp_path / "dumpstate-real.txt"
        real_file1.write_text("content")
        
        real_file2 = tmp_path / "other-real.txt"
        real_file2.write_text("content")
        
        # Create virtual paths
        zip_path = str(tmp_path / "archive.zip")
        virtual_path1 = f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}bugreport-data.txt"
        virtual_path2 = f"{zip_path}{ZIP_VIRTUAL_PATH_SEPARATOR}normal-file.txt"
        
        file_paths = [
            str(real_file1),
            str(real_file2),
            virtual_path1,
            virtual_path2,
        ]
        
        file_filter = FileFilter(file_paths)
        file_filter.filter_files(r"dumpstate-", r"bugreport-")
        result_files = file_filter.get_files()
        
        # Should match: real_file1 (dumpstate-), virtual_path1 (bugreport-)
        assert len(result_files) == 2
        assert str(real_file1) in result_files
        assert virtual_path1 in result_files
        assert str(real_file2) not in result_files
        assert virtual_path2 not in result_files
