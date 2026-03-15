"""
IOPV 基金估值系统 - Streamlit Web 应用

运行方式：
=========
方式一（推荐）：使用 Streamlit 命令
    cd web
    streamlit run app.py

方式二：指定端口
    cd web
    streamlit run app.py --server.port 8501

方式三：允许外网访问
    cd web
    streamlit run app.py --server.port 8501 --server.address 0.0.0.0

注意：
- 不要使用 python app.py 运行，否则会报错
- 默认端口是 8501，如果被占用可以换成其他端口
- 访问地址：http://localhost:8501
"""

import warnings
warnings.filterwarnings("ignore", message=".*missing ScriptRunContext.*")
warnings.filterwarnings("ignore", message=".*Could not infer format.*")
warnings.filterwarnings("ignore", category=UserWarning, module="akshare")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os
import time

# 添加父目录到路径，以便导入 core 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.base import FundData
from core.nav_history import NavHistoryManager
from funds.fund_520580 import Fund520580
from funds.fund_159687 import Fund159687
from funds.fund_513730 import Fund513730
import akshare as ak
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="IOPV 基金估值系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4a90d9;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #2d2d44;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stMetric > div {
        background-color: #2d2d44;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    
    /* 侧边栏导航美化 */
    section[data-testid="stSidebar"] [role="radiogroup"] {
        gap: 8px;
    }
    
    section[data-testid="stSidebar"] [role="radiogroup"] label {
        background: linear-gradient(135deg, #2d2d44 0%, #1a1a2e 100%);
        border-radius: 12px;
        padding: 12px 16px;
        margin: 2px 0;
        border: 1px solid #3d3d54;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: linear-gradient(135deg, #4a90d9 0%, #357abd 50%, #2d6aa0 100%);
        border-color: #5a9de9;
        transform: translateX(5px);
        box-shadow: 0 4px 15px rgba(74, 144, 217, 0.3);
    }
    
    section[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {
        background: linear-gradient(135deg, #4a90d9 0%, #357abd 100%);
        border-color: #5a9de9;
        box-shadow: 0 4px 15px rgba(74, 144, 217, 0.4);
    }
    
    section[data-testid="stSidebar"] [role="radiogroup"] label span {
        color: #e0e0e0;
        font-size: 15px;
        font-weight: 500;
    }
    
    section[data-testid="stSidebar"] [role="radiogroup"] label:hover span {
        color: #ffffff;
    }
    
    section[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] span {
        color: #ffffff;
        font-weight: 600;
    }
    
    /* 隐藏圆点 */
    section[data-testid="stSidebar"] [role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
        display: flex;
        align-items: center;
    }
    
    section[data-testid="stSidebar"] [role="radiogroup"] label div[data-testid="stMarkdownContainer"] p::before {
        content: none !important;
    }
    
    /* 隐藏 Streamlit 默认的圆点样式 */
    section[data-testid="stSidebar"] [role="radiogroup"] label input[type="radio"] {
        display: none;
    }
    
    section[data-testid="stSidebar"] [role="radiogroup"] label div[data-testid="stMarkdownContainer"] {
        display: block !important;
    }
    
    /* 侧边栏标题美化 */
    section[data-testid="stSidebar"] .stMarkdown h1 {
        color: #4a90d9;
        font-size: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #3d3d54;
    }
</style>
""", unsafe_allow_html=True)


def init_funds():
    """初始化基金"""
    if 'funds' not in st.session_state:
        st.session_state.funds = {
            '520580': Fund520580(),
            '159687': Fund159687(),
            '513730': Fund513730()
        }
    return st.session_state.funds


def show_main_dashboard(funds):
    """显示主仪表盘"""
    # 在命令行打印分割线和时间
    print("\n" + "=" * 80)
    print(f"Web 刷新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    st.markdown('<h1 class="main-header">📊 IOPV 基金估值系统</h1>', unsafe_allow_html=True)
    
    # 时间显示 - 在标题下方，字体大一点
    st.markdown(f'<p style="font-size: 18px; color: #888; text-align: center; margin-top: -10px; margin-bottom: 20px;">📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>', unsafe_allow_html=True)
    
    # 紧凑的顶部布局：刷新 | 保存TXT | 保存CSV | 自动刷新
    col1, col2, col3, col4 = st.columns([1, 1, 1.2, 1.5])
    
    with col1:
        refresh_clicked = st.button("🔄 刷新", type="primary")
    
    with col2:
        save_clicked = st.button("💾 保存TXT", type="secondary")
        if save_clicked:
            saved_count = 0
            for fund_code, fund in funds.items():
                try:
                    data = fund.calculate()
                    if data:
                        fund.save_to_file(data)
                        saved_count += 1
                except Exception as e:
                    st.error(f"保存 {fund_code} 数据失败: {e}")
            if saved_count > 0:
                st.success(f"已保存 {saved_count} 个基金")
    
    with col3:
        csv_clicked = st.button("📊 保存CSV", type="secondary")
        if csv_clicked:
            saved_count = 0
            for fund_code, fund in funds.items():
                try:
                    data = fund.calculate()
                    if data:
                        # 保存历史净值到CSV
                        if data.market_time:
                            market_date = data.market_time.split(' ')[0]
                            fund.nav_history.add_record(
                                date=market_date,
                                market_price=data.market_price,
                                close_estimated_nav=data.estimated_nav,
                                latest_nav=None,
                                historical_nav=None
                            )
                        if data.latest_nav_date:
                            fund.nav_history.add_record(
                                date=data.latest_nav_date,
                                market_price=None,
                                close_estimated_nav=None,
                                latest_nav=data.latest_nav,
                                historical_nav=data.historical_nav
                            )
                        saved_count += 1
                except Exception as e:
                    st.error(f"保存 {fund_code} 历史净值失败: {e}")
            if saved_count > 0:
                st.success(f"已保存 {saved_count} 个基金CSV")
    
    with col4:
        auto_refresh = st.toggle("自动刷新", value=False, key="auto_refresh_toggle")
        if auto_refresh:
            refresh_interval = st.select_slider(
                "间隔(秒)",
                options=[10, 30, 60, 120, 300],
                value=60,
                key="refresh_interval"
            )
    
    st.divider()
    
    # 三个基金并排显示，每个基金数据竖向排列
    fund_list = list(funds.items())
    
    # 创建3列布局
    cols = st.columns(3)
    
    # 辅助函数：安全格式化数值
    def fmt(value, format_str, prefix='', suffix=''):
        if value is None:
            return 'N/A'
        try:
            return f"{prefix}{value:{format_str}}{suffix}"
        except:
            return 'N/A'
    
    for idx, (fund_code, fund) in enumerate(fund_list):
        with cols[idx]:
            try:
                data = fund.calculate()
                if data:
                    # 基金标题
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #4a90d9 0%, #357abd 100%); 
                                padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                        <h3 style="color: white; margin: 0; text-align: center;">📈 {fund_code}</h3>
                        <p style="color: #e0e0e0; margin: 5px 0 0 0; text-align: center; font-size: 14px;">{data.fund_name}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 颜色判断函数
                    def get_color(value):
                        if value is None:
                            return 'white'
                        return '#e74c3c' if value > 0 else '#2ecc71' if value < 0 else 'white'
                    
                    # 数据表格
                    st.markdown(f"""
                    <div style="background-color: #2d2d44; padding: 15px; border-radius: 10px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr><td style="padding: 8px; border-bottom: 1px solid #3d3d54;">场内价格</td><td style="padding: 8px; border-bottom: 1px solid #3d3d54; text-align: right;">{fmt(data.market_price, '.3f', '¥')}</td></tr>
                            <tr><td style="padding: 8px; border-bottom: 1px solid #3d3d54;">涨跌幅</td><td style="padding: 8px; border-bottom: 1px solid #3d3d54; text-align: right; color: {get_color(data.market_change_pct)};">{fmt(data.market_change_pct, '+.2f', suffix='%')}</td></tr>
                            <tr><td style="padding: 8px; border-bottom: 1px solid #3d3d54;">估算净值</td><td style="padding: 8px; border-bottom: 1px solid #3d3d54; text-align: right;">{fmt(data.estimated_nav, '.4f', '¥')}</td></tr>
                            <tr style="background-color: rgba(74, 144, 217, 0.3);"><td style="padding: 10px; border-bottom: 2px solid #4a90d9; font-weight: bold;">折溢价率</td><td style="padding: 10px; border-bottom: 2px solid #4a90d9; text-align: right; font-weight: bold; font-size: 18px; color: {get_color(data.premium_discount)};">{fmt(data.premium_discount, '.2f', suffix='%')}</td></tr>
                            <tr><td style="padding: 8px; border-bottom: 1px solid #3d3d54;">最新净值</td><td style="padding: 8px; border-bottom: 1px solid #3d3d54; text-align: right;">{fmt(data.latest_nav, '.4f', '¥')}</td></tr>
                            <tr><td style="padding: 8px; border-bottom: 1px solid #3d3d54;">净值日期</td><td style="padding: 8px; border-bottom: 1px solid #3d3d54; text-align: right;">{data.latest_nav_date or 'N/A'}</td></tr>
                            <tr><td style="padding: 8px; border-bottom: 1px solid #3d3d54;">NAV涨跌幅</td><td style="padding: 8px; border-bottom: 1px solid #3d3d54; text-align: right; color: {get_color(data.nav_change_pct)};">{fmt(data.nav_change_pct, '.2f', suffix='%')}</td></tr>
                            <tr><td style="padding: 8px; border-bottom: 1px solid #3d3d54;">Intraday NAV</td><td style="padding: 8px; border-bottom: 1px solid #3d3d54; text-align: right;">{fmt(data.intraday_nav, '.4f', '$')}</td></tr>
                            <tr><td style="padding: 8px; border-bottom: 1px solid #3d3d54;">Historical NAV</td><td style="padding: 8px; border-bottom: 1px solid #3d3d54; text-align: right;">{fmt(data.historical_nav, '.4f', '$')}</td></tr>
                            <tr><td style="padding: 8px; border-bottom: 1px solid #3d3d54;">共同日期</td><td style="padding: 8px; border-bottom: 1px solid #3d3d54; text-align: right;">{data.common_date or 'N/A'}</td></tr>
                            <tr><td style="padding: 8px; border-bottom: 1px solid #3d3d54;">汇率</td><td style="padding: 8px; border-bottom: 1px solid #3d3d54; text-align: right;">{fmt(data.usd_cny_rate, '.4f')}</td></tr>
                            <tr><td style="padding: 8px; border-bottom: 1px solid #3d3d54;">汇率涨跌幅</td><td style="padding: 8px; border-bottom: 1px solid #3d3d54; text-align: right; color: {get_color(data.usd_cny_change_pct)};">{fmt(data.usd_cny_change_pct, '+.2f', suffix='%')}</td></tr>
                            <tr><td style="padding: 8px;">共同日期汇率</td><td style="padding: 8px; text-align: right;">{fmt(data.usd_cny_rate_on_common_date, '.4f')}</td></tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 官网链接
                    fund_urls = {
                        '520580': 'https://www.lionglobalinvestors.com/en/fund-lion-china-merchants-emerging-asia-select-index-etf.html',
                        '159687': 'https://www.csopasset.com/sg/en/products/sg-carbon/etf.php',
                        '513730': 'https://www.csopasset.com/sg/en/products/sg-atech/etf.php'
                    }
                    
                    st.markdown(f"""
                    <a href="{fund_urls.get(fund_code, '#')}" target="_blank" style="
                        display: inline-block;
                        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                        color: white;
                        padding: 8px 16px;
                        border-radius: 5px;
                        text-decoration: none;
                        font-size: 14px;
                        margin-top: 10px;
                    ">🔗 访问官网查看 Historical NAV</a>
                    """, unsafe_allow_html=True)
                    
                    # 手动输入 Historical NAV
                    st.markdown("---")
                    st.markdown("**📝 手动输入 Historical NAV**")
                    
                    col_date, col_input, col_save = st.columns([1.5, 2, 1])
                    with col_date:
                        nav_date = st.date_input(
                            "日期",
                            value=datetime.now().date(),
                            key=f"nav_date_{fund_code}"
                        )
                    with col_input:
                        historical_nav_input = st.text_input(
                            "Historical NAV (USD)",
                            value=f"{data.historical_nav:.4f}" if data.historical_nav else "",
                            key=f"historical_nav_{fund_code}",
                            placeholder="例如: 0.9531"
                        )
                    with col_save:
                        st.write("")  # 占位
                        st.write("")  # 占位
                        if st.button("保存", key=f"save_historical_{fund_code}"):
                            try:
                                nav_value = float(historical_nav_input)
                                # 保存到缓存文件 - 统一格式
                                import json
                                cache_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), f"cache/{fund_code}/historical_nav_cache.json")
                                save_date = nav_date.strftime("%Y-%m-%d")
                                today_str = datetime.now().strftime("%Y-%m-%d")
                                
                                # 读取现有缓存或创建新的
                                if os.path.exists(cache_file):
                                    with open(cache_file, 'r', encoding='utf-8') as f:
                                        cache_data = json.load(f)
                                    # 获取现有的 data 字典
                                    nav_dict = cache_data.get('data', {})
                                else:
                                    nav_dict = {}
                                
                                # 添加或更新指定日期的数据
                                nav_dict[save_date] = nav_value
                                
                                # 构建缓存数据 - 统一格式
                                cache_data = {
                                    'cache_date': today_str,
                                    'data': nav_dict
                                }
                                
                                # 保存缓存
                                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                                with open(cache_file, 'w', encoding='utf-8') as f:
                                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                                
                                # 同步更新 nav_history.csv
                                try:
                                    from core.nav_history import NavHistoryManager
                                    cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), f"cache/{fund_code}")
                                    nav_history = NavHistoryManager(cache_dir, fund_code)
                                    nav_history.add_record(
                                        date=save_date,
                                        market_price=None,
                                        close_estimated_nav=None,
                                        next_day_estimated_nav=None,
                                        latest_nav=None,
                                        historical_nav=nav_value
                                    )
                                except Exception as e:
                                    print(f"更新 nav_history 失败: {e}")
                                
                                # 在命令行打印手动输入的信息
                                print("\n" + "=" * 80)
                                print(f"[手动输入] {fund_code} Historical NAV 已更新")
                                print(f"  日期: {save_date}")
                                print(f"  净值: ${nav_value:.4f}")
                                print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                                print("=" * 80)
                                
                                st.success(f"✅ 已保存 {save_date} 的 Historical NAV: ${nav_value:.4f}")
                                st.rerun()
                            except ValueError:
                                st.error("❌ 请输入有效的数字")
                            except Exception as e:
                                st.error(f"❌ 保存失败: {e}")
            except Exception as e:
                st.error(f"获取 {fund_code} 数据失败: {e}")
    
    # 自动刷新逻辑 - 放在数据显示之后
    if auto_refresh:
        st.markdown("---")
        countdown_placeholder = st.empty()
        countdown_placeholder.info(f"⏱️ 自动刷新已启用，{refresh_interval} 秒后刷新...")
        time.sleep(refresh_interval)
        st.rerun()


def show_premium_query():
    """显示折溢价查询页面"""
    st.markdown('<h1 class="main-header">📊 基金折溢价查询</h1>', unsafe_allow_html=True)
    
    # 输入基金代码
    col1, col2 = st.columns([1, 3])
    with col1:
        fund_code = st.text_input("基金代码", value="520580", max_chars=10)
    with col2:
        st.write("")  # 占位
    
    if st.button("🔍 查询", type="primary"):
        with st.spinner("正在查询数据..."):
            try:
                # 获取基金净值数据
                nav_df = ak.fund_etf_fund_info_em(fund=fund_code)
                
                # 获取市场代码
                if fund_code.startswith('5'):
                    market_code = f"sh{fund_code}"
                else:
                    market_code = f"sz{fund_code}"
                
                # 获取行情数据
                price_df = ak.fund_etf_hist_sina(symbol=market_code)
                
                # 数据处理
                nav_df['净值日期'] = pd.to_datetime(nav_df['净值日期']).dt.strftime('%Y-%m-%d')
                price_df['date'] = pd.to_datetime(price_df['date']).dt.strftime('%Y-%m-%d')
                
                # 合并数据
                merged_df = pd.merge(
                    nav_df[['净值日期', '单位净值']], 
                    price_df[['date', 'close']], 
                    left_on='净值日期', 
                    right_on='date',
                    how='inner'
                )
                
                # 计算折溢价
                merged_df['折溢价率(%)'] = ((merged_df['close'] - merged_df['单位净值']) / merged_df['单位净值'] * 100).round(2)
                merged_df = merged_df.sort_values('净值日期', ascending=False).reset_index(drop=True)
                
                # 保存到session state
                st.session_state.merged_df = merged_df
                st.session_state.fund_code = fund_code
                
            except Exception as e:
                st.error(f"查询失败: {e}")
    
    # 显示数据
    if 'merged_df' in st.session_state and st.session_state.merged_df is not None:
        df = st.session_state.merged_df
        fund_code = st.session_state.fund_code
        
        # 自定义天数选择
        st.subheader(f"📈 {fund_code} 折溢价统计")
        col_days, col_info = st.columns([1, 3])
        with col_days:
            days = st.number_input("统计天数", min_value=1, max_value=len(df), value=5, step=1)
        with col_info:
            st.write("")  # 占位
        
        # 统计信息
        recent_x = df.head(days)
        mean_val = recent_x['折溢价率(%)'].mean()
        std_val = recent_x['折溢价率(%)'].std()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(f"{days}日平均折溢价", f"{mean_val:.2f}%")
        with col2:
            st.metric(f"{days}日最高折溢价", f"{recent_x['折溢价率(%)'].max():.2f}%")
        with col3:
            st.metric(f"{days}日最低折溢价", f"{recent_x['折溢价率(%)'].min():.2f}%")
        with col4:
            st.metric(f"{days}日中位数", f"{recent_x['折溢价率(%)'].median():.2f}%")
        
        # 标准差信息
        col5, col6, col7 = st.columns(3)
        with col5:
            st.metric(f"{days}日标准差", f"{std_val:.2f}%")
        with col6:
            st.metric(f"+2σ 上限", f"{mean_val + 2*std_val:.2f}%")
        with col7:
            st.metric(f"-2σ 下限", f"{mean_val - 2*std_val:.2f}%")
        
        st.metric("总记录数", len(df))
        
        st.divider()
        
        # 显示图表
        st.subheader("📊 折溢价率走势图")
        
        # 准备绘图数据
        plot_df = df.sort_values('净值日期', ascending=True)
        
        # 创建图表
        fig = go.Figure()
        
        # 添加折线
        fig.add_trace(go.Scatter(
            x=plot_df['净值日期'],
            y=plot_df['折溢价率(%)'],
            mode='lines',
            name='折溢价率',
            line=dict(color='#4a90d9', width=2),
            hovertemplate='<b>日期</b>: %{x}<br><b>折溢价率</b>: %{y:.2f}%<extra></extra>'
        ))
        
        # 添加填充区域
        fig.add_trace(go.Scatter(
            x=plot_df['净值日期'],
            y=plot_df['折溢价率(%)'].clip(lower=0),
            fill='tozeroy',
            fillcolor='rgba(231, 76, 60, 0.3)',
            line=dict(width=0),
            name='溢价区域',
            hoverinfo='skip'
        ))
        
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
        fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
        
        # 更新布局
        fig.update_layout(
            title=f'{fund_code} 折溢价率走势',
            xaxis_title='日期',
            yaxis_title='折溢价率 (%)',
            hovermode='x unified',
            height=500,
            xaxis=dict(
                rangeslider=dict(visible=True),
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1月", step="month", stepmode="backward"),
                        dict(count=3, label="3月", step="month", stepmode="backward"),
                        dict(count=6, label="6月", step="month", stepmode="backward"),
                        dict(count=1, label="1年", step="year", stepmode="backward"),
                        dict(step="all", label="全部")
                    ])
                )
            ),
            yaxis=dict(autorange=True, fixedrange=False)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # 显示数据表格
        st.subheader("📋 折溢价数据表")
        
        # 分页控制
        page_size = 20
        total_pages = (len(df) + page_size - 1) // page_size
        page = st.number_input("页码", min_value=1, max_value=total_pages, value=1)
        
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, len(df))
        
        # 显示当前页数据
        display_df = df.iloc[start_idx:end_idx][['净值日期', 'close', '单位净值', '折溢价率(%)']].copy()
        display_df.columns = ['日期', '收盘价', '单位净值', '折溢价率(%)']
        display_df = display_df.reset_index(drop=True)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={
                "日期": st.column_config.TextColumn("日期"),
                "收盘价": st.column_config.NumberColumn("收盘价", format="%.3f"),
                "单位净值": st.column_config.NumberColumn("单位净值", format="%.4f"),
                "折溢价率(%)": st.column_config.NumberColumn("折溢价率(%)", format="%.2f%%")
            }
        )
        
        st.write(f"显示 {start_idx + 1}-{end_idx} 条，共 {len(df)} 条记录")
        
        # 导出按钮
        if st.button("📁 导出CSV"):
            csv = df[['净值日期', 'close', '单位净值', '折溢价率(%)']].to_csv(index=False)
            st.download_button(
                label="下载 CSV",
                data=csv,
                file_name=f"{fund_code}_折溢价数据_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )


def show_history_data(funds):
    """显示历史数据页面"""
    st.markdown('<h1 class="main-header">📊 历史数据查看</h1>', unsafe_allow_html=True)
    
    # 选择基金
    fund_code = st.selectbox("选择基金", list(funds.keys()))
    
    if st.button("查看历史数据", type="primary"):
        try:
            # 获取历史数据
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache', fund_code)
            nav_manager = NavHistoryManager(cache_dir, fund_code)
            records = nav_manager.get_all_records()
            
            if records:
                df = pd.DataFrame(records)
                st.dataframe(df, use_container_width=True)
                
                # 导出按钮
                csv = df.to_csv(index=False)
                st.download_button(
                    label="下载 CSV",
                    data=csv,
                    file_name=f"{fund_code}_历史数据_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("暂无历史数据")
                
        except Exception as e:
            st.error(f"获取历史数据失败: {e}")


def main():
    """主函数"""
    # 初始化基金
    funds = init_funds()
    
    # 侧边栏导航
    st.sidebar.title("导航")
    page = st.sidebar.radio(
        "选择页面",
        ["🏠 主仪表盘", "📊 折溢价查询", "📋 历史数据"],
        label_visibility="collapsed"
    )
    
    # 根据选择显示不同页面
    if page == "🏠 主仪表盘":
        show_main_dashboard(funds)
    elif page == "📊 折溢价查询":
        show_premium_query()
    elif page == "📋 历史数据":
        show_history_data(funds)
    
    # 侧边栏信息
    st.sidebar.divider()
    st.sidebar.info("IOPV 基金估值系统")


if __name__ == "__main__":
    main()
