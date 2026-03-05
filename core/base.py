"""
基金基类定义
所有基金模块必须继承此基类并实现相应方法
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import os


@dataclass
class FundData:
    """基金数据结构"""
    fund_code: str
    fund_name: str
    market_price: Optional[float] = None
    market_change_pct: Optional[float] = None
    market_time: Optional[str] = None
    estimated_nav: Optional[float] = None
    premium_discount: Optional[float] = None
    latest_nav: Optional[float] = None
    latest_nav_date: Optional[str] = None
    intraday_nav: Optional[float] = None
    intraday_nav_time: Optional[str] = None
    historical_nav: Optional[float] = None
    historical_nav_date: Optional[str] = None
    nav_change_pct: Optional[float] = None
    common_date_nav: Optional[float] = None
    common_date: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'fund_code': self.fund_code,
            'fund_name': self.fund_name,
            'market_price': self.market_price,
            'market_change_pct': self.market_change_pct,
            'market_time': self.market_time,
            'estimated_nav': self.estimated_nav,
            'premium_discount': self.premium_discount,
            'latest_nav': self.latest_nav,
            'latest_nav_date': self.latest_nav_date,
            'intraday_nav': self.intraday_nav,
            'intraday_nav_time': self.intraday_nav_time,
            'historical_nav': self.historical_nav,
            'historical_nav_date': self.historical_nav_date,
            'nav_change_pct': self.nav_change_pct,
            'common_date_nav': self.common_date_nav,
            'common_date': self.common_date,
            'extra_data': self.extra_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FundData':
        """从字典创建实例"""
        known_fields = {
            'fund_code', 'fund_name', 'market_price', 'market_change_pct',
            'market_time', 'estimated_nav', 'premium_discount', 'latest_nav',
            'latest_nav_date', 'intraday_nav', 'intraday_nav_time',
            'historical_nav', 'historical_nav_date', 'nav_change_pct', 'extra_data'
        }
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        extra_data = {k: v for k, v in data.items() if k not in known_fields}
        if extra_data:
            filtered_data['extra_data'] = extra_data
        return cls(**filtered_data)
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"FundData({self.fund_code} - {self.fund_name})"


class BaseFund(ABC):
    """
    基金基类 - 所有基金必须继承此类
    
    每个基金模块需要实现以下方法：
    - fund_code: 基金代码
    - fund_name: 基金名称
    - calculate(): 计算估值数据
    """
    
    def __init__(self, base_dir: str = None):
        """
        初始化基金
        
        Args:
            base_dir: 项目根目录，用于定位缓存和输出目录
        """
        self._base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    @property
    @abstractmethod
    def fund_code(self) -> str:
        """
        基金代码
        
        Returns:
            str: 基金代码，如 "159687"
        """
        pass
    
    @property
    @abstractmethod
    def fund_name(self) -> str:
        """
        基金名称
        
        Returns:
            str: 基金名称，如 "南方东英富时亚太低碳精选ETF"
        """
        pass
    
    @property
    def description(self) -> str:
        """
        基金描述（可选）
        
        Returns:
            str: 基金描述信息
        """
        return ""
    
    @property
    def update_interval(self) -> int:
        """
        自动刷新间隔（秒）
        
        Returns:
            int: 刷新间隔秒数，默认30秒
        """
        return 30
    
    @abstractmethod
    def calculate(self) -> FundData:
        """
        计算估值数据
        
        每个基金实现自己的估值逻辑，可以包括：
        - API调用
        - 网页爬虫
        - 股票组合计算
        - 任何自定义方法
        
        Returns:
            FundData: 基金数据对象
        """
        pass
    
    def get_cache_dir(self) -> str:
        """
        获取缓存目录路径
        
        Returns:
            str: 缓存目录路径
        """
        cache_dir = os.path.join(self._base_dir, 'cache', self.fund_code)
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir
    
    def get_output_dir(self) -> str:
        """
        获取输出目录路径
        
        Returns:
            str: 输出目录路径
        """
        output_dir = os.path.join(self._base_dir, 'output', self.fund_code)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def print_table(self, data: FundData) -> None:
        """
        打印表格（可选重写）
        
        Args:
            data: 基金数据
        """
        print("\n")
        print("┌" + "─" * 78)
        print(f"│ {self.fund_code} {self.fund_name:^68} │")
        print("├" + "─" * 78 + "")
        print("│ {:<20} │ {:^54} ".format("项目", "数值"))
        print("├" + "─" * 78)
        
        if data.market_price is not None:
            price_str = f"{data.market_price:.3f} CNY"
            print("│ {:<20}  {:^54} ".format("场内价格", price_str))
        
        if data.market_change_pct is not None:
            change_str = f"{data.market_change_pct:.2f}%"
            print("│ {:<20}  {:^54} ".format("涨跌幅", change_str))
        
        if data.market_time:
            print("│ {:<20}  {:^54} ".format("更新时间", data.market_time))
        
        if data.estimated_nav is not None:
            nav_str = f"{data.estimated_nav:.4f} CNY"
            print("│ {:<20}  {:^54} ".format("估算实时净值", nav_str))
        
        if data.premium_discount is not None:
            pd_str = f"{data.premium_discount:.2f}%"
            print("│ {:<20}  {:^54} ".format("溢价率", pd_str))
        
        if data.latest_nav is not None:
            nav_str = f"{data.latest_nav} CNY"
            if data.latest_nav_date:
                nav_str += f" (日期: {data.latest_nav_date})"
            print("│ {:<20}  {:^54} ".format("最新基金净值", nav_str))
        
        if data.intraday_nav is not None:
            nav_str = f"{data.intraday_nav} USD"
            if data.intraday_nav_time:
                nav_str += f" (时间: {data.intraday_nav_time})"
            print("│ {:<20}  {:^54} ".format("Intraday NAV", nav_str))
        
        if data.historical_nav is not None:
            nav_str = f"{data.historical_nav} USD"
            if data.historical_nav_date:
                nav_str += f" (日期: {data.historical_nav_date})"
            print("│ {:<20}  {:^54} ".format("Historical NAV", nav_str))
        
        if data.common_date_nav is not None:
            nav_str = f"{data.common_date_nav} CNY"
            if data.common_date:
                nav_str += f" (日期: {data.common_date})"
            print("│ {:<20}  {:^54} ".format("共同日期净值", nav_str))
        
        if data.nav_change_pct is not None:
            change_str = f"{data.nav_change_pct:.2f}%"
            print("│ {:<20}  {:^54} ".format("NAV涨跌幅", change_str))
        
        print("└" + "─" * 78 + "")
        
        print(f"\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def save_to_file(self, data: FundData, filename: str = None) -> str:
        """
        保存数据到文件
        
        Args:
            data: 基金数据
            filename: 文件名（可选）
            
        Returns:
            str: 保存的文件路径
        """
        if filename is None:
            today = datetime.now().strftime("%Y-%m-%d")
            filename = f"{self.fund_code}_估值数据_{today}.txt"
        
        filepath = os.path.join(self.get_output_dir(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"{self.fund_code} {self.fund_name} - 估值数据\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"保存时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if data.market_price is not None:
                f.write(f"场内价格: {data.market_price:.3f} CNY\n")
            if data.market_change_pct is not None:
                f.write(f"涨跌幅: {data.market_change_pct:.2f}%\n")
            if data.market_time:
                f.write(f"更新时间: {data.market_time}\n")
            if data.estimated_nav is not None:
                f.write(f"估算净值: {data.estimated_nav:.4f} CNY\n")
            if data.premium_discount is not None:
                f.write(f"溢价率: {data.premium_discount:.2f}%\n")
            if data.latest_nav is not None:
                f.write(f"最新净值: {data.latest_nav} CNY\n")
            if data.latest_nav_date:
                f.write(f"净值日期: {data.latest_nav_date}\n")
            if data.intraday_nav is not None:
                f.write(f"Intraday NAV: {data.intraday_nav} USD\n")
            if data.intraday_nav_time:
                f.write(f"更新时间: {data.intraday_nav_time}\n")
            
            f.write("\n" + "=" * 80 + "\n")
        
        return filepath
