"""
基金模块包
每个基金作为一个独立的子模块
"""

from .fund_159687 import Fund159687
from .fund_513730 import Fund513730

# 添加新基金时在这里导入
# from .fund_159915 import Fund159915
# from .fund_xxxxx import FundXXXXX

__all__ = [
    'Fund159687',
    'Fund513730',
    # 'Fund159915',
    # 'FundXXXXX',
]

# 所有可用的基金列表
AVAILABLE_FUNDS = [
    Fund159687,
    Fund513730,
    # Fund159915,
    # FundXXXXX,
]
