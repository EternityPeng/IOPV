# 159687 实时估值计算

本项目用于计算和显示ETF 159687的实时估值和溢价/折价率。

## 功能特点

- 获取CSOP官网的历史NAV数据
- 计算NAV变化百分比
- 基于历史数据估算实时NAV
- 显示市场价格及其变化百分比
- 计算并显示溢价/折价率
- 支持手动刷新和自动刷新
- 提供GUI界面和命令行界面

## 目录结构

```
IOPV/
├── calculate_iopv.py  # 核心计算模块
├── iopv_gui.py        # GUI界面
├── iopv_cli.py        # 命令行界面
├── test_gui.py        # GUI测试脚本
├── official_nav_cache.json    # 官方NAV缓存
├── latest_nav_cache.json      # 最新NAV缓存
├── historical_nav_cache.json  # 历史NAV缓存
└── README.md          # 说明文档
```

## 依赖项

- Python 3.7+
- tkinter (GUI界面)
- requests
- lxml
- akshare
- DrissionPage (用于网页数据抓取)

## 安装依赖

```bash
pip install requests lxml akshare DrissionPage
```

## 使用方法

### GUI版本

```bash
python iopv_gui.py
```

- 启动时会自动刷新一次数据
- 每30秒自动刷新一次数据
- 点击"刷新数据"按钮可以手动刷新数据
- 溢价率显示为红色表示溢价，绿色表示折价
- 价格涨跌幅显示为红色表示上涨，绿色表示下跌

### 命令行版本

```bash
python iopv_cli.py
```

- 启动时会自动刷新一次数据
- 每30秒自动刷新一次数据
- 按 Ctrl+C 退出程序

## 数据来源

- 历史NAV数据：CSOP官网
- 实时NAV数据：CSOP官网的iframe页面
- 市场价格数据：新浪财经API
- 最新基金净值：akshare库

## 注意事项

- 首次运行时会抓取数据并缓存，可能需要较长时间
- 缓存数据每天更新一次，避免重复抓取
- 如果网络连接不稳定，可能会导致数据获取失败
- GUI版本需要在有图形界面的环境中运行
- 命令行版本可以在任何环境中运行

## 故障排除

- 如果GUI无法启动，尝试使用命令行版本
- 如果数据获取失败，检查网络连接
- 如果缓存文件损坏，删除缓存文件后重新运行
