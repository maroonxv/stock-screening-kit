"""请求 DTO - 用于验证和解析 API 请求数据

实现 IndustryResearchRequest 和 CredibilityVerificationRequest，
提供请求数据验证和解析功能。
"""
import re
from dataclasses import dataclass
from typing import Any, Dict


# A股代码验证正则表达式（与 StockCode 值对象保持一致）
STOCK_CODE_PATTERN = r'^\d{6}\.(SH|SZ)$'


@dataclass
class IndustryResearchRequest:
    """快速行业认知请求 DTO
    
    用于验证和解析 POST /api/intelligence/tasks/industry-research 请求。
    
    Attributes:
        query: 用户查询文本（如"快速了解合成生物学赛道"）
    """
    query: str
    
    def __post_init__(self):
        """初始化后处理：去除首尾空白"""
        if isinstance(self.query, str):
            self.query = self.query.strip()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndustryResearchRequest':
        """从字典创建请求对象
        
        Args:
            data: 请求 JSON 数据字典
            
        Returns:
            IndustryResearchRequest 实例
            
        Raises:
            ValueError: 如果 data 为 None 或不是字典
        """
        if data is None:
            raise ValueError("请求数据不能为空")
        if not isinstance(data, dict):
            raise ValueError("请求数据必须是 JSON 对象")
        
        query = data.get('query', '')
        if not isinstance(query, str):
            query = str(query) if query is not None else ''
        
        return cls(query=query)
    
    def validate(self) -> None:
        """验证请求数据
        
        Raises:
            ValueError: 如果验证失败
        """
        if not self.query:
            raise ValueError("查询文本不能为空")


@dataclass
class CredibilityVerificationRequest:
    """概念可信度验证请求 DTO
    
    用于验证和解析 POST /api/intelligence/tasks/credibility-verification 请求。
    
    Attributes:
        stock_code: A股代码（格式如 600519.SH 或 000001.SZ）
        concept: 被验证的概念（如"AI+白酒"）
    """
    stock_code: str
    concept: str
    
    def __post_init__(self):
        """初始化后处理：去除首尾空白"""
        if isinstance(self.stock_code, str):
            self.stock_code = self.stock_code.strip()
        if isinstance(self.concept, str):
            self.concept = self.concept.strip()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CredibilityVerificationRequest':
        """从字典创建请求对象
        
        Args:
            data: 请求 JSON 数据字典
            
        Returns:
            CredibilityVerificationRequest 实例
            
        Raises:
            ValueError: 如果 data 为 None 或不是字典
        """
        if data is None:
            raise ValueError("请求数据不能为空")
        if not isinstance(data, dict):
            raise ValueError("请求数据必须是 JSON 对象")
        
        stock_code = data.get('stock_code', '')
        if not isinstance(stock_code, str):
            stock_code = str(stock_code) if stock_code is not None else ''
        
        concept = data.get('concept', '')
        if not isinstance(concept, str):
            concept = str(concept) if concept is not None else ''
        
        return cls(stock_code=stock_code, concept=concept)
    
    def validate(self) -> None:
        """验证请求数据
        
        Raises:
            ValueError: 如果验证失败
        """
        if not self.stock_code:
            raise ValueError("股票代码不能为空")
        
        if not re.match(STOCK_CODE_PATTERN, self.stock_code):
            raise ValueError(
                f"无效的股票代码格式: {self.stock_code}，"
                "应为 6 位数字 + .SH 或 .SZ（如 600519.SH 或 000001.SZ）"
            )
        
        if not self.concept:
            raise ValueError("概念不能为空")
