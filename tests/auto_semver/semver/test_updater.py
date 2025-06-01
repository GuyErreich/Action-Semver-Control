"""
Unit tests for VersionFileUpdater class.

This module provides comprehensive unit tests for the VersionFileUpdater class,
including initialization, file updating, error handling, and edge cases.
"""

import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from auto_semver.semver.updater import VersionFileUpdater
from auto_semver.semver.version import Version


class TestVersionFileUpdaterInit:

    """Test cases for VersionFileUpdater initialization."""

    @pytest.mark.unit
    def test_init_basic(self):
        """Test basic initialization with file path and version."""
        version = Version(major=1, minor=2, patch=3)
        updater = VersionFileUpdater(file_path="test.txt", version=version)
        
        assert updater.file_path == "test.txt"
        assert updater.new_version == version
        assert updater.new_version.major == 1
        assert updater.new_version.minor == 2
        assert updater.new_version.patch == 3

    @pytest.mark.unit
    def test_init_with_complex_version(self):
        """Test initialization with complex version."""
        version = Version(major=2, minor=0, patch=0, suffix="-beta.1")
        updater = VersionFileUpdater(file_path="/path/to/file.py", version=version)
        
        assert updater.file_path == "/path/to/file.py"
        assert updater.new_version == version
        assert updater.new_version.suffix == "-beta.1"

    @pytest.mark.unit
    def test_init_requires_keyword_args(self):
        """Test that initialization requires keyword arguments."""
        version = Version(major=1, minor=0, patch=0)
        
        # Should work with keyword args
        updater = VersionFileUpdater(file_path="test.txt", version=version)
        assert updater.file_path == "test.txt"


class TestVersionFileUpdaterUpdate:

    """Test cases for VersionFileUpdater.update() method."""

    @pytest.mark.unit
    def test_update_single_version_line(self):
        """Test updating a file with a single version line."""
        file_content = "version = '1.0.0'\n"
        expected_content = "version = '2.0.0'\n"
        new_version = Version(major=2, minor=0, patch=0)
        
        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            updater = VersionFileUpdater(file_path="test.py", version=new_version)
            updater.update()
            
            # Verify the file was opened correctly
            mock_file.assert_called_once_with("test.py", "r+", encoding="utf-8")
            
            # Verify the content was written
            handle = mock_file()
            handle.writelines.assert_called_once_with([expected_content])
            handle.seek.assert_called_once_with(0)
            handle.truncate.assert_called_once()

    @pytest.mark.unit
    def test_update_multiple_version_lines(self):
        """Test updating a file with multiple version lines."""
        file_content = (
            "# Version: 1.0.0\n"
            "version = '1.0.0'\n"
            "regular line\n"
        )
        expected_lines = [
            "# Version: 2.5.0\n",
            "version = '2.5.0'\n",
            "regular line\n"
        ]
        new_version = Version(major=2, minor=5, patch=0)
        
        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            updater = VersionFileUpdater(file_path="test.js", version=new_version)
            updater.update()
            
            handle = mock_file()
            handle.writelines.assert_called_once_with(expected_lines)

    @pytest.mark.unit
    def test_update_preserves_non_version_lines(self):
        """Test that non-version lines are preserved unchanged."""
        file_content = (
            "# This is a comment\n"
            "import os\n"
            "version = '1.0.0'\n"
            "def function():\n"
            "    pass\n"
        )
        expected_lines = [
            "# This is a comment\n",
            "import os\n",
            "version = '3.0.0'\n",
            "def function():\n",
            "    pass\n"
        ]
        new_version = Version(major=3, minor=0, patch=0)
        
        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            updater = VersionFileUpdater(file_path="module.py", version=new_version)
            updater.update()
            
            handle = mock_file()
            handle.writelines.assert_called_once_with(expected_lines)

    @pytest.mark.unit
    def test_update_with_merge_behavior(self):
        """Test updating with version merging behavior."""
        file_content = "version = '1.0.0-alpha'\n"
        new_version = Version(major=2, minor=0, patch=0)
        
        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            with patch.object(Version, 'parse') as mock_parse:
                # Mock the parsed version
                current_version = Mock()
                current_version.format_full_line.return_value = "version = '2.0.0'"
                mock_parse.return_value = current_version
                
                updater = VersionFileUpdater(file_path="test.py", version=new_version)
                updater.update()
                
                # Verify merge_from was called
                current_version.merge_from.assert_called_once_with(new_version)
                current_version.format_full_line.assert_called_once()

    @pytest.mark.integration
    def test_update_real_file(self):
        """Test updating a real temporary file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as tmp_file:
            tmp_file.write("version = '1.0.0'\n")
            tmp_file.write("# Some comment\n")
            tmp_file.write("__version__ = \"1.0.0\"\n")
            tmp_path = tmp_file.name
        
        try:
            new_version = Version(major=2, minor=1, patch=0)
            updater = VersionFileUpdater(file_path=tmp_path, version=new_version)
            updater.update()
            
            # Read the updated file
            with open(tmp_path, encoding='utf-8') as f:
                content = f.read()
            
            assert "version = '2.1.0'" in content
            assert "__version__ = \"2.1.0\"" in content
            assert "# Some comment" in content
            
        finally:
            Path(tmp_path).unlink()


class TestVersionFileUpdaterErrorHandling:

    """Test cases for VersionFileUpdater error handling."""

    @pytest.mark.unit
    def test_update_file_not_found(self):
        """Test handling when file doesn't exist."""
        new_version = Version(major=1, minor=0, patch=0)
        updater = VersionFileUpdater(file_path="nonexistent.txt", version=new_version)
        
        with patch("auto_semver.semver.updater.logger") as mock_logger:
            # Should not raise exception, just log warning
            updater.update()
            mock_logger.warning.assert_called_once()
            assert "File not found" in str(mock_logger.warning.call_args)

    @pytest.mark.unit
    def test_update_permission_error(self):
        """Test handling permission errors."""
        new_version = Version(major=1, minor=0, patch=0)
        updater = VersionFileUpdater(file_path="test.py", version=new_version)
        
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with patch("auto_semver.semver.updater.logger") as mock_logger:
                with pytest.raises(PermissionError):
                    updater.update()
                
                mock_logger.error.assert_called_once()
                assert "Failed to update version" in str(mock_logger.error.call_args)

    @pytest.mark.unit 
    def test_update_parse_error_handling(self):
        """Test handling when Version.parse raises ValueError."""
        file_content = (
            "version = '1.0.0'\n"
            "invalid version line\n"
            "another = '2.0.0'\n"
        )
        new_version = Version(major=3, minor=0, patch=0)
        
        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            with patch.object(Version, 'parse') as mock_parse:
                # First call succeeds, second raises ValueError, third succeeds
                mock_parse.side_effect = [
                    Mock(merge_from=Mock(), format_full_line=Mock(return_value="version = '3.0.0'")),
                    ValueError("Invalid version"),
                    Mock(merge_from=Mock(), format_full_line=Mock(return_value="another = '3.0.0'"))
                ]
                
                updater = VersionFileUpdater(file_path="test.py", version=new_version)
                updater.update()
                
                # Should have called parse for each line
                expected_calls = len(file_content.strip().split('\n'))
                assert mock_parse.call_count == expected_calls
                
                # Should have written all lines, including the invalid one unchanged
                handle = mock_file()
                written_lines = handle.writelines.call_args[0][0]
                assert len(written_lines) == expected_calls
                assert "invalid version line\n" in written_lines

    @pytest.mark.unit
    def test_update_io_error_during_write(self):
        """Test handling I/O errors during write operations."""
        file_content = "version = '1.0.0'\n"
        new_version = Version(major=2, minor=0, patch=0)
        
        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            # Make writelines raise an exception
            handle = mock_file()
            handle.writelines.side_effect = OSError("Disk full")
            
            with patch("auto_semver.semver.updater.logger") as mock_logger:
                updater = VersionFileUpdater(file_path="test.py", version=new_version)
                
                with pytest.raises(OSError):
                    updater.update()
                
                mock_logger.error.assert_called_once()


class TestVersionFileUpdaterLogging:

    """Test cases for VersionFileUpdater logging behavior."""

    @pytest.mark.unit
    def test_successful_update_logging(self):
        """Test that successful updates are logged."""
        file_content = "version = '1.0.0'\n"
        new_version = Version(major=2, minor=0, patch=0)
        
        with patch("builtins.open", mock_open(read_data=file_content)):
            with patch("auto_semver.semver.updater.logger") as mock_logger:
                updater = VersionFileUpdater(file_path="test.py", version=new_version)
                updater.update()
                
                # Should log successful update
                mock_logger.info.assert_called_once()
                info_call = mock_logger.info.call_args[0]
                assert "Updated version in test.py to 2.0.0" in info_call[0] % info_call[1:]

    @pytest.mark.unit
    def test_line_update_debug_logging(self):
        """Test that individual line updates are logged at debug level."""
        file_content = "version = '1.0.0'\n"
        new_version = Version(major=2, minor=0, patch=0)
        
        with patch("builtins.open", mock_open(read_data=file_content)):
            with patch("auto_semver.semver.updater.logger") as mock_logger:
                updater = VersionFileUpdater(file_path="test.py", version=new_version)
                updater.update()
                
                # Should log debug message for line update
                mock_logger.debug.assert_called_once()
                debug_call = mock_logger.debug.call_args[0]
                assert "Updated:" in debug_call[0]

    @pytest.mark.unit
    def test_logger_configuration(self):
        """Test that logger is properly configured."""
        from auto_semver.semver import updater
        
        assert updater.logger.name == "auto_semver.semver"
        assert isinstance(updater.logger, logging.Logger)


class TestVersionFileUpdaterEdgeCases:

    """Test cases for edge cases and boundary conditions."""

    @pytest.mark.edge_case
    def test_update_empty_file(self):
        """Test updating an empty file."""
        file_content = ""
        new_version = Version(major=1, minor=0, patch=0)
        
        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            updater = VersionFileUpdater(file_path="empty.txt", version=new_version)
            updater.update()
            
            handle = mock_file()
            handle.writelines.assert_called_once_with([])

    @pytest.mark.edge_case
    def test_update_file_with_only_whitespace(self):
        """Test updating file with only whitespace."""
        file_content = "\n\n   \n\t\n"
        new_version = Version(major=1, minor=0, patch=0)
        
        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            updater = VersionFileUpdater(file_path="whitespace.txt", version=new_version)
            updater.update()
            
            handle = mock_file()
            written_lines = handle.writelines.call_args[0][0]
            expected_line_count = 4  # All whitespace lines preserved
            assert len(written_lines) == expected_line_count
            assert all(line.strip() == "" or line.isspace() for line in written_lines)

    @pytest.mark.edge_case
    def test_update_very_long_file(self):
        """Test updating a file with many lines."""
        max_lines = 1000
        version_line_index = 500
        lines = [f"# Comment line {i}\n" for i in range(max_lines)]
        lines[version_line_index] = "version = '1.0.0'\n"  # Insert version line in middle
        file_content = "".join(lines)
        new_version = Version(major=2, minor=0, patch=0)
        
        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            updater = VersionFileUpdater(file_path="large.py", version=new_version)
            updater.update()
            
            handle = mock_file()
            written_lines = handle.writelines.call_args[0][0]
            assert len(written_lines) == max_lines
            assert written_lines[version_line_index] == "version = '2.0.0'\n"

    @pytest.mark.edge_case
    def test_update_binary_like_file(self):
        """Test updating file with binary-like content."""
        file_content = (
            "version = '1.0.0'\n"
            "\x00\x01\x02\n"  # Binary data
            "more text\n"
        )
        new_version = Version(major=2, minor=0, patch=0)
        
        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            updater = VersionFileUpdater(file_path="mixed.txt", version=new_version)
            updater.update()
            
            handle = mock_file()
            written_lines = handle.writelines.call_args[0][0]
            assert written_lines[0] == "version = '2.0.0'\n"
            assert written_lines[1] == "\x00\x01\x02\n"  # Binary preserved

    @pytest.mark.edge_case
    def test_update_with_unicode_content(self):
        """Test updating file with Unicode content."""
        file_content = (
            "# 版本: version = '1.0.0'\n"
            "# Versión: 1.0.0\n"
            "version = '1.0.0'  # 🚀\n"
        )
        new_version = Version(major=2, minor=0, patch=0)
        
        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            updater = VersionFileUpdater(file_path="unicode.py", version=new_version)
            updater.update()
            
            handle = mock_file()
            written_lines = handle.writelines.call_args[0][0]
            assert "version = '2.0.0'" in written_lines[2]
            assert "🚀" in written_lines[2]


class TestVersionFileUpdaterIntegration:

    """Integration test cases for VersionFileUpdater."""

    @pytest.mark.integration
    def test_update_multiple_file_types(self):
        """Test updating different types of files."""
        test_files = {
            "package.json": '{\n  "version": "1.0.0"\n}\n',
            "setup.py": "version='1.0.0'\n",
            "Cargo.toml": '[package]\nversion = "1.0.0"\n',
            "README.md": "# Project v1.0.0\n"
        }
        
        new_version = Version(major=2, minor=1, patch=0)
        
        for filename, content in test_files.items():
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=filename) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                updater = VersionFileUpdater(file_path=tmp_path, version=new_version)
                updater.update()
                
                with open(tmp_path, encoding='utf-8') as f:
                    updated_content = f.read()
                
                # Should contain the new version
                assert "2.1.0" in updated_content
                
            finally:
                Path(tmp_path).unlink()

    @pytest.mark.integration
    def test_concurrent_updates(self):
        """Test that concurrent updates work correctly."""
        import threading
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as tmp_file:
            tmp_file.write("version = '1.0.0'\n")
            tmp_path = tmp_file.name
        
        try:
            results = []
            
            def update_version(version_str):
                parts = version_str.split('.')
                version = Version(major=int(parts[0]), minor=int(parts[1]), patch=int(parts[2]))
                updater = VersionFileUpdater(file_path=tmp_path, version=version)
                try:
                    updater.update()
                    results.append(version_str)
                except Exception as e:
                    results.append(f"Error: {e}")
            
            # Start multiple threads updating to different versions
            threads = []
            for version_str in ["2.0.0", "2.1.0", "2.2.0"]:
                thread = threading.Thread(target=update_version, args=(version_str,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # At least one should succeed
            success_count = sum(1 for r in results if not r.startswith("Error"))
            assert success_count >= 1
            
        finally:
            Path(tmp_path).unlink()