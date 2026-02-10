"""StockCode 值对象 - A股代码"""
import re


class StockCode:
    """A股代码值对象
    
    格式：6位数字 + .SH 或 .SZ
    沪市：600xxx.SH, 601xxx.SH, 603xxx.SH, 688xxx.SH
    深市：000xxx.SZ, 001xxx.SZ, 002xxx.SZ, 300xxx.SZ
    """
    
    VALID_PATTERN = r'^\d{6}\.(SH|SZ)$'
    
    def __init__(self, code: str):
        """初始化股票代码
        
        Args:
            code: 股票代码字符串，格式为 "XXXXXX.SH" 或 "XXXXXX.SZ"
            
        Raises:
            ValueError: 如果代码格式无效
        """
        if not re.match(self.VALID_PATTERN, code):
            raise ValueError(f"无效的股票代码格式: {code}")
        self._code = code
    
    @property
    def code(self) -> str:
        """完整的股票代码"""
        return self._code
    
    @property
    def exchange(self) -> str:
        """交易所代码 (SH 或 SZ)"""
        return self._code.split('.')[1]
    
    @property
    def numeric_code(self) -> str:
        """6位数字代码"""
        return self._code.split('.')[0]
    
    def __eq__(self, other):
        """相等性比较"""
        return isinstance(other, StockCode) and self._code == other._code
    
    def __hash__(self):
        """哈希值，使对象可用于集合和字典"""
        return hash(self._code)
    
    def __repr__(self):
        """字符串表示"""
        return f"StockCode('{self._code}')"
    
    def __str__(self):
        """字符串转换"""
        return self._code
