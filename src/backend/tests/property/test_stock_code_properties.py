"""StockCode 属性基测试"""
import pytest
from hypothesis import given, strategies as st, settings

from shared_kernel.value_objects.stock_code import StockCode


# Feature: stock-screening-platform, Property 1: StockCode 格式验证一致性
# Validates: Requirements 1.3, 1.5
@settings(max_examples=10)
@given(st.from_regex(r'^\d{6}\.(SH|SZ)$', fullmatch=True))
def test_valid_stock_code_construction(code_string):
    """
    Property 1: StockCode 格式验证一致性
    
    对于任意字符串 s，如果 s 匹配正则表达式 ^\\d{6}\\.(SH|SZ)$，
    则 StockCode(s) 应成功构造；如果 s 不匹配该模式，
    则 StockCode(s) 应抛出 ValueError。
    """
    # 如果字符串匹配正则，应该成功构造
    stock_code = StockCode(code_string)
    assert stock_code.code == code_string
    assert stock_code.exchange in ['SH', 'SZ']
    assert len(stock_code.numeric_code) == 6
    assert stock_code.numeric_code.isdigit()


@settings(max_examples=10)
@given(st.text().filter(lambda s: not s or not s[0].isdigit() or '.' not in s))
def test_invalid_stock_code_construction(invalid_string):
    """
    Property 1 (反向): 无效格式应抛出 ValueError
    
    对于任意不匹配正则的字符串，StockCode 构造应失败
    """
    with pytest.raises(ValueError, match="无效的股票代码格式"):
        StockCode(invalid_string)


@settings(max_examples=10)
@given(st.from_regex(r'^\d{6}\.(SH|SZ)$', fullmatch=True))
def test_stock_code_properties_consistency(code_string):
    """
    验证 StockCode 属性的一致性
    
    对于任意有效的股票代码，code、exchange 和 numeric_code 属性
    应该保持一致
    """
    stock_code = StockCode(code_string)
    
    # 重构后的代码应该等于原始代码
    reconstructed = f"{stock_code.numeric_code}.{stock_code.exchange}"
    assert reconstructed == code_string
    assert reconstructed == stock_code.code


@settings(max_examples=10)
@given(st.from_regex(r'^\d{6}\.(SH|SZ)$', fullmatch=True))
def test_stock_code_equality_and_hash(code_string):
    """
    验证 StockCode 的相等性和哈希一致性
    
    对于任意有效的股票代码，相同代码构造的两个 StockCode 对象
    应该相等且具有相同的哈希值
    """
    stock_code1 = StockCode(code_string)
    stock_code2 = StockCode(code_string)
    
    # 相等性
    assert stock_code1 == stock_code2
    
    # 哈希一致性
    assert hash(stock_code1) == hash(stock_code2)
    
    # 可用于集合
    stock_set = {stock_code1, stock_code2}
    assert len(stock_set) == 1


@settings(max_examples=10)
@given(
    st.from_regex(r'^\d{6}\.(SH|SZ)$', fullmatch=True),
    st.from_regex(r'^\d{6}\.(SH|SZ)$', fullmatch=True)
)
def test_stock_code_inequality(code1, code2):
    """
    验证不同代码的 StockCode 对象不相等
    
    对于任意两个不同的股票代码，构造的 StockCode 对象应该不相等
    """
    if code1 != code2:
        stock_code1 = StockCode(code1)
        stock_code2 = StockCode(code2)
        assert stock_code1 != stock_code2
