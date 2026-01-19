# Markdown Converter Service

基于 Pandoc 的文档转换 Web 服务，支持将 Markdown 文档转换为 PDF 和 Word (DOCX) 格式。

## 功能特性

- ✅ Markdown 转 PDF
- ✅ Markdown 转 Word (DOCX)
- ✅ RESTful API 接口
- ✅ Docker 容器化部署
- ✅ 支持中文字符
- ✅ 自动生成 API 文档 (Swagger UI / ReDoc)

## 快速开始

### 使用 Docker Compose（推荐）

```bash
# 构建并启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

服务将在 http://localhost:8000 上运行。

### API 使用示例

#### 转换为 PDF

```bash
curl -X POST "http://localhost:8000/api/v1/convert" \
  -F "file=@document.md" \
  -F "format=pdf" \
  -o output.pdf
```

#### 转换为 Word

```bash
curl -X POST "http://localhost:8000/api/v1/convert" \
  -F "file=@document.md" \
  -F "format=docx" \
  -o output.docx
```

#### 健康检查

```bash
curl http://localhost:8000/health
```

## API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 配置选项

通过环境变量配置服务：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LOG_LEVEL` | INFO | 日志级别 (DEBUG, INFO, WARNING, ERROR) |
| `MAX_FILE_SIZE` | 10485760 | 最大文件大小（字节），默认 10MB |
| `TEMP_DIR` | /tmp/converter | 临时文件目录 |
| `PANDOC_TIMEOUT` | 30 | Pandoc 转换超时（秒） |
| `PDF_ENGINE` | xelatex | PDF 引擎 |

## 开发

### 本地开发环境

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest --cov=src

# 启动开发服务器（需要本地安装 Pandoc）
uvicorn src.api.main:app --reload
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/api/test_convert.py

# 查看测试覆盖率
pytest --cov=src --cov-report=html
```

## 项目结构

```
.
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── src/
│   ├── api/
│   │   ├── main.py          # FastAPI 应用入口
│   │   └── routes/
│   │       └── convert.py   # 转换路由
│   ├── converters/
│   │   ├── exceptions.py    # 异常定义
│   │   └── pandoc.py        # Pandoc 包装器
│   ├── utils/
│   │   └── file_handler.py  # 文件处理
│   └── config.py            # 配置管理
├── tests/
│   ├── api/
│   │   └── test_convert.py
│   └── converters/
│       └── test_pandoc.py
├── requirements.txt
└── README.md
```

## 许可证

MIT License
