# 股票投研工作流定制化平台

## 项目概述

基于 DDD 架构的股票筛选平台 MVP，支持自定义筛选策略、评分配置和自选股管理。

## 技术栈

- **后端**: Python 3.11, Flask, SQLAlchemy
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **前端**: React.js, Vite, Ant Design
- **测试**: pytest, hypothesis

## 项目结构

```
src/
├── backend/                       # 后端代码
│   ├── shared_kernel/             # 共享内核
│   ├── contexts/screening/        # 筛选上下文
│   │   ├── interface/             # 接口层 (Controllers, DTOs)
│   │   ├── application/           # 应用层 (Services)
│   │   ├── domain/                # 领域层 (Models, Value Objects)
│   │   └── infrastructure/        # 基础设施层 (Repositories, PO Models)
│   ├── migrations/                # 数据库迁移
│   ├── tests/                     # 测试
│   ├── app.py                     # Flask 入口
│   ├── config.py                  # 配置管理
│   └── requirements.txt           # Python 依赖
├── frontend/                      # 前端代码 (React + Vite)
```

## 快速开始

### 使用 Docker Compose（推荐）

1. 启动所有服务：
```bash
docker-compose up -d
```

2. 查看日志：
```bash
docker-compose logs -f flask
```

3. 停止服务：
```bash
docker-compose down
```

### 本地开发

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件
```

3. 启动 PostgreSQL 和 Redis（需要本地安装）

4. 初始化数据库：
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. 运行应用：
```bash
python app.py
```

## 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行属性基测试
pytest tests/property/

# 运行集成测试
pytest tests/integration/

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

## API 文档

应用启动后访问：
- 健康检查: http://localhost:5000/health
- API 端点: http://localhost:5000/api/screening/

## 开发指南

### DDD 分层架构

1. **领域层**: 纯 Python，零技术依赖
2. **应用层**: 编排领域对象，管理事务
3. **基础设施层**: 实现领域接口（Repository、Service）
4. **接口层**: Flask Controllers 和 DTOs

### 测试策略

- **单元测试**: 验证具体示例和边界情况
- **属性基测试**: 使用 hypothesis 验证通用属性
- **集成测试**: 测试 API 端点和数据库交互

## 许可证

MIT
