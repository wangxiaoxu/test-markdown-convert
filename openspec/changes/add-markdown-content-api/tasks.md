# Tasks: 添加基于Markdown内容字符串的转换API

## Overview
本任务列表用于实现新增的 `/api/v1/convert-content` 端点，按优先级和依赖关系排序。

## Tasks

### 1. 创建Pydantic请求模型
**优先级**: 高
**预估工作量**: 小
**依赖**: 无

创建Pydantic模型用于验证JSON请求体：
- 在 `src/api/routes/convert.py` 或新建 `src/api/models.py` 中创建 `MarkdownContentRequest` 类
- 字段定义：
  - `content`: str, required, min_length=1, max_length=10485760
  - `format`: str, required, pattern="^(pdf|docx)$"
  - `filename`: str, optional, default="document", pattern="^[a-zA-Z0-9_-]+$"
- 添加模型验证和错误消息

**验证**: 运行 `pytest tests/api/test_models.py -v`，所有模型验证测试通过

---

### 2. 实现convert_markdown_content端点
**优先级**: 高
**预估工作量**: 中
**依赖**: 任务1

在 `src/api/routes/convert.py` 中实现新端点：
- 定义 `convert_markdown_content` 异步函数
- 添加路由装饰器 `@router.post("/convert-content")`
- 添加详细的API文档字符串（summary、description、responses）
- 实现请求验证逻辑：
  - 使用Pydantic模型解析请求体
  - 验证内容非空
  - 验证格式支持
  - 验证内容长度
- 实现转换流程：
  - 将内容字符串写入临时文件（复用 `file_handler.save_bytes`）
  - 调用 `converter.convert`
  - 返回 `FileResponse`
- 实现错误处理：
  - 复用现有的异常处理逻辑
  - 添加内容长度超限错误
  - 添加内容编码错误处理
- 添加后台任务清理临时文件

**验证**:
- 使用 `pytest` 运行端点测试
- 使用 `curl` 或 Postman 手动测试端点

---

### 3. 更新API文档
**优先级**: 中
**预估工作量**: 小
**依赖**: 任务2

确保新端点在Swagger UI和ReDoc中正确显示：
- 验证 `/docs` 端点显示新端点
- 验证 `/redoc` 端点显示新端点
- 验证 `/openapi.json` 包含新端点定义
- 添加请求/响应示例

**验证**: 启动服务，访问 `http://localhost:8000/docs` 确认文档正确

---

### 4. 编写单元测试
**优先级**: 高
**预估工作量**: 中
**依赖**: 任务2

在 `tests/api/test_routes.py` 或新建 `tests/api/test_convert_content.py` 中编写测试：

**正常场景测试**:
- 成功转换Markdown内容为PDF
- 成功转换Markdown内容为DOCX
- 使用自定义文件名
- 使用默认文件名

**错误场景测试**:
- 空内容返回400错误
- 内容超长返回413错误
- 不支持的格式返回400错误
- 无效的文件名字符返回400错误
- Pandoc转换失败返回500错误

**边界测试**:
- 最小有效内容（1个字符）
- 最大有效内容（10MB）
- 包含特殊字符的内容
- 包含中文的内容
- 包含Markdown语法的内容

**验证**: 运行 `pytest tests/api/ -v --cov=src/api/routes`，覆盖率 >90%

---

### 5. 编写集成测试
**优先级**: 中
**预估工作量**: 中
**依赖**: 任务2

在 `tests/integration/` 中编写端到端测试：
- 测试完整的请求-响应流程
- 测试临时文件正确清理
- 测试并发请求不互相干扰
- 测试与 `/api/v1/convert` 端点结果一致性

**验证**: 运行 `pytest tests/integration/ -v`，所有测试通过

---

### 6. 更新项目文档
**优先级**: 低
**预估工作量**: 小
**依赖**: 任务2

更新项目README或API文档：
- 添加新端点的使用说明
- 添加请求/响应示例
- 更新API端点列表

**验证**: 文档准确描述新端点功能

---

### 7. 代码审查和优化
**优先级**: 中
**预估工作量**: 小
**依赖**: 任务1-4

- 运行 `black` 格式化代码
- 运行 `ruff` 检查代码质量
- 运行 `mypy` 进行类型检查
- 审查代码，确保符合项目规范
- 优化性能（如有必要）

**验证**:
- `black src/api/routes/convert.py` 无变更
- `ruff check src/api/routes/convert.py` 无错误
- `mypy src/api/routes/convert.py` 无类型错误

---

## 测试策略

### 测试环境设置
```bash
# 启动服务
docker-compose up -d

# 运行测试
pytest tests/ -v --cov=src
```

### 手动测试命令
```bash
# 测试PDF转换
curl -X POST http://localhost:8000/api/v1/convert-content \
  -H "Content-Type: application/json" \
  -d '{"content": "# Hello World\n\nThis is a test.", "format": "pdf"}' \
  --output test.pdf

# 测试DOCX转换
curl -X POST http://localhost:8000/api/v1/convert-content \
  -H "Content-Type: application/json" \
  -d '{"content": "# Hello World", "format": "docx"}' \
  --output test.docx

# 测试错误处理（空内容）
curl -X POST http://localhost:8000/api/v1/convert-content \
  -H "Content-Type: application/json" \
  -d '{"content": "", "format": "pdf"}'
```

## 并行化机会
- **任务1 和 任务4的准备**: 可以并行进行测试框架搭建
- **任务3 和 任务4**: 文档更新和测试编写可以部分并行
- **任务5 和 任务7**: 集成测试和代码审查可以并行

## 验收标准
1. [x] 所有单元测试通过
2. [x] 所有集成测试通过
3. [x] 测试覆盖率 >90%
4. [x] API文档正确显示新端点
5. [x] 代码通过所有质量检查（black、mypy）
6. [x] 手动测试验证功能正常
