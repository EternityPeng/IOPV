"""
基金净值历史数据管理模块
用于维护基金净值历史记录，支持CSV格式存储
"""

import os
import csv
from datetime import datetime
from typing import Optional, List, Dict


class NavHistoryManager:
    """基金净值历史数据管理器"""
    
    def __init__(self, cache_dir: str, fund_code: str):
        """
        初始化管理器
        
        Args:
            cache_dir: 缓存目录
            fund_code: 基金代码
        """
        self.cache_dir = cache_dir
        self.fund_code = fund_code
        self.csv_file = os.path.join(cache_dir, "nav_history.csv")
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """确保CSV文件存在"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '日期',
                    '场内价格(CNY)',
                    '估算实时净值(CNY)',
                    '最新基金净值(CNY)',
                    'Historical NAV(USD)',
                    'A股收盘溢价率(%)',
                    '净值溢价率(%)',
                    '估算误差(%)',
                    '更新时间'
                ])
    
    def add_record(self, date: str, market_price: float = None, estimated_nav: float = None,
                   latest_nav: float = None, historical_nav: float = None, 
                   a_share_premium: float = None, nav_premium: float = None,
                   estimation_error: float = None):
        """
        添加或更新记录
        
        Args:
            date: 日期 (YYYY-MM-DD)
            market_price: 场内价格
            estimated_nav: 估算实时净值
            latest_nav: 最新基金净值
            historical_nav: Historical NAV (USD)
            a_share_premium: A股收盘溢价率
            nav_premium: 净值溢价率
            estimation_error: 估算误差
        """
        # 检查是否已有该日期的记录
        existing_records = self.get_all_records()
        for record in existing_records:
            if record['日期'] == date:
                # 更新已有记录
                self._update_record(date, market_price, estimated_nav, latest_nav, 
                                   historical_nav, a_share_premium, nav_premium,
                                   estimation_error)
                return
        
        # 添加新记录
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                date,
                f"{market_price:.3f}" if market_price else '',
                f"{estimated_nav:.4f}" if estimated_nav else '',
                f"{latest_nav:.4f}" if latest_nav else '',
                f"{historical_nav:.4f}" if historical_nav else '',
                f"{a_share_premium:.2f}" if a_share_premium is not None else '',
                f"{nav_premium:.2f}" if nav_premium is not None else '',
                f"{estimation_error:.2f}" if estimation_error is not None else '',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    def _update_record(self, date: str, market_price: float = None, estimated_nav: float = None,
                       latest_nav: float = None, historical_nav: float = None, 
                       a_share_premium: float = None, nav_premium: float = None,
                       estimation_error: float = None):
        """
        更新已有记录
        
        Args:
            date: 日期
            market_price: 场内价格
            estimated_nav: 估算实时净值
            latest_nav: 最新基金净值
            historical_nav: Historical NAV (USD)
            a_share_premium: A股收盘溢价率
            nav_premium: 净值溢价率
            estimation_error: 估算误差
        """
        records = self.get_all_records()
        
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['日期', '场内价格(CNY)', '估算实时净值(CNY)', '最新基金净值(CNY)', 
                           'Historical NAV(USD)', 'A股收盘溢价率(%)', '净值溢价率(%)', 
                           '估算误差(%)', '更新时间'])
            
            for record in records:
                if record['日期'] == date:
                    # 更新非空字段
                    new_market_price = f"{market_price:.3f}" if market_price else record.get('场内价格(CNY)', '')
                    new_estimated_nav = f"{estimated_nav:.4f}" if estimated_nav else record.get('估算实时净值(CNY)', '')
                    new_latest_nav = f"{latest_nav:.4f}" if latest_nav else record.get('最新基金净值(CNY)', '')
                    new_historical_nav = f"{historical_nav:.4f}" if historical_nav else record.get('Historical NAV(USD)', '')
                    new_a_share_premium = f"{a_share_premium:.2f}" if a_share_premium is not None else record.get('A股收盘溢价率(%)', '')
                    new_nav_premium = f"{nav_premium:.2f}" if nav_premium is not None else record.get('净值溢价率(%)', '')
                    new_estimation_error = f"{estimation_error:.2f}" if estimation_error is not None else record.get('估算误差(%)', '')
                    
                    writer.writerow([
                        date,
                        new_market_price,
                        new_estimated_nav,
                        new_latest_nav,
                        new_historical_nav,
                        new_a_share_premium,
                        new_nav_premium,
                        new_estimation_error,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ])
                else:
                    writer.writerow([
                        record['日期'],
                        record.get('场内价格(CNY)', ''),
                        record.get('估算实时净值(CNY)', ''),
                        record.get('最新基金净值(CNY)', ''),
                        record.get('Historical NAV(USD)', ''),
                        record.get('A股收盘溢价率(%)', ''),
                        record.get('净值溢价率(%)', ''),
                        record.get('估算误差(%)', ''),
                        record.get('更新时间', '')
                    ])
    
    def get_all_records(self) -> List[Dict]:
        """
        获取所有记录
        
        Returns:
            List[Dict]: 记录列表
        """
        records = []
        
        if not os.path.exists(self.csv_file):
            return records
        
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        
        return records
    
    def get_record_by_date(self, date: str) -> Optional[Dict]:
        """
        获取指定日期的记录
        
        Args:
            date: 日期 (YYYY-MM-DD)
            
        Returns:
            Optional[Dict]: 记录字典，如果不存在返回None
        """
        records = self.get_all_records()
        for record in records:
            if record['日期'] == date:
                return record
        return None
    
    def get_latest_records(self, count: int = 10) -> List[Dict]:
        """
        获取最近的N条记录
        
        Args:
            count: 记录数量
            
        Returns:
            List[Dict]: 记录列表
        """
        records = self.get_all_records()
        return records[-count:] if len(records) >= count else records
