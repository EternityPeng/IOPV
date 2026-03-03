"""
159687 ETF 实时估值计算模块

本模块用于计算ETF 159687（南方东英银河-联昌富时亚太低碳精选ETF）的实时估值和溢价/折价率。

主要功能：
1. 获取实时净值（Intraday NAV）
2. 获取市场价格
3. 获取最新基金净值
4. 获取历史净值数据
5. 计算NAV涨跌幅
6. 估算实时净值
7. 计算溢价/折价率

数据来源：
- 实时净值：CSOP官网的iframe页面
- 市场价格：新浪财经API
- 最新基金净值：akshare库
- 历史净值：CSOP官网的echarts图表数据
"""

import requests
from lxml import etree
import akshare as ak
from datetime import datetime, timedelta
import time
import json
import os
import warnings
warnings.filterwarnings('ignore')


class IOPVCalculator:
    """
    ETF 159687 实时估值计算器
    
    该类封装了所有与估值计算相关的方法，包括数据获取、计算和输出功能。
    
    属性:
        url (str): CSOP官网主页URL
        iframe_url (str): 包含实时净值数据的iframe页面URL
        latest_nav_cache_file (str): 最新基金净值缓存文件路径
        historical_nav_cache_file (str): 历史净值缓存文件路径
    
    使用示例:
        >>> calculator = IOPVCalculator()
        >>> calculator.run()  # 运行完整计算流程
    """
    
    def __init__(self):
        """
        初始化估值计算器
        
        设置必要的URL和缓存文件路径。
        """
        self.url = "https://www.csopasset.com/sg/en/products/sg-carbon/etf.php"
        self.iframe_url = "https://csopasset.factsetdigitalsolutions.com/application/index/quote?s=LCU-SG"
        self.api_url = "https://inav.ice.com/api/1/csop/application/index/quote?symbol=LCU-SG&language=en"
        self.latest_nav_cache_file = "latest_nav_cache.json"
        self.historical_nav_cache_file = "historical_nav_cache.json"
        self.intraday_nav_cache_file = "intraday_nav_cache.json"
    
    def get_intraday_nav(self):
        """
        获取实时净值（Intraday NAV）
        
        从CSOP官网的iframe页面获取实时净值数据。该数据以美元计价，
        通常在交易日内实时更新。
        
        返回:
            dict: 包含以下键的字典:
                - date (str): 日期，格式为 "DD-Mon-YYYY"（如 "26-Feb-2026"）
                - time (str): 时间，格式为 "YYYY-MM-DD HH:MM:SS"（如 "2026-02-26 16:59:00"）
                - nav_usd (float): 实时净值（美元）
                
                如果获取失败，返回:
                - date: 'N/A'
                - time: 'N/A'
                - nav_usd: None
        
        注意:
            - 时间格式会自动转换为与场内价格一致的格式
            - 支持AM/PM格式和24小时制格式的转换
            - 包含重试机制，最多重试3次
        
        使用示例:
            >>> calculator = IOPVCalculator()
            >>> result = calculator.get_intraday_nav()
            >>> print(result)
            {'date': '26-Feb-2026', 'time': '2026-02-26 16:59:00', 'nav_usd': 2.038}
        """
        max_retries = 3
        retry_count = 0
        
        # 创建session来维持状态
        session = requests.Session()
        
        # 完整的浏览器headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "iframe",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        
        # 先访问主页面获取cookies
        try:
            print("正在访问主页面获取cookies...")
            main_response = session.get(
                self.url,
                headers=headers,
                timeout=30
            )
            main_response.raise_for_status()
            print("主页面访问成功")
        except Exception as e:
            print(f"访问主页面失败: {e}")
            return self._get_cached_intraday_nav()
        
        while retry_count < max_retries:
            try:
                # 添加Referer和更新headers
                iframe_headers = headers.copy()
                iframe_headers["Referer"] = self.url
                
                response = session.get(
                    self.iframe_url, 
                    headers=iframe_headers,
                    timeout=30,
                    verify=True
                )
                response.raise_for_status()
                break
            except requests.exceptions.SSLError as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"SSL连接错误，正在重试 ({retry_count}/{max_retries})...")
                    time.sleep(2)
                else:
                    print(f"SSL连接错误，已达到最大重试次数: {e}")
                    # 尝试使用缓存数据
                    return self._get_cached_intraday_nav()
            except requests.exceptions.Timeout as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"请求超时，正在重试 ({retry_count}/{max_retries})...")
                    time.sleep(2)
                else:
                    print(f"请求超时，已达到最大重试次数: {e}")
                    return self._get_cached_intraday_nav()
            except requests.exceptions.HTTPError as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"HTTP错误 ({e.response.status_code})，正在重试 ({retry_count}/{max_retries})...")
                    time.sleep(2)
                else:
                    print(f"HTTP错误，已达到最大重试次数: {e}")
                    return self._get_cached_intraday_nav()
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"网络请求错误，正在重试 ({retry_count}/{max_retries})...")
                    time.sleep(2)
                else:
                    print(f"网络请求错误，已达到最大重试次数: {e}")
                    return self._get_cached_intraday_nav()
        
        try:
            
            html = etree.HTML(response.content)
            
            result = {
                'date': None,
                'time': None,
                'nav_usd': None
            }
            
            # 提取日期
            date_elements = html.xpath("//span[@class='sIopvDate']")
            if date_elements:
                result['date'] = date_elements[0].text.strip()
            
            # 提取时间并转换格式
            time_elements = html.xpath("//span[@class='sIopvTime']")
            if time_elements:
                time_str = time_elements[0].text.strip()
                # 尝试将时间格式转换为与场内价格一致的格式
                if result['date']:
                    try:
                        # 解析日期和时间
                        date_obj = datetime.strptime(result['date'], "%d-%b-%Y")
                        # 解析时间
                        if 'AM' in time_str or 'PM' in time_str:
                            time_obj = datetime.strptime(time_str, "%I:%M %p")
                        else:
                            time_obj = datetime.strptime(time_str, "%H:%M")
                        # 组合日期和时间
                        combined_datetime = datetime.combine(date_obj.date(), time_obj.time())
                        # 格式化为统一格式
                        result['time'] = combined_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception as e:
                        # 如果解析失败，使用原始时间
                        # 手动构造时间格式
                        if 'AM' in time_str:
                            # 上午时间
                            time_part = time_str.replace('AM', '').strip()
                            hour, minute = map(int, time_part.split(':'))
                        elif 'PM' in time_str:
                            # 下午时间
                            time_part = time_str.replace('PM', '').strip()
                            hour, minute = map(int, time_part.split(':'))
                            hour += 12
                            if hour == 24:
                                hour = 0
                        else:
                            # 24小时制时间
                            hour, minute = map(int, time_str.split(':'))
                        
                        # 构造完整的日期时间
                        if result['date']:
                            try:
                                date_obj = datetime.strptime(result['date'], "%d-%b-%Y")
                                combined_datetime = datetime(date_obj.year, date_obj.month, date_obj.day, hour, minute, 0)
                                result['time'] = combined_datetime.strftime("%Y-%m-%d %H:%M:%S")
                            except:
                                result['time'] = time_str
                        else:
                            result['time'] = time_str
                else:
                    result['time'] = time_str
            
            # 提取净值
            usd_nav_elements = html.xpath("//span[@class='nIopvPrice1']")
            if usd_nav_elements:
                result['nav_usd'] = float(usd_nav_elements[0].text.strip())
            
            # 保存到缓存
            self._save_intraday_nav_cache(result)
            
            return result
                
        except Exception as e:
            print(f"获取实时净值时出错: {e}")
            return self._get_cached_intraday_nav()
    
    def get_intraday_nav_from_api(self):
        """
        从ICE API获取实时净值（Intraday NAV）
        
        使用新的ICE API获取实时净值数据。该API返回JSON格式数据，
        更稳定可靠。
        
        返回:
            dict: 包含以下键的字典:
                - date (str): 日期，格式为 "DD-Mon-YYYY"
                - time (str): 时间，格式为 "YYYY-MM-DD HH:MM:SS"
                - nav_usd (float): 实时净值（美元）
                
                如果获取失败，返回 None
        
        使用示例:
            >>> calculator = IOPVCalculator()
            >>> result = calculator.get_intraday_nav_from_api()
            >>> print(result)
            {'date': '03-Mar-2026', 'time': '2026-03-03 13:34:00', 'nav_usd': 1.9539}
        """
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
                
                # 解析JSON响应
                data = response.json()
                
                result = {
                    'date': None,
                    'time': None,
                    'nav_usd': None
                }
                
                # 从JSON中提取数据
                if 'quote' in data and 'rows' in data['quote'] and len(data['quote']['rows']) > 0:
                    row = data['quote']['rows'][0]
                    result['date'] = row.get('date', None)
                    result['time'] = row.get('time', None)
                    # values[1] 是USD净值
                    if 'values' in row and len(row['values']) > 1:
                        result['nav_usd'] = float(row['values'][1])
                
                # 转换日期和时间格式
                if result['date'] and result['time']:
                    try:
                        # 解析日期格式 "03 Mar 2026"
                        date_obj = datetime.strptime(result['date'], "%d %b %Y")
                        # 解析时间格式 "01:34 PM"
                        time_obj = datetime.strptime(result['time'], "%I:%M %p")
                        # 组合日期和时间
                        combined_datetime = datetime.combine(date_obj.date(), time_obj.time())
                        # 格式化为统一格式
                        result['time'] = combined_datetime.strftime("%Y-%m-%d %H:%M:%S")
                        result['date'] = date_obj.strftime("%d-%b-%Y")
                    except Exception as e:
                        print(f"日期时间格式转换失败: {e}")
                
                # 保存到缓存
                self._save_intraday_nav_cache(result)
                
                return result
                
            except requests.exceptions.SSLError as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"SSL连接错误，正在重试 ({retry_count}/{max_retries})...")
                    time.sleep(2)
                else:
                    print(f"SSL连接错误，已达到最大重试次数: {e}")
                    return None
            except requests.exceptions.Timeout as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"请求超时，正在重试 ({retry_count}/{max_retries})...")
                    time.sleep(2)
                else:
                    print(f"请求超时，已达到最大重试次数: {e}")
                    return None
            except requests.exceptions.HTTPError as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"HTTP错误 ({e.response.status_code})，正在重试 ({retry_count}/{max_retries})...")
                    time.sleep(2)
                else:
                    print(f"HTTP错误，已达到最大重试次数: {e}")
                    return None
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"网络请求错误，正在重试 ({retry_count}/{max_retries})...")
                    time.sleep(2)
                else:
                    print(f"网络请求错误，已达到最大重试次数: {e}")
                    return None
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"JSON解析错误: {e}")
                return None
        
        return None
    
    def _get_cached_intraday_nav(self):
        """
        从缓存获取实时净值数据
        
        当无法从网络获取数据时，尝试从缓存文件中读取之前保存的数据。
        
        返回:
            dict: 包含以下键的字典:
                - date (str): 日期
                - time (str): 时间
                - nav_usd (float): 实时净值（美元）
                
                如果缓存不存在或已过期，返回默认值。
        """
        try:
            if os.path.exists(self.intraday_nav_cache_file):
                with open(self.intraday_nav_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # 检查缓存是否是当天的
                today = datetime.now().strftime("%Y-%m-%d")
                if cache_data.get('cache_date') == today:
                    print(f"使用缓存的Intraday NAV数据 ({cache_data.get('cache_date')})")
                    return cache_data.get('data')
            
            return {'date': 'N/A', 'time': 'N/A', 'nav_usd': None}
        except Exception as e:
            print(f"读取缓存数据时出错: {e}")
            return {'date': 'N/A', 'time': 'N/A', 'nav_usd': None}
    
    def _save_intraday_nav_cache(self, data):
        """
        保存实时净值数据到缓存
        
        参数:
            data (dict): 要保存的实时净值数据
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            cache_data = {
                'cache_date': today,
                'data': data
            }
            with open(self.intraday_nav_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存数据时出错: {e}")
    
    def get_market_price(self):
        """
        获取159687的当前市场价格
        
        从新浪财经API获取ETF 159687的实时市场价格数据，包括当前价格、
        涨跌幅和更新时间。
        
        返回:
            dict: 包含以下键的字典:
                - price (float): 当前市场价格（人民币）
                - time (str): 更新时间，格式为 "YYYY-MM-DD HH:MM:SS"
                - change_pct (float): 涨跌幅百分比
                
                如果获取失败，返回:
                - price: None
                - time: None
                - change_pct: None
        
        注意:
            - 涨跌幅计算公式：(当前价格 - 昨收价) / 昨收价 * 100
            - 如果当前价格不可用，会尝试使用昨收价
        
        使用示例:
            >>> calculator = IOPVCalculator()
            >>> result = calculator.get_market_price()
            >>> print(result)
            {'price': 1.742, 'time': '2026-02-26 15:00:00', 'change_pct': 0.17}
        """
        try:
            import re
            
            url = "http://hq.sinajs.cn/list=sz159687"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://finance.sina.com.cn/"
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # 解析返回的数据
            match = re.search(r'="([^"]*)"', response.text)
            if match:
                data = match.group(1).split(',')
                if len(data) >= 32:
                    # data[2]: 昨收价
                    # data[3]: 当前价格
                    price = float(data[3]) if data[3] else float(data[2])
                    prev_close = float(data[2]) if data[2] else None
                    date = data[30] if len(data) > 30 else None
                    time_str = data[31] if len(data) > 31 else None
                    
                    update_time = f"{date} {time_str}" if date and time_str else None
                    
                    # 计算涨跌幅
                    change_pct = None
                    if prev_close and prev_close > 0 and price:
                        change_pct = ((price - prev_close) / prev_close) * 100
                    
                    return {
                        'price': price,
                        'time': update_time,
                        'change_pct': change_pct
                    }
            
            raise Exception("未找到价格数据")
                
        except Exception as e:
            print(f"获取实时价格时出错: {e}")
            return {'price': None, 'time': None, 'change_pct': None}
    
    def get_latest_nav(self):
        """
        获取最新基金净值
        
        通过akshare库获取ETF 159687的最新基金净值数据。为了减少API调用，
        数据会缓存到本地文件，每天只获取一次。
        
        返回:
            dict: 包含以下键的字典:
                - nav (float): 最新基金净值（人民币）
                - date (str): 净值日期，格式为 "YYYY-MM-DD"
                
                如果获取失败，返回:
                - nav: None
                - date: None
        
        注意:
            - 缓存文件: latest_nav_cache.json
            - 缓存有效期: 1天（当天有效）
            - 数据来源: 东方财富网（通过akshare库）
        
        使用示例:
            >>> calculator = IOPVCalculator()
            >>> result = calculator.get_latest_nav()
            >>> print(result)
            {'nav': 1.7351, 'date': '2026-02-24'}
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # 检查缓存是否存在且有效
            if os.path.exists(self.latest_nav_cache_file):
                with open(self.latest_nav_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                if cache_data.get('cache_date') == today:
                    return cache_data.get('data')
            
            # 从akshare获取数据
            df = ak.fund_etf_fund_info_em(fund='159687')
            latest_row = df.iloc[-1]
            
            result = {
                'nav': float(latest_row['单位净值']),
                'date': str(latest_row['净值日期'])
            }
            
            # 保存到缓存
            cache_data = {
                'cache_date': today,
                'data': result
            }
            with open(self.latest_nav_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            return result
        except Exception as e:
            print(f"获取最新基金净值时出错: {e}")
            return {'nav': None, 'date': None}
    
    def get_historical_nav_by_date(self, target_date):
        """
        获取指定日期的历史净值
        
        从CSOP官网获取Historical NAVs数据，并查找与指定日期匹配的净值。
        数据通过解析网页上的echarts图表获取。
        
        参数:
            target_date (str): 目标日期，格式为 "YYYY-MM-DD"（如 "2026-02-24"）
        
        返回:
            dict: 包含以下键的字典:
                - date (str): 日期，格式为 "YYYY-MM-DD"
                - nav (float): 历史净值（美元）
                
                如果未找到匹配日期，返回最新可用的历史净值。
                如果获取失败，返回 None。
        
        注意:
            - 缓存文件: historical_nav_cache.json
            - 缓存有效期: 1天（当天有效）
            - 数据来源: CSOP官网的echarts图表
            - 需要使用DrissionPage库进行网页自动化
        
        使用示例:
            >>> calculator = IOPVCalculator()
            >>> result = calculator.get_historical_nav_by_date("2026-02-24")
            >>> print(result)
            {'date': '2026-02-24', 'nav': 2.0003}
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # 检查缓存是否存在且有效
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
            
            # 如果没有缓存，从网页获取数据
            if not cache_data:
                from DrissionPage import ChromiumPage
                
                page = ChromiumPage()
                page.get(self.url)
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
                    # 转换最后一个日期的格式为 YYYY-MM-DD
                    date_obj = datetime.strptime(dates[-1], "%d %b,%Y")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                    return {
                        'date': formatted_date,
                        'nav': nav_data[-1]
                    }
                except:
                    # 如果转换失败，使用原始日期
                    return {
                        'date': dates[-1],
                        'nav': nav_data[-1]
                    }
            
            return None
                
        except Exception as e:
            print(f"获取Historical NAV时出错: {e}")
            return None
    
    def estimate_premium_discount(self, market_price, nav):
        """
        计算溢价/折价率
        
        根据市场价格和净值计算溢价/折价率。正值表示溢价，负值表示折价。
        
        参数:
            market_price (float): 市场价格（人民币）
            nav (float): 估算净值（人民币）
        
        返回:
            float: 溢价/折价率百分比
                   正值表示溢价（市场价格高于净值）
                   负值表示折价（市场价格低于净值）
                   如果参数无效，返回 None
        
        计算公式:
            溢价率 = (市场价格 - 净值) / 净值 * 100
        
        使用示例:
            >>> calculator = IOPVCalculator()
            >>> rate = calculator.estimate_premium_discount(1.742, 1.7678)
            >>> print(f"{rate:.2f}%")  # 输出: -1.46%
        """
        if market_price and nav:
            return ((market_price - nav) / nav) * 100
        return None
    
    def calculate_nav_change(self, historical_nav, intraday_nav):
        """
        计算NAV涨跌幅
        
        计算从历史净值到实时净值的涨跌幅度和百分比。
        
        参数:
            historical_nav (float): 历史净值（美元）
            intraday_nav (float): 实时净值（美元）
        
        返回:
            dict: 包含以下键的字典:
                - change (float): 涨跌额（美元）
                - change_pct (float): 涨跌幅百分比
                
                如果参数无效，返回 None
        
        计算公式:
            涨跌额 = 实时净值 - 历史净值
            涨跌幅 = 涨跌额 / 历史净值 * 100
        
        使用示例:
            >>> calculator = IOPVCalculator()
            >>> result = calculator.calculate_nav_change(2.0003, 2.038)
            >>> print(result)
            {'change': 0.0377, 'change_pct': 1.88}
        """
        if historical_nav and intraday_nav and historical_nav > 0:
            change = intraday_nav - historical_nav
            change_pct = (change / historical_nav) * 100
            return {
                'change': change,
                'change_pct': change_pct
            }
        return None
    
    def print_table(self, market_price_info, intraday_result, latest_nav, historical_nav, nav_change_result, estimated_nav, premium_discount):
        """
        打印估值数据表格
        
        将估值数据以表格形式输出到控制台。该方法不获取数据，
        只负责格式化输出。
        
        参数:
            market_price_info (dict): 市场价格信息，包含 price, time, change_pct
            intraday_result (dict): 实时净值信息，包含 date, time, nav_usd
            latest_nav (dict): 最新基金净值，包含 nav, date
            historical_nav (dict): 历史净值，包含 nav, date
            nav_change_result (dict): NAV涨跌幅，包含 change, change_pct
            estimated_nav (float): 估算实时净值（人民币）
            premium_discount (float): 溢价/折价率百分比
        
        返回:
            None（直接打印到控制台）
        
        输出格式:
            ┌──────────────────────────────────────────────────────────────────────────────
            │                                159687 实时估值数据
            ├──────────────────────────────────────────────────────────────────────────────
            │ 项目                   │                           数值
            ├──────────────────────────────────────────────────────────────────────────────
            │ 场内价格                                        1.742 CNY
            │ 涨跌幅                                           0.17%
            │ 更新时间                                   2026-02-26 15:00:00
            │ 估算实时净值                                      1.7678 CNY
            │ 溢价率                                           -1.46%
            │ 最新基金净值                             1.7351 CNY (日期: 2026-02-24)
            │ Intraday NAV                   2.038 USD (时间: 2026-02-26 16:59:00)
            │ Historical NAV                     2.0003 USD (日期: 2026-02-24)
            │ NAV涨跌幅                                        1.88%
            └──────────────────────────────────────────────────────────────────────────────
        
        使用示例:
            >>> calculator = IOPVCalculator()
            >>> calculator.print_table(
            ...     {'price': 1.742, 'time': '2026-02-26 15:00:00', 'change_pct': 0.17},
            ...     {'date': '26-Feb-2026', 'time': '2026-02-26 16:59:00', 'nav_usd': 2.038},
            ...     {'nav': 1.7351, 'date': '2026-02-24'},
            ...     {'nav': 2.0003, 'date': '2026-02-24'},
            ...     {'change': 0.0377, 'change_pct': 1.88},
            ...     1.7678,
            ...     -1.46
            ... )
        """
        # 表格输出
        print("\n")
        print("┌" + "─" * 78)
        print("│ {:^76} ".format("159687 实时估值数据"))
        print("├" + "─" * 78 + "")
        print("│ {:<20} │ {:^54} ".format("项目", "数值"))
        print("├" + "─" * 78)
        
        # 市场价格
        price_str = f"{market_price_info['price']:.3f} CNY" if market_price_info['price'] else "--"
        print("│ {:<20}  {:^54} ".format("场内价格", price_str))
        
        # 涨跌幅
        change_str = f"{market_price_info['change_pct']:.2f}%" if market_price_info['change_pct'] is not None else "--"
        print("│ {:<20}  {:^54} ".format("涨跌幅", change_str))
        
        # 更新时间
        time_str = f"{market_price_info['time']}" if market_price_info['time'] else "--"
        print("│ {:<20}  {:^54} ".format("更新时间", time_str))
        
        # 估算净值
        estimated_nav_str = f"{estimated_nav:.4f} CNY" if estimated_nav else "--"
        print("│ {:<20}  {:^54} ".format("估算实时净值", estimated_nav_str))
        
        # 溢价率
        premium_str = f"{premium_discount:.2f}%" if premium_discount is not None else "--"
        print("│ {:<20}  {:^54} ".format("溢价率", premium_str))
        
        # 最新净值
        latest_nav_str = f"{latest_nav['nav']} CNY" if latest_nav['nav'] else "--"
        latest_nav_date = latest_nav['date'] if latest_nav['date'] else "--"
        print("│ {:<20}  {:^54} ".format("最新基金净值", f"{latest_nav_str} (日期: {latest_nav_date})"))
        
        # Intraday NAV
        intraday_nav_str = f"{intraday_result['nav_usd']} USD" if intraday_result['nav_usd'] else "--"
        intraday_time = intraday_result['time'] if intraday_result['time'] else "--"
        # 确保时间格式统一
        if 'PM' in intraday_time or 'AM' in intraday_time:
            # 手动转换时间格式
            try:
                # 解析带AM/PM的时间
                if ' ' in intraday_time:
                    parts = intraday_time.split(' ')
                    if len(parts) == 2:
                        time_part, am_pm = parts
                        hour, minute = map(int, time_part.split(':'))
                        if am_pm.upper() == 'PM' and hour != 12:
                            hour += 12
                        elif am_pm.upper() == 'AM' and hour == 12:
                            hour = 0
                        # 构造当前日期
                        today = datetime.now().strftime("%Y-%m-%d")
                        intraday_time = f"{today} {hour:02d}:{minute:02d}:00"
            except:
                pass
        print("│ {:<20}  {:^54} ".format("Intraday NAV", f"{intraday_nav_str} (时间: {intraday_time})"))
        
        # Historical NAV
        if historical_nav:
            print("│ {:<20}  {:^54} ".format("Historical NAV", f"{historical_nav['nav']} USD (日期: {historical_nav['date']})"))
        
        # NAV涨跌幅
        if nav_change_result:
            print("│ {:<20}  {:^54} ".format("NAV涨跌幅", f"{nav_change_result['change_pct']:.2f}%"))
        
        print("└" + "─" * 78 + "")
        
        # 更新时间
        print(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    
    def run(self):
        """
        运行完整计算流程
        
        执行完整的估值计算流程，包括：
        1. 获取实时净值（Intraday NAV）- 先尝试新API，失败则使用原方法
        2. 获取市场价格
        3. 获取最新基金净值
        4. 获取历史净值数据
        5. 计算NAV涨跌幅
        6. 估算实时净值
        7. 计算溢价/折价率
        8. 打印结果表格
        
        返回:
            None（结果直接打印到控制台）
        
        使用示例:
            >>> calculator = IOPVCalculator()
            >>> calculator.run()
        """
        # 1. 获取实时净值 - 先尝试新API
        print("正在获取实时净值...")
        intraday_result = self.get_intraday_nav_from_api()
        
        # 如果新API失败，使用原来的方法
        if intraday_result is None or intraday_result.get('nav_usd') is None:
            print("新API获取失败，尝试使用原来的方法...")
            intraday_result = self.get_intraday_nav()
        
        # 2. 获取市场价格
        market_price_info = self.get_market_price()
        
        # 3. 获取最新基金净值
        latest_nav = self.get_latest_nav()
        
        # 4. 获取Historical NAVs并对比相同日期
        target_date = latest_nav['date']
        historical_nav = self.get_historical_nav_by_date(target_date)
        
        # 5. 计算Historical NAV到Intraday NAV的涨跌幅
        nav_change_result = None
        if historical_nav and intraday_result['nav_usd']:
            nav_change_result = self.calculate_nav_change(historical_nav['nav'], intraday_result['nav_usd'])
        
        # 6. 估算159687实时净值
        estimated_nav = None
        premium_discount = None
        if nav_change_result and latest_nav['nav']:
            estimated_nav = latest_nav['nav'] * (1 + nav_change_result['change_pct'] / 100)
            if market_price_info['price']:
                premium_discount = self.estimate_premium_discount(market_price_info['price'], estimated_nav)
        
        # 打印表格
        self.print_table(market_price_info, intraday_result, latest_nav, historical_nav, nav_change_result, estimated_nav, premium_discount)


if __name__ == "__main__":
    calculator = IOPVCalculator()
    calculator.run()
