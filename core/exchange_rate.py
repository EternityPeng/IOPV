"""
汇率获取模块
从akshare获取美元兑人民币历史汇率中间价
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd


class USDCNYExchangeRateFetcher:
    """美元兑人民币汇率中间价获取器"""
    
    def __init__(self, cache_dir: str = None):
        """
        初始化
        
        Args:
            cache_dir: 缓存目录
        """
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
        self.cache_dir = cache_dir
        self.history_cache_file = os.path.join(cache_dir, "usd_cny_exchange_rate_history_cache.json")
        
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def fetch_historical_rates(self, force_update: bool = False) -> pd.DataFrame:
        """
        获取美元兑人民币历史汇率
        
        Args:
            force_update: 是否强制更新缓存
        
        Returns:
            包含历史汇率的DataFrame，列为['日期', '汇率']
        """
        # 检查缓存是否有效
        if not force_update and os.path.exists(self.history_cache_file):
            try:
                with open(self.history_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                cache_date = cache_data.get('cache_date', '')
                today = datetime.now().strftime("%Y-%m-%d")
                current_time = datetime.now().time()
                from datetime import time as time_class
                threshold_time = time_class(9, 15, 0)
                
                # 如果缓存是今天的且当前时间大于9:15，直接返回
                # 或者缓存不是今天但当前时间小于9:15（今日中间价还未公布）
                if cache_date == today or (cache_date != today and current_time < threshold_time):
                    df = pd.DataFrame(cache_data.get('data'))
                    return df
            except Exception as e:
                print(f"读取历史汇率缓存失败: {e}")
        
        # 从akshare获取历史汇率
        try:
            import akshare as ak
            
            print("正在从akshare获取美元兑人民币历史汇率...")
            currency_df = ak.currency_boc_safe()
            
            # 提取日期和美元汇率列
            # 美元汇率是以100美元兑换多少人民币为单位，需要除以100
            df = currency_df[['日期', '美元']].copy()
            df.columns = ['日期', '汇率']
            df['汇率'] = df['汇率'] / 100  # 转换为1美元兑换多少人民币
            
            # 保存到缓存
            self._save_history_cache(df)
            
            return df
            
        except Exception as e:
            print(f"获取历史汇率失败: {e}")
            # 尝试从缓存读取
            if os.path.exists(self.history_cache_file):
                try:
                    with open(self.history_cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    df = pd.DataFrame(cache_data.get('data'))
                    return df
                except:
                    pass
            return pd.DataFrame()
    
    def _save_history_cache(self, df: pd.DataFrame):
        """保存历史汇率缓存（只保存最近15天）"""
        try:
            # 只保存最近15天的数据
            df_recent = df.tail(15).copy()
            
            # 将日期转换为字符串格式
            df_recent['日期'] = df_recent['日期'].astype(str)
            
            cache_data = {
                'cache_date': datetime.now().strftime("%Y-%m-%d"),
                'description': '美元兑人民币历史汇率中间价（最近15天）',
                'source': 'akshare - currency_boc_safe',
                'data': df_recent.to_dict('records')
            }
            with open(self.history_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"历史汇率已保存到缓存（最近15天）: {self.history_cache_file}")
        except Exception as e:
            print(f"保存历史汇率缓存失败: {e}")
    
    def get_rate_by_date(self, date: str) -> Optional[float]:
        """
        获取指定日期的汇率
        
        Args:
            date: 日期字符串，格式为YYYY-MM-DD
        
        Returns:
            该日期的汇率，如果不存在则返回None
        """
        df = self.fetch_historical_rates()
        if df.empty:
            return None
        
        # 查找指定日期的汇率
        row = df[df['日期'] == date]
        if not row.empty:
            return float(row.iloc[0]['汇率'])
        
        return None
    
    def get_latest_rate(self) -> Optional[Dict[str, Any]]:
        """
        获取最新的汇率（历史汇率中的最后一条）
        
        Returns:
            包含汇率信息的字典:
            - date: 日期
            - rate: 汇率
            - success: 是否成功
        """
        df = self.fetch_historical_rates()
        if df.empty:
            return {
                'date': None,
                'rate': None,
                'success': False
            }
        
        # 获取最后一条记录
        last_row = df.iloc[-1]
        return {
            'date': str(last_row['日期']),
            'rate': float(last_row['汇率']),
            'success': True
        }


def get_usd_cny_historical_rates(cache_dir: str = None, force_update: bool = False) -> pd.DataFrame:
    """
    获取美元兑人民币历史汇率（便捷函数）
    
    Args:
        cache_dir: 缓存目录
        force_update: 是否强制更新缓存
    
    Returns:
        包含历史汇率的DataFrame
    """
    fetcher = USDCNYExchangeRateFetcher(cache_dir)
    return fetcher.fetch_historical_rates(force_update)


def get_usd_cny_rate_by_date(date: str, cache_dir: str = None) -> Optional[float]:
    """
    获取指定日期的美元兑人民币汇率（便捷函数）
    
    Args:
        date: 日期字符串，格式为YYYY-MM-DD
        cache_dir: 缓存目录
    
    Returns:
        该日期的汇率
    """
    fetcher = USDCNYExchangeRateFetcher(cache_dir)
    return fetcher.get_rate_by_date(date)


def get_usd_cny_latest_rate(cache_dir: str = None) -> Dict[str, Any]:
    """
    获取最新的美元兑人民币汇率（便捷函数）
    
    Args:
        cache_dir: 缓存目录
    
    Returns:
        包含汇率信息的字典
    """
    fetcher = USDCNYExchangeRateFetcher(cache_dir)
    return fetcher.get_latest_rate()


if __name__ == "__main__":
    # 测试
    result = get_usd_cny_latest_rate()
    print(f"美元兑人民币汇率中间价: {result.get('rate')}")
    print(f"日期: {result.get('date')}")
    print(f"成功: {result.get('success')}")
    
    # 测试获取指定日期的汇率
    rate = get_usd_cny_rate_by_date('2026-02-27')
    print(f"\n2026-02-27 汇率: {rate}")
