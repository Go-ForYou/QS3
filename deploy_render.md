# 🚀 Render免费部署指南

## 📋 准备工作

### 1. 注册账号
- 访问 [Render官网](https://render.com/)
- 点击 "Get Started for Free"
- 使用GitHub账号登录（推荐）

### 2. 准备代码
- 确保您的代码已推送到GitHub仓库
- 仓库必须是公开的（免费版要求）

## 🎯 部署步骤

### 步骤1：创建新服务
1. 登录Render后，点击 "New +"
2. 选择 "Web Service"
3. 点击 "Connect a repository"
4. 选择您的GitHub仓库

### 步骤2：配置服务
- **Name**: `qings-author-backend` (或您喜欢的名称)
- **Environment**: `Python 3`
- **Region**: 选择离您最近的地区
- **Branch**: `main` 或 `master`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

### 步骤3：环境变量设置
Render会自动设置以下环境变量：
- `PORT`: 自动分配
- `SECRET_KEY`: 自动生成
- `FLASK_ENV`: production

### 步骤4：部署
1. 点击 "Create Web Service"
2. 等待构建完成（通常2-5分钟）
3. 看到 "Live" 状态表示部署成功

## 🌐 访问您的应用

部署成功后，您会得到一个类似这样的URL：
```
https://qings-author-backend.onrender.com
```

## 🔧 自定义域名（可选）

### 免费域名
Render提供免费的 `.onrender.com` 域名

### 自定义域名
1. 在服务设置中找到 "Custom Domains"
2. 添加您的域名
3. 在域名提供商处配置DNS记录

## 📊 监控和维护

### 查看日志
- 在服务页面点击 "Logs" 标签
- 实时查看应用运行状态

### 自动部署
- 每次推送到GitHub main分支
- Render会自动重新部署

### 性能监控
- 免费版包含基本监控
- 查看响应时间和错误率

## 💰 免费版限制

- **每月750小时**：足够24/7运行
- **512MB内存**：适合中小型应用
- **共享CPU**：响应速度可能较慢
- **无休眠**：应用始终在线

## 🚨 注意事项

1. **数据库**：SQLite文件会在重启时重置，建议使用外部数据库
2. **文件存储**：本地文件不会持久化
3. **环境变量**：敏感信息通过环境变量设置
4. **日志**：定期清理日志避免占用空间

## 🔄 升级到付费版

当您的应用需要更多资源时：
- **Starter**: $7/月，1GB内存，专用CPU
- **Standard**: $25/月，2GB内存，更好性能
- **Pro**: $50/月，4GB内存，企业级支持

## 📞 获取帮助

- **官方文档**: [docs.render.com](https://docs.render.com/)
- **社区支持**: [community.render.com](https://community.render.com/)
- **状态页面**: [status.render.com](https://status.render.com/)

## 🎉 部署完成后的下一步

1. **测试功能**：确保所有功能正常工作
2. **配置域名**：设置自定义域名（可选）
3. **监控性能**：关注应用响应时间
4. **备份数据**：定期备份重要数据
5. **用户反馈**：收集用户使用反馈
