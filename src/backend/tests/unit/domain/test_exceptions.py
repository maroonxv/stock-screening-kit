"""
单元测试：领域层异常类

验证所有领域异常的继承关系和行为
Validates: Requirements 2.6, 2.7, 2.8, 2.9
"""
import pytest

from contexts.screening.domain.exceptions import (
    DomainError,
    DuplicateStockError,
    StockNotFoundError,
    DuplicateNameError,
    StrategyNotFoundError,
    WatchListNotFoundError,
    ScoringError,
    IndicatorCalculationError,
    ValidationError,
)


class TestDomainError:
    """DomainError 基础异常测试"""
    
    def test_inherits_from_exception(self):
        """测试 DomainError 继承自 Exception"""
        assert issubclass(DomainError, Exception)
    
    def test_can_be_raised(self):
        """测试 DomainError 可以被抛出"""
        with pytest.raises(DomainError):
            raise DomainError("测试错误")
    
    def test_can_be_raised_with_message(self):
        """测试 DomainError 可以携带错误消息"""
        error_message = "这是一个领域错误"
        with pytest.raises(DomainError) as exc_info:
            raise DomainError(error_message)
        assert str(exc_info.value) == error_message
    
    def test_can_be_raised_without_message(self):
        """测试 DomainError 可以不带消息抛出"""
        with pytest.raises(DomainError):
            raise DomainError()


class TestDuplicateStockError:
    """DuplicateStockError 异常测试"""
    
    def test_inherits_from_domain_error(self):
        """测试 DuplicateStockError 继承自 DomainError"""
        assert issubclass(DuplicateStockError, DomainError)
    
    def test_can_be_raised(self):
        """测试 DuplicateStockError 可以被抛出"""
        with pytest.raises(DuplicateStockError):
            raise DuplicateStockError("股票 600000.SH 已存在于列表中")
    
    def test_can_be_caught_as_domain_error(self):
        """测试 DuplicateStockError 可以作为 DomainError 捕获"""
        with pytest.raises(DomainError):
            raise DuplicateStockError("重复股票")
    
    def test_message_preserved(self):
        """测试错误消息被保留"""
        message = "股票 600000.SH 已存在于列表中"
        with pytest.raises(DuplicateStockError) as exc_info:
            raise DuplicateStockError(message)
        assert str(exc_info.value) == message


class TestStockNotFoundError:
    """StockNotFoundError 异常测试"""
    
    def test_inherits_from_domain_error(self):
        """测试 StockNotFoundError 继承自 DomainError"""
        assert issubclass(StockNotFoundError, DomainError)
    
    def test_can_be_raised(self):
        """测试 StockNotFoundError 可以被抛出"""
        with pytest.raises(StockNotFoundError):
            raise StockNotFoundError("股票 600000.SH 不在列表中")
    
    def test_can_be_caught_as_domain_error(self):
        """测试 StockNotFoundError 可以作为 DomainError 捕获"""
        with pytest.raises(DomainError):
            raise StockNotFoundError("股票不存在")
    
    def test_message_preserved(self):
        """测试错误消息被保留"""
        message = "股票 600000.SH 不在列表中"
        with pytest.raises(StockNotFoundError) as exc_info:
            raise StockNotFoundError(message)
        assert str(exc_info.value) == message


class TestDuplicateNameError:
    """DuplicateNameError 异常测试"""
    
    def test_inherits_from_domain_error(self):
        """测试 DuplicateNameError 继承自 DomainError"""
        assert issubclass(DuplicateNameError, DomainError)
    
    def test_can_be_raised(self):
        """测试 DuplicateNameError 可以被抛出"""
        with pytest.raises(DuplicateNameError):
            raise DuplicateNameError("策略名称 '高ROE策略' 已存在")
    
    def test_can_be_caught_as_domain_error(self):
        """测试 DuplicateNameError 可以作为 DomainError 捕获"""
        with pytest.raises(DomainError):
            raise DuplicateNameError("名称重复")
    
    def test_message_preserved(self):
        """测试错误消息被保留"""
        message = "策略名称 '高ROE策略' 已存在"
        with pytest.raises(DuplicateNameError) as exc_info:
            raise DuplicateNameError(message)
        assert str(exc_info.value) == message


class TestStrategyNotFoundError:
    """StrategyNotFoundError 异常测试"""
    
    def test_inherits_from_domain_error(self):
        """测试 StrategyNotFoundError 继承自 DomainError"""
        assert issubclass(StrategyNotFoundError, DomainError)
    
    def test_can_be_raised(self):
        """测试 StrategyNotFoundError 可以被抛出"""
        with pytest.raises(StrategyNotFoundError):
            raise StrategyNotFoundError("策略 abc-123 不存在")
    
    def test_can_be_caught_as_domain_error(self):
        """测试 StrategyNotFoundError 可以作为 DomainError 捕获"""
        with pytest.raises(DomainError):
            raise StrategyNotFoundError("策略不存在")
    
    def test_message_preserved(self):
        """测试错误消息被保留"""
        message = "策略 abc-123 不存在"
        with pytest.raises(StrategyNotFoundError) as exc_info:
            raise StrategyNotFoundError(message)
        assert str(exc_info.value) == message


class TestWatchListNotFoundError:
    """WatchListNotFoundError 异常测试"""
    
    def test_inherits_from_domain_error(self):
        """测试 WatchListNotFoundError 继承自 DomainError"""
        assert issubclass(WatchListNotFoundError, DomainError)
    
    def test_can_be_raised(self):
        """测试 WatchListNotFoundError 可以被抛出"""
        with pytest.raises(WatchListNotFoundError):
            raise WatchListNotFoundError("自选股列表 xyz-456 不存在")
    
    def test_can_be_caught_as_domain_error(self):
        """测试 WatchListNotFoundError 可以作为 DomainError 捕获"""
        with pytest.raises(DomainError):
            raise WatchListNotFoundError("列表不存在")
    
    def test_message_preserved(self):
        """测试错误消息被保留"""
        message = "自选股列表 xyz-456 不存在"
        with pytest.raises(WatchListNotFoundError) as exc_info:
            raise WatchListNotFoundError(message)
        assert str(exc_info.value) == message


class TestScoringError:
    """ScoringError 异常测试"""
    
    def test_inherits_from_domain_error(self):
        """测试 ScoringError 继承自 DomainError"""
        assert issubclass(ScoringError, DomainError)
    
    def test_can_be_raised(self):
        """测试 ScoringError 可以被抛出"""
        with pytest.raises(ScoringError):
            raise ScoringError("评分计算失败：权重配置无效")
    
    def test_can_be_caught_as_domain_error(self):
        """测试 ScoringError 可以作为 DomainError 捕获"""
        with pytest.raises(DomainError):
            raise ScoringError("评分错误")
    
    def test_message_preserved(self):
        """测试错误消息被保留"""
        message = "评分计算失败：权重配置无效"
        with pytest.raises(ScoringError) as exc_info:
            raise ScoringError(message)
        assert str(exc_info.value) == message


class TestIndicatorCalculationError:
    """IndicatorCalculationError 异常测试"""
    
    def test_inherits_from_domain_error(self):
        """测试 IndicatorCalculationError 继承自 DomainError"""
        assert issubclass(IndicatorCalculationError, DomainError)
    
    def test_can_be_raised(self):
        """测试 IndicatorCalculationError 可以被抛出"""
        with pytest.raises(IndicatorCalculationError):
            raise IndicatorCalculationError("指标 ROE 计算失败：数据缺失")
    
    def test_can_be_caught_as_domain_error(self):
        """测试 IndicatorCalculationError 可以作为 DomainError 捕获"""
        with pytest.raises(DomainError):
            raise IndicatorCalculationError("计算错误")
    
    def test_message_preserved(self):
        """测试错误消息被保留"""
        message = "指标 ROE 计算失败：数据缺失"
        with pytest.raises(IndicatorCalculationError) as exc_info:
            raise IndicatorCalculationError(message)
        assert str(exc_info.value) == message


class TestValidationError:
    """ValidationError 异常测试"""
    
    def test_inherits_from_domain_error(self):
        """测试 ValidationError 继承自 DomainError"""
        assert issubclass(ValidationError, DomainError)
    
    def test_can_be_raised(self):
        """测试 ValidationError 可以被抛出"""
        with pytest.raises(ValidationError):
            raise ValidationError("策略名称不能为空")
    
    def test_can_be_caught_as_domain_error(self):
        """测试 ValidationError 可以作为 DomainError 捕获"""
        with pytest.raises(DomainError):
            raise ValidationError("验证失败")
    
    def test_message_preserved(self):
        """测试错误消息被保留"""
        message = "策略名称不能为空"
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(message)
        assert str(exc_info.value) == message


class TestExceptionHierarchy:
    """异常继承层次结构测试"""
    
    def test_all_exceptions_inherit_from_domain_error(self):
        """测试所有领域异常都继承自 DomainError"""
        exception_classes = [
            DuplicateStockError,
            StockNotFoundError,
            DuplicateNameError,
            StrategyNotFoundError,
            WatchListNotFoundError,
            ScoringError,
            IndicatorCalculationError,
            ValidationError,
        ]
        for exc_class in exception_classes:
            assert issubclass(exc_class, DomainError), \
                f"{exc_class.__name__} 应该继承自 DomainError"
    
    def test_domain_error_inherits_from_exception(self):
        """测试 DomainError 继承自 Exception"""
        assert issubclass(DomainError, Exception)
    
    def test_all_exceptions_can_be_caught_by_domain_error(self):
        """测试所有领域异常都可以被 DomainError 捕获"""
        exception_classes = [
            DuplicateStockError,
            StockNotFoundError,
            DuplicateNameError,
            StrategyNotFoundError,
            WatchListNotFoundError,
            ScoringError,
            IndicatorCalculationError,
            ValidationError,
        ]
        for exc_class in exception_classes:
            try:
                raise exc_class("测试消息")
            except DomainError as e:
                assert isinstance(e, exc_class)
            except Exception:
                pytest.fail(f"{exc_class.__name__} 应该可以被 DomainError 捕获")
    
    def test_exception_count(self):
        """测试异常类数量正确"""
        # 包括 DomainError 在内共 9 个异常类
        from contexts.screening.domain import exceptions
        exception_classes = [
            name for name in dir(exceptions)
            if isinstance(getattr(exceptions, name), type)
            and issubclass(getattr(exceptions, name), Exception)
            and name != 'Exception'
        ]
        assert len(exception_classes) == 11, \
            f"应该有 11 个异常类，实际有 {len(exception_classes)} 个"
