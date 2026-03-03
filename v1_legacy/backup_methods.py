"""
备用方法模块
包含一些暂时未使用但可能在未来需要的方法
"""
from datetime import datetime
import os
import json

class BackupMethods:
    def __init__(self):
        self.url = "https://www.csopasset.com/sg/en/products/sg-carbon/etf.php"
        self.official_nav_cache_file = "official_nav_cache.json"
    
    def get_official_nav(self):
        """
        从官网获取Official NAV数据，每天只获取一次并缓存
        
        这个方法用于从CSOP官网获取Official NAV数据，包括：
        - 日期 (date)
        - 最新净值 (nav_last)
        - 净值变化 (nav_change)
        
        返回示例:
        {
            'date': '13-Feb-2026',
            'nav_last': 1.9924,
            'nav_change': -0.0244
        }
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            if os.path.exists(self.official_nav_cache_file):
                with open(self.official_nav_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                if cache_data.get('cache_date') == today:
                    print(f"使用缓存的Official NAV数据 ({today})")
                    return cache_data.get('data')
            
            print("正在从官网获取Official NAV数据...")
            from DrissionPage import ChromiumPage
            
            page = ChromiumPage()
            page.get(self.url)
            page.wait(5)
            
            nav_date = None
            nav_last = None
            nav_change = None
            
            rows = page.eles(".MarketInfoLine")
            print(f"找到 {len(rows)} 行MarketInfoLine")
            
            if len(rows) > 0:
                row0 = rows[0]
                row_text = row0.text.strip()
                print(f"行0完整文本: {row_text}")
                
                lines = row_text.split('\n')
                print(f"分割后的行数: {len(lines)}")
                for i, line in enumerate(lines):
                    print(f"  行[{i}]: {line.strip()}")
                
                if len(lines) >= 4:
                    nav_date = lines[1].strip()
                    nav_last = float(lines[2].strip())
                    nav_change = float(lines[3].strip())
                    print(f"成功获取Official NAV数据: {nav_last} USD ({nav_date})")
            
            page.quit()
            
            if nav_date and nav_last:
                result = {
                    'date': nav_date,
                    'nav_last': nav_last,
                    'nav_change': nav_change if nav_change else 0
                }
                
                cache_data = {
                    'cache_date': today,
                    'data': result
                }
                with open(self.official_nav_cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                print(f"数据已缓存到 {self.official_nav_cache_file}")
                
                return result
            else:
                raise Exception("无法从网页提取数据")
                
        except Exception as e:
            print(f"获取Official NAV数据时出错: {e}")
            print("使用备用数据...")
            return {
                'date': '13-Feb-2026',
                'nav_last': 1.9924,
                'nav_change': -0.0244
            }
    
    def calculate_previous_date(self, date_str):
        """
        根据日期字符串计算前一天的日期
        
        参数:
            date_str: 日期字符串，格式为 "DD-Mon-YYYY" (如 "13-Feb-2026")
        
        返回:
            前一天的日期字符串，格式相同
        
        示例:
            calculate_previous_date("13-Feb-2026") -> "12-Feb-2026"
        """
        from datetime import timedelta
        try:
            date_obj = datetime.strptime(date_str, "%d-%b-%Y")
            previous_date = date_obj - timedelta(days=1)
            return previous_date.strftime("%d-%b-%Y")
        except:
            return "N/A"


def demo_get_official_nav():
    """
    演示 get_official_nav 方法的使用
    
    这个函数展示了如何使用 get_official_nav 方法获取Official NAV数据，
    并打印出获取到的数据。
    """
    print("=" * 80)
    print("演示 get_official_nav 方法")
    print("=" * 80)
    
    backup = BackupMethods()
    result = backup.get_official_nav()
    
    print("\n")
    print("┌" + "─" * 78)
    print("│ {:^76} ".format("Official NAV 数据"))
    print("├" + "─" * 78 + "")
    print("│ {:<20} │ {:^54} ".format("项目", "数值"))
    print("├" + "─" * 78)
    
    # 日期
    print("│ {:<20}  {:^54} ".format("日期", result['date']))
    
    # 最新净值
    nav_last_str = f"{result['nav_last']} USD" if result['nav_last'] else "--"
    print("│ {:<20}  {:^54} ".format("最新净值", nav_last_str))
    
    # 净值变化
    nav_change_str = f"{result['nav_change']} USD" if result['nav_change'] else "--"
    print("│ {:<20}  {:^54} ".format("净值变化", nav_change_str))
    
    # 前一天净值
    if result['nav_last'] and result['nav_change']:
        previous_nav = result['nav_last'] - result['nav_change']
        previous_date = backup.calculate_previous_date(result['date'])
        print("│ {:<20}  {:^54} ".format("前一天净值", f"{previous_nav:.4f} USD (日期: {previous_date})"))
    
    print("└" + "─" * 78 + "")
    
    print("\n")
    print(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print("演示完成！")


if __name__ == "__main__":
    demo_get_official_nav()
