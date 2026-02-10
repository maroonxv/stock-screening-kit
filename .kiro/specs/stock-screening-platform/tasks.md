# Implementation Plan: Stock Screening Platform MVP

## Overview

从零搭建股票投研工作流定制化平台 MVP，聚焦 Stock Screening Context。后端 Python Flask + SQLAlchemy + PostgreSQL，前端 React.js + Vite + Ant Design。按 DDD 分层架构自底向上实现：共享内核 → 领域层 → 基础设施层 → 应用层 → 接口层 → 前端。

## Tasks

- [x] 1. 项目骨架与共享内核
  - [x] 1.1 创建项目目录结构与配置文件
    - 创建 `src/` 后端目录结构（shared_kernel、contexts/screening 的 interface/application/domain/infrastructure 各层）
    - 创建 `requirements.txt`（Flask、SQLAlchemy、psycopg2-binary、flask-migrate、redis、hypothesis、pytest 等）
    - 创建 `config.py`（development/testing/production 配置）
    - 创建 `app.py` Flask 入口，注册蓝图、初始化数据库
    - 创建 `docker-compose.yml`（Flask、PostgreSQL、Redis 服务）
    - 创建各层 `__init__.py`
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 1.1, 1.2_

  - [x] 1.2 实现共享内核 StockCode 值对象
    - 在 `shared_kernel/value_objects/stock_code.py` 实现 StockCode
    - 正则验证 A 股代码格式（6位数字 + .SH/.SZ）
    - 实现 `code`、`exchange`、`numeric_code` 属性
    - 实现 `__eq__`、`__hash__`、`__repr__`
    - _Requirements: 1.3, 1.5_

  - [x] 1.3 编写 StockCode 属性测试
    - **Property 1: StockCode 格式验证一致性**
    - **Validates: Requirements 1.3, 1.5**

  - [x] 1.4 实现共享内核 IMarketDataRepository 接口
    - 在 `shared_kernel/interfaces/market_data_repository.py` 定义抽象接口
    - 包含 `get_all_stock_codes`、`get_stock`、`get_stocks_by_codes`、`get_last_update_time`、`get_available_industries` 方法
    - _Requirements: 1.4_

- [x] 2. 领域层 - 枚举与值对象
  - [x] 2.1 实现枚举类型
    - 在 `contexts/screening/domain/enums/` 下实现：
      - `enums.py`：LogicalOperator、IndicatorCategory、ValueType、NormalizationMethod
      - `indicator_field.py`：IndicatorField 枚举，带元数据（name、category、value_type、description），覆盖基础/时间序列/衍生指标
      - `comparison_operator.py`：ComparisonOperator 枚举，带 `apply()` 方法
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 2.2 编写 ComparisonOperator.apply 属性测试
    - **Property 8: ComparisonOperator.apply 与原生运算符一致**
    - **Validates: Requirements 4.6, 4.7, 4.8**

  - [x] 2.3 实现 IndicatorValue Tagged Union
    - 在 `contexts/screening/domain/value_objects/indicator_value.py` 实现：
      - 抽象基类 IndicatorValue（to_comparable、to_dict、factory_from_dict）
      - NumericValue（含 NaN/Infinity 验证）
      - TextValue
      - ListValue
      - RangeValue（含 min <= max 验证）
      - TimeSeriesValue
    - _Requirements: 3.2, 3.10_

  - [x] 2.4 实现标识符值对象
    - 在 `contexts/screening/domain/value_objects/identifiers.py` 实现 StrategyId、SessionId、WatchListId
    - 带 UUID 验证、generate() 工厂方法、from_string() 方法
    - _Requirements: 3.7_

  - [x] 2.5 实现 ScoringConfig 值对象
    - 在 `contexts/screening/domain/value_objects/scoring_config.py` 实现
    - 包含 weights（IndicatorField → float 映射）和 normalization_method
    - 验证权重之和等于 1.0（浮点精度容差）
    - 实现 to_dict / from_dict
    - _Requirements: 3.3, 3.8_

  - [x] 2.6 编写 ScoringConfig 权重约束属性测试
    - **Property 4: ScoringConfig 权重之和约束**
    - **Validates: Requirements 3.8**

  - [x] 2.7 实现 FilterCondition 值对象
    - 在 `contexts/screening/domain/value_objects/filter_condition.py` 实现
    - 类型匹配验证（field.value_type 与 IndicatorValue 类型）
    - evaluate() 方法（调用 calc_service 计算指标并应用运算符）
    - to_dict / from_dict 序列化
    - _Requirements: 3.1, 3.9, 3.11, 5.1, 5.2_

  - [x] 2.8 编写 FilterCondition 类型匹配属性测试
    - **Property 5: FilterCondition 类型匹配约束**
    - **Validates: Requirements 3.9**

  - [x] 2.9 编写 FilterCondition 序列化 round-trip 属性测试
    - **Property 6: FilterCondition 序列化 round-trip**
    - **Validates: Requirements 3.11**

  - [x] 2.10 实现 ScoredStock、ScreeningResult、WatchedStock 值对象
    - `scored_stock.py`：stock_code、stock_name、score、score_breakdown、indicator_values、matched_conditions
    - `screening_result.py`：matched_stocks、total_scanned、execution_time、filters_applied、scoring_config、timestamp
    - `watched_stock.py`：stock_code、stock_name、added_at、note、tags
    - _Requirements: 3.4, 3.5, 3.6_

  - [x] 2.11 实现领域异常类
    - 在 `contexts/screening/domain/exceptions.py` 实现所有领域异常
    - DomainError、DuplicateStockError、StockNotFoundError、DuplicateNameError、StrategyNotFoundError、WatchListNotFoundError、ScoringError、IndicatorCalculationError、ValidationError
    - _Requirements: 2.6, 2.7, 2.8, 2.9_

- [x] 3. 领域层 - 实体与聚合根
  - [x] 3.1 实现 FilterGroup 实体
    - 在 `contexts/screening/domain/models/filter_group.py` 实现
    - 支持 AND/OR/NOT 递归嵌套
    - match() 方法实现逻辑运算
    - has_any_condition()、count_total_conditions() 辅助方法
    - to_dict / from_dict 序列化
    - _Requirements: 2.4, 5.3, 5.4, 5.5, 3.12_

  - [x] 3.2 编写 FilterGroup 序列化 round-trip 属性测试
    - **Property 7: FilterGroup 序列化 round-trip**
    - **Validates: Requirements 3.12**

  - [x] 3.3 编写 FilterGroup.match 逻辑语义属性测试
    - **Property 9: FilterGroup.match 逻辑语义一致性**
    - **Validates: Requirements 5.3, 5.4, 5.5**

  - [x] 3.4 实现 Stock 实体
    - 在 `contexts/screening/domain/models/stock.py` 实现
    - 包含财务指标属性（roe、pe、pb、eps、revenue、net_profit、debt_ratio、market_cap 等）
    - _Requirements: 2.5_

  - [x] 3.5 实现 ScreeningStrategy 聚合根
    - 在 `contexts/screening/domain/models/screening_strategy.py` 实现
    - 包含所有属性（strategy_id、name、description、filters、scoring_config、tags、is_template、created_at、updated_at）
    - 验证：名称非空、filters 包含至少一个条件
    - execute() 方法：过滤 → 评分 → 排序 → 返回 ScreeningResult
    - _Requirements: 2.1, 2.6, 2.7, 5.6_

  - [x] 3.6 编写 ScreeningStrategy.execute 结果有序性属性测试
    - **Property 10: ScreeningStrategy.execute 结果有序性**
    - **Validates: Requirements 5.6**

  - [x] 3.7 实现 ScreeningSession 聚合根
    - 在 `contexts/screening/domain/models/screening_session.py` 实现
    - 包含所有属性（session_id、strategy_id、strategy_name、executed_at、total_scanned、execution_time、top_stocks、other_stock_codes、filters_snapshot、scoring_config_snapshot）
    - create_from_result() 工厂方法
    - _Requirements: 2.2_

  - [x] 3.8 实现 WatchList 聚合根
    - 在 `contexts/screening/domain/models/watchlist.py` 实现
    - add_stock()（重复抛 DuplicateStockError）、remove_stock()（不存在抛 StockNotFoundError）、contains()
    - _Requirements: 2.3, 2.8, 2.9_

  - [x] 3.9 编写 WatchList 属性测试
    - **Property 2: WatchList 不允许重复添加**
    - **Property 3: WatchList 移除不存在的股票应报错**
    - **Validates: Requirements 2.8, 2.9**

  - [x] 3.10 实现领域服务接口
    - `contexts/screening/domain/services/scoring_service.py`：IScoringService 接口（score_stocks 方法）
    - `contexts/screening/domain/services/indicator_calculation_service.py`：IIndicatorCalculationService 接口（calculate_indicator、validate_derived_indicator、calculate_batch）
    - `contexts/screening/domain/repositories/`：IScreeningStrategyRepository、IScreeningSessionRepository、IWatchListRepository、IHistoricalDataProvider 接口
    - _Requirements: 4.4, 4.5_

- [x] 4. Checkpoint - 领域层验证
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. 基础设施层 - 持久化
  - [x] 5.1 实现 SQLAlchemy PO 模型
    - `contexts/screening/infrastructure/persistence/models/screening_strategy_po.py`
    - `contexts/screening/infrastructure/persistence/models/screening_session_po.py`
    - `contexts/screening/infrastructure/persistence/models/watchlist_po.py`
    - 使用 JSONB 存储 filters、scoring_config、top_stocks、other_stock_codes、stocks
    - _Requirements: 6.1, 6.5, 6.6_

  - [x] 5.2 实现 Repository（ScreeningStrategy）
    - `contexts/screening/infrastructure/persistence/repositories/screening_strategy_repository_impl.py`
    - 实现 save、find_by_id、find_by_name、find_all、delete
    - PO ↔ 领域对象映射（含 FilterGroup、ScoringConfig 的 JSONB 序列化/反序列化）
    - _Requirements: 6.2, 6.7_

  - [x] 5.3 实现 Repository（ScreeningSession 和 WatchList）
    - `screening_session_repository_impl.py`：save、find_by_id、find_by_strategy_id、find_recent
    - `watchlist_repository_impl.py`：save、find_by_id、find_by_name、find_all、delete
    - _Requirements: 6.3, 6.4_

  - [x] 5.4 实现领域服务（ScoringService 和 IndicatorCalculationService）
    - `contexts/screening/infrastructure/services/scoring_service_impl.py`：实现 min-max 归一化评分
    - `contexts/screening/infrastructure/services/indicator_calculation_service_impl.py`：实现指标计算逻辑
    - _Requirements: 4.4, 4.5_

  - [x] 5.5 创建 Flask-Migrate 数据库迁移
    - 配置 Flask-Migrate（Alembic）
    - 生成初始迁移脚本
    - _Requirements: 10.5_

- [x] 6. 应用层服务
  - [x] 6.1 实现 ScreeningStrategyService
    - `contexts/screening/application/services/screening_strategy_service.py`
    - create_strategy、update_strategy、delete_strategy、get_strategy、list_strategies、execute_strategy
    - execute_strategy：加载候选股票 → 调用 execute() → 创建 ScreeningSession → 持久化 → 返回结果
    - 重复名称检查
    - _Requirements: 7.1, 7.3, 7.4_

  - [x] 6.2 实现 WatchListService
    - `contexts/screening/application/services/watchlist_service.py`
    - create_watchlist、add_stock、remove_stock、get_watchlist、list_watchlists
    - _Requirements: 7.2_

- [x] 7. 接口层 - RESTful API
  - [x] 7.1 实现 DTO 类
    - `contexts/screening/interface/dto/strategy_dto.py`：CreateStrategyRequest、UpdateStrategyRequest、StrategyResponse、ScreeningResultResponse
    - `contexts/screening/interface/dto/session_dto.py`：SessionResponse
    - `contexts/screening/interface/dto/watchlist_dto.py`：CreateWatchlistRequest、WatchlistResponse
    - 请求验证逻辑
    - _Requirements: 8.10_

  - [x] 7.2 实现 Strategy Controller
    - `contexts/screening/interface/controllers/strategy_controller.py`
    - POST /api/screening/strategies（创建）
    - GET /api/screening/strategies（分页列表）
    - GET /api/screening/strategies/<id>（详情）
    - PUT /api/screening/strategies/<id>（更新）
    - DELETE /api/screening/strategies/<id>（删除）
    - POST /api/screening/strategies/<id>/execute（执行）
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [x] 7.3 实现 Session 和 WatchList Controller
    - `session_controller.py`：GET /api/screening/sessions、GET /api/screening/sessions/<id>
    - `watchlist_controller.py`：CRUD 端点 /api/screening/watchlists
    - _Requirements: 8.7, 8.8, 8.9_

  - [x] 7.4 实现全局错误处理与蓝图注册
    - 在 app.py 中注册所有蓝图
    - 实现 DomainError → HTTP 状态码映射的全局错误处理器
    - 400（ValidationError）、404（NotFound）、409（Duplicate）
    - _Requirements: 8.11, 8.12_

- [x] 8. Checkpoint - 后端 API 验证
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. 前端基础框架
  - [x] 9.1 初始化前端项目
    - 使用 Vite 创建 React.js 项目（frontend/）
    - 安装 Ant Design、Axios、React Router
    - 配置 Vite 代理到 Flask 后端
    - _Requirements: 9.1_

  - [x] 9.2 实现布局与路由
    - `MainLayout.jsx`：侧边栏导航 + 主内容区域
    - `App.jsx`：配置路由（策略列表、创建策略、筛选结果）
    - _Requirements: 9.2_

  - [x] 9.3 实现 API 服务层
    - `services/api.js`：基于 Axios 的 API 客户端
    - 封装所有后端 API 调用（strategies、sessions、watchlists）
    - _Requirements: 9.3_

  - [x] 9.4 实现策略列表页面
    - `StrategyListPage.jsx`：展示策略列表，支持删除、执行操作
    - _Requirements: 9.4_

  - [x] 9.5 实现策略创建页面
    - `StrategyCreatePage.jsx`：策略创建表单
    - `FilterConditionBuilder.jsx`：筛选条件构建器组件
    - _Requirements: 9.5_

  - [x] 9.6 实现筛选结果页面
    - `ScreeningResultPage.jsx`：展示筛选结果
    - `ScoredStockTable.jsx`：带评分的股票表格组件
    - _Requirements: 9.6_

- [x] 10. Final Checkpoint - 全链路验证
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks are required, including property-based tests
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (using hypothesis)
- Unit tests validate specific examples and edge cases (using pytest)
- 领域层零技术依赖，纯 Python 实现
- 基础设施层通过 Repository 模式实现持久化
