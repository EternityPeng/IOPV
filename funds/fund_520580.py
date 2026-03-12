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
        # 1. 获取实时净值
        nav_data = self._get_nav_from_web()
        intraday_result = nav_data.get('intraday')
        
        # 2. 获取市场价格
        market_price_info = self._get_market_price()
        
        # 3. 获取最新基金净值
        latest_nav = self._get_latest_nav()
        
        # 4. 获取共同日期净值（包含A股净值和官网Historical NAV）
        common_date_result = self._get_common_date_nav()
        
        # 5. 获取汇率数据
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
                    
                    # 检查日期格式，如果是 '27-Feb-2026' 格式，需要转换为 '2026-02-27'
                    if '-' in common_date and len(common_date.split('-')[0]) != 4:
                        # 格式为 '27-Feb-2026'
                        from datetime import datetime
                        dt = datetime.strptime(common_date, "%d-%b-%Y")
                        common_date_str = dt.strftime("%Y-%m-%d")
                    else:
                        # 格式已经是 '2026-02-27'
                        common_date_str = common_date
                    
                    # 获取共同日期的汇率
                    usd_cny_rate_on_common_date = get_usd_cny_rate_by_date(common_date_str)
                    
                    if usd_cny_rate_on_common_date and usd_cny_rate:
                        # 计算汇率涨跌幅
                        usd_cny_change_pct = ((usd_cny_rate - usd_cny_rate_on_common_date) / usd_cny_rate_on_common_date) * 100
        except Exception as e:
            print(f"获取美元兑人民币汇率失败: {e}")
        
        # 6. 计算NAV涨跌幅（使用共同日期的Historical NAV）
        nav_change_result = None
        if common_date_result and common_date_result.get('official_nav') and intraday_result and intraday_result.get('nav_usd'):
            nav_change_result = self._calculate_nav_change(
                common_date_result['official_nav'], 
                intraday_result.get('nav_usd')
            )
        
        # 7. 估算实时净值（考虑汇率因素）
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
            historical_nav=common_date_result.get('official_nav') if common_date_result else None,
            historical_nav_date=common_date_result.get('date') if common_date_result else None,
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
                # 触发获取历史净值数据
                nav_data = self._get_nav_from_web()
                if nav_data and nav_data.get('historical'):
                    # 成功获取到数据
                    pass
            
            # 再次检查缓存是否存在
            if not os.path.exists(self.historical_nav_cache_file):
                print("获取官网历史净值失败")
                return None
            
            with open(self.historical_nav_cache_file, 'r', encoding='utf-8') as f:
                official_cache_data = json.load(f)
            
            # 520580的官网历史净值格式为 {'data': {'date': [...], 'nav': [...]}}
            official_data = official_cache_data.get('data', {})
            official_dates = official_data.get('date', [])
            official_navs = official_data.get('nav', [])
            
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
                    # 将日期格式转换为官网格式 (YYYY-MM-DD -> DD-Mon-YY)
                    try:
                        date_obj = datetime.strptime(date, "%Y-%m-%d")
                        official_date_format = date_obj.strftime("%d-%b-%y")
                        
                        # 检查官网历史净值中是否有该日期
                        if official_date_format in official_dates:
                            idx = official_dates.index(official_date_format)
                            official_nav = official_navs[idx] if idx < len(official_navs) else None
                            
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
    
    def _get_fund_security_id(self) -> Optional[str]:
        """从网页获取fundSecurityId"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(self.main_url, headers=headers, timeout=30)
            
            # 搜索fundSecurityId
            import re
            match = re.search(r'meta\s+property=["\']og:fundSecurityId["\']\s+content=["\']([^"\']+)["\']', response.text, re.IGNORECASE)
            if match:
                return match.group(1)
            
            # 尝试另一种格式
            match = re.search(r'content=["\']([^"\']+)["\']\s+property=["\']og:fundSecurityId["\']', response.text, re.IGNORECASE)
            if match:
                return match.group(1)
            
            print("未找到fundSecurityId")
            return None
            
        except Exception as e:
            print(f"获取fundSecurityId失败: {e}")
            return None
    
    def _get_nav_from_web(self) -> dict:
        """从Lion Global Investors网页获取Intraday NAV和Historical NAV"""
        result = {
            'intraday': None,
            'historical': None
        }
        
        # Historical NAV：检查缓存是否存在且创建日期是今日
        today = datetime.now().strftime("%Y-%m-%d")
        cached_historical = None
        need_fetch_historical = True
        
        if os.path.exists(self.historical_nav_cache_file):
            try:
                with open(self.historical_nav_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                cache_date = cache_data.get('cache_date', '')
                if cache_date == today:
                    cached_historical = cache_data.get('data')
                    result['historical'] = cached_historical
                    # print(f"使用今日缓存的Historical NAV数据 (缓存日期: {cache_date})")
                    need_fetch_historical = False
                else:
                    print(f"Historical NAV缓存日期({cache_date})不是今日，需要重新获取")
            except Exception as e:
                print(f"读取Historical NAV缓存失败: {e}")
        else:
            print("Historical NAV缓存不存在，需要获取")
        
        # Intraday NAV需要实时爬取
        try:
            # print("正在从Lion Global Investors API获取Intraday NAV数据...")
            
            # 首先获取fundSecurityId
            fund_security_id = self._get_fund_security_id()
            if fund_security_id:
                # 调用API获取Intraday NAV
                api_url = f"https://api.lionglobalinvestors.com/markitapi?fundSecurityId={fund_security_id}&format=2"
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                
                api_response = requests.get(api_url, headers=headers, timeout=30)
                if api_response.status_code == 200:
                    api_data = api_response.json()
                    
                    # 解析API数据
                    intraday_result = {
                        'date': None,
                        'time': None,
                        'nav_usd': None,
                        'nav_sgd': None
                    }
                    
                    # 获取SGD数据
                    if 'SGD' in api_data:
                        sgd_data = api_data['SGD']
                        intraday_result['nav_sgd'] = sgd_data.get('values')
                        if sgd_data.get('timeStamp'):
                            try:
                                dt = datetime.fromisoformat(sgd_data['timeStamp'].replace('Z', '+00:00'))
                                intraday_result['time'] = dt.strftime("%Y-%m-%d %H:%M:%S")
                                intraday_result['date'] = dt.strftime("%d-%b-%Y")
                            except:
                                pass
                    
                    # 获取USD数据
                    if 'USD' in api_data:
                        usd_data = api_data['USD']
                        intraday_result['nav_usd'] = usd_data.get('values')
                    
                    # 保存Intraday NAV到缓存
                    if intraday_result.get('nav_usd'):
                        self._save_intraday_nav_cache(intraday_result)
                        result['intraday'] = intraday_result
                        # print(f"Intraday NAV已获取: {intraday_result}")
                else:
                    print(f"API请求失败: {api_response.status_code}")
                    # 如果API获取失败，使用浏览器获取
                    result = self._get_nav_from_browser(result, need_fetch_historical, today)
            else:
                print("未找到fundSecurityId，使用浏览器获取数据")
                # 如果API获取失败，使用浏览器获取
                result = self._get_nav_from_browser(result, need_fetch_historical, today)
            
            # 如果需要获取Historical NAV，则从网页获取
            if need_fetch_historical and not result.get('historical'):
                result = self._fetch_historical_nav_from_browser(result, today)
            
        except Exception as e:
            print(f"获取NAV数据失败: {e}")
            # Intraday NAV获取失败时，使用缓存作为备用
            if not result['intraday']:
                result['intraday'] = self._get_cached_intraday_nav()
            # Historical NAV获取失败时，使用缓存
            if not result['historical']:
                result['historical'] = cached_historical
        
        # print(f"返回结果: Intraday={result['intraday'] is not None}, Historical={result['historical'] is not None}")
        return result
    
    def _get_nav_from_browser(self, result: dict, need_fetch_historical: bool, today: str) -> dict:
        """使用浏览器获取NAV数据"""
        try:
            from core.base import get_browser_lock
            from DrissionPage import ChromiumPage
            import time
            
            # 使用浏览器锁保护浏览器操作
            with get_browser_lock():
                print(f"[{self.fund_code}] 正在使用浏览器获取NAV数据...")
                
                page = ChromiumPage()
                print("浏览器已启动")
                print("正在加载网页...")
                page.get(self.main_url, timeout=60)
                print("网页已加载，等待数据加载...")
                time.sleep(3)  # 等待3秒让数据加载
                print("数据加载完成")
                
                # 解析Intraday NAV
                intraday_result = {
                    'date': None,
                    'time': None,
                    'nav_usd': None,
                    'nav_sgd': None
                }
                
                # 使用XPath获取数据容器
                data_container = page.ele('xpath:/html/body/div[1]/div[1]/div[3]/div/div[3]', timeout=5)
                if data_container:
                    container_text = data_container.text
                    print("数据容器已找到")
                    
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
                        print(f"Intraday NAV已解析: {intraday_result}")
                        
                        try:
                            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                            intraday_result['time'] = dt.strftime("%Y-%m-%d %H:%M:%S")
                            intraday_result['date'] = dt.strftime("%d-%b-%Y")
                        except:
                            pass
                
                # 保存Intraday NAV到缓存
                if intraday_result.get('nav_usd'):
                    self._save_intraday_nav_cache(intraday_result)
                    result['intraday'] = intraday_result
                
                page.quit()
                print("浏览器已关闭")
            
        except Exception as e:
            print(f"浏览器获取NAV数据失败: {e}")
        
        return result
    
    def _fetch_historical_nav_from_browser(self, result: dict, today: str) -> dict:
        """使用浏览器获取Historical NAV数据"""
        # 首先检查缓存
        if os.path.exists(self.historical_nav_cache_file):
            try:
                with open(self.historical_nav_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                data = cache_data.get('data', {})
                dates = data.get('date', [])
                navs = data.get('nav', [])
                
                if dates and navs:
                    result['historical'] = {
                        'date': dates[0],
                        'nav': navs[0]
                    }
                    print(f"[{self.fund_code}] 使用缓存的Historical NAV数据")
                    return result
            except Exception as e:
                print(f"[{self.fund_code}] 读取缓存失败: {e}")
        
        # 如果没有缓存，尝试使用浏览器获取（仅在本地环境）
        try:
            from core.base import get_browser_lock
            from DrissionPage import ChromiumPage
            
            # 使用浏览器锁保护浏览器操作
            with get_browser_lock():
                print(f"[{self.fund_code}] 正在使用浏览器获取Historical NAV...")
                
                page = ChromiumPage()
                print("浏览器已启动，正在获取Historical NAV...")
                page.get(self.main_url, timeout=60)
                
                # 点击同意cookie按钮
                try:
                    agree_btn = page.ele('xpath:/html/body/div[1]/div[1]/div[10]/div/div/div[3]/div[2]/a[1]', timeout=5)
                    if agree_btn:
                        agree_btn.click()
                        page.wait(1)
                        print("已点击同意cookie按钮")
                except Exception as e:
                    print(f"点击同意cookie按钮失败: {e}")
                
                # 点击Historical NAVs按钮
                try:
                    historical_btn = page.ele('xpath:/html/body/div[1]/div[1]/div[4]/div[1]/div/div[1]/div[9]/div[2]/ul/li[2]/button', timeout=5)
                    if historical_btn:
                        historical_btn.click()
                        page.wait(2)
                        print("已点击Historical NAVs按钮")
                except Exception as e:
                    print(f"点击Historical NAVs按钮失败: {e}")
                
                # 解析Historical NAV表格
                historical_result = {
                    'date': None,
                    'nav': None
                }
                
                historical_nav_list = {
                    'date': [],
                    'nav': []
                }
                
                try:
                    # 使用表格ID来定位
                    table = page.ele('#dtHistoricalPricing', timeout=5)
                    if table:
                        print("Historical NAV表格已找到")
                        tbody = table.ele('tag:tbody')
                        if tbody:
                            rows = tbody.eles('tag:tr')
                            for row in rows:
                                cells = row.eles('tag:td')
                                if len(cells) >= 2:
                                    # 第一列是NAV Price，第二列是Date
                                    nav_str = cells[0].text.strip()
                                    date_str = cells[1].text.strip()
                                    
                                    # 跳过表头行
                                    if nav_str == 'NAV Price' or date_str == 'Date':
                                        continue
                                    
                                    try:
                                        nav_value = float(nav_str)
                                        historical_nav_list['date'].append(date_str)
                                        historical_nav_list['nav'].append(nav_value)
                                    except:
                                        pass
                            
                            if historical_nav_list['date']:
                                historical_result['date'] = historical_nav_list['date'][0]
                                historical_result['nav'] = historical_nav_list['nav'][0]
                                print(f"成功获取Historical NAV数据: {len(historical_nav_list['date'])}条记录")
                except Exception as e:
                    print(f"解析Historical NAV表格失败: {e}")
                
                # 保存Historical NAV到缓存
                if historical_result.get('nav'):
                    cache_data = {
                        'cache_date': today,
                        'data': historical_nav_list
                    }
                    with open(self.historical_nav_cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                    result['historical'] = historical_result
                
                page.quit()
                print("浏览器已关闭")
            
        except ImportError:
            print(f"[{self.fund_code}] DrissionPage 未安装，跳过浏览器获取")
        except Exception as e:
            print(f"浏览器获取Historical NAV数据失败: {e}")
        
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
            
            # 使用 .item() 方法获取标量值，避免 NaN 问题
            nav_value = latest_row['单位净值']
            date_value = latest_row['净值日期']
            
            # 检查是否为 NaN
            import pandas as pd
            if pd.isna(nav_value) or pd.isna(date_value):
                print(f"获取到的数据无效: nav={nav_value}, date={date_value}")
                return None
            
            result = {
                'nav': float(nav_value),
                'date': str(date_value)
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
            import pandas as pd
            
            a_historical_nav = {}
            for _, row in df.iterrows():
                date_str = str(row['净值日期'])
                nav = row['单位净值']
                
                # 检查是否为 NaN
                if pd.isna(date_str) or pd.isna(nav) or date_str == 'nan' or date_str == 'NaT':
                    continue
                
                a_historical_nav[date_str] = float(nav)
            
            cache_data = {
                'cache_date': datetime.now().strftime("%Y-%m-%d"),
                'data': a_historical_nav
            }
            
            a_historical_nav_file = os.path.join(self.cache_dir, "a_historical_nav_cache.json")
            with open(a_historical_nav_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存A股历史净值失败: {e}")
