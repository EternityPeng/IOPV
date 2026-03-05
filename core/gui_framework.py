"""
GUI框架模块
提供统一的GUI界面，支持多基金切换
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import os
from typing import List, Optional

from core.base import BaseFund, FundData


class FundManagerGUI:
    """
    基金管理GUI
    
    支持多基金切换、实时刷新、数据保存等功能
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
        self.current_fund: Optional[BaseFund] = None
        self.current_data: Optional[FundData] = None
        
        self.auto_refresh_interval = 30000  # 30秒
        self.auto_refresh_id = None
        
        self._setup_window()
        self._setup_styles()
        self._setup_ui()
        
        # 默认选择第一个基金
        if funds:
            self._switch_fund(funds[0].fund_code)
    
    def _setup_window(self):
        """设置窗口属性"""
        self.root.title("基金实时估值系统")
        self.root.geometry("700x700")
        self.root.resizable(True, True)
        self.root.minsize(600, 600)
        self.root.attributes('-topmost', True)
        
        # 设置窗口背景色
        self.root.configure(bg="#1a1a2e")
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_styles(self):
        """设置样式"""
        # 配置ttk样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 下拉框样式
        style.configure(
            'Custom.TCombobox',
            fieldbackground='#2a2a4e',
            background='#2a2a4e',
            foreground='#ffffff',
            arrowcolor='#ffffff',
            font=('Microsoft YaHei', 11)
        )
        
        # 按钮样式
        style.configure(
            'Refresh.TButton',
            font=('Microsoft YaHei', 10),
            padding=10
        )
    
    def _setup_ui(self):
        """设置UI组件"""
        # 主容器
        self.main_container = tk.Frame(self.root, bg="#1a1a2e")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 基金选择区域
        self._create_fund_selector()
        
        # 数据显示区域
        self._create_data_display()
        
        # 控制按钮区域
        self._create_control_buttons()
    
    def _create_fund_selector(self):
        """创建基金选择器"""
        selector_frame = tk.Frame(self.main_container, bg="#1a1a2e")
        selector_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 标题和选择器在同一行
        tk.Label(
            selector_frame,
            text="🎯 选择基金:",
            font=("Microsoft YaHei", 12, "bold"),
            fg="#ffffff",
            bg="#1a1a2e"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.fund_var = tk.StringVar()
        self.fund_combo = ttk.Combobox(
            selector_frame,
            textvariable=self.fund_var,
            state="readonly",
            width=40,
            font=("Microsoft YaHei", 11),
            style='Custom.TCombobox'
        )
        
        # 填充基金列表
        fund_list = [f"{code} - {fund.fund_name}" for code, fund in self.funds.items()]
        self.fund_combo['values'] = fund_list
        self.fund_combo.pack(side=tk.LEFT, padx=5, ipady=5)
        self.fund_combo.bind("<<ComboboxSelected>>", self._on_fund_selected)
    
    def _create_data_display(self):
        """创建数据显示区域"""
        # 数据框架
        self.data_frame = tk.Frame(self.main_container, bg="#2a2a4e", relief=tk.FLAT)
        self.data_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 内边距
        inner_frame = tk.Frame(self.data_frame, bg="#2a2a4e")
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # 标题
        self.title_label = tk.Label(
            inner_frame,
            text="请选择基金",
            font=("Microsoft YaHei", 16, "bold"),
            fg="#ffffff",
            bg="#2a2a4e",
            cursor="hand2"
        )
        self.title_label.pack(pady=(0, 20))
        self.title_label.bind("<Button-1>", self._show_csv_table)
        
        # 分隔线
        separator = tk.Frame(inner_frame, height=2, bg="#4a4a6e")
        separator.pack(fill=tk.X, pady=10)
        
        # 数据标签
        self.labels = {}
        data_items = [
            ("market_price", "📈 场内价格", "#ff9800"),
            ("market_change", "📊 涨跌幅", "#4caf50"),
            ("update_time", "🕐 更新时间", "#2196f3"),
            ("estimated_nav", "💰 估算净值", "#9c27b0"),
            ("premium_discount", "📉 溢价率", "#f44336"),
            ("latest_nav", "📋 最新净值", "#00bcd4"),
            ("common_date_nav", "🔗 共同日期净值", "#e91e63"),
            ("intraday_nav", "🌐 Intraday NAV", "#ff5722"),
            ("historical_nav", "📜 Historical NAV", "#795548"),
            ("nav_change", "📈 NAV涨跌幅", "#607d8b")
        ]
        
        for key, label_text, color in data_items:
            frame = tk.Frame(inner_frame, bg="#2a2a4e")
            frame.pack(fill=tk.X, pady=8)
            
            # 标签
            tk.Label(
                frame,
                text=label_text,
                font=("Microsoft YaHei", 12),
                fg=color,
                bg="#2a2a4e",
                width=18,
                anchor=tk.W
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            # 数值
            self.labels[key] = tk.Label(
                frame,
                text="--",
                font=("Microsoft YaHei", 14, "bold"),
                fg="#ffffff",
                bg="#2a2a4e",
                anchor=tk.W
            )
            self.labels[key].pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _create_control_buttons(self):
        """创建控制按钮"""
        button_frame = tk.Frame(self.main_container, bg="#1a1a2e")
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # 刷新按钮
        self.refresh_btn = tk.Button(
            button_frame,
            text="🔄 刷新数据",
            font=("Microsoft YaHei", 11, "bold"),
            fg="#ffffff",
            bg="#4a90d9",
            activebackground="#5aa0e9",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._refresh_data,
            width=14,
            height=2
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 自动刷新按钮
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
        
        # 保存按钮
        self.save_btn = tk.Button(
            button_frame,
            text="💾 保存数据",
            font=("Microsoft YaHei", 11, "bold"),
            fg="#ffffff",
            bg="#e67e22",
            activebackground="#f68e32",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._save_data,
            width=14,
            height=2
        )
        self.save_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 保存历史净值按钮
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
            command=self._save_history_to_csv,
            width=14,
            height=2
        )
        self.save_history_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 状态标签
        self.status_label = tk.Label(
            button_frame,
            text="就绪",
            font=("Microsoft YaHei", 10),
            fg="#888888",
            bg="#1a1a2e"
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
    
    def _on_fund_selected(self, event):
        """基金选择事件"""
        selected = self.fund_var.get()
        if selected:
            fund_code = selected.split(" - ")[0]
            self._switch_fund(fund_code)
    
    def _switch_fund(self, fund_code: str):
        """切换基金"""
        if fund_code not in self.funds:
            return
        
        # 停止当前自动刷新
        if self.auto_refresh_id:
            self.root.after_cancel(self.auto_refresh_id)
            self.auto_refresh_id = None
            self.auto_refresh_btn.config(text="▶ 开启自动刷新", bg="#2ecc71")
        
        self.current_fund = self.funds[fund_code]
        self.current_data = None
        
        # 更新标题
        self.title_label.config(text=f"{self.current_fund.fund_code} - {self.current_fund.fund_name}")
        
        # 重置显示
        for key in self.labels:
            self.labels[key].config(text="--", fg="#ffffff")
        
        # 刷新数据
        self._refresh_data()
    
    def _refresh_data(self):
        """刷新数据"""
        if not self.current_fund:
            return
        
        self.refresh_btn.config(state=tk.DISABLED, text="⏳ 刷新中...")
        self.status_label.config(text="正在获取数据...")
        
        def fetch():
            try:
                data = self.current_fund.calculate()
                self.current_data = data
                self.root.after(0, lambda: self._update_display(data))
                
                # 打印表格
                self.current_fund.print_table(data)
                
                self.root.after(0, lambda: self.status_label.config(
                    text=f"✅ 更新于 {datetime.now().strftime('%H:%M:%S')}"
                ))
                
            except Exception as e:
                print(f"获取数据出错: {e}")
                self.root.after(0, lambda: messagebox.showerror("错误", f"获取数据失败: {e}"))
                self.root.after(0, lambda: self.status_label.config(text="❌ 获取失败"))
            finally:
                self.root.after(0, lambda: self.refresh_btn.config(state=tk.NORMAL, text="🔄 刷新数据"))
        
        thread = threading.Thread(target=fetch, daemon=True)
        thread.start()
    
    def _update_display(self, data: FundData):
        """更新显示"""
        # 场内价格
        if data.market_price is not None:
            self.labels["market_price"].config(text=f"{data.market_price:.3f} CNY")
        else:
            self.labels["market_price"].config(text="--")
        
        # 涨跌幅
        if data.market_change_pct is not None:
            if data.market_change_pct >= 0:
                self.labels["market_change"].config(
                    text=f"📈 +{data.market_change_pct:.2f}%",
                    fg="#ff4444"
                )
            else:
                self.labels["market_change"].config(
                    text=f"📉 {data.market_change_pct:.2f}%",
                    fg="#44ff44"
                )
        else:
            self.labels["market_change"].config(text="--", fg="#ffffff")
        
        # 更新时间
        if data.market_time:
            self.labels["update_time"].config(text=f"📅 {data.market_time}")
        else:
            self.labels["update_time"].config(text="--")
        
        # 估算净值
        if data.estimated_nav is not None:
            self.labels["estimated_nav"].config(text=f"{data.estimated_nav:.4f} CNY")
        else:
            self.labels["estimated_nav"].config(text="--")
        
        # 溢价率
        if data.premium_discount is not None:
            if data.premium_discount >= 0:
                self.labels["premium_discount"].config(
                    text=f"📈 +{data.premium_discount:.2f}% (溢价)",
                    fg="#ff4444"
                )
            else:
                self.labels["premium_discount"].config(
                    text=f"📉 {data.premium_discount:.2f}% (折价)",
                    fg="#44ff44"
                )
        else:
            self.labels["premium_discount"].config(text="--", fg="#ffffff")
        
        # 最新净值
        if data.latest_nav is not None:
            nav_text = f"{data.latest_nav} CNY"
            if data.latest_nav_date:
                nav_text += f" ({data.latest_nav_date})"
            self.labels["latest_nav"].config(text=nav_text)
        else:
            self.labels["latest_nav"].config(text="--")
        
        # 共同日期净值
        if data.common_date_nav is not None:
            nav_text = f"{data.common_date_nav} CNY"
            if data.common_date:
                nav_text += f" ({data.common_date})"
            self.labels["common_date_nav"].config(text=nav_text)
        else:
            self.labels["common_date_nav"].config(text="--")
        
        # Intraday NAV
        if data.intraday_nav is not None:
            nav_text = f"{data.intraday_nav} USD"
            if data.intraday_nav_time:
                nav_text += f" ({data.intraday_nav_time})"
            self.labels["intraday_nav"].config(text=nav_text)
        else:
            self.labels["intraday_nav"].config(text="--")
        
        # Historical NAV
        if data.historical_nav is not None:
            nav_text = f"{data.historical_nav} USD"
            if data.historical_nav_date:
                nav_text += f" ({data.historical_nav_date})"
            self.labels["historical_nav"].config(text=nav_text)
        else:
            self.labels["historical_nav"].config(text="--")
        
        # NAV涨跌幅
        if data.nav_change_pct is not None:
            if data.nav_change_pct >= 0:
                self.labels["nav_change"].config(
                    text=f"📈 +{data.nav_change_pct:.2f}%",
                    fg="#ff4444"
                )
            else:
                self.labels["nav_change"].config(
                    text=f"📉 {data.nav_change_pct:.2f}%",
                    fg="#44ff44"
                )
        else:
            self.labels["nav_change"].config(text="--", fg="#ffffff")
    
    def _toggle_auto_refresh(self):
        """切换自动刷新"""
        if self.auto_refresh_id:
            # 停止自动刷新
            self.root.after_cancel(self.auto_refresh_id)
            self.auto_refresh_id = None
            self.auto_refresh_btn.config(text="▶ 开启自动刷新", bg="#2ecc71")
            self.status_label.config(text="⏸ 自动刷新已停止")
        else:
            # 开始自动刷新
            self._start_auto_refresh()
            self.auto_refresh_btn.config(text="⏸ 停止自动刷新", bg="#e74c3c")
            self.status_label.config(text="▶ 自动刷新已开启")
    
    def _start_auto_refresh(self):
        """开始自动刷新"""
        if self.current_fund:
            self._refresh_data()
            self.auto_refresh_id = self.root.after(
                self.current_fund.update_interval * 1000,
                self._auto_refresh
            )
    
    def _auto_refresh(self):
        """自动刷新"""
        self._refresh_data()
        if self.current_fund:
            self.auto_refresh_id = self.root.after(
                self.current_fund.update_interval * 1000,
                self._auto_refresh
            )
    
    def _save_data(self):
        """保存数据"""
        if not self.current_fund or not self.current_data:
            messagebox.showwarning("警告", "没有数据可保存")
            return
        
        try:
            filepath = self.current_fund.save_to_file(self.current_data)
            self.status_label.config(text=f"💾 已保存")
            messagebox.showinfo("成功", f"数据已保存到:\n{filepath}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def _save_history_to_csv(self):
        """保存历史净值数据到CSV"""
        if not self.current_fund or not self.current_data:
            messagebox.showwarning("警告", "没有数据可保存")
            return
        
        try:
            data = self.current_data
            
            # 1. 保存场内价格、估算实时净值和A股收盘溢价率到市场价格的日期
            if data.market_time:
                # 从market_time提取日期 (格式: 2026-03-04 15:00:00)
                market_date = data.market_time.split(' ')[0]
                
                # 检查CSV中该日期是否已有最新基金净值数据
                existing_record = self.current_fund.nav_history.get_record_by_date(market_date)
                nav_premium = None
                estimation_error = None
                if existing_record and existing_record.get('最新基金净值(CNY)'):
                    try:
                        latest_nav = float(existing_record['最新基金净值(CNY)'])
                        if data.market_price and latest_nav:
                            nav_premium = ((data.market_price - latest_nav) / latest_nav) * 100
                        # 计算估算误差（估算实时净值相对于最新基金净值）
                        if data.estimated_nav and latest_nav:
                            estimation_error = ((data.estimated_nav - latest_nav) / latest_nav) * 100
                    except (ValueError, TypeError):
                        pass
                
                self.current_fund.nav_history.add_record(
                    date=market_date,
                    market_price=data.market_price,
                    estimated_nav=data.estimated_nav,
                    latest_nav=None,
                    historical_nav=None,
                    a_share_premium=data.premium_discount,
                    nav_premium=nav_premium,
                    estimation_error=estimation_error
                )
            
            # 2. 保存最新基金净值和Historical NAV到最新净值的日期
            if data.latest_nav_date:
                # 检查CSV中该日期是否已有场内价格数据
                existing_record = self.current_fund.nav_history.get_record_by_date(data.latest_nav_date)
                nav_premium = None
                estimation_error = None
                if existing_record and existing_record.get('场内价格(CNY)'):
                    try:
                        market_price = float(existing_record['场内价格(CNY)'])
                        if market_price and data.latest_nav:
                            nav_premium = ((market_price - data.latest_nav) / data.latest_nav) * 100
                    except (ValueError, TypeError):
                        pass
                
                # 检查CSV中该日期是否已有估算实时净值数据
                if existing_record and existing_record.get('估算实时净值(CNY)'):
                    try:
                        estimated_nav = float(existing_record['估算实时净值(CNY)'])
                        if estimated_nav and data.latest_nav:
                            estimation_error = ((estimated_nav - data.latest_nav) / data.latest_nav) * 100
                    except (ValueError, TypeError):
                        pass
                
                self.current_fund.nav_history.add_record(
                    date=data.latest_nav_date,
                    market_price=None,
                    estimated_nav=None,
                    latest_nav=data.latest_nav,
                    historical_nav=data.historical_nav,
                    a_share_premium=None,
                    nav_premium=nav_premium,
                    estimation_error=estimation_error
                )
            
            csv_path = os.path.join(self.current_fund.get_cache_dir(), "nav_history.csv")
            self.status_label.config(text=f"📊 历史净值已保存")
            messagebox.showinfo("成功", f"历史净值数据已保存到:\n{csv_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def _show_csv_table(self, event=None):
        """显示CSV表格窗口"""
        if not self.current_fund:
            messagebox.showwarning("警告", "请先选择基金")
            return
        
        try:
            csv_path = os.path.join(self.current_fund.get_cache_dir(), "nav_history.csv")
            
            if not os.path.exists(csv_path):
                messagebox.showwarning("警告", "CSV文件不存在，请先保存历史净值数据")
                return
            
            # 创建新窗口
            table_window = tk.Toplevel(self.root)
            table_window.title(f"{self.current_fund.fund_code} - {self.current_fund.fund_name} - 历史净值")
            table_window.geometry("1200x600")
            table_window.configure(bg="#1a1a2e")
            
            # 创建表格框架
            table_frame = tk.Frame(table_window, bg="#2a2a4e")
            table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 创建Treeview
            from tkinter import ttk
            
            # 定义列
            columns = ['日期', '场内价格(CNY)', '估算实时净值(CNY)', '最新基金净值(CNY)', 
                      'Historical NAV(USD)', 'A股收盘溢价率(%)', '净值溢价率(%)', '估算误差(%)', '更新时间']
            
            tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
            
            # 设置列标题
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120, anchor=tk.CENTER)
            
            # 添加滚动条
            scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
            scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=tree.xview)
            tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
            
            # 读取CSV文件
            import csv
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # 跳过标题行
                for row in reader:
                    tree.insert('', tk.END, values=row)
            
            # 布局
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 设置样式
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
        
        # 保存最后的数据
        if self.current_fund and self.current_data:
            try:
                self.current_fund.save_to_file(self.current_data)
                print("数据已自动保存")
            except Exception as e:
                print(f"自动保存失败: {e}")
        
        self.root.destroy()
