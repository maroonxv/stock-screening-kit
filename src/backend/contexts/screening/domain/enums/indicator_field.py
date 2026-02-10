"""
指标字段枚举定义
"""
from enum import Enum
from .enums import IndicatorCategory, ValueType


class IndicatorField(Enum):
    """
    指标字段枚举，每个成员携带元数据：
    - display_name: 显示名称
    - category: 指标分类
    - value_type: 值类型
    - description: 描述
    """
    
    # 基础指标 (BASIC)
    ROE = ("净资产收益率", IndicatorCategory.BASIC, ValueType.NUMERIC, "净利润/净资产")
    PE = ("市盈率", IndicatorCategory.BASIC, ValueType.NUMERIC, "股价/每股收益")
    PB = ("市净率", IndicatorCategory.BASIC, ValueType.NUMERIC, "股价/每股净资产")
    EPS = ("每股收益", IndicatorCategory.BASIC, ValueType.NUMERIC, "净利润/总股本")
    REVENUE = ("营业收入", IndicatorCategory.BASIC, ValueType.NUMERIC, "企业营业收入总额")
    NET_PROFIT = ("净利润", IndicatorCategory.BASIC, ValueType.NUMERIC, "企业净利润")
    DEBT_RATIO = ("资产负债率", IndicatorCategory.BASIC, ValueType.NUMERIC, "总负债/总资产")
    MARKET_CAP = ("市值", IndicatorCategory.BASIC, ValueType.NUMERIC, "股价×总股本")
    GROSS_MARGIN = ("毛利率", IndicatorCategory.BASIC, ValueType.NUMERIC, "毛利润/营业收入")
    NET_MARGIN = ("净利率", IndicatorCategory.BASIC, ValueType.NUMERIC, "净利润/营业收入")
    CURRENT_RATIO = ("流动比率", IndicatorCategory.BASIC, ValueType.NUMERIC, "流动资产/流动负债")
    QUICK_RATIO = ("速动比率", IndicatorCategory.BASIC, ValueType.NUMERIC, "(流动资产-存货)/流动负债")
    
    # 时间序列指标 (TIME_SERIES)
    ROE_CONTINUOUS_GROWTH_YEARS = ("ROE连续增长年数", IndicatorCategory.TIME_SERIES, ValueType.NUMERIC, "ROE连续增长的年数")
    REVENUE_CAGR_3Y = ("营收3年复合增长率", IndicatorCategory.TIME_SERIES, ValueType.NUMERIC, "近3年营业收入复合增长率")
    REVENUE_CAGR_5Y = ("营收5年复合增长率", IndicatorCategory.TIME_SERIES, ValueType.NUMERIC, "近5年营业收入复合增长率")
    NET_PROFIT_CAGR_3Y = ("净利润3年复合增长率", IndicatorCategory.TIME_SERIES, ValueType.NUMERIC, "近3年净利润复合增长率")
    NET_PROFIT_CAGR_5Y = ("净利润5年复合增长率", IndicatorCategory.TIME_SERIES, ValueType.NUMERIC, "近5年净利润复合增长率")
    EPS_GROWTH_RATE = ("EPS增长率", IndicatorCategory.TIME_SERIES, ValueType.NUMERIC, "每股收益同比增长率")
    
    # 衍生指标 (DERIVED)
    PE_PB_RATIO = ("PE/PB比率", IndicatorCategory.DERIVED, ValueType.NUMERIC, "市盈率/市净率")
    PEG = ("PEG比率", IndicatorCategory.DERIVED, ValueType.NUMERIC, "市盈率/盈利增长率")
    ROE_PE_PRODUCT = ("ROE×PE", IndicatorCategory.DERIVED, ValueType.NUMERIC, "ROE与PE的乘积")
    DEBT_TO_EQUITY = ("负债权益比", IndicatorCategory.DERIVED, ValueType.NUMERIC, "总负债/股东权益")
    
    # 文本类型指标
    INDUSTRY = ("所属行业", IndicatorCategory.BASIC, ValueType.TEXT, "股票所属行业分类")
    STOCK_NAME = ("股票名称", IndicatorCategory.BASIC, ValueType.TEXT, "股票名称")
    
    def __init__(self, display_name: str, category: IndicatorCategory, 
                 value_type: ValueType, description: str = ""):
        self.display_name = display_name
        self.category = category
        self.value_type = value_type
        self.description = description
