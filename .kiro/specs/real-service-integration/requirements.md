# 需求文档：真实服务集成（Real Service Integration）

## 简介

将"快速行业认知"和"概念可信度验证"两个功能页面从前端 mock 实现切换为调用真实后端 API，并通过 WebSocket 接收实时任务进度。同时确保后端 DeepSeek API 配置正确可用，可选增强接入真实外部数据源（新闻、公告）以提升工作流分析质量。

## 术语表

- **IndustryResearchPage**：快速行业认知前端页面组件，负责用户输入行业查询并展示分析结果
- **CredibilityVerificationPage**：概念可信度验证前端页面组件，负责用户输入股票代码和概念并展示验证结果
- **intelligenceApi**：前端 API 服务层模块（`intelligenceApi.js`），封装了 REST API 调用和 WebSocket 连接管理
- **WebSocket_Client**：前端 WebSocket 连接管理器，基于 Socket.IO 实现，用于接收任务进度和完成事件
- **Backend_API**：后端 Flask REST API 端点，已实现任务创建、查询、取消等功能
- **DeepSeek_Client**：后端 DeepSeek LLM 客户端，负责调用 DeepSeek API 生成分析结果
- **INewsDataProvider**：领域层新闻数据提供者接口，定义 `fetch_news` 方法
- **IAnnouncementDataProvider**：领域层公告数据提供者接口，定义 `fetch_announcements` 方法
- **AKShare**：开源 A 股数据接口库，已在 shared_kernel 中集成

## 需求

### 需求 1：快速行业认知页面接入真实 API

**用户故事：** 作为投研用户，我希望在快速行业认知页面提交查询后能调用真实后端 API 执行 LangGraph 工作流分析，以获得基于 DeepSeek LLM 的真实行业分析结果。

#### 验收标准

1. WHEN 用户在 IndustryResearchPage 输入查询并提交, THE IndustryResearchPage SHALL 调用 `intelligenceApi.createIndustryResearch(query)` 创建真实任务并获取返回的 `task_id`
2. WHEN 任务创建成功, THE IndustryResearchPage SHALL 移除 `simulateTaskProgress()` 和 `getMockResult()` 等所有 mock 逻辑
3. WHEN 任务创建 API 返回错误, THE IndustryResearchPage SHALL 将任务状态设为 FAILED 并展示后端返回的错误信息
4. WHEN 任务完成后收到结果数据, THE IndustryResearchPage SHALL 使用后端返回的真实 `IndustryInsight` 数据渲染结果展示区域

### 需求 2：概念可信度验证页面接入真实 API

**用户故事：** 作为投研用户，我希望在概念可信度验证页面提交股票代码和概念后能调用真实后端 API 执行可信度验证工作流，以获得基于 DeepSeek LLM 的真实可信度报告。

#### 验收标准

1. WHEN 用户在 CredibilityVerificationPage 输入股票代码和概念并提交, THE CredibilityVerificationPage SHALL 调用 `intelligenceApi.createCredibilityVerification(stockCode, concept)` 创建真实任务并获取返回的 `task_id`
2. WHEN 任务创建成功, THE CredibilityVerificationPage SHALL 移除 `simulateTaskProgress()` 和 `getMockResult()` 等所有 mock 逻辑
3. WHEN 任务创建 API 返回错误, THE CredibilityVerificationPage SHALL 将任务状态设为 FAILED 并展示后端返回的错误信息
4. WHEN 任务完成后收到结果数据, THE CredibilityVerificationPage SHALL 使用后端返回的真实 `CredibilityReport` 数据渲染结果展示区域

### 需求 3：WebSocket 实时进度接收

**用户故事：** 作为投研用户，我希望在任务执行过程中能通过 WebSocket 实时看到各 Agent 的执行进度，而不是看到模拟的进度动画。

#### 验收标准

1. WHEN IndustryResearchPage 或 CredibilityVerificationPage 组件挂载时, THE WebSocket_Client SHALL 建立与后端 `/intelligence` 命名空间的 Socket.IO 连接
2. WHEN 任务创建成功并获得 `task_id`, THE WebSocket_Client SHALL 通过 `joinTaskRoom(taskId)` 加入对应任务房间以接收该任务的事件
3. WHEN 收到 `task_progress` 事件, THE 页面组件 SHALL 更新进度百分比和 Agent 步骤状态（agent_name、status、output_summary）
4. WHEN 收到 `task_completed` 事件, THE 页面组件 SHALL 将任务状态设为 COMPLETED 并使用事件中的 `result` 数据渲染结果
5. WHEN 收到 `task_failed` 事件, THE 页面组件 SHALL 将任务状态设为 FAILED 并展示事件中的错误信息
6. WHEN 组件卸载时, THE WebSocket_Client SHALL 通过 `leaveTaskRoom(taskId)` 离开任务房间并断开连接以避免资源泄漏
7. WHEN WebSocket 连接失败或断开, THE 页面组件 SHALL 展示连接状态提示并支持自动重连

### 需求 4：DeepSeek API 配置验证

**用户故事：** 作为系统部署者，我希望系统能在启动时验证 DeepSeek API 密钥是否已配置，以便在配置缺失时获得明确提示。

#### 验收标准

1. WHEN 后端应用启动且 `DEEPSEEK_API_KEY` 环境变量为空, THE Backend_API SHALL 在日志中输出警告信息提示 API 密钥未配置
2. WHEN 用户提交任务但 `DEEPSEEK_API_KEY` 未配置, THE Backend_API SHALL 返回明确的错误信息告知用户需要配置 API 密钥
3. THE 部署配置 SHALL 在 `.env.example` 中记录所有必需的环境变量及其说明

### 需求 5（可选）：接入 AKShare 真实数据源增强工作流

**用户故事：** 作为投研用户，我希望工作流 Agent 能获取真实的新闻和公告数据，而不是完全依赖 LLM 的训练知识，以提升分析结果的时效性和准确性。

#### 验收标准

1. WHERE 系统启用真实数据源增强, THE INewsDataProvider 的实现 SHALL 通过 AKShare 获取与查询相关的近期新闻数据
2. WHERE 系统启用真实数据源增强, THE IAnnouncementDataProvider 的实现 SHALL 通过 AKShare 获取指定股票的近期公告数据
3. WHERE 真实数据源可用, THE 行业认知工作流的市场热度分析 Agent SHALL 将获取到的新闻数据作为上下文传递给 DeepSeek LLM 以增强分析质量
4. WHERE 真实数据源可用, THE 可信度验证工作流的证据收集 Agent SHALL 将获取到的公告数据作为上下文传递给 DeepSeek LLM 以增强分析质量
5. IF AKShare 数据获取失败, THEN THE 工作流 Agent SHALL 降级为仅使用 LLM 知识进行分析并在日志中记录警告
