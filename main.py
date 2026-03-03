"""
基金实时估值系统 - 主程序入口

使用方法:
    python main.py              # 启动GUI
    python main.py --cli        # 命令行模式
    python main.py --list       # 列出所有可用基金
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from funds import AVAILABLE_FUNDS


def list_funds():
    """列出所有可用基金"""
    print("\n" + "=" * 80)
    print("可用基金列表")
    print("=" * 80)
    
    for fund_class in AVAILABLE_FUNDS:
        fund = fund_class()
        print(f"\n{fund.fund_code} - {fund.fund_name}")
        if fund.description:
            print(f"  描述: {fund.description}")
        print(f"  刷新间隔: {fund.update_interval}秒")
    
    print("\n" + "=" * 80)


def run_cli(fund_code: str = None):
    """命令行模式运行"""
    if not AVAILABLE_FUNDS:
        print("错误: 没有可用的基金模块")
        return
    
    # 选择基金
    if fund_code:
        fund = None
        for fund_class in AVAILABLE_FUNDS:
            if fund_class().fund_code == fund_code:
                fund = fund_class()
                break
        if not fund:
            print(f"错误: 找不到基金 {fund_code}")
            return
    else:
        # 默认使用第一个基金
        fund = AVAILABLE_FUNDS[0]()
    
    print(f"\n正在计算 {fund.fund_code} - {fund.fund_name} 的估值...")
    
    try:
        data = fund.calculate()
        fund.print_table(data)
        
        # 保存数据
        save = input("\n是否保存数据到文件? (y/n): ")
        if save.lower() == 'y':
            filepath = fund.save_to_file(data)
            print(f"数据已保存到: {filepath}")
    except Exception as e:
        print(f"计算失败: {e}")


def run_gui():
    """GUI模式运行"""
    import tkinter as tk
    from core.gui_framework import FundManagerGUI
    
    if not AVAILABLE_FUNDS:
        print("错误: 没有可用的基金模块")
        return
    
    # 创建基金实例
    funds = [fund_class() for fund_class in AVAILABLE_FUNDS]
    
    # 创建GUI
    root = tk.Tk()
    app = FundManagerGUI(root, funds)
    
    print("GUI已启动，关闭窗口退出程序...")
    root.mainloop()


def main():
    """主函数"""
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "--list" or arg == "-l":
            list_funds()
        elif arg == "--cli":
            fund_code = sys.argv[2] if len(sys.argv) > 2 else None
            run_cli(fund_code)
        elif arg == "--help" or arg == "-h":
            print(__doc__)
        else:
            print(f"未知参数: {arg}")
            print("使用 --help 查看帮助")
    else:
        # 默认启动GUI
        run_gui()


if __name__ == "__main__":
    main()
