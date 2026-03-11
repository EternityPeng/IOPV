"""
基金折溢价查询模块
用于查询基金的折溢价情况
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import akshare as ak
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px


class FundPremiumQuery:
    """基金折溢价查询界面"""
    
    def __init__(self, parent=None):
        """初始化查询界面"""
        if parent is None:
            self.root = tk.Tk()
            self.root.title("基金折溢价查询")
            self.root.geometry("1100x800")
        else:
            self.root = tk.Toplevel(parent)
            self.root.title("基金折溢价查询")
            self.root.geometry("1100x800")
        
        self.root.configure(bg="#1a1a2e")
        
        # 数据存储
        self.merged_df = None
        self.current_page = 1
        self.page_size = 20  # 每页显示20条数据
        self.total_pages = 0
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI组件"""
        # 标题
        title_label = tk.Label(
            self.root,
            text="📊 基金折溢价查询",
            font=("Microsoft YaHei", 18, "bold"),
            fg="#ffffff",
            bg="#1a1a2e"
        )
        title_label.pack(pady=20)
        
        # 输入区域
        input_frame = tk.Frame(self.root, bg="#1a1a2e")
        input_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 基金代码输入
        tk.Label(
            input_frame,
            text="基金代码:",
            font=("Microsoft YaHei", 12),
            fg="#ffffff",
            bg="#1a1a2e"
        ).pack(side=tk.LEFT, padx=5)
        
        self.fund_code_entry = tk.Entry(
            input_frame,
            font=("Microsoft YaHei", 12),
            width=15,
            bg="#2d2d44",
            fg="#ffffff",
            insertbackground="#ffffff"
        )
        self.fund_code_entry.pack(side=tk.LEFT, padx=5)
        
        # 查询按钮
        self.query_btn = tk.Button(
            input_frame,
            text="🔍 查询",
            font=("Microsoft YaHei", 11, "bold"),
            fg="#ffffff",
            bg="#4a90d9",
            activebackground="#5aa0e9",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._query_fund,
            width=10,
            height=1
        )
        self.query_btn.pack(side=tk.LEFT, padx=10)
        
        # 统计信息区域
        self.stats_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.stats_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.stats_label = tk.Label(
            self.stats_frame,
            text="",
            font=("Microsoft YaHei", 11),
            fg="#00ff00",
            bg="#1a1a2e",
            justify=tk.LEFT
        )
        self.stats_label.pack(anchor=tk.W)
        
        # 数据表格区域
        table_frame = tk.Frame(self.root, bg="#1a1a2e")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 创建表格
        columns = ("日期", "收盘价", "单位净值", "折溢价率(%)", "说明")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=25)
        
        # 设置列标题和宽度
        self.tree.heading("日期", text="日期")
        self.tree.heading("收盘价", text="收盘价")
        self.tree.heading("单位净值", text="单位净值")
        self.tree.heading("折溢价率(%)", text="折溢价率(%)")
        self.tree.heading("说明", text="说明")
        
        self.tree.column("日期", width=120, anchor=tk.CENTER)
        self.tree.column("收盘价", width=120, anchor=tk.CENTER)
        self.tree.column("单位净值", width=120, anchor=tk.CENTER)
        self.tree.column("折溢价率(%)", width=150, anchor=tk.CENTER)
        self.tree.column("说明", width=200, anchor=tk.CENTER)
        
        # 滚动条
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 设置表格样式
        style = ttk.Style()
        style.configure("Treeview", 
                       background="#2d2d44",
                       foreground="#ffffff",
                       fieldbackground="#2d2d44",
                       font=("Consolas", 11))
        style.configure("Treeview.Heading", 
                       background="#4a90d9",
                       foreground="#ffffff",
                       font=("Microsoft YaHei", 11, "bold"))
        
        # 分页控制区域
        page_frame = tk.Frame(self.root, bg="#1a1a2e")
        page_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 上一页按钮
        self.prev_btn = tk.Button(
            page_frame,
            text="⬅ 上一页",
            font=("Microsoft YaHei", 11, "bold"),
            fg="#ffffff",
            bg="#607d8b",
            activebackground="#708d9b",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._prev_page,
            width=12,
            height=1,
            state=tk.DISABLED
        )
        self.prev_btn.pack(side=tk.LEFT, padx=10)
        
        # 页码显示
        self.page_label = tk.Label(
            page_frame,
            text="第 0 页 / 共 0 页",
            font=("Microsoft YaHei", 12),
            fg="#ffffff",
            bg="#1a1a2e"
        )
        self.page_label.pack(side=tk.LEFT, padx=20)
        
        # 下一页按钮
        self.next_btn = tk.Button(
            page_frame,
            text="➡ 下一页",
            font=("Microsoft YaHei", 11, "bold"),
            fg="#ffffff",
            bg="#607d8b",
            activebackground="#708d9b",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._next_page,
            width=12,
            height=1,
            state=tk.DISABLED
        )
        self.next_btn.pack(side=tk.LEFT, padx=10)
        
        # 跳转到指定页
        tk.Label(
            page_frame,
            text="跳转到:",
            font=("Microsoft YaHei", 11),
            fg="#ffffff",
            bg="#1a1a2e"
        ).pack(side=tk.LEFT, padx=5)
        
        self.page_entry = tk.Entry(
            page_frame,
            font=("Microsoft YaHei", 11),
            width=5,
            bg="#2d2d44",
            fg="#ffffff",
            insertbackground="#ffffff"
        )
        self.page_entry.pack(side=tk.LEFT, padx=5)
        
        self.goto_btn = tk.Button(
            page_frame,
            text="跳转",
            font=("Microsoft YaHei", 10),
            fg="#ffffff",
            bg="#4a90d9",
            activebackground="#5aa0e9",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._goto_page,
            width=6,
            state=tk.DISABLED
        )
        self.goto_btn.pack(side=tk.LEFT, padx=5)
        
        # 导出按钮
        self.export_btn = tk.Button(
            page_frame,
            text="📁 导出CSV",
            font=("Microsoft YaHei", 11, "bold"),
            fg="#ffffff",
            bg="#e67e22",
            activebackground="#f68e32",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._export_csv,
            width=12,
            height=1,
            state=tk.DISABLED
        )
        self.export_btn.pack(side=tk.RIGHT, padx=10)
        
        # 图表按钮
        self.chart_btn = tk.Button(
            page_frame,
            text="📈 显示图表",
            font=("Microsoft YaHei", 11, "bold"),
            fg="#ffffff",
            bg="#9b59b6",
            activebackground="#ab69c6",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._show_chart,
            width=12,
            height=1,
            state=tk.DISABLED
        )
        self.chart_btn.pack(side=tk.RIGHT, padx=10)
    
    def _get_market_code(self, fund_code: str) -> str:
        """获取基金的市场代码"""
        if fund_code.startswith('5'):
            return f"sh{fund_code}"
        elif fund_code.startswith('1') or fund_code.startswith('2'):
            return f"sz{fund_code}"
        else:
            return f"sh{fund_code}"
    
    def _query_fund(self):
        """查询基金折溢价"""
        fund_code = self.fund_code_entry.get().strip()
        if not fund_code:
            messagebox.showwarning("警告", "请输入基金代码")
            return
        
        self.query_btn.config(state=tk.DISABLED, text="查询中...")
        self.stats_label.config(text="正在查询数据...")
        
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            # 1. 获取基金历史净值数据
            nav_df = ak.fund_etf_fund_info_em(fund=fund_code)
            if nav_df.empty:
                messagebox.showwarning("警告", f"未找到基金 {fund_code} 的净值数据")
                return
            
            # 2. 获取基金历史行情数据（收盘价）
            market_code = self._get_market_code(fund_code)
            price_df = ak.fund_etf_hist_sina(symbol=market_code)
            if price_df.empty:
                messagebox.showwarning("警告", f"未找到基金 {fund_code} 的行情数据")
                return
            
            # 3. 数据处理和匹配
            nav_df['净值日期'] = pd.to_datetime(nav_df['净值日期']).dt.strftime('%Y-%m-%d')
            price_df['date'] = pd.to_datetime(price_df['date']).dt.strftime('%Y-%m-%d')
            
            # 合并数据
            self.merged_df = pd.merge(
                nav_df[['净值日期', '单位净值']], 
                price_df[['date', 'close']], 
                left_on='净值日期', 
                right_on='date',
                how='inner'
            )
            
            if self.merged_df.empty:
                messagebox.showwarning("警告", "没有找到匹配的日期数据")
                return
            
            # 计算折溢价
            self.merged_df['折溢价率(%)'] = ((self.merged_df['close'] - self.merged_df['单位净值']) / self.merged_df['单位净值'] * 100).round(2)
            
            # 按日期降序排列
            self.merged_df = self.merged_df.sort_values('净值日期', ascending=False).reset_index(drop=True)
            
            # 计算总页数
            self.total_pages = (len(self.merged_df) + self.page_size - 1) // self.page_size
            self.current_page = 1
            
            # 显示统计信息
            self._show_stats(fund_code)
            
            # 显示第一页数据
            self._show_page()
            
            # 启用分页按钮
            self._update_page_buttons()
            
        except Exception as e:
            messagebox.showerror("错误", f"查询失败: {e}")
            import traceback
            print(traceback.format_exc())
        finally:
            self.query_btn.config(state=tk.NORMAL, text="🔍 查询")
    
    def _show_stats(self, fund_code: str):
        """显示统计信息"""
        if self.merged_df is None or self.merged_df.empty:
            return
        
        total_records = len(self.merged_df)
        recent_5 = self.merged_df.head(5)
        avg_premium = recent_5['折溢价率(%)'].mean()
        max_premium = recent_5['折溢价率(%)'].max()
        min_premium = recent_5['折溢价率(%)'].min()
        
        stats_text = f"基金代码: {fund_code} | 总记录数: {total_records} | "
        stats_text += f"最近5日平均折溢价: {avg_premium:.2f}% | 最高: {max_premium:.2f}% | 最低: {min_premium:.2f}%"
        
        self.stats_label.config(text=stats_text)
    
    def _show_page(self):
        """显示当前页的数据"""
        if self.merged_df is None:
            return
        
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 计算当前页的数据范围
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.merged_df))
        
        # 显示数据
        for i in range(start_idx, end_idx):
            row = self.merged_df.iloc[i]
            date_str = str(row['净值日期'])
            close_price = row['close']
            nav = row['单位净值']
            premium = row['折溢价率(%)']
            
            # 判断溢价还是折价
            if premium > 0:
                desc = "🔴 溢价"
            elif premium < 0:
                desc = "� 折价"
            else:
                desc = "⚪ 平价"
            
            self.tree.insert("", tk.END, values=(
                date_str,
                f"{close_price:.3f}",
                f"{nav:.4f}",
                f"{premium:.2f}",
                desc
            ))
        
        # 更新页码显示
        self.page_label.config(text=f"第 {self.current_page} 页 / 共 {self.total_pages} 页 (共 {len(self.merged_df)} 条记录)")
    
    def _update_page_buttons(self):
        """更新分页按钮状态"""
        if self.merged_df is None or self.merged_df.empty:
            self.prev_btn.config(state=tk.DISABLED)
            self.next_btn.config(state=tk.DISABLED)
            self.goto_btn.config(state=tk.DISABLED)
            self.export_btn.config(state=tk.DISABLED)
            self.chart_btn.config(state=tk.DISABLED)
            return
        
        # 上一页按钮
        if self.current_page <= 1:
            self.prev_btn.config(state=tk.DISABLED)
        else:
            self.prev_btn.config(state=tk.NORMAL)
        
        # 下一页按钮
        if self.current_page >= self.total_pages:
            self.next_btn.config(state=tk.DISABLED)
        else:
            self.next_btn.config(state=tk.NORMAL)
        
        # 跳转按钮
        self.goto_btn.config(state=tk.NORMAL)
        
        # 导出按钮
        self.export_btn.config(state=tk.NORMAL)
        
        # 图表按钮
        self.chart_btn.config(state=tk.NORMAL)
    
    def _prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self._show_page()
            self._update_page_buttons()
    
    def _next_page(self):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._show_page()
            self._update_page_buttons()
    
    def _goto_page(self):
        """跳转到指定页"""
        try:
            page = int(self.page_entry.get())
            if page < 1 or page > self.total_pages:
                messagebox.showwarning("警告", f"请输入 1 到 {self.total_pages} 之间的页码")
                return
            self.current_page = page
            self._show_page()
            self._update_page_buttons()
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的页码数字")
    
    def _export_csv(self):
        """导出数据到CSV文件"""
        if self.merged_df is None or self.merged_df.empty:
            messagebox.showwarning("警告", "没有数据可导出")
            return
        
        from tkinter import filedialog
        import os
        
        fund_code = self.fund_code_entry.get().strip()
        default_filename = f"{fund_code}_折溢价数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            initialfile=default_filename
        )
        
        if file_path:
            try:
                # 准备导出数据
                export_df = self.merged_df[['净值日期', 'close', '单位净值', '折溢价率(%)']].copy()
                export_df.columns = ['日期', '收盘价', '单位净值', '折溢价率(%)']
                export_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                messagebox.showinfo("成功", f"数据已导出到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")
    
    def _show_chart(self):
        """显示折溢价率图表"""
        if self.merged_df is None or self.merged_df.empty:
            messagebox.showwarning("警告", "没有数据可显示")
            return
        
        fund_code = self.fund_code_entry.get().strip()
        
        # 准备数据（按日期升序排列用于绘图）
        plot_df = self.merged_df.sort_values('净值日期', ascending=True).copy()
        
        # 创建交互式图表
        fig = go.Figure()
        
        # 添加折溢价率折线
        fig.add_trace(go.Scatter(
            x=plot_df['净值日期'],
            y=plot_df['折溢价率(%)'],
            mode='lines',
            name='折溢价率',
            line=dict(color='#4a90d9', width=2),
            hovertemplate='<b>日期</b>: %{x}<br><b>折溢价率</b>: %{y:.2f}%<extra></extra>'
        ))
        
        # 添加溢价区域填充
        fig.add_trace(go.Scatter(
            x=plot_df['净值日期'],
            y=plot_df['折溢价率(%)'].clip(lower=0),
            fill='tozeroy',
            fillcolor='rgba(231, 76, 60, 0.3)',
            line=dict(width=0),
            name='溢价区域',
            hoverinfo='skip'
        ))
        
        # 添加折价区域填充
        fig.add_trace(go.Scatter(
            x=plot_df['净值日期'],
            y=plot_df['折溢价率(%)'].clip(upper=0),
            fill='tozeroy',
            fillcolor='rgba(46, 204, 113, 0.3)',
            line=dict(width=0),
            name='折价区域',
            hoverinfo='skip'
        ))
        
        # 添加零线
        fig.add_hline(
            y=0, 
            line_dash="dash", 
            line_color="white",
            opacity=0.5,
            annotation_text="零线",
            annotation_position="right"
        )
        
        # 计算统计信息
        recent_30 = self.merged_df.head(30)
        avg_30 = recent_30['折溢价率(%)'].mean()
        max_30 = recent_30['折溢价率(%)'].max()
        min_30 = recent_30['折溢价率(%)'].min()
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text=f'{fund_code} 折溢价率走势<br><sub>最近30日: 平均 {avg_30:.2f}% | 最高 {max_30:.2f}% | 最低 {min_30:.2f}%</sub>',
                font=dict(size=18, color='white'),
                x=0.5
            ),
            xaxis=dict(
                title='日期',
                title_font=dict(size=14, color='white'),
                tickfont=dict(color='white'),
                gridcolor='rgba(255,255,255,0.1)',
                rangeslider=dict(visible=True),
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1月", step="month", stepmode="backward"),
                        dict(count=3, label="3月", step="month", stepmode="backward"),
                        dict(count=6, label="6月", step="month", stepmode="backward"),
                        dict(count=1, label="1年", step="year", stepmode="backward"),
                        dict(step="all", label="全部")
                    ]),
                    font=dict(color='white'),
                    bgcolor='#2d2d44'
                )
            ),
            yaxis=dict(
                title='折溢价率 (%)',
                title_font=dict(size=14, color='white'),
                tickfont=dict(color='white'),
                gridcolor='rgba(255,255,255,0.1)',
                autorange=True,
                fixedrange=False
            ),
            paper_bgcolor='#1a1a2e',
            plot_bgcolor='#2d2d44',
            font=dict(color='white'),
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color='white'),
                bgcolor='rgba(45, 45, 68, 0.8)'
            ),
            height=600
        )
        
        # 保存为HTML文件并在浏览器中打开
        import os
        import webbrowser
        import tempfile
        
        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        html_file = os.path.join(temp_dir, f'{fund_code}_折溢价率图表.html')
        
        # 保存图表
        fig.write_html(html_file, include_plotlyjs=True)
        
        # 在浏览器中打开
        webbrowser.open(f'file://{html_file}')
        
        messagebox.showinfo("提示", f"图表已在浏览器中打开\n文件保存在: {html_file}")
    
    def run(self):
        """运行查询界面"""
        if isinstance(self.root, tk.Tk):
            self.root.mainloop()


def run_premium_query():
    """运行基金折溢价查询界面"""
    app = FundPremiumQuery()
    app.run()


if __name__ == "__main__":
    run_premium_query()
