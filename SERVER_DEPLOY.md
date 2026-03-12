# IOPV 基金估值系统 - 服务器部署教程

## 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                      您的服务器                              │
│                                                             │
│  ┌─────────────────┐     ┌─────────────────┐               │
│  │  Streamlit Web  │     │   Cron 定时任务  │               │
│  │  (端口 8501)    │     │   (15:00, 05:00)│               │
│  │                 │     │                 │               │
│  │  - 显示数据     │     │  - 自动保存数据 │               │
│  │  - 手动操作     │     │  - 更新缓存     │               │
│  └─────────────────┘     └─────────────────┘               │
│           │                      │                          │
│           └──────────┬───────────┘                          │
│                      ↓                                      │
│              ┌─────────────┐                                │
│              │   数据文件   │                                │
│              │  cache/     │                                │
│              └─────────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 一、服务器要求

### 最低配置
- CPU: 1核
- 内存: 1GB
- 硬盘: 10GB
- 系统: Ubuntu 20.04+ / Debian 10+ / CentOS 7+

### 推荐配置
- CPU: 2核
- 内存: 2GB
- 硬盘: 20GB

---

## 二、安装依赖

### 1. 更新系统

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. 安装 Python 3.10+

```bash
# Ubuntu 20.04+
sudo apt install python3.10 python3.10-venv python3-pip -y

# 或者使用 pyenv 安装
curl https://pyenv.run | bash
pyenv install 3.10.12
pyenv global 3.10.12
```

### 3. 安装 Chrome 浏览器（用于爬虫）

```bash
# 安装 Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install google-chrome-stable -y

# 安装依赖
sudo apt install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2
```

---

## 三、部署应用

### 1. 创建应用目录

```bash
sudo mkdir -p /opt/iopv
sudo chown $USER:$USER /opt/iopv
```

### 2. 克隆或上传代码

```bash
# 方式一：从 GitHub 克隆
cd /opt/iopv
git clone https://github.com/your-username/IOPV.git .

# 方式二：使用 scp 上传
# 在本地执行：
scp -r c:\Users\Eternity\Desktop\IOPV/* user@your-server:/opt/iopv/
```

### 3. 创建虚拟环境

```bash
cd /opt/iopv
python3 -m venv venv
source venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r web/requirements.txt
```

### 5. 测试运行

```bash
cd /opt/iopv/web
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

访问 `http://your-server-ip:8501` 确认正常运行。

---

## 四、配置 Systemd 服务

### 1. 创建服务文件

```bash
sudo nano /etc/systemd/system/iopv-web.service
```

### 2. 添加以下内容

```ini
[Unit]
Description=IOPV Fund Valuation System
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/opt/iopv/web
Environment="PATH=/opt/iopv/venv/bin"
ExecStart=/opt/iopv/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**注意**：将 `your-username` 替换为您的用户名。

### 3. 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable iopv-web
sudo systemctl start iopv-web
```

### 4. 检查状态

```bash
sudo systemctl status iopv-web
```

---

## 五、配置定时任务

### 1. 编辑 crontab

```bash
crontab -e
```

### 2. 添加定时任务

```bash
# IOPV 定时任务
# 15:00 收盘保存
0 15 * * 1-5 cd /opt/iopv/web && /opt/iopv/venv/bin/python nav_scheduler.py close >> /var/log/iopv_close.log 2>&1

# 05:00 次日保存
0 5 * * 1-5 cd /opt/iopv/web && /opt/iopv/venv/bin/python nav_scheduler.py next_day >> /var/log/iopv_next_day.log 2>&1
```

### 3. 创建日志目录

```bash
sudo touch /var/log/iopv_close.log /var/log/iopv_next_day.log
sudo chown $USER:$USER /var/log/iopv_*.log
```

---

## 六、配置防火墙

### Ubuntu/Debian (UFW)

```bash
sudo ufw allow 8501/tcp
sudo ufw enable
```

### CentOS/RHEL (firewalld)

```bash
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload
```

---

## 七、配置域名（可选）

### 使用 Nginx 反向代理

### 1. 安装 Nginx

```bash
sudo apt install nginx -y
```

### 2. 创建配置文件

```bash
sudo nano /etc/nginx/sites-available/iopv
```

### 3. 添加以下内容

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 4. 启用配置

```bash
sudo ln -s /etc/nginx/sites-available/iopv /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. 配置 SSL（可选）

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

## 八、常用命令

### 服务管理

```bash
# 启动服务
sudo systemctl start iopv-web

# 停止服务
sudo systemctl stop iopv-web

# 重启服务
sudo systemctl restart iopv-web

# 查看状态
sudo systemctl status iopv-web

# 查看日志
sudo journalctl -u iopv-web -f
```

### 手动执行任务

```bash
# 收盘保存
cd /opt/iopv/web && /opt/iopv/venv/bin/python nav_scheduler.py close

# 次日保存
cd /opt/iopv/web && /opt/iopv/venv/bin/python nav_scheduler.py next_day

# 测试所有任务
cd /opt/iopv/web && /opt/iopv/venv/bin/python nav_scheduler.py test
```

### 查看日志

```bash
# 查看收盘保存日志
tail -f /var/log/iopv_close.log

# 查看次日保存日志
tail -f /var/log/iopv_next_day.log
```

---

## 九、更新应用

```bash
cd /opt/iopv
git pull
source venv/bin/activate
pip install -r web/requirements.txt
sudo systemctl restart iopv-web
```

---

## 十、备份

### 创建备份脚本

```bash
nano /opt/iopv/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/iopv/backups"
DATE=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR

# 备份缓存数据
tar -czf $BACKUP_DIR/cache_$DATE.tar.gz /opt/iopv/cache/

# 删除30天前的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### 添加定时备份

```bash
crontab -e
```

```bash
# 每天凌晨3点备份
0 3 * * * /opt/iopv/backup.sh >> /var/log/iopv_backup.log 2>&1
```

---

## 十一、安全建议

### 1. 添加密码保护

在 Streamlit 应用中添加密码验证。

### 2. 限制访问 IP

```bash
# 只允许特定 IP 访问
sudo ufw allow from 192.168.1.0/24 to any port 8501
```

### 3. 定期更新系统

```bash
sudo apt update && sudo apt upgrade -y
```

---

## 十二、故障排除

### 问题1：服务无法启动

```bash
# 检查日志
sudo journalctl -u iopv-web -n 50

# 检查端口占用
sudo netstat -tlnp | grep 8501
```

### 问题2：定时任务不执行

```bash
# 检查 cron 服务
sudo systemctl status cron

# 检查日志
tail -f /var/log/iopv_close.log
```

### 问题3：Chrome 启动失败

```bash
# 检查 Chrome 是否安装
google-chrome --version

# 检查依赖
ldd $(which google-chrome)
```

---

## 完成！

现在您的服务器已经部署完成：

- ✅ Web 应用：`http://your-server-ip:8501`
- ✅ 定时任务：15:00 和 05:00 自动执行
- ✅ 日志记录：`/var/log/iopv_*.log`
- ✅ 自动重启：systemd 管理
