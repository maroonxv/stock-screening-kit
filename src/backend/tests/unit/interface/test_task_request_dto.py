"""
任务请求 DTO 单元测试

测试 IndustryResearchRequest 和 CredibilityVerificationRequest 的请求验证功能。

Requirements:
- 8.8: 实现 DTO 类用于请求验证和响应格式化
- 8.9: API 请求包含无效数据时返回 HTTP 400 和描述性错误信息
"""
import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from contexts.intelligence.interface.dto.task_request_dto import (
    IndustryResearchRequest,
    CredibilityVerificationRequest,
)


class TestIndustryResearchRequest:
    """IndustryResearchRequest 测试"""
    
    # === from_dict 测试 ===
    
    def test_from_dict_valid_data(self):
        """测试有效数据解析"""
        data = {'query': '快速了解合成生物学赛道'}
        
        request = IndustryResearchRequest.from_dict(data)
        
        assert request.query == '快速了解合成生物学赛道'
    
    def test_from_dict_strips_whitespace(self):
        """测试 query 会被去除首尾空格"""
        data = {'query': '  合成生物学  '}
        
        request = IndustryResearchRequest.from_dict(data)
        
        assert request.query == '合成生物学'
    
    def test_from_dict_none_data_raises_error(self):
        """测试 None 数据抛出异常"""
        with pytest.raises(ValueError, match="请求数据不能为空"):
            IndustryResearchRequest.from_dict(None)
    
    def test_from_dict_non_dict_data_raises_error(self):
        """测试非字典数据抛出异常"""
        with pytest.raises(ValueError, match="请求数据必须是 JSON 对象"):
            IndustryResearchRequest.from_dict("invalid")
        
        with pytest.raises(ValueError, match="请求数据必须是 JSON 对象"):
            IndustryResearchRequest.from_dict(['query'])
    
    def test_from_dict_missing_query_returns_empty(self):
        """测试缺少 query 字段返回空字符串"""
        data = {}
        
        request = IndustryResearchRequest.from_dict(data)
        
        assert request.query == ''
    
    def test_from_dict_non_string_query_converts(self):
        """测试非字符串 query 会被转换"""
        data = {'query': 123}
        
        request = IndustryResearchRequest.from_dict(data)
        
        assert request.query == '123'
    
    def test_from_dict_none_query_returns_empty(self):
        """测试 None query 返回空字符串"""
        data = {'query': None}
        
        request = IndustryResearchRequest.from_dict(data)
        
        assert request.query == ''
    
    # === validate 测试 ===
    
    def test_validate_valid_query(self):
        """测试有效 query 验证通过"""
        request = IndustryResearchRequest(query='合成生物学')
        
        # 不应抛出异常
        request.validate()
    
    def test_validate_empty_query_raises_error(self):
        """测试空 query 验证失败"""
        request = IndustryResearchRequest(query='')
        
        with pytest.raises(ValueError, match="查询文本不能为空"):
            request.validate()
    
    def test_validate_whitespace_only_query_raises_error(self):
        """测试仅空白字符的 query 验证失败"""
        # __post_init__ 会 strip，所以空白字符会变成空字符串
        request = IndustryResearchRequest(query='   ')
        
        with pytest.raises(ValueError, match="查询文本不能为空"):
            request.validate()
    
    # === 集成测试：from_dict + validate ===
    
    def test_from_dict_and_validate_valid_data(self):
        """测试有效数据的完整流程"""
        data = {'query': '快速了解新能源汽车行业'}
        
        request = IndustryResearchRequest.from_dict(data)
        request.validate()  # 不应抛出异常
        
        assert request.query == '快速了解新能源汽车行业'
    
    def test_from_dict_and_validate_empty_query(self):
        """测试空 query 的完整流程"""
        data = {'query': ''}
        
        request = IndustryResearchRequest.from_dict(data)
        
        with pytest.raises(ValueError, match="查询文本不能为空"):
            request.validate()


class TestCredibilityVerificationRequest:
    """CredibilityVerificationRequest 测试"""
    
    # === from_dict 测试 ===
    
    def test_from_dict_valid_data_sh(self):
        """测试有效沪市数据解析"""
        data = {'stock_code': '600519.SH', 'concept': 'AI+白酒'}
        
        request = CredibilityVerificationRequest.from_dict(data)
        
        assert request.stock_code == '600519.SH'
        assert request.concept == 'AI+白酒'
    
    def test_from_dict_valid_data_sz(self):
        """测试有效深市数据解析"""
        data = {'stock_code': '000001.SZ', 'concept': '数字货币'}
        
        request = CredibilityVerificationRequest.from_dict(data)
        
        assert request.stock_code == '000001.SZ'
        assert request.concept == '数字货币'
    
    def test_from_dict_strips_whitespace(self):
        """测试字段会被去除首尾空格"""
        data = {'stock_code': '  600519.SH  ', 'concept': '  AI+白酒  '}
        
        request = CredibilityVerificationRequest.from_dict(data)
        
        assert request.stock_code == '600519.SH'
        assert request.concept == 'AI+白酒'
    
    def test_from_dict_none_data_raises_error(self):
        """测试 None 数据抛出异常"""
        with pytest.raises(ValueError, match="请求数据不能为空"):
            CredibilityVerificationRequest.from_dict(None)
    
    def test_from_dict_non_dict_data_raises_error(self):
        """测试非字典数据抛出异常"""
        with pytest.raises(ValueError, match="请求数据必须是 JSON 对象"):
            CredibilityVerificationRequest.from_dict("invalid")
        
        with pytest.raises(ValueError, match="请求数据必须是 JSON 对象"):
            CredibilityVerificationRequest.from_dict(['stock_code', 'concept'])
    
    def test_from_dict_missing_fields_returns_empty(self):
        """测试缺少字段返回空字符串"""
        data = {}
        
        request = CredibilityVerificationRequest.from_dict(data)
        
        assert request.stock_code == ''
        assert request.concept == ''
    
    def test_from_dict_non_string_fields_converts(self):
        """测试非字符串字段会被转换"""
        data = {'stock_code': 600519, 'concept': 123}
        
        request = CredibilityVerificationRequest.from_dict(data)
        
        assert request.stock_code == '600519'
        assert request.concept == '123'
    
    def test_from_dict_none_fields_returns_empty(self):
        """测试 None 字段返回空字符串"""
        data = {'stock_code': None, 'concept': None}
        
        request = CredibilityVerificationRequest.from_dict(data)
        
        assert request.stock_code == ''
        assert request.concept == ''
    
    # === validate 测试 ===
    
    def test_validate_valid_sh_stock_code(self):
        """测试有效沪市股票代码验证通过"""
        # 沪市主板
        request = CredibilityVerificationRequest(stock_code='600519.SH', concept='白酒')
        request.validate()
        
        # 沪市科创板
        request = CredibilityVerificationRequest(stock_code='688001.SH', concept='芯片')
        request.validate()
    
    def test_validate_valid_sz_stock_code(self):
        """测试有效深市股票代码验证通过"""
        # 深市主板
        request = CredibilityVerificationRequest(stock_code='000001.SZ', concept='银行')
        request.validate()
        
        # 深市创业板
        request = CredibilityVerificationRequest(stock_code='300001.SZ', concept='新能源')
        request.validate()
        
        # 深市中小板
        request = CredibilityVerificationRequest(stock_code='002001.SZ', concept='制造')
        request.validate()
    
    def test_validate_empty_stock_code_raises_error(self):
        """测试空股票代码验证失败"""
        request = CredibilityVerificationRequest(stock_code='', concept='AI')
        
        with pytest.raises(ValueError, match="股票代码不能为空"):
            request.validate()
    
    def test_validate_invalid_stock_code_format_raises_error(self):
        """测试无效股票代码格式验证失败"""
        # 缺少交易所后缀
        request = CredibilityVerificationRequest(stock_code='600519', concept='AI')
        with pytest.raises(ValueError, match="无效的股票代码格式"):
            request.validate()
        
        # 错误的交易所后缀
        request = CredibilityVerificationRequest(stock_code='600519.HK', concept='AI')
        with pytest.raises(ValueError, match="无效的股票代码格式"):
            request.validate()
        
        # 位数不对
        request = CredibilityVerificationRequest(stock_code='60051.SH', concept='AI')
        with pytest.raises(ValueError, match="无效的股票代码格式"):
            request.validate()
        
        # 包含字母
        request = CredibilityVerificationRequest(stock_code='60051A.SH', concept='AI')
        with pytest.raises(ValueError, match="无效的股票代码格式"):
            request.validate()
        
        # 小写后缀
        request = CredibilityVerificationRequest(stock_code='600519.sh', concept='AI')
        with pytest.raises(ValueError, match="无效的股票代码格式"):
            request.validate()
    
    def test_validate_empty_concept_raises_error(self):
        """测试空概念验证失败"""
        request = CredibilityVerificationRequest(stock_code='600519.SH', concept='')
        
        with pytest.raises(ValueError, match="概念不能为空"):
            request.validate()
    
    def test_validate_whitespace_only_concept_raises_error(self):
        """测试仅空白字符的概念验证失败"""
        # __post_init__ 会 strip，所以空白字符会变成空字符串
        request = CredibilityVerificationRequest(stock_code='600519.SH', concept='   ')
        
        with pytest.raises(ValueError, match="概念不能为空"):
            request.validate()
    
    # === 集成测试：from_dict + validate ===
    
    def test_from_dict_and_validate_valid_data(self):
        """测试有效数据的完整流程"""
        data = {'stock_code': '600519.SH', 'concept': 'AI+白酒'}
        
        request = CredibilityVerificationRequest.from_dict(data)
        request.validate()  # 不应抛出异常
        
        assert request.stock_code == '600519.SH'
        assert request.concept == 'AI+白酒'
    
    def test_from_dict_and_validate_invalid_stock_code(self):
        """测试无效股票代码的完整流程"""
        data = {'stock_code': 'INVALID', 'concept': 'AI'}
        
        request = CredibilityVerificationRequest.from_dict(data)
        
        with pytest.raises(ValueError, match="无效的股票代码格式"):
            request.validate()
    
    def test_from_dict_and_validate_empty_concept(self):
        """测试空概念的完整流程"""
        data = {'stock_code': '600519.SH', 'concept': ''}
        
        request = CredibilityVerificationRequest.from_dict(data)
        
        with pytest.raises(ValueError, match="概念不能为空"):
            request.validate()
    
    # === 边界情况测试 ===
    
    def test_validate_all_valid_stock_code_prefixes(self):
        """测试所有有效的股票代码前缀"""
        valid_codes = [
            '600000.SH',  # 沪市主板 600xxx
            '601000.SH',  # 沪市主板 601xxx
            '603000.SH',  # 沪市主板 603xxx
            '688000.SH',  # 沪市科创板 688xxx
            '000000.SZ',  # 深市主板 000xxx
            '001000.SZ',  # 深市主板 001xxx
            '002000.SZ',  # 深市中小板 002xxx
            '300000.SZ',  # 深市创业板 300xxx
        ]
        
        for code in valid_codes:
            request = CredibilityVerificationRequest(stock_code=code, concept='测试概念')
            request.validate()  # 不应抛出异常
    
    def test_validate_error_message_includes_stock_code(self):
        """测试错误信息包含股票代码"""
        request = CredibilityVerificationRequest(stock_code='INVALID', concept='AI')
        
        with pytest.raises(ValueError) as exc_info:
            request.validate()
        
        assert 'INVALID' in str(exc_info.value)
        assert '600519.SH' in str(exc_info.value) or '000001.SZ' in str(exc_info.value)
