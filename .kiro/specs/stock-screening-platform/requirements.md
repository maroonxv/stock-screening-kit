# 需求文档

## 简介

本文档定义了"股票投研工作流定制化平台"MVP 阶段的需求，聚焦于 Stock Screening Context（筛选上下文）的完整搭建。平台采用 DDD 分层架构，前端 React.js + Ant Design，后端 Python Flask + SQLAlchemy，数据库 PostgreSQL，前后端通过 RESTful API 交互。本阶段目标是搭建可运行的项目骨架，实现筛选策略的创建、执行、历史查看和自选股管理的核心链路。

## 术语表

- **Platform（平台）**: 股票投研工作流定制化平台的整体系统
- **Screening_Context（筛选上下文）**: 负责股票筛选策略的定义、执行和结果管理的限界上下文
- **Shared_Kernel（共享内核）**: 跨上下文共享的值对象和接口定义
- **Domain_Layer（领域层）**: 包含聚合根、实体、值对象、枚举和领域服务接口，不依赖任何技术框架
- **Infrastructure_Layer（基础设施层）**: 包含 Repository 实现、ORM 模型、数据源适配器
- **Application_Layer（应用层）**: 编排领域对象，管理事务
- **Interface_Layer（接口层）**: Flask Controller 和 DTO
- **ScreeningStrategy（筛选策略）**: 聚合根，定义筛选条件和评分配置
- **ScreeningSession（筛选会话）**: 聚合根，记录某次筛选的执行结果
- **WatchList（自选股列表）**: 聚合根，管理用户关注的股票
- **FilterGroup（筛选条件组）**: 实体，支持 AND/OR/NOT 递归嵌套
- **FilterCondition（筛选条件）**: 值对象，描述单个筛选规则
- **IndicatorValue（指标值）**: Tagged Union 值对象，包含 NumericValue、TextValue、ListValue、RangeValue、TimeSeriesValue
- **ScoringConfig（评分配置）**: 值对象，定义权重和归一化方法
- **ScreeningResult（筛选结果）**: 值对象
- **ScoredStock（带评分股票）**: 值对象
- **StockCode（股票代码）**: A股代码值对象（共享内核）
- **PO（持久化对象）**: ORM 映射的数据库模型
- **Repository（仓储）**: 领域层定义接口，基础设施层实现

## 需求

### 需求 1：项目结构与共享内核

**用户故事：** 作为开发者，我希望项目具有清晰的 DDD 目录结构和共享内核，以便代码库可维护且遵循领域驱动设计原则。

#### 验收标准

1. THE Platform SHALL 将后端代码组织为 `shared_kernel/`、`contexts/screening/` 目录，遵循 DDD 分层架构（interface、application、domain、infrastructure）
2. THE Platform SHALL 将前端代码组织为 `frontend/src/`，采用基于功能的目录结构
3. THE Shared_Kernel SHALL 提供 `StockCode` 值对象，验证 A 股代码格式（6 位数字字符串，带交易所后缀）
4. THE Shared_Kernel SHALL 提供 `IMarketDataRepository` 抽象接口，包含查询股票数据的方法
5. WHEN 使用无效格式构造 `StockCode` 时, THEN THE Shared_Kernel SHALL 抛出验证错误

### 需求 2：领域层 - 聚合根与实体

**用户故事：** 作为开发者，我希望领域层包含所有聚合根、实体和值对象，以便业务逻辑被封装且独立于基础设施。

#### 验收标准

1. THE Domain_Layer SHALL 实现 `ScreeningStrategy` 聚合根，包含属性：strategy_id、name、description、filters、scoring_config、tags、is_template、created_at、updated_at
2. THE Domain_Layer SHALL 实现 `ScreeningSession` 聚合根，包含属性：session_id、strategy_id、strategy_name、executed_at、total_scanned、execution_time、top_stocks、other_stock_codes、filters_snapshot、scoring_config_snapshot
3. THE Domain_Layer SHALL 实现 `WatchList` 聚合根，包含属性：watchlist_id、name、description、stocks、created_at、updated_at
4. THE Domain_Layer SHALL 实现 `FilterGroup` 实体，支持 AND/OR/NOT 逻辑运算符的递归结构
5. THE Domain_Layer SHALL 实现 `Stock` 实体，包含财务指标属性（roe、pe、pb、eps、revenue、net_profit、debt_ratio、market_cap 等）
6. WHEN 使用空名称创建 `ScreeningStrategy` 时, THEN THE Domain_Layer SHALL 抛出验证错误
7. WHEN 使用不包含任何条件的 filters 创建 `ScreeningStrategy` 时, THEN THE Domain_Layer SHALL 抛出验证错误
8. WHEN 对已存在的 stock_code 调用 `WatchList.add_stock()` 时, THEN THE Domain_Layer SHALL 抛出 `DuplicateStockError`
9. WHEN 对不存在的 stock_code 调用 `WatchList.remove_stock()` 时, THEN THE Domain_Layer SHALL 抛出 `StockNotFoundError`

### 需求 3：领域层 - 值对象

**用户故事：** 作为开发者，我希望拥有不可变的值对象用于筛选条件、指标值和评分配置，以便领域不变量在构造时即被强制执行。

#### 验收标准

1. THE Domain_Layer SHALL 实现 `FilterCondition` 值对象，包含 field（IndicatorField）、operator（ComparisonOperator）和 value（IndicatorValue）
2. THE Domain_Layer SHALL 实现 `IndicatorValue` 作为 Tagged Union，包含子类型：NumericValue、TextValue、ListValue、RangeValue、TimeSeriesValue
3. THE Domain_Layer SHALL 实现 `ScoringConfig` 值对象，包含 weights（IndicatorField 到 float 的映射）和 normalization_method
4. THE Domain_Layer SHALL 实现 `ScreeningResult` 值对象，包含 matched_stocks、total_scanned、execution_time、filters_applied、scoring_config、timestamp
5. THE Domain_Layer SHALL 实现 `ScoredStock` 值对象，包含 stock_code、stock_name、score、score_breakdown、indicator_values、matched_conditions
6. THE Domain_Layer SHALL 实现 `WatchedStock` 值对象，包含 stock_code、stock_name、added_at、note、tags
7. THE Domain_Layer SHALL 实现标识符值对象：StrategyId、SessionId、WatchListId，带 UUID 验证
8. WHEN 使用权重之和不等于 1.0 的 weights 构造 `ScoringConfig` 时, THEN THE Domain_Layer SHALL 抛出验证错误
9. WHEN 使用不匹配的 field value_type 和 IndicatorValue 类型构造 `FilterCondition` 时, THEN THE Domain_Layer SHALL 抛出 TypeError
10. WHEN 使用 min 大于 max 的值构造 `RangeValue` 时, THEN THE Domain_Layer SHALL 抛出验证错误
11. THE FilterCondition SHALL 支持通过 `to_dict()` 序列化为字典，通过 `from_dict()` 反序列化
12. THE FilterGroup SHALL 支持通过 `to_dict()` 序列化为字典，通过 `from_dict()` 反序列化

### 需求 4：领域层 - 枚举与领域服务接口

**用户故事：** 作为开发者，我希望拥有定义良好的枚举和领域服务接口，以便指标类型、运算符和评分逻辑被清晰规定。

#### 验收标准

1. THE Domain_Layer SHALL 实现 `IndicatorField` 枚举，带元数据（name、category、value_type、description），覆盖基础指标（ROE、PE、PB 等）、时间序列指标（ROE_CONTINUOUS_GROWTH_YEARS、REVENUE_CAGR_3Y 等）和衍生指标（PE_PB_RATIO、PEG 等）
2. THE Domain_Layer SHALL 实现 `ComparisonOperator` 枚举，带 `apply()` 方法执行实际值与期望值的比较
3. THE Domain_Layer SHALL 实现 `LogicalOperator`、`IndicatorCategory`、`ValueType` 和 `NormalizationMethod` 枚举
4. THE Domain_Layer SHALL 定义 `IScoringService` 接口，包含 `score_stocks()` 方法
5. THE Domain_Layer SHALL 定义 `IIndicatorCalculationService` 接口，包含 `calculate_indicator()`、`validate_derived_indicator()` 和 `calculate_batch()` 方法
6. WHEN 使用 GREATER_THAN 和 NumericValue 调用 `ComparisonOperator.apply()` 时, THEN THE Domain_Layer SHALL 在实际值超过期望值时返回 True
7. WHEN 使用 IN 和 ListValue 调用 `ComparisonOperator.apply()` 时, THEN THE Domain_Layer SHALL 在实际值包含在列表中时返回 True
8. WHEN 使用 BETWEEN 和 RangeValue 调用 `ComparisonOperator.apply()` 时, THEN THE Domain_Layer SHALL 在实际值落在区间内（含边界）时返回 True

### 需求 5：领域层 - 筛选执行逻辑

**用户故事：** 作为开发者，我希望筛选策略能对候选股票执行过滤和评分，以便核心业务工作流在领域层中实现。

#### 验收标准

1. WHEN 使用 stock 和 calc_service 调用 `FilterCondition.evaluate()` 时, THEN THE Domain_Layer SHALL 计算指标值并应用比较运算符
2. WHEN `FilterCondition.evaluate()` 遇到 None 指标值（数据缺失）时, THEN THE Domain_Layer SHALL 返回 False
3. WHEN 使用 AND 运算符调用 `FilterGroup.match()` 时, THEN THE Domain_Layer SHALL 仅在所有条件和子组都匹配时返回 True
4. WHEN 使用 OR 运算符调用 `FilterGroup.match()` 时, THEN THE Domain_Layer SHALL 在至少一个条件或子组匹配时返回 True
5. WHEN 使用 NOT 运算符调用 `FilterGroup.match()` 时, THEN THE Domain_Layer SHALL 对单个子元素的结果取反
6. WHEN 调用 `ScreeningStrategy.execute()` 时, THEN THE Domain_Layer SHALL 过滤候选股票、对匹配股票评分、按分数降序排序，并返回 ScreeningResult

### 需求 6：基础设施层 - 持久化

**用户故事：** 作为开发者，我希望拥有 SQLAlchemy ORM 模型和 Repository 实现，以便领域对象能按照 PO + Repository + DAO 模式持久化到 PostgreSQL。

#### 验收标准

1. THE Infrastructure_Layer SHALL 实现 SQLAlchemy PO 模型，对应 ScreeningStrategy、ScreeningSession 和 WatchList，包含适当的表结构
2. THE Infrastructure_Layer SHALL 实现 `ScreeningStrategyRepository`，在 ScreeningStrategy 领域对象和 PO 模型之间进行映射
3. THE Infrastructure_Layer SHALL 实现 `ScreeningSessionRepository`，在 ScreeningSession 领域对象和 PO 模型之间进行映射
4. THE Infrastructure_Layer SHALL 实现 `WatchListRepository`，在 WatchList 领域对象和 PO 模型之间进行映射
5. THE Infrastructure_Layer SHALL 使用 PostgreSQL 的 JSONB 存储 FilterGroup，以支持灵活的嵌套结构
6. THE Infrastructure_Layer SHALL 使用 JSONB 列存储 ScreeningSession 中的 top_stocks 和 other_stock_codes
7. WHEN 保存 ScreeningStrategy 后按 ID 检索时, THEN THE Infrastructure_Layer SHALL 返回等价的领域对象，包含所有嵌套的 FilterGroup

### 需求 7：应用层服务

**用户故事：** 作为开发者，我希望应用层服务能编排领域对象并管理事务，以便用例被正确协调。

#### 验收标准

1. THE Application_Layer SHALL 实现 `ScreeningStrategyService`，包含方法：create_strategy、update_strategy、delete_strategy、get_strategy、list_strategies、execute_strategy
2. THE Application_Layer SHALL 实现 `WatchListService`，包含方法：create_watchlist、add_stock、remove_stock、get_watchlist、list_watchlists
3. WHEN 调用 `execute_strategy` 时, THEN THE Application_Layer SHALL 加载候选股票、调用 ScreeningStrategy.execute()、创建 ScreeningSession、持久化会话并返回结果
4. WHEN 使用重复名称调用 `create_strategy` 时, THEN THE Application_Layer SHALL 抛出适当的错误

### 需求 8：接口层 - RESTful API

**用户故事：** 作为开发者，我希望拥有 Flask RESTful API 端点用于筛选操作，以便前端能与后端交互。

#### 验收标准

1. THE Interface_Layer SHALL 暴露 `POST /api/screening/strategies` 用于创建新的筛选策略
2. THE Interface_Layer SHALL 暴露 `GET /api/screening/strategies` 用于分页列出所有策略
3. THE Interface_Layer SHALL 暴露 `GET /api/screening/strategies/<id>` 用于按 ID 获取策略
4. THE Interface_Layer SHALL 暴露 `PUT /api/screening/strategies/<id>` 用于更新策略
5. THE Interface_Layer SHALL 暴露 `DELETE /api/screening/strategies/<id>` 用于删除策略
6. THE Interface_Layer SHALL 暴露 `POST /api/screening/strategies/<id>/execute` 用于执行策略并返回结果
7. THE Interface_Layer SHALL 暴露 `GET /api/screening/sessions` 用于列出最近的筛选会话
8. THE Interface_Layer SHALL 暴露 `GET /api/screening/sessions/<id>` 用于获取会话详情
9. THE Interface_Layer SHALL 暴露 WatchList 的 CRUD 端点，路径为 `/api/screening/watchlists`
10. THE Interface_Layer SHALL 实现 DTO 类用于请求验证和响应格式化
11. WHEN API 请求包含无效数据时, THEN THE Interface_Layer SHALL 返回 HTTP 400 和描述性错误信息
12. WHEN 请求的资源不存在时, THEN THE Interface_Layer SHALL 返回 HTTP 404

### 需求 9：前端基础框架

**用户故事：** 作为开发者，我希望拥有基于 React.js 和 Ant Design 的前端，以便用户能通过 Web 界面与筛选系统交互。

#### 验收标准

1. THE Platform SHALL 提供使用 Vite 引导的 React.js 前端，并配置 Ant Design 组件库
2. THE Platform SHALL 实现基础布局，包含侧边栏导航和主内容区域
3. THE Platform SHALL 实现基于 Axios 的 API 服务层，用于与 Flask 后端通信
4. THE Platform SHALL 实现筛选策略列表页面，展示来自 API 的策略数据
5. THE Platform SHALL 实现筛选策略创建表单，包含筛选条件构建器
6. THE Platform SHALL 实现筛选结果展示页面，以表格形式展示带评分的股票

### 需求 10：基础配置与部署

**用户故事：** 作为开发者，我希望拥有 Docker Compose 配置和项目初始化设置，以便开发环境能通过一条命令启动。

#### 验收标准

1. THE Platform SHALL 提供 `docker-compose.yml`，包含 Flask 应用、PostgreSQL 和 Redis 服务
2. THE Platform SHALL 提供 `requirements.txt`，包含所有 Python 依赖（Flask、SQLAlchemy、psycopg2、redis 等）
3. THE Platform SHALL 提供 Flask 应用入口（`app.py`），注册蓝图并初始化数据库
4. THE Platform SHALL 提供 `config.py`，包含基于环境的配置（development、testing、production）
5. THE Platform SHALL 提供基于 Flask-Migrate（Alembic）的数据库迁移支持
6. WHEN 执行 `docker-compose up` 时, THEN THE Platform SHALL 启动所有服务，应用可被访问
