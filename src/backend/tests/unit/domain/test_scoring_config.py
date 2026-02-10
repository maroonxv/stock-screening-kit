"""
单元测试：ScoringConfig 值对象
"""
import pytest

from contexts.screening.domain.value_objects.scoring_config import ScoringConfig
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.enums import NormalizationMethod


class TestScoringConfig:
    """ScoringConfig 单元测试"""
    
    def test_valid_construction(self):
        """测试使用有效权重构造"""
        weights = {
            IndicatorField.ROE: 0.3,
            IndicatorField.PE: 0.2,
            IndicatorField.REVENUE_CAGR_3Y: 0.5
        }
        config = ScoringConfig(weights=weights)
        assert config.weights == weights
        assert config.normalization_method == NormalizationMethod.MIN_MAX
    
    def test_custom_normalization_method(self):
        """测试自定义归一化方法"""
        weights = {IndicatorField.ROE: 1.0}
        config = ScoringConfig(
            weights=weights, 
            normalization_method=NormalizationMethod.Z_SCORE
        )
        assert config.normalization_method == NormalizationMethod.Z_SCORE
    
    def test_weights_sum_not_one_raises_error(self):
        """测试权重之和不等于 1.0 抛出错误"""
        weights = {
            IndicatorField.ROE: 0.3,
            IndicatorField.PE: 0.3  # 总和 0.6，不等于 1.0
        }
        with pytest.raises(ValueError, match="权重之和必须等于 1.0"):
            ScoringConfig(weights=weights)
    
    def test_weights_sum_with_tolerance(self):
        """测试权重之和在容差范围内"""
        # 由于浮点数精度问题，0.1 + 0.2 + 0.7 可能不完全等于 1.0
        weights = {
            IndicatorField.ROE: 0.1,
            IndicatorField.PE: 0.2,
            IndicatorField.PB: 0.7
        }
        # 应该成功构造（在容差范围内）
        config = ScoringConfig(weights=weights)
        assert abs(sum(config.weights.values()) - 1.0) < ScoringConfig.TOLERANCE
    
    def test_negative_weight_raises_error(self):
        """测试负权重抛出错误"""
        weights = {
            IndicatorField.ROE: 1.5,
            IndicatorField.PE: -0.5  # 负权重
        }
        with pytest.raises(ValueError, match="权重不能为负数"):
            ScoringConfig(weights=weights)
    
    def test_empty_weights_raises_error(self):
        """测试空权重映射抛出错误"""
        with pytest.raises(ValueError, match="权重映射不能为空"):
            ScoringConfig(weights={})
    
    def test_get_weight(self):
        """测试 get_weight 方法"""
        weights = {
            IndicatorField.ROE: 0.6,
            IndicatorField.PE: 0.4
        }
        config = ScoringConfig(weights=weights)
        assert config.get_weight(IndicatorField.ROE) == 0.6
        assert config.get_weight(IndicatorField.PE) == 0.4
        assert config.get_weight(IndicatorField.PB) == 0.0  # 不存在的字段
    
    def test_to_dict(self):
        """测试序列化为字典"""
        weights = {
            IndicatorField.ROE: 0.5,
            IndicatorField.PE: 0.5
        }
        config = ScoringConfig(
            weights=weights,
            normalization_method=NormalizationMethod.Z_SCORE
        )
        data = config.to_dict()
        assert data['weights'] == {'ROE': 0.5, 'PE': 0.5}
        assert data['normalization_method'] == 'z_score'
    
    def test_from_dict(self):
        """测试从字典反序列化"""
        data = {
            'weights': {'ROE': 0.3, 'PE': 0.7},
            'normalization_method': 'min_max'
        }
        config = ScoringConfig.from_dict(data)
        assert config.get_weight(IndicatorField.ROE) == 0.3
        assert config.get_weight(IndicatorField.PE) == 0.7
        assert config.normalization_method == NormalizationMethod.MIN_MAX
    
    def test_serialization_round_trip(self):
        """测试序列化往返"""
        weights = {
            IndicatorField.ROE: 0.2,
            IndicatorField.PE: 0.3,
            IndicatorField.REVENUE_CAGR_3Y: 0.5
        }
        config1 = ScoringConfig(
            weights=weights,
            normalization_method=NormalizationMethod.NONE
        )
        data = config1.to_dict()
        config2 = ScoringConfig.from_dict(data)
        assert config1 == config2
    
    def test_equality(self):
        """测试相等性"""
        weights = {IndicatorField.ROE: 0.5, IndicatorField.PE: 0.5}
        config1 = ScoringConfig(weights=weights)
        config2 = ScoringConfig(weights=weights)
        assert config1 == config2
    
    def test_inequality_different_weights(self):
        """测试不同权重的不相等"""
        config1 = ScoringConfig(weights={IndicatorField.ROE: 1.0})
        config2 = ScoringConfig(weights={IndicatorField.PE: 1.0})
        assert config1 != config2
    
    def test_inequality_different_normalization(self):
        """测试不同归一化方法的不相等"""
        weights = {IndicatorField.ROE: 1.0}
        config1 = ScoringConfig(
            weights=weights,
            normalization_method=NormalizationMethod.MIN_MAX
        )
        config2 = ScoringConfig(
            weights=weights,
            normalization_method=NormalizationMethod.Z_SCORE
        )
        assert config1 != config2
    
    def test_hash_consistency(self):
        """测试哈希一致性"""
        weights = {IndicatorField.ROE: 0.5, IndicatorField.PE: 0.5}
        config1 = ScoringConfig(weights=weights)
        config2 = ScoringConfig(weights=weights)
        assert hash(config1) == hash(config2)
    
    def test_immutability(self):
        """测试不可变性"""
        weights = {IndicatorField.ROE: 0.5, IndicatorField.PE: 0.5}
        config = ScoringConfig(weights=weights)
        
        # 修改返回的权重字典不应影响原对象
        returned_weights = config.weights
        returned_weights[IndicatorField.PB] = 0.3
        
        # 原对象应该保持不变
        assert IndicatorField.PB not in config.weights
        assert len(config.weights) == 2
