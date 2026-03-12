"""
159687 南方东英富时亚太低碳精选ETF 估值模块
"""

import requests
from datetime import datetime, timedelta
import os
import json
import time
from typing import Optional

from core.base import BaseFund, FundData
from core.nav_history import NavHistoryManager


class Fund159687(BaseFund):
    """
    南方东英富时亚太低碳精选ETF (159687)
    
    估值方法：
    1. 从ICE API获取Intraday NAV (美元)
    2. 从新浪财经获取市场价格 (人民币)
    3. 从akshare获取最新基金净值 (人民币)
    4. 从CSOP官网获取Historical NAV (美元)
    5. 计算NAV涨跌幅和估算实时净值
    """
    
    @property
    def fund_code(self) -> str:
        return "159687"
    
    @property
    def fund_name(self) -> str:
        return "南方东英富时亚太低碳精选ETF"
    
    @property
    def description(self) -> str:
        return "追踪富时亚太低碳指数，投资亚太地区低碳概念股票"
    
    @property
    def update_interval(self) -> int:
        return 30  # 30秒刷新一次
    
    def __init__(self, base_dir: str = None):
        super().__init__(base_dir)
        
        # API URLs
        self.main_url = "https://www.csopasset.com/sg/en/products/sg-carbon/etf.php"
        self.iframe_url = "https://csopasset.factsetdigitalsolutions.com/application/index/quote?s=LCU-SG"
        self.api_url = "https://inav.ice.com/api/1/csop/application/index/quote?symbol=LCU-SG&language=en"
        
        # 缓存文件
        self.cache_dir = self.get_cache_dir()
        self.latest_nav_cache_file = os.path.join(self.cache_dir, "latest_nav_cache.json")
        self.historical_nav_cache_file = os.path.join(self.cache_dir, "historical_nav_cache.json")
        self.intraday_nav_cache_file = os.path.join(self.cache_dir, "intraday_nav_cache.json")
        
        # 净值历史管理器
        self.nav_history = NavHistoryManager(self.cache_dir, self.fund_code)
    
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
        
        # 4. 获取共同日期净值
        common_date_result = self._get_common_date_nav()
        
        # 5. 获取Historical NAV（使用共同日期）
        target_date = common_date_result.get('date') if common_date_result else None
        historical_nav = self._get_historical_nav_by_date(target_date) if target_date else None
        
        # 6. 获取汇率数据
        usd_cny_rate = None
        usd_cny_change_pct = None
        usd_cny_rate_on_common_date = None
        try:
            from core.exchange_rate import get_usd_cny_latest_rate, get_usd_cny_rate_by_date
            
            # 获取最新汇率
            rate_result = get_usd_cny_latest_rate()
            if rate_result.get('success'):
                usd_cny_rate = rate_result.get('rate')
                
                # 如果有共同日期，获取共同日期的汇率，计算汇率涨跌幅
                if common_date_result and common_date_result.get('date'):
                    common_date = common_date_result['date']
                    
                    # common_date 已经是 'YYYY-MM-DD' 格式
                    
                    # 获取共同日期的汇率
                    usd_cny_rate_on_common_date = get_usd_cny_rate_by_date(common_date)
                    
                    if usd_cny_rate_on_common_date and usd_cny_rate:
                        # 计算汇率涨跌幅
                        usd_cny_change_pct = ((usd_cny_rate - usd_cny_rate_on_common_date) / usd_cny_rate_on_common_date) * 100
        except Exception as e:
            print(f"获取美元兑人民币汇率失败: {e}")
        
        # 7. 计算NAV涨跌幅
        nav_change_result = None
        if historical_nav and intraday_result and intraday_result.get('nav_usd'):
            nav_change_result = self._calculate_nav_change(
                historical_nav.get('nav'), 
                intraday_result.get('nav_usd')
            )
        
        # 8. 估算实时净值（考虑汇率因素）
        estimated_nav = None
        premium_discount = None
        if nav_change_result and common_date_result and common_date_result.get('nav'):
            # NAV涨跌幅（美元计价）
            nav_change_pct = nav_change_result['change_pct'] / 100
            
            # 如果有汇率涨跌幅，需要考虑汇率因素
            # 估算实时净值 = 共同日期的A股净值 * (1 + NAV涨跌幅) * (1 + 汇率涨跌幅)
            if usd_cny_change_pct is not None:
                exchange_rate_change = usd_cny_change_pct / 100
                estimated_nav = common_date_result['nav'] * (1 + nav_change_pct) * (1 + exchange_rate_change)
            else:
                estimated_nav = common_date_result['nav'] * (1 + nav_change_pct)
            
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
            nav_change_pct=nav_change_result.get('change_pct') if nav_change_result else None,
            common_date_nav=common_date_result.get('nav') if common_date_result else None,
            common_date=common_date_result.get('date') if common_date_result else None,
            usd_cny_rate=usd_cny_rate,
            usd_cny_change_pct=usd_cny_change_pct,
            usd_cny_rate_on_common_date=usd_cny_rate_on_common_date
        )
    
    def _get_common_date_nav(self) -> Optional[dict]:
        """获取共同日期净值"""
        try:
            # 读取A股历史净值缓存
            a_historical_nav_file = os.path.join(self.cache_dir, "a_historical_nav_cache.json")
            if not os.path.exists(a_historical_nav_file):
                print("A股历史净值缓存文件不存在")
                return None
            
            with open(a_historical_nav_file, 'r', encoding='utf-8') as f:
                a_cache_data = json.load(f)
            a_historical_nav = a_cache_data.get('data', {})
            
            # 检查官网历史净值缓存是否存在，如果不存在则获取
            if not os.path.exists(self.historical_nav_cache_file):
                print("官网历史净值缓存文件不存在，正在获取...")
                # 获取最近15天的日期，尝试获取历史净值
                from datetime import datetime, timedelta
                today = datetime.now()
                for i in range(15):
                    target_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
                    result = self._get_historical_nav_by_date(target_date)
                    if result:
                        break
            
            # 再次检查缓存是否存在
            if not os.path.exists(self.historical_nav_cache_file):
                print("获取官网历史净值失败")
                return None
            
            with open(self.historical_nav_cache_file, 'r', encoding='utf-8') as f:
                official_cache_data = json.load(f)
            
            official_dates = official_cache_data.get('dates', [])
            official_nav_data = official_cache_data.get('nav_data', [])
            
            # 获取最近15日的A股净值日期
            from datetime import datetime, timedelta
            today = datetime.now()
            recent_15_dates = []
            for i in range(15):
                date = today - timedelta(days=i)
                recent_15_dates.append(date.strftime("%Y-%m-%d"))
            
            # 找到两者日期一致的且离现在的日期最近的日期
            for date in recent_15_dates:
                # 检查A股历史净值中是否有该日期
                if date in a_historical_nav:
                    # 检查官网历史净值中是否有该日期
                    # 需要将日期格式转换为官网格式 (YYYY-MM-DD -> DD Mon,YYYY)
                    try:
                        date_obj = datetime.strptime(date, "%Y-%m-%d")
                        official_date_format = date_obj.strftime("%d %b,%Y")
                        
                        if official_date_format in official_dates:
                            idx = official_dates.index(official_date_format)
                            official_nav = official_nav_data[idx]
                            
                            return {
                                'date': date,
                                'nav': a_historical_nav[date],
                                'official_nav': official_nav
                            }
                    except Exception as e:
                        print(f"日期格式转换错误: {e}")
                        continue
            
            print("未找到共同日期的净值数据")
            return None
            
        except Exception as e:
            print(f"获取共同日期净值失败: {e}")
            return None
    
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
                    'nav_usd': None
                }
                
                if 'quote' in data and 'rows' in data['quote'] and len(data['quote']['rows']) > 0:
                    row = data['quote']['rows'][0]
                    result['date'] = row.get('date', None)
                    result['time'] = row.get('time', None)
                    if 'values' in row and len(row['values']) > 1:
                        result['nav_usd'] = float(row['values'][1])
                
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
            
            url = "http://hq.sinajs.cn/list=sz159687"
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
            
            df = ak.fund_etf_fund_info_em(fund='159687')
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
            
            # 保存全部A股历史净值到缓存
            self._save_a_historical_nav(df)
            
            return result
        except Exception as e:
            print(f"获取最新净值失败: {e}")
        
        return None
    
    def _save_a_historical_nav(self, df):
        """保存A股历史净值到缓存"""
        try:
            a_historical_nav = {}
            for _, row in df.iterrows():
                date_str = str(row['净值日期'])
                nav = float(row['单位净值'])
                a_historical_nav[date_str] = nav
            
            cache_data = {
                'cache_date': datetime.now().strftime("%Y-%m-%d"),
                'data': a_historical_nav
            }
            
            a_historical_nav_file = os.path.join(self.cache_dir, "a_historical_nav_cache.json")
            with open(a_historical_nav_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存A股历史净值失败: {e}")
    
    def _get_historical_nav_by_date(self, target_date: str) -> Optional[dict]:
        """获取指定日期的历史净值"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # 首先检查缓存是否存在
            if os.path.exists(self.historical_nav_cache_file):
                with open(self.historical_nav_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                dates = cache_data.get('dates', [])
                nav_data = cache_data.get('nav_data', [])
                
                # 尝试从缓存中查找目标日期
                target_date_obj = None
                try:
                    target_date_obj = datetime.strptime(target_date, "%Y-%m-%d")
                except:
                    pass
                
                for i, date in enumerate(dates):
                    try:
                        date_obj = datetime.strptime(date, "%d %b,%Y")
                        if target_date_obj and date_obj.strftime("%Y-%m-%d") == target_date:
                            nav = nav_data[i] if i < len(nav_data) else None
                            formatted_date = date_obj.strftime("%Y-%m-%d")
                            return {
                                'date': formatted_date,
                                'nav': nav
                            }
                    except:
                        pass
                
                # 如果缓存中有数据但没找到目标日期，返回 None
                print(f"[{self.fund_code}] 缓存中未找到目标日期 {target_date} 的数据")
                return None
            
            # 如果没有缓存，尝试使用浏览器获取（仅在本地环境）
            try:
                from core.base import get_browser_lock
                from DrissionPage import ChromiumPage, ChromiumOptions
                import platform
                
                # 使用浏览器锁保护浏览器操作
                with get_browser_lock():
                    print(f"[{self.fund_code}] 正在获取Historical NAV数据...")
                    
                    # 配置浏览器选项
                    co = ChromiumOptions()
                    
                    # Linux 环境需要特殊配置
                    if platform.system() == 'Linux':
                        co.headless(True)  # 无头模式
                        co.set_argument('--no-sandbox')  # 禁用沙箱
                        co.set_argument('--disable-gpu')  # 禁用 GPU
                        co.set_argument('--disable-dev-shm-usage')  # 禁用 /dev/shm 使用
                    
                    page = ChromiumPage(addr_or_opts=co)
                    page.get(self.main_url)
                    page.wait(3)  # 等待页面完全加载
                    
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
                        
                        cache_data = {
                            'cache_date': today,
                            'dates': dates,
                            'nav_data': nav_data
                        }
                        
                        with open(self.historical_nav_cache_file, 'w', encoding='utf-8') as f:
                            json.dump(cache_data, f, ensure_ascii=False)
                        
                        print(f"[{self.fund_code}] Historical NAV数据已更新")
                        
                        # 再次尝试查找目标日期
                        target_date_obj = None
                        try:
                            target_date_obj = datetime.strptime(target_date, "%Y-%m-%d")
                        except:
                            pass
                        
                        for i, date in enumerate(dates):
                            try:
                                date_obj = datetime.strptime(date, "%d %b,%Y")
                                if target_date_obj and date_obj.strftime("%Y-%m-%d") == target_date:
                                    nav = nav_data[i] if i < len(nav_data) else None
                                    formatted_date = date_obj.strftime("%Y-%m-%d")
                                    return {
                                        'date': formatted_date,
                                        'nav': nav
                                    }
                            except:
                                pass
            except ImportError:
                print(f"[{self.fund_code}] DrissionPage 未安装，跳过浏览器获取")
            except Exception as e:
                print(f"[{self.fund_code}] 浏览器获取失败: {e}")
            
            # 如果未找到匹配日期，返回None
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
