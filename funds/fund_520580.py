"""
520580 新兴亚洲ETF 估值模块

Lion-China Merchants Emerging Asia Select Index ETF
跟踪iEdge Emerging Asia Select 50 Index，投资新兴亚洲市场
"""

import requests
from datetime import datetime
import os
import json
import time
from typing import Optional
import re

from core.base import BaseFund, FundData
from core.nav_history import NavHistoryManager


class Fund520580(BaseFund):
    """
    新兴亚洲ETF (520580)
    
    估值方法：
    1. 从Lion Global Investors网页获取Intraday Indicative NAV (美元/新加坡元)
    2. 从Lion Global Investors网页获取Historical NAV (美元)
    3. 从新浪财经获取市场价格 (人民币)
    4. 从akshare获取最新基金净值 (人民币)
    5. 计算NAV涨跌幅和估算实时净值
    """
    
    @property
    def fund_code(self) -> str:
        return "520580"
    
    @property
    def fund_name(self) -> str:
        return "新兴亚洲ETF"
    
    @property
    def description(self) -> str:
        return "跟踪iEdge Emerging Asia Select 50 Index，投资新兴亚洲市场50只精选股票"
    
    @property
    def update_interval(self) -> int:
        return 30  # 30秒刷新一次
    
    def __init__(self, base_dir: str = None):
        super().__init__(base_dir)
        
        # API URLs
        self.main_url = "https://www.lionglobalinvestors.com/en/fund-lion-china-merchants-emerging-asia-select-index-etf.html"
        
        # 缓存文件
        self.cache_dir = self.get_cache_dir()
        self.latest_nav_cache_file = os.path.join(self.cache_dir, "latest_nav_cache.json")
        self.historical_nav_cache_file = os.path.join(self.cache_dir, "historical_nav_cache.json")
        self.intraday_nav_cache_file = os.path.join(self.cache_dir, "intraday_nav_cache.json")
        
        # 净值历史管理器
        self.nav_history = NavHistoryManager(self.cache_dir, self.fund_code)
    
    def calculate(self) -> FundData:
        """计算估值数据"""
        # 1. 获取实时净值和历史净值（一起获取，减少网页访问）
        nav_data = self._get_nav_from_web()
        intraday_result = nav_data.get('intraday')
        historical_nav = nav_data.get('historical')
        
        # 2. 获取市场价格
        market_price_info = self._get_market_price()
        
        # 3. 获取最新基金净值
        latest_nav = self._get_latest_nav()
        
        # 4. 计算NAV涨跌幅
        nav_change_result = None
        if historical_nav and intraday_result and intraday_result.get('nav_usd'):
            nav_change_result = self._calculate_nav_change(
                historical_nav.get('nav'), 
                intraday_result.get('nav_usd')
            )
        
        # 5. 估算实时净值
        estimated_nav = None
        premium_discount = None
        if nav_change_result and latest_nav and latest_nav.get('nav'):
            estimated_nav = latest_nav['nav'] * (1 + nav_change_result['change_pct'] / 100)
            if market_price_info and market_price_info.get('price'):
                premium_discount = ((market_price_info['price'] - estimated_nav) / estimated_nav) * 100
        
        # 构建返回数据
        return FundData(
            fund_code=self.fund_code,
            fund_name=self.fund_name,
            market_price=market_price_info.get('price') if market_price_info else None,
            market_change_pct=market_price_info.get('change_pct') if market_price_info else None,
            market_time=market_price_info.get('time') if market_price_info else None,
            estimated_nav=estimated_nav,
            premium_discount=premium_discount,
            latest_nav=latest_nav.get('nav') if latest_nav else None,
            latest_nav_date=latest_nav.get('date') if latest_nav else None,
            intraday_nav=intraday_result.get('nav_usd') if intraday_result else None,
            intraday_nav_time=intraday_result.get('time') if intraday_result else None,
            historical_nav=historical_nav.get('nav') if historical_nav else None,
            historical_nav_date=historical_nav.get('date') if historical_nav else None,
            nav_change_pct=nav_change_result.get('change_pct') if nav_change_result else None
        )
    
    def _get_nav_from_web(self) -> dict:
        """从Lion Global Investors网页获取Intraday NAV和Historical NAV"""
        result = {
            'intraday': None,
            'historical': None
        }
        
        # 先尝试使用requests快速获取
        try:
            print("正在从Lion Global Investors获取NAV数据...")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            response = requests.get(self.main_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            html_content = response.text
            
            # 解析Intraday NAV
            intraday_result = {
                'date': None,
                'time': None,
                'nav_usd': None,
                'nav_sgd': None
            }
            
            # 查找Intraday Indicative NAV
            intraday_match = re.search(
                r'IntraDay Indicative NAV\s+as of\s+([\d-]+),\s+([\d:]+)\s+SGD\s+([\d.]+)\s+\*+\s+USD\s+([\d.]+)',
                html_content,
                re.IGNORECASE | re.DOTALL
            )
            if intraday_match:
                date_str = intraday_match.group(1)
                time_str = intraday_match.group(2)
                intraday_result['nav_sgd'] = float(intraday_match.group(3))
                intraday_result['nav_usd'] = float(intraday_match.group(4))
                
                try:
                    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                    intraday_result['time'] = dt.strftime("%Y-%m-%d %H:%M:%S")
                    intraday_result['date'] = dt.strftime("%d-%b-%Y")
                except:
                    pass
            
            # 解析Historical NAV
            historical_result = {
                'date': None,
                'nav': None
            }
            
            # 查找NAV
            nav_match = re.search(
                r'NAV\s+as of\s+([\d-]+)\s+USD\s+([\d.]+)',
                html_content,
                re.IGNORECASE | re.DOTALL
            )
            if nav_match:
                historical_result['date'] = nav_match.group(1)
                historical_result['nav'] = float(nav_match.group(2))
            
            # 如果成功获取数据，保存并返回
            if intraday_result.get('nav_usd') and historical_result.get('nav'):
                # 保存到缓存
                self._save_intraday_nav_cache(intraday_result)
                result['intraday'] = intraday_result
                
                today = datetime.now().strftime("%Y-%m-%d")
                cache_data = {
                    'cache_date': today,
                    'data': historical_result
                }
                with open(self.historical_nav_cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                result['historical'] = historical_result
                
                return result
            
        except Exception as e:
            print(f"requests获取失败: {e}")
        
        # 如果requests失败，使用DrissionPage
        try:
            print("使用浏览器获取数据...")
            
            from DrissionPage import ChromiumPage
            from DrissionPage import ChromiumOptions
            
            # 使用无头模式加快速度
            co = ChromiumOptions()
            co.headless()  # 无头模式
            co.no_imgs(True)  # 不加载图片
            co.incognito(True)  # 无痕模式
            
            page = ChromiumPage(co)
            page.get(self.main_url)
            page.wait(3)  # 减少等待时间
            
            # 使用XPath获取数据容器
            data_container = page.ele('xpath:/html/body/div[1]/div[1]/div[3]/div/div[3]', timeout=5)
            if data_container:
                container_text = data_container.text
                
                # 解析Intraday NAV
                intraday_result = {
                    'date': None,
                    'time': None,
                    'nav_usd': None,
                    'nav_sgd': None
                }
                
                intraday_match = re.search(
                    r'IntraDay Indicative NAV\s+as of\s+([\d-]+),\s+([\d:]+)\s+SGD\s+([\d.]+)\s+\*+\s+USD\s+([\d.]+)',
                    container_text,
                    re.IGNORECASE
                )
                if intraday_match:
                    date_str = intraday_match.group(1)
                    time_str = intraday_match.group(2)
                    intraday_result['nav_sgd'] = float(intraday_match.group(3))
                    intraday_result['nav_usd'] = float(intraday_match.group(4))
                    
                    try:
                        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                        intraday_result['time'] = dt.strftime("%Y-%m-%d %H:%M:%S")
                        intraday_result['date'] = dt.strftime("%d-%b-%Y")
                    except:
                        pass
                
                # 解析Historical NAV
                historical_result = {
                    'date': None,
                    'nav': None
                }
                
                nav_match = re.search(
                    r'NAV\s+as of\s+([\d-]+)\s+USD\s+([\d.]+)',
                    container_text,
                    re.IGNORECASE
                )
                if nav_match:
                    historical_result['date'] = nav_match.group(1)
                    historical_result['nav'] = float(nav_match.group(2))
                
                # 保存到缓存
                if intraday_result.get('nav_usd'):
                    self._save_intraday_nav_cache(intraday_result)
                    result['intraday'] = intraday_result
                
                if historical_result.get('nav'):
                    today = datetime.now().strftime("%Y-%m-%d")
                    cache_data = {
                        'cache_date': today,
                        'data': historical_result
                    }
                    with open(self.historical_nav_cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                    result['historical'] = historical_result
            
            page.quit()
            
        except Exception as e:
            print(f"浏览器获取失败: {e}")
            
            # 使用缓存数据
            result['intraday'] = self._get_cached_intraday_nav()
            result['historical'] = self._get_cached_historical_nav()
        
        return result
    
    def _get_cached_intraday_nav(self) -> dict:
        """从缓存获取Intraday NAV"""
        try:
            if os.path.exists(self.intraday_nav_cache_file):
                with open(self.intraday_nav_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                today = datetime.now().strftime("%Y-%m-%d")
                if cache_data.get('cache_date') == today:
                    return cache_data.get('data')
        except Exception:
            pass
        
        return {'date': 'N/A', 'time': 'N/A', 'nav_usd': None}
    
    def _get_cached_historical_nav(self) -> Optional[dict]:
        """从缓存获取Historical NAV"""
        try:
            if os.path.exists(self.historical_nav_cache_file):
                with open(self.historical_nav_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                return cache_data.get('data')
        except Exception:
            pass
        
        return None
    
    def _save_intraday_nav_cache(self, data: dict):
        """保存实时净值缓存"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            cache_data = {
                'cache_date': today,
                'data': data
            }
            with open(self.intraday_nav_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def _calculate_nav_change(self, historical_nav: float, intraday_nav: float) -> Optional[dict]:
        """计算NAV涨跌幅"""
        if historical_nav and intraday_nav and historical_nav > 0:
            change = intraday_nav - historical_nav
            change_pct = (change / historical_nav) * 100
            return {
                'change': change,
                'change_pct': change_pct
            }
        return None
    
    def _get_market_price(self) -> Optional[dict]:
        """获取市场价格"""
        try:
            url = "http://hq.sinajs.cn/list=sh520580"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://finance.sina.com.cn/"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            match = re.search(r'="([^"]*)"', response.text)
            if match:
                data = match.group(1).split(',')
                if len(data) >= 32:
                    price = float(data[3]) if data[3] else float(data[2])
                    prev_close = float(data[2]) if data[2] else None
                    date = data[30] if len(data) > 30 else None
                    time_str = data[31] if len(data) > 31 else None
                    
                    update_time = f"{date} {time_str}" if date and time_str else None
                    
                    change_pct = None
                    if prev_close and prev_close > 0 and price:
                        change_pct = ((price - prev_close) / prev_close) * 100
                    
                    return {
                        'price': price,
                        'time': update_time,
                        'change_pct': change_pct
                    }
        except Exception as e:
            print(f"获取市场价格失败: {e}")
        
        return None
    
    def _get_latest_nav(self) -> Optional[dict]:
        """获取最新基金净值"""
        try:
            import akshare as ak
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            if os.path.exists(self.latest_nav_cache_file):
                with open(self.latest_nav_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                if cache_data.get('cache_date') == today:
                    return cache_data.get('data')
            
            df = ak.fund_etf_fund_info_em(fund='520580')
            latest_row = df.iloc[-1]
            
            result = {
                'nav': float(latest_row['单位净值']),
                'date': str(latest_row['净值日期'])
            }
            
            cache_data = {
                'cache_date': today,
                'data': result
            }
            with open(self.latest_nav_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            return result
        except Exception as e:
            print(f"获取最新净值失败: {e}")
        
        return None
