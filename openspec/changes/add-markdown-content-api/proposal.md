# Proposal: 添加基于Markdown内容字符串的转换API

## Change ID
`add-markdown-content-api`

## Summary
在现有的文件上传转换API基础上，新增一个API端点，接受Markdown内容字符串作为输入而非文件上传，直接将字符串内容转换为目标格式文档。

## Motivation
当前 `/api/v1/convert` 端点要求客户端上传文件，这在某些场景下不够便利：

1. **动态内容生成**：应用动态生成Markdown内容，需要先写入临时文件才能调用API
2. **数据库内容**：Markdown内容存储在数据库中，需要先导出为文件
3. **模板生成**：基于模板生成的内容，希望直接转换而无需文件I/O
4. **微服务架构**：服务间调用时，直接传递内容字符串比文件传输更高效

通过添加内容字符串转换端点，可以：
- 简化客户端代码，无需文件处理
- 减少不必要的文件I/O操作
- 提高微服务间调用的效率
- 保持与现有API的一致性

## Proposed Solution

### API设计
新增端点 `/api/v1/convert-content`，使用JSON格式接收请求：

```
POST /api/v1/convert-content
Content-Type: application/json

Request:
{
  "content": "Markdown内容字符串",
  "format": "pdf",
  "filename": "document"  // 可选，用于生成下载文件名
}

Response:
- 200: 转换后的文件流
- 400: 请求参数错误（内容为空、格式不支持等）
- 413: 内容长度超过限制
- 500/504: 转换失败或超时
```

### 实现策略
1. **复用现有组件**：使用相同的 `PandocConverter`、`FileHandler` 和错误处理逻辑
2. **参数验证**：
   - `content`: 必需，非空字符串，最大长度与文件大小限制一致（10MB）
   - `format`: 必需，与现有端点相同的验证逻辑
   - `filename`: 可选，默认为 "document"
3. **临时文件处理**：将内容字符串写入临时文件后调用现有转换流程
4. **错误处理**：与现有端点保持一致的错误响应格式

### 代码位置
在 `/Users/wxx/workspace/test-code/test-markdown-convert/src/api/routes/convert.py` 中新增端点函数 `convert_markdown_content`

## Scope

### 包含内容
- [x] 新增 `/api/v1/convert-content` 端点
- [x] JSON请求体验证
- [x] 内容长度限制验证
- [x] 复用现有转换逻辑
- [x] 错误处理与日志
- [x] API文档更新（Swagger/OpenAPI）
- [x] 单元测试

### 不包含内容
- [ ] 批量内容转换
- [ ] 内容模板支持
- [ ] 转换进度反馈
- [ ] WebSocket支持

## Alternatives Considered

### 方案1: 扩展现有端点支持多种Content-Type
**优点**:
- 统一端点
- 减少API数量

**缺点**:
- 端点逻辑复杂化（需要判断Content-Type）
- 违反单一职责原则
- 文档说明不清晰

**结论**: 不采用，保持端点职责单一

### 方案2: 使用查询参数传递内容
**优点**:
- 实现简单

**缺点**:
- URL长度限制
- 不符合RESTful规范
- 安全性问题（内容暴露在URL中）

**结论**: 不采用，使用JSON请求体更规范

### 方案3: 客户端自行处理文件生成
**优点**:
- 无需服务端改动

**缺点**:
- 增加客户端复杂度
- 不必要的文件I/O
- 性能损失

**结论**: 不采用，服务端支持更合理

## Impact Analysis

### 新增依赖
无需新增依赖，完全使用现有组件

### 代码变更
- **修改文件**: `src/api/routes/convert.py`（新增约60-80行代码）
- **修改文件**: `tests/api/test_routes.py`（新增测试用例）

### 性能考虑
- 内存占用：内容字符串临时存储，与文件上传类似
- 转换性能：与现有端点一致
- 并发能力：不受影响，复用现有并发处理机制

## Risks and Mitigations

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 内容过长导致内存问题 | 服务不稳定 | 设置10MB长度限制，与文件大小限制一致 |
| 内容编码问题 | 转换失败 | 强制UTF-8编码验证 |
| 恶意内容注入 | 安全风险 | 内容视为纯文本，无代码执行 |

## Success Criteria
1. [ ] 新端点能成功接受Markdown内容字符串
2. [ ] 转换结果与文件上传端点一致
3. [ ] 错误处理覆盖所有边界情况
4. [ ] 测试覆盖率 >90%
5. [ ] API文档准确反映新端点用法

## Dependencies
- 现有的 `/api/v1/convert` 端点正常工作
- Pandoc转换服务可用

## Timeline
不提供时间估算（遵循项目约定）

## Related Changes
- `add-pandoc-converter-service`: 父变更，本变更在其基础上扩展

## Open Questions
1. **内容长度限制**：是否与文件大小限制保持一致（10MB）？
2. **文件名默认值**：是否使用 "document" 作为默认文件名？
3. **端点命名**：`/api/v1/convert-content` 是否合适，或使用 `/api/v1/convert/string`？
