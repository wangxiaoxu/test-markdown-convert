"""
Document conversion API routes.

This module provides the REST API endpoint for converting
Markdown documents to PDF and Word formats.
"""

import logging
import re
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator

from src.config import settings
from src.converters.pandoc import PandocConverter
from src.converters.exceptions import (
    ConversionError,
    UnsupportedFormatError,
    PandocExecutionError,
    FileAccessError,
    TimeoutError,
    FileTooLargeError,
    InvalidFileTypeError,
    EmptyFileError,
)
from src.utils.file_handler import FileHandler
from src.api.validators import validate_file_type, validate_output_format

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["conversion"])


# Pydantic models for content-based conversion
class MarkdownContentRequest(BaseModel):
    """Request model for Markdown content conversion.

    Attributes:
        content: Markdown content string to convert.
        format: Target output format (pdf or docx).
        filename: Optional filename for the download (without extension).
    """

    content: str = Field(
        ...,
        min_length=1,
        max_length=10485760,
        description="Markdown content to convert",
        examples=["# Hello World\n\nThis is a test."],
    )
    format: Literal["pdf", "docx"] = Field(
        ..., description="Target output format", examples=["pdf"]
    )
    filename: str = Field(
        default="document",
        pattern="^[a-zA-Z0-9_-]+$",
        description="Filename for download (without extension)",
        examples=["my-document"],
    )

    @field_validator("content")
    @classmethod
    def content_must_not_be_whitespace(cls, v: str) -> str:
        """Validate that content is not just whitespace."""
        if not v.strip():
            raise ValueError("Content cannot be empty or whitespace only")
        return v

    @field_validator("filename")
    @classmethod
    def filename_must_be_safe(cls, v: str) -> str:
        """Validate that filename is safe (no path traversal)."""
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Filename cannot contain path separators or '..'")
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "examples": [
                {
                    "content": "# Hello World\n\nThis is a test.",
                    "format": "pdf",
                    "filename": "my-document",
                },
                {
                    "content": "# 测试文档\n\n这是中文内容。",
                    "format": "docx",
                    "filename": "chinese-doc",
                },
            ]
        }


# Initialize components
file_handler = FileHandler(
    temp_dir=settings.TEMP_DIR,
    max_file_size=settings.MAX_FILE_SIZE,
)


def get_converter() -> PandocConverter:
    """Get a PandocConverter instance.

    Returns:
        Configured PandocConverter.
    """
    return PandocConverter(
        pdf_engine=settings.PDF_ENGINE,
        timeout=settings.PANDOC_TIMEOUT,
    )


def cleanup_files(input_path: Path, output_path: Path) -> None:
    """Background task to cleanup temporary files.

    Args:
        input_path: Path to input file.
        output_path: Path to output file.
    """
    file_handler.cleanup(input_path, output_path)
    logger.debug(f"Cleaned up files: {input_path}, {output_path}")


@router.post(
    "/convert",
    summary="Convert Markdown document",
    description="""
Convert a Markdown document to PDF or Word (DOCX) format.

**Supported input formats:**
- `.md` - Markdown
- `.markdown` - Markdown
- `.txt` - Plain text (treated as Markdown)

**Supported output formats:**
- `pdf` - PDF document (using XeLaTeX for Chinese support)
- `docx` - Microsoft Word document

**File size limit:** 10MB (configurable)
""",
    responses={
        200: {
            "description": "Successfully converted document",
            "content": {
                "application/pdf": {},
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {},
            },
        },
        400: {
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "INVALID_FILE_TYPE",
                            "message": "Only .md, .markdown, and .txt files are allowed",
                            "details": {"filename": "test.pdf"},
                        }
                    }
                }
            },
        },
        413: {
            "description": "File too large",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "FILE_TOO_LARGE",
                            "message": "File size exceeds maximum allowed",
                            "details": {"size": 15000000, "max_size": 10485760},
                        }
                    }
                }
            },
        },
        500: {
            "description": "Conversion error",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "CONVERSION_FAILED",
                            "message": "Pandoc conversion failed",
                            "details": {},
                        }
                    }
                }
            },
        },
        504: {
            "description": "Conversion timeout",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "TIMEOUT",
                            "message": "Conversion timed out after 30 seconds",
                            "details": {"timeout": 30},
                        }
                    }
                }
            },
        },
    },
)
async def convert_document(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(description="Markdown file to convert")],
    format: Annotated[str, Form(description="Target format: pdf or docx")] = "pdf",
):
    """Convert a Markdown document to the specified format.

    Args:
        background_tasks: FastAPI background tasks for cleanup.
        file: The uploaded Markdown file.
        format: Target output format (pdf or docx).

    Returns:
        FileResponse with the converted document.
    """
    input_path = None
    output_path = None

    try:
        # Validate file type
        try:
            validate_file_type(file.filename or "")
        except InvalidFileTypeError as e:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "INVALID_FILE_TYPE",
                        "message": e.message,
                        "details": e.details,
                    }
                },
            )

        # Validate output format
        try:
            format = validate_output_format(format)
        except UnsupportedFormatError as e:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "UNSUPPORTED_FORMAT",
                        "message": e.message,
                        "details": e.details,
                    }
                },
            )

        # Read file content
        content = await file.read()

        # Validate file size
        if len(content) > settings.MAX_FILE_SIZE:
            return JSONResponse(
                status_code=413,
                content={
                    "error": {
                        "code": "FILE_TOO_LARGE",
                        "message": f"File size ({len(content)} bytes) exceeds maximum allowed ({settings.MAX_FILE_SIZE} bytes)",
                        "details": {
                            "size": len(content),
                            "max_size": settings.MAX_FILE_SIZE,
                        },
                    }
                },
            )

        # Validate not empty
        if len(content) == 0:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "EMPTY_FILE",
                        "message": f"File '{file.filename}' is empty",
                        "details": {"filename": file.filename},
                    }
                },
            )

        # Save input file
        input_path = file_handler.save_bytes(
            content, file_handler.get_file_extension(file.filename or ".md")
        )

        # Generate output path
        output_path = file_handler.generate_output_path(format)

        # Get converter and execute
        converter = get_converter()
        converter.convert(input_path, output_path, format)

        # Generate download filename
        original_name = Path(file.filename or "document").stem
        download_filename = f"{original_name}.{format}"

        # Schedule cleanup after response is sent
        background_tasks.add_task(cleanup_files, input_path, output_path)

        # Return the file
        return FileResponse(
            path=str(output_path),
            filename=download_filename,
            media_type=converter.get_content_type(format),
        )

    except TimeoutError as e:
        logger.error(f"Conversion timeout: {e}")
        if input_path:
            file_handler.cleanup(input_path)
        if output_path:
            file_handler.cleanup(output_path)
        return JSONResponse(
            status_code=504,
            content={
                "error": {
                    "code": "TIMEOUT",
                    "message": e.message,
                    "details": e.details,
                }
            },
        )

    except PandocExecutionError as e:
        logger.error(f"Pandoc execution error: {e}")
        if input_path:
            file_handler.cleanup(input_path)
        if output_path:
            file_handler.cleanup(output_path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "PANDOC_ERROR",
                    "message": e.message,
                    "details": e.details,
                }
            },
        )

    except FileAccessError as e:
        logger.error(f"File access error: {e}")
        if input_path:
            file_handler.cleanup(input_path)
        if output_path:
            file_handler.cleanup(output_path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "FILE_ACCESS_ERROR",
                    "message": e.message,
                    "details": e.details,
                }
            },
        )

    except ConversionError as e:
        logger.error(f"Conversion error: {e}")
        if input_path:
            file_handler.cleanup(input_path)
        if output_path:
            file_handler.cleanup(output_path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "CONVERSION_FAILED",
                    "message": e.message,
                    "details": e.details,
                }
            },
        )

    except Exception as e:
        logger.exception(f"Unexpected error during conversion: {e}")
        if input_path:
            file_handler.cleanup(input_path)
        if output_path:
            file_handler.cleanup(output_path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {"error": str(e)},
                }
            },
        )


@router.post(
    "/convert-content",
    summary="Convert Markdown content string",
    description="""
Convert a Markdown content string to PDF or Word (DOCX) format.

This endpoint accepts Markdown content directly as a string in the request body,
eliminating the need for file upload. Useful for dynamically generated content,
database-stored Markdown, or microservice integrations.

**Supported output formats:**
- `pdf` - PDF document (using XeLaTeX for Chinese support)
- `docx` - Microsoft Word document

**Content size limit:** 10MB (configurable)
**Default filename:** "document" (customizable via request parameter)
""",
    responses={
        200: {
            "description": "Successfully converted document",
            "content": {
                "application/pdf": {},
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {},
            },
        },
        400: {
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Content cannot be empty or whitespace only",
                            "details": {},
                        }
                    }
                }
            },
        },
        413: {
            "description": "Content too large",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "CONTENT_TOO_LARGE",
                            "message": "Content length exceeds maximum allowed",
                            "details": {"length": 15000000, "max_length": 10485760},
                        }
                    }
                }
            },
        },
        500: {
            "description": "Conversion error",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "CONVERSION_FAILED",
                            "message": "Pandoc conversion failed",
                            "details": {},
                        }
                    }
                }
            },
        },
        504: {
            "description": "Conversion timeout",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "TIMEOUT",
                            "message": "Conversion timed out after 30 seconds",
                            "details": {"timeout": 30},
                        }
                    }
                }
            },
        },
    },
)
async def convert_markdown_content(
    background_tasks: BackgroundTasks,
    request: MarkdownContentRequest,
):
    """Convert Markdown content string to the specified format.

    Args:
        background_tasks: FastAPI background tasks for cleanup.
        request: Markdown content conversion request.

    Returns:
        FileResponse with the converted document.
    """
    input_path = None
    output_path = None

    try:
        # Encode content to bytes
        content_bytes = request.content.encode("utf-8")

        # Validate content length (already validated by Pydantic, but double-check)
        content_length = len(content_bytes)
        if content_length > settings.MAX_FILE_SIZE:
            return JSONResponse(
                status_code=413,
                content={
                    "error": {
                        "code": "CONTENT_TOO_LARGE",
                        "message": f"Content length ({content_length} bytes) exceeds maximum allowed ({settings.MAX_FILE_SIZE} bytes)",
                        "details": {
                            "length": content_length,
                            "max_length": settings.MAX_FILE_SIZE,
                        },
                    }
                },
            )

        # Save input file from content bytes
        input_path = file_handler.save_bytes(content_bytes, ".md")

        # Generate output path
        output_path = file_handler.generate_output_path(request.format)

        # Get converter and execute
        converter = get_converter()
        converter.convert(input_path, output_path, request.format)

        # Generate download filename
        download_filename = f"{request.filename}.{request.format}"

        # Schedule cleanup after response is sent
        background_tasks.add_task(cleanup_files, input_path, output_path)

        # Return the file
        return FileResponse(
            path=str(output_path),
            filename=download_filename,
            media_type=converter.get_content_type(request.format),
        )

    except TimeoutError as e:
        logger.error(f"Conversion timeout: {e}")
        if input_path:
            file_handler.cleanup(input_path)
        if output_path:
            file_handler.cleanup(output_path)
        return JSONResponse(
            status_code=504,
            content={
                "error": {
                    "code": "TIMEOUT",
                    "message": e.message,
                    "details": e.details,
                }
            },
        )

    except PandocExecutionError as e:
        logger.error(f"Pandoc execution error: {e}")
        if input_path:
            file_handler.cleanup(input_path)
        if output_path:
            file_handler.cleanup(output_path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "PANDOC_ERROR",
                    "message": e.message,
                    "details": e.details,
                }
            },
        )

    except FileAccessError as e:
        logger.error(f"File access error: {e}")
        if input_path:
            file_handler.cleanup(input_path)
        if output_path:
            file_handler.cleanup(output_path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "FILE_ACCESS_ERROR",
                    "message": e.message,
                    "details": e.details,
                }
            },
        )

    except ConversionError as e:
        logger.error(f"Conversion error: {e}")
        if input_path:
            file_handler.cleanup(input_path)
        if output_path:
            file_handler.cleanup(output_path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "CONVERSION_FAILED",
                    "message": e.message,
                    "details": e.details,
                }
            },
        )

    except Exception as e:
        logger.exception(f"Unexpected error during conversion: {e}")
        if input_path:
            file_handler.cleanup(input_path)
        if output_path:
            file_handler.cleanup(output_path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {"error": str(e)},
                }
            },
        )
