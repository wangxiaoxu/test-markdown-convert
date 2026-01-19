"""
Request validation utilities for the API.

This module provides validation functions for file uploads and
conversion parameters.
"""

from pathlib import Path
from fastapi import UploadFile

from src.config import settings
from src.converters.exceptions import (
    InvalidFileTypeError,
    FileTooLargeError,
    EmptyFileError,
    UnsupportedFormatError,
)
from src.converters.pandoc import PandocConverter


ALLOWED_EXTENSIONS = {".md", ".markdown", ".txt"}
SUPPORTED_OUTPUT_FORMATS = {"pdf", "docx"}


def validate_file_type(filename: str) -> None:
    """Validate that the file has an allowed extension.
    
    Args:
        filename: The name of the uploaded file.
    
    Raises:
        InvalidFileTypeError: If the file type is not allowed.
    """
    if not filename:
        raise InvalidFileTypeError("", list(ALLOWED_EXTENSIONS))
    
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileTypeError(filename, list(ALLOWED_EXTENSIONS))


def validate_file_size(size: int) -> None:
    """Validate that the file size is within limits.
    
    Args:
        size: Size of the file in bytes.
    
    Raises:
        FileTooLargeError: If the file exceeds the size limit.
    """
    if size > settings.MAX_FILE_SIZE:
        raise FileTooLargeError(size, settings.MAX_FILE_SIZE)


def validate_file_not_empty(size: int, filename: str) -> None:
    """Validate that the file is not empty.
    
    Args:
        size: Size of the file in bytes.
        filename: Name of the file for error message.
    
    Raises:
        EmptyFileError: If the file is empty.
    """
    if size == 0:
        raise EmptyFileError(filename)


def validate_output_format(format: str) -> str:
    """Validate and normalize the output format.
    
    Args:
        format: The requested output format.
    
    Returns:
        Normalized format string (lowercase).
    
    Raises:
        UnsupportedFormatError: If the format is not supported.
    """
    normalized = format.lower().strip()
    if normalized not in SUPPORTED_OUTPUT_FORMATS:
        raise UnsupportedFormatError(format, list(SUPPORTED_OUTPUT_FORMATS))
    return normalized


async def validate_upload_file(file: UploadFile) -> bytes:
    """Validate an uploaded file completely.
    
    This function performs all validation checks:
    - File type validation
    - File size validation
    - Empty file check
    
    Args:
        file: The FastAPI UploadFile object.
    
    Returns:
        The file content as bytes.
    
    Raises:
        InvalidFileTypeError: If the file type is not allowed.
        FileTooLargeError: If the file exceeds the size limit.
        EmptyFileError: If the file is empty.
    """
    # Validate file type
    validate_file_type(file.filename or "")
    
    # Read file content
    content = await file.read()
    
    # Validate size
    validate_file_size(len(content))
    
    # Validate not empty
    validate_file_not_empty(len(content), file.filename or "unknown")
    
    # Reset file position for potential re-read
    await file.seek(0)
    
    return content
