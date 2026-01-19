# Design: Pandoc文档转换服务

## Overview

本文档描述了基于Pandoc的文档转换Web服务的技术设计。

## Architecture

```
┌─────────────────┐
│  HTTP Client    │
└────────┬────────┘
         │ HTTP POST /api/v1/convert
         ▼
┌─────────────────────────────────┐
│         FastAPI App             │
│  ┌──────────────────────────┐  │
│  │   Request Validation     │  │
│  │   - File type check      │  │
│  │   - Size limit           │  │
│  └───────────┬──────────────┘  │
│              │                  │
│  ┌───────────▼──────────────┐  │
│  │   PandocConverter        │  │
│  │   - Command builder      │  │
│  │   - Process execution    │  │
│  └───────────┬──────────────┘  │
│              │                  │
│  ┌───────────▼──────────────┐  │
│  │   Response Handler       │  │
│  └──────────────────────────┘  │
└─────────────────────────────────┘
         │ subprocess
         ▼
┌─────────────────────────────────┐
│      Pandoc (in container)      │
│  ┌──────────────────────────┐  │
│  │   Markdown Parser        │  │
│  └───────────┬──────────────┘  │
│              │                  │
│  ┌───────────▼──────────────┐  │
│  │   Format Converters      │  │
│  │   - PDF (via LaTeX)      │  │
│  │   - DOCX                 │  │
│  └──────────────────────────┘  │
└─────────────────────────────────┘
```

## Component Design

### 1. FastAPI Application (src/api/main.py)

**职责**: HTTP服务器和路由管理

```python
# 核心配置
config = {
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "allowed_input_formats": ["md", "markdown", "txt"],
    "timeout": 30,  # seconds
}

# 端点
POST /api/v1/convert
  - 接收multipart/form-data
  - 返回application/pdf或application/vnd.openxmlformats-officedocument.wordprocessingml.document
  - 错误返回application/json

GET /health
  - 健康检查
  - 返回服务状态和Pandoc版本
```

### 2. Pandoc Converter (src/converters/pandoc.py)

**职责**: 封装Pandoc命令行调用

```python
class PandocConverter:
    def convert(
        self,
        input_path: str,
        output_path: str,
        output_format: str,
        options: dict = None
    ) -> bool:
        """执行转换

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            output_format: 目标格式 (pdf|docx)
            options: 额外的Pandoc选项

        Returns:
            成功返回True，失败抛出ConversionError
        """

    def _build_command(self, output_format: str) -> list[str]:
        """构建Pandoc命令

        PDF: pandoc input.md -o output.pdf --pdf-engine=xelatex
        DOCX: pandoc input.md -o output.docx
        """
```

**错误处理**:
- `ConversionError`: 转换失败
- `UnsupportedFormatError`: 不支持的格式
- `FileAccessError`: 文件读写错误

### 3. File Handler (src/utils/file_handler.py)

**职责**: 临时文件管理

```python
class FileHandler:
    def __init__(self, temp_dir: str = "/tmp/converter"):
        self.temp_dir = temp_dir

    def save_upload(self, upload_file: UploadFile) -> str:
        """保存上传的文件到临时目录"""

    def cleanup(self, *paths: str):
        """清理临时文件"""

    @contextmanager
    def managed_file(self, upload_file: UploadFile):
        """上下文管理器，自动清理"""
```

## Docker Design

### Dockerfile

```dockerfile
# 多阶段构建
FROM python:3.10-slim as base

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    pandoc \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-lang-chinese \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ /app/src/

# 创建非root用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  converter:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./src:/app/src:ro  # 开发模式挂载
    environment:
      - LOG_LEVEL=INFO
      - MAX_FILE_SIZE=10485760
      - TEMP_DIR=/tmp/converter
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Data Flow

### 转换流程

```
1. 客户端上传文件
   └─> POST /api/v1/convert
       └─> multipart/form-data: {file, format, options}

2. FastAPI验证请求
   ├─> 检查文件类型
   ├─> 检查文件大小
   └─> 验证format参数

3. 文件处理
   ├─> FileHandler保存到临时目录
   ├─> 生成唯一输出文件名
   └─> 注册清理回调

4. 执行转换
   ├─> PandocConverter构建命令
   ├─> subprocess调用pandoc
   └─> 捕获输出和错误

5. 返回结果
   ├─> 成功: FileResponse(输出文件)
   ├─> 失败: JSONResponse({"error": message})
   └─> 清理临时文件
```

## Security Considerations

### 输入验证
- 文件类型白名单: `.md`, `.markdown`, `.txt`
- 文件大小限制: 10MB（可配置）
- 格式参数白名单: `pdf`, `docx`
- Pandoc选项过滤: 防止命令注入

### 资源限制
- 容器内存限制: 1GB
- 请求超时: 30秒
- 并发限制: 建议使用反向代理（nginx）

### 隔离
- 容器内非root用户运行
- 临时文件隔离
- 网络隔离（如需要）

## Error Handling

### 错误分类

| 错误类型 | HTTP状态 | 示例 |
|---------|---------|------|
| ValidationError | 400 | 无效的文件类型 |
| FileTooLargeError | 413 | 文件超过10MB |
| UnsupportedFormatError | 400 | 不支持的输出格式 |
| ConversionError | 500 | Pandoc转换失败 |
| InternalError | 500 | 服务器内部错误 |

### 错误响应格式

```json
{
  "error": {
    "code": "INVALID_FILE_TYPE",
    "message": "Only .md, .markdown, and .txt files are allowed",
    "details": {
      "received_type": "application/pdf"
    }
  }
}
```

## Testing Strategy

### 单元测试
- `test_pandoc_converter.py`: 测试转换逻辑
- `test_file_handler.py`: 测试文件处理
- `test_validators.py`: 测试输入验证

### 集成测试
- `test_api_endpoints.py`: 测试API端点
- 使用真实Pandoc执行
- 测试各种文件格式

### 测试Fixtures

```python
@pytest.fixture
def sample_markdown():
    return """# Test Document

This is a **test** document.

## Section 1

- Item 1
- Item 2
"""

@pytest.fixture
def temp_output():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        yield f.name
    os.unlink(f.name)
```

## Performance Considerations

### 优化点
1. **流式响应**: 大文件使用流式传输
2. **连接池**: HTTP客户端复用
3. **缓存**: 不适用（每次转换独立）
4. **异步处理**: FastAPI异步端点

### 扩展性
- 水平扩展: 多容器实例
- 负载均衡: nginx/docker swarm
- 任务队列: 未来可添加Celery

## Configuration

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| LOG_LEVEL | INFO | 日志级别 |
| MAX_FILE_SIZE | 10485760 | 最大文件大小(字节) |
| TEMP_DIR | /tmp/converter | 临时文件目录 |
| PANDOC_TIMEOUT | 30 | Pandoc超时(秒) |
| PDF_ENGINE | xelatex | PDF引擎 |

### Pandoc选项映射

```python
FORMAT_OPTIONS = {
    "pdf": {
        "pdf_engine": "xelatex",
        "variables": {
            "geometry": "margin=1in",
            "linestretch": "1.2"
        }
    },
    "docx": {
        "standalone": True
    }
}
```

## Monitoring

### 日志
- 请求日志: method, path, status, duration
- 转换日志: input_size, output_size, format, duration
- 错误日志: error_type, message, traceback

### 健康检查

```python
GET /health
{
  "status": "healthy",
  "version": "1.0.0",
  "pandoc_version": "3.1.3",
  "uptime": 3600
}
```

## Future Enhancements

### Phase 2
- [ ] 批量转换支持
- [ ] 自定义样式/模板
- [ ] 转换进度反馈
- [ ] WebSocket支持

### Phase 3
- [ ] 任务队列 (Celery)
- [ ] 结果缓存 (Redis)
- [ ] 文件存储 (S3)
- [ ] 用户认证
