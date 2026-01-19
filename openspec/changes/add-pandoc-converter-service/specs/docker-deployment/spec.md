# Spec: Docker部署

## ADDED Requirements

### Requirement: Docker镜像构建

The system MUST provide a buildable Docker image.

系统必须提供可构建的Docker镜像。

**Rationale**: 容器化确保环境一致性和简化部署。

#### Scenario: 镜像包含所有依赖

**Given** Dockerfile存在
**When** 执行docker build
**Then** 镜像包含Python 3.10+运行时
**And** 镜像包含Pandoc可执行文件
**And** 镜像包含LaTeX环境（用于PDF生成）
**And** 镜像包含中文字体支持

#### Scenario: 镜像使用多阶段构建

**Given** 优化镜像大小是目标
**When** 查看Dockerfile
**Then** Dockerfile使用多阶段构建（如果适用）
**And** 清理不必要的构建工具
**And** 最小化镜像层数

#### Scenario: 镜像使用非root用户

**Given** 安全性是关注点
**When** 容器启动
**Then** 应用以非root用户运行
**And** 该用户具有必要的文件权限

#### Scenario: 镜像暴露正确的端口

**Given** 应用监听8000端口
**When** 查看Dockerfile
**Then** EXPOSE指令声明8000端口
**And** 端口与应用配置匹配

---

### Requirement: Docker Compose配置

The system MUST provide a Docker Compose configuration file.

系统必须提供Docker Compose配置文件。

**Rationale**: 简化本地开发和一键部署。

#### Scenario: 一键启动服务

**Given** docker-compose.yml存在
**When** 执行docker-compose up
**Then** 所有服务正确启动
**And** 服务可以在 http://localhost:8000 访问
**And** 健康检查通过

#### Scenario: 端口映射配置正确

**Given** docker-compose.yml配置端口映射
**When** 服务启动
**Then** 容器8000端口映射到主机8000端口
**And** 客户端可以通过主机端口访问

#### Scenario: 环境变量可配置

**Given** docker-compose.yml包含环境变量配置
**When** 服务启动
**Then** 环境变量正确传递给容器
**And** 应用可以读取这些变量

#### Scenario: 开发模式支持代码挂载

**Given** 开发者需要实时修改代码
**When** 使用docker-compose.yml启动开发环境
**Then** src目录以只读方式挂载到容器
**And** 代码修改无需重新构建镜像

#### Scenario: 服务重启策略

**Given** 服务可能崩溃
**When** 容器意外退出
**Then** Docker自动重启容器
**And** 重启策略为unless-stopped

---

### Requirement: 健康检查配置

The system MUST configure container health checks.

系统必须配置容器健康检查。

**Rationale**: 容器编排系统需要知道服务状态。

#### Scenario: 健康检查端点可用

**Given** 容器正在运行
**When** Docker执行健康检查
**Then** 健康检查调用/health端点
**And** 端点返回200状态码表示健康

#### Scenario: 健康检查间隔配置

**Given** docker-compose.yml配置健康检查
**When** 查看配置
**Then** 检查间隔为30秒
**And** 超时时间为10秒
**And** 失败3次后标记为不健康

#### Scenario: 不健康时容器重启

**Given** 连续健康检查失败
**When** 达到重试阈值
**Then** Docker标记容器为不健康
**And** 根据重启策略决定是否重启

---

### Requirement: 日志配置

The system MUST properly configure container logging.

系统必须正确配置容器日志。

**Rationale**: 便于调试和问题追踪。

#### Scenario: 应用日志输出到标准输出

**Given** 应用运行在容器中
**When** 应用产生日志
**Then** 日志输出到stdout
**And** 可以通过docker logs查看

#### Scenario: 日志级别可配置

**Given** 通过环境变量配置
**When** 设置LOG_LEVEL环境变量
**Then** 应用使用指定的日志级别
**And** 支持的级别包括DEBUG, INFO, WARNING, ERROR

#### Scenario: 结构化日志格式

**Given** 需要日志分析
**When** 应用记录日志
**Then** 日志包含时间戳
**And** 日志包含日志级别
**And** 日志包含请求ID（如果有）

---

### Requirement: 资源限制

The system MUST configure appropriate resource limits.

系统必须配置适当的资源限制。

**Rationale**: 防止容器消耗过多主机资源。

#### Scenario: 内存限制配置

**Given** docker-compose.yml配置资源限制
**When** 查看服务配置
**Then** 设置合理的内存限制（推荐1GB）
**And** 设置内存预留值

#### Scenario: CPU限制配置

**Given** 需要限制CPU使用
**When** 查看服务配置
**Then** 可以配置CPU限制（可选）
**And** 可以配置CPU预留值（可选）

---

### Requirement: 网络配置

The system MUST properly configure container networking.

系统必须正确配置容器网络。

**Rationale**: 确保服务可访问性和安全性。

#### Scenario: 容器监听所有接口

**Given** 应用在容器内运行
**When** 应用启动
**Then** 应用监听0.0.0.0:8000
**And** 可以从容器外部访问

#### Scenario: 网络隔离（可选）

**Given** 需要网络隔离
**When** 创建Docker网络
**Then** 服务在独立的网络中运行
**And** 可以配置与其他服务的通信

---

### Requirement: 镜像版本管理

The system MUST support Docker image version management.

系统必须支持镜像版本管理。

**Rationale**: 便于回滚和版本追踪。

#### Scenario: 镜像标签规范

**Given** 构建Docker镜像
**When** 为镜像打标签
**Then** 使用语义化版本号
**And** 提供latest标签指向最新稳定版

#### Scenario: 镜像元数据

**Given** 查看镜像信息
**When** 执行docker inspect
**Then** 镜像包含维护者信息
**And** 镜像包含描述信息
**And** 镜像包含版本标签

---

### Requirement: 本地开发支持

The system MUST support local development workflows.

系统必须支持本地开发工作流。

**Rationale**: 降低开发环境搭建难度。

#### Scenario: 热重载支持

**Given** 开发者修改代码
**When** 保存文件
**Then** 容器内的应用可以检测变化
**And** 无需重新构建容器（可选，取决于实现）

#### Scenario: 依赖安装

**Given** 新开发者加入项目
**When** 需要设置开发环境
**Then** 只需执行docker-compose up
**And** 所有依赖自动安装

#### Scenario: 调试支持

**Given** 开发者需要调试
**When** 启动开发环境
**Then** 可以配置调试端口映射
**And** 可以连接远程调试器（可选）
