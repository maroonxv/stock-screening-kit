"""
Stock 实体单元测试

测试 Stock 的核心功能：
- 构造和属性访问
- to_dict() / from_dict() 序列化
- __eq__, __hash__, __repr__ 方法

Requirements:
- 2.5: Stock 实体，包含财务指标属性（roe、pe、pb、eps、revenue、net_profit、debt_ratio、market_cap 等）
"""
import pytest

from contexts.screening.domain.models.stock import Stock
from shared_kernel.value_objects.stock_code import StockCode


class TestStockConstruction:
    """Stock 构造测试"""
    
    def test_create_with_required_params(self):
        """测试使用必需参数创建 Stock"""
        stock_code = StockCode("600000.SH")
        stock = Stock(
            stock_code=stock_code,
            stock_name="浦发银行"
        )
        
        assert stock.stock_code == stock_code
        assert stock.stock_name == "浦发银行"
        # 所有财务指标应为 None
        assert stock.roe is None
        assert stock.pe is None
        assert stock.pb is None
        assert stock.eps is None
        assert stock.revenue is None
        assert stock.net_profit is None
        assert stock.debt_ratio is None
        assert stock.market_cap is None
        assert stock.industry is None
        assert stock.dividend_yield is None
        assert stock.revenue_growth is None
        assert stock.profit_growth is None
    
    def test_create_with_all_params(self):
        """测试使用所有参数创建 Stock"""
        stock_code = StockCode("000001.SZ")
        stock = Stock(
            stock_code=stock_code,
            stock_name="平安银行",
            roe=0.12,
            pe=8.5,
            pb=0.8,
            eps=1.5,
            revenue=1500000000000.0,
            net_profit=300000000000.0,
            debt_ratio=0.92,
            market_cap=250000000000.0,
            industry="银行",
            dividend_yield=0.05,
            revenue_growth=0.08,
            profit_growth=0.10
        )
        
        assert stock.stock_code == stock_code
        assert stock.stock_name == "平安银行"
        assert stock.roe == 0.12
        assert stock.pe == 8.5
        assert stock.pb == 0.8
        assert stock.eps == 1.5
        assert stock.revenue == 1500000000000.0
        assert stock.net_profit == 300000000000.0
        assert stock.debt_ratio == 0.92
        assert stock.market_cap == 250000000000.0
        assert stock.industry == "银行"
        assert stock.dividend_yield == 0.05
        assert stock.revenue_growth == 0.08
        assert stock.profit_growth == 0.10
    
    def test_create_with_partial_params(self):
        """测试使用部分参数创建 Stock"""
        stock_code = StockCode("600519.SH")
        stock = Stock(
            stock_code=stock_code,
            stock_name="贵州茅台",
            roe=0.30,
            pe=35.0,
            industry="白酒"
        )
        
        assert stock.stock_code == stock_code
        assert stock.stock_name == "贵州茅台"
        assert stock.roe == 0.30
        assert stock.pe == 35.0
        assert stock.industry == "白酒"
        # 未设置的参数应为 None
        assert stock.pb is None
        assert stock.eps is None
        assert stock.revenue is None
    
    def test_create_with_negative_values(self):
        """测试使用负值创建 Stock（如亏损公司）"""
        stock_code = StockCode("300001.SZ")
        stock = Stock(
            stock_code=stock_code,
            stock_name="某亏损公司",
            roe=-0.15,
            pe=-10.0,  # 负市盈率表示亏损
            eps=-0.5,
            net_profit=-100000000.0,
            profit_growth=-0.20
        )
        
        assert stock.roe == -0.15
        assert stock.pe == -10.0
        assert stock.eps == -0.5
        assert stock.net_profit == -100000000.0
        assert stock.profit_growth == -0.20
    
    def test_create_with_zero_values(self):
        """测试使用零值创建 Stock"""
        stock_code = StockCode("688001.SH")
        stock = Stock(
            stock_code=stock_code,
            stock_name="某公司",
            roe=0.0,
            pe=0.0,
            revenue_growth=0.0
        )
        
        assert stock.roe == 0.0
        assert stock.pe == 0.0
        assert stock.revenue_growth == 0.0


class TestStockSerialization:
    """Stock 序列化测试"""
    
    def test_to_dict_with_all_params(self):
        """测试完整参数的序列化"""
        stock_code = StockCode("000001.SZ")
        stock = Stock(
            stock_code=stock_code,
            stock_name="平安银行",
            roe=0.12,
            pe=8.5,
            pb=0.8,
            eps=1.5,
            revenue=1500000000000.0,
            net_profit=300000000000.0,
            debt_ratio=0.92,
            market_cap=250000000000.0,
            industry="银行",
            dividend_yield=0.05,
            revenue_growth=0.08,
            profit_growth=0.10
        )
        
        result = stock.to_dict()
        
        assert result['stock_code'] == "000001.SZ"
        assert result['stock_name'] == "平安银行"
        assert result['roe'] == 0.12
        assert result['pe'] == 8.5
        assert result['pb'] == 0.8
        assert result['eps'] == 1.5
        assert result['revenue'] == 1500000000000.0
        assert result['net_profit'] == 300000000000.0
        assert result['debt_ratio'] == 0.92
        assert result['market_cap'] == 250000000000.0
        assert result['industry'] == "银行"
        assert result['dividend_yield'] == 0.05
        assert result['revenue_growth'] == 0.08
        assert result['profit_growth'] == 0.10
    
    def test_to_dict_with_none_values(self):
        """测试带 None 值的序列化"""
        stock_code = StockCode("600000.SH")
        stock = Stock(
            stock_code=stock_code,
            stock_name="浦发银行",
            roe=0.10
        )
        
        result = stock.to_dict()
        
        assert result['stock_code'] == "600000.SH"
        assert result['stock_name'] == "浦发银行"
        assert result['roe'] == 0.10
        assert result['pe'] is None
        assert result['pb'] is None
        assert result['industry'] is None
    
    def test_from_dict_with_string_stock_code(self):
        """测试从字典反序列化（stock_code 为字符串）"""
        data = {
            'stock_code': "000001.SZ",
            'stock_name': "平安银行",
            'roe': 0.12,
            'pe': 8.5,
            'pb': 0.8,
            'eps': 1.5,
            'revenue': 1500000000000.0,
            'net_profit': 300000000000.0,
            'debt_ratio': 0.92,
            'market_cap': 250000000000.0,
            'industry': "银行",
            'dividend_yield': 0.05,
            'revenue_growth': 0.08,
            'profit_growth': 0.10
        }
        
        stock = Stock.from_dict(data)
        
        assert stock.stock_code == StockCode("000001.SZ")
        assert stock.stock_name == "平安银行"
        assert stock.roe == 0.12
        assert stock.pe == 8.5
        assert stock.pb == 0.8
        assert stock.eps == 1.5
        assert stock.revenue == 1500000000000.0
        assert stock.net_profit == 300000000000.0
        assert stock.debt_ratio == 0.92
        assert stock.market_cap == 250000000000.0
        assert stock.industry == "银行"
        assert stock.dividend_yield == 0.05
        assert stock.revenue_growth == 0.08
        assert stock.profit_growth == 0.10
    
    def test_from_dict_with_stock_code_object(self):
        """测试从字典反序列化（stock_code 为 StockCode 对象）"""
        stock_code = StockCode("600519.SH")
        data = {
            'stock_code': stock_code,
            'stock_name': "贵州茅台",
            'roe': 0.30
        }
        
        stock = Stock.from_dict(data)
        
        assert stock.stock_code == stock_code
        assert stock.stock_name == "贵州茅台"
        assert stock.roe == 0.30
    
    def test_from_dict_with_missing_optional_fields(self):
        """测试从字典反序列化（缺少可选字段）"""
        data = {
            'stock_code': "600000.SH",
            'stock_name': "浦发银行"
        }
        
        stock = Stock.from_dict(data)
        
        assert stock.stock_code == StockCode("600000.SH")
        assert stock.stock_name == "浦发银行"
        assert stock.roe is None
        assert stock.pe is None
        assert stock.industry is None
    
    def test_serialization_round_trip(self):
        """测试序列化往返"""
        stock_code = StockCode("000001.SZ")
        original = Stock(
            stock_code=stock_code,
            stock_name="平安银行",
            roe=0.12,
            pe=8.5,
            pb=0.8,
            eps=1.5,
            revenue=1500000000000.0,
            net_profit=300000000000.0,
            debt_ratio=0.92,
            market_cap=250000000000.0,
            industry="银行",
            dividend_yield=0.05,
            revenue_growth=0.08,
            profit_growth=0.10
        )
        
        # 序列化然后反序列化
        data = original.to_dict()
        restored = Stock.from_dict(data)
        
        # 验证相等
        assert restored == original
        assert restored.stock_name == original.stock_name
        assert restored.roe == original.roe
        assert restored.pe == original.pe
        assert restored.pb == original.pb
        assert restored.eps == original.eps
        assert restored.revenue == original.revenue
        assert restored.net_profit == original.net_profit
        assert restored.debt_ratio == original.debt_ratio
        assert restored.market_cap == original.market_cap
        assert restored.industry == original.industry
        assert restored.dividend_yield == original.dividend_yield
        assert restored.revenue_growth == original.revenue_growth
        assert restored.profit_growth == original.profit_growth
    
    def test_serialization_round_trip_with_none_values(self):
        """测试带 None 值的序列化往返"""
        stock_code = StockCode("600519.SH")
        original = Stock(
            stock_code=stock_code,
            stock_name="贵州茅台",
            roe=0.30,
            industry="白酒"
        )
        
        # 序列化然后反序列化
        data = original.to_dict()
        restored = Stock.from_dict(data)
        
        # 验证相等
        assert restored == original
        assert restored.stock_name == original.stock_name
        assert restored.roe == original.roe
        assert restored.pe is None
        assert restored.industry == original.industry


class TestStockEquality:
    """Stock 相等性测试"""
    
    def test_equal_stocks_same_code(self):
        """测试相同代码的股票相等"""
        stock_code = StockCode("000001.SZ")
        stock1 = Stock(stock_code=stock_code, stock_name="平安银行", roe=0.12)
        stock2 = Stock(stock_code=stock_code, stock_name="平安银行", roe=0.15)  # 不同的 roe
        
        # 基于 stock_code 判断相等
        assert stock1 == stock2
    
    def test_not_equal_different_codes(self):
        """测试不同代码的股票不相等"""
        stock1 = Stock(stock_code=StockCode("000001.SZ"), stock_name="平安银行")
        stock2 = Stock(stock_code=StockCode("600000.SH"), stock_name="浦发银行")
        
        assert stock1 != stock2
    
    def test_not_equal_to_non_stock(self):
        """测试与非 Stock 对象不相等"""
        stock = Stock(stock_code=StockCode("000001.SZ"), stock_name="平安银行")
        
        assert stock != "not a stock"
        assert stock != 123
        assert stock != None
        assert stock != {"stock_code": "000001.SZ"}


class TestStockHash:
    """Stock 哈希测试"""
    
    def test_hash_consistency(self):
        """测试哈希值一致性"""
        stock_code = StockCode("000001.SZ")
        stock = Stock(stock_code=stock_code, stock_name="平安银行")
        
        # 多次调用应返回相同的哈希值
        assert hash(stock) == hash(stock)
    
    def test_equal_stocks_same_hash(self):
        """测试相等的股票有相同的哈希值"""
        stock_code = StockCode("000001.SZ")
        stock1 = Stock(stock_code=stock_code, stock_name="平安银行", roe=0.12)
        stock2 = Stock(stock_code=stock_code, stock_name="平安银行", roe=0.15)
        
        assert hash(stock1) == hash(stock2)
    
    def test_can_be_used_in_set(self):
        """测试可以在集合中使用"""
        stock_code = StockCode("000001.SZ")
        stock1 = Stock(stock_code=stock_code, stock_name="平安银行")
        stock2 = Stock(stock_code=stock_code, stock_name="平安银行")
        stock3 = Stock(stock_code=StockCode("600000.SH"), stock_name="浦发银行")
        
        stock_set = {stock1, stock2, stock3}
        
        # stock1 和 stock2 相等，所以集合中只有 2 个元素
        assert len(stock_set) == 2
    
    def test_can_be_used_as_dict_key(self):
        """测试可以作为字典键使用"""
        stock1 = Stock(stock_code=StockCode("000001.SZ"), stock_name="平安银行")
        stock2 = Stock(stock_code=StockCode("600000.SH"), stock_name="浦发银行")
        
        stock_dict = {stock1: "银行A", stock2: "银行B"}
        
        assert stock_dict[stock1] == "银行A"
        assert stock_dict[stock2] == "银行B"


class TestStockRepr:
    """Stock __repr__ 测试"""
    
    def test_repr_basic(self):
        """测试基本的字符串表示"""
        stock = Stock(
            stock_code=StockCode("000001.SZ"),
            stock_name="平安银行"
        )
        
        repr_str = repr(stock)
        
        assert "Stock" in repr_str
        assert "000001.SZ" in repr_str
        assert "平安银行" in repr_str
    
    def test_repr_with_industry(self):
        """测试带行业的字符串表示"""
        stock = Stock(
            stock_code=StockCode("600519.SH"),
            stock_name="贵州茅台",
            industry="白酒"
        )
        
        repr_str = repr(stock)
        
        assert "Stock" in repr_str
        assert "600519.SH" in repr_str
        assert "贵州茅台" in repr_str
        assert "白酒" in repr_str
    
    def test_repr_with_none_industry(self):
        """测试行业为 None 的字符串表示"""
        stock = Stock(
            stock_code=StockCode("000001.SZ"),
            stock_name="平安银行"
        )
        
        repr_str = repr(stock)
        
        assert "industry=None" in repr_str


class TestStockEdgeCases:
    """Stock 边界情况测试"""
    
    def test_very_large_values(self):
        """测试非常大的数值"""
        stock = Stock(
            stock_code=StockCode("600519.SH"),
            stock_name="贵州茅台",
            revenue=1e15,  # 1000万亿
            market_cap=5e12  # 5万亿
        )
        
        assert stock.revenue == 1e15
        assert stock.market_cap == 5e12
    
    def test_very_small_values(self):
        """测试非常小的数值"""
        stock = Stock(
            stock_code=StockCode("300001.SZ"),
            stock_name="某小公司",
            roe=0.0001,
            eps=0.001
        )
        
        assert stock.roe == 0.0001
        assert stock.eps == 0.001
    
    def test_empty_string_name(self):
        """测试空字符串名称（虽然不推荐，但应该能处理）"""
        stock = Stock(
            stock_code=StockCode("000001.SZ"),
            stock_name=""
        )
        
        assert stock.stock_name == ""
    
    def test_unicode_name(self):
        """测试 Unicode 名称"""
        stock = Stock(
            stock_code=StockCode("000001.SZ"),
            stock_name="平安银行🏦"
        )
        
        assert stock.stock_name == "平安银行🏦"
    
    def test_unicode_industry(self):
        """测试 Unicode 行业"""
        stock = Stock(
            stock_code=StockCode("600519.SH"),
            stock_name="贵州茅台",
            industry="食品饮料-白酒"
        )
        
        assert stock.industry == "食品饮料-白酒"
