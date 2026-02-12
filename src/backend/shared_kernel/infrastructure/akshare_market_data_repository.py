"""
AKShare 市场数据仓储实现

基于 AKShare 库实现 IMarketDataRepository 接口，
提供 A 股股票数据的获取功能。
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import akshare as ak
import pandas as pd

from shared_kernel.interfaces.market_data_repository import IMarketDataRepository
from shared_kernel.value_objects.stock_code import StockCode
from contexts.screening.domain.models.stock import Stock

logger = logging.getLogger(__name__)


class AKShareMarketDataRepository(IMarketDataRepository[Stock]):
    """
    基于 AKShare 的市场数据仓储实现
    
    使用 AKShare 库获取 A 股股票数据，包括：
    - 股票列表
    - 财务指标（ROE、EPS、资产负债率等）
    - 公司概况（行业分类）
    
    注意：
    - AKShare 接口有频率限制，批量获取时需要控制并发
    - 数据缓存在内存中，避免重复请求
    """
    
    def __init__(self, max_workers: int = 5, cache_ttl_minutes: int = 60):
        """
        初始化仓储
        
        Args:
            max_workers: 并发获取数据的最大线程数
            cache_ttl_minutes: 缓存有效期（分钟）
        """
        self._max_workers = max_workers
        self._cache_ttl_minutes = cache_ttl_minutes
        self._stock_list_cache: Optional[pd.DataFrame] = None
        self._stock_data_cache: Dict[str, Stock] = {}
        self._last_update_time: Optional[datetime] = None
        self._industry_cache: Dict[str, str] = {}
    
    def get_all_stock_codes(self) -> List[StockCode]:
        """获取所有 A 股股票代码"""
        df = self._get_stock_list()
        codes = []
        for _, row in df.iterrows():
            code = row['code']
            # 转换为带后缀的格式
            stock_code = self._convert_to_stock_code(code)
            if stock_code:
                codes.append(stock_code)
        return codes
    
    def get_stock(self, stock_code: StockCode) -> Optional[Stock]:
        """根据股票代码获取单只股票"""
        # 检查缓存
        cache_key = stock_code.code
        if cache_key in self._stock_data_cache:
            return self._stock_data_cache[cache_key]
        
        # 获取数据
        stock = self._fetch_stock_data(stock_code)
        if stock:
            self._stock_data_cache[cache_key] = stock
        return stock
    
    def get_stocks_by_codes(self, stock_codes: List[StockCode]) -> List[Stock]:
        """批量获取股票数据"""
        stocks = []
        codes_to_fetch = []
        
        # 先检查缓存
        for code in stock_codes:
            cache_key = code.code
            if cache_key in self._stock_data_cache:
                stocks.append(self._stock_data_cache[cache_key])
            else:
                codes_to_fetch.append(code)
        
        # 并发获取未缓存的数据
        if codes_to_fetch:
            logger.info(f"开始获取 {len(codes_to_fetch)} 只股票数据...")
            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                future_to_code = {
                    executor.submit(self._fetch_stock_data, code): code 
                    for code in codes_to_fetch
                }
                for future in as_completed(future_to_code):
                    code = future_to_code[future]
                    try:
                        stock = future.result()
                        if stock:
                            self._stock_data_cache[code.code] = stock
                            stocks.append(stock)
                    except Exception as e:
                        logger.warning(f"获取股票 {code.code} 数据失败: {e}")
        
        self._last_update_time = datetime.now()
        return stocks
    
    def get_last_update_time(self) -> datetime:
        """获取数据最后更新时间"""
        return self._last_update_time or datetime.now()
    
    def get_available_industries(self) -> List[str]:
        """获取所有可用的行业分类"""
        # 如果缓存为空，返回空列表
        if not self._industry_cache:
            return []
        return list(set(self._industry_cache.values()))
    
    # ==================== 私有方法 ====================
    
    def _get_stock_list(self) -> pd.DataFrame:
        """获取股票列表（带缓存）"""
        if self._stock_list_cache is not None:
            return self._stock_list_cache
        
        try:
            logger.info("正在获取 A 股股票列表...")
            df = ak.stock_info_a_code_name()
            self._stock_list_cache = df
            logger.info(f"获取到 {len(df)} 只股票")
            return df
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame(columns=['code', 'name'])
    
    def _convert_to_stock_code(self, code: str) -> Optional[StockCode]:
        """
        将纯数字代码转换为带后缀的 StockCode
        
        规则：
        - 6 开头 -> 上海 (.SH)
        - 0/3 开头 -> 深圳 (.SZ)
        - 8/4 开头 -> 北京 (.BJ)
        """
        code = str(code).zfill(6)
        try:
            if code.startswith('6'):
                return StockCode(f"{code}.SH")
            elif code.startswith(('0', '3')):
                return StockCode(f"{code}.SZ")
            elif code.startswith(('8', '4')):
                return StockCode(f"{code}.BJ")
            else:
                return None
        except Exception:
            return None
    
    def _get_pure_code(self, stock_code: StockCode) -> str:
        """从 StockCode 提取纯数字代码"""
        return stock_code.code.split('.')[0]
    
    def _fetch_stock_data(self, stock_code: StockCode) -> Optional[Stock]:
        """获取单只股票的完整数据"""
        pure_code = self._get_pure_code(stock_code)
        stock_list = self._get_stock_list()
        
        # 获取股票名称
        name_row = stock_list[stock_list['code'] == pure_code]
        if name_row.empty:
            name_row = stock_list[stock_list['code'] == int(pure_code)]
        
        stock_name = name_row['name'].iloc[0] if not name_row.empty else f"未知({pure_code})"
        
        # 获取财务指标
        financial_data = self._fetch_financial_indicators(pure_code)
        
        # 获取行业信息
        industry = self._fetch_industry(pure_code)
        
        return Stock(
            stock_code=stock_code,
            stock_name=stock_name,
            roe=financial_data.get('roe'),
            pe=financial_data.get('pe'),
            pb=financial_data.get('pb'),
            eps=financial_data.get('eps'),
            revenue=financial_data.get('revenue'),
            net_profit=financial_data.get('net_profit'),
            debt_ratio=financial_data.get('debt_ratio'),
            market_cap=financial_data.get('market_cap'),
            industry=industry,
            dividend_yield=financial_data.get('dividend_yield'),
            revenue_growth=financial_data.get('revenue_growth'),
            profit_growth=financial_data.get('profit_growth'),
        )
    
    def _fetch_financial_indicators(self, pure_code: str) -> Dict[str, Optional[float]]:
        """
        获取财务指标
        
        使用 stock_financial_analysis_indicator 接口获取：
        - ROE (净资产收益率)
        - EPS (每股收益)
        - 资产负债率
        - 流动比率
        - 速动比率
        - 营收增长率
        - 净利润增长率
        
        使用 stock_a_indicator_lg 接口获取市场估值指标：
        - PE (市盈率 TTM)
        - PB (市净率)
        - 总市值
        - 股息率
        """
        result: Dict[str, Optional[float]] = {}
        
        try:
            # 获取最近的财务数据
            current_year = datetime.now().year
            df = ak.stock_financial_analysis_indicator(
                symbol=pure_code, 
                start_year=str(current_year - 1)
            )
            
            if not df.empty:
                # 取最新一期数据
                latest = df.iloc[-1]
                
                # 映射字段
                result['roe'] = self._safe_float(latest.get('净资产收益率(%)'))
                result['eps'] = self._safe_float(latest.get('摊薄每股收益(元)'))
                result['debt_ratio'] = self._safe_float(latest.get('资产负债率(%)'))
                result['revenue_growth'] = self._safe_float(latest.get('主营业务收入增长率(%)'))
                result['profit_growth'] = self._safe_float(latest.get('净利润增长率(%)'))
                
                # 流动比率和速动比率
                result['current_ratio'] = self._safe_float(latest.get('流动比率'))
                result['quick_ratio'] = self._safe_float(latest.get('速动比率'))
                
                # 毛利率和净利率
                result['gross_margin'] = self._safe_float(latest.get('销售毛利率(%)'))
                result['net_margin'] = self._safe_float(latest.get('销售净利率(%)'))
            
        except Exception as e:
            logger.debug(f"获取股票 {pure_code} 财务指标失败: {e}")
        
        # 获取市场估值指标（PE、PB、总市值、股息率）
        try:
            indicator_df = ak.stock_a_indicator_lg(symbol=pure_code)
            if indicator_df is not None and not indicator_df.empty:
                # 取最新一行数据
                latest_indicator = indicator_df.iloc[-1]
                result['pe'] = self._safe_float(latest_indicator.get('pe_ttm'))
                result['pb'] = self._safe_float(latest_indicator.get('pb'))
                result['market_cap'] = self._safe_float(latest_indicator.get('total_mv'))
                result['dividend_yield'] = self._safe_float(latest_indicator.get('dv_ratio'))
        except Exception as e:
            logger.debug(f"获取股票 {pure_code} 市场估值指标失败: {e}")
        
        return result
    
    def _fetch_industry(self, pure_code: str) -> Optional[str]:
        """获取行业分类"""
        # 检查缓存
        if pure_code in self._industry_cache:
            return self._industry_cache[pure_code]
        
        try:
            df = ak.stock_profile_cninfo(symbol=pure_code)
            if not df.empty:
                industry = df['所属行业'].iloc[0] if '所属行业' in df.columns else None
                if industry:
                    self._industry_cache[pure_code] = industry
                    return industry
        except Exception as e:
            logger.debug(f"获取股票 {pure_code} 行业信息失败: {e}")
        
        return None
    
    def _safe_float(self, value) -> Optional[float]:
        """安全转换为浮点数"""
        if value is None or pd.isna(value):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
