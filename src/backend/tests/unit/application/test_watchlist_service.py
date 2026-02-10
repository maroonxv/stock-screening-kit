"""
WatchListService 单元测试

测试应用层服务的业务逻辑编排。
使用 Mock 模拟 Repository 以隔离依赖。

Requirements:
- 7.2: 实现 create_watchlist、add_stock、remove_stock、get_watchlist、list_watchlists 方法
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock
import uuid

from contexts.screening.application.services.watchlist_service import WatchListService
from contexts.screening.domain.models.watchlist import WatchList
from contexts.screening.domain.value_objects.identifiers import WatchListId
from contexts.screening.domain.value_objects.watched_stock import WatchedStock
from contexts.screening.domain.exceptions import (
    DuplicateNameError,
    WatchListNotFoundError,
    DuplicateStockError,
    StockNotFoundError,
)
from shared_kernel.value_objects.stock_code import StockCode


class TestWatchListService:
    """WatchListService 单元测试"""
    
    @pytest.fixture
    def mock_watchlist_repo(self):
        """创建 Mock 自选股列表仓储"""
        repo = Mock()
        repo.save = Mock()
        repo.find_by_id = Mock(return_value=None)
        repo.find_by_name = Mock(return_value=None)
        repo.find_all = Mock(return_value=[])
        repo.delete = Mock()
        repo.exists = Mock(return_value=False)
        repo.count = Mock(return_value=0)
        return repo
    
    @pytest.fixture
    def service(self, mock_watchlist_repo):
        """创建 WatchListService 实例"""
        return WatchListService(watchlist_repo=mock_watchlist_repo)
    
    @pytest.fixture
    def sample_watchlist(self):
        """创建示例 WatchList 领域对象"""
        watchlist_id = WatchListId.generate()
        now = datetime.now(timezone.utc)
        
        return WatchList(
            watchlist_id=watchlist_id,
            name="测试自选股",
            description="这是一个测试自选股列表",
            stocks=[],
            created_at=now,
            updated_at=now
        )
    
    @pytest.fixture
    def sample_watchlist_with_stock(self):
        """创建包含股票的示例 WatchList 领域对象"""
        watchlist_id = WatchListId.generate()
        now = datetime.now(timezone.utc)
        
        stock_code = StockCode("600000.SH")
        watched_stock = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            added_at=now,
            note="测试备注",
            tags=["银行", "金融"]
        )
        
        return WatchList(
            watchlist_id=watchlist_id,
            name="测试自选股",
            description="这是一个测试自选股列表",
            stocks=[watched_stock],
            created_at=now,
            updated_at=now
        )
    
    # ==================== create_watchlist 测试 ====================
    
    def test_create_watchlist_success(self, service, mock_watchlist_repo):
        """测试成功创建自选股列表"""
        # 设置 mock：名称不存在
        mock_watchlist_repo.find_by_name.return_value = None
        
        # 执行创建
        result = service.create_watchlist(
            name="新自选股列表",
            description="测试描述"
        )
        
        # 验证返回的列表
        assert result is not None
        assert result.name == "新自选股列表"
        assert result.description == "测试描述"
        assert result.stock_count() == 0
        
        # 验证 save 被调用
        mock_watchlist_repo.save.assert_called_once()
    
    def test_create_watchlist_duplicate_name_raises_error(
        self,
        service,
        mock_watchlist_repo,
        sample_watchlist
    ):
        """测试创建重复名称列表时抛出 DuplicateNameError"""
        # 设置 mock：名称已存在
        mock_watchlist_repo.find_by_name.return_value = sample_watchlist
        
        # 执行创建并验证异常
        with pytest.raises(DuplicateNameError) as exc_info:
            service.create_watchlist(
                name="测试自选股",  # 与 sample_watchlist 同名
                description="测试描述"
            )
        
        assert "测试自选股" in str(exc_info.value)
        
        # 验证 save 未被调用
        mock_watchlist_repo.save.assert_not_called()
    
    def test_create_watchlist_empty_name_raises_error(
        self,
        service,
        mock_watchlist_repo
    ):
        """测试创建空名称列表时抛出 ValueError"""
        # 设置 mock：名称不存在
        mock_watchlist_repo.find_by_name.return_value = None
        
        # 执行创建并验证异常
        with pytest.raises(ValueError) as exc_info:
            service.create_watchlist(
                name="",  # 空名称
                description="测试描述"
            )
        
        assert "名称" in str(exc_info.value) or "空" in str(exc_info.value)
    
    def test_create_watchlist_without_description(
        self,
        service,
        mock_watchlist_repo
    ):
        """测试不提供描述时成功创建列表"""
        # 设置 mock：名称不存在
        mock_watchlist_repo.find_by_name.return_value = None
        
        # 执行创建（不提供 description）
        result = service.create_watchlist(name="简单列表")
        
        # 验证返回的列表
        assert result is not None
        assert result.name == "简单列表"
        assert result.description is None
    
    # ==================== add_stock 测试 ====================
    
    def test_add_stock_success(
        self,
        service,
        mock_watchlist_repo,
        sample_watchlist
    ):
        """测试成功添加股票到列表"""
        # 设置 mock：列表存在
        mock_watchlist_repo.find_by_id.return_value = sample_watchlist
        
        # 执行添加
        result = service.add_stock(
            watchlist_id_str=sample_watchlist.watchlist_id.value,
            stock_code_str="600000.SH",
            stock_name="浦发银行",
            note="测试备注",
            tags=["银行", "金融"]
        )
        
        # 验证返回的列表
        assert result is not None
        assert result.stock_count() == 1
        assert result.contains(StockCode("600000.SH"))
        
        # 验证 save 被调用
        mock_watchlist_repo.save.assert_called_once()
    
    def test_add_stock_watchlist_not_found_raises_error(
        self,
        service,
        mock_watchlist_repo
    ):
        """测试向不存在的列表添加股票时抛出 WatchListNotFoundError"""
        # 设置 mock：列表不存在
        mock_watchlist_repo.find_by_id.return_value = None
        
        watchlist_id = str(uuid.uuid4())
        
        # 执行添加并验证异常
        with pytest.raises(WatchListNotFoundError) as exc_info:
            service.add_stock(
                watchlist_id_str=watchlist_id,
                stock_code_str="600000.SH",
                stock_name="浦发银行"
            )
        
        assert watchlist_id in str(exc_info.value)
        
        # 验证 save 未被调用
        mock_watchlist_repo.save.assert_not_called()
    
    def test_add_stock_duplicate_raises_error(
        self,
        service,
        mock_watchlist_repo,
        sample_watchlist_with_stock
    ):
        """测试添加重复股票时抛出 DuplicateStockError"""
        # 设置 mock：列表存在且已包含该股票
        mock_watchlist_repo.find_by_id.return_value = sample_watchlist_with_stock
        
        # 执行添加并验证异常
        with pytest.raises(DuplicateStockError) as exc_info:
            service.add_stock(
                watchlist_id_str=sample_watchlist_with_stock.watchlist_id.value,
                stock_code_str="600000.SH",  # 已存在的股票
                stock_name="浦发银行"
            )
        
        assert "600000.SH" in str(exc_info.value)
        
        # 验证 save 未被调用
        mock_watchlist_repo.save.assert_not_called()
    
    def test_add_stock_invalid_code_raises_error(
        self,
        service,
        mock_watchlist_repo,
        sample_watchlist
    ):
        """测试添加无效股票代码时抛出 ValueError"""
        # 设置 mock：列表存在
        mock_watchlist_repo.find_by_id.return_value = sample_watchlist
        
        # 执行添加并验证异常
        with pytest.raises(ValueError):
            service.add_stock(
                watchlist_id_str=sample_watchlist.watchlist_id.value,
                stock_code_str="INVALID",  # 无效的股票代码
                stock_name="无效股票"
            )
    
    def test_add_stock_without_optional_params(
        self,
        service,
        mock_watchlist_repo,
        sample_watchlist
    ):
        """测试不提供可选参数时成功添加股票"""
        # 设置 mock：列表存在
        mock_watchlist_repo.find_by_id.return_value = sample_watchlist
        
        # 执行添加（不提供 note 和 tags）
        result = service.add_stock(
            watchlist_id_str=sample_watchlist.watchlist_id.value,
            stock_code_str="600000.SH",
            stock_name="浦发银行"
        )
        
        # 验证返回的列表
        assert result is not None
        assert result.stock_count() == 1
    
    # ==================== remove_stock 测试 ====================
    
    def test_remove_stock_success(
        self,
        service,
        mock_watchlist_repo,
        sample_watchlist_with_stock
    ):
        """测试成功从列表移除股票"""
        # 设置 mock：列表存在且包含该股票
        mock_watchlist_repo.find_by_id.return_value = sample_watchlist_with_stock
        
        # 执行移除
        result = service.remove_stock(
            watchlist_id_str=sample_watchlist_with_stock.watchlist_id.value,
            stock_code_str="600000.SH"
        )
        
        # 验证返回的列表
        assert result is not None
        assert result.stock_count() == 0
        assert not result.contains(StockCode("600000.SH"))
        
        # 验证 save 被调用
        mock_watchlist_repo.save.assert_called_once()
    
    def test_remove_stock_watchlist_not_found_raises_error(
        self,
        service,
        mock_watchlist_repo
    ):
        """测试从不存在的列表移除股票时抛出 WatchListNotFoundError"""
        # 设置 mock：列表不存在
        mock_watchlist_repo.find_by_id.return_value = None
        
        watchlist_id = str(uuid.uuid4())
        
        # 执行移除并验证异常
        with pytest.raises(WatchListNotFoundError) as exc_info:
            service.remove_stock(
                watchlist_id_str=watchlist_id,
                stock_code_str="600000.SH"
            )
        
        assert watchlist_id in str(exc_info.value)
        
        # 验证 save 未被调用
        mock_watchlist_repo.save.assert_not_called()
    
    def test_remove_stock_not_found_raises_error(
        self,
        service,
        mock_watchlist_repo,
        sample_watchlist
    ):
        """测试移除不存在的股票时抛出 StockNotFoundError"""
        # 设置 mock：列表存在但不包含该股票
        mock_watchlist_repo.find_by_id.return_value = sample_watchlist
        
        # 执行移除并验证异常
        with pytest.raises(StockNotFoundError) as exc_info:
            service.remove_stock(
                watchlist_id_str=sample_watchlist.watchlist_id.value,
                stock_code_str="600000.SH"  # 不存在的股票
            )
        
        assert "600000.SH" in str(exc_info.value)
        
        # 验证 save 未被调用
        mock_watchlist_repo.save.assert_not_called()
    
    def test_remove_stock_invalid_code_raises_error(
        self,
        service,
        mock_watchlist_repo,
        sample_watchlist_with_stock
    ):
        """测试移除无效股票代码时抛出 ValueError"""
        # 设置 mock：列表存在
        mock_watchlist_repo.find_by_id.return_value = sample_watchlist_with_stock
        
        # 执行移除并验证异常
        with pytest.raises(ValueError):
            service.remove_stock(
                watchlist_id_str=sample_watchlist_with_stock.watchlist_id.value,
                stock_code_str="INVALID"  # 无效的股票代码
            )
    
    # ==================== get_watchlist 测试 ====================
    
    def test_get_watchlist_found(
        self,
        service,
        mock_watchlist_repo,
        sample_watchlist
    ):
        """测试获取存在的列表"""
        # 设置 mock：列表存在
        mock_watchlist_repo.find_by_id.return_value = sample_watchlist
        
        # 执行获取
        result = service.get_watchlist(sample_watchlist.watchlist_id.value)
        
        # 验证返回的列表
        assert result is not None
        assert result.watchlist_id == sample_watchlist.watchlist_id
    
    def test_get_watchlist_not_found(
        self,
        service,
        mock_watchlist_repo
    ):
        """测试获取不存在的列表返回 None"""
        # 设置 mock：列表不存在
        mock_watchlist_repo.find_by_id.return_value = None
        
        watchlist_id = str(uuid.uuid4())
        
        # 执行获取
        result = service.get_watchlist(watchlist_id)
        
        # 验证返回 None
        assert result is None
    
    # ==================== list_watchlists 测试 ====================
    
    def test_list_watchlists_returns_list(
        self,
        service,
        mock_watchlist_repo,
        sample_watchlist
    ):
        """测试列出列表返回列表"""
        # 设置 mock：返回列表
        mock_watchlist_repo.find_all.return_value = [sample_watchlist]
        
        # 执行列出
        result = service.list_watchlists()
        
        # 验证返回列表
        assert len(result) == 1
        assert result[0].watchlist_id == sample_watchlist.watchlist_id
    
    def test_list_watchlists_empty(
        self,
        service,
        mock_watchlist_repo
    ):
        """测试列出列表返回空列表"""
        # 设置 mock：返回空列表
        mock_watchlist_repo.find_all.return_value = []
        
        # 执行列出
        result = service.list_watchlists()
        
        # 验证返回空列表
        assert result == []
    
    def test_list_watchlists_with_pagination(
        self,
        service,
        mock_watchlist_repo
    ):
        """测试列出列表使用分页参数"""
        # 设置 mock
        mock_watchlist_repo.find_all.return_value = []
        
        # 执行列出
        service.list_watchlists(limit=50, offset=10)
        
        # 验证分页参数
        mock_watchlist_repo.find_all.assert_called_once_with(limit=50, offset=10)
    
    # ==================== delete_watchlist 测试 ====================
    
    def test_delete_watchlist_success(
        self,
        service,
        mock_watchlist_repo,
        sample_watchlist
    ):
        """测试成功删除列表"""
        # 设置 mock：列表存在
        mock_watchlist_repo.exists.return_value = True
        
        # 执行删除
        service.delete_watchlist(sample_watchlist.watchlist_id.value)
        
        # 验证 delete 被调用
        mock_watchlist_repo.delete.assert_called_once()
    
    def test_delete_watchlist_not_found_raises_error(
        self,
        service,
        mock_watchlist_repo
    ):
        """测试删除不存在的列表时抛出 WatchListNotFoundError"""
        # 设置 mock：列表不存在
        mock_watchlist_repo.exists.return_value = False
        
        watchlist_id = str(uuid.uuid4())
        
        # 执行删除并验证异常
        with pytest.raises(WatchListNotFoundError) as exc_info:
            service.delete_watchlist(watchlist_id)
        
        assert watchlist_id in str(exc_info.value)
        
        # 验证 delete 未被调用
        mock_watchlist_repo.delete.assert_not_called()
    
    # ==================== update_watchlist 测试 ====================
    
    def test_update_watchlist_success(
        self,
        service,
        mock_watchlist_repo,
        sample_watchlist
    ):
        """测试成功更新列表"""
        # 设置 mock：列表存在
        mock_watchlist_repo.find_by_id.return_value = sample_watchlist
        mock_watchlist_repo.find_by_name.return_value = None
        
        # 执行更新
        result = service.update_watchlist(
            watchlist_id_str=sample_watchlist.watchlist_id.value,
            name="更新后的名称",
            description="更新后的描述"
        )
        
        # 验证返回的列表
        assert result is not None
        assert result.name == "更新后的名称"
        assert result.description == "更新后的描述"
        
        # 验证 save 被调用
        mock_watchlist_repo.save.assert_called_once()
    
    def test_update_watchlist_not_found_raises_error(
        self,
        service,
        mock_watchlist_repo
    ):
        """测试更新不存在的列表时抛出 WatchListNotFoundError"""
        # 设置 mock：列表不存在
        mock_watchlist_repo.find_by_id.return_value = None
        
        watchlist_id = str(uuid.uuid4())
        
        # 执行更新并验证异常
        with pytest.raises(WatchListNotFoundError) as exc_info:
            service.update_watchlist(
                watchlist_id_str=watchlist_id,
                name="新名称"
            )
        
        assert watchlist_id in str(exc_info.value)
    
    def test_update_watchlist_duplicate_name_raises_error(
        self,
        service,
        mock_watchlist_repo,
        sample_watchlist
    ):
        """测试更新为重复名称时抛出 DuplicateNameError"""
        # 创建另一个列表
        other_watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="其他列表"
        )
        
        # 设置 mock：当前列表存在，新名称与其他列表重复
        mock_watchlist_repo.find_by_id.return_value = sample_watchlist
        mock_watchlist_repo.find_by_name.return_value = other_watchlist
        
        # 执行更新并验证异常
        with pytest.raises(DuplicateNameError) as exc_info:
            service.update_watchlist(
                watchlist_id_str=sample_watchlist.watchlist_id.value,
                name="其他列表"  # 与 other_watchlist 同名
            )
        
        assert "其他列表" in str(exc_info.value)
    
    def test_update_watchlist_same_name_allowed(
        self,
        service,
        mock_watchlist_repo,
        sample_watchlist
    ):
        """测试更新为相同名称时允许（自己的名称）"""
        # 设置 mock：当前列表存在，名称查询返回自己
        mock_watchlist_repo.find_by_id.return_value = sample_watchlist
        mock_watchlist_repo.find_by_name.return_value = sample_watchlist  # 返回自己
        
        # 执行更新（使用相同名称）
        result = service.update_watchlist(
            watchlist_id_str=sample_watchlist.watchlist_id.value,
            name=sample_watchlist.name  # 相同名称
        )
        
        # 验证成功
        assert result is not None
        mock_watchlist_repo.save.assert_called_once()
    
    def test_update_watchlist_partial_update(
        self,
        service,
        mock_watchlist_repo,
        sample_watchlist
    ):
        """测试部分更新（只更新部分字段）"""
        original_name = sample_watchlist.name
        
        # 设置 mock：列表存在
        mock_watchlist_repo.find_by_id.return_value = sample_watchlist
        
        # 只更新 description
        result = service.update_watchlist(
            watchlist_id_str=sample_watchlist.watchlist_id.value,
            description="新描述"
        )
        
        # 验证只有 description 被更新
        assert result is not None
        assert result.name == original_name  # 名称未变
        assert result.description == "新描述"  # description 已更新


class TestWatchListServiceIntegration:
    """WatchListService 集成测试（使用真实领域对象）"""
    
    @pytest.fixture
    def mock_watchlist_repo(self):
        """创建 Mock 自选股列表仓储"""
        repo = Mock()
        repo.save = Mock()
        repo.find_by_id = Mock(return_value=None)
        repo.find_by_name = Mock(return_value=None)
        repo.find_all = Mock(return_value=[])
        repo.delete = Mock()
        repo.exists = Mock(return_value=False)
        return repo
    
    @pytest.fixture
    def service(self, mock_watchlist_repo):
        """创建 WatchListService 实例"""
        return WatchListService(watchlist_repo=mock_watchlist_repo)
    
    def test_create_and_get_watchlist(
        self,
        service,
        mock_watchlist_repo
    ):
        """测试创建列表后能够获取"""
        # 创建列表
        created = service.create_watchlist(
            name="集成测试列表",
            description="集成测试描述"
        )
        
        # 设置 mock 返回创建的列表
        mock_watchlist_repo.find_by_id.return_value = created
        
        # 获取列表
        retrieved = service.get_watchlist(created.watchlist_id.value)
        
        # 验证
        assert retrieved is not None
        assert retrieved.watchlist_id == created.watchlist_id
        assert retrieved.name == "集成测试列表"
        assert retrieved.description == "集成测试描述"
    
    def test_add_and_remove_stock_workflow(
        self,
        service,
        mock_watchlist_repo
    ):
        """测试添加和移除股票的完整工作流"""
        # 创建列表
        watchlist = service.create_watchlist(name="工作流测试列表")
        
        # 设置 mock 返回创建的列表
        mock_watchlist_repo.find_by_id.return_value = watchlist
        
        # 添加股票
        watchlist = service.add_stock(
            watchlist_id_str=watchlist.watchlist_id.value,
            stock_code_str="600000.SH",
            stock_name="浦发银行"
        )
        
        assert watchlist.stock_count() == 1
        assert watchlist.contains(StockCode("600000.SH"))
        
        # 移除股票
        watchlist = service.remove_stock(
            watchlist_id_str=watchlist.watchlist_id.value,
            stock_code_str="600000.SH"
        )
        
        assert watchlist.stock_count() == 0
        assert not watchlist.contains(StockCode("600000.SH"))
