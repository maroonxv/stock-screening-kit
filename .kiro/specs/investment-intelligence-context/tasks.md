# 实现计划：智能分析上下文（Investment Intelligence Context）

## 概述

基于已批准的需求和设计文档，将智能分析上下文的实现分解为增量式编码任务。每个任务构建在前一个任务之上，从领域层核心模型开始，逐步扩展到基础设施层、应用层和接口层。测试任务作为子任务嵌入到对应的实现任务中。

## 任务

- [x] 1. 搭建智能分析上下文目录结构和基础文件
  - 在 `src/backend/contexts/intelligence/` 下创建完整的 DDD 四层目录结构
  - 创建所有 `__init__.py` 文件
  - 创建 `domain/exceptions.py`，定义 IntelligenceDomainError、InvalidTaskStateError、TaskNotFoundError、AnalysisTimeoutError、LLMServiceError
  - _Requirements: 4.6_

- [x] 2. 实现领域层枚举
  - [x] 2.1 创建 `domain/enums/enums.py`，实现 TaskType、TaskStatus、AgentStepStatus、RiskLabel 枚举
    - TaskType: INDUSTRY_RESEARCH, CREDIBILITY_VERIFICATION
    - TaskStatus: PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    - AgentStepStatus: PENDING, RUNNING, COMPLETED, FAILED, SKIPPED
    - RiskLabel: PURE_HYPE, WEAK_EVIDENCE, BUSINESS_MISMATCH, HIGH_DEBT, FREQUENT_CONCEPT_CHANGE, SUPPLY_CHAIN_RISK
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 3. 实现领域层值对象
  - [x] 3.1 创建 `domain/value_objects/identifiers.py`，实现 TaskId 值对象
    - UUID 验证、generate() 工厂方法、from_string() 工厂方法、__eq__、__hash__
    - _Requirements: 1.13_
  - [x] 3.2 创建 `domain/value_objects/credibility_score.py`，实现 CredibilityScore 值对象
    - 0-100 整数范围验证、level 属性（高/中/低可信度）、to_dict/from_dict
    - _Requirements: 1.4, 1.12_
  - [x] 3.3 创建 `domain/value_objects/agent_step.py`，实现 AgentStep 值对象
    - 属性：agent_name、status、started_at、completed_at、output_summary、error_message
    - to_dict/from_dict 序列化（datetime 使用 isoformat）
    - _Requirements: 1.6_
  - [x] 3.4 创建 `domain/value_objects/stock_credibility.py`，实现 StockCredibility 值对象
    - 属性：stock_code（StockCode）、stock_name、credibility_score（CredibilityScore）、relevance_summary
    - to_dict/from_dict 序列化
    - _Requirements: 1.5_
  - [x] 3.5 创建 `domain/value_objects/credibility_report.py`，实现 CredibilityReport 及子值对象
    - MainBusinessMatch（score、main_business_description、match_analysis）
    - EvidenceAnalysis（score、patents、orders、partnerships、analysis）
    - HypeHistory（score、past_concepts、analysis）
    - SupplyChainLogic（score、upstream、downstream、analysis）
    - CredibilityReport（stock_code、stock_name、concept、overall_score、四个维度分析、risk_labels、conclusion）
    - 所有值对象实现 to_dict/from_dict
    - _Requirements: 1.3, 1.7, 1.8, 1.9, 1.10_
  - [x] 3.6 创建 `domain/value_objects/industry_insight.py`，实现 IndustryInsight 值对象
    - 属性：industry_name、summary、industry_chain、technology_routes、market_size、top_stocks、risk_alerts、catalysts、heat_score、competitive_landscape
    - to_dict/from_dict 序列化（top_stocks 使用 StockCredibility.to_dict/from_dict）
    - _Requirements: 1.2_
  - [x] 3.7 编写值对象属性测试
    - **Property 1: CredibilityScore 范围验证**
    - **Validates: Requirements 1.4, 1.12**
  - [x] 3.8 编写值对象序列化 round-trip 属性测试
    - **Property 9: 值对象序列化 round-trip**
    - 测试 AgentStep、IndustryInsight、CredibilityReport、CredibilityScore、StockCredibility 的 to_dict/from_dict round-trip
    - **Validates: Requirements 5.3, 5.4**
  - [x] 3.9 编写 TaskId UUID 验证属性测试
    - **Property 3: TaskId UUID 验证一致性**
    - **Validates: Requirements 1.13**

- [x] 4. 实现领域层聚合根 InvestigationTask
  - [x] 4.1 创建 `domain/models/investigation_task.py`，实现 InvestigationTask 聚合根
    - 构造函数：验证 query 非空
    - 状态转换方法：start()、complete(result)、fail(error_message)、cancel()
    - 进度更新：update_progress(progress, agent_step)
    - duration 属性
    - _Requirements: 1.1, 1.11, 3.1-3.8_
  - [x] 4.2 编写 InvestigationTask 状态机属性测试
    - **Property 4: start() 状态机**
    - **Property 5: complete() 状态机**
    - **Property 6: fail/cancel 终态转换**
    - **Validates: Requirements 3.1, 3.2, 3.4, 3.5, 3.6, 3.7**
  - [x] 4.3 编写 InvestigationTask 行为属性测试
    - **Property 2: 空查询文本拒绝**
    - **Property 7: update_progress 追加步骤不变量**
    - **Property 8: duration 计算一致性**
    - **Validates: Requirements 1.11, 3.3, 3.8**

- [x] 5. 实现领域层服务接口和 Repository 接口
  - [x] 5.1 创建 `domain/services/industry_research_service.py`，定义 IIndustryResearchService 抽象接口
    - 异步方法 execute_research(query, progress_callback) -> IndustryInsight
    - _Requirements: 4.1_
  - [x] 5.2 创建 `domain/services/credibility_verification_service.py`，定义 ICredibilityVerificationService 抽象接口
    - 异步方法 verify_credibility(stock_code, concept, progress_callback) -> CredibilityReport
    - _Requirements: 4.2_
  - [x] 5.3 创建 `domain/repositories/investigation_task_repository.py`，定义 IInvestigationTaskRepository 抽象接口
    - 方法：save、find_by_id、find_by_status、find_recent_tasks、delete、count_by_status
    - _Requirements: 4.3_
  - [x] 5.4 创建 `domain/repositories/news_data_provider.py`，定义 INewsDataProvider 接口和 NewsItem 数据类
    - _Requirements: 4.4_
  - [x] 5.5 创建 `domain/repositories/announcement_data_provider.py`，定义 IAnnouncementDataProvider 接口和 Announcement 数据类
    - _Requirements: 4.5_

- [x] 6. Checkpoint - 确保领域层完整
  - 确保所有测试通过，向用户确认领域层实现是否有问题。

- [x] 7. 实现基础设施层持久化
  - [x] 7.1 创建 `infrastructure/persistence/models/investigation_task_po.py`，实现 InvestigationTaskPO SQLAlchemy 模型
    - 表名 investigation_tasks，使用 JSONB 存储 agent_steps 和 result
    - result_type 字段区分 IndustryInsight 和 CredibilityReport
    - _Requirements: 5.1_
  - [x] 7.2 创建 `infrastructure/persistence/repositories/investigation_task_repository_impl.py`，实现 InvestigationTaskRepositoryImpl
    - _to_po 和 _to_domain 双向映射
    - 支持 IndustryInsight 和 CredibilityReport 两种 result 类型的序列化/反序列化
    - _Requirements: 5.2, 5.3, 5.4_
  - [x] 7.3 创建数据库迁移脚本 `migrations/versions/002_intelligence_tables.py`
    - 创建 investigation_tasks 表
    - _Requirements: 5.1_
  - [x] 7.4 编写 Repository round-trip 集成测试
    - **Property 10: InvestigationTask 持久化 round-trip**
    - **Validates: Requirements 5.3**

- [ ] 8. 实现基础设施层 AI 工作流
  - [-] 8.1 创建 `infrastructure/ai/deepseek_client.py`，实现 DeepSeek LLM 客户端
    - 封装 DeepSeek API 调用，支持超时控制和重试
    - _Requirements: 6.4, 10.5_
  - [~] 8.2 创建 `infrastructure/ai/industry_research_workflow.py`，实现快速行业认知 LangGraph 工作流
    - 定义 IndustryResearchState TypedDict
    - 实现 5 个 Agent 节点函数
    - 构建 StateGraph 并配置 Redis checkpointer
    - 实现 IIndustryResearchService 接口
    - _Requirements: 6.1, 6.2, 6.5, 6.7_
  - [~] 8.3 创建 `infrastructure/ai/credibility_workflow.py`，实现概念可信度验证 LangGraph 工作流
    - 分析维度：主营业务匹配、证据收集、历史蹭热点检测、供应链逻辑
    - 实现 ICredibilityVerificationService 接口
    - _Requirements: 6.3, 6.7_
  - [~] 8.4 实现 Agent 失败重试机制
    - LangGraph 节点错误处理，记录错误到 AgentStep
    - Redis checkpoint 支持断点续传
    - _Requirements: 6.6, 10.3_

- [ ] 9. Checkpoint - 确保基础设施层完整
  - 确保所有测试通过，向用户确认基础设施层实现是否有问题。

- [ ] 10. 实现应用层服务
  - [~] 10.1 创建 `application/services/investigation_task_service.py`，实现 InvestigationTaskService
    - create_industry_research_task(query) -> task_id
    - create_credibility_verification_task(stock_code, concept) -> task_id
    - get_task(task_id) -> InvestigationTask
    - list_recent_tasks(limit, offset) -> List[InvestigationTask]
    - cancel_task(task_id)
    - 异步启动工作流，通过回调更新进度和推送 WebSocket 事件
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  - [~] 10.2 编写应用层服务单元测试
    - Mock Repository 和工作流服务
    - 测试任务创建、查询、取消流程
    - _Requirements: 7.1, 7.2, 7.3_

- [ ] 11. 实现接口层
  - [~] 11.1 创建 `interface/dto/task_request_dto.py`，实现请求 DTO
    - IndustryResearchRequest（query 字段验证）
    - CredibilityVerificationRequest（stock_code、concept 字段验证）
    - _Requirements: 8.8_
  - [~] 11.2 创建 `interface/dto/task_response_dto.py`，实现响应 DTO
    - TaskResponseDTO.from_domain(task) -> dict
    - _Requirements: 8.8_
  - [~] 11.3 创建 `interface/controllers/intelligence_controller.py`，实现 Flask Blueprint
    - POST /api/intelligence/tasks/industry-research
    - POST /api/intelligence/tasks/credibility-verification
    - GET /api/intelligence/tasks/<task_id>
    - GET /api/intelligence/tasks
    - POST /api/intelligence/tasks/<task_id>/cancel
    - 错误处理：400（无效数据）、404（任务不存在）、409（状态冲突）
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.9, 8.10_
  - [~] 11.4 实现 WebSocket 事件处理
    - task_progress 事件推送
    - task_completed 事件推送
    - _Requirements: 8.6, 8.7_
  - [~] 11.5 编写接口层集成测试
    - 测试 API 端点的请求/响应
    - 测试无效数据返回 400、不存在资源返回 404
    - _Requirements: 8.9, 8.10_

- [~] 12. 注册 Blueprint 并集成到 Flask 应用
  - 在 `app.py` 中注册 intelligence Blueprint
  - 配置 WebSocket（Flask-SocketIO）
  - 配置依赖注入（Repository、Service 实例化）
  - _Requirements: 8.1-8.7_

- [ ] 13. 实现前端页面
  - [~] 13.1 创建快速行业认知页面组件
    - 查询输入框 + 提交按钮
    - 任务进度展示（各 Agent 状态）
    - 结果展示（行业总结、核心标的列表、风险提示、催化剂）
    - _Requirements: 9.1, 9.2, 9.3_
  - [~] 13.2 创建概念可信度验证页面组件
    - 股票代码 + 概念输入
    - 可信度评分仪表盘
    - 各维度分析详情展示
    - _Requirements: 9.4_
  - [~] 13.3 创建调研任务历史列表页面
    - 任务列表（状态、类型、创建时间）
    - WebSocket 实时更新进度
    - _Requirements: 9.5, 9.6_
  - [~] 13.4 创建前端 API 服务层
    - intelligenceApi：createIndustryResearch、createCredibilityVerification、getTask、listTasks、cancelTask
    - WebSocket 连接管理
    - _Requirements: 9.1-9.6_

- [ ] 14. Final Checkpoint - 确保所有测试通过
  - 确保所有测试通过，向用户确认是否有问题。

## 备注

- 标记 `*` 的任务为可选测试任务，可跳过以加速 MVP 开发
- 每个任务引用了具体的需求编号以确保可追溯性
- Checkpoint 任务确保增量验证
- 属性测试验证通用正确性属性，单元测试验证具体示例和边界情况
