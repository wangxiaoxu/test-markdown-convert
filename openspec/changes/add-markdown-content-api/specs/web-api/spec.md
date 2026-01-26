# Spec: Web API接口 - Markdown内容转换端点

## ADDED Requirements

### Requirement: Markdown内容转换API端点

The system MUST provide a RESTful API endpoint for converting Markdown content strings to PDF or Word format.

系统必须提供RESTful API端点用于将Markdown内容字符串转换为PDF或Word格式。

**Rationale**: 某些场景下，Markdown内容以字符串形式存在（如数据库存储、动态生成），直接传递内容字符串比文件上传更高效，避免了不必要的文件I/O操作。

#### Scenario: POST请求转换Markdown内容为PDF

**Given** 系统正在运行
**And** API端点 `/api/v1/convert-content` 可用
**When** 客户端发送POST请求
**And** 请求Content-Type为application/json
**And** 请求体包含：
  - `content`: "# Hello World\n\nThis is a test."
  - `format`: "pdf"
  - `filename`: "my-document" (可选)
**Then** 系统返回200状态码
**And** 响应Content-Type为application/pdf
**And** 响应体包含转换后的PDF文件内容
**And** Content-Disposition包含文件名 "my-document.pdf"

#### Scenario: POST请求转换Markdown内容为Word

**Given** 系统正在运行
**When** 客户端发送POST请求
**And** 请求体包含：
  - `content`: "# Document Title\n\nSome content."
  - `format`: "docx"
**Then** 系统返回200状态码
**And** 响应Content-Type为application/vnd.openxmlformats-officedocument.wordprocessingml.document
**And** 响应体包含转换后的Word文件内容

#### Scenario: 使用默认文件名

**Given** 系统正在运行
**When** 客户端发送POST请求
**And** 请求体不包含 `filename` 字段
**Then** 系统使用默认文件名 "document"
**And** Content-Disposition包含文件名 "document.pdf" (或docx)

#### Scenario: 内容为空时返回错误

**Given** 系统正在运行
**When** 客户端发送POST请求
**And** 请求体中 `content` 为空字符串或null
**Then** 系统返回400状态码
**And** 错误消息说明内容不能为空

#### Scenario: 内容长度超过限制时返回错误

**Given** 系统配置的内容长度限制为10MB
**When** 客户端发送POST请求
**And** 请求体中 `content` 长度超过10485760字节
**Then** 系统返回413状态码
**And** 错误消息说明内容长度超过限制
**And** 错误详情包含实际长度和最大长度

#### Scenario: 格式不支持时返回错误

**Given** 系统正在运行
**When** 客户端发送POST请求
**And** 请求体中 `format` 为 "html" 或其他不支持的值
**Then** 系统返回400状态码
**And** 错误消息说明格式不支持
**And** 错误详情列出支持的格式（pdf、docx）

#### Scenario: 文件名包含非法字符时返回错误

**Given** 系统正在运行
**When** 客户端发送POST请求
**And** 请求体中 `filename` 包含路径字符（如 ../ 或 /）
**Then** 系统返回400状态码
**And** 错误消息说明文件名格式无效

#### Scenario: 转换超时返回错误

**Given** 系统配置的转换超时为30秒
**When** Pandoc转换超过30秒未完成
**Then** 系统终止转换进程
**And** 返回504 Gateway Timeout状态码
**And** 错误消息说明操作超时

#### Scenario: Pandoc执行失败返回错误

**Given** 系统正在运行
**When** Pandoc转换执行失败
**Then** 系统返回500状态码
**And** 错误消息说明转换失败
**And** 错误详情包含Pandoc错误信息

---

### Requirement: JSON请求体验证

The system MUST properly validate and parse JSON request bodies.

系统必须正确验证和解析JSON请求体。

**Rationale**: 确保请求数据的完整性和安全性，防止无效数据导致转换失败或系统异常。

#### Scenario: 无效的JSON格式

**Given** 系统正在运行
**When** 客户端发送POST请求
**And** 请求体不是有效的JSON格式
**Then** 系统返回400状态码
**And** 错误消息说明JSON格式无效

#### Scenario: 缺少必需字段

**Given** 系统正在运行
**When** 客户端发送POST请求
**And** 请求体缺少 `content` 字段
**Then** 系统返回400状态码
**And** 错误消息说明缺少必需字段

#### Scenario: 字段类型错误

**Given** 系统正在运行
**When** 客户端发送POST请求
**And** `content` 字段不是字符串类型
**Then** 系统返回400状态码
**And** 错误消息说明字段类型错误

---

### Requirement: 内容编码处理

The system MUST handle content encoding correctly.

系统必须正确处理内容编码。

**Rationale**: 确保各种字符（特别是中文等多字节字符）能够正确转换。

#### Scenario: UTF-8编码的中文内容

**Given** 客户端发送包含中文的Markdown内容
**And** 内容使用UTF-8编码
**When** 系统执行转换
**Then** 转换后的文档正确显示中文字符
**And** 无乱码或编码错误

#### Scenario: 包含特殊字符的内容

**Given** 客户端发送包含特殊字符的内容
**And** 内容包含：emoji、数学符号、特殊标点
**When** 系统执行转换
**Then** 转换后的文档正确显示这些字符

---

### Requirement: 临时文件管理

The system MUST properly manage temporary files created during conversion.

系统必须正确管理转换过程中创建的临时文件。

**Rationale**: 防止磁盘空间耗尽和敏感信息泄露。

#### Scenario: 转换成功后清理临时文件

**Given** 系统接收到内容转换请求
**When** 转换成功完成
**And** 响应已发送给客户端
**Then** 系统在后台删除输入临时文件
**And** 系统在后台删除输出临时文件
**And** 清理任务在响应返回后异步执行

#### Scenario: 转换失败后清理临时文件

**Given** 系统接收到内容转换请求
**When** 转换过程中发生错误
**Then** 系统删除已创建的临时文件
**And** 不会留下孤立的临时文件

#### Scenario: 客户端断开连接时清理

**Given** 转换正在进行中
**When** 客户端断开HTTP连接
**Then** 系统终止转换进程
**And** 系统清理已创建的临时文件

---

### Requirement: 与文件上传端点的一致性

The new content-based endpoint MUST produce identical results to the file upload endpoint.

新的基于内容的端点必须产生与文件上传端点相同的结果。

**Rationale**: 确保API行为的一致性，避免用户困惑。

#### Scenario: 相同内容产生相同输出

**Given** 有一个Markdown文件 "test.md"
**And** 文件内容为 "# Test\n\nContent"
**When** 客户端通过 `/api/v1/convert` 上传该文件
**And** 客户端通过 `/api/v1/convert-content` 发送相同内容
**Then** 两个端点返回的转换结果完全一致
**And** 文件内容差异为0字节

#### Scenario: 错误处理一致性

**Given** 两种端点接收到无效请求
**And** 错误类型相同（如格式不支持）
**When** 比较两个端点的错误响应
**Then** 错误码、错误消息格式、HTTP状态码完全一致

---

### Requirement: API文档

The system MUST provide accurate API documentation for the new endpoint.

系统必须为新端点提供准确的API文档。

**Rationale**: 便于开发者理解和正确使用新端点。

#### Scenario: Swagger UI显示新端点

**Given** 系统正在运行
**When** 客户端访问 `/docs` 端点
**Then** Swagger UI显示 `/api/v1/convert-content` 端点
**And** 文档包含请求方法（POST）
**And** 文档包含请求体格式
**And** 文档包含所有参数说明
**And** 文档包含响应示例

#### Scenario: OpenAPI规范包含新端点

**Given** 系统正在运行
**When** 客户端请求 `/openapi.json`
**Then** 返回的JSON包含 `/api/v1/convert-content` 定义
**And** 定义包含请求schema
**And** 定义包含响应schema
**And** 定义包含错误响应

#### Scenario: 提供请求示例

**Given** 开发者查看API文档
**Then** 文档提供完整的请求示例
**And** 示例包含基本的Markdown内容转换
**And** 示例包含自定义文件名的用法
**And** 示例包含错误响应示例

---

### Requirement: 并发处理

The system MUST handle multiple concurrent content conversion requests properly.

系统必须正确处理多个并发的内容转换请求。

**Rationale**: 支持多用户同时使用API，确保请求间不相互干扰。

#### Scenario: 多个请求并行处理

**Given** 系统同时收到多个内容转换请求
**When** 这些请求同时到达
**Then** 系统并行处理这些请求
**And** 每个请求获得独立的临时文件
**And** 请求之间不互相干扰
**And** 所有请求都成功完成

#### Scenario: 临时文件隔离

**Given** 系统正在处理多个并发请求
**When** 每个请求创建临时文件
**Then** 每个请求的临时文件使用唯一文件名
**And** 临时文件不会互相覆盖
**And** 临时文件在对应请求完成后独立清理

---

### Requirement: 内容长度限制

The system MUST enforce a maximum content length limit.

系统必须强制执行最大内容长度限制。

**Rationale**: 防止内存耗尽和服务拒绝攻击。

#### Scenario: 默认长度限制

**Given** 系统配置的最大内容长度为10MB
**When** 客户端发送内容
**Then** 系统允许不超过10485760字节的内容
**And** 系统拒绝超过该长度的内容

#### Scenario: 长度限制可配置

**Given** 系统管理员需要调整长度限制
**When** 修改配置文件中的MAX_CONTENT_LENGTH
**Then** 新的限制立即生效
**And** 系统使用新限制验证后续请求

#### Scenario: 长度计算准确

**Given** 客户端发送UTF-8编码的内容
**When** 系统计算内容长度
**Then** 长度计算基于字节数而非字符数
**And** 多字节字符正确计入长度

---

## MODIFIED Requirements

### Requirement: API端点组织

The system API endpoints MUST follow a consistent naming and organizational pattern.

系统API端点必须遵循一致的命名和组织模式。

**Rationale**: 提高API的可理解性和可维护性。

#### Scenario: 端点命名一致性

**Given** 系统有多个转换相关端点
**When** 比较端点路径
**Then** 所有转换端点使用 `/api/v1/convert-*` 模式
**And** `/api/v1/convert` 用于文件上传
**And** `/api/v1/convert-content` 用于内容字符串

#### Scenario: 响应格式一致性

**Given** 两种端点都返回错误响应
**When** 比较错误响应格式
**Then** 使用相同的错误响应结构
**And** 使用相同的错误码
**And** 使用相同的HTTP状态码
