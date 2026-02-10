"""
Stock 实体实现

Stock 是一个实体，包含股票的基本信息和财务指标属性。
用于筛选策略执行时的数据载体。

Requirements:
- 2.5: Stock 实体，包含财务指标属性（roe、pe、pb、eps、revenue、net_profit、debt_ratio、market_cap 等）
"""
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from shared_kernel.value_objects.stock_code import StockCode


class Stock:
    """
    股票实体
    
    包含股票的基本信息和财务指标属性。
    
    属性:
    - stock_code: 股票代码（StockCode 值对象）
    - stock_name: 股票名称
    
    财务指标属性（均为 Optional，可能缺失数据）:
    - roe: 净资产收益率 (Return on Equity)
    - pe: 市盈率 (Price-to-Earnings Ratio)
    - pb: 市净率 (Price-to-Book Ratio)
    - eps: 每股收益 (Earnings Per Share)
    - revenue: 营业收入
    - net_profit: 净利润
    - debt_ratio: 资产负债率
    - market_cap: 市值
    - industry: 行业
    - dividend_yield: 股息率
    - revenue_growth: 营收增长率
    - profit_growth: 净利润增长率
    """
    
    def __init__(
        self,
        stock_code: 'StockCode',
        stock_name: str,
        roe: Optional[float] = None,
        pe: Optional[float] = None,
        pb: Optional[float] = None,
        eps: Optional[float] = None,
        revenue: Optional[float] = None,
        net_profit: Optional[float] = None,
        debt_ratio: Optional[float] = None,
        market_cap: Optional[float] = None,
        industry: Optional[str] = None,
        dividend_yield: Optional[float] = None,
        revenue_growth: Optional[float] = None,
        profit_growth: Optional[float] = None
    ):
        """
        构造股票实体
        
        Args:
            stock_code: 股票代码（StockCode 值对象）
            stock_name: 股票名称
            roe: 净资产收益率（可选）
            pe: 市盈率（可选）
            pb: 市净率（可选）
            eps: 每股收益（可选）
            revenue: 营业收入（可选）
            net_profit: 净利润（可选）
            debt_ratio: 资产负债率（可选）
            market_cap: 市值（可选）
            industry: 行业（可选）
            dividend_yield: 股息率（可选）
            revenue_growth: 营收增长率（可选）
            profit_growth: 净利润增长率（可选）
        """
        self._stock_code = stock_code
        self._stock_name = stock_name
        self._roe = roe
        self._pe = pe
        self._pb = pb
        self._eps = eps
        self._revenue = revenue
        self._net_profit = net_profit
        self._debt_ratio = debt_ratio
        self._market_cap = market_cap
        self._industry = industry
        self._dividend_yield = dividend_yield
        self._revenue_growth = revenue_growth
        self._profit_growth = profit_growth
    
    # ==================== 属性访问器 ====================
    
    @property
    def stock_code(self) -> 'StockCode':
        """获取股票代码"""
        return self._stock_code
    
    @property
    def stock_name(self) -> str:
        """获取股票名称"""
        return self._stock_name
    
    @property
    def roe(self) -> Optional[float]:
        """获取净资产收益率"""
        return self._roe
    
    @property
    def pe(self) -> Optional[float]:
        """获取市盈率"""
        return self._pe
    
    @property
    def pb(self) -> Optional[float]:
        """获取市净率"""
        return self._pb
    
    @property
    def eps(self) -> Optional[float]:
        """获取每股收益"""
        return self._eps
    
    @property
    def revenue(self) -> Optional[float]:
        """获取营业收入"""
        return self._revenue
    
    @property
    def net_profit(self) -> Optional[float]:
        """获取净利润"""
        return self._net_profit
    
    @property
    def debt_ratio(self) -> Optional[float]:
        """获取资产负债率"""
        return self._debt_ratio
    
    @property
    def market_cap(self) -> Optional[float]:
        """获取市值"""
        return self._market_cap
    
    @property
    def industry(self) -> Optional[str]:
        """获取行业"""
        return self._industry
    
    @property
    def dividend_yield(self) -> Optional[float]:
        """获取股息率"""
        return self._dividend_yield
    
    @property
    def revenue_growth(self) -> Optional[float]:
        """获取营收增长率"""
        return self._revenue_growth
    
    @property
    def profit_growth(self) -> Optional[float]:
        """获取净利润增长率"""
        return self._profit_growth
    
    # ==================== 序列化方法 ====================
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        return {
            'stock_code': self._stock_code.code,
            'stock_name': self._stock_name,
            'roe': self._roe,
            'pe': self._pe,
            'pb': self._pb,
            'eps': self._eps,
            'revenue': self._revenue,
            'net_profit': self._net_profit,
            'debt_ratio': self._debt_ratio,
            'market_cap': self._market_cap,
            'industry': self._industry,
            'dividend_yield': self._dividend_yield,
            'revenue_growth': self._revenue_growth,
            'profit_growth': self._profit_growth
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Stock':
        """
        从字典反序列化
        
        Args:
            data: 包含股票属性的字典
            
        Returns:
            Stock 实例
            
        Note:
            stock_code 可以是字符串或 StockCode 对象
        """
        # 延迟导入以避免循环依赖
        from shared_kernel.value_objects.stock_code import StockCode
        
        stock_code_value = data['stock_code']
        if isinstance(stock_code_value, str):
            stock_code = StockCode(stock_code_value)
        else:
            stock_code = stock_code_value
        
        return cls(
            stock_code=stock_code,
            stock_name=data['stock_name'],
            roe=data.get('roe'),
            pe=data.get('pe'),
            pb=data.get('pb'),
            eps=data.get('eps'),
            revenue=data.get('revenue'),
            net_profit=data.get('net_profit'),
            debt_ratio=data.get('debt_ratio'),
            market_cap=data.get('market_cap'),
            industry=data.get('industry'),
            dividend_yield=data.get('dividend_yield'),
            revenue_growth=data.get('revenue_growth'),
            profit_growth=data.get('profit_growth')
        )
    
    # ==================== 特殊方法 ====================
    
    def __eq__(self, other: object) -> bool:
        """
        判断两个 Stock 是否相等
        
        基于 stock_code 判断相等性（实体标识）
        """
        if not isinstance(other, Stock):
            return False
        return self._stock_code == other._stock_code
    
    def __hash__(self) -> int:
        """
        计算哈希值
        
        基于 stock_code 计算哈希值
        """
        return hash(self._stock_code)
    
    def __repr__(self) -> str:
        """返回字符串表示"""
        return (f"Stock(stock_code={self._stock_code!r}, "
                f"stock_name='{self._stock_name}', "
                f"industry={self._industry!r})")
