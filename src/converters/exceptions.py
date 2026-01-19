"""
Custom exceptions for the document conversion process.

These exceptions provide specific error types for different failure scenarios,
enabling proper error handling and appropriate HTTP status codes.
"""


class ConversionError(Exception):
    """Base exception for conversion-related errors.
    
    This is the base class for all conversion exceptions.
    It should be used when the specific error type is unknown.
    """
    
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class UnsupportedFormatError(ConversionError):
    """Raised when the requested output format is not supported.
    
    Supported formats are: pdf, docx
    """
    
    def __init__(self, format: str, supported_formats: list[str] | None = None):
        supported = supported_formats or ["pdf", "docx"]
        message = f"Unsupported output format: '{format}'. Supported formats: {', '.join(supported)}"
        super().__init__(message, {"format": format, "supported_formats": supported})
        self.format = format
        self.supported_formats = supported


class FileAccessError(ConversionError):
    """Raised when there's an error reading or writing files.
    
    This includes:
    - Input file not found
    - Output directory not writable
    - Temporary directory issues
    """
    
    def __init__(self, path: str, operation: str, reason: str = ""):
        message = f"File access error during '{operation}' for path: {path}"
        if reason:
            message += f". Reason: {reason}"
        super().__init__(message, {"path": path, "operation": operation, "reason": reason})
        self.path = path
        self.operation = operation
        self.reason = reason


class PandocExecutionError(ConversionError):
    """Raised when Pandoc command execution fails.
    
    This includes:
    - Pandoc not found
    - Pandoc process exit with non-zero code
    - Pandoc timeout
    """
    
    def __init__(
        self,
        message: str,
        return_code: int | None = None,
        stdout: str = "",
        stderr: str = "",
    ):
        details = {
            "return_code": return_code,
            "stdout": stdout[:1000] if stdout else "",  # Limit output size
            "stderr": stderr[:1000] if stderr else "",
        }
        super().__init__(message, details)
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr


class FileTooLargeError(ConversionError):
    """Raised when the uploaded file exceeds the size limit."""
    
    def __init__(self, size: int, max_size: int):
        message = f"File size ({size} bytes) exceeds maximum allowed ({max_size} bytes)"
        super().__init__(message, {"size": size, "max_size": max_size})
        self.size = size
        self.max_size = max_size


class InvalidFileTypeError(ConversionError):
    """Raised when the uploaded file type is not allowed."""
    
    def __init__(self, filename: str, allowed_types: list[str]):
        message = f"Invalid file type for '{filename}'. Allowed types: {', '.join(allowed_types)}"
        super().__init__(message, {"filename": filename, "allowed_types": allowed_types})
        self.filename = filename
        self.allowed_types = allowed_types


class EmptyFileError(ConversionError):
    """Raised when the uploaded file is empty."""
    
    def __init__(self, filename: str):
        message = f"File '{filename}' is empty"
        super().__init__(message, {"filename": filename})
        self.filename = filename


class TimeoutError(ConversionError):
    """Raised when the conversion process times out."""
    
    def __init__(self, timeout: int):
        message = f"Conversion timed out after {timeout} seconds"
        super().__init__(message, {"timeout": timeout})
        self.timeout = timeout
