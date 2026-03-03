"""
513730 南方东英东南亚科技ETF 估值模块

CSOP iEdge Southeast Asia+ TECH Index ETF
跟踪iEdge东南亚科技指数，投资东南亚和新兴亚洲市场最大的30家科技公司
"""

import requests
from datetime import datetime, timedelta
import os
import json
import time
from typing import Optional

from core.base import BaseFund, FundData


class Fund513730(BaseFund):
    """
    南方东英东南亚科技ETF (513730)
    
    估值方法：
    1. 从ICE API获取Intraday NAV (美元/新加坡元)
    2. 从新浪财经获取市场价格 (人民币)
    3. 从akshare获取最新基金净值 (人民币)
    4. 从CSOP官网获取Historical NAV (美元)
    5. 计算NAV涨跌幅和估算实时净值
    """
    
    @property
    def fund_code(self) -> str:
        return "513730"
    
    @property
    def fund_name(self) -> str:
        return "南方东英东南亚科技ETF"
    
    @property
    def description(self) -> str:
        return "跟踪iEdge东南亚科技指数，投资东南亚和新兴亚洲市场最大的30家科技公司"
    
    @property
    def update_interval(self) -> int:
        return 30  # 30秒刷新一次
    
    def __init__(self, base_dir: str = None):
        super().__init__(base_dir)
        
        # API URLs
        self.main_url = "https://www.csopasset.com/sg/en/products/sg-atech/etf.php"
        self.iframe_url = "https://csopasset.factsetdigitalsolutions.com/application/index/quote?s=SQQ-SG"
        self.api_url = "https://inav.ice.com/api/1/csop/application/index/quote?symbol=SQQ-SG&language=en"
        
        # 缓存文件
        self.cache_dir = self.get_cache_dir()
        self.latest_nav_cache_file = os.path.join(self.cache_dir, "latest_nav_cache.json")
        self.historical_nav_cache_file = os.path.join(self.cache_dir, "historical_nav_cache.json")
        self.intraday_nav_cache_file = os.path.join(self.cache_dir, "intraday_nav_cache.json")
    
    def calculate(self) -> FundData:
        """计算估值数据"""
        # 1. 获取实时净值
        intraday_result = self._get_intraday_nav_from_api()
        if intraday_result is None or intraday_result.get('nav_usd') is None:
            intraday_result = self._get_intraday_nav()
        
        # 2. 获取市场价格
        market_price_info = self._get_market_price()
        
        # 3. 获取最新基金净值
        latest_nav = self._get_latest_nav()
        
        # 4. 获取Historical NAV
        target_date = latest_nav.get('date') if latest_nav else None
        historical_nav = self._get_historical_nav_by_date(target_date) if target_date else None
        
        # 5. 计算NAV涨跌幅
        nav_change_result = None
        if historical_nav and intraday_result and intraday_result.get('nav_usd'):
            nav_change_result = self._calculate_nav_change(
                historical_nav.get('nav'), 
                intraday_result.get('nav_usd')
            )
        
        # 6. 估算实时净值
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
    
    def _get_intraday_nav_from_api(self) -> Optional[dict]:
        """从ICE API获取实时净值"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.get(
                    self.api_url, 
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "application/json"
                    },
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                
                result = {
                    'date': None,
                    'time': None,
                    'nav_usd': None,
                    'nav_sgd': None
                }
                
                if 'quote' in data and 'rows' in data['quote'] and len(data['quote']['rows']) > 0:
                    row = data['quote']['rows'][0]
                    result['date'] = row.get('date', None)
                    result['time'] = row.get('time', None)
                    # values[0] 是USD净值, values[1] 是SGD净值
                    if 'values' in row and len(row['values']) > 1:
                        result['nav_usd'] = float(row['values'][0])
                        result['nav_sgd'] = float(row['values'][1])
                
                if result['date'] and result['time']:
                    try:
                        date_obj = datetime.strptime(result['date'], "%d %b %Y")
                        time_obj = datetime.strptime(result['time'], "%I:%M %p")
                        combined_datetime = datetime.combine(date_obj.date(), time_obj.time())
                        result['time'] = combined_datetime.strftime("%Y-%m-%d %H:%M:%S")
                        result['date'] = date_obj.strftime("%d-%b-%Y")
                    except Exception:
                        pass
                
                self._save_intraday_nav_cache(result)
                return result
                
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(2)
                else:
                    print(f"ICE API获取失败: {e}")
                    return None
        
        return None
    
    def _get_intraday_nav(self) -> dict:
        """从iframe页面获取实时净值（备用方法）"""
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
    
    def _get_market_price(self) -> Optional[dict]:
        """获取市场价格"""
        try:
            import re
            
            url = "http://hq.sinajs.cn/list=sh513730"
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
            
            df = ak.fund_etf_fund_info_em(fund='513730')
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
    
    def _get_historical_nav_by_date(self, target_date: str) -> Optional[dict]:
        """获取指定日期的历史净值"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            if os.path.exists(self.historical_nav_cache_file):
                with open(self.historical_nav_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                if cache_data.get('cache_date') == today:
                    dates = cache_data.get('dates', [])
                    nav_data = cache_data.get('nav_data', [])
                else:
                    cache_data = None
            else:
                cache_data = None
            
            if not cache_data:
                from DrissionPage import ChromiumPage
                
                page = ChromiumPage()
                page.get(self.main_url)
                page.wait(2)
                
                # 处理cookie弹窗
                try:
                    agree_btn = page.ele("#StateAccept", timeout=3)
                    if agree_btn:
                        agree_btn.click()
                        page.wait(1)
                except:
                    pass
                
                # 滚动到图表位置
                page.run_js("window.scrollTo(0, 1500)")
                page.wait(1)
                
                # 点击Historical NAVs标签
                historical_tab = page.ele("text:Historical NAVs", timeout=5)
                if historical_tab:
                    historical_tab.click()
                    page.wait(2)
                
                # 从echarts图表提取数据
                chart_data = page.run_js("""
                    var chartDom = document.getElementById('PerformChart');
                    if (chartDom && typeof echarts !== 'undefined') {
                        var chart = echarts.getInstanceByDom(chartDom);
                        if (chart) {
                            var option = chart.getOption();
                            return JSON.stringify(option);
                        }
                    }
                    return null;
                """)
                
                page.quit()
                
                if chart_data:
                    data = json.loads(chart_data)
                    
                    dates = []
                    nav_data = []
                    
                    # 提取日期数据
                    if 'xAxis' in data:
                        for xa in data['xAxis']:
                            if 'data' in xa:
                                dates = xa['data']
                    
                    # 提取净值数据
                    if 'series' in data:
                        for s in data['series']:
                            if 'data' in s and len(s.get('data', [])) > 0:
                                nav_data = s.get('data', [])
                                break
                    
                    # 保存到缓存
                    cache_data = {
                        'cache_date': today,
                        'dates': dates,
                        'nav_data': nav_data
                    }
                    
                    with open(self.historical_nav_cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False)
            
            dates = cache_data.get('dates', [])
            nav_data = cache_data.get('nav_data', [])
            
            # 解析目标日期
            target_date_obj = None
            try:
                target_date_obj = datetime.strptime(target_date, "%Y-%m-%d")
            except:
                pass
            
            # 查找匹配日期的净值
            for i, date in enumerate(dates):
                try:
                    date_obj = datetime.strptime(date, "%d %b,%Y")
                    if target_date_obj and date_obj.strftime("%Y-%m-%d") == target_date:
                        nav = nav_data[i] if i < len(nav_data) else None
                        # 转换日期格式为 YYYY-MM-DD
                        formatted_date = date_obj.strftime("%Y-%m-%d")
                        return {
                            'date': formatted_date,
                            'nav': nav
                        }
                except:
                    pass
            
            # 如果未找到匹配日期，返回最新可用的历史净值
            if dates and nav_data:
                try:
                    date_obj = datetime.strptime(dates[-1], "%d %b,%Y")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                    return {
                        'date': formatted_date,
                        'nav': nav_data[-1]
                    }
                except:
                    return {
                        'date': dates[-1],
                        'nav': nav_data[-1]
                    }
            
            return None
                
        except Exception as e:
            print(f"获取Historical NAV失败: {e}")
            return None
    
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
