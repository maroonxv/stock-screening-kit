# 实现计划：真实服务集成（Real Service Integration）

## 概述

将前端"快速行业认知"和"概念可信度验证"页面从 mock 实现切换为调用真实后端 API，接入 WebSocket 实时进度，并增强后端配置验证。前端 API 服务层和后端全栈已就绪，核心工作是前端页面组件改造和 WebSocket 事件补全。

## Tasks

- [x] 1. 扩展 WebSocket 客户端支持 task_failed 事件
  - [x] 1.1 在 `src/frontend/src/services/intelligenceApi.js` 中添加 `task_failed` 事件支持
    - 在 `eventCallbacks` 对象中添加 `task_failed: []`
    - 在 `connectWebSocket` 函数中添加 `socket.on('task_failed', ...)` 监听
    - 导出 `onTaskFailed` 订阅函数（与 `onTaskProgress`/`onTaskCompleted` 同模式）
    - 将 `onTaskFailed` 添加到 `intelligenceWebSocket` 对象中
    - _Requirements: 3.5_

- [x] 2. 改造 IndustryResearchPage 接入真实 API 和 WebSocket
  - [x] 2.1 重写 `src/frontend/src/pages/IndustryResearchPage.jsx` 的 `handleSubmit` 函数
    - 导入 `intelligenceApi`、`connectWebSocket`、`joinTaskRoom`、`leaveTaskRoom`、`onTaskProgress`、`onTaskCompleted`、`onTaskFailed`、`disconnectWebSocket`
    - 将 `handleSubmit` 改为 `async` 函数
    - 调用 `intelligenceApi.createIndustryResearch(trimmedQuery)` 获取 `task_id`
    - 成功后调用 `connectWebSocket()` 和 `joinTaskRoom(taskId)`
    - 移除 `simulateTaskProgress()` 函数和 `getMockResult()` 函数
    - 移除 `simulateTaskProgress` 的 `useCallback` 依赖
    - _Requirements: 1.1, 1.2_
  - [x] 2.2 添加 WebSocket 事件订阅的 `useEffect`
    - 当 `taskId` 存在且 `taskStatus === RUNNING` 时订阅 `task_progress`、`task_completed`、`task_failed` 事件
    - `task_progress` 回调：更新 `progress` 和累积更新 `agentSteps`（已存在的 agent_name 更新，不存在的追加）
    - `task_completed` 回调：设置 `progress=100`、`result=data.result`、`taskStatus=COMPLETED`，调用 `leaveTaskRoom`
    - `task_failed` 回调：设置 `error=data.error`、`taskStatus=FAILED`，调用 `leaveTaskRoom`
    - 所有回调需过滤 `data.task_id !== taskId` 的事件
    - cleanup 函数中取消所有订阅
    - _Requirements: 3.2, 3.3, 3.4, 3.5_
  - [x] 2.3 添加组件卸载时的 WebSocket 清理逻辑
    - 使用 `useEffect` 返回 cleanup 函数，调用 `leaveTaskRoom` 和 `disconnectWebSocket`
    - _Requirements: 3.6_
  - [x] 2.4 编写 IndustryResearchPage 单元测试
    - 测试提交查询后调用正确的 API
    - 测试 API 错误时展示错误信息
    - 测试 WebSocket 事件更新组件状态
    - **Property 1: 行业认知 API 调用正确性**
    - **Validates: Requirements 1.1**

- [x] 3. 改造 CredibilityVerificationPage 接入真实 API 和 WebSocket
  - [x] 3.1 重写 `src/frontend/src/pages/CredibilityVerificationPage.jsx` 的 `handleSubmit` 函数
    - 导入 `intelligenceApi`、`connectWebSocket`、`joinTaskRoom`、`leaveTaskRoom`、`onTaskProgress`、`onTaskCompleted`、`onTaskFailed`、`disconnectWebSocket`
    - 将 `handleSubmit` 改为 `async` 函数
    - 调用 `intelligenceApi.createCredibilityVerification(stockCode, concept)` 获取 `task_id`
    - 成功后调用 `connectWebSocket()` 和 `joinTaskRoom(taskId)`
    - 移除 `simulateTaskProgress()` 函数和 `getMockResult()` 函数
    - 移除 `simulateTaskProgress` 的 `useCallback` 依赖
    - _Requirements: 2.1, 2.2_
  - [x] 3.2 添加 WebSocket 事件订阅的 `useEffect`
    - 与 IndustryResearchPage 相同模式：订阅 `task_progress`、`task_completed`、`task_failed`
    - 所有回调需过滤 `data.task_id !== taskId` 的事件
    - cleanup 函数中取消所有订阅
    - _Requirements: 3.2, 3.3, 3.4, 3.5_
  - [x] 3.3 添加组件卸载时的 WebSocket 清理逻辑
    - _Requirements: 3.6_
  - [x] 3.4 编写 CredibilityVerificationPage 单元测试
    - **Property 2: 可信度验证 API 调用正确性**
    - **Validates: Requirements 2.1**

- [x] 4. Checkpoint - 确保前端改造完成
  - 确保所有测试通过，ask the user if questions arise.

- [x] 5. 后端 DeepSeek API 配置验证
  - [x] 5.1 在 `src/backend/app.py` 的 `get_intelligence_service` 中添加 API key 缺失警告日志
    - 当 `DEEPSEEK_API_KEY` 为空时，使用 `logger.warning` 输出明确警告
    - _Requirements: 4.1_
  - [x] 5.2 在 `intelligence_controller.py` 的任务创建端点中添加 API key 检查
    - 在 `create_industry_research` 和 `create_credibility_verification` 中检查 DeepSeek API key 是否已配置
    - 未配置时返回 400 错误：`{"error": "DeepSeek API 密钥未配置，请在环境变量中设置 DEEPSEEK_API_KEY"}`
    - _Requirements: 4.2_
  - [x] 5.3 更新 `.env.example` 文件，确保包含所有必需环境变量及说明
    - _Requirements: 4.3_
  - [x] 5.4 编写后端 API key 验证的单元测试
    - 测试 API key 为空时的警告日志
    - 测试 API key 为空时的 400 错误响应
    - _Requirements: 4.1, 4.2_

- [x] 6. Checkpoint - 确保后端配置验证完成
  - 确保所有测试通过，ask the user if questions arise.

- [~] 7. （可选）实现 AKShare 数据源提供者
  - [x] 7.1 创建 `src/backend/contexts/intelligence/infrastructure/data/akshare_news_provider.py`
    - 实现 `INewsDataProvider` 接口
    - 使用 AKShare 的新闻相关 API 获取行业新闻
    - 异常时返回空列表并记录 WARNING 日志
    - _Requirements: 5.1, 5.5_
  - [x] 7.2 创建 `src/backend/contexts/intelligence/infrastructure/data/akshare_announcement_provider.py`
    - 实现 `IAnnouncementDataProvider` 接口
    - 使用 AKShare 的公告相关 API 获取公司公告
    - 异常时返回空列表并记录 WARNING 日志
    - _Requirements: 5.2, 5.5_
  - [x] 7.3 改造行业认知工作流的市场热度分析 Agent，注入新闻数据上下文
    - 在 `_build_market_heat_node` 中接受可选的 `INewsDataProvider` 参数
    - 获取新闻数据后拼接到 LLM prompt 中
    - 数据获取失败时降级为仅使用 LLM 知识
    - _Requirements: 5.3, 5.5_
  - [-] 7.4 改造可信度验证工作流的证据收集 Agent，注入公告数据上下文
    - 在 `_build_evidence_collection_node` 中接受可选的 `IAnnouncementDataProvider` 参数
    - 获取公告数据后拼接到 LLM prompt 中
    - 数据获取失败时降级为仅使用 LLM 知识
    - _Requirements: 5.4, 5.5_
  - [~] 7.5 在 `app.py` 的 `get_intelligence_service` 中注入数据提供者
    - 创建 AKShare 数据提供者实例并注入到工作流服务中
    - _Requirements: 5.1, 5.2_
  - [~] 7.6 编写数据提供者和工作流增强的单元测试
    - **Property 7: 外部数据上下文注入**
    - **Validates: Requirements 5.3, 5.4**

- [x] 8. Final checkpoint - 确保所有功能完成
  - 确保所有测试通过，ask the user if questions arise.

## 用户需要提供的配置

| 配置项 | 环境变量 | 必需 | 说明 |
|-------|---------|------|------|
| DeepSeek API 密钥 | `DEEPSEEK_API_KEY` | 是 | 在 `deploy/.env` 中设置，用于调用 DeepSeek LLM |
| DeepSeek API 地址 | `DEEPSEEK_BASE_URL` | 否 | 默认 `https://api.deepseek.com/v1` |
| DeepSeek 模型 | `DEEPSEEK_MODEL` | 否 | 默认 `deepseek-chat` |

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Task 7 整体为可选增强，可在核心功能（Tasks 1-6）完成后再实施
- 后端 API、工作流、WebSocket 推送器均已实现，无需修改
- 前端结果渲染组件（IndustryInsightResult、CredibilityReportResult）无需修改，因为后端数据格式与 mock 格式一致
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
