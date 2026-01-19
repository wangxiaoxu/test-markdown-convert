# Tasks: 添加基于Pandoc的文档转换服务

## 任务列表

### 阶段1: 项目基础结构

- [ ] **1.1 创建项目目录结构**
  - 创建 `src/` 目录及其子目录（api/, converters/, utils/）
  - 创建 `tests/` 目录及其子目录
  - 创建 `docker/` 目录
  - 添加所有必要的 `__init__.py` 文件
  - **验证**: 运行 `tree` 或 `ls -R` 确认目录结构正确
  - **依赖**: 无

- [ ] **1.2 创建requirements.txt**
  - 添加 fastapi 依赖
  - 添加 uvicorn[standard] 依赖
  - 添加 python-multipart 依赖
  - 添加 pytest 依赖
  - 添加 httpx 依赖（用于测试）
  - **验证**: cat requirements.txt 确认所有依赖列出
  - **依赖**: 1.1

- [ ] **1.3 配置项目基础配置文件**
  - 创建 .gitignore 文件（包含 __pycache__, .pytest_cache, *.pyc 等）
  - 创建 README.md 基础文档
  - **验证**: 确认 .gitignore 正确配置
  - **依赖**: 1.1

---

### 阶段2: Docker环境

- [ ] **2.1 编写Dockerfile**
  - 选择基础镜像（python:3.10-slim）
  - 安装Pandoc和LaTeX依赖
  - 安装中文字体支持
  - 配置工作目录
  - 复制requirements.txt并安装Python依赖
  - 创建非root用户
  - 配置启动命令
  - **验证**: docker build -t md-converter . 成功构建
  - **依赖**: 1.2

- [ ] **2.2 编写docker-compose.yml**
  - 定义converter服务
  - 配置端口映射（8000:8000）
  - 配置环境变量
  - 配置卷挂载（开发模式）
  - 配置健康检查
  - 配置重启策略
  - **验证**: docker-compose config 验证配置正确
  - **依赖**: 2.1

- [ ] **2.3 测试Docker环境**
  - 构建镜像: docker-compose build
  - 启动容器: docker-compose up -d
  - 验证容器运行: docker-compose ps
  - 验证Pandoc可用: docker-compose exec converter pandoc --version
  - 验证LaTeX可用: docker-compose exec converter pdflatex --version
  - **验证**: 所有命令执行成功，Pandoc版本正确显示
  - **依赖**: 2.2

---

### 阶段3: 核心转换功能

- [ ] **3.1 实现PandocConverter类**
  - 创建 src/converters/pandoc.py
  - 实现 __init__ 方法
  - 实现 convert() 方法（执行pandoc命令）
  - 实现 _build_command() 方法（构建命令行）
  - 实现 _validate_format() 方法（验证输出格式）
  - 添加类型注解
  - 添加docstrings
  - **验证**: 单元测试覆盖所有方法
  - **依赖**: 2.3

- [ ] **3.2 实现错误处理**
  - 创建 src/converters/exceptions.py
  - 定义 ConversionError 异常
  - 定义 UnsupportedFormatError 异常
  - 定义 FileAccessError 异常
  - 定义 PandocExecutionError 异常
  - **验证**: 测试所有异常类型可正确抛出
  - **依赖**: 3.1

- [ ] **3.3 实现FileHandler类**
  - 创建 src/utils/file_handler.py
  - 实现 __init__ 方法（配置临时目录）
  - 实现 save_upload() 方法（保存上传文件）
  - 实现 cleanup() 方法（清理临时文件）
  - 实现 managed_file() 上下文管理器
  - **验证**: 单元测试验证文件清理逻辑
  - **依赖**: 3.2

- [ ] **3.4 编写转换器单元测试**
  - 创建 tests/converters/test_pandoc.py
  - 测试简单的MD到PDF转换
  - 测试简单的MD到DOCX转换
  - 测试带中文的MD转换
  - 测试带代码块的MD转换
  - 测试错误处理（无效文件、不支持格式）
  - 测试临时文件清理
  - **验证**: pytest --cov=src/converters 显示覆盖率 >80%
  - **依赖**: 3.3

---

### 阶段4: Web API

- [ ] **4.1 创建FastAPI应用入口**
  - 创建 src/api/main.py
  - 初始化FastAPI应用
  - 配置CORS（如果需要）
  - 添加中间件（日志、错误处理）
  - **验证**: uvicorn可以导入并启动应用
  - **依赖**: 3.4

- [ ] **4.2 实现转换API端点**
  - 创建 src/api/routes/convert.py
  - 实现 POST /api/v1/convert 端点
  - 实现文件上传验证（类型、大小）
  - 实现格式参数验证
  - 调用PandocConverter执行转换
  - 返回FileResponse或错误响应
  - **验证**: Postman或curl测试端点
  - **依赖**: 4.1

- [ ] **4.3 实现健康检查端点**
  - 在 main.py 中实现 GET /health 端点
  - 检查Pandoc可用性
  - 检查临时目录可写性
  - 返回服务状态信息
  - **验证**: GET /health 返回正确的状态
  - **依赖**: 4.2

- [ ] **4.4 配置请求验证和错误处理**
  - 创建 src/api/validators.py
  - 实现文件类型验证函数
  - 实现文件大小验证函数
  - 实现格式参数验证函数
  - 在主应用中添加全局异常处理器
  - **验证**: 测试各种错误场景返回正确的HTTP状态码
  - **依赖**: 4.3

- [ ] **4.5 编写API集成测试**
  - 创建 tests/api/test_convert.py
  - 测试成功转换场景（PDF和DOCX）
  - 测试文件类型验证
  - 测试文件大小限制
  - 测试格式参数验证
  - 测试健康检查端点
  - 使用TestClient进行测试
  - **验证**: 所有测试通过
  - **依赖**: 4.4

---

### 阶段5: 配置和文档

- [ ] **5.1 实现配置管理**
  - 创建 src/config.py
  - 定义配置类（使用环境变量）
  - 配置项: LOG_LEVEL, MAX_FILE_SIZE, TEMP_DIR, PANDOC_TIMEOUT, PDF_ENGINE
  - 提供默认值
  - **验证**: 环境变量正确覆盖默认值
  - **依赖**: 4.5

- [ ] **5.2 完善日志系统**
  - 配置应用日志格式
  - 配置请求日志（中间件）
  - 配置错误日志
  - 确保日志输出到stdout
  - **验证**: docker logs 查看日志输出
  - **依赖**: 5.1

- [ ] **5.3 编写API文档**
  - 为所有端点添加详细的docstrings
  - 配置FastAPI自动生成OpenAPI文档
  - 添加请求/响应示例
  - **验证**: 访问 /docs 和 /redoc 查看文档
  - **依赖**: 5.2

- [ ] **5.4 编写使用文档**
  - 更新 README.md
  - 添加快速开始指南
  - 添加Docker启动说明
  - 添加API使用示例
  - 添加配置说明
  - **验证**: 按照文档可以成功启动和使用服务
  - **依赖**: 5.3

---

### 阶段6: 测试和优化

- [ ] **6.1 完善测试覆盖率**
  - 运行完整测试套件
  - 检查测试覆盖率
  - 补充遗漏的测试用例
  - 目标: 覆盖率 >80%
  - **验证**: pytest --cov=src --cov-report=term-missing
  - **依赖**: 5.4

- [ ] **6.2 性能测试**
  - 测试不同大小文件的转换时间
  - 测试并发请求处理
  - 识别性能瓶颈
  - **验证**: 记录性能基准数据
  - **依赖**: 6.1

- [ ] **6.3 端到端测试**
  - 使用真实的Markdown文件测试
  - 测试各种Markdown特性（标题、列表、代码、表格、链接）
  - 验证输出文件质量
  - **验证**: 手动检查输出文件
  - **依赖**: 6.2

- [ ] **6.4 安全性检查**
  - 验证文件上传安全
  - 验证命令注入防护
  - 验证资源限制
  - 检查依赖漏洞
  - **验证**: 无已知安全漏洞
  - **依赖**: 6.3

---

### 阶段7: 最终验证

- [ ] **7.1 完整的Docker工作流测试**
  - 清理所有容器和镜像
  - 重新构建: docker-compose build
  - 启动服务: docker-compose up -d
  - 测试API功能
  - 停止服务: docker-compose down
  - **验证**: 完整流程无错误
  - **依赖**: 6.4

- [ ] **7.2 验证所有规格要求**
  - 检查每个spec.md中的场景
  - 确保所有场景都有对应测试
  - 确保所有场景都能通过
  - **验证**: 运行 openspec validate <change-id> --strict
  - **依赖**: 7.1

- [ ] **7.3 代码质量检查**
  - 运行 black 格式化检查
  - 运行 ruff linting
  - 检查类型注解完整性
  - 检查docstrings完整性
  - **验证**: 所有质量检查通过
  - **依赖**: 7.2

- [ ] **7.4 准备提交**
  - 检查 .gitignore 是否正确
  - 确认没有敏感信息
  - 确认没有临时文件
  - 编写提交信息
  - **验证**: git status 显示正确的变更
  - **依赖**: 7.3

## 并行化机会

以下任务可以并行执行以节省时间：
- **任务 3.4** 和 **4.1** 可以同时进行（单元测试和API开发独立）
- **任务 5.2**、**5.3**、**5.4** 可以并行进行（日志、API文档、使用文档）
- **任务 6.1**、**6.2** 可以并行进行（测试覆盖率和性能测试）

## 关键路径

关键路径上的任务决定了最短完成时间：
1.1 → 1.2 → 2.1 → 2.2 → 2.3 → 3.1 → 3.2 → 3.3 → 3.4 → 4.1 → 4.2 → 4.3 → 4.4 → 4.5 → 5.1 → 5.2 → 6.1 → 6.3 → 7.1 → 7.2 → 7.3 → 7.4
