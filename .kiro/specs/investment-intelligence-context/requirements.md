# 需求文档

## 简介

本文档定义了"股票投研工作流定制化平台"中 Investment Intelligence Context（智能分析上下文）的需求。该上下文负责 AI 驱动的快速行业认知、概念可信度验证和产业链深度分析。系统采用 DDD 四层架构，后端 Python Flask + SQLAlchemy + PostgreSQL，AI 编排使用 LangGraph + DeepSeek，实时进度推送使用 WebSocket，缓存使用 Redis。本上下文与 Screening Context 通过 Shared Kernel 共享 StockCode 值对象和 IMarketDataRepository 接口，两个上下文之间无运行时依赖。

## 术语表

- **Intelligence_Context（智能分析上下文）**: 负责 AI 驱动的行业认知、概念可信度验证和产业链分析的限界上下文
- **Shared_Kernel（共享内核）**: 跨上下文共享的值对象和接口定义，包含 StockCode 和 IMarketDataRepository
- **Domain_Layer（领域层）**: 包含聚合根、实体、值对象、枚举和领域服务接口，不依赖任何技术框架
- **Infrastructure_Layer（基础设施层）**: 包含 Repository 实现、ORM 模型、LangGraph 工作流、DeepSeek 客户端
- **Application_Layer（应用层）**: 编排领域对象，管理事务，协调 LangGraph 工作流
- **Interface_Layer（接口层）**: Flask Controller、DTO 和 WebSocket 事件处理
- **InvestigationTask（调研任务）**: 聚合根，代表用户发起的一次调研任务（快速行业认知或概念验证）
- **IndustryInsight（行业认知）**: 值对象，快速行业认知工作流的输出结果
- **CredibilityReport（可信度报告）**: 值对象，概念可信度验证的分析结果
- **CredibilityScore（可信度评分）**: 值对象，0-100 的评分加风险标签
- **StockCredibility（个股可信度）**: 值对象，单只股票的可信度分析结果
- **AgentStep（Agent 步骤）**: 值对象，记录 LangGraph 工作流中单个 Agent 的执行状态和输出
- **TaskId（任务标识符）**: 值对象，调研任务的唯一标识
- **StockCode（股票代码）**: A 股代码值对象（来自共享内核）
- **LangGraph**: 多 Agent 工作流编排框架，用于实现 5-Agent 协作工作流
- **DeepSeek**: 国产大语言模型，用于行业分析推理和概念验证
- **WebSocket**: 实时双向通信协议，用于推送任务执行进度
- **PO（持久化对象）**: ORM 映射的数据库模型
- **Repository（仓储）**: 领域层定义接口，基础设施层实现

## 需求

### 需求 1：领域层 - 聚合根与值对象

**用户故事：** 作为开发者，我希望智能分析上下文拥有清晰的领域模型，以便 AI 分析的业务逻辑被封装且独立于基础设施。

#### 验收标准

1. THE Domain_Layer SHALL 实现 `InvestigationTask` 聚合根，包含属性：task_id（TaskId）、task_type（TaskType 枚举）、query（用户输入的查询文本）、status（TaskStatus 枚举）、progress（0-100 整数）、agent_steps（List[AgentStep]）、result（IndustryInsight 或 CredibilityReport，根据 task_type 决定）、error_message（可选）、created_at、updated_at、completed_at（可选）
2. THE Domain_Layer SHALL 实现 `IndustryInsight` 值对象，包含属性：industry_name（行业名称）、summary（行业一页纸总结）、industry_chain（产业链结构描述）、technology_routes（技术路线列表）、market_size（市场规模描述）、top_stocks（List[StockCredibility]，5-10 只核心标的）、risk_alerts（List[str]，风险提示）、catalysts（List[str]，催化剂）、heat_score（市场热度评分 0-100）、competitive_landscape（竞争格局描述）
3. THE Domain_Layer SHALL 实现 `CredibilityReport` 值对象，包含属性：stock_code（StockCode）、stock_name、concept（被验证的概念）、overall_score（CredibilityScore）、main_business_match（MainBusinessMatch 值对象）、evidence（EvidenceAnalysis 值对象）、hype_history（HypeHistory 值对象）、supply_chain_logic（SupplyChainLogic 值对象）、risk_labels（List[RiskLabel] 枚举）、conclusion（总结文本）
4. THE Domain_Layer SHALL 实现 `CredibilityScore` 值对象，包含 score（0-100 整数）属性
5. THE Domain_Layer SHALL 实现 `StockCredibility` 值对象，包含属性：stock_code（StockCode）、stock_name、credibility_score（CredibilityScore）、relevance_summary（相关性摘要）
6. THE Domain_Layer SHALL 实现 `AgentStep` 值对象，包含属性：agent_name（Agent 名称）、status（AgentStepStatus 枚举）、started_at、completed_at（可选）、output_summary（输出摘要，可选）、error_message（可选）
7. THE Domain_Layer SHALL 实现 `MainBusinessMatch` 值对象，包含属性：score（0-100）、main_business_description（主营业务描述）、match_analysis（匹配分析文本）
8. THE Domain_Layer SHALL 实现 `EvidenceAnalysis` 值对象，包含属性：score（0-100）、patents（List[str]，专利列表）、orders（List[str]，订单列表）、partnerships（List[str]，合作伙伴列表）、analysis（分析文本）
9. THE Domain_Layer SHALL 实现 `HypeHistory` 值对象，包含属性：score（0-100，越高越可信，即历史蹭热点越少）、past_concepts（List[str]，历史蹭过的概念列表）、analysis（分析文本）
10. THE Domain_Layer SHALL 实现 `SupplyChainLogic` 值对象，包含属性：score（0-100）、upstream（List[str]，上游环节）、downstream（List[str]，下游环节）、analysis（分析文本）
11. WHEN 使用空查询文本创建 `InvestigationTask` 时, THEN THE Domain_Layer SHALL 抛出验证错误
12. WHEN 使用超出 0-100 范围的值构造 `CredibilityScore` 时, THEN THE Domain_Layer SHALL 抛出验证错误
13. THE Domain_Layer SHALL 实现标识符值对象 `TaskId`，带 UUID 验证和工厂方法（generate、from_string）

### 需求 2：领域层 - 枚举定义

**用户故事：** 作为开发者，我希望拥有定义良好的枚举类型，以便任务类型、状态和风险标签被清晰规定。

#### 验收标准

1. THE Domain_Layer SHALL 实现 `TaskType` 枚举，包含值：INDUSTRY_RESEARCH（快速行业认知）、CREDIBILITY_VERIFICATION（概念可信度验证）
2. THE Domain_Layer SHALL 实现 `TaskStatus` 枚举，包含值：PENDING（等待中）、RUNNING（执行中）、COMPLETED（已完成）、FAILED（失败）、CANCELLED（已取消）
3. THE Domain_Layer SHALL 实现 `AgentStepStatus` 枚举，包含值：PENDING（等待中）、RUNNING（执行中）、COMPLETED（已完成）、FAILED（失败）、SKIPPED（跳过）
4. THE Domain_Layer SHALL 实现 `RiskLabel` 枚举，包含值：PURE_HYPE（纯蹭热点）、WEAK_EVIDENCE（证据不足）、BUSINESS_MISMATCH（主业不匹配）、HIGH_DEBT（高负债风险）、FREQUENT_CONCEPT_CHANGE（频繁概念切换）、SUPPLY_CHAIN_RISK（供应链风险）

### 需求 3：领域层 - InvestigationTask 行为

**用户故事：** 作为开发者，我希望 InvestigationTask 聚合根封装任务生命周期管理逻辑，以便任务状态转换和进度更新在领域层中被正确控制。

#### 验收标准

1. WHEN 调用 `InvestigationTask.start()` 时, THEN THE Domain_Layer SHALL 将 status 从 PENDING 转换为 RUNNING，并记录开始时间
2. WHEN 在非 PENDING 状态调用 `InvestigationTask.start()` 时, THEN THE Domain_Layer SHALL 抛出 InvalidTaskStateError
3. WHEN 调用 `InvestigationTask.update_progress(progress, agent_step)` 时, THEN THE Domain_Layer SHALL 更新 progress 值并追加 agent_step 到 agent_steps 列表
4. WHEN 调用 `InvestigationTask.complete(result)` 时, THEN THE Domain_Layer SHALL 将 status 设为 COMPLETED，保存 result，记录 completed_at，并将 progress 设为 100
5. WHEN 在非 RUNNING 状态调用 `InvestigationTask.complete()` 时, THEN THE Domain_Layer SHALL 抛出 InvalidTaskStateError
6. WHEN 调用 `InvestigationTask.fail(error_message)` 时, THEN THE Domain_Layer SHALL 将 status 设为 FAILED，保存 error_message，并记录 completed_at
7. WHEN 调用 `InvestigationTask.cancel()` 时, THEN THE Domain_Layer SHALL 将 status 设为 CANCELLED，并记录 completed_at
8. THE InvestigationTask SHALL 提供 `duration` 属性，返回从 created_at 到 completed_at 的时间差（任务未完成时返回 None）

### 需求 4：领域层 - 领域服务接口与 Repository 接口

**用户故事：** 作为开发者，我希望领域层定义清晰的服务接口和 Repository 接口，以便基础设施层可以提供具体实现而不污染领域逻辑。

#### 验收标准

1. THE Domain_Layer SHALL 定义 `IIndustryResearchService` 接口，包含 `execute_research(query: str) -> IndustryInsight` 异步方法
2. THE Domain_Layer SHALL 定义 `ICredibilityVerificationService` 接口，包含 `verify_credibility(stock_code: StockCode, concept: str) -> CredibilityReport` 异步方法
3. THE Domain_Layer SHALL 定义 `IInvestigationTaskRepository` 接口，包含方法：save、find_by_id、find_by_status、find_recent_tasks、delete、count_by_status
4. THE Domain_Layer SHALL 定义 `INewsDataProvider` 接口，包含 `fetch_news(query: str, days: int) -> List[NewsItem]` 方法，用于获取新闻数据
5. THE Domain_Layer SHALL 定义 `IAnnouncementDataProvider` 接口，包含 `fetch_announcements(stock_code: StockCode, days: int) -> List[Announcement]` 方法，用于获取公司公告
6. THE Domain_Layer SHALL 在 `exceptions.py` 中定义异常类：IntelligenceDomainError（基类）、InvalidTaskStateError、TaskNotFoundError、AnalysisTimeoutError、LLMServiceError

### 需求 5：基础设施层 - 持久化

**用户故事：** 作为开发者，我希望拥有 SQLAlchemy ORM 模型和 Repository 实现，以便调研任务能持久化到 PostgreSQL。

#### 验收标准

1. THE Infrastructure_Layer SHALL 实现 `InvestigationTaskPO` SQLAlchemy 模型，使用 JSONB 存储 agent_steps 和 result 字段
2. THE Infrastructure_Layer SHALL 实现 `InvestigationTaskRepositoryImpl`，在 InvestigationTask 领域对象和 PO 模型之间进行双向映射
3. WHEN 保存 InvestigationTask 后按 ID 检索时, THEN THE Infrastructure_Layer SHALL 返回等价的领域对象，包含所有嵌套的值对象（AgentStep、IndustryInsight 或 CredibilityReport）
4. THE Infrastructure_Layer SHALL 使用 JSONB 存储 result 字段，支持 IndustryInsight 和 CredibilityReport 两种类型的序列化与反序列化

### 需求 6：基础设施层 - LangGraph 工作流

**用户故事：** 作为开发者，我希望使用 LangGraph 实现 5-Agent 协作工作流，以便快速行业认知能在 30 分钟内完成并提供结构化输出。

#### 验收标准

1. THE Infrastructure_Layer SHALL 实现快速行业认知 LangGraph 工作流，包含 5 个 Agent 节点：行业背景速览、市场热度分析、标的快速筛选、真实性批量验证、竞争格局速览
2. WHEN 工作流执行时, THEN THE Infrastructure_Layer SHALL 按顺序执行 5 个 Agent，每个 Agent 完成后通过回调更新 InvestigationTask 的进度
3. THE Infrastructure_Layer SHALL 实现概念可信度验证工作流，分析维度包括：主营业务匹配度、实质订单/专利证据、历史蹭热点记录、供应链逻辑合理性
4. THE Infrastructure_Layer SHALL 使用 DeepSeek LLM 进行行业分析推理和概念验证
5. THE Infrastructure_Layer SHALL 使用 Redis 持久化 LangGraph 工作流状态，支持断点续传
6. WHEN 某个 Agent 执行失败时, THEN THE Infrastructure_Layer SHALL 记录错误信息并允许从失败点重试
7. THE Infrastructure_Layer SHALL 实现 `IIndustryResearchService` 和 `ICredibilityVerificationService` 接口

### 需求 7：应用层服务

**用户故事：** 作为开发者，我希望应用层服务编排调研任务的创建、执行和查询，以便用例被正确协调。

#### 验收标准

1. THE Application_Layer SHALL 实现 `InvestigationTaskService`，包含方法：create_industry_research_task、create_credibility_verification_task、get_task、list_recent_tasks、cancel_task
2. WHEN 调用 `create_industry_research_task(query)` 时, THEN THE Application_Layer SHALL 创建 InvestigationTask、持久化、异步启动 LangGraph 工作流，并返回 task_id
3. WHEN 调用 `create_credibility_verification_task(stock_code, concept)` 时, THEN THE Application_Layer SHALL 创建 InvestigationTask、持久化、异步启动可信度验证工作流，并返回 task_id
4. WHEN 工作流执行过程中进度更新时, THEN THE Application_Layer SHALL 更新 InvestigationTask 的进度并通过 WebSocket 推送进度事件
5. WHEN 工作流执行完成时, THEN THE Application_Layer SHALL 更新 InvestigationTask 为 COMPLETED 状态并通过 WebSocket 推送完成事件

### 需求 8：接口层 - RESTful API

**用户故事：** 作为开发者，我希望拥有 Flask RESTful API 端点用于智能分析操作，以便前端能与后端交互。

#### 验收标准

1. THE Interface_Layer SHALL 暴露 `POST /api/intelligence/tasks/industry-research` 用于创建快速行业认知任务，请求体包含 query 字段
2. THE Interface_Layer SHALL 暴露 `POST /api/intelligence/tasks/credibility-verification` 用于创建概念可信度验证任务，请求体包含 stock_code 和 concept 字段
3. THE Interface_Layer SHALL 暴露 `GET /api/intelligence/tasks/<task_id>` 用于查询任务详情（包含进度和结果）
4. THE Interface_Layer SHALL 暴露 `GET /api/intelligence/tasks` 用于分页列出最近的调研任务
5. THE Interface_Layer SHALL 暴露 `POST /api/intelligence/tasks/<task_id>/cancel` 用于取消正在执行的任务
6. THE Interface_Layer SHALL 实现 WebSocket 事件 `task_progress` 用于实时推送任务进度更新
7. THE Interface_Layer SHALL 实现 WebSocket 事件 `task_completed` 用于推送任务完成通知
8. THE Interface_Layer SHALL 实现 DTO 类用于请求验证和响应格式化
9. WHEN API 请求包含无效数据时, THEN THE Interface_Layer SHALL 返回 HTTP 400 和描述性错误信息
10. WHEN 请求的任务不存在时, THEN THE Interface_Layer SHALL 返回 HTTP 404

### 需求 9：前端页面

**用户故事：** 作为投资者，我希望通过 Web 界面发起行业认知和概念验证任务，并实时查看分析进度和结果。

#### 验收标准

1. THE Platform SHALL 实现快速行业认知页面，包含查询输入框和提交按钮
2. THE Platform SHALL 实现任务进度展示组件，实时显示各 Agent 的执行状态（等待中/执行中/已完成/失败）
3. THE Platform SHALL 实现行业认知结果展示页面，包含行业总结、核心标的列表（含可信度评分）、风险提示和催化剂
4. THE Platform SHALL 实现概念可信度验证页面，包含股票代码和概念输入，展示可信度评分仪表盘和各维度分析详情
5. THE Platform SHALL 实现调研任务历史列表页面，展示最近的调研任务及其状态
6. WHEN 任务正在执行时, THEN THE Platform SHALL 通过 WebSocket 实时更新进度条和 Agent 状态

### 需求 10：非功能需求

**用户故事：** 作为投资者，我希望 AI 分析任务能在合理时间内完成，并且系统具备容错能力。

#### 验收标准

1. THE Intelligence_Context SHALL 在 30 分钟内完成快速行业认知工作流的全部 5 个 Agent 执行
2. THE Intelligence_Context SHALL 通过 WebSocket 实时推送任务进度，延迟小于 2 秒
3. THE Infrastructure_Layer SHALL 将 LangGraph 工作流状态持久化到 Redis，支持 Agent 失败后从断点恢复
4. THE Infrastructure_Layer SHALL 对外部数据源（新闻爬虫、公告接口）使用依赖倒置，通过接口抽象解耦
5. THE Infrastructure_Layer SHALL 对 DeepSeek API 调用实现超时控制和重试机制
