"""
ScreeningSessionRepositoryImpl 单元测试

测试 Repository 实现的 PO ↔ 领域对象映射逻辑。
使用 Mock 模拟 SQLAlchemy session 以隔离数据库依赖。

Requirements:
- 6.3: 实现 ScreeningSessionRepository，在 ScreeningSession 领域对象和 PO 模型之间进行映射
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
import uuid

from contexts.screening.infrastructure.persistence.repositories.screening_session_repository_impl import (
    ScreeningSessionRepositoryImpl
)
from contexts.screening.infrastructure.persistence.models.screening_session_po import (
    ScreeningSessionPO
)
from contexts.screening.domain.models.screening_session import ScreeningSession
from contexts.screening.domain.models.filter_group import FilterGroup
from contexts.screening.domain.value_objects.scoring_config import ScoringConfig
from contexts.screening.domain.value_objects.scored_stock import ScoredStock
from contexts.screening.domain.value_objects.identifiers import SessionId, StrategyId
from contexts.screening.domain.value_objects.filter_condition import FilterCondition
from contexts.screening.domain.value_objects.indicator_value import NumericValue
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.comparison_operator import ComparisonOperator
from contexts.screening.domain.enums.enums import LogicalOperator, NormalizationMethod
from shared_kernel.value_objects.stock_code import StockCode


class TestScreeningSessionRepositoryImpl:
    """ScreeningSessionRepositoryImpl 单元测试"""
    
    @pytest.fixture
    def mock_session(self):
        """创建 Mock SQLAlchemy session"""
        session = Mock()
        session.query = Mock(return_value=Mock())
        session.merge = Mock()
        session.flush = Mock()
        session.delete = Mock()
        return session
    
    @pytest.fixture
    def repository(self, mock_session):
        """创建 Repository 实例"""
        return ScreeningSessionRepositoryImpl(mock_session)
    
    @pytest.fixture
    def sample_filters(self):
        """创建示例 FilterGroup"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        return FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[condition],
            sub_groups=[]
        )
    
    @pytest.fixture
    def sample_scoring_config(self):
        """创建示例 ScoringConfig"""
        return ScoringConfig(
            weights={IndicatorField.ROE: 0.5, IndicatorField.PE: 0.5},
            normalization_method=NormalizationMethod.MIN_MAX
        )
    
    @pytest.fixture
    def sample_scored_stock(self):
        """创建示例 ScoredStock"""
        return ScoredStock(
            stock_code=StockCode("600000.SH"),
            stock_name="浦发银行",
            score=85.5,
            score_breakdown={IndicatorField.ROE: 42.75, IndicatorField.PE: 42.75},
            indicator_values={IndicatorField.ROE: 0.18, IndicatorField.PE: 8.5},
            matched_conditions=[]
        )
    
    @pytest.fixture
    def sample_session(self, sample_filters, sample_scoring_config, sample_scored_stock):
        """创建示例 ScreeningSession 领域对象"""
        session_id = SessionId.generate()
        strategy_id = StrategyId.generate()
        now = datetime.now(timezone.utc)
        
        return ScreeningSession(
            session_id=session_id,
            strategy_id=strategy_id,
            strategy_name="测试策略",
            executed_at=now,
            total_scanned=1000,
            execution_time=1.5,
            top_stocks=[sample_scored_stock],
            other_stock_codes=["600001.SH", "600002.SH"],
            filters_snapshot=sample_filters,
            scoring_config_snapshot=sample_scoring_config
        )
    
    @pytest.fixture
    def sample_po(self, sample_session):
        """创建示例 ScreeningSessionPO 持久化对象"""
        po = Mock(spec=ScreeningSessionPO)
        po.id = sample_session.session_id.value
        po.strategy_id = sample_session.strategy_id.value
        po.strategy_name = sample_session.strategy_name
        po.executed_at = sample_session.executed_at
        po.total_scanned = sample_session.total_scanned
        po.execution_time = sample_session.execution_time
        po.top_stocks = [stock.to_dict() for stock in sample_session.top_stocks]
        po.other_stock_codes = sample_session.other_stock_codes
        po.filters_snapshot = sample_session.filters_snapshot.to_dict()
        po.scoring_config_snapshot = sample_session.scoring_config_snapshot.to_dict()
        return po
    
    # ==================== save 方法测试 ====================
    
    def test_save_calls_merge_and_flush(self, repository, mock_session, sample_session):
        """测试 save 方法调用 merge 和 flush"""
        repository.save(sample_session)
        
        mock_session.merge.assert_called_once()
        mock_session.flush.assert_called_once()
    
    def test_save_converts_domain_to_po(self, repository, mock_session, sample_session):
        """测试 save 方法正确转换领域对象为 PO"""
        repository.save(sample_session)
        
        call_args = mock_session.merge.call_args
        po = call_args[0][0]
        
        assert po.id == sample_session.session_id.value
        assert po.strategy_id == sample_session.strategy_id.value
        assert po.strategy_name == sample_session.strategy_name
        assert po.executed_at == sample_session.executed_at
        assert po.total_scanned == sample_session.total_scanned
        assert po.execution_time == sample_session.execution_time
        assert po.top_stocks == [stock.to_dict() for stock in sample_session.top_stocks]
        assert po.other_stock_codes == sample_session.other_stock_codes
        assert po.filters_snapshot == sample_session.filters_snapshot.to_dict()
        assert po.scoring_config_snapshot == sample_session.scoring_config_snapshot.to_dict()
    
    # ==================== find_by_id 方法测试 ====================
    
    def test_find_by_id_returns_domain_object_when_found(
        self, repository, mock_session, sample_session, sample_po
    ):
        """测试 find_by_id 找到记录时返回领域对象"""
        mock_query = Mock()
        mock_query.get = Mock(return_value=sample_po)
        mock_session.query.return_value = mock_query
        
        result = repository.find_by_id(sample_session.session_id)
        
        assert result is not None
        assert result.session_id == sample_session.session_id
        assert result.strategy_id == sample_session.strategy_id
        assert result.strategy_name == sample_session.strategy_name
        assert result.total_scanned == sample_session.total_scanned
    
    def test_find_by_id_returns_none_when_not_found(self, repository, mock_session):
        """测试 find_by_id 未找到记录时返回 None"""
        mock_query = Mock()
        mock_query.get = Mock(return_value=None)
        mock_session.query.return_value = mock_query
        
        session_id = SessionId.generate()
        result = repository.find_by_id(session_id)
        
        assert result is None
    
    # ==================== find_by_strategy_id 方法测试 ====================
    
    def test_find_by_strategy_id_returns_list_of_sessions(
        self, repository, mock_session, sample_po
    ):
        """测试 find_by_strategy_id 返回会话列表"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[sample_po])
        mock_session.query.return_value = mock_query
        
        strategy_id = StrategyId.from_string(sample_po.strategy_id)
        result = repository.find_by_strategy_id(strategy_id)
        
        assert len(result) == 1
        assert result[0].strategy_name == sample_po.strategy_name
    
    def test_find_by_strategy_id_returns_empty_list_when_no_sessions(
        self, repository, mock_session
    ):
        """测试 find_by_strategy_id 无会话时返回空列表"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_session.query.return_value = mock_query
        
        strategy_id = StrategyId.generate()
        result = repository.find_by_strategy_id(strategy_id)
        
        assert result == []
    
    # ==================== find_recent 方法测试 ====================
    
    def test_find_recent_returns_list_of_sessions(
        self, repository, mock_session, sample_po
    ):
        """测试 find_recent 返回会话列表"""
        mock_query = Mock()
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[sample_po])
        mock_session.query.return_value = mock_query
        
        result = repository.find_recent(limit=10, offset=0)
        
        assert len(result) == 1
    
    def test_find_recent_applies_pagination(self, repository, mock_session):
        """测试 find_recent 正确应用分页参数"""
        mock_query = Mock()
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_session.query.return_value = mock_query
        
        repository.find_recent(limit=50, offset=10)
        
        mock_query.offset.assert_called_once_with(10)
        mock_query.limit.assert_called_once_with(50)
    
    # ==================== delete 方法测试 ====================
    
    def test_delete_removes_existing_record(
        self, repository, mock_session, sample_po
    ):
        """测试 delete 删除存在的记录"""
        mock_query = Mock()
        mock_query.get = Mock(return_value=sample_po)
        mock_session.query.return_value = mock_query
        
        session_id = SessionId.from_string(sample_po.id)
        repository.delete(session_id)
        
        mock_session.delete.assert_called_once_with(sample_po)
        mock_session.flush.assert_called_once()
    
    def test_delete_does_nothing_when_not_found(self, repository, mock_session):
        """测试 delete 记录不存在时静默处理"""
        mock_query = Mock()
        mock_query.get = Mock(return_value=None)
        mock_session.query.return_value = mock_query
        
        session_id = SessionId.generate()
        repository.delete(session_id)
        
        mock_session.delete.assert_not_called()
    
    # ==================== delete_by_strategy_id 方法测试 ====================
    
    def test_delete_by_strategy_id_returns_deleted_count(
        self, repository, mock_session
    ):
        """测试 delete_by_strategy_id 返回删除数量"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.delete = Mock(return_value=3)
        mock_session.query.return_value = mock_query
        
        strategy_id = StrategyId.generate()
        result = repository.delete_by_strategy_id(strategy_id)
        
        assert result == 3
        mock_session.flush.assert_called_once()
    
    # ==================== count 方法测试 ====================
    
    def test_count_returns_total_records(self, repository, mock_session):
        """测试 count 返回记录总数"""
        mock_query = Mock()
        mock_query.count = Mock(return_value=5)
        mock_session.query.return_value = mock_query
        
        result = repository.count()
        
        assert result == 5
    
    # ==================== count_by_strategy_id 方法测试 ====================
    
    def test_count_by_strategy_id_returns_count(self, repository, mock_session):
        """测试 count_by_strategy_id 返回指定策略的会话数量"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=3)
        mock_session.query.return_value = mock_query
        
        strategy_id = StrategyId.generate()
        result = repository.count_by_strategy_id(strategy_id)
        
        assert result == 3
    
    # ==================== 映射测试 ====================
    
    def test_to_domain_preserves_top_stocks(self, repository, mock_session):
        """测试 _to_domain 保留 top_stocks 结构"""
        top_stocks_data = [
            {
                'stock_code': '600000.SH',
                'stock_name': '浦发银行',
                'score': 85.5,
                'score_breakdown': {'ROE': 42.75},
                'indicator_values': {'ROE': 0.18},
                'matched_conditions': []
            }
        ]
        
        filters_snapshot = {
            'group_id': str(uuid.uuid4()),
            'operator': 'AND',
            'conditions': [
                {
                    'field': 'ROE',
                    'operator': '>',
                    'value': {'type': 'numeric', 'value': 0.15, 'unit': None}
                }
            ],
            'sub_groups': []
        }
        
        scoring_config_snapshot = {
            'weights': {'ROE': 1.0},
            'normalization_method': 'min_max'
        }
        
        po = Mock(spec=ScreeningSessionPO)
        po.id = str(uuid.uuid4())
        po.strategy_id = str(uuid.uuid4())
        po.strategy_name = "测试策略"
        po.executed_at = datetime.now(timezone.utc)
        po.total_scanned = 1000
        po.execution_time = 1.5
        po.top_stocks = top_stocks_data
        po.other_stock_codes = ["600001.SH"]
        po.filters_snapshot = filters_snapshot
        po.scoring_config_snapshot = scoring_config_snapshot
        
        mock_query = Mock()
        mock_query.get = Mock(return_value=po)
        mock_session.query.return_value = mock_query
        
        session_id = SessionId.from_string(po.id)
        result = repository.find_by_id(session_id)
        
        assert result is not None
        assert len(result.top_stocks) == 1
        assert result.top_stocks[0].stock_code.code == '600000.SH'
        assert result.top_stocks[0].stock_name == '浦发银行'
        assert result.top_stocks[0].score == 85.5
    
    def test_to_domain_handles_empty_top_stocks(self, repository, mock_session):
        """测试 _to_domain 处理空 top_stocks"""
        filters_snapshot = {
            'group_id': str(uuid.uuid4()),
            'operator': 'AND',
            'conditions': [
                {
                    'field': 'ROE',
                    'operator': '>',
                    'value': {'type': 'numeric', 'value': 0.15, 'unit': None}
                }
            ],
            'sub_groups': []
        }
        
        scoring_config_snapshot = {
            'weights': {'ROE': 1.0},
            'normalization_method': 'min_max'
        }
        
        po = Mock(spec=ScreeningSessionPO)
        po.id = str(uuid.uuid4())
        po.strategy_id = str(uuid.uuid4())
        po.strategy_name = "空结果测试"
        po.executed_at = datetime.now(timezone.utc)
        po.total_scanned = 1000
        po.execution_time = 1.5
        po.top_stocks = None  # 空 top_stocks
        po.other_stock_codes = None  # 空 other_stock_codes
        po.filters_snapshot = filters_snapshot
        po.scoring_config_snapshot = scoring_config_snapshot
        
        mock_query = Mock()
        mock_query.get = Mock(return_value=po)
        mock_session.query.return_value = mock_query
        
        session_id = SessionId.from_string(po.id)
        result = repository.find_by_id(session_id)
        
        assert result is not None
        assert result.top_stocks == []
        assert result.other_stock_codes == []
