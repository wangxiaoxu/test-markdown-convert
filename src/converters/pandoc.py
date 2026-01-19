"""
Pandoc-based document converter.

This module provides a wrapper around the Pandoc command-line tool
for converting Markdown documents to PDF and Word (DOCX) formats.
"""

import logging
import os
import subprocess
import shutil
from pathlib import Path
from typing import Any

from .exceptions import (
    PandocExecutionError,
    UnsupportedFormatError,
    FileAccessError,
    TimeoutError,
)

logger = logging.getLogger(__name__)


class PandocConverter:
    """Wrapper for Pandoc document conversion.
    
    This class encapsulates the Pandoc command-line tool and provides
    a Pythonic interface for converting documents.
    
    Attributes:
        supported_formats: List of supported output formats.
        pdf_engine: LaTeX engine for PDF generation.
        default_timeout: Default timeout for conversion in seconds.
    """
    
    SUPPORTED_FORMATS = ["pdf", "docx"]
    
    # Content type mapping for output formats
    CONTENT_TYPES = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    
    # Default Pandoc options for each format
    FORMAT_OPTIONS: dict[str, dict[str, Any]] = {
        "pdf": {
            "pdf_engine": "xelatex",
            "variables": {
                "geometry": "margin=1in",
                "linestretch": "1.2",
                "CJKmainfont": "Noto Sans CJK SC",
            },
        },
        "docx": {
            "standalone": True,
        },
    }
    
    def __init__(
        self,
        pdf_engine: str = "xelatex",
        timeout: int = 30,
    ):
        """Initialize the Pandoc converter.
        
        Args:
            pdf_engine: LaTeX engine for PDF generation (default: xelatex).
            timeout: Maximum time for conversion in seconds (default: 30).
        """
        self.pdf_engine = pdf_engine
        self.timeout = timeout
        self._verify_pandoc_installation()
    
    def _verify_pandoc_installation(self) -> None:
        """Verify that Pandoc is installed and accessible."""
        if not shutil.which("pandoc"):
            raise PandocExecutionError(
                "Pandoc is not installed or not found in PATH",
                return_code=None,
            )
    
    def get_pandoc_version(self) -> str:
        """Get the installed Pandoc version.
        
        Returns:
            Version string of the installed Pandoc.
        """
        try:
            result = subprocess.run(
                ["pandoc", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # First line contains version info
            first_line = result.stdout.split("\n")[0]
            return first_line.replace("pandoc ", "").strip()
        except Exception as e:
            logger.warning(f"Failed to get Pandoc version: {e}")
            return "unknown"
    
    def convert(
        self,
        input_path: str | Path,
        output_path: str | Path,
        output_format: str,
        options: dict[str, Any] | None = None,
    ) -> bool:
        """Execute document conversion.
        
        Args:
            input_path: Path to the input Markdown file.
            output_path: Path for the output file.
            output_format: Target format ('pdf' or 'docx').
            options: Optional dictionary of additional Pandoc options.
        
        Returns:
            True if conversion was successful.
        
        Raises:
            UnsupportedFormatError: If the output format is not supported.
            FileAccessError: If there's an error accessing files.
            PandocExecutionError: If Pandoc execution fails.
            TimeoutError: If conversion times out.
        """
        # Validate format
        output_format = output_format.lower()
        if output_format not in self.SUPPORTED_FORMATS:
            raise UnsupportedFormatError(output_format, self.SUPPORTED_FORMATS)
        
        # Convert to Path objects
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        # Validate input file
        if not input_path.exists():
            raise FileAccessError(str(input_path), "read", "File does not exist")
        
        if not input_path.is_file():
            raise FileAccessError(str(input_path), "read", "Path is not a file")
        
        # Validate output directory
        output_dir = output_path.parent
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise FileAccessError(str(output_dir), "create", str(e))
        
        if not os.access(output_dir, os.W_OK):
            raise FileAccessError(str(output_dir), "write", "Directory is not writable")
        
        # Build and execute command
        command = self._build_command(input_path, output_path, output_format, options)
        logger.info(f"Executing Pandoc command: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            if result.returncode != 0:
                raise PandocExecutionError(
                    f"Pandoc conversion failed with exit code {result.returncode}",
                    return_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )
            
            # Verify output file was created
            if not output_path.exists():
                raise PandocExecutionError(
                    "Pandoc completed but output file was not created",
                    return_code=0,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )
            
            logger.info(f"Conversion successful: {input_path} -> {output_path}")
            return True
            
        except subprocess.TimeoutExpired:
            raise TimeoutError(self.timeout)
    
    def _build_command(
        self,
        input_path: Path,
        output_path: Path,
        output_format: str,
        options: dict[str, Any] | None = None,
    ) -> list[str]:
        """Build the Pandoc command line arguments.
        
        Args:
            input_path: Path to the input file.
            output_path: Path for the output file.
            output_format: Target format.
            options: Optional additional options.
        
        Returns:
            List of command-line arguments.
        """
        command = ["pandoc", str(input_path), "-o", str(output_path)]
        
        # Get default options for format
        format_options = self.FORMAT_OPTIONS.get(output_format, {}).copy()
        
        # Merge with user options
        if options:
            format_options.update(options)
        
        # Add format-specific options
        if output_format == "pdf":
            pdf_engine = format_options.pop("pdf_engine", self.pdf_engine)
            command.extend(["--pdf-engine", pdf_engine])
            
            # Add variables
            variables = format_options.pop("variables", {})
            for key, value in variables.items():
                command.extend(["-V", f"{key}={value}"])
        
        elif output_format == "docx":
            if format_options.pop("standalone", False):
                command.append("-s")
        
        return command
    
    def get_content_type(self, format: str) -> str:
        """Get the content type for a given format.
        
        Args:
            format: Output format ('pdf' or 'docx').
        
        Returns:
            MIME content type string.
        """
        return self.CONTENT_TYPES.get(format.lower(), "application/octet-stream")
    
    @classmethod
    def is_format_supported(cls, format: str) -> bool:
        """Check if a format is supported.
        
        Args:
            format: Format to check.
        
        Returns:
            True if format is supported.
        """
        return format.lower() in cls.SUPPORTED_FORMATS
