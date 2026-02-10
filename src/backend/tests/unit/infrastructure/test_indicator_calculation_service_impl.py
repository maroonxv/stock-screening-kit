"""
IndicatorCalculationServiceImpl 单元测试

测试指标计算服务的各种功能：
- 基础指标计算
- 衍生指标计算
- 时间序列指标计算
- 批量计算
- 边界情况处理

Requirements:
- 4.5: IIndicatorCalculationService 接口实现
"""
import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared_kernel.value_objects.stock_code import StockCode
from contexts.screening.domain.models.stock import Stock
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.enums import IndicatorCategory
from contexts.screening.infrastructure.services.indicator_calculation_service_impl import (
    IndicatorCalculationServiceImpl
)


class TestIndicatorCalculationServiceImpl:
    """IndicatorCalculationServiceImpl 测试类"""
    
    @pytest.fixture
    def calc_service(self):
        """创建指标计算服务实例"""
        return IndicatorCalculationServiceImpl()
    
    @pytest.fixture
    def sample_stock(self):
        """创建示例股票"""
        return Stock(
            stock_code=StockCode("600000.SH"),
            stock_name="浦发银行",
            roe=0.12,
            pe=8.5,
            pb=0.8,
            eps=1.5,
            revenue=200000000000,
            net_profit=50000000000,
            debt_ratio=0.6,
            market_cap=300000000000,
            industry="银行",
            dividend_yield=0.04,
            revenue_growth=0.08,
            profit_growth=0.10
        )
    
    @pytest.fixture
    def stock_with_missing_data(self):
        """创建缺失数据的股票"""
        return Stock(
            stock_code=StockCode("600001.SH"),
            stock_name="测试股票",
            roe=0.15,
            pe=None,  # 缺失 PE
            pb=1.2,
            eps=None,  # 缺失 EPS
        )
    
    # ==================== 基础指标测试 ====================
    
    def test_calculate_basic_indicator_roe(self, calc_service, sample_stock):
        """测试计算基础指标 ROE"""
        result = calc_service.calculate_indicator(IndicatorField.ROE, sample_stock)
        assert result == 0.12
    
    def test_calculate_basic_indicator_pe(self, calc_service, sample_stock):
        """测试计算基础指标 PE"""
        result = calc_service.calculate_indicator(IndicatorField.PE, sample_stock)
        assert result == 8.5
    
    def test_calculate_basic_indicator_pb(self, calc_service, sample_stock):
        """测试计算基础指标 PB"""
        result = calc_service.calculate_indicator(IndicatorField.PB, sample_stock)
        assert result == 0.8
    
    def test_calculate_basic_indicator_industry(self, calc_service, sample_stock):
        """测试计算文本类型基础指标 INDUSTRY"""
        result = calc_service.calculate_indicator(IndicatorField.INDUSTRY, sample_stock)
        assert result == "银行"
    
    def test_calculate_basic_indicator_stock_name(self, calc_service, sample_stock):
        """测试计算文本类型基础指标 STOCK_NAME"""
        result = calc_service.calculate_indicator(IndicatorField.STOCK_NAME, sample_stock)
        assert result == "浦发银行"
    
    def test_calculate_basic_indicator_missing_value(self, calc_service, stock_with_missing_data):
        """测试计算缺失的基础指标"""
        result = calc_service.calculate_indicator(IndicatorField.PE, stock_with_missing_data)
        assert result is None
    
    # ==================== 衍生指标测试 ====================
    
    def test_calculate_derived_indicator_pe_pb_ratio(self, calc_service, sample_stock):
        """测试计算衍生指标 PE/PB 比率"""
        result = calc_service.calculate_indicator(IndicatorField.PE_PB_RATIO, sample_stock)
        expected = 8.5 / 0.8  # PE / PB
        assert result == pytest.approx(expected, rel=1e-6)
    
    def test_calculate_derived_indicator_roe_pe_product(self, calc_service, sample_stock):
        """测试计算衍生指标 ROE × PE"""
        result = calc_service.calculate_indicator(IndicatorField.ROE_PE_PRODUCT, sample_stock)
        expected = 0.12 * 8.5  # ROE × PE
        assert result == pytest.approx(expected, rel=1e-6)
    
    def test_calculate_derived_indicator_debt_to_equity(self, calc_service, sample_stock):
        """测试计算衍生指标负债权益比"""
        result = calc_service.calculate_indicator(IndicatorField.DEBT_TO_EQUITY, sample_stock)
        expected = 0.6 / (1 - 0.6)  # debt_ratio / (1 - debt_ratio)
        assert result == pytest.approx(expected, rel=1e-6)
    
    def test_calculate_derived_indicator_with_missing_dependency(self, calc_service, stock_with_missing_data):
        """测试计算依赖缺失的衍生指标"""
        # PE_PB_RATIO 需要 PE 和 PB，但 PE 缺失
        result = calc_service.calculate_indicator(IndicatorField.PE_PB_RATIO, stock_with_missing_data)
        assert result is None
    
    def test_calculate_pe_pb_ratio_with_zero_pb(self, calc_service):
        """测试 PB 为零时的 PE/PB 比率计算"""
        stock = Stock(
            stock_code=StockCode("600002.SH"),
            stock_name="测试股票",
            pe=10.0,
            pb=0.0  # PB 为零
        )
        result = calc_service.calculate_indicator(IndicatorField.PE_PB_RATIO, stock)
        assert result is None  # 除零应返回 None
    
    def test_calculate_debt_to_equity_with_100_percent_debt(self, calc_service):
        """测试资产负债率为 100% 时的负债权益比计算"""
        stock = Stock(
            stock_code=StockCode("600003.SH"),
            stock_name="测试股票",
            debt_ratio=1.0  # 100% 负债率
        )
        result = calc_service.calculate_indicator(IndicatorField.DEBT_TO_EQUITY, stock)
        assert result is None  # 无法计算
    
    # ==================== 时间序列指标测试 ====================
    
    def test_calculate_time_series_indicator_eps_growth(self, calc_service, sample_stock):
        """测试计算时间序列指标 EPS 增长率"""
        result = calc_service.calculate_indicator(IndicatorField.EPS_GROWTH_RATE, sample_stock)
        # MVP 阶段使用 profit_growth 作为近似
        assert result == 0.10
    
    def test_calculate_time_series_indicator_revenue_cagr(self, calc_service, sample_stock):
        """测试计算时间序列指标营收复合增长率"""
        result = calc_service.calculate_indicator(IndicatorField.REVENUE_CAGR_3Y, sample_stock)
        # MVP 阶段使用 revenue_growth 作为近似
        assert result == 0.08
    
    def test_calculate_time_series_indicator_not_available(self, calc_service, sample_stock):
        """测试计算不可用的时间序列指标"""
        result = calc_service.calculate_indicator(
            IndicatorField.ROE_CONTINUOUS_GROWTH_YEARS, sample_stock
        )
        # MVP 阶段没有历史数据，返回 None
        assert result is None
    
    # ==================== PEG 计算测试 ====================
    
    def test_calculate_peg_ratio(self, calc_service, sample_stock):
        """测试计算 PEG 比率"""
        result = calc_service.calculate_indicator(IndicatorField.PEG, sample_stock)
        # PEG = PE / (EPS增长率 * 100)
        # profit_growth = 0.10 (10%), 转换为百分比 = 10
        # PEG = 8.5 / 10 = 0.85
        assert result == pytest.approx(0.85, rel=1e-6)
    
    def test_calculate_peg_with_zero_growth(self, calc_service):
        """测试 EPS 增长率为零时的 PEG 计算"""
        stock = Stock(
            stock_code=StockCode("600004.SH"),
            stock_name="测试股票",
            pe=10.0,
            profit_growth=0.0  # 零增长
        )
        result = calc_service.calculate_indicator(IndicatorField.PEG, stock)
        assert result is None  # 除零应返回 None
    
    # ==================== 验证衍生指标测试 ====================
    
    def test_validate_derived_indicator_valid(self, calc_service, sample_stock):
        """测试验证有效的衍生指标"""
        result = calc_service.validate_derived_indicator(
            IndicatorField.PE_PB_RATIO, sample_stock
        )
        assert result is True
    
    def test_validate_derived_indicator_invalid(self, calc_service, stock_with_missing_data):
        """测试验证无效的衍生指标（依赖缺失）"""
        result = calc_service.validate_derived_indicator(
            IndicatorField.PE_PB_RATIO, stock_with_missing_data
        )
        assert result is False
    
    def test_validate_non_derived_indicator(self, calc_service, sample_stock):
        """测试验证非衍生指标（应始终返回 True）"""
        result = calc_service.validate_derived_indicator(
            IndicatorField.ROE, sample_stock
        )
        assert result is True
    
    # ==================== 批量计算测试 ====================
    
    def test_calculate_batch(self, calc_service, sample_stock):
        """测试批量计算多个指标"""
        fields = [IndicatorField.ROE, IndicatorField.PE, IndicatorField.PB]
        result = calc_service.calculate_batch(fields, sample_stock)
        
        assert len(result) == 3
        assert result[IndicatorField.ROE] == 0.12
        assert result[IndicatorField.PE] == 8.5
        assert result[IndicatorField.PB] == 0.8
    
    def test_calculate_batch_with_missing_values(self, calc_service, stock_with_missing_data):
        """测试批量计算包含缺失值的指标"""
        fields = [IndicatorField.ROE, IndicatorField.PE, IndicatorField.PB]
        result = calc_service.calculate_batch(fields, stock_with_missing_data)
        
        assert len(result) == 3
        assert result[IndicatorField.ROE] == 0.15
        assert result[IndicatorField.PE] is None  # 缺失
        assert result[IndicatorField.PB] == 1.2
    
    def test_calculate_batch_empty_fields(self, calc_service, sample_stock):
        """测试批量计算空字段列表"""
        result = calc_service.calculate_batch([], sample_stock)
        assert result == {}
    
    def test_calculate_batch_mixed_indicators(self, calc_service, sample_stock):
        """测试批量计算混合类型指标"""
        fields = [
            IndicatorField.ROE,  # 基础
            IndicatorField.PE_PB_RATIO,  # 衍生
            IndicatorField.EPS_GROWTH_RATE,  # 时间序列
            IndicatorField.INDUSTRY  # 文本
        ]
        result = calc_service.calculate_batch(fields, sample_stock)
        
        assert len(result) == 4
        assert result[IndicatorField.ROE] == 0.12
        assert result[IndicatorField.PE_PB_RATIO] == pytest.approx(8.5 / 0.8, rel=1e-6)
        assert result[IndicatorField.EPS_GROWTH_RATE] == 0.10
        assert result[IndicatorField.INDUSTRY] == "银行"


class TestIndicatorCalculationServiceEdgeCases:
    """边界情况测试"""
    
    @pytest.fixture
    def calc_service(self):
        """创建指标计算服务实例"""
        return IndicatorCalculationServiceImpl()
    
    def test_stock_with_all_none_values(self, calc_service):
        """测试所有指标都为 None 的股票"""
        stock = Stock(
            stock_code=StockCode("600005.SH"),
            stock_name="空数据股票"
        )
        
        # 基础指标
        assert calc_service.calculate_indicator(IndicatorField.ROE, stock) is None
        assert calc_service.calculate_indicator(IndicatorField.PE, stock) is None
        
        # 衍生指标
        assert calc_service.calculate_indicator(IndicatorField.PE_PB_RATIO, stock) is None
        
        # 时间序列指标
        assert calc_service.calculate_indicator(IndicatorField.EPS_GROWTH_RATE, stock) is None
    
    def test_stock_with_negative_values(self, calc_service):
        """测试包含负值的股票"""
        stock = Stock(
            stock_code=StockCode("600006.SH"),
            stock_name="负值股票",
            roe=-0.05,  # 负 ROE
            pe=-10.0,   # 负 PE（亏损）
            pb=0.5
        )
        
        # 基础指标应正常返回负值
        assert calc_service.calculate_indicator(IndicatorField.ROE, stock) == -0.05
        assert calc_service.calculate_indicator(IndicatorField.PE, stock) == -10.0
        
        # 衍生指标也应正常计算
        pe_pb = calc_service.calculate_indicator(IndicatorField.PE_PB_RATIO, stock)
        assert pe_pb == pytest.approx(-10.0 / 0.5, rel=1e-6)
    
    def test_stock_with_very_large_values(self, calc_service):
        """测试包含极大值的股票"""
        stock = Stock(
            stock_code=StockCode("600007.SH"),
            stock_name="大值股票",
            roe=0.5,
            pe=1000.0,
            pb=100.0,
            market_cap=1e15  # 1000万亿
        )
        
        assert calc_service.calculate_indicator(IndicatorField.MARKET_CAP, stock) == 1e15
        pe_pb = calc_service.calculate_indicator(IndicatorField.PE_PB_RATIO, stock)
        assert pe_pb == pytest.approx(10.0, rel=1e-6)
    
    def test_stock_with_very_small_values(self, calc_service):
        """测试包含极小值的股票"""
        stock = Stock(
            stock_code=StockCode("600008.SH"),
            stock_name="小值股票",
            roe=0.001,
            pe=0.1,
            pb=0.01
        )
        
        pe_pb = calc_service.calculate_indicator(IndicatorField.PE_PB_RATIO, stock)
        assert pe_pb == pytest.approx(10.0, rel=1e-6)
