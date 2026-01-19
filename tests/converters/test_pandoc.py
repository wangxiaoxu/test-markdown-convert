"""
Unit tests for the PandocConverter class.

Note: These tests require Pandoc to be installed.
When running in Docker, all tests should pass.
When running locally without Pandoc, some tests will be skipped.
"""

import pytest
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.converters.pandoc import PandocConverter
from src.converters.exceptions import (
    UnsupportedFormatError,
    FileAccessError,
    PandocExecutionError,
    TimeoutError,
)


# Check if Pandoc is installed
PANDOC_AVAILABLE = shutil.which("pandoc") is not None


class TestPandocConverterInit:
    """Tests for PandocConverter initialization."""
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_init_default(self):
        """Test default initialization."""
        converter = PandocConverter()
        assert converter.pdf_engine == "xelatex"
        assert converter.timeout == 30
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_init_custom(self):
        """Test initialization with custom settings."""
        converter = PandocConverter(pdf_engine="pdflatex", timeout=60)
        assert converter.pdf_engine == "pdflatex"
        assert converter.timeout == 60
    
    def test_init_without_pandoc(self):
        """Test initialization raises error when Pandoc is not found."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(PandocExecutionError) as exc_info:
                PandocConverter()
            assert "not installed" in str(exc_info.value).lower()


class TestPandocConverterVersion:
    """Tests for Pandoc version retrieval."""
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_get_version(self):
        """Test getting Pandoc version."""
        converter = PandocConverter()
        version = converter.get_pandoc_version()
        assert version != "unknown"
        # Version should match pattern like "3.1.3" or similar
        assert "." in version or version.isalnum()


class TestPandocConverterValidation:
    """Tests for validation logic."""
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_unsupported_format(self, sample_md_file, temp_dir):
        """Test error for unsupported format."""
        converter = PandocConverter()
        output_path = temp_dir / "output.xyz"
        
        with pytest.raises(UnsupportedFormatError) as exc_info:
            converter.convert(sample_md_file, output_path, "xyz")
        
        assert "xyz" in str(exc_info.value)
        assert "pdf" in str(exc_info.value) or "docx" in str(exc_info.value)
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_nonexistent_input_file(self, temp_dir):
        """Test error for non-existent input file."""
        converter = PandocConverter()
        input_path = temp_dir / "nonexistent.md"
        output_path = temp_dir / "output.pdf"
        
        with pytest.raises(FileAccessError) as exc_info:
            converter.convert(input_path, output_path, "pdf")
        
        assert "does not exist" in str(exc_info.value)
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_input_is_directory(self, temp_dir):
        """Test error when input is a directory instead of file."""
        converter = PandocConverter()
        output_path = temp_dir / "output.pdf"
        
        with pytest.raises(FileAccessError) as exc_info:
            converter.convert(temp_dir, output_path, "pdf")
        
        assert "not a file" in str(exc_info.value)


class TestPandocConverterConversion:
    """Tests for actual conversion functionality."""
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_to_pdf(self, sample_md_file, temp_dir):
        """Test Markdown to PDF conversion."""
        converter = PandocConverter()
        output_path = temp_dir / "output.pdf"
        
        result = converter.convert(sample_md_file, output_path, "pdf")
        
        assert result is True
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        # Verify it's a PDF (starts with %PDF)
        with open(output_path, "rb") as f:
            header = f.read(4)
        assert header == b"%PDF"
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_to_docx(self, sample_md_file, temp_dir):
        """Test Markdown to DOCX conversion."""
        converter = PandocConverter()
        output_path = temp_dir / "output.docx"
        
        result = converter.convert(sample_md_file, output_path, "docx")
        
        assert result is True
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        # Verify it's a ZIP file (DOCX is ZIP-based)
        with open(output_path, "rb") as f:
            header = f.read(4)
        assert header == b"PK\x03\x04"
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_case_insensitive_format(self, sample_md_file, temp_dir):
        """Test that format is case-insensitive."""
        converter = PandocConverter()
        output_path = temp_dir / "output.docx"
        
        result = converter.convert(sample_md_file, output_path, "DOCX")
        
        assert result is True
        assert output_path.exists()
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_creates_output_dir(self, sample_md_file, temp_dir):
        """Test that output directory is created if it doesn't exist."""
        converter = PandocConverter()
        output_path = temp_dir / "subdir" / "nested" / "output.pdf"
        
        result = converter.convert(sample_md_file, output_path, "pdf")
        
        assert result is True
        assert output_path.exists()


class TestPandocConverterChineseContent:
    """Tests for Chinese content support."""
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_chinese_to_pdf(self, sample_md_file_chinese, temp_dir):
        """Test conversion of Chinese Markdown to PDF."""
        converter = PandocConverter()
        output_path = temp_dir / "chinese_output.pdf"
        
        result = converter.convert(sample_md_file_chinese, output_path, "pdf")
        
        assert result is True
        assert output_path.exists()
        assert output_path.stat().st_size > 0
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_chinese_to_docx(self, sample_md_file_chinese, temp_dir):
        """Test conversion of Chinese Markdown to DOCX."""
        converter = PandocConverter()
        output_path = temp_dir / "chinese_output.docx"
        
        result = converter.convert(sample_md_file_chinese, output_path, "docx")
        
        assert result is True
        assert output_path.exists()


class TestPandocConverterCodeBlocks:
    """Tests for code block handling."""
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_with_code_to_pdf(self, sample_md_file_code, temp_dir):
        """Test conversion of Markdown with code blocks to PDF."""
        converter = PandocConverter()
        output_path = temp_dir / "code_output.pdf"
        
        result = converter.convert(sample_md_file_code, output_path, "pdf")
        
        assert result is True
        assert output_path.exists()
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_with_code_to_docx(self, sample_md_file_code, temp_dir):
        """Test conversion of Markdown with code blocks to DOCX."""
        converter = PandocConverter()
        output_path = temp_dir / "code_output.docx"
        
        result = converter.convert(sample_md_file_code, output_path, "docx")
        
        assert result is True
        assert output_path.exists()


class TestPandocConverterTimeout:
    """Tests for timeout handling."""
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_timeout_raised(self, sample_md_file, temp_dir):
        """Test that TimeoutError is raised when conversion exceeds timeout."""
        # Use very short timeout
        converter = PandocConverter(timeout=0.001)
        output_path = temp_dir / "output.pdf"
        
        # This may or may not timeout depending on system speed
        # We mock subprocess to guarantee timeout
        with patch("subprocess.run") as mock_run:
            import subprocess
            mock_run.side_effect = subprocess.TimeoutExpired("pandoc", 0.001)
            
            with pytest.raises(TimeoutError) as exc_info:
                converter.convert(sample_md_file, output_path, "pdf")
            
            assert "timed out" in str(exc_info.value).lower()


class TestPandocConverterHelpers:
    """Tests for helper methods."""
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_get_content_type_pdf(self):
        """Test content type for PDF."""
        converter = PandocConverter()
        assert converter.get_content_type("pdf") == "application/pdf"
    
    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_get_content_type_docx(self):
        """Test content type for DOCX."""
        converter = PandocConverter()
        content_type = converter.get_content_type("docx")
        assert "word" in content_type.lower() or "officedocument" in content_type.lower()
    
    def test_is_format_supported(self):
        """Test format support check."""
        assert PandocConverter.is_format_supported("pdf") is True
        assert PandocConverter.is_format_supported("docx") is True
        assert PandocConverter.is_format_supported("PDF") is True  # Case insensitive
        assert PandocConverter.is_format_supported("xyz") is False
