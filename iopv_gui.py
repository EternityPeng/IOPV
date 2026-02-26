"""159687 实时估值计算 - UI版本"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import threading
from calculate_iopv import IOPVCalculator

class IOPVGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("159687 实时估值")
        # 设置初始窗口大小
        self.root.geometry("400x300")
        # 允许窗口调整大小
        self.root.resizable(True, True)
        # 设置最小窗口大小
        self.root.minsize(300, 200)
        # 不设置最大窗口大小，允许最大化
        # 设置窗口置顶，点击别处时不会最小化
        self.root.attributes('-topmost', True)
        self.root.configure(bg="#1a1a2e")
        
        self.calculator = IOPVCalculator()
        self.auto_refresh_interval = 30000  # 30秒自动刷新一次
        self.auto_refresh_id = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # 标题 - 更新时间
        self.title_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.title_frame.pack(fill=tk.X, padx=20, pady=15)
        
        self.update_time_label = tk.Label(
            self.title_frame,
            text="更新时间: --",
            font=("Microsoft YaHei", 14, "bold"),
            fg="#ffffff",
            bg="#1a1a2e"
        )
        self.update_time_label.pack()
        
        # 分隔线
        separator = tk.Frame(self.root, height=2, bg="#4a4a6a")
        separator.pack(fill=tk.X, padx=20, pady=10)
        
        # 数据区域
        self.data_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.data_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 溢价率
        self.premium_frame = tk.Frame(self.data_frame, bg="#1a1a2e")
        self.premium_frame.pack(fill=tk.X, pady=10)
        
        self.premium_title = tk.Label(
            self.premium_frame,
            text="溢价率",
            font=("Microsoft YaHei", 12),
            fg="#aaaaaa",
            bg="#1a1a2e"
        )
        self.premium_title.pack(anchor=tk.W)
        
        self.premium_value = tk.Label(
            self.premium_frame,
            text="--",
            font=("Microsoft YaHei", 28, "bold"),
            fg="#ffffff",
            bg="#1a1a2e"
        )
        self.premium_value.pack(anchor=tk.W)
        
        # 场内价格
        self.price_frame = tk.Frame(self.data_frame, bg="#1a1a2e")
        self.price_frame.pack(fill=tk.X, pady=10)
        
        self.price_title = tk.Label(
            self.price_frame,
            text="场内价格",
            font=("Microsoft YaHei", 12),
            fg="#aaaaaa",
            bg="#1a1a2e"
        )
        self.price_title.pack(anchor=tk.W)
        
        self.price_value_frame = tk.Frame(self.price_frame, bg="#1a1a2e")
        self.price_value_frame.pack(anchor=tk.W)
        
        self.price_value = tk.Label(
            self.price_value_frame,
            text="--",
            font=("Microsoft YaHei", 28, "bold"),
            fg="#ffffff",
            bg="#1a1a2e"
        )
        self.price_value.pack(side=tk.LEFT)
        
        self.price_change = tk.Label(
            self.price_value_frame,
            text="",
            font=("Microsoft YaHei", 14),
            fg="#ffffff",
            bg="#1a1a2e"
        )
        self.price_change.pack(side=tk.LEFT, padx=(10, 0))
        
        # 刷新按钮
        self.refresh_btn = tk.Button(
            self.root,
            text="刷新数据",
            font=("Microsoft YaHei", 11),
            fg="#ffffff",
            bg="#4a4a6a",
            activebackground="#5a5a7a",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.refresh_data
        )
        # 确保按钮可见
        self.refresh_btn.pack(pady=15, side=tk.BOTTOM)
        # 设置按钮大小
        self.refresh_btn.config(width=15, height=2)
        
    def refresh_data(self):
        """刷新数据"""
        self.refresh_btn.config(state=tk.DISABLED, text="刷新中...")
        
        def fetch_data():
            try:
                # 获取数据
                intraday_result = self.calculator.get_intraday_nav()
                market_price_info = self.calculator.get_market_price()
                latest_nav = self.calculator.get_latest_nav()
                
                target_date = latest_nav['date']
                historical_nav = self.calculator.get_historical_nav_by_date(target_date)
                
                # 计算涨跌幅和估算净值
                nav_change_result = None
                estimated_nav = None
                premium_discount = None
                
                if historical_nav and intraday_result['nav_usd']:
                    nav_change_result = self.calculator.calculate_nav_change(
                        historical_nav['nav'], intraday_result['nav_usd']
                    )
                    
                if nav_change_result and latest_nav['nav']:
                    estimated_nav = latest_nav['nav'] * (1 + nav_change_result['change_pct'] / 100)
                    
                if estimated_nav and market_price_info['price']:
                    premium_discount = ((market_price_info['price'] - estimated_nav) / estimated_nav) * 100
                
                # 打印表格
                self.calculator.print_table(
                    market_price_info, intraday_result, latest_nav, 
                    historical_nav, nav_change_result, estimated_nav, premium_discount
                )
                
                # 更新UI
                self.root.after(0, lambda: self.update_ui(
                    market_price_info, premium_discount, estimated_nav
                ))
                
            except Exception as e:
                print(f"获取数据出错: {e}")
                self.root.after(0, lambda: self.refresh_btn.config(state=tk.NORMAL, text="刷新数据"))
        
        thread = threading.Thread(target=fetch_data)
        thread.daemon = True
        thread.start()
        
    def update_ui(self, market_price_info, premium_discount, estimated_nav):
        """更新UI显示"""
        # 更新时间
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.update_time_label.config(text=f"更新时间: {now}")
        
        # 更新溢价率
        if premium_discount is not None:
            if premium_discount >= 0:
                color = "#ff4757"  # 红色 - 溢价
                text = f"+{premium_discount:.2f}%"
            else:
                color = "#2ed573"  # 绿色 - 折价
                text = f"{premium_discount:.2f}%"
            self.premium_value.config(text=text, fg=color)
        else:
            self.premium_value.config(text="--", fg="#ffffff")
        
        # 更新场内价格
        if market_price_info['price']:
            self.price_value.config(text=f"{market_price_info['price']:.3f} CNY")
            
            # 涨跌幅
            if market_price_info['change_pct'] is not None:
                change_pct = market_price_info['change_pct']
                if change_pct >= 0:
                    color = "#ff4757"  # 红色 - 涨
                    text = f"(+{change_pct:.2f}%)"
                else:
                    color = "#2ed573"  # 绿色 - 跌
                    text = f"({change_pct:.2f}%)"
                self.price_change.config(text=text, fg=color)
            else:
                self.price_change.config(text="")
        else:
            self.price_value.config(text="-- CNY")
            self.price_change.config(text="")
        
        self.refresh_btn.config(state=tk.NORMAL, text="刷新数据")
        
    def run(self):
        """运行程序"""
        # 启动时自动刷新一次
        self.root.after(500, self.refresh_data)
        # 启动自动刷新
        self.start_auto_refresh()
        
        self.root.mainloop()
    
    def start_auto_refresh(self):
        """启动自动刷新"""
        self.auto_refresh_id = self.root.after(self.auto_refresh_interval, self.auto_refresh)
    
    def auto_refresh(self):
        """自动刷新数据"""
        self.refresh_data()
        # 继续设置下一次自动刷新
        self.auto_refresh_id = self.root.after(self.auto_refresh_interval, self.auto_refresh)

if __name__ == "__main__":
    app = IOPVGUI()
    app.run()
