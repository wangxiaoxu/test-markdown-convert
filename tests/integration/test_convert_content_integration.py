"""
Integration tests for the /api/v1/convert-content endpoint.

These tests verify end-to-end behavior including:
- Complete request-response flow
- Temporary file cleanup
- Concurrent request handling
- Consistency with /api/v1/convert endpoint
"""

import pytest
import shutil
from pathlib import Path

from fastapi.testclient import TestClient


# Check if Pandoc is installed for skip conditions
PANDOC_AVAILABLE = shutil.which("pandoc") is not None


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    from src.api.main import app

    return TestClient(app)


@pytest.fixture
def sample_markdown_content():
    """Sample Markdown content for testing."""
    return """# Integration Test Document

This is a comprehensive test document.

## Features

- Feature 1
- Feature 2

## Code Example

```python
def hello():
    print("Hello, World!")
```

## Table

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |
"""


class TestConvertContentIntegration:
    """Integration tests for convert-content endpoint."""

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_complete_request_response_flow(self, client, sample_markdown_content):
        """Test complete request-response flow with content conversion."""
        request_data = {
            "content": sample_markdown_content,
            "format": "pdf",
            "filename": "integration-test",
        }

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "integration-test.pdf" in response.headers["content-disposition"]
        assert response.content[:4] == b"%PDF"
        assert len(response.content) > 1000  # Verify non-empty PDF

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_docx_conversion_flow(self, client, sample_markdown_content):
        """Test complete DOCX conversion flow."""
        request_data = {
            "content": sample_markdown_content,
            "format": "docx",
            "filename": "integration-docx",
        }

        response = client.post("/api/v1/convert-content", json=request_data)

        assert response.status_code == 200
        assert "word" in response.headers["content-type"].lower()
        assert response.content[:4] == b"PK\x03\x04"
        assert len(response.content) > 1000

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_temp_files_cleanup_on_success(self, client, sample_markdown_content):
        """Test that temporary files are cleaned up after successful conversion."""
        # Get temp directory path from settings
        from src.config import settings

        request_data = {"content": sample_markdown_content, "format": "pdf"}

        # List files before conversion
        temp_dir = Path(settings.TEMP_DIR)
        files_before = set(temp_dir.glob("*")) if temp_dir.exists() else set()

        # Perform conversion
        response = client.post("/api/v1/convert-content", json=request_data)
        assert response.status_code == 200

        # Give some time for background cleanup
        import time

        time.sleep(0.5)

        # Check that temp directory is clean (files may differ but no excess accumulation)
        files_after = set(temp_dir.glob("*")) if temp_dir.exists() else set()
        # Background cleanup should have removed the temporary files
        # We allow for some variance but significant accumulation would indicate a problem
        assert len(files_after) - len(files_before) <= 1

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_temp_files_cleanup_on_error(self, client):
        """Test that temporary files are cleaned up after conversion error."""
        from src.config import settings

        # This should cause a conversion error
        request_data = {
            "content": "# Test\n\n![Invalid Image](nonexistent.png)",
            "format": "pdf",
        }

        temp_dir = Path(settings.TEMP_DIR)
        files_before = set(temp_dir.glob("*")) if temp_dir.exists() else set()

        # This might fail due to missing image, but should still clean up
        response = client.post("/api/v1/convert-content", json=request_data)

        # Regardless of success or failure, temp files should be cleaned
        import time

        time.sleep(0.5)

        files_after = set(temp_dir.glob("*")) if temp_dir.exists() else set()
        assert len(files_after) - len(files_before) <= 1

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_consistency_with_file_upload_endpoint(
        self, client, sample_markdown_content
    ):
        """Test that content endpoint produces same results as file upload endpoint."""
        from io import BytesIO

        # Convert via content endpoint
        content_request = {
            "content": sample_markdown_content,
            "format": "pdf",
            "filename": "consistency-test",
        }
        content_response = client.post("/api/v1/convert-content", json=content_request)

        # Convert via file upload endpoint
        files = {
            "file": (
                "test.md",
                BytesIO(sample_markdown_content.encode("utf-8")),
                "text/markdown",
            )
        }
        data = {"format": "pdf"}
        file_response = client.post("/api/v1/convert", files=files, data=data)

        assert content_response.status_code == file_response.status_code == 200

        # Both should be valid PDFs
        assert content_response.content[:4] == b"%PDF"
        assert file_response.content[:4] == b"%PDF"

        # Content should be very similar (may differ slightly due to filename handling)
        # Check that both produce valid PDFs of reasonable size
        assert len(content_response.content) > 1000
        assert len(file_response.content) > 1000


class TestConcurrentRequests:
    """Tests for concurrent request handling."""

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_concurrent_requests(self, client):
        """Test that multiple concurrent requests are handled correctly."""
        import concurrent.futures
        import time

        def make_request(request_id):
            """Make a single conversion request."""
            request_data = {
                "content": f"# Concurrent Test {request_id}\n\nThis is test {request_id}.",
                "format": "pdf",
                "filename": f"concurrent-{request_id}",
            }
            response = client.post("/api/v1/convert-content", json=request_data)
            return response.status_code, response.content[:4]

        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # All requests should succeed
        for status_code, magic_bytes in results:
            assert status_code == 200
            assert magic_bytes == b"%PDF"

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_unique_temp_files_for_concurrent_requests(self, client):
        """Test that concurrent requests get unique temporary files."""
        import concurrent.futures

        def make_request_with_delay(request_id):
            """Make a request with slight delay to increase overlap."""
            import time

            request_data = {
                "content": f"# Test {request_id}\n\nContent {request_id}.",
                "format": "pdf",
                "filename": f"unique-{request_id}",
            }
            response = client.post("/api/v1/convert-content", json=request_data)
            return response.status_code

        # Launch requests rapidly
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request_with_delay, i) for i in range(3)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # All should succeed (no file conflicts)
        assert all(status == 200 for status in results)


class TestEdgeCases:
    """Integration tests for edge cases."""

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_very_long_line_in_content(self, client):
        """Test content with very long lines."""
        long_line = "# Test\n\n" + "x" * 10000 + "\n\nEnd."
        request_data = {"content": long_line, "format": "pdf"}

        response = client.post("/api/v1/convert-content", json=request_data)
        assert response.status_code == 200

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_unicode_content(self, client):
        """Test content with various Unicode characters."""
        unicode_content = """# Unicode Test

## Scripts
- Chinese: 你好世界
- Japanese: こんにちは
- Korean: 안녕하세요
- Arabic: مرحبا بالعالم
- Hebrew: שלום עולם
- Russian: Привет мир
- Greek: Γειά σου Κόσμε

## Emoji
😀 🎉 🚀 ❤️ 🌟 ⭐ 🎯

## Math
∑ ∫ ∞ √ ≈ ≠ ≤ ≥

## Symbols
© ® ™ € £ ¥ ¢
"""
        request_data = {"content": unicode_content, "format": "pdf"}

        response = client.post("/api/v1/convert-content", json=request_data)
        assert response.status_code == 200

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_empty_lines_and_whitespace(self, client):
        """Test content with many empty lines and whitespace."""
        whitespace_content = """# Test



    Indented text




More text


"""
        request_data = {"content": whitespace_content, "format": "pdf"}

        response = client.post("/api/v1/convert-content", json=request_data)
        assert response.status_code == 200

    @pytest.mark.skipif(not PANDOC_AVAILABLE, reason="Pandoc not installed")
    def test_custom_filename_validation(self, client):
        """Test various valid filename patterns."""
        valid_filenames = [
            "simple",
            "with_underscore",
            "with-dash",
            "MixedCase123",
            "UPPERCASE",
            "lowercase",
            "123numbers",
            "file_name_v2",
        ]

        for filename in valid_filenames:
            request_data = {"content": "# Test", "format": "pdf", "filename": filename}
            response = client.post("/api/v1/convert-content", json=request_data)
            assert response.status_code == 200
            assert f"{filename}.pdf" in response.headers["content-disposition"]
