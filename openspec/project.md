# Project Context

## Purpose
一个用于转换 Markdown 格式的工具，支持 Markdown 与其他格式（如 HTML、PDF 等）之间的相互转换。

## Tech Stack
- **Python 3.10+** - 主要编程语言
- **标准库** - 优先使用 Python 标准库
- **markdown / markdown2** - Markdown 解析（待定）
- **pytest** - 测试框架
- **black** - 代码格式化
- **ruff** - Linting

## Project Conventions

### Code Style
- **命名规范**：
  - 函数和变量：`snake_case`
  - 类名：`PascalCase`
  - 常量：`UPPER_SNAKE_CASE`
  - 私有成员：前缀单下划线 `_private`
- **格式化**：使用 `black`（默认配置）
- **类型注解**：使用类型提示（Type Hints）
- **文档字符串**：使用 Google 风格的 docstrings

### Architecture Patterns
- **模块化设计**：每个转换格式作为独立模块
- **单一职责**：每个函数/类只做一件事
- **依赖注入**：使用依赖注入而非硬编码依赖
- **错误处理**：使用明确的异常类型，避免裸 `except`
- **配置管理**：使用环境变量或配置文件

### Testing Strategy
- **测试覆盖率目标**：>90%
- **测试框架**：pytest
- **测试类型**：
  - 单元测试：每个函数/类
  - 集成测试：端到端转换流程
  - 边界测试：空输入、特殊字符、大文件
- **测试组织**：`tests/` 目录镜像 `src/` 结构
- **Fixtures**：使用 pytest fixtures 管理测试数据

### Git Workflow
- **主分支**：`main`
- **功能分支**：`feature/` 前缀（如 `feature/html-export`）
- **修复分支**：`fix/` 前缀（如 `fix/encoding-issue`）
- **提交信息**：使用约定式提交（Conventional Commits）
  - `feat:` 新功能
  - `fix:` Bug 修复
  - `refactor:` 重构
  - `test:` 测试相关
  - `docs:` 文档更新
- **审查**：所有更改需要 PR 审查

## Domain Context
- **Markdown 规范**：遵循 CommonMark 或 GitHub Flavored Markdown (GFM)
- **转换目标**：
  - HTML：保持结构和格式
  - PDF：支持分页、样式
  - 其他格式按需扩展
- **字符编码**：默认 UTF-8
- **扩展性**：设计支持插件/扩展添加新转换器

## Important Constraints
- **性能**：支持大文件（>10MB）转换不崩溃
- **兼容性**：Python 3.10+
- **依赖最小化**：优先使用标准库，减少外部依赖
- **向后兼容**：API 变更需要 major 版本更新

## External Dependencies
- *待确定*：具体依赖库将根据功能需求选择
