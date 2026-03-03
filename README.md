# 159687 ETF 实时估值计算系统

一个支持多基金扩展的实时估值计算系统，采用插件式架构设计。

## 📁 项目结构

```
IOPV/
├── core/                          # 核心框架
│   ├── __init__.py                # 核心模块导出
│   ├── base.py                    # 基类定义（BaseFund, FundData）
│   ├── gui_framework.py           # GUI框架
│   └── utils.py                   # 工具函数
│
├── funds/                         # 基金模块（插件式）
│   ├── __init__.py                # 基金列表管理
│   └── fund_159687.py             # 159687基金模块
│
├── cache/                         # 缓存数据
│   └── 159687/                    # 按基金代码分类
│
├── output/                        # 输出文件
│   └── 159687/                    # 按基金代码分类
│
├── v1_legacy/                     # 旧版本（保留作为蓝本）
│   ├── README.md                  # 旧版本使用说明
│   ├── calculate_iopv.py          # 旧版本核心计算模块
│   ├── iopv_gui.py                # 旧版本GUI
│   └── ...
│
├── main.py                        # 主程序入口
└── README.md                      # 本文件
```

## 🚀 使用方法

### 1. 列出所有可用基金

```bash
python main.py --list
```

### 2. 命令行模式（单次获取）

```bash
python main.py --cli 159687
```

### 3. GUI模式（实时监控）

```bash
python main.py
```

## 🔧 添加新基金

只需3步：

### 步骤1：创建基金模块

在 `funds/` 目录下创建新文件 `fund_xxxxx.py`：

```python
from core.base import BaseFund, FundData

class FundXXXXX(BaseFund):
    @property
    def fund_code(self) -> str:
        return "xxxxx"
  
    @property
    def fund_name(self) -> str:
        return "基金名称"
  
    @property
    def description(self) -> str:
        return "基金描述"
  
    @property
    def update_interval(self) -> int:
        return 30  # 刷新间隔（秒）
  
    def calculate(self) -> FundData:
        """实现你的估值逻辑"""
        # 可以使用：
        # - API调用
        # - 网页爬虫
        # - 股票组合计算
        # - 任何自定义方法
      
        return FundData(
            fund_code=self.fund_code,
            fund_name=self.fund_name,
            market_price=...,
            estimated_nav=...,
            # ...
        )
```

### 步骤2：注册基金

在 `funds/__init__.py` 中添加：

```python
from .fund_xxxxx import FundXXXXX

__all__ = ['Fund159687', 'FundXXXXX']
AVAILABLE_FUNDS = [Fund159687, FundXXXXX]
```

### 步骤3：创建缓存目录

```bash
mkdir cache\xxxxx output\xxxxx
```

## 📊 已支持的基金

| 基金代码 | 基金名称                    | 数据来源                     |
| -------- | --------------------------- | ---------------------------- |
| 159687   | 南方东英富时亚太低碳精选ETF | ICE API + 新浪财经 + akshare |

## 📦 依赖安装

```bash
pip install requests lxml akshare DrissionPage
```

## 📝 旧版本

如需使用旧版本（单基金版本），请查看 `v1_legacy/` 目录：

```bash
cd v1_legacy
python calculate_iopv.py  # 命令行模式
python iopv_gui.py        # GUI模式
```

## ✅ 功能特点

| 特性          | 说明                       |
| ------------- | -------------------------- |
| 🔌 插件式架构 | 每个基金独立模块，互不影响 |
| 📊 统一接口   | 所有基金遵循相同的基类规范 |
| 🎯 易于扩展   | 添加新基金只需创建新模块   |
| 📁 文件管理   | 缓存和输出按基金代码分类   |
| 🖥️ 多种模式 | 支持GUI、命令行、列表查询  |
| 💾 数据保存   | 关闭GUI时自动保存数据      |
| 🔄 自动刷新   | GUI支持自动刷新功能        |

## 📅 版本历史

- **V1**: 单基金版本（保留在 `v1_legacy/` 目录）
- **V2**: 插件式架构，支持多基金扩展（当前版本）

---

**最后更新**: 2026-03-03
