"""
WatchListRepositoryImpl 单元测试

测试 Repository 实现的 PO ↔ 领域对象映射逻辑。
使用 Mock 模拟 SQLAlchemy session 以隔离数据库依赖。

Requirements:
- 6.4: 实现 WatchListRepository，在 WatchList 领域对象和 PO 模型之间进行映射
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock
import uuid

from contexts.screening.infrastructure.persistence.repositories.watchlist_repository_impl import (
    WatchListRepositoryImpl
)
from contexts.screening.infrastructure.persistence.models.watchlist_po import (
    WatchListPO
)
from contexts.screening.domain.models.watchlist import WatchList
from contexts.screening.domain.value_objects.watched_stock import WatchedStock
from contexts.screening.domain.value_objects.identifiers import WatchListId
from shared_kernel.value_objects.stock_code import StockCode


class TestWatchListRepositoryImpl:
    """WatchListRepositoryImpl 单元测试"""
    
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
        return WatchListRepositoryImpl(mock_session)
    
    @pytest.fixture
    def sample_watched_stock(self):
        """创建示例 WatchedStock"""
        return WatchedStock(
            stock_code=StockCode("600000.SH"),
            stock_name="浦发银行",
            added_at=datetime.now(timezone.utc),
            note="银行股龙头",
            tags=["银行", "蓝筹"]
        )
    
    @pytest.fixture
    def sample_watchlist(self, sample_watched_stock):
        """创建示例 WatchList 领域对象"""
        watchlist_id = WatchListId.generate()
        now = datetime.now(timezone.utc)
        
        return WatchList(
            watchlist_id=watchlist_id,
            name="我的自选股",
            description="重点关注的股票",
            stocks=[sample_watched_stock],
            created_at=now,
            updated_at=now
        )
    
    @pytest.fixture
    def sample_po(self, sample_watchlist):
        """创建示例 WatchListPO 持久化对象"""
        po = Mock(spec=WatchListPO)
        po.id = sample_watchlist.watchlist_id.value
        po.name = sample_watchlist.name
        po.description = sample_watchlist.description
        po.stocks = [stock.to_dict() for stock in sample_watchlist.stocks]
        po.created_at = sample_watchlist.created_at
        po.updated_at = sample_watchlist.updated_at
        return po
    
    # ==================== save 方法测试 ====================
    
    def test_save_calls_merge_and_flush(self, repository, mock_session, sample_watchlist):
        """测试 save 方法调用 merge 和 flush"""
        repository.save(sample_watchlist)
        
        mock_session.merge.assert_called_once()
        mock_session.flush.assert_called_once()
    
    def test_save_converts_domain_to_po(self, repository, mock_session, sample_watchlist):
        """测试 save 方法正确转换领域对象为 PO"""
        repository.save(sample_watchlist)
        
        call_args = mock_session.merge.call_args
        po = call_args[0][0]
        
        assert po.id == sample_watchlist.watchlist_id.value
        assert po.name == sample_watchlist.name
        assert po.description == sample_watchlist.description
        assert po.stocks == [stock.to_dict() for stock in sample_watchlist.stocks]
        assert po.created_at == sample_watchlist.created_at
        assert po.updated_at == sample_watchlist.updated_at
    
    # ==================== find_by_id 方法测试 ====================
    
    def test_find_by_id_returns_domain_object_when_found(
        self, repository, mock_session, sample_watchlist, sample_po
    ):
        """测试 find_by_id 找到记录时返回领域对象"""
        mock_query = Mock()
        mock_query.get = Mock(return_value=sample_po)
        mock_session.query.return_value = mock_query
        
        result = repository.find_by_id(sample_watchlist.watchlist_id)
        
        assert result is not None
        assert result.watchlist_id == sample_watchlist.watchlist_id
        assert result.name == sample_watchlist.name
        assert result.description == sample_watchlist.description
    
    def test_find_by_id_returns_none_when_not_found(self, repository, mock_session):
        """测试 find_by_id 未找到记录时返回 None"""
        mock_query = Mock()
        mock_query.get = Mock(return_value=None)
        mock_session.query.return_value = mock_query
        
        watchlist_id = WatchListId.generate()
        result = repository.find_by_id(watchlist_id)
        
        assert result is None
    
    # ==================== find_by_name 方法测试 ====================
    
    def test_find_by_name_returns_domain_object_when_found(
        self, repository, mock_session, sample_watchlist, sample_po
    ):
        """测试 find_by_name 找到记录时返回领域对象"""
        mock_query = Mock()
        mock_query.filter_by = Mock(return_value=Mock(first=Mock(return_value=sample_po)))
        mock_session.query.return_value = mock_query
        
        result = repository.find_by_name(sample_watchlist.name)
        
        assert result is not None
        assert result.name == sample_watchlist.name
    
    def test_find_by_name_returns_none_when_not_found(self, repository, mock_session):
        """测试 find_by_name 未找到记录时返回 None"""
        mock_query = Mock()
        mock_query.filter_by = Mock(return_value=Mock(first=Mock(return_value=None)))
        mock_session.query.return_value = mock_query
        
        result = repository.find_by_name("不存在的列表")
        
        assert result is None
    
    # ==================== find_all 方法测试 ====================
    
    def test_find_all_returns_list_of_domain_objects(
        self, repository, mock_session, sample_po
    ):
        """测试 find_all 返回领域对象列表"""
        po_list = [sample_po]
        
        mock_query = Mock()
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=po_list)
        mock_session.query.return_value = mock_query
        
        result = repository.find_all(limit=10, offset=0)
        
        assert len(result) == 1
        assert result[0].name == sample_po.name
    
    def test_find_all_returns_empty_list_when_no_records(
        self, repository, mock_session
    ):
        """测试 find_all 无记录时返回空列表"""
        mock_query = Mock()
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_session.query.return_value = mock_query
        
        result = repository.find_all()
        
        assert result == []
    
    def test_find_all_applies_pagination(self, repository, mock_session):
        """测试 find_all 正确应用分页参数"""
        mock_query = Mock()
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_session.query.return_value = mock_query
        
        repository.find_all(limit=50, offset=10)
        
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
        
        watchlist_id = WatchListId.from_string(sample_po.id)
        repository.delete(watchlist_id)
        
        mock_session.delete.assert_called_once_with(sample_po)
        mock_session.flush.assert_called_once()
    
    def test_delete_does_nothing_when_not_found(self, repository, mock_session):
        """测试 delete 记录不存在时静默处理"""
        mock_query = Mock()
        mock_query.get = Mock(return_value=None)
        mock_session.query.return_value = mock_query
        
        watchlist_id = WatchListId.generate()
        repository.delete(watchlist_id)
        
        mock_session.delete.assert_not_called()
    
    # ==================== exists 方法测试 ====================
    
    def test_exists_returns_true_when_found(self, repository, mock_session):
        """测试 exists 记录存在时返回 True"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=1)
        mock_session.query.return_value = mock_query
        
        watchlist_id = WatchListId.generate()
        result = repository.exists(watchlist_id)
        
        assert result is True
    
    def test_exists_returns_false_when_not_found(self, repository, mock_session):
        """测试 exists 记录不存在时返回 False"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=0)
        mock_session.query.return_value = mock_query
        
        watchlist_id = WatchListId.generate()
        result = repository.exists(watchlist_id)
        
        assert result is False
    
    # ==================== count 方法测试 ====================
    
    def test_count_returns_total_records(self, repository, mock_session):
        """测试 count 返回记录总数"""
        mock_query = Mock()
        mock_query.count = Mock(return_value=5)
        mock_session.query.return_value = mock_query
        
        result = repository.count()
        
        assert result == 5
    
    # ==================== 映射测试 ====================
    
    def test_to_domain_preserves_stocks_list(self, repository, mock_session):
        """测试 _to_domain 保留 stocks 列表结构"""
        stocks_data = [
            {
                'stock_code': '600000.SH',
                'stock_name': '浦发银行',
                'added_at': datetime.now(timezone.utc).isoformat(),
                'note': '银行股龙头',
                'tags': ['银行', '蓝筹']
            },
            {
                'stock_code': '000001.SZ',
                'stock_name': '平安银行',
                'added_at': datetime.now(timezone.utc).isoformat(),
                'note': None,
                'tags': None
            }
        ]
        
        po = Mock(spec=WatchListPO)
        po.id = str(uuid.uuid4())
        po.name = "测试列表"
        po.description = "测试描述"
        po.stocks = stocks_data
        po.created_at = datetime.now(timezone.utc)
        po.updated_at = datetime.now(timezone.utc)
        
        mock_query = Mock()
        mock_query.get = Mock(return_value=po)
        mock_session.query.return_value = mock_query
        
        watchlist_id = WatchListId.from_string(po.id)
        result = repository.find_by_id(watchlist_id)
        
        assert result is not None
        assert len(result.stocks) == 2
        assert result.stocks[0].stock_code.code == '600000.SH'
        assert result.stocks[0].stock_name == '浦发银行'
        assert result.stocks[0].note == '银行股龙头'
        assert result.stocks[0].tags == ['银行', '蓝筹']
        assert result.stocks[1].stock_code.code == '000001.SZ'
        assert result.stocks[1].stock_name == '平安银行'
    
    def test_to_domain_handles_empty_stocks(self, repository, mock_session):
        """测试 _to_domain 处理空 stocks"""
        po = Mock(spec=WatchListPO)
        po.id = str(uuid.uuid4())
        po.name = "空列表测试"
        po.description = None
        po.stocks = None  # 空 stocks
        po.created_at = datetime.now(timezone.utc)
        po.updated_at = datetime.now(timezone.utc)
        
        mock_query = Mock()
        mock_query.get = Mock(return_value=po)
        mock_session.query.return_value = mock_query
        
        watchlist_id = WatchListId.from_string(po.id)
        result = repository.find_by_id(watchlist_id)
        
        assert result is not None
        assert result.stocks == []
    
    def test_to_domain_handles_empty_description(self, repository, mock_session):
        """测试 _to_domain 处理空 description"""
        po = Mock(spec=WatchListPO)
        po.id = str(uuid.uuid4())
        po.name = "无描述测试"
        po.description = None
        po.stocks = []
        po.created_at = datetime.now(timezone.utc)
        po.updated_at = datetime.now(timezone.utc)
        
        mock_query = Mock()
        mock_query.get = Mock(return_value=po)
        mock_session.query.return_value = mock_query
        
        watchlist_id = WatchListId.from_string(po.id)
        result = repository.find_by_id(watchlist_id)
        
        assert result is not None
        assert result.description is None
