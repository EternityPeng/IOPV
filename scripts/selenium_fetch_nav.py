"""
使用 Selenium 获取 Historical NAV 和 Intraday NAV 数据的脚本

运行方式:
    python scripts/selenium_fetch_nav.py

依赖安装:
    pip install selenium webdriver-manager
"""

import json
import time
import os
import re
from datetime import datetime
from typing import Optional, Dict

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium 未安装，请运行: pip install selenium webdriver-manager")


def fetch_historical_nav_csop(
    driver,
    fund_code: str,
    main_url: str,
    max_wait_time: int = 30,
    wait_interval: int = 3
) -> Optional[Dict]:
    """
    获取 CSOP 基金 (159687, 513730) 的 Historical NAV 数据
    使用 echarts 图表数据
    """
    print(f"[{fund_code}] 正在获取 Historical NAV...")
    
    # 访问页面
    driver.get(main_url)
    time.sleep(3)
    
    # 尝试点击同意 Cookie 按钮
    try:
        agree_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.ID, "StateAccept"))
        )
        if agree_btn:
            agree_btn.click()
            print(f"[{fund_code}] 已点击同意 Cookie 按钮")
            time.sleep(1)
    except:
        pass
    
    # 滚动页面
    driver.execute_script("window.scrollTo(0, 1500)")
    time.sleep(1)
    
    # 点击 Historical NAVs 标签
    try:
        historical_tab = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Historical NAVs')]"))
        )
        if historical_tab:
            historical_tab.click()
            print(f"[{fund_code}] 已点击 Historical NAVs 标签")
            time.sleep(5)
    except:
        print(f"[{fund_code}] 未找到 Historical NAVs 标签")
    
    # 等待图表数据加载
    chart_data = None
    elapsed_time = 0
    
    while elapsed_time < max_wait_time:
        chart_data = driver.execute_script("""
            var chartDom = document.getElementById('PerformChart');
            if (chartDom && typeof echarts !== 'undefined') {
                var chart = echarts.getInstanceByDom(chartDom);
                if (chart) {
                    var option = chart.getOption();
                    if (option && option.xAxis && option.xAxis[0] && option.xAxis[0].data && option.xAxis[0].data.length > 0) {
                        return JSON.stringify(option);
                    }
                }
            }
            return null;
        """)
        
        if chart_data:
            data = json.loads(chart_data)
            dates = []
            if 'xAxis' in data:
                for xa in data['xAxis']:
                    if 'data' in xa and len(xa['data']) > 0:
                        dates = xa['data']
                        break
            
            if len(dates) > 0:
                print(f"[{fund_code}] 图表数据已加载，共 {len(dates)} 条记录")
                break
        
        print(f"[{fund_code}] 等待图表数据加载... ({elapsed_time + wait_interval}秒)")
        time.sleep(wait_interval)
        elapsed_time += wait_interval
    
    if not chart_data:
        print(f"[{fund_code}] 等待超时，未能获取到图表数据")
        return None
    
    # 解析数据
    data = json.loads(chart_data)
    dates = []
    nav_data = []
    
    if 'xAxis' in data:
        for xa in data['xAxis']:
            if 'data' in xa and len(xa['data']) > 0:
                dates = xa['data']
                break
    
    if 'series' in data:
        for s in data['series']:
            if 'data' in s and len(s.get('data', [])) > 0:
                nav_data = s.get('data', [])
                break
    
    # 转换为统一格式: {"YYYY-MM-DD": 净值}
    nav_dict = {}
    for i in range(len(dates)):
        try:
            date_str = dates[i]
            nav = nav_data[i] if i < len(nav_data) else None
            date_obj = datetime.strptime(date_str, "%d %b,%Y")
            formatted_date = date_obj.strftime("%Y-%m-%d")
            nav_dict[formatted_date] = float(nav) if nav is not None else None
        except:
            pass
    
    return nav_dict


def fetch_historical_nav_lionglobal(
    driver,
    fund_code: str,
    main_url: str,
    max_wait_time: int = 30,
    wait_interval: int = 3
) -> Optional[Dict]:
    """
    获取 Lion Global 基金 (520580) 的 Historical NAV 数据
    使用表格数据 - 仿照 fund_520580.py 的 _fetch_historical_nav_from_web 方法
    """
    print(f"[{fund_code}] 正在获取 Historical NAV...")
    
    # 访问页面
    driver.get(main_url)
    time.sleep(5)
    
    # 点击同意 Cookie 按钮 - 使用 fund_520580.py 的 XPath
    try:
        agree_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[1]/div[10]/div/div/div[3]/div[2]/a[1]'))
        )
        if agree_btn:
            agree_btn.click()
            print(f"[{fund_code}] 已点击同意 Cookie 按钮")
            time.sleep(1)
    except Exception as e:
        print(f"[{fund_code}] 点击同意 Cookie 按钮失败: {e}")
    
    # 点击 Historical NAVs 按钮 - 使用 fund_520580.py 的 XPath
    try:
        historical_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[1]/div[4]/div[1]/div/div[1]/div[9]/div[2]/ul/li[2]/button'))
        )
        if historical_btn:
            # 先滚动到元素位置
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", historical_btn)
            time.sleep(1)
            # 使用 JavaScript 点击，避免元素被遮挡
            driver.execute_script("arguments[0].click();", historical_btn)
            print(f"[{fund_code}] 已点击 Historical NAVs 按钮")
            time.sleep(3)
    except Exception as e:
        print(f"[{fund_code}] 点击 Historical NAVs 按钮失败: {e}")
    
    # 解析 Historical NAV 表格 - 使用 fund_520580.py 的选择器
    historical_nav_list = {
        'date': [],
        'nav': []
    }
    
    try:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'dtHistoricalPricing'))
        )
        if table:
            print(f"[{fund_code}] Historical NAV 表格已找到")
            tbody = table.find_element(By.TAG_NAME, 'tbody')
            if tbody:
                rows = tbody.find_elements(By.TAG_NAME, 'tr')
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    if len(cells) >= 2:
                        nav_str = cells[0].text.strip()
                        date_str = cells[1].text.strip()
                        
                        if nav_str == 'NAV Price' or date_str == 'Date':
                            continue
                        
                        try:
                            nav_value = float(nav_str)
                            historical_nav_list['date'].append(date_str)
                            historical_nav_list['nav'].append(nav_value)
                        except:
                            pass
                
                if historical_nav_list['date']:
                    print(f"[{fund_code}] 成功获取 Historical NAV 数据: {len(historical_nav_list['date'])} 条记录")
    except Exception as e:
        print(f"[{fund_code}] 解析 Historical NAV 表格失败: {e}")
    
    # 转换为字典格式 {"YYYY-MM-DD": 净值}
    nav_dict = {}
    for date_str, nav_value in zip(historical_nav_list['date'], historical_nav_list['nav']):
        # 将日期格式从 "DD-Mon-YY" 转换为 "YYYY-MM-DD"
        try:
            dt = datetime.strptime(date_str, "%d-%b-%y")
            formatted_date = dt.strftime("%Y-%m-%d")
            nav_dict[formatted_date] = nav_value
        except:
            pass
    
    return nav_dict if nav_dict else None


def fetch_historical_nav_selenium(
    fund_code: str,
    main_url: str,
    cache_file: str,
    fund_type: str = 'csop',
    max_wait_time: int = 30,
    wait_interval: int = 3
) -> Optional[Dict]:
    """
    使用 Selenium 获取 Historical NAV 数据
    
    Args:
        fund_code: 基金代码
        main_url: 基金官网 URL
        cache_file: 缓存文件路径
        fund_type: 基金类型 ('csop' 或 'lionglobal')
        max_wait_time: 最大等待时间（秒）
        wait_interval: 检查间隔（秒）
    
    Returns:
        dict: {"YYYY-MM-DD": 净值} 格式的数据
    """
    if not SELENIUM_AVAILABLE:
        print(f"[{fund_code}] Selenium 未安装，无法获取数据")
        return None
    
    # 配置 Chrome 选项
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # 注释掉以查看浏览器运行过程
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 根据基金类型选择获取方法
        if fund_type == 'lionglobal':
            nav_dict = fetch_historical_nav_lionglobal(driver, fund_code, main_url, max_wait_time, wait_interval)
        else:
            nav_dict = fetch_historical_nav_csop(driver, fund_code, main_url, max_wait_time, wait_interval)
        
        if nav_dict:
            # 保存到缓存文件
            today = datetime.now().strftime("%Y-%m-%d")
            cache_data = {
                'cache_date': today,
                'data': nav_dict
            }
            
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            print(f"[{fund_code}] Historical NAV 数据已保存到: {cache_file}")
            return nav_dict
        
        return None
        
    except Exception as e:
        print(f"[{fund_code}] Selenium 获取失败: {e}")
        return None
    
    finally:
        if driver:
            driver.quit()
            print(f"[{fund_code}] 浏览器已关闭")


def main():
    """测试脚本"""
    # 测试配置
    test_configs = [
        {
            'fund_code': '159687',
            'main_url': 'https://www.csopasset.com/sg/en/products/sg-carbon/etf.php',
            'cache_file': 'cache/159687/historical_nav_cache.json',
            'fund_type': 'csop'
        },
        {
            'fund_code': '513730',
            'main_url': 'https://www.csopasset.com/sg/en/products/sg-carbon/etf.php',
            'cache_file': 'cache/513730/historical_nav_cache.json',
            'fund_type': 'csop'
        },
        {
            'fund_code': '520580',
            'main_url': 'https://www.lionglobalinvestors.com/en/fund-lion-china-merchants-emerging-asia-select-index-etf.html',
            'cache_file': 'cache/520580/historical_nav_cache.json',
            'fund_type': 'lionglobal'
        }
    ]
    
    all_results = {}
    
    for config in test_configs:
        print("\n" + "=" * 80)
        print(f"正在处理 {config['fund_code']}...")
        print("=" * 80)
        
        # 获取 Historical NAV
        result = fetch_historical_nav_selenium(
            fund_code=config['fund_code'],
            main_url=config['main_url'],
            cache_file=config['cache_file'],
            fund_type=config['fund_type']
        )
        
        if result:
            all_results[config['fund_code']] = {
                'success': True,
                'record_count': len(result),
                'latest_date': max(result.keys()) if result else None,
                'latest_nav': result.get(max(result.keys())) if result else None,
                'oldest_date': min(result.keys()) if result else None,
                'sample_data': dict(list(result.items())[:5]) if result else None
            }
        else:
            all_results[config['fund_code']] = {
                'success': False,
                'record_count': 0
            }
        
        print("=" * 80)
    
    # 输出汇总结果
    print("\n" + "=" * 80)
    print("汇总结果")
    print("=" * 80)
    
    for fund_code, result in all_results.items():
        print(f"\n{fund_code}:")
        print(f"  成功: {result['success']}")
        print(f"  记录数: {result['record_count']}")
        if result['success']:
            print(f"  最新日期: {result['latest_date']}")
            print(f"  最新净值: {result['latest_nav']}")
            print(f"  最早日期: {result['oldest_date']}")
            print(f"  样本数据: {result['sample_data']}")
    
    # 保存汇总结果到 JSON 文件
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'selenium_fetch_result.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n汇总结果已保存到: {output_file}")


if __name__ == "__main__":
    main()
