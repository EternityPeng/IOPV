# IOPV 基金估值系统 - Web 版本

基于 Streamlit 构建的 Web 应用，可以通过浏览器访问。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 本地运行

### 方式一：使用启动脚本
双击 `start.bat` 文件

### 方式二：命令行运行
```bash
streamlit run app.py
```

## 定时任务配置

### Windows 任务计划程序

1. 打开"任务计划程序"（搜索 `taskschd.msc`）
2. 创建基本任务
3. 设置触发器和操作

**收盘保存任务 (15:00)**:
- 触发器：每天 15:00
- 操作：启动程序 `C:\Users\Eternity\Desktop\IOPV\web\save_close.bat`

**次日保存任务 (05:00)**:
- 触发器：每天 05:00
- 操作：启动程序 `C:\Users\Eternity\Desktop\IOPV\web\save_next_day.bat`

### Linux Cron

编辑 crontab:
```bash
crontab -e
```

添加以下任务:
```bash
# 15:00 收盘保存 (周一到周五)
0 15 * * 1-5 cd /path/to/IOPV/web && ./save_close.sh >> /var/log/iopv_close.log 2>&1

# 05:00 次日保存 (周一到周五)
0 5 * * 1-5 cd /path/to/IOPV/web && ./save_next_day.sh >> /var/log/iopv_next_day.log 2>&1
```

### 手动测试

```bash
# 测试收盘保存
python nav_scheduler.py close

# 测试次日保存
python nav_scheduler.py next_day

# 保存所有数据
python nav_scheduler.py all

# 测试所有任务
python nav_scheduler.py test
```

## 服务器部署

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动服务
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### 3. 后台运行（Linux）
```bash
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
```

### 4. 使用 Docker（推荐）

创建 Dockerfile：
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

构建并运行：
```bash
docker build -t iopv-web .
docker run -p 8501:8501 iopv-web
```

## 访问地址

- 本地访问：http://localhost:8501
- 局域网访问：http://你的IP:8501

## 功能说明

### 主仪表盘
- 实时显示所有基金的估值数据
- 场内价格、估算净值、折溢价率等

### 折溢价查询
- 输入基金代码查询历史折溢价
- 交互式图表展示
- 数据导出功能

### 历史数据
- 查看基金历史净值记录
- 数据导出功能

## 配置文件

可以通过创建 `.streamlit/config.toml` 文件来自定义配置：

```toml
[server]
port = 8501
address = "0.0.0.0"

[theme]
primaryColor = "#4a90d9"
backgroundColor = "#1a1a2e"
secondaryBackgroundColor = "#2d2d44"
textColor = "#ffffff"
```

## 注意事项

1. 确保服务器可以访问外网（用于获取基金数据）
2. 建议使用 HTTPS 加密传输
3. 可以配置密码保护（参考 Streamlit 文档）
