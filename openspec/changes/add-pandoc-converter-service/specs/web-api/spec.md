# Spec: Web API接口

## ADDED Requirements

### Requirement: 转换API端点

The system MUST provide RESTful API endpoints for document conversion.

系统必须提供RESTful API端点用于文档转换。

**Rationale**: 提供标准化的HTTP接口，便于各种客户端集成。

#### Scenario: POST请求转换文档

**Given** 系统正在运行
**And** API端点 `/api/v1/convert` 可用
**When** 客户端发送POST请求
**And** 请求包含multipart/form-data格式的文件
**And** 请求指定目标格式（pdf或docx）
**Then** 系统返回200状态码
**And** 响应Content-Type与目标格式匹配
**And** 响应体包含转换后的文件内容

#### Scenario: 请求缺少必需参数

**Given** 系统正在运行
**When** 客户端发送POST请求但不包含文件
**Then** 系统返回400状态码
**And** 响应包含错误消息说明缺少参数

#### Scenario: 请求使用不支持的格式

**Given** 系统正在运行
**When** 客户端请求转换为不支持的格式
**Then** 系统返回400状态码
**And** 响应包含错误消息列出支持的格式

---

### Requirement: 文件上传处理

The system MUST properly handle file upload requests.

系统必须正确处理文件上传请求。

**Rationale**: 确保文件传输的安全性和可靠性。

#### Scenario: 支持multipart/form-data上传

**Given** 客户端使用multipart/form-data格式
**When** 上传Markdown文件
**Then** 系统正确解析文件内容
**And** 系统提取原始文件名

#### Scenario: 验证文件类型

**Given** 客户端上传文件
**When** 文件扩展名不是.md或.markdown或.txt
**Then** 系统拒绝请求
**And** 返回400状态码
**And** 错误消息说明允许的文件类型

#### Scenario: 验证文件大小

**Given** 系统配置的最大文件大小为10MB
**When** 客户端上传超过10MB的文件
**Then** 系统拒绝请求
**And** 返回413状态码
**And** 错误消息说明文件大小限制

#### Scenario: 处理空文件

**Given** 客户端上传0字节文件
**When** 系统尝试转换
**Then** 系统返回400状态码
**And** 错误消息说明文件为空

---

### Requirement: 响应格式

The system MUST return standardized HTTP responses.

系统必须返回标准化的HTTP响应。

**Rationale**: 提供一致的客户端体验。

#### Scenario: 成功转换返回文件流

**Given** 转换成功完成
**When** 返回响应给客户端
**Then** 状态码为200
**And** Content-Type根据格式设置：
  - PDF: application/pdf
  - DOCX: application/vnd.openxmlformats-officedocument.wordprocessingml.document
**And** Content-Disposition包含下载文件名
**And** 响应体包含文件二进制内容

#### Scenario: 错误响应使用JSON格式

**Given** 请求处理失败
**When** 返回错误响应
**Then** Content-Type为application/json
**And** 响应体包含以下结构：
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "人类可读的错误消息",
    "details": {}
  }
}
```

#### Scenario: 包含CORS头

**Given** 客户端从不同源发起请求
**When** 系统返回响应
**Then** 响应包含适当的CORS头
**And** 允许跨域访问（如果配置启用）

---

### Requirement: 健康检查端点

The system MUST provide a health check endpoint for monitoring.

系统必须提供健康检查端点用于监控。

**Rationale**: 便于容器编排和负载均衡器检查服务状态。

#### Scenario: GET请求健康检查

**Given** 系统正在运行
**When** 客户端请求 `/health` 端点
**Then** 系统返回200状态码
**And** 响应包含以下信息：
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "pandoc_version": "3.1.3",
  "uptime": 秒数
}
```

#### Scenario: 包含依赖项状态

**Given** 系统正在运行
**When** 客户端请求 `/health` 端点
**Then** 响应包含Pandoc是否可用
**And** 响应包含临时目录是否可写

#### Scenario: 系统不健康时返回503

**Given** Pandoc不可用
**When** 客户端请求 `/health` 端点
**Then** 系统返回503状态码
**And** 响应包含不健康的原因

---

### Requirement: API文档

The system MUST provide auto-generated API documentation.

系统必须提供自动生成的API文档。

**Rationale**: 降低API使用和集成的难度。

#### Scenario: Swagger UI可用

**Given** 系统正在运行
**When** 客户端访问 `/docs` 端点
**Then** 系统显示Swagger UI界面
**And** 文档包含所有API端点
**And** 文档包含请求/响应示例

#### Scenario: ReDoc文档可用

**Given** 系统正在运行
**When** 客户端访问 `/redoc` 端点
**Then** 系统显示ReDoc文档界面
**And** 文档包含完整的API规范

#### Scenario: OpenAPI规范可访问

**Given** 系统正在运行
**When** 客户端请求 `/openapi.json` 端点
**Then** 系统返回OpenAPI JSON规范
**And** 规范包含所有端点、参数、响应定义

---

### Requirement: 请求超时处理

The system MUST properly handle long-running conversion requests.

系统必须正确处理长时间运行的转换请求。

**Rationale**: 防止资源耗尽和挂起的连接。

#### Scenario: 转换超时返回错误

**Given** 系统配置的转换超时为30秒
**When** Pandoc转换超过30秒未完成
**Then** 系统终止转换进程
**And** 返回504 Gateway Timeout状态码
**And** 错误消息说明操作超时

#### Scenario: 客户端提前断开连接

**Given** 转换正在进行中
**When** 客户端断开HTTP连接
**Then** 系统终止转换进程
**And** 系统清理临时文件

---

### Requirement: 并发请求处理

The system MUST be able to handle multiple conversion requests simultaneously.

系统必须能够同时处理多个转换请求。

**Rationale**: 支持多用户并发使用。

#### Scenario: 多个独立请求并行处理

**Given** 系统收到多个转换请求
**When** 这些请求同时到达
**Then** 系统并行处理这些请求
**And** 每个请求获得独立的临时文件
**And** 请求之间不互相干扰

#### Scenario: 并发限制

**Given** 系统配置的最大并发数为10
**When** 同时有超过10个请求
**Then** 系统处理前10个请求
**And** 其他请求等待或返回503状态码（取决于配置）
