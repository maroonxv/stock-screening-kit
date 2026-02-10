"""
ScoringServiceImpl 单元测试

测试评分服务的各种功能：
- Min-Max 归一化评分
- Z-Score 归一化评分
- 无归一化评分
- 边界情况处理（空列表、缺失值、除零等）

Requirements:
- 4.4: IScoringService 接口实现
"""
import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared_kernel.value_objects.stock_code import StockCode
from contexts.screening.domain.models.stock import Stock
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.enums import NormalizationMethod
from contexts.screening.domain.value_objects.scoring_config import ScoringConfig
from contexts.screening.infrastructure.services.scoring_service_impl import ScoringServiceImpl
from contexts.screening.infrastructure.services.indicator_calculation_service_impl import (
    IndicatorCalculationServiceImpl
)


class TestScoringServiceImpl:
    """ScoringServiceImpl 测试类"""
    
    @pytest.fixture
    def scoring_service(self):
        """创建评分服务实例"""
        return ScoringServiceImpl()
    
    @pytest.fixture
    def calc_service(self):
        """创建指标计算服务实例"""
        return IndicatorCalculationServiceImpl()
    
    @pytest.fixture
    def sample_stocks(self):
        """创建示例股票列表"""
        return [
            Stock(
                stock_code=StockCode("600000.SH"),
                stock_name="股票A",
                roe=0.20,  # 最高 ROE
                pe=10.0,
                pb=1.0
            ),
            Stock(
                stock_code=StockCode("600001.SH"),
                stock_name="股票B",
                roe=0.15,
                pe=15.0,
                pb=1.5
            ),
            Stock(
                stock_code=StockCode("600002.SH"),
                stock_name="股票C",
                roe=0.10,  # 最低 ROE
                pe=20.0,
                pb=2.0
            ),
        ]
    
    @pytest.fixture
    def single_indicator_config(self):
        """创建单指标评分配置"""
        return ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
    
    @pytest.fixture
    def multi_indicator_config(self):
        """创建多指标评分配置"""
        return ScoringConfig(
            weights={
                IndicatorField.ROE: 0.5,
                IndicatorField.PE: 0.3,
                IndicatorField.PB: 0.2
            },
            normalization_method=NormalizationMethod.MIN_MAX
        )
    
    # ==================== 基本功能测试 ====================
    
    def test_score_stocks_empty_list(self, scoring_service, calc_service, single_indicator_config):
        """测试空股票列表"""
        result = scoring_service.score_stocks([], single_indicator_config, calc_service)
        assert result == []
    
    def test_score_stocks_single_stock(self, scoring_service, calc_service, single_indicator_config):
        """测试单只股票评分"""
        stocks = [
            Stock(
                stock_code=StockCode("600000.SH"),
                stock_name="单只股票",
                roe=0.15
            )
        ]
        result = scoring_service.score_stocks(stocks, single_indicator_config, calc_service)
        
        assert len(result) == 1
        assert result[0].stock_code.code == "600000.SH"
        assert result[0].stock_name == "单只股票"
        # 单只股票的 min-max 归一化结果为 0.5（因为 min == max）
        assert result[0].score == pytest.approx(0.5, rel=1e-6)
    
    def test_score_stocks_returns_scored_stock_objects(
        self, scoring_service, calc_service, sample_stocks, single_indicator_config
    ):
        """测试返回 ScoredStock 对象"""
        result = scoring_service.score_stocks(
            sample_stocks, single_indicator_config, calc_service
        )
        
        assert len(result) == 3
        for scored_stock in result:
            assert hasattr(scored_stock, 'stock_code')
            assert hasattr(scored_stock, 'stock_name')
            assert hasattr(scored_stock, 'score')
            assert hasattr(scored_stock, 'score_breakdown')
            assert hasattr(scored_stock, 'indicator_values')
    
    # ==================== Min-Max 归一化测试 ====================
    
    def test_min_max_normalization_single_indicator(
        self, scoring_service, calc_service, sample_stocks, single_indicator_config
    ):
        """测试单指标 Min-Max 归一化"""
        result = scoring_service.score_stocks(
            sample_stocks, single_indicator_config, calc_service
        )
        
        # ROE: 0.20 (max), 0.15, 0.10 (min)
        # 归一化后: 1.0, 0.5, 0.0
        scores = {r.stock_code.code: r.score for r in result}
        
        assert scores["600000.SH"] == pytest.approx(1.0, rel=1e-6)  # 最高 ROE
        assert scores["600001.SH"] == pytest.approx(0.5, rel=1e-6)  # 中间 ROE
        assert scores["600002.SH"] == pytest.approx(0.0, rel=1e-6)  # 最低 ROE
    
    def test_min_max_normalization_multi_indicator(
        self, scoring_service, calc_service, sample_stocks, multi_indicator_config
    ):
        """测试多指标 Min-Max 归一化"""
        result = scoring_service.score_stocks(
            sample_stocks, multi_indicator_config, calc_service
        )
        
        # 验证所有股票都有评分
        assert len(result) == 3
        for scored_stock in result:
            assert 0.0 <= scored_stock.score <= 1.0
            assert IndicatorField.ROE in scored_stock.score_breakdown
            assert IndicatorField.PE in scored_stock.score_breakdown
            assert IndicatorField.PB in scored_stock.score_breakdown
    
    def test_min_max_normalization_all_same_values(self, scoring_service, calc_service):
        """测试所有值相同时的 Min-Max 归一化"""
        stocks = [
            Stock(stock_code=StockCode("600000.SH"), stock_name="股票A", roe=0.15),
            Stock(stock_code=StockCode("600001.SH"), stock_name="股票B", roe=0.15),
            Stock(stock_code=StockCode("600002.SH"), stock_name="股票C", roe=0.15),
        ]
        config = ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
        
        result = scoring_service.score_stocks(stocks, config, calc_service)
        
        # 所有值相同时，归一化结果应为 0.5
        for scored_stock in result:
            assert scored_stock.score == pytest.approx(0.5, rel=1e-6)
    
    # ==================== Z-Score 归一化测试 ====================
    
    def test_z_score_normalization(self, scoring_service, calc_service, sample_stocks):
        """测试 Z-Score 归一化"""
        config = ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.Z_SCORE
        )
        
        result = scoring_service.score_stocks(sample_stocks, config, calc_service)
        
        # Z-Score 归一化后，均值应接近 0
        scores = [r.score for r in result]
        mean_score = sum(scores) / len(scores)
        assert mean_score == pytest.approx(0.0, abs=1e-6)
    
    # ==================== 无归一化测试 ====================
    
    def test_no_normalization(self, scoring_service, calc_service, sample_stocks):
        """测试无归一化"""
        config = ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.NONE
        )
        
        result = scoring_service.score_stocks(sample_stocks, config, calc_service)
        
        # 无归一化时，评分应等于原始值
        scores = {r.stock_code.code: r.score for r in result}
        assert scores["600000.SH"] == pytest.approx(0.20, rel=1e-6)
        assert scores["600001.SH"] == pytest.approx(0.15, rel=1e-6)
        assert scores["600002.SH"] == pytest.approx(0.10, rel=1e-6)
    
    # ==================== 缺失值处理测试 ====================
    
    def test_score_stocks_with_missing_values(self, scoring_service, calc_service):
        """测试包含缺失值的股票评分"""
        stocks = [
            Stock(stock_code=StockCode("600000.SH"), stock_name="股票A", roe=0.20, pe=10.0),
            Stock(stock_code=StockCode("600001.SH"), stock_name="股票B", roe=0.15, pe=None),  # PE 缺失
            Stock(stock_code=StockCode("600002.SH"), stock_name="股票C", roe=0.10, pe=20.0),
        ]
        config = ScoringConfig(
            weights={IndicatorField.ROE: 0.5, IndicatorField.PE: 0.5},
            normalization_method=NormalizationMethod.MIN_MAX
        )
        
        result = scoring_service.score_stocks(stocks, config, calc_service)
        
        # 所有股票都应有评分
        assert len(result) == 3
        
        # 缺失值的股票评分应按比例调整
        scores = {r.stock_code.code: r.score for r in result}
        # 股票B 只有 ROE 数据，其评分应基于 ROE 的归一化值
        assert scores["600001.SH"] is not None
    
    def test_score_stocks_all_missing_values(self, scoring_service, calc_service):
        """测试所有指标都缺失的股票"""
        stocks = [
            Stock(stock_code=StockCode("600000.SH"), stock_name="股票A"),  # 无任何指标
        ]
        config = ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
        
        result = scoring_service.score_stocks(stocks, config, calc_service)
        
        assert len(result) == 1
        # 所有值缺失时，评分为 0
        assert result[0].score == 0.0
    
    # ==================== 评分明细测试 ====================
    
    def test_score_breakdown_contains_all_indicators(
        self, scoring_service, calc_service, sample_stocks, multi_indicator_config
    ):
        """测试评分明细包含所有指标"""
        result = scoring_service.score_stocks(
            sample_stocks, multi_indicator_config, calc_service
        )
        
        for scored_stock in result:
            breakdown = scored_stock.score_breakdown
            assert IndicatorField.ROE in breakdown
            assert IndicatorField.PE in breakdown
            assert IndicatorField.PB in breakdown
    
    def test_score_breakdown_sum_equals_total_score(
        self, scoring_service, calc_service, sample_stocks, multi_indicator_config
    ):
        """测试评分明细之和等于总评分"""
        result = scoring_service.score_stocks(
            sample_stocks, multi_indicator_config, calc_service
        )
        
        for scored_stock in result:
            breakdown_sum = sum(scored_stock.score_breakdown.values())
            assert breakdown_sum == pytest.approx(scored_stock.score, rel=1e-6)
    
    # ==================== 指标值记录测试 ====================
    
    def test_indicator_values_recorded(
        self, scoring_service, calc_service, sample_stocks, single_indicator_config
    ):
        """测试指标值被正确记录"""
        result = scoring_service.score_stocks(
            sample_stocks, single_indicator_config, calc_service
        )
        
        for scored_stock in result:
            assert IndicatorField.ROE in scored_stock.indicator_values
    
    def test_indicator_values_match_original(
        self, scoring_service, calc_service, sample_stocks, single_indicator_config
    ):
        """测试记录的指标值与原始值匹配"""
        result = scoring_service.score_stocks(
            sample_stocks, single_indicator_config, calc_service
        )
        
        # 创建股票代码到原始 ROE 的映射
        original_roe = {
            "600000.SH": 0.20,
            "600001.SH": 0.15,
            "600002.SH": 0.10,
        }
        
        for scored_stock in result:
            code = scored_stock.stock_code.code
            recorded_roe = scored_stock.indicator_values.get(IndicatorField.ROE)
            assert recorded_roe == original_roe[code]


class TestScoringServiceEdgeCases:
    """边界情况测试"""
    
    @pytest.fixture
    def scoring_service(self):
        """创建评分服务实例"""
        return ScoringServiceImpl()
    
    @pytest.fixture
    def calc_service(self):
        """创建指标计算服务实例"""
        return IndicatorCalculationServiceImpl()
    
    def test_large_number_of_stocks(self, scoring_service, calc_service):
        """测试大量股票评分"""
        stocks = [
            Stock(
                stock_code=StockCode(f"60{i:04d}.SH"),
                stock_name=f"股票{i}",
                roe=0.05 + (i / 1000)  # ROE 从 0.05 到 0.15
            )
            for i in range(100)
        ]
        config = ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
        
        result = scoring_service.score_stocks(stocks, config, calc_service)
        
        assert len(result) == 100
        # 验证评分在 0-1 范围内
        for scored_stock in result:
            assert 0.0 <= scored_stock.score <= 1.0
    
    def test_negative_indicator_values(self, scoring_service, calc_service):
        """测试负指标值"""
        stocks = [
            Stock(stock_code=StockCode("600000.SH"), stock_name="股票A", roe=-0.10),
            Stock(stock_code=StockCode("600001.SH"), stock_name="股票B", roe=0.00),
            Stock(stock_code=StockCode("600002.SH"), stock_name="股票C", roe=0.10),
        ]
        config = ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
        
        result = scoring_service.score_stocks(stocks, config, calc_service)
        
        scores = {r.stock_code.code: r.score for r in result}
        # Min-Max 归一化应正确处理负值
        assert scores["600000.SH"] == pytest.approx(0.0, rel=1e-6)  # 最低
        assert scores["600001.SH"] == pytest.approx(0.5, rel=1e-6)  # 中间
        assert scores["600002.SH"] == pytest.approx(1.0, rel=1e-6)  # 最高
    
    def test_very_small_weight_differences(self, scoring_service, calc_service):
        """测试非常小的权重差异"""
        stocks = [
            Stock(stock_code=StockCode("600000.SH"), stock_name="股票A", roe=0.15, pe=10.0),
            Stock(stock_code=StockCode("600001.SH"), stock_name="股票B", roe=0.10, pe=15.0),
        ]
        config = ScoringConfig(
            weights={
                IndicatorField.ROE: 0.999999,
                IndicatorField.PE: 0.000001
            },
            normalization_method=NormalizationMethod.MIN_MAX
        )
        
        result = scoring_service.score_stocks(stocks, config, calc_service)
        
        # 应该正常计算，不会因为浮点精度问题出错
        assert len(result) == 2
    
    def test_extreme_indicator_values(self, scoring_service, calc_service):
        """测试极端指标值"""
        stocks = [
            Stock(stock_code=StockCode("600000.SH"), stock_name="股票A", roe=1e-10),
            Stock(stock_code=StockCode("600001.SH"), stock_name="股票B", roe=1e10),
        ]
        config = ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
        
        result = scoring_service.score_stocks(stocks, config, calc_service)
        
        scores = {r.stock_code.code: r.score for r in result}
        assert scores["600000.SH"] == pytest.approx(0.0, rel=1e-6)
        assert scores["600001.SH"] == pytest.approx(1.0, rel=1e-6)
    
    def test_mixed_valid_and_invalid_stocks(self, scoring_service, calc_service):
        """测试混合有效和无效数据的股票"""
        stocks = [
            Stock(stock_code=StockCode("600000.SH"), stock_name="股票A", roe=0.20),
            Stock(stock_code=StockCode("600001.SH"), stock_name="股票B"),  # 无 ROE
            Stock(stock_code=StockCode("600002.SH"), stock_name="股票C", roe=0.10),
        ]
        config = ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
        
        result = scoring_service.score_stocks(stocks, config, calc_service)
        
        assert len(result) == 3
        scores = {r.stock_code.code: r.score for r in result}
        
        # 有效数据的股票应正常评分
        assert scores["600000.SH"] == pytest.approx(1.0, rel=1e-6)
        assert scores["600002.SH"] == pytest.approx(0.0, rel=1e-6)
        # 无效数据的股票评分为 0
        assert scores["600001.SH"] == 0.0
