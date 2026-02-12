# 实现计划：异步策略执行

## 概述

本计划将异步策略执行功能分解为可增量实现的任务。每个任务都是独立可测试的，按依赖顺序排列。

## 任务列表

- [x] 1. 领域层实现
  - [x] 1.1 实现 TaskStatus 枚举和 InvalidTaskStateError 异常
    - 创建 `contexts/screening/domain/enums/task_status.py`
    - 创建 `contexts/screening/domain/exceptions.py` 中添加 InvalidTaskStateError
    - _Requirements: 1.2, 1.7_
  - [x] 1.2 实现 ExecutionTask 实体
    - 创建 `contexts/screening/domain/models/execution_task.py`
    - 实现状态转换方法：start()、complete()、fail()、cancel()
    - 实现 update_progress() 方法
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 1.7_
  - [ ]* 1.3 编写 ExecutionTask 属性测试
    - **Property 1: 初始状态测试**
    - **Property 2: 有效状态转换测试**
    - **Property 3: 非法状态转换测试**
    - **Validates: Requirements 1.3, 1.4, 1.5, 1.6, 1.7**
  - [x] 1.4 实现 IExecutionTaskRepository 接口
    - 创建 `contexts/screening/domain/repositories/execution_task_repository.py`
    - _Requirements: 8.1_

- [x] 2. 基础设施层实现
  - [x] 2.1 实现 ExecutionTaskPO 模型
    - 创建 `contexts/screening/infrastructure/persistence/models/execution_task_po.py`
    - 添加到 models/__init__.py 导出
    - _Requirements: 8.2_
  - [x] 2.2 创建数据库迁移
    - 运行 flask db migrate 生成迁移文件
    - 运行 flask db upgrade 应用迁移
    - _Requirements: 8.2_
  - [x] 2.3 实现 ExecutionTaskRepositoryImpl
    - 创建 `contexts/screening/infrastructure/persistence/repositories/execution_task_repository_impl.py`
    - 实现 PO 与领域对象的映射
    - 实现 cleanup_old_tasks 方法
    - _Requirements: 8.1, 8.3, 8.4_
  - [ ]* 2.4 编写任务保留策略属性测试
    - **Property 7: 任务保留策略测试**
    - **Validates: Requirements 8.4**
  - [x] 2.5 实现 BackgroundExecutor 组件
    - 创建 `contexts/screening/infrastructure/services/background_executor.py`
    - 使用单例模式和 ThreadPoolExecutor
    - _Requirements: 3.1, 3.6_
  - [ ]* 2.6 编写 BackgroundExecutor 属性测试
    - **Property 4: 立即返回测试**
    - **Validates: Requirements 3.2**
  - [x] 2.7 实现 ScreeningWebSocketEmitter 组件
    - 创建 `contexts/screening/interface/websocket/screening_ws_emitter.py`
    - 实现 emit_status_changed、emit_progress、emit_completed、emit_failed 方法
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 3. Checkpoint - 确保基础组件测试通过
  - 运行所有单元测试，确保通过
  - 如有问题，询问用户

- [ ] 4. 应用层实现
  - [ ] 4.1 实现 AsyncExecutionService
    - 创建 `contexts/screening/application/services/async_execution_service.py`
    - 实现 start_execution、_execute_task、get_task、list_tasks、cancel_task 方法
    - 实现带进度报告的 _fetch_stocks_with_progress 和 _filter_with_progress
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 5.1, 5.2, 5.3_
  - [ ]* 4.2 编写进度计算属性测试
    - **Property 5: 进度百分比计算测试**
    - **Property 6: 进度更新结构完整性测试**
    - **Validates: Requirements 5.2, 5.3, 5.4**

- [ ] 5. 接口层实现
  - [ ] 5.1 实现 TaskResponse DTO
    - 创建 `contexts/screening/interface/dto/task_dto.py`
    - _Requirements: 2.2_
  - [ ] 5.2 实现 TaskController
    - 创建 `contexts/screening/interface/controllers/task_controller.py`
    - 实现 GET /tasks、GET /tasks/<id>、POST /tasks/<id>/cancel 端点
    - _Requirements: 2.2, 2.3, 2.4, 2.7_
  - [ ] 5.3 修改 StrategyController 的 execute 端点
    - 修改为异步模式，返回 202 + task_id
    - _Requirements: 2.1, 2.5, 2.6_
  - [ ] 5.4 注册 WebSocket 命名空间和蓝图
    - 在 app.py 中注册 /screening 命名空间
    - 注册 task_bp 蓝图
    - 初始化 AsyncExecutionService 依赖
    - _Requirements: 4.1_

- [ ] 6. Checkpoint - 确保后端 API 测试通过
  - 运行集成测试，确保 API 正常工作
  - 如有问题，询问用户

- [ ] 7. 配置更新
  - [ ] 7.1 更新 Nginx 配置
    - 修改 deploy/nginx.conf，增加 /api/ 的超时配置
    - _Requirements: 6.1, 6.2, 6.3_
  - [ ] 7.2 添加服务启动时的任务状态恢复逻辑
    - 在 app.py 中添加启动钩子，将 RUNNING 任务标记为 FAILED
    - _Requirements: 8.3_

- [ ] 8. 前端实现
  - [ ] 8.1 扩展 API 服务
    - 修改 `frontend/src/services/api.js`，添加任务相关 API
    - _Requirements: 7.1_
  - [ ] 8.2 实现 WebSocket 客户端
    - 创建 `frontend/src/services/screeningSocket.js`
    - _Requirements: 7.2_
  - [ ] 8.3 实现执行进度组件
    - 创建 `frontend/src/components/ExecutionProgress.jsx`
    - _Requirements: 7.3, 7.4, 7.5, 7.6_
  - [ ] 8.4 修改策略执行页面
    - 集成进度组件，处理异步执行流程
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 9. 最终 Checkpoint
  - 运行完整测试套件
  - 手动测试完整执行流程
  - 如有问题，询问用户

## 注意事项

- 任务标记 `*` 的为可选测试任务，可跳过以加快 MVP 开发
- 每个任务完成后应确保代码可编译运行
- 属性测试使用 Hypothesis 库
- 前端任务依赖后端 API 完成
