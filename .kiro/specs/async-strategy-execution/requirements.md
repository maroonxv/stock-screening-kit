# 需求文档：异步策略执行

## 简介

本文档定义了筛选策略异步执行功能的需求。当前系统在执行筛选策略时，需要同步获取全市场约 5000+ 只股票的财务数据并进行筛选评分，整个过程耗时可能达到数十分钟，远超 nginx 默认的 60 秒超时限制，导致 504 Gateway Timeout 错误。

本功能将策略执行改为异步模式：前端发起执行请求后立即返回任务 ID，后端在后台线程中执行筛选，前端通过 WebSocket 实时接收进度更新和最终结果。

## 术语表

- **Execution_Task（执行任务）**: 表示一次策略执行的后台任务，包含任务状态、进度和结果
- **Task_Status（任务状态）**: 执行任务的生命周期状态（PENDING、RUNNING、COMPLETED、FAILED、CANCELLED）
- **Progress_Update（进度更新）**: 通过 WebSocket 推送的执行进度信息
- **Background_Executor（后台执行器）**: 负责在后台线程中执行策略的组件
- **WebSocket_Emitter（WebSocket 推送器）**: 负责向前端推送进度和结果的组件
- **Screening_Context（筛选上下文）**: 现有的筛选策略限界上下文

## 需求

### 需求 1：执行任务领域模型

**用户故事：** 作为开发者，我希望有一个执行任务领域模型来跟踪策略执行的状态和进度，以便系统能够管理长时间运行的筛选任务。

#### 验收标准

1. THE Domain_Layer SHALL 实现 `ExecutionTask` 实体，包含属性：task_id、strategy_id、status、progress、total_steps、current_step、result、error_message、created_at、started_at、completed_at
2. THE Domain_Layer SHALL 实现 `TaskStatus` 枚举，包含状态：PENDING、RUNNING、COMPLETED、FAILED、CANCELLED
3. WHEN 创建 ExecutionTask 时, THEN THE Domain_Layer SHALL 将初始状态设为 PENDING，progress 设为 0
4. WHEN 调用 `ExecutionTask.start()` 时, THEN THE Domain_Layer SHALL 将状态从 PENDING 转换为 RUNNING，并记录 started_at
5. WHEN 调用 `ExecutionTask.complete(result)` 时, THEN THE Domain_Layer SHALL 将状态从 RUNNING 转换为 COMPLETED，并记录 result 和 completed_at
6. WHEN 调用 `ExecutionTask.fail(error_message)` 时, THEN THE Domain_Layer SHALL 将状态从 RUNNING 转换为 FAILED，并记录 error_message
7. WHEN 在非法状态下调用状态转换方法时, THEN THE Domain_Layer SHALL 抛出 InvalidTaskStateError

### 需求 2：异步执行 API

**用户故事：** 作为前端开发者，我希望有一个异步执行 API，以便发起策略执行后能立即获得响应，而不必等待整个执行完成。

#### 验收标准

1. THE Interface_Layer SHALL 修改 `POST /api/screening/strategies/<id>/execute` 端点，使其立即返回 task_id 而非等待执行完成
2. THE Interface_Layer SHALL 暴露 `GET /api/screening/tasks/<task_id>` 端点，用于查询任务状态和结果
3. THE Interface_Layer SHALL 暴露 `GET /api/screening/tasks` 端点，用于列出当前用户的执行任务
4. THE Interface_Layer SHALL 暴露 `POST /api/screening/tasks/<task_id>/cancel` 端点，用于取消正在执行的任务
5. WHEN 调用 execute 端点时, THEN THE Interface_Layer SHALL 返回 HTTP 202 Accepted 和 task_id
6. WHEN 查询已完成任务时, THEN THE Interface_Layer SHALL 返回完整的筛选结果
7. WHEN 查询不存在的任务时, THEN THE Interface_Layer SHALL 返回 HTTP 404

### 需求 3：后台执行器

**用户故事：** 作为系统，我希望有一个后台执行器来异步执行策略筛选，以便不阻塞 HTTP 请求线程。

#### 验收标准

1. THE Infrastructure_Layer SHALL 实现 `BackgroundExecutor` 组件，使用线程池执行策略筛选任务
2. WHEN 提交任务到 BackgroundExecutor 时, THEN THE Infrastructure_Layer SHALL 立即返回，任务在后台线程中执行
3. WHILE 任务执行过程中, THE BackgroundExecutor SHALL 定期更新 ExecutionTask 的 progress 和 current_step
4. WHEN 任务执行完成时, THEN THE BackgroundExecutor SHALL 调用 ExecutionTask.complete() 并持久化结果
5. WHEN 任务执行失败时, THEN THE BackgroundExecutor SHALL 调用 ExecutionTask.fail() 并记录错误信息
6. THE BackgroundExecutor SHALL 支持任务取消，通过检查取消标志来中断执行

### 需求 4：WebSocket 进度推送

**用户故事：** 作为前端用户，我希望能实时看到策略执行的进度，以便了解执行状态而不必反复轮询。

#### 验收标准

1. THE Interface_Layer SHALL 在 `/screening` 命名空间下提供 WebSocket 连接支持
2. WHEN 任务状态变化时, THEN THE System SHALL 通过 WebSocket 推送 `task_status_changed` 事件
3. WHEN 任务进度更新时, THEN THE System SHALL 通过 WebSocket 推送 `task_progress` 事件，包含 progress、current_step、total_steps
4. WHEN 任务完成时, THEN THE System SHALL 通过 WebSocket 推送 `task_completed` 事件，包含筛选结果摘要
5. WHEN 任务失败时, THEN THE System SHALL 通过 WebSocket 推送 `task_failed` 事件，包含错误信息
6. THE WebSocket 事件 SHALL 包含 task_id 以便前端识别对应的任务

### 需求 5：执行进度跟踪

**用户故事：** 作为系统，我希望能够跟踪策略执行的详细进度，以便向用户提供有意义的进度信息。

#### 验收标准

1. THE System SHALL 将策略执行分解为可跟踪的步骤：获取股票列表、获取股票数据、执行筛选、计算评分、保存结果
2. WHEN 获取股票数据时, THE System SHALL 报告已获取的股票数量占总数的百分比
3. WHEN 执行筛选时, THE System SHALL 报告已筛选的股票数量占总数的百分比
4. THE Progress_Update SHALL 包含字段：phase（当前阶段）、progress（0-100）、message（可读描述）、details（可选的详细信息）

### 需求 6：Nginx 超时配置

**用户故事：** 作为运维人员，我希望 nginx 配置能支持长时间运行的 WebSocket 连接，以便前端能持续接收进度更新。

#### 验收标准

1. THE Platform SHALL 配置 nginx 的 `/api/` location 增加 `proxy_read_timeout` 为 300 秒，以支持可能的长轮询场景
2. THE Platform SHALL 确保 `/socket.io/` location 的 `proxy_read_timeout` 保持为 86400 秒以支持 WebSocket 长连接
3. THE Platform SHALL 配置 `proxy_connect_timeout` 和 `proxy_send_timeout` 为合理值

### 需求 7：前端异步执行支持

**用户故事：** 作为前端用户，我希望在执行策略时能看到实时进度，并在完成后自动显示结果。

#### 验收标准

1. THE Frontend SHALL 在调用 execute API 后显示执行进度界面
2. THE Frontend SHALL 建立 WebSocket 连接以接收进度更新
3. WHEN 收到 task_progress 事件时, THEN THE Frontend SHALL 更新进度条和状态文本
4. WHEN 收到 task_completed 事件时, THEN THE Frontend SHALL 自动跳转到结果页面或显示结果
5. WHEN 收到 task_failed 事件时, THEN THE Frontend SHALL 显示错误信息
6. THE Frontend SHALL 提供取消执行的按钮，调用 cancel API

### 需求 8：任务持久化

**用户故事：** 作为系统，我希望执行任务能够持久化，以便在服务重启后能够查询历史任务状态。

#### 验收标准

1. THE Infrastructure_Layer SHALL 实现 `ExecutionTaskRepository`，将 ExecutionTask 持久化到数据库
2. THE Infrastructure_Layer SHALL 实现 `ExecutionTaskPO` 模型，包含所有任务属性
3. WHEN 服务重启时, THE System SHALL 将所有 RUNNING 状态的任务标记为 FAILED（带有"服务重启"错误信息）
4. THE System SHALL 保留最近 100 条执行任务记录，自动清理更早的记录

