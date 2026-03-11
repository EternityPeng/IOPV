"""
定时任务调度器
用于系统定时任务调用，保存基金数据
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from funds.fund_520580 import Fund520580
from funds.fund_159687 import Fund159687
from funds.fund_513730 import Fund513730
from datetime import datetime


def get_all_funds():
    """获取所有基金实例"""
    return {
        '520580': Fund520580(),
        '159687': Fund159687(),
        '513730': Fund513730()
    }


def save_close_data():
    """
    收盘时保存数据（15:00）
    用于系统定时任务调用
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行收盘保存任务...")
    
    funds = get_all_funds()
    saved_count = 0
    
    for fund_code, fund in funds.items():
        try:
            data = fund.calculate()
            if data and data.market_price and data.estimated_nav:
                market_date = datetime.now().strftime('%Y-%m-%d')
                fund.nav_history.add_record(
                    date=market_date,
                    market_price=data.market_price,
                    close_estimated_nav=data.estimated_nav
                )
                print(f"  ✓ {fund_code}: 价格={data.market_price}, 估算净值={data.estimated_nav}")
                
                # 如果有共同日期净值数据，保存到对应日期
                if data.common_date and data.common_date_nav and data.historical_nav:
                    fund.nav_history.add_record(
                        date=data.common_date,
                        latest_nav=data.common_date_nav,
                        historical_nav=data.historical_nav
                    )
                    print(f"    共同日期={data.common_date}, 净值={data.common_date_nav}")
                
                saved_count += 1
        except Exception as e:
            print(f"  ✗ {fund_code} 保存失败: {e}")
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 收盘保存完成，共保存 {saved_count} 个基金")
    return saved_count


def save_next_day_data():
    """
    次日5点保存估算净值（05:00）
    用于系统定时任务调用
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行次日保存任务...")
    
    funds = get_all_funds()
    saved_count = 0
    
    for fund_code, fund in funds.items():
        try:
            data = fund.calculate()
            if data and data.estimated_nav:
                today = datetime.now().strftime('%Y-%m-%d')
                fund.nav_history.add_record(
                    date=today,
                    next_day_estimated_nav=data.estimated_nav
                )
                print(f"  ✓ {fund_code}: 日期={today}, 估算净值={data.estimated_nav}")
                
                # 如果有共同日期净值数据，保存到对应日期
                if data.common_date and data.common_date_nav and data.historical_nav:
                    fund.nav_history.add_record(
                        date=data.common_date,
                        latest_nav=data.common_date_nav,
                        historical_nav=data.historical_nav
                    )
                    print(f"    共同日期={data.common_date}, 净值={data.common_date_nav}")
                
                saved_count += 1
        except Exception as e:
            print(f"  ✗ {fund_code} 保存失败: {e}")
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 次日保存完成，共保存 {saved_count} 个基金")
    return saved_count


def save_all_data():
    """
    保存所有基金数据
    用于手动调用或测试
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始保存所有基金数据...")
    
    funds = get_all_funds()
    saved_count = 0
    
    for fund_code, fund in funds.items():
        try:
            data = fund.calculate()
            if data:
                fund.save_to_file(data)
                print(f"  ✓ {fund_code} 数据已保存")
                saved_count += 1
        except Exception as e:
            print(f"  ✗ {fund_code} 保存失败: {e}")
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 保存完成，共保存 {saved_count} 个基金")
    return saved_count


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='基金数据定时任务')
    parser.add_argument('task', choices=['close', 'next_day', 'all', 'test'],
                       help='任务类型: close=收盘保存, next_day=次日保存, all=保存所有数据, test=测试')
    
    args = parser.parse_args()
    
    if args.task == 'close':
        save_close_data()
    elif args.task == 'next_day':
        save_next_day_data()
    elif args.task == 'all':
        save_all_data()
    elif args.task == 'test':
        print("=" * 50)
        print("测试模式：执行所有保存任务")
        print("=" * 50)
        print("\n1. 测试收盘保存:")
        save_close_data()
        print("\n2. 测试次日保存:")
        save_next_day_data()
        print("\n3. 测试保存所有数据:")
        save_all_data()
        print("\n" + "=" * 50)
        print("测试完成")
        print("=" * 50)
