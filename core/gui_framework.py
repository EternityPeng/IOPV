"""
GUI框架模块
提供统一的GUI界面，同时显示多个基金
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import os
from typing import List, Optional, Dict

from core.base import BaseFund, FundData


class FundManagerGUI:
    """
    基金管理GUI
    
    同时显示多个基金、实时刷新、数据保存等功能
    """
    
    def __init__(self, root: tk.Tk, funds: List[BaseFund]):
        """
        初始化GUI
        
        Args:
            root: Tkinter根窗口
            funds: 基金列表
        """
        self.root = root
        self.funds = {fund.fund_code: fund for fund in funds}
        self.fund_data: Dict[str, FundData] = {}
        
        self.auto_refresh_interval = 30000  # 30秒
        self.auto_refresh_id = None
        
        self._setup_window()
        self._setup_styles()
        self._setup_ui()
        
        # 自动刷新数据
        self._refresh_all_data()
    
    def _setup_window(self):
        """设置窗口属性"""
        self.root.title("基金实时估值系统")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        self.root.minsize(1000, 700)
        self.root.attributes('-topmost', True)
        
        self.root.configure(bg="#1a1a2e")
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure(
            'Refresh.TButton',
            font=('Microsoft YaHei', 11, 'bold'),
            padding=10
        )
    
    def _setup_ui(self):
        """设置UI组件"""
        self.main_container = tk.Frame(self.root, bg="#1a1a2e")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self._create_header()
        
        self._create_fund_displays()
        
        self._create_control_buttons()
    
    def _create_header(self):
        """创建标题区域"""
        header_frame = tk.Frame(self.main_container, bg="#1a1a2e")
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            header_frame,
            text="📊 基金实时估值监控",
            font=("Microsoft YaHei", 18, "bold"),
            fg="#ffffff",
            bg="#1a1a2e"
        ).pack(side=tk.LEFT)
        
        # 汇率显示
        self.rate_label = tk.Label(
            header_frame,
            text="美元/人民币: --",
            font=("Microsoft YaHei", 10),
            fg="#00bcd4",
            bg="#1a1a2e"
        )
        self.rate_label.pack(side=tk.RIGHT, padx=10)
        
        self.status_label = tk.Label(
            header_frame,
            text="就绪",
            font=("Microsoft YaHei", 10),
            fg="#888888",
            bg="#1a1a2e"
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
    
    def _create_fund_displays(self):
        """创建基金显示区域"""
        self.fund_frames = {}
        self.fund_labels = {}
        
        funds_frame = tk.Frame(self.main_container, bg="#1a1a2e")
        funds_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        for i, (fund_code, fund) in enumerate(self.funds.items()):
            fund_frame = self._create_single_fund_display(funds_frame, fund_code, fund)
            fund_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
    
    def _create_single_fund_display(self, parent, fund_code: str, fund: BaseFund) -> tk.Frame:
        """创建单个基金显示区域"""
        frame = tk.Frame(parent, bg="#2a2a4e", relief=tk.FLAT)
        
        inner_frame = tk.Frame(frame, bg="#2a2a4e")
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        title_label = tk.Label(
            inner_frame,
            text=f"{fund_code} - {fund.fund_name}",
            font=("Microsoft YaHei", 14, "bold"),
            fg="#ffffff",
            bg="#2a2a4e",
            cursor="hand2"
        )
        title_label.pack(pady=(0, 15))
        title_label.bind("<Button-1>", lambda e, fc=fund_code: self._show_csv_table(fc))
        
        separator = tk.Frame(inner_frame, height=2, bg="#4a4a6e")
        separator.pack(fill=tk.X, pady=10)
        
        self.fund_labels[fund_code] = {}
        
        data_items = [
            ("market_price", "📈 场内价格", "#ff9800"),
            ("market_change", "📊 涨跌幅", "#4caf50"),
            ("update_time", "🕐 更新时间", "#2196f3"),
            ("estimated_nav", "💰 估算净值", "#9c27b0"),
            ("premium_discount", "📉 溢价率", "#f44336"),
            ("latest_nav", "📋 最新净值", "#00bcd4"),
            ("intraday_nav", "🌐 Intraday NAV", "#ff5722"),
            ("historical_nav", "📜 Historical NAV", "#795548"),
            ("common_date_nav", "🔗 共同日期净值", "#e91e63"),
            ("nav_change", "📈 NAV涨跌幅", "#607d8b"),
            ("exchange_rate", "💱 汇率信息", "#00acc1")
        ]
        
        for key, label_text, color in data_items:
            item_frame = tk.Frame(inner_frame, bg="#2a2a4e")
            item_frame.pack(fill=tk.X, pady=4)
            
            tk.Label(
                item_frame,
                text=label_text,
                font=("Microsoft YaHei", 10),
                fg=color,
                bg="#2a2a4e",
                width=14,
                anchor=tk.W
            ).pack(side=tk.LEFT, padx=(0, 5))
            
            self.fund_labels[fund_code][key] = tk.Label(
                item_frame,
                text="--",
                font=("Microsoft YaHei", 11, "bold"),
                fg="#ffffff",
                bg="#2a2a4e",
                anchor=tk.W
            )
            self.fund_labels[fund_code][key].pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.fund_frames[fund_code] = frame
        return frame
    
    def _create_control_buttons(self):
        """创建控制按钮"""
        button_frame = tk.Frame(self.main_container, bg="#1a1a2e")
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.refresh_btn = tk.Button(
            button_frame,
            text="🔄 刷新全部数据",
            font=("Microsoft YaHei", 11, "bold"),
            fg="#ffffff",
            bg="#4a90d9",
            activebackground="#5aa0e9",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._refresh_all_data,
            width=14,
            height=2
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.auto_refresh_btn = tk.Button(
            button_frame,
            text="▶ 开启自动刷新",
            font=("Microsoft YaHei", 11, "bold"),
            fg="#ffffff",
            bg="#2ecc71",
            activebackground="#3edc81",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._toggle_auto_refresh,
            width=14,
            height=2
        )
        self.auto_refresh_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.save_btn = tk.Button(
            button_frame,
            text="💾 保存全部数据",
            font=("Microsoft YaHei", 11, "bold"),
            fg="#ffffff",
            bg="#e67e22",
            activebackground="#f68e32",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._save_all_data,
            width=14,
            height=2
        )
        self.save_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.save_history_btn = tk.Button(
            button_frame,
            text="📊 保存历史净值",
            font=("Microsoft YaHei", 11, "bold"),
            fg="#ffffff",
            bg="#9b59b6",
            activebackground="#ab69c6",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._save_all_history,
            width=14,
            height=2
        )
        self.save_history_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.test_btn = tk.Button(
            button_frame,
            text="🔧 单基金测试",
            font=("Microsoft YaHei", 11, "bold"),
            fg="#ffffff",
            bg="#607d8b",
            activebackground="#708d9b",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._open_single_fund_gui,
            width=14,
            height=2
        )
        self.test_btn.pack(side=tk.LEFT, padx=5, pady=5)
    
    def _refresh_all_data(self):
        """刷新所有基金数据"""
        self.refresh_btn.config(state=tk.DISABLED, text="⏳ 刷新中...")
        self.status_label.config(text="正在获取数据...")
        
        def fetch_all():
            threads = []
            results = {}
            errors = {}
            
            # 获取美元兑人民币汇率中间价
            try:
                from core.exchange_rate import get_usd_cny_latest_rate
                usd_cny_rate = get_usd_cny_latest_rate()
                if usd_cny_rate.get('success'):
                    rate_text = f"美元/人民币: {usd_cny_rate['rate']}"
                    self.root.after(0, lambda: self.rate_label.config(text=rate_text))
            except Exception as e:
                print(f"获取美元兑人民币汇率失败: {e}")
            
            def fetch_single(fund_code):
                try:
                    fund = self.funds[fund_code]
                    data = fund.calculate()
                    results[fund_code] = data
                except Exception as e:
                    errors[fund_code] = str(e)
                    results[fund_code] = None
            
            # 启动所有线程
            for fund_code in self.funds:
                thread = threading.Thread(target=fetch_single, args=(fund_code,), daemon=True)
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            # 按顺序输出结果（避免多线程输出冲突）
            for fund_code in self.funds:
                if fund_code in results and results[fund_code]:
                    self.funds[fund_code].print_table(results[fund_code])
                elif fund_code in errors:
                    print(f"获取{fund_code}数据出错: {errors[fund_code]}")
            
            # 更新GUI显示
            for fund_code, data in results.items():
                if data:
                    self.fund_data[fund_code] = data
                    self.root.after(0, lambda fc=fund_code, d=data: self._update_display(fc, d))
            
            self.root.after(0, lambda: self.status_label.config(
                text=f"✅ 更新于 {datetime.now().strftime('%H:%M:%S')}"
            ))
            self.root.after(0, lambda: self.refresh_btn.config(state=tk.NORMAL, text="🔄 刷新全部数据"))
        
        thread = threading.Thread(target=fetch_all, daemon=True)
        thread.start()
    
    def _update_display(self, fund_code: str, data: FundData):
        """更新单个基金的显示"""
        if fund_code not in self.fund_labels:
            return
        
        labels = self.fund_labels[fund_code]
        
        if data.market_price is not None:
            labels["market_price"].config(text=f"{data.market_price:.3f} CNY")
        else:
            labels["market_price"].config(text="--")
        
        if data.market_change_pct is not None:
            if data.market_change_pct >= 0:
                labels["market_change"].config(
                    text=f"📈 +{data.market_change_pct:.2f}%",
                    fg="#ff4444"
                )
            else:
                labels["market_change"].config(
                    text=f"📉 {data.market_change_pct:.2f}%",
                    fg="#44ff44"
                )
        else:
            labels["market_change"].config(text="--", fg="#ffffff")
        
        if data.market_time:
            labels["update_time"].config(text=f"{data.market_time}")
        else:
            labels["update_time"].config(text="--")
        
        if data.estimated_nav is not None:
            labels["estimated_nav"].config(text=f"{data.estimated_nav:.4f} CNY")
        else:
            labels["estimated_nav"].config(text="--")
        
        if data.premium_discount is not None:
            if data.premium_discount >= 0:
                labels["premium_discount"].config(
                    text=f"📈 +{data.premium_discount:.2f}%",
                    fg="#ff4444"
                )
            else:
                labels["premium_discount"].config(
                    text=f"📉 {data.premium_discount:.2f}%",
                    fg="#44ff44"
                )
        else:
            labels["premium_discount"].config(text="--", fg="#ffffff")
        
        if data.latest_nav is not None:
            nav_text = f"{data.latest_nav} CNY"
            if data.latest_nav_date:
                nav_text += f" ({data.latest_nav_date})"
            labels["latest_nav"].config(text=nav_text)
        else:
            labels["latest_nav"].config(text="--")
        
        if data.intraday_nav is not None:
            nav_text = f"{data.intraday_nav} USD"
            if data.intraday_nav_time:
                nav_text += f" ({data.intraday_nav_time})"
            labels["intraday_nav"].config(text=nav_text)
        else:
            labels["intraday_nav"].config(text="--")
        
        if data.historical_nav is not None:
            nav_text = f"{data.historical_nav} USD"
            if data.historical_nav_date:
                nav_text += f" ({data.historical_nav_date})"
            labels["historical_nav"].config(text=nav_text)
        else:
            labels["historical_nav"].config(text="--")
        
        if data.common_date_nav is not None:
            nav_text = f"{data.common_date_nav} CNY"
            if data.common_date:
                nav_text += f" ({data.common_date})"
            labels["common_date_nav"].config(text=nav_text)
        else:
            labels["common_date_nav"].config(text="--")
        
        if data.nav_change_pct is not None:
            if data.nav_change_pct >= 0:
                labels["nav_change"].config(
                    text=f"📈 +{data.nav_change_pct:.2f}%",
                    fg="#ff4444"
                )
            else:
                labels["nav_change"].config(
                    text=f"📉 {data.nav_change_pct:.2f}%",
                    fg="#44ff44"
                )
        else:
            labels["nav_change"].config(text="--", fg="#ffffff")
        
        # 更新汇率信息
        if data.usd_cny_rate is not None:
            rate_text = f"{data.usd_cny_rate:.4f}"
            if data.usd_cny_change_pct is not None and data.usd_cny_rate_on_common_date is not None and data.common_date:
                rate_text += f" ({data.usd_cny_change_pct:.2f}%"
                rate_text += f", {data.common_date}: {data.usd_cny_rate_on_common_date:.4f})"
            labels["exchange_rate"].config(text=rate_text)
        else:
            labels["exchange_rate"].config(text="--")
    
    def _toggle_auto_refresh(self):
        """切换自动刷新"""
        if self.auto_refresh_id:
            self.root.after_cancel(self.auto_refresh_id)
            self.auto_refresh_id = None
            self.auto_refresh_btn.config(text="▶ 开启自动刷新", bg="#2ecc71")
            self.status_label.config(text="⏸ 自动刷新已停止")
        else:
            self._start_auto_refresh()
            self.auto_refresh_btn.config(text="⏸ 停止自动刷新", bg="#e74c3c")
            self.status_label.config(text="▶ 自动刷新已开启")
    
    def _start_auto_refresh(self):
        """开始自动刷新"""
        self._refresh_all_data()
        self.auto_refresh_id = self.root.after(
            self.auto_refresh_interval,
            self._auto_refresh
        )
    
    def _auto_refresh(self):
        """自动刷新"""
        self._refresh_all_data()
        self.auto_refresh_id = self.root.after(
            self.auto_refresh_interval,
            self._auto_refresh
        )
    
    def _save_all_data(self):
        """保存所有基金数据"""
        saved_count = 0
        for fund_code, data in self.fund_data.items():
            if data:
                try:
                    self.funds[fund_code].save_to_file(data)
                    saved_count += 1
                except Exception as e:
                    print(f"保存{fund_code}数据失败: {e}")
        
        if saved_count > 0:
            self.status_label.config(text=f"💾 已保存 {saved_count} 个基金数据")
            messagebox.showinfo("成功", f"已保存 {saved_count} 个基金的数据")
        else:
            messagebox.showwarning("警告", "没有数据可保存")
    
    def _save_all_history(self):
        """保存所有基金的历史净值"""
        saved_count = 0
        for fund_code, data in self.fund_data.items():
            if data:
                try:
                    self._save_single_history(fund_code, data)
                    saved_count += 1
                except Exception as e:
                    print(f"保存{fund_code}历史净值失败: {e}")
        
        if saved_count > 0:
            self.status_label.config(text=f"📊 已保存 {saved_count} 个基金历史净值")
            messagebox.showinfo("成功", f"已保存 {saved_count} 个基金的历史净值")
        else:
            messagebox.showwarning("警告", "没有数据可保存")
    
    def _open_single_fund_gui(self):
        """打开单基金测试GUI"""
        from core.gui_single import run_single_fund_gui
        funds_list = list(self.funds.values())
        run_single_fund_gui(funds_list)
    
    def _save_single_history(self, fund_code: str, data: FundData):
        """保存单个基金的历史净值"""
        fund = self.funds[fund_code]
        
        if data.market_time:
            market_date = data.market_time.split(' ')[0]
            
            existing_record = fund.nav_history.get_record_by_date(market_date)
            nav_premium = None
            estimation_error = None
            if existing_record and existing_record.get('最新基金净值(CNY)'):
                try:
                    latest_nav = float(existing_record['最新基金净值(CNY)'])
                    if data.market_price and latest_nav:
                        nav_premium = ((data.market_price - latest_nav) / latest_nav) * 100
                    if data.estimated_nav and latest_nav:
                        estimation_error = ((data.estimated_nav - latest_nav) / latest_nav) * 100
                except (ValueError, TypeError):
                    pass
            
            fund.nav_history.add_record(
                date=market_date,
                market_price=data.market_price,
                estimated_nav=data.estimated_nav,
                latest_nav=None,
                historical_nav=None,
                a_share_premium=data.premium_discount,
                nav_premium=nav_premium,
                estimation_error=estimation_error
            )
        
        if data.latest_nav_date:
            existing_record = fund.nav_history.get_record_by_date(data.latest_nav_date)
            a_share_premium = None
            if existing_record and existing_record.get('场内价格(CNY)'):
                try:
                    market_price = float(existing_record['场内价格(CNY)'])
                    if data.latest_nav and market_price:
                        a_share_premium = ((market_price - data.latest_nav) / data.latest_nav) * 100
                except (ValueError, TypeError):
                    pass
            
            fund.nav_history.add_record(
                date=data.latest_nav_date,
                market_price=None,
                estimated_nav=None,
                latest_nav=data.latest_nav,
                historical_nav=data.historical_nav,
                a_share_premium=a_share_premium,
                nav_premium=None,
                estimation_error=None
            )
    
    def _show_csv_table(self, fund_code: str):
        """显示CSV表格"""
        fund = self.funds[fund_code]
        csv_path = fund.nav_history.csv_file
        
        if not os.path.exists(csv_path):
            messagebox.showinfo("提示", f"暂无历史数据")
            return
        
        try:
            table_window = tk.Toplevel(self.root)
            table_window.title(f"{fund_code} - 历史净值数据")
            table_window.geometry("900x500")
            table_window.configure(bg="#1a1a2e")
            
            tree_frame = tk.Frame(table_window, bg="#1a1a2e")
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            columns = ("日期", "场内价格", "估算净值", "最新净值", "Historical NAV", "场内溢价率", "净值溢价率", "估算误差")
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
            
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100, anchor=tk.CENTER)
            
            scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
            tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
            
            import csv
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    tree.insert('', tk.END, values=row)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
            
            style = ttk.Style()
            style.theme_use("clam")
            style.configure("Treeview", 
                          background="#2a2a4e",
                          foreground="#ffffff",
                          fieldbackground="#2a2a4e",
                          font=("Microsoft YaHei", 10))
            style.configure("Treeview.Heading", 
                          background="#4a4a6e",
                          foreground="#ffffff",
                          font=("Microsoft YaHei", 10, "bold"))
            
        except Exception as e:
            messagebox.showerror("错误", f"显示表格失败: {e}")
    
    def _on_closing(self):
        """窗口关闭事件"""
        if self.auto_refresh_id:
            self.root.after_cancel(self.auto_refresh_id)
        
        for fund_code, data in self.fund_data.items():
            if data:
                try:
                    self.funds[fund_code].save_to_file(data)
                    print(f"{fund_code} 数据已自动保存")
                except Exception as e:
                    print(f"{fund_code} 自动保存失败: {e}")
        
        self.root.destroy()
