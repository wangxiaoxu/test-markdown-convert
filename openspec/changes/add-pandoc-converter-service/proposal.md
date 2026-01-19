# Proposal: 添加基于Pandoc的文档转换Web服务

## Change ID
`add-pandoc-converter-service`

## Summary
引入Pandoc作为核心转换引擎，通过Docker容器化部署，提供HTTP API接口实现Markdown到PDF和Word文档的转换功能。

## Motivation
当前项目需要支持Markdown到PDF和Word格式的转换。Pandoc是业界标准的文档转换工具，支持丰富的输入输出格式。通过容器化部署可以：
- 避免在本地安装Pandoc及其依赖（如LaTeX用于PDF生成）
- 提供一致的运行环境
- 简化部署和分发
- 便于横向扩展

## Proposed Solution

### 核心组件
1. **Web API服务**：基于FastAPI构建RESTful API
2. **Pandoc集成层**：封装Pandoc命令行调用
3. **Docker镜像**：包含Pandoc、LaTeX环境和应用代码
4. **Docker Compose配置**：简化本地开发和部署

### API设计
```
POST /api/v1/convert
Content-Type: multipart/form-data

Request:
- file: Markdown文件
- format: 目标格式 (pdf|docx)
- options: 可选的Pandoc参数

Response:
- 200: 转换后的文件流
- 400: 请求参数错误
- 500: 转换失败
```

### 技术选型
- **Web框架**: FastAPI (轻量、异步、自动文档)
- **Pandoc**: 最新稳定版
- **PDF引擎**: LaTeX (通过Pandoc)
- **容器**: Docker + Docker Compose
- **Python**: 3.10+

## Scope

### 包含内容
- [x] Markdown转PDF功能
- [x] Markdown转Word (docx)功能
- [x] HTTP API接口
- [x] Docker镜像构建
- [x] Docker Compose配置
- [x] 基础错误处理和日志
- [x] API文档 (Swagger UI)

### 不包含内容
- [ ] 用户认证和授权
- [ ] 批量转换
- [ ] 转换任务队列
- [ ] 自定义样式/模板
- [ ] 进度反馈
- [ ] 文件存储

## Alternatives Considered

### 方案1: 本地安装Pandoc
**优点**:
- 实现简单
- 无需容器化

**缺点**:
- 依赖管理复杂（尤其是LaTeX）
- 跨平台兼容性问题
- 部署困难

**结论**: 不采用，违反了"不在本机安装"的要求

### 方案2: 使用纯Python库（如pypandoc、markdown2）
**优点**:
- 纯Python实现
- 部署简单

**缺点**:
- PDF生成仍需Pandoc/LaTeX
- 功能有限
- 维护成本

**结论**: 不采用，功能受限且无法避免外部依赖

### 方案3: 云服务API（如ConvertAPI）
**优点**:
- 无需自建
- 可靠性高

**缺点**:
- 成本
- 数据隐私
- 依赖外部服务

**结论**: 不采用，需要自建服务

## Impact Analysis

### 新增依赖
- `fastapi`: Web框架
- `uvicorn`: ASGI服务器
- `python-multipart`: 文件上传支持
- `pandoc`: 容器内安装
- `texlive-full`: PDF生成依赖

### 文件结构
```
.
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI应用入口
│   │   └── routes/
│   │       └── convert.py   # 转换路由
│   ├── converters/
│   │   ├── __init__.py
│   │   ├── base.py          # 转换器基类
│   │   ├── pandoc.py        # Pandoc包装器
│   │   └── formats.py       # 格式定义
│   └── utils/
│       ├── __init__.py
│       └── file_handler.py  # 文件处理
└── tests/
    ├── api/
    └── converters/
```

### 性能考虑
- 单次转换耗时: PDF ~1-5秒, Word ~0.5-2秒
- 内存占用: 容器限制512MB-1GB
- 并发: 单容器可处理10-20并发

## Risks and Mitigations

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Pandoc/LaTeX镜像大 | 构建时间长 | 使用多阶段构建，缓存层 |
| PDF转换失败 | 功能不可用 | 详细错误日志，降级处理 |
| 容器资源占用 | 运行成本 | 资源限制，按需扩展 |
| 安全漏洞 | 数据泄露 | 输入验证，定期更新 |

## Success Criteria
1. [ ] 能够成功将Markdown转换为PDF和Word
2. [ ] HTTP API响应正常，文档完整
3. [ ] Docker Compose一键启动成功
4. [ ] 测试覆盖率 >80%
5. [ ] API响应时间 <5秒 (PDF), <2秒 (Word)

## Dependencies
- Docker和Docker Compose已安装
- 端口8000未被占用

## Timeline
不提供时间估算（遵循项目约定）

## Related Changes
无（这是项目的第一个功能实现）

## Open Questions
1. 是否需要支持中文PDF生成？（需要配置CJK字体）
2. 是否需要添加基本的健康检查端点？
