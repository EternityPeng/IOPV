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
            bg="#2a2a4e"
        )
        self.title_label.pack(pady=(0, 20))
        
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
