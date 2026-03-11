# IOPV 基金估值系统 - 部署教程

本教程将指导您如何将系统部署到 **Streamlit Cloud**（免费），并使用 **GitHub Actions** 实现定时任务。

---

## 📋 部署架构

```
┌─────────────────┐     ┌─────────────────┐
│  Streamlit Cloud │     │  GitHub Actions  │
│  (Web界面)       │     │  (定时任务)      │
│                 │     │                 │
│  - 查看估值      │     │  - 15:00 收盘保存│
│  - 查询折溢价    │     │  - 05:00 次日保存│
│  - 手动保存      │     │  - 自动提交数据  │
└─────────────────┘     └─────────────────┘
         ↓                       ↓
    浏览器访问              自动保存到
    随时查看                GitHub 仓库
```

---

## 🚀 第一步：上传代码到 GitHub

### 1.1 创建 GitHub 账号

如果您还没有 GitHub 账号：
1. 访问 https://github.com
2. 点击 "Sign up" 注册
3. 完成邮箱验证

### 1.2 创建新仓库

1. 登录 GitHub
2. 点击右上角 "+" → "New repository"
3. 填写信息：
   - Repository name: `IOPV`
   - Description: `基金估值系统`
   - 选择 **Public**（公开，免费部署必须）
4. 点击 "Create repository"

### 1.3 上传代码

**方式一：使用 GitHub Desktop（推荐新手）**

1. 下载安装 [GitHub Desktop](https://desktop.github.com/)
2. 登录 GitHub 账号
3. File → Add local repository → 选择 `IOPV` 文件夹
4. Publish repository → 选择刚创建的仓库 → Publish

**方式二：使用命令行**

```bash
cd c:\Users\Eternity\Desktop\IOPV

git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的用户名/IOPV.git
git push -u origin main
```

---

## 🌐 第二步：部署到 Streamlit Cloud

### 2.1 注册 Streamlit Cloud

1. 访问 https://streamlit.io/cloud
2. 点击 "Sign up" 用 GitHub 账号登录
3. 授权 Streamlit 访问您的 GitHub

### 2.2 创建应用

1. 点击 "New app"
2. 填写信息：
   - Repository: 选择 `IOPV` 仓库
   - Branch: `main`
   - Main file path: `web/app.py`
3. 点击 "Deploy!"

### 2.3 等待部署

- 首次部署需要 2-5 分钟
- 部署成功后会显示类似 `https://iopv-xxx.streamlit.app` 的网址

---

## ⏰ 第三步：配置 GitHub Actions 定时任务

GitHub Actions 已经配置好了，但需要启用：

### 3.1 启用 GitHub Actions

1. 进入 GitHub 仓库页面
2. 点击 "Actions" 标签
3. 如果看到提示，点击 "I understand my workflows, go ahead and enable them"

### 3.2 测试定时任务

1. 在 Actions 页面，点击左侧 "Scheduled NAV Data Save"
2. 点击右侧 "Run workflow" → "Run workflow"
3. 等待执行完成，查看日志

### 3.3 定时任务说明

| 任务 | 北京时间 | UTC时间 | 说明 |
|------|---------|---------|------|
| 收盘保存 | 15:00 | 07:00 | 周一到周五 |
| 次日保存 | 05:00 | 21:00 | 周一到周五 |

---

## 📁 第四步：查看保存的数据

### 4.1 数据位置

定时任务会将数据保存到 `cache/` 目录，并自动提交到 GitHub 仓库。

### 4.2 查看方式

1. 进入 GitHub 仓库
2. 点击 `cache/` 文件夹
3. 选择基金代码文件夹
4. 查看 `nav_history.csv` 文件

---

## ⚙️ 高级配置

### 添加密码保护（可选）

如果不想让其他人访问您的应用，可以添加密码保护：

1. 在 Streamlit Cloud 中设置密钥：
   - 进入应用设置 → Secrets
   - 添加：`PASSWORD = "您的密码"`

2. 代码中会自动读取密码进行验证

---

## 🔧 常见问题

### Q1: Streamlit 应用显示 "Sleeping"

**原因**：免费版在不活动后会休眠

**解决**：
- 访问应用网址会自动唤醒
- 或使用定时服务（如 UptimeRobot）定期访问

### Q2: GitHub Actions 没有执行

**检查**：
1. 仓库是否为 Public
2. Actions 是否已启用
3. 查看 Actions 页面的错误日志

### Q3: 数据没有保存

**检查**：
1. 查看 Actions 执行日志
2. 确认 `cache/` 目录权限

---

## 📞 需要帮助？

如果遇到问题，可以：
1. 查看 GitHub Actions 的执行日志
2. 查看 Streamlit Cloud 的应用日志
3. 在 GitHub 上创建 Issue

---

## ✅ 部署完成清单

- [ ] 代码已上传到 GitHub
- [ ] Streamlit Cloud 应用已创建
- [ ] GitHub Actions 已启用
- [ ] 手动测试 Actions 成功
- [ ] 可以正常访问 Web 应用

恭喜！您的基金估值系统已经成功部署！🎉
