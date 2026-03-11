# 📊 IOPV 基金估值系统

一个用于实时监控 QDII 基金估值和折溢价的系统，支持自动定时保存数据、历史净值查询和可视化分析。

---

## ✨ 功能特点

### 核心功能
- 🔄 **实时估值计算** - 基于场内价格和汇率计算基金估值
- 📈 **折溢价监控** - 实时显示基金折溢价率
- 💾 **自动保存数据** - 定时保存历史净值到 CSV 文件
- 📊 **可视化图表** - 交互式折溢价走势图

### 支持的基金
| 基金代码 | 基金名称 | 类型 |
|---------|---------|------|
| 520580 | 新兴亚洲ETF | QDII-ETF |
| 159687 | 南方东英富时亚太低碳精选ETF | QDII-ETF |
| 513730 | 南方东英东南亚科技ETF | QDII-ETF |

---

## 🖥️ 运行方式

### 方式一：桌面应用（本地运行）

```bash
# 安装依赖
pip install -r requirements.txt

# 运行桌面应用
python main.py
```

### 方式二：Web 应用（本地运行）

```bash
# 进入 web 目录
cd web

# 安装依赖
pip install -r requirements.txt

# 运行 Web 应用
streamlit run app.py
```

访问 http://localhost:8501 查看应用。

---

## 📁 项目结构

```
IOPV/
├── main.py                 # 桌面应用入口
├── requirements.txt        # Python 依赖
├── DEPLOY.md              # 部署教程
│
├── core/                  # 核心模块
│   ├── base.py           # 基金基类和数据结构
│   ├── gui_framework.py  # 桌面 GUI 框架
│   ├── nav_history.py    # 历史净值管理
│   └── premium_query.py  # 折溢价查询模块
│
├── funds/                 # 基金实现
│   ├── fund_520580.py    # 新兴亚洲ETF
│   ├── fund_159687.py    # 亚太低碳ETF
│   └── fund_513730.py    # 东南亚科技ETF
│
├── web/                   # Web 应用
│   ├── app.py            # Streamlit 主应用
│   ├── nav_scheduler.py  # 定时任务调度器
│   ├── requirements.txt  # Web 依赖
│   └── start.bat         # Windows 启动脚本
│
├── cache/                 # 数据缓存
│   ├── 520580/           # 基金数据
│   │   ├── fund_data.json
│   │   └── nav_history.csv
│   ├── 159687/
│   └── 513730/
│
└── output/               # 输出文件
    └── 520580/
        └── 520580_估值数据_*.txt
```

---

## ⏰ 定时任务

### 桌面应用定时任务

桌面应用内置定时任务功能：
- **15:00** - 收盘保存（场内价格、估算净值）
- **05:00** - 次日保存（次日5点估算净值）

### Web 应用定时任务

使用系统定时任务或 GitHub Actions：
```bash
# 收盘保存
python web/nav_scheduler.py close

# 次日保存
python web/nav_scheduler.py next_day

# 测试所有任务
python web/nav_scheduler.py test
```

---

## 🚀 部署到云端

### 架构说明

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Streamlit Cloud │     │  GitHub Actions  │     │   UptimeRobot   │
│  (Web界面)       │     │  (定时任务)      │     │  (保持运行)      │
│                 │     │                 │     │                 │
│  - 查看估值      │     │  - 15:00 收盘保存│     │  - 每5分钟访问  │
│  - 查询折溢价    │     │  - 05:00 次日保存│     │  - 防止休眠     │
│  - 手动保存      │     │  - 自动提交数据  │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 部署步骤

详细部署教程请查看 [DEPLOY.md](DEPLOY.md)

1. **上传代码到 GitHub**（Public 仓库）
2. **部署到 Streamlit Cloud**（免费）
3. **启用 GitHub Actions**（自动定时任务）
4. **配置 UptimeRobot**（保持运行）

---

## 📊 功能截图

### 主仪表盘
- 三基金并排显示
- 实时估值和折溢价
- 美化表格，突出折溢价率

### 折溢价查询
- 输入基金代码查询历史折溢价
- 交互式 Plotly 图表
- 分页数据表格
- CSV 导出功能

### 历史数据
- 查看保存的历史净值记录
- 数据导出功能

---

## 🔧 配置说明

### 基金配置

在 `funds/` 目录下添加新的基金类：

```python
from core.base import BaseFund

class FundXXXXXX(BaseFund):
    def __init__(self):
        super().__init__(
            fund_code="XXXXXX",
            fund_name="基金名称",
            # 其他配置...
        )
    
    def calculate(self) -> FundData:
        # 实现估值计算逻辑
        pass
```

### 定时任务配置

修改 `.github/workflows/scheduled_save.yml` 调整执行时间。

---

## 📝 数据说明

### CSV 文件字段

| 字段 | 说明 |
|------|------|
| 日期 | 交易日期 |
| 场内收盘价(CNY) | 场内交易收盘价 |
| 收盘估算净值(CNY) | 收盘时计算的估算净值 |
| 次日5点估算净值(CNY) | 次日5点的估算净值 |
| 最新基金净值(CNY) | 基金公司公布的净值 |
| Historical NAV(USD) | 历史净值(美元) |
| 净值溢价率(%) | 基于净值的溢价率 |
| 估算误差(%) | 估算净值与实际净值的误差 |

---

## ⚠️ 注意事项

1. **数据来源** - 数据来自 akshare 和公开数据源，仅供参考
2. **估值准确性** - 估值为计算值，可能与实际净值有偏差
3. **投资风险** - 本系统仅供学习研究，不构成投资建议
4. **时区设置** - 确保服务器时区为北京时间

---

## 📜 更新日志

### v2.0.0 (2026-03-11)
- ✨ 新增 Web 版本（Streamlit）
- ✨ 新增折溢价查询功能
- ✨ 新增交互式图表（Plotly）
- ✨ 新增 GitHub Actions 定时任务
- ✨ 新增部署到云端支持
- 🎨 美化表格布局
- 🐛 修复定时任务问题

### v1.0.0
- 🎉 初始版本
- ✨ 桌面应用基础功能
- ✨ 定时保存数据
- ✨ 历史净值管理

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
