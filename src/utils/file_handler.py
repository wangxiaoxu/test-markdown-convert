"""
File handling utilities for document conversion.

This module provides utilities for managing file uploads and temporary files
during the conversion process.
"""

import logging
import os
import shutil
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, BinaryIO

from fastapi import UploadFile

logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file operations for the conversion service.
    
    This class manages:
    - Saving uploaded files to temporary storage
    - Generating unique file names
    - Cleaning up temporary files
    - Providing context managers for automatic cleanup
    
    Attributes:
        temp_dir: Base directory for temporary files.
        allowed_extensions: Set of allowed file extensions.
        max_file_size: Maximum allowed file size in bytes.
    """
    
    ALLOWED_EXTENSIONS = {".md", ".markdown", ".txt"}
    DEFAULT_TEMP_DIR = "/tmp/converter"
    
    def __init__(
        self,
        temp_dir: str | Path | None = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
    ):
        """Initialize the file handler.
        
        Args:
            temp_dir: Directory for temporary files. Defaults to /tmp/converter.
            max_file_size: Maximum allowed file size in bytes (default: 10MB).
        """
        self.temp_dir = Path(temp_dir or self.DEFAULT_TEMP_DIR)
        self.max_file_size = max_file_size
        self._ensure_temp_dir()
    
    def _ensure_temp_dir(self) -> None:
        """Ensure the temporary directory exists and is writable."""
        try:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create temp directory: {e}")
            # Fall back to system temp dir
            self.temp_dir = Path(tempfile.gettempdir()) / "converter"
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        if not os.access(self.temp_dir, os.W_OK):
            raise RuntimeError(f"Temp directory is not writable: {self.temp_dir}")
    
    def is_temp_dir_writable(self) -> bool:
        """Check if the temporary directory is writable.
        
        Returns:
            True if the directory is writable.
        """
        return os.access(self.temp_dir, os.W_OK)
    
    def _generate_unique_name(self, extension: str = "") -> str:
        """Generate a unique file name.
        
        Args:
            extension: File extension to append.
        
        Returns:
            Unique file name string.
        """
        unique_id = uuid.uuid4().hex[:12]
        return f"{unique_id}{extension}"
    
    def get_file_extension(self, filename: str) -> str:
        """Extract the file extension from a filename.
        
        Args:
            filename: The filename to extract extension from.
        
        Returns:
            Lowercase file extension including the dot.
        """
        return Path(filename).suffix.lower()
    
    def is_allowed_extension(self, filename: str) -> bool:
        """Check if a file has an allowed extension.
        
        Args:
            filename: The filename to check.
        
        Returns:
            True if the extension is allowed.
        """
        ext = self.get_file_extension(filename)
        return ext in self.ALLOWED_EXTENSIONS
    
    async def save_upload(self, upload_file: UploadFile) -> Path:
        """Save an uploaded file to the temporary directory.
        
        Args:
            upload_file: The FastAPI UploadFile object.
        
        Returns:
            Path to the saved file.
        
        Raises:
            ValueError: If the file name is empty.
        """
        if not upload_file.filename:
            raise ValueError("File name is required")
        
        # Get the original extension
        original_ext = self.get_file_extension(upload_file.filename)
        if not original_ext:
            original_ext = ".md"  # Default to markdown
        
        # Generate unique file path
        unique_name = self._generate_unique_name(original_ext)
        file_path = self.temp_dir / unique_name
        
        # Save the file
        try:
            content = await upload_file.read()
            file_path.write_bytes(content)
            logger.debug(f"Saved upload to: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to save upload: {e}")
            raise
    
    def save_bytes(self, content: bytes, extension: str = ".md") -> Path:
        """Save raw bytes to a temporary file.
        
        Args:
            content: The file content as bytes.
            extension: File extension to use.
        
        Returns:
            Path to the saved file.
        """
        unique_name = self._generate_unique_name(extension)
        file_path = self.temp_dir / unique_name
        file_path.write_bytes(content)
        logger.debug(f"Saved bytes to: {file_path}")
        return file_path
    
    def generate_output_path(self, extension: str) -> Path:
        """Generate a unique path for an output file.
        
        Args:
            extension: File extension for the output (including dot).
        
        Returns:
            Path for the output file.
        """
        if not extension.startswith("."):
            extension = f".{extension}"
        unique_name = self._generate_unique_name(extension)
        return self.temp_dir / unique_name
    
    def cleanup(self, *paths: str | Path) -> None:
        """Clean up specified files.
        
        Args:
            *paths: File paths to delete.
        """
        for path in paths:
            try:
                path = Path(path)
                if path.exists():
                    path.unlink()
                    logger.debug(f"Cleaned up: {path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {path}: {e}")
    
    def cleanup_old_files(self, max_age_seconds: int = 3600) -> int:
        """Clean up old temporary files.
        
        Args:
            max_age_seconds: Maximum age of files to keep (default: 1 hour).
        
        Returns:
            Number of files deleted.
        """
        import time
        
        deleted_count = 0
        current_time = time.time()
        
        try:
            for path in self.temp_dir.iterdir():
                if path.is_file():
                    file_age = current_time - path.stat().st_mtime
                    if file_age > max_age_seconds:
                        path.unlink()
                        deleted_count += 1
                        logger.debug(f"Cleaned up old file: {path}")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
        
        return deleted_count
    
    @contextmanager
    def managed_file(self, upload_file: UploadFile) -> Generator[tuple[Path, Path], None, None]:
        """Context manager for handling file conversion with automatic cleanup.
        
        This async context manager:
        1. Saves the uploaded file
        2. Creates a path for the output file
        3. Yields both paths for use
        4. Cleans up both files when done
        
        Args:
            upload_file: The FastAPI UploadFile object.
        
        Yields:
            Tuple of (input_path, output_path).
        """
        # Note: This is a sync version. For async, use async context manager separately.
        raise NotImplementedError("Use managed_files_async for async operations")
    
    @contextmanager
    def managed_paths(self, output_format: str) -> Generator[tuple[Path, Path], None, None]:
        """Context manager for managed input/output paths with cleanup.
        
        Args:
            output_format: The output format extension (e.g., 'pdf', 'docx').
        
        Yields:
            Tuple of (input_path, output_path) - input path is placeholder.
        """
        input_path = self.temp_dir / self._generate_unique_name(".md")
        output_path = self.generate_output_path(output_format)
        
        try:
            yield input_path, output_path
        finally:
            self.cleanup(input_path, output_path)


class AsyncFileHandler(FileHandler):
    """Async version of FileHandler with async context manager support."""
    
    async def managed_files_async(
        self,
        upload_file: UploadFile,
        output_format: str,
    ) -> tuple[Path, Path]:
        """Async method to create managed file paths.
        
        Args:
            upload_file: The FastAPI UploadFile object.
            output_format: The target output format.
        
        Returns:
            Tuple of (input_path, output_path).
        """
        input_path = await self.save_upload(upload_file)
        output_path = self.generate_output_path(output_format)
        return input_path, output_path
