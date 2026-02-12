股票列表-A股

接口: stock_info_a_code_name

目标地址: 沪深京三个交易所

描述: 沪深京 A 股股票代码和股票简称数据

限量: 单次获取所有 A 股股票代码和简称数据

输入参数

名称类型描述---

输出参数

名称类型描述codeobject-nameobject-

接口示例

import akshare as ak  stock_info_a_code_name_df = ak.stock_info_a_code_name() print(stock_info_a_code_name_df) 

数据示例

code   name 0     000001   平安银行 1     000002  万  科Ａ 2     000004   国华网安 3     000005   ST星源 4     000006   深振业Ａ       ...    ... 4623  871396   常辅股份 4624  871553   凯腾精工 4625  871642   通易航天 4626  871981   晶赛科技 4627  872925   锦好医疗



估值比较

接口: stock_zh_valuation_comparison_em

目标地址: https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?type=web&code=000895&color=b#/thbj/gzbj

描述: 东方财富-行情中心-同行比较-估值比较

限量: 单次返回全部数据

输入参数

名称类型描述symbolstrsymbol="SZ000895"

输出参数

名称类型描述排名object-代码object-简称object-PEGfloat64-市盈率-24Afloat64-市盈率-TTMfloat64-市盈率-25Efloat64-市盈率-26Efloat64-市盈率-27Efloat64-市销率-24Afloat64-市销率-TTMfloat64-市销率-25Efloat64-市销率-26Efloat64-市销率-27Efloat64-市净率-24Afloat64-市净率-MRQfloat64-市现率1-24Afloat64-市现率1-TTMfloat64-市现率2-24Afloat64-市现率2-TTMfloat64-EV/EBITDA-24Afloat64-

接口示例

import akshare as ak  stock_zh_valuation_comparison_em_df = ak.stock_zh_valuation_comparison_em(symbol="SZ000895") print(stock_zh_valuation_comparison_em_df)





财务报表-同花顺

资产负债表

接口: stock_financial_debt_new_ths

目标地址: https://basic.10jqka.com.cn/astockpc/astockmain/index.html#/financen?code=000063

描述: 同花顺-财务指标-资产负债表；替换 stock_financial_debt_ths 接口

限量: 单次获取资产负债表所有历史数据

输入参数

名称类型描述symbolstrsymbol="000063"; 股票代码indicatorstrindicator="按报告期"; choice of {"按报告期", "按年度"}

输出参数

名称类型描述report_dateobject-report_nameobject-report_periodobject-quarter_nameobject-metric_nameobject-valuefloat64-singleobject-yoyfloat64-momobject-single_yoyobject-

接口示例

import akshare as ak  stock_financial_debt_new_ths_df = ak.stock_financial_debt_new_ths(symbol="000063", indicator="按年度") print(stock_financial_debt_new_ths_df) 

数据示例

report_date report_name report_period  ...          yoy   mom single_yoy 0     2024-12-31      2024年报        2024-4  ...         <NA>  <NA>       <NA> 1     2024-12-31      2024年报        2024-4  ...         <NA>  <NA>       <NA> 2     2024-12-31      2024年报        2024-4  ...   0.16420728  <NA>       <NA> 3     2024-12-31      2024年报        2024-4  ...  -0.15807123  <NA>       <NA> 4     2024-12-31      2024年报        2024-4  ...   0.00005916  <NA>       <NA> ...          ...         ...           ...  ...          ...   ...        ... 3684  1994-12-31      1994年报        1994-4  ...         <NA>  <NA>       <NA> 3685  1994-12-31      1994年报        1994-4  ...         <NA>  <NA>       <NA> 3686  1994-12-31      1994年报        1994-4  ...         <NA>  <NA>       <NA> 3687  1994-12-31      1994年报        1994-4  ...         <NA>  <NA>       <NA> 3688  1994-12-31      1994年报        1994-4  ...         <NA>  <NA>       <NA> [3689 rows x 10 columns] 

利润表

接口: stock_financial_benefit_new_ths

目标地址: https://basic.10jqka.com.cn/astockpc/astockmain/index.html#/financen?code=000063

描述: 同花顺-财务指标-利润表；替换 stock_financial_benefit_ths 接口

限量: 单次获取利润表所有历史数据

输入参数

名称类型描述symbolstrsymbol="000063"; 股票代码indicatorstrindicator="按报告期"; choice of {"按报告期", "一季度", "二季度", "三季度", "四季度", "按年度"}

输出参数

名称类型描述report_dateobject-report_nameobject-report_periodobject-quarter_nameobject-metric_nameobject-valuefloat64-singleobject-yoyfloat64-momobject-single_yoyobject-

接口示例

import akshare as ak  stock_financial_benefit_new_ths_df = ak.stock_financial_benefit_new_ths(symbol="000063", indicator="按报告期") print(stock_financial_benefit_new_ths_df) 

数据示例

report_date report_name report_period  ...        yoy       mom  single_yoy 0     2025-09-30     2025三季报        2025-3  ...  -0.307496 -0.912701   -0.893714 1     2025-09-30     2025三季报        2025-3  ...        NaN       NaN         NaN 2     2025-09-30     2025三季报        2025-3  ...   0.116943 -0.221946   -0.139571 3     2025-09-30     2025三季报        2025-3  ...        NaN       NaN         NaN 4     2025-09-30     2025三季报        2025-3  ...        NaN       NaN         NaN ...          ...         ...           ...  ...        ...       ...         ... 2545  2013-06-30      2013中报        2013-2  ...   0.285714 -0.500000    0.000000 2546  2013-06-30      2013中报        2013-2  ...        NaN       NaN         NaN 2547  2013-06-30      2013中报        2013-2  ...        NaN       NaN         NaN 2548  2013-06-30      2013中报        2013-2  ...        NaN       NaN         NaN 2549  2013-06-30      2013中报        2013-2  ... -11.669821  0.777595    0.078450 [2550 rows x 10 columns] 

现金流量表

接口: stock_financial_cash_new_ths

目标地址: https://basic.10jqka.com.cn/astockpc/astockmain/index.html#/financen?code=000063

描述: 同花顺-财务指标-现金流量表；替换 stock_financial_cash_ths 接口

限量: 单次获取现金流量表所有历史数据

输入参数

名称类型描述symbolstrsymbol="000063"; 股票代码indicatorstrindicator="按报告期"; choice of {"按报告期", "一季度", "二季度", "三季度", "四季度", "按年度"}

输出参数

名称类型描述report_dateobject-report_nameobject-report_periodobject-quarter_nameobject-metric_nameobject-valuefloat64-singleobject-yoyfloat64-momobject-single_yoyobject-

接口示例

import akshare as ak  stock_financial_cash_new_ths_df = ak.stock_financial_cash_new_ths(symbol="000063", indicator="按年度") print(stock_financial_cash_new_ths_df) 

数据示例

report_date report_name  ...          mom   single_yoy 0     2024-12-31      2024年报  ...         <NA>         <NA> 1     2024-12-31      2024年报  ...  -0.23161757   0.57803131 2     2024-12-31      2024年报  ...   0.36015447  -0.45630237 3     2024-12-31      2024年报  ...   0.17900055  -0.47569575 4     2024-12-31      2024年报  ...   0.05788915  -0.47553164 ...          ...         ...  ...          ...          ... 2425  1998-12-31      1998年报  ...         <NA>         <NA> 2426  1998-12-31      1998年报  ...         <NA>         <NA> 2427  1998-12-31      1998年报  ...         <NA>         <NA> 2428  1998-12-31      1998年报  ...         <NA>         <NA> 2429  1998-12-31      1998年报  ...         <NA>         <NA>

财务指标
接口: stock_financial_analysis_indicator

目标地址: https://money.finance.sina.com.cn/corp/go.php/vFD_FinancialGuideLine/stockid/600004/ctrl/2019/displaytype/4.phtml

描述: 新浪财经-财务分析-财务指标

限量: 单次获取指定 symbol 和 start_year 的所有财务指标历史数据

输入参数

名称	类型	描述
symbol	str	symbol="600004"; 股票代码
start_year	str	start_year="2020"; 开始查询的时间
输出参数

名称	类型	描述
日期	object	-
摊薄每股收益(元)	float64	-
加权每股收益(元)	float64	-
每股收益_调整后(元)	float64	-
扣除非经常性损益后的每股收益(元)	float64	-
每股净资产_调整前(元)	float64	-
每股净资产_调整后(元)	float64	-
每股经营性现金流(元)	float64	-
每股资本公积金(元)	float64	-
每股未分配利润(元)	float64	-
调整后的每股净资产(元)	float64	-
总资产利润率(%)	float64	-
主营业务利润率(%)	float64	-
总资产净利润率(%)	float64	-
成本费用利润率(%)	float64	-
营业利润率(%)	float64	-
主营业务成本率(%)	float64	-
销售净利率(%)	float64	-
股本报酬率(%)	float64	-
净资产报酬率(%)	float64	-
资产报酬率(%)	float64	-
销售毛利率(%)	float64	-
三项费用比重	float64	-
非主营比重	float64	-
主营利润比重	float64	-
股息发放率(%)	float64	-
投资收益率(%)	float64	-
主营业务利润(元)	float64	-
净资产收益率(%)	float64	-
加权净资产收益率(%)	float64	-
扣除非经常性损益后的净利润(元)	float64	-
主营业务收入增长率(%)	float64	-
净利润增长率(%)	float64	-
净资产增长率(%)	float64	-
总资产增长率(%)	float64	-
应收账款周转率(次)	float64	-
应收账款周转天数(天)	float64	-
存货周转天数(天)	float64	-
存货周转率(次)	float64	-
固定资产周转率(次)	float64	-
总资产周转率(次)	float64	-
总资产周转天数(天)	float64	-
流动资产周转率(次)	float64	-
流动资产周转天数(天)	float64	-
股东权益周转率(次)	float64	-
流动比率	float64	-
速动比率	float64	-
现金比率(%)	float64	-
利息支付倍数	float64	-
长期债务与营运资金比率(%)	float64	-
股东权益比率(%)	float64	-
长期负债比率(%)	float64	-
股东权益与固定资产比率(%)	float64	-
负债与所有者权益比率(%)	float64	-
长期资产与长期资金比率(%)	float64	-
资本化比率(%)	float64	-
固定资产净值率(%)	float64	-
资本固定化比率(%)	float64	-
产权比率(%)	float64	-
清算价值比率(%)	float64	-
固定资产比重(%)	float64	-
资产负债率(%)	float64	-
总资产(元)	float64	-
经营现金净流量对销售收入比率(%)	float64	-
资产的经营现金流量回报率(%)	float64	-
经营现金净流量与净利润的比率(%)	float64	-
经营现金净流量对负债比率(%)	float64	-
现金流量比率(%)	float64	-
短期股票投资(元)	float64	-
短期债券投资(元)	float64	-
短期其它经营性投资(元)	float64	-
长期股票投资(元)	float64	-
长期债券投资(元)	float64	-
长期其它经营性投资(元)	float64	-
1年以内应收帐款(元)	float64	-
1-2年以内应收帐款(元)	float64	-
2-3年以内应收帐款(元)	float64	-
3年以内应收帐款(元)	float64	-
1年以内预付货款(元)	float64	-
1-2年以内预付货款(元)	float64	-
2-3年以内预付货款(元)	float64	-
3年以内预付货款(元)	float64	-
1年以内其它应收款(元)	float64	-
1-2年以内其它应收款(元)	float64	-
2-3年以内其它应收款(元)	float64	-
3年以内其它应收款(元)	float64	-
接口示例

import akshare as ak

stock_financial_analysis_indicator_df = ak.stock_financial_analysis_indicator(symbol="600004", start_year="2020")
print(stock_financial_analysis_indicator_df)
数据示例

         日期  摊薄每股收益(元)  ... 2-3年以内其它应收款(元) 3年以内其它应收款(元)
0   2020-03-31    -0.0307  ...             NaN           NaN
1   2020-06-30    -0.0816  ...      1189862.00           NaN
2   2020-09-30    -0.1380  ...             NaN           NaN
3   2020-12-31    -0.0980  ...      1495234.99           NaN
4   2021-03-31    -0.0645  ...             NaN           NaN
5   2021-06-30    -0.1686  ...      3471186.42           NaN
6   2021-09-30    -0.2038  ...             NaN           NaN
7   2021-12-31    -0.1628  ...      1380992.96           NaN
8   2022-03-31    -0.0326  ...             NaN           NaN
9   2022-06-30    -0.2242  ...      1680204.08           NaN
10  2022-09-30    -0.2671  ...             NaN           NaN
11  2022-12-31    -0.4613  ...      2459538.50           NaN
12  2023-03-31     0.0216  ...             NaN           NaN
13  2023-06-30     0.0720  ...      2591827.74           NaN
14  2023-09-30     0.1232  ...             NaN           NaN
15  2023-12-31     0.2032  ...      7162683.42           NaN
16  2024-03-31     0.0841  ...             NaN           NaN
[17 rows x 86 columns]


公司概况-巨潮资讯
接口: stock_profile_cninfo

目标地址: http://webapi.cninfo.com.cn/#/company

描述: 巨潮资讯-个股-公司概况

限量: 单次获取指定 symbol 的公司概况

输入参数

名称	类型	描述
symbol	str	symbol="600030"
输出参数

名称	类型	描述
公司名称	object	-
英文名称	object	-
曾用简称	object	-
A股代码	object	-
A股简称	object	-
B股代码	object	-
B股简称	object	-
H股代码	object	-
H股简称	object	-
入选指数	object	-
所属市场	object	-
所属行业	object	-
法人代表	object	-
注册资金	object	-
成立日期	object	-
上市日期	object	-
官方网站	object	-
电子邮箱	object	-
联系电话	object	-
传真	object	-
注册地址	object	-
办公地址	object	-
邮政编码	object	-
主营业务	object	-
经营范围	object	-
机构简介	object	-
接口示例

import akshare as ak

stock_profile_cninfo_df = ak.stock_profile_cninfo(symbol="600030")
print(stock_profile_cninfo_df)
数据示例

         公司名称  ...                                               机构简介
0  中信证券股份有限公司  ...  公司的前身中信证券有限责任公司是经中国人民银行银复[1995]313号文批准，由中信公司，中...