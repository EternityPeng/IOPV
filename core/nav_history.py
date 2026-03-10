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
                    '场内收盘价(CNY)',
                    '收盘估算净值(CNY)',
                    'A股收盘溢价率(%)',
                    '次日5点估算净值(CNY)',
                    '最新基金净值(CNY)',
                    'Historical NAV(USD)',
                    '净值溢价率(%)',
                    '估算误差(%)',
                    '更新时间'
                ])
    
    def _safe_float(self, value) -> Optional[float]:
        """安全转换为浮点数"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _calculate_derived_values(self, market_price: float = None, close_estimated_nav: float = None,
                                   next_day_estimated_nav: float = None, latest_nav: float = None) -> dict:
        """
        计算派生值
        
        Args:
            market_price: 场内收盘价
            close_estimated_nav: 收盘估算净值
            next_day_estimated_nav: 次日5点估算净值
            latest_nav: 最新基金净值
            
        Returns:
            包含计算后值的字典
        """
        result = {
            'a_share_premium': None,
            'nav_premium': None,
            'estimation_error': None
        }
        
        # 计算A股收盘溢价率：(场内收盘价 - 收盘估算净值) / 收盘估算净值 * 100
        if market_price is not None and close_estimated_nav is not None and close_estimated_nav > 0:
            result['a_share_premium'] = round((market_price - close_estimated_nav) / close_estimated_nav * 100, 2)
        
        # 计算净值溢价率：(场内收盘价 - 最新基金净值) / 最新基金净值 * 100
        if market_price is not None and latest_nav is not None and latest_nav > 0:
            result['nav_premium'] = round((market_price - latest_nav) / latest_nav * 100, 2)
        
        # 计算估算误差：(次日5点估算净值 - 最新基金净值) / 最新基金净值 * 100
        if next_day_estimated_nav is not None and latest_nav is not None and latest_nav > 0:
            result['estimation_error'] = round((next_day_estimated_nav - latest_nav) / latest_nav * 100, 2)
        
        return result
    
    def add_record(self, date: str, market_price: float = None, close_estimated_nav: float = None,
                   next_day_estimated_nav: float = None, latest_nav: float = None, historical_nav: float = None):
        """
        添加或更新记录
        
        Args:
            date: 日期 (YYYY-MM-DD)
            market_price: 场内收盘价
            close_estimated_nav: 收盘估算净值
            next_day_estimated_nav: 次日5点估算净值
            latest_nav: 最新基金净值
            historical_nav: Historical NAV (USD)
        """
        # 检查是否已有该日期的记录
        existing_records = self.get_all_records()
        existing_record = None
        for record in existing_records:
            if record['日期'] == date:
                existing_record = record
                break
        
        if existing_record:
            # 合并已有数据和新数据
            existing_market_price = self._safe_float(existing_record.get('场内收盘价(CNY)'))
            existing_close_estimated_nav = self._safe_float(existing_record.get('收盘估算净值(CNY)'))
            existing_next_day_estimated_nav = self._safe_float(existing_record.get('次日5点估算净值(CNY)'))
            existing_latest_nav = self._safe_float(existing_record.get('最新基金净值(CNY)'))
            existing_historical_nav = self._safe_float(existing_record.get('Historical NAV(USD)'))
            
            # 使用新值覆盖旧值（如果新值存在）
            final_market_price = market_price if market_price is not None else existing_market_price
            final_close_estimated_nav = close_estimated_nav if close_estimated_nav is not None else existing_close_estimated_nav
            final_next_day_estimated_nav = next_day_estimated_nav if next_day_estimated_nav is not None else existing_next_day_estimated_nav
            final_latest_nav = latest_nav if latest_nav is not None else existing_latest_nav
            final_historical_nav = historical_nav if historical_nav is not None else existing_historical_nav
            
            # 更新已有记录
            self._update_record(
                date, 
                final_market_price, 
                final_close_estimated_nav, 
                final_next_day_estimated_nav,
                final_latest_nav, 
                final_historical_nav
            )
            return
        
        # 添加新记录
        # 读取现有记录
        records = self.get_all_records()
        
        # 创建新记录
        new_record = {
            '日期': date,
            '场内收盘价(CNY)': f"{market_price:.3f}" if market_price is not None else '',
            '收盘估算净值(CNY)': f"{close_estimated_nav:.4f}" if close_estimated_nav is not None else '',
            'A股收盘溢价率(%)': '',
            '次日5点估算净值(CNY)': f"{next_day_estimated_nav:.4f}" if next_day_estimated_nav is not None else '',
            '最新基金净值(CNY)': f"{latest_nav:.4f}" if latest_nav is not None else '',
            'Historical NAV(USD)': f"{historical_nav:.4f}" if historical_nav is not None else '',
            '净值溢价率(%)': '',
            '估算误差(%)': '',
            '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 插入新记录并按日期降序排列
        records.append(new_record)
        records.sort(key=lambda x: x['日期'], reverse=True)
        
        # 保存前重新计算所有记录的派生值
        self._save_with_recalculation(records)
    
    def _update_record(self, date: str, market_price: float = None, close_estimated_nav: float = None,
                       next_day_estimated_nav: float = None, latest_nav: float = None, historical_nav: float = None):
        """
        更新已有记录
        
        Args:
            date: 日期
            market_price: 场内收盘价
            close_estimated_nav: 收盘估算净值
            next_day_estimated_nav: 次日5点估算净值
            latest_nav: 最新基金净值
            historical_nav: Historical NAV (USD)
        """
        records = self.get_all_records()
        
        # 更新记录
        for record in records:
            if record['日期'] == date:
                record['场内收盘价(CNY)'] = f"{market_price:.3f}" if market_price is not None else ''
                record['收盘估算净值(CNY)'] = f"{close_estimated_nav:.4f}" if close_estimated_nav is not None else ''
                record['次日5点估算净值(CNY)'] = f"{next_day_estimated_nav:.4f}" if next_day_estimated_nav is not None else ''
                record['最新基金净值(CNY)'] = f"{latest_nav:.4f}" if latest_nav is not None else ''
                record['Historical NAV(USD)'] = f"{historical_nav:.4f}" if historical_nav is not None else ''
                record['更新时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                break
        
        # 按日期降序排列
        records.sort(key=lambda x: x['日期'], reverse=True)
        
        # 保存前重新计算所有记录的派生值
        self._save_with_recalculation(records)
    
    def _save_with_recalculation(self, records: List[Dict]):
        """
        保存记录前重新计算所有记录的派生值
        
        Args:
            records: 记录列表
        """
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['日期', '场内收盘价(CNY)', '收盘估算净值(CNY)', 'A股收盘溢价率(%)', 
                           '次日5点估算净值(CNY)', '最新基金净值(CNY)', 'Historical NAV(USD)', 
                           '净值溢价率(%)', '估算误差(%)', '更新时间'])
            
            for record in records:
                market_price = self._safe_float(record.get('场内收盘价(CNY)'))
                close_estimated_nav = self._safe_float(record.get('收盘估算净值(CNY)'))
                next_day_estimated_nav = self._safe_float(record.get('次日5点估算净值(CNY)'))
                latest_nav = self._safe_float(record.get('最新基金净值(CNY)'))
                historical_nav = self._safe_float(record.get('Historical NAV(USD)'))
                
                # 计算派生值
                derived = self._calculate_derived_values(
                    market_price, close_estimated_nav, next_day_estimated_nav, latest_nav
                )
                
                writer.writerow([
                    record['日期'],
                    f"{market_price:.3f}" if market_price is not None else '',
                    f"{close_estimated_nav:.4f}" if close_estimated_nav is not None else '',
                    f"{derived['a_share_premium']:.2f}" if derived['a_share_premium'] is not None else '',
                    f"{next_day_estimated_nav:.4f}" if next_day_estimated_nav is not None else '',
                    f"{latest_nav:.4f}" if latest_nav is not None else '',
                    f"{historical_nav:.4f}" if historical_nav is not None else '',
                    f"{derived['nav_premium']:.2f}" if derived['nav_premium'] is not None else '',
                    f"{derived['estimation_error']:.2f}" if derived['estimation_error'] is not None else '',
                    record.get('更新时间', '')
                ])
    
    def recalculate_all_derived_values(self):
        """
        重新计算所有记录的派生值
        用于修复历史数据中的缺失值
        """
        records = self.get_all_records()
        
        # 按日期降序排列
        records.sort(key=lambda x: x['日期'], reverse=True)
        
        # 保存并重新计算
        self._save_with_recalculation(records)
    
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
        return records[:count] if len(records) >= count else records
