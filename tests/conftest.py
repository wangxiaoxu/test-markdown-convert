"""
Shared pytest fixtures for all tests.
"""

import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def sample_markdown():
    """Simple Markdown content for testing."""
    return """# Test Document

This is a **test** document with various Markdown features.

## Section 1: Lists

- Item 1
- Item 2
- Item 3

## Section 2: Code

Here's some inline `code` and a code block:

```python
def hello():
    print("Hello, World!")
```

## Section 3: Table

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| A        | B        | C        |
| D        | E        | F        |

## Section 4: Links

Visit [Example](https://example.com) for more information.
"""


@pytest.fixture
def sample_markdown_chinese():
    """Markdown content with Chinese characters."""
    return """# 测试文档

这是一个**测试**文档，包含中文内容。

## 第一节：列表

- 项目一
- 项目二
- 项目三

## 第二节：表格

| 姓名 | 年龄 | 城市 |
|------|------|------|
| 张三 | 25   | 北京 |
| 李四 | 30   | 上海 |

## 第三节：代码

```python
def 你好():
    print("你好，世界！")
```
"""


@pytest.fixture
def sample_markdown_code():
    """Markdown with various code blocks."""
    return """# Code Examples

## Python

```python
import asyncio

async def main():
    await asyncio.sleep(1)
    return "done"
```

## JavaScript

```javascript
const greet = (name) => {
    console.log(`Hello, ${name}!`);
};
```

## Bash

```bash
#!/bin/bash
echo "Hello from bash"
```
"""


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_md_file(temp_dir, sample_markdown):
    """Create a temporary Markdown file."""
    file_path = temp_dir / "test.md"
    file_path.write_text(sample_markdown)
    yield file_path


@pytest.fixture
def sample_md_file_chinese(temp_dir, sample_markdown_chinese):
    """Create a temporary Markdown file with Chinese content."""
    file_path = temp_dir / "test_chinese.md"
    file_path.write_text(sample_markdown_chinese, encoding="utf-8")
    yield file_path


@pytest.fixture
def sample_md_file_code(temp_dir, sample_markdown_code):
    """Create a temporary Markdown file with code blocks."""
    file_path = temp_dir / "test_code.md"
    file_path.write_text(sample_markdown_code)
    yield file_path


@pytest.fixture
def empty_md_file(temp_dir):
    """Create an empty Markdown file."""
    file_path = temp_dir / "empty.md"
    file_path.touch()
    yield file_path
