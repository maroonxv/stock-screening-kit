"""
AKShareMarketDataRepository 单元测试

使用 Mock 模拟 AKShare 接口，测试仓储的逻辑正确性。
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime

from shared_kernel.infrastructure.akshare_market_data_repository import (
    AKShareMarketDataRepository
)
from shared_kernel.value_objects.stock_code import StockCode


class TestAKShareMarketDataRepository:
    """AKShareMarketDataRepository 单元测试"""
    
    @pytest.fixture
    def mock_stock_list_df(self):
        """模拟股票列表数据"""
        return pd.DataFrame({
            'code': ['600000', '000001', '300001', '830001'],
            'name': ['浦发银行', '平安银行', '特锐德', '北京股票']
        })
    
    @pytest.fixture
    def mock_financial_df(self):
        """模拟财务指标数据"""
        return pd.DataFrame({
            '日期': ['2024-12-31'],
            '净资产收益率(%)': [15.5],
            '摊薄每股收益(元)': [1.25],
            '资产负债率(%)': [45.0],
            '主营业务收入增长率(%)': [12.5],
            '净利润增长率(%)': [8.3],
            '流动比率': [1.5],
            '速动比率': [1.2],
            '销售毛利率(%)': [30.0],
            '销售净利率(%)': [10.0],
        })
    
    @pytest.fixture
    def mock_profile_df(self):
        """模拟公司概况数据"""
        return pd.DataFrame({
            '所属行业': ['银行']
        })
    
    # ==================== 股票代码转换测试 ====================
    
    def test_convert_sh_stock_code(self):
        """测试上海股票代码转换"""
        repo = AKShareMarketDataRepository()
        result = repo._convert_to_stock_code('600000')
        
        assert result is not None
        assert result.code == '600000.SH'
    
    def test_convert_sz_stock_code_0(self):
        """测试深圳主板股票代码转换（0开头）"""
        repo = AKShareMarketDataRepository()
        result = repo._convert_to_stock_code('000001')
        
        assert result is not None
        assert result.code == '000001.SZ'
    
    def test_convert_sz_stock_code_3(self):
        """测试深圳创业板股票代码转换（3开头）"""
        repo = AKShareMarketDataRepository()
        result = repo._convert_to_stock_code('300001')
        
        assert result is not None
        assert result.code == '300001.SZ'
    
    def test_convert_bj_stock_code_8(self):
        """测试北京股票代码转换（8开头）"""
        repo = AKShareMarketDataRepository()
        result = repo._convert_to_stock_code('830001')
        
        assert result is not None
        assert result.code == '830001.BJ'
    
    def test_convert_bj_stock_code_4(self):
        """测试北京股票代码转换（4开头）"""
        repo = AKShareMarketDataRepository()
        result = repo._convert_to_stock_code('430001')
        
        assert result is not None
        assert result.code == '430001.BJ'
    
    def test_convert_invalid_stock_code(self):
        """测试无效股票代码转换"""
        repo = AKShareMarketDataRepository()
        result = repo._convert_to_stock_code('999999')
        
        assert result is None
    
    def test_get_pure_code(self):
        """测试从 StockCode 提取纯数字代码"""
        repo = AKShareMarketDataRepository()
        stock_code = StockCode('600000.SH')
        
        result = repo._get_pure_code(stock_code)
        
        assert result == '600000'
    
    # ==================== 获取股票列表测试 ====================
    
    @patch('shared_kernel.infrastructure.akshare_market_data_repository.ak')
    def test_get_all_stock_codes(self, mock_ak, mock_stock_list_df):
        """测试获取所有股票代码"""
        mock_ak.stock_info_a_code_name.return_value = mock_stock_list_df
        
        repo = AKShareMarketDataRepository()
        codes = repo.get_all_stock_codes()
        
        assert len(codes) == 4
        assert any(c.code == '600000.SH' for c in codes)
        assert any(c.code == '000001.SZ' for c in codes)
        assert any(c.code == '300001.SZ' for c in codes)
        assert any(c.code == '830001.BJ' for c in codes)
    
    @patch('shared_kernel.infrastructure.akshare_market_data_repository.ak')
    def test_get_all_stock_codes_caches_result(self, mock_ak, mock_stock_list_df):
        """测试股票列表缓存"""
        mock_ak.stock_info_a_code_name.return_value = mock_stock_list_df
        
        repo = AKShareMarketDataRepository()
        
        # 第一次调用
        repo.get_all_stock_codes()
        # 第二次调用
        repo.get_all_stock_codes()
        
        # 应该只调用一次 API
        assert mock_ak.stock_info_a_code_name.call_count == 1
    
    @patch('shared_kernel.infrastructure.akshare_market_data_repository.ak')
    def test_get_all_stock_codes_handles_error(self, mock_ak):
        """测试获取股票列表失败时返回空列表"""
        mock_ak.stock_info_a_code_name.side_effect = Exception("API Error")
        
        repo = AKShareMarketDataRepository()
        codes = repo.get_all_stock_codes()
        
        assert codes == []
    
    # ==================== 获取单只股票测试 ====================
    
    @patch('shared_kernel.infrastructure.akshare_market_data_repository.ak')
    def test_get_stock(self, mock_ak, mock_stock_list_df, mock_financial_df, mock_profile_df):
        """测试获取单只股票数据"""
        mock_ak.stock_info_a_code_name.return_value = mock_stock_list_df
        mock_ak.stock_financial_analysis_indicator.return_value = mock_financial_df
        mock_ak.stock_profile_cninfo.return_value = mock_profile_df
        
        repo = AKShareMarketDataRepository()
        stock_code = StockCode('600000.SH')
        
        stock = repo.get_stock(stock_code)
        
        assert stock is not None
        assert stock.stock_code == stock_code
        assert stock.stock_name == '浦发银行'
        assert stock.roe == 15.5
        assert stock.eps == 1.25
        assert stock.debt_ratio == 45.0
        assert stock.industry == '银行'
    
    @patch('shared_kernel.infrastructure.akshare_market_data_repository.ak')
    def test_get_stock_caches_result(self, mock_ak, mock_stock_list_df, mock_financial_df, mock_profile_df):
        """测试股票数据缓存"""
        mock_ak.stock_info_a_code_name.return_value = mock_stock_list_df
        mock_ak.stock_financial_analysis_indicator.return_value = mock_financial_df
        mock_ak.stock_profile_cninfo.return_value = mock_profile_df
        
        repo = AKShareMarketDataRepository()
        stock_code = StockCode('600000.SH')
        
        # 第一次调用
        repo.get_stock(stock_code)
        # 第二次调用
        repo.get_stock(stock_code)
        
        # 财务指标 API 应该只调用一次
        assert mock_ak.stock_financial_analysis_indicator.call_count == 1
    
    # ==================== 批量获取股票测试 ====================
    
    @patch('shared_kernel.infrastructure.akshare_market_data_repository.ak')
    def test_get_stocks_by_codes(self, mock_ak, mock_stock_list_df, mock_financial_df, mock_profile_df):
        """测试批量获取股票数据"""
        mock_ak.stock_info_a_code_name.return_value = mock_stock_list_df
        mock_ak.stock_financial_analysis_indicator.return_value = mock_financial_df
        mock_ak.stock_profile_cninfo.return_value = mock_profile_df
        
        repo = AKShareMarketDataRepository()
        codes = [StockCode('600000.SH'), StockCode('000001.SZ')]
        
        stocks = repo.get_stocks_by_codes(codes)
        
        assert len(stocks) == 2
    
    @patch('shared_kernel.infrastructure.akshare_market_data_repository.ak')
    def test_get_stocks_by_codes_uses_cache(self, mock_ak, mock_stock_list_df, mock_financial_df, mock_profile_df):
        """测试批量获取时使用缓存"""
        mock_ak.stock_info_a_code_name.return_value = mock_stock_list_df
        mock_ak.stock_financial_analysis_indicator.return_value = mock_financial_df
        mock_ak.stock_profile_cninfo.return_value = mock_profile_df
        
        repo = AKShareMarketDataRepository()
        code1 = StockCode('600000.SH')
        code2 = StockCode('000001.SZ')
        
        # 先获取一只股票
        repo.get_stock(code1)
        
        # 再批量获取两只
        stocks = repo.get_stocks_by_codes([code1, code2])
        
        assert len(stocks) == 2
        # 第一只股票应该从缓存获取，只有第二只需要调用 API
        # 所以财务指标 API 应该调用 2 次（第一次单独获取 + 第二次批量获取中的新股票）
        assert mock_ak.stock_financial_analysis_indicator.call_count == 2
    
    # ==================== 辅助方法测试 ====================
    
    def test_safe_float_with_valid_value(self):
        """测试有效值转换"""
        repo = AKShareMarketDataRepository()
        
        assert repo._safe_float(10.5) == 10.5
        assert repo._safe_float('10.5') == 10.5
        assert repo._safe_float(10) == 10.0
    
    def test_safe_float_with_none(self):
        """测试 None 值转换"""
        repo = AKShareMarketDataRepository()
        
        assert repo._safe_float(None) is None
    
    def test_safe_float_with_nan(self):
        """测试 NaN 值转换"""
        repo = AKShareMarketDataRepository()
        
        assert repo._safe_float(float('nan')) is None
    
    def test_safe_float_with_invalid_string(self):
        """测试无效字符串转换"""
        repo = AKShareMarketDataRepository()
        
        assert repo._safe_float('invalid') is None
        assert repo._safe_float('--') is None
    
    # ==================== 行业信息测试 ====================
    
    @patch('shared_kernel.infrastructure.akshare_market_data_repository.ak')
    def test_get_available_industries(self, mock_ak, mock_stock_list_df, mock_financial_df, mock_profile_df):
        """测试获取可用行业列表"""
        mock_ak.stock_info_a_code_name.return_value = mock_stock_list_df
        mock_ak.stock_financial_analysis_indicator.return_value = mock_financial_df
        mock_ak.stock_profile_cninfo.return_value = mock_profile_df
        
        repo = AKShareMarketDataRepository()
        
        # 先获取一只股票以填充行业缓存
        repo.get_stock(StockCode('600000.SH'))
        
        industries = repo.get_available_industries()
        
        assert '银行' in industries
    
    def test_get_available_industries_empty_cache(self):
        """测试空缓存时返回空列表"""
        repo = AKShareMarketDataRepository()
        
        industries = repo.get_available_industries()
        
        assert industries == []
    
    # ==================== 更新时间测试 ====================
    
    def test_get_last_update_time_initial(self):
        """测试初始更新时间"""
        repo = AKShareMarketDataRepository()
        
        update_time = repo.get_last_update_time()
        
        # 应该返回当前时间附近的值
        assert isinstance(update_time, datetime)
        assert (datetime.now() - update_time).total_seconds() < 1
    
    @patch('shared_kernel.infrastructure.akshare_market_data_repository.ak')
    def test_get_last_update_time_after_fetch(self, mock_ak, mock_stock_list_df, mock_financial_df, mock_profile_df):
        """测试获取数据后的更新时间"""
        mock_ak.stock_info_a_code_name.return_value = mock_stock_list_df
        mock_ak.stock_financial_analysis_indicator.return_value = mock_financial_df
        mock_ak.stock_profile_cninfo.return_value = mock_profile_df
        
        repo = AKShareMarketDataRepository()
        
        # 获取数据
        repo.get_stocks_by_codes([StockCode('600000.SH')])
        
        update_time = repo.get_last_update_time()
        
        assert isinstance(update_time, datetime)
        assert (datetime.now() - update_time).total_seconds() < 1
