"""
Integration tests for the API endpoints.

These tests use FastAPI's TestClient to test the API endpoints.
"""

import pytest
import shutil
from io import BytesIO
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient


# Check if Pandoc is installed for skip conditions
PANDOC_AVAILABLE = shutil.which("pandoc") is not None


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    from src.api.main import app

    return TestClient(app)


@pytest.fixture
def sample_markdown_bytes():
    """Markdown content as bytes for upload."""
    content = """# Test Document

This is a **test** document.

## Features

- Item 1
- Item 2
"""
    return content.encode("utf-8")


@pytest.fixture
def sample_markdown_chinese_bytes():
    """Chinese Markdown content as bytes."""
    content = """# 测试文档

这是一个**测试**文档。

## 功能

- 项目一
- 项目二
"""
    return content.encode("utf-8")


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check_success(self, client):
        """Test health check returns 200 when service is healthy."""
        response = client.get("/health")

        # Should succeed if Pandoc is available
        if PANDOC_AVAILABLE:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "version" in data
            assert "pandoc_version" in data
            assert "uptime" in data
            assert "checks" in data
        else:
            # Without Pandoc, should return 503
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"

    def test_health_check_includes_checks(self, client):
        """Test health check includes individual component checks."""
        response = client.get("/health")
        data = response.json()

        assert "checks" in data
        assert "pandoc" in data["checks"]
        assert "temp_dir" in data["checks"]


class TestRootEndpoint:
    """Tests for the / endpoint."""

    def test_root_returns_info(self, client):
        """Test root endpoint returns service info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data


class TestConvertEndpoint:
    """Tests for the /api/v1/convert endpoint."""

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_to_pdf_success(self, client, sample_markdown_bytes):
        """Test successful PDF conversion."""
        files = {"file": ("test.md", BytesIO(sample_markdown_bytes), "text/markdown")}
        data = {"format": "pdf"}

        response = client.post("/api/v1/convert", files=files, data=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "content-disposition" in response.headers
        assert response.content[:4] == b"%PDF"  # PDF magic bytes

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_to_docx_success(self, client, sample_markdown_bytes):
        """Test successful DOCX conversion."""
        files = {"file": ("test.md", BytesIO(sample_markdown_bytes), "text/markdown")}
        data = {"format": "docx"}

        response = client.post("/api/v1/convert", files=files, data=data)

        assert response.status_code == 200
        assert (
            "word" in response.headers["content-type"].lower()
            or "officedocument" in response.headers["content-type"].lower()
        )
        assert response.content[:4] == b"PK\x03\x04"  # ZIP magic bytes

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_chinese_to_pdf(self, client, sample_markdown_chinese_bytes):
        """Test conversion of Chinese content to PDF."""
        files = {
            "file": (
                "chinese.md",
                BytesIO(sample_markdown_chinese_bytes),
                "text/markdown",
            )
        }
        data = {"format": "pdf"}

        response = client.post("/api/v1/convert", files=files, data=data)

        assert response.status_code == 200
        assert response.content[:4] == b"%PDF"

    def test_convert_invalid_file_type(self, client):
        """Test error for invalid file type."""
        files = {"file": ("test.pdf", BytesIO(b"fake pdf"), "application/pdf")}
        data = {"format": "pdf"}

        response = client.post("/api/v1/convert", files=files, data=data)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INVALID_FILE_TYPE"

    def test_convert_unsupported_format(self, client, sample_markdown_bytes):
        """Test error for unsupported output format."""
        files = {"file": ("test.md", BytesIO(sample_markdown_bytes), "text/markdown")}
        data = {"format": "xyz"}

        response = client.post("/api/v1/convert", files=files, data=data)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "UNSUPPORTED_FORMAT"

    def test_convert_empty_file(self, client):
        """Test error for empty file."""
        files = {"file": ("empty.md", BytesIO(b""), "text/markdown")}
        data = {"format": "pdf"}

        response = client.post("/api/v1/convert", files=files, data=data)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "EMPTY_FILE"

    def test_convert_file_too_large(self, client):
        """Test error for file exceeding size limit."""
        # Create a large file (slightly over 10MB)
        large_content = b"x" * (11 * 1024 * 1024)
        files = {"file": ("large.md", BytesIO(large_content), "text/markdown")}
        data = {"format": "pdf"}

        response = client.post("/api/v1/convert", files=files, data=data)

        assert response.status_code == 413
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "FILE_TOO_LARGE"

    def test_convert_missing_file(self, client):
        """Test error when file is missing."""
        data = {"format": "pdf"}

        response = client.post("/api/v1/convert", data=data)

        assert response.status_code == 422  # Validation error

    def test_convert_default_format_is_pdf(self, client, sample_markdown_bytes):
        """Test that default format is PDF when not specified."""
        files = {"file": ("test.md", BytesIO(sample_markdown_bytes), "text/markdown")}

        if PANDOC_AVAILABLE:
            response = client.post("/api/v1/convert", files=files)
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_with_txt_extension(self, client, sample_markdown_bytes):
        """Test conversion with .txt extension works."""
        files = {"file": ("test.txt", BytesIO(sample_markdown_bytes), "text/plain")}
        data = {"format": "pdf"}

        response = client.post("/api/v1/convert", files=files, data=data)

        assert response.status_code == 200

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_with_markdown_extension(self, client, sample_markdown_bytes):
        """Test conversion with .markdown extension works."""
        files = {
            "file": ("test.markdown", BytesIO(sample_markdown_bytes), "text/markdown")
        }
        data = {"format": "pdf"}

        response = client.post("/api/v1/convert", files=files, data=data)

        assert response.status_code == 200


class TestOpenAPIDocumentation:
    """Tests for OpenAPI documentation availability."""

    def test_swagger_docs_available(self, client):
        """Test Swagger UI is available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_available(self, client):
        """Test ReDoc documentation is available."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_json_available(self, client):
        """Test OpenAPI JSON spec is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "/api/v1/convert" in data["paths"]
        assert "/health" in data["paths"]
        assert "/api/v1/convert-content" in data["paths"]


class TestConvertContentEndpoint:
    """Tests for the /api/v1/convert-content endpoint."""

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_content_to_pdf_success(self, client):
        """Test successful PDF conversion from content string."""
        request_data = {
            "content": "# Test Document\n\nThis is a test.",
            "format": "pdf",
            "filename": "test-doc",
        }

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "content-disposition" in response.headers
        assert "test-doc.pdf" in response.headers["content-disposition"]
        assert response.content[:4] == b"%PDF"

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_content_to_docx_success(self, client):
        """Test successful DOCX conversion from content string."""
        request_data = {
            "content": "# Document Title\n\nSome content.",
            "format": "docx",
        }

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 200
        assert (
            "word" in response.headers["content-type"].lower()
            or "officedocument" in response.headers["content-type"].lower()
        )
        assert response.content[:4] == b"PK\x03\x04"

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_content_with_default_filename(self, client):
        """Test conversion uses default filename when not specified."""
        request_data = {"content": "# Test", "format": "pdf"}

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 200
        assert "document.pdf" in response.headers["content-disposition"]

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_content_chinese_to_pdf(self, client):
        """Test conversion of Chinese content to PDF."""
        request_data = {
            "content": "# 测试文档\n\n这是中文内容。",
            "format": "pdf",
            "filename": "chinese-test",
        }

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 200
        assert response.content[:4] == b"%PDF"

    def test_convert_content_empty_returns_400(self, client):
        """Test error when content is empty string."""
        request_data = {"content": "", "format": "pdf"}

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 422  # Pydantic validation error

    def test_convert_content_whitespace_only_returns_422(self, client):
        """Test error when content is whitespace only."""
        request_data = {"content": "   \n\n   ", "format": "pdf"}

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 422

    def test_convert_content_missing_format_returns_422(self, client):
        """Test error when format field is missing."""
        request_data = {"content": "# Test"}

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 422

    def test_convert_content_unsupported_format_returns_422(self, client):
        """Test error for unsupported output format."""
        request_data = {"content": "# Test", "format": "html"}

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 422  # Pydantic validation error

    def test_convert_content_invalid_filename_returns_422(self, client):
        """Test error for filename with path traversal."""
        request_data = {
            "content": "# Test",
            "format": "pdf",
            "filename": "../etc/passwd",
        }

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 422

    def test_convert_content_invalid_filename_with_slash_returns_422(self, client):
        """Test error for filename with slash."""
        request_data = {"content": "# Test", "format": "pdf", "filename": "subdir/file"}

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 422

    def test_convert_content_missing_content_returns_422(self, client):
        """Test error when content field is missing."""
        request_data = {"format": "pdf"}

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 422

    def test_convert_content_special_characters(self, client):
        """Test conversion with special characters."""
        request_data = {
            "content": "# Test\n\nEmoji: 🎉\nMath: E = mc²",
            "format": "pdf",
        }

        if PANDOC_AVAILABLE:
            response = client.post("/api/v1/convert-content", json=request_data)
            assert response.status_code == 200

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_content_minimal_content(self, client):
        """Test conversion with minimal valid content (1 character)."""
        request_data = {"content": "#", "format": "pdf"}

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 200

    def test_convert_content_large_content_returns_413(self, client):
        """Test error when content exceeds maximum length."""
        # Create content slightly over 10MB
        large_content = "x" * (11 * 1024 * 1024)
        request_data = {"content": large_content, "format": "pdf"}

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 413 or response.status_code == 422

    def test_convert_content_invalid_json_returns_422(self, client):
        """Test error for invalid JSON."""
        response = client.post(
            "/api/v1/convert-content",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_convert_content_markdown_syntax(self, client):
        """Test conversion with various Markdown syntax."""
        content = """
# Heading 1

## Heading 2

**Bold text** and *italic text*

- List item 1
- List item 2
  - Nested item

1. Numbered item
2. Another item

[Link](https://example.com)

`inline code`

```
code block
```
"""
        request_data = {"content": content, "format": "pdf"}

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 200
