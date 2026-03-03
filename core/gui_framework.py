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
        self._setup_ui()
        
        # 默认选择第一个基金
        if funds:
            self._switch_fund(funds[0].fund_code)
    
    def _setup_window(self):
        """设置窗口属性"""
        self.root.title("基金实时估值系统")
        self.root.geometry("500x400")
        self.root.resizable(True, True)
        self.root.minsize(400, 300)
        self.root.attributes('-topmost', True)
        self.root.configure(bg="#1a1a2e")
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_ui(self):
        """设置UI组件"""
        # 基金选择区域
        self._create_fund_selector()
        
        # 数据显示区域
        self._create_data_display()
        
        # 控制按钮区域
        self._create_control_buttons()
    
    def _create_fund_selector(self):
        """创建基金选择器"""
        selector_frame = tk.Frame(self.root, bg="#1a1a2e")
        selector_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            selector_frame,
            text="选择基金:",
            font=("Microsoft YaHei", 11),
            fg="#ffffff",
            bg="#1a1a2e"
        ).pack(side=tk.LEFT, padx=5)
        
        self.fund_var = tk.StringVar()
        self.fund_combo = ttk.Combobox(
            selector_frame,
            textvariable=self.fund_var,
            state="readonly",
            width=30,
            font=("Microsoft YaHei", 10)
        )
        
        # 填充基金列表
        fund_list = [f"{code} - {fund.fund_name}" for code, fund in self.funds.items()]
        self.fund_combo['values'] = fund_list
        self.fund_combo.pack(side=tk.LEFT, padx=5)
        self.fund_combo.bind("<<ComboboxSelected>>", self._on_fund_selected)
    
    def _create_data_display(self):
        """创建数据显示区域"""
        self.data_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.data_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 标题
        self.title_label = tk.Label(
            self.data_frame,
            text="请选择基金",
            font=("Microsoft YaHei", 14, "bold"),
            fg="#ffffff",
            bg="#1a1a2e"
        )
        self.title_label.pack(pady=10)
        
        # 数据标签
        self.labels = {}
        data_items = [
            ("market_price", "场内价格"),
            ("market_change", "涨跌幅"),
            ("update_time", "更新时间"),
            ("estimated_nav", "估算净值"),
            ("premium_discount", "溢价率"),
            ("latest_nav", "最新净值"),
            ("intraday_nav", "Intraday NAV"),
            ("historical_nav", "Historical NAV"),
            ("nav_change", "NAV涨跌幅")
        ]
        
        for key, label_text in data_items:
            frame = tk.Frame(self.data_frame, bg="#1a1a2e")
            frame.pack(fill=tk.X, pady=3)
            
            tk.Label(
                frame,
                text=f"{label_text}:",
                font=("Microsoft YaHei", 11),
                fg="#aaaaaa",
                bg="#1a1a2e",
                width=12,
                anchor=tk.W
            ).pack(side=tk.LEFT, padx=5)
            
            self.labels[key] = tk.Label(
                frame,
                text="--",
                font=("Microsoft YaHei", 11, "bold"),
                fg="#ffffff",
                bg="#1a1a2e",
                anchor=tk.W
            )
            self.labels[key].pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    def _create_control_buttons(self):
        """创建控制按钮"""
        button_frame = tk.Frame(self.root, bg="#1a1a2e")
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.refresh_btn = tk.Button(
            button_frame,
            text="刷新数据",
            font=("Microsoft YaHei", 10),
            fg="#ffffff",
            bg="#4a4a6a",
            activebackground="#5a5a7a",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._refresh_data,
            width=12
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.auto_refresh_btn = tk.Button(
            button_frame,
            text="开启自动刷新",
            font=("Microsoft YaHei", 10),
            fg="#ffffff",
            bg="#2a6a4a",
            activebackground="#3a7a5a",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._toggle_auto_refresh,
            width=12
        )
        self.auto_refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = tk.Button(
            button_frame,
            text="保存数据",
            font=("Microsoft YaHei", 10),
            fg="#ffffff",
            bg="#6a4a2a",
            activebackground="#7a5a3a",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._save_data,
            width=12
        )
        self.save_btn.pack(side=tk.LEFT, padx=5)
    
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
        
        self.current_fund = self.funds[fund_code]
        self.current_data = None
        
        # 更新标题
        self.title_label.config(text=f"{self.current_fund.fund_code} - {self.current_fund.fund_name}")
        
        # 刷新数据
        self._refresh_data()
    
    def _refresh_data(self):
        """刷新数据"""
        if not self.current_fund:
            return
        
        self.refresh_btn.config(state=tk.DISABLED, text="刷新中...")
        
        def fetch():
            try:
                data = self.current_fund.calculate()
                self.current_data = data
                self.root.after(0, lambda: self._update_display(data))
                
                # 打印表格
                self.current_fund.print_table(data)
                
            except Exception as e:
                print(f"获取数据出错: {e}")
                self.root.after(0, lambda: messagebox.showerror("错误", f"获取数据失败: {e}"))
            finally:
                self.root.after(0, lambda: self.refresh_btn.config(state=tk.NORMAL, text="刷新数据"))
        
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
                    text=f"+{data.market_change_pct:.2f}%",
                    fg="#ff4444"
                )
            else:
                self.labels["market_change"].config(
                    text=f"{data.market_change_pct:.2f}%",
                    fg="#44ff44"
                )
        else:
            self.labels["market_change"].config(text="--", fg="#ffffff")
        
        # 更新时间
        if data.market_time:
            self.labels["update_time"].config(text=data.market_time)
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
                    text=f"+{data.premium_discount:.2f}% (溢价)",
                    fg="#ff4444"
                )
            else:
                self.labels["premium_discount"].config(
                    text=f"{data.premium_discount:.2f}% (折价)",
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
                    text=f"+{data.nav_change_pct:.2f}%",
                    fg="#ff4444"
                )
            else:
                self.labels["nav_change"].config(
                    text=f"{data.nav_change_pct:.2f}%",
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
            self.auto_refresh_btn.config(text="开启自动刷新", bg="#2a6a4a")
        else:
            # 开始自动刷新
            self._start_auto_refresh()
            self.auto_refresh_btn.config(text="停止自动刷新", bg="#6a2a2a")
    
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
