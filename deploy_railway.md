# 🚀 Railway免费部署指南

## 📋 准备工作

### 1. 注册账号
- 访问 [Railway官网](https://railway.app/)
- 点击 "Start a New Project"
- 使用GitHub账号登录（推荐）

### 2. 准备代码
- 确保您的代码已推送到GitHub仓库
- 仓库可以是公开或私有的（Railway都支持）

## 🎯 部署步骤

### 步骤1：创建新项目
1. 登录Railway后，点击 "Start a New Project"
2. 选择 "Deploy from GitHub repo"
3. 选择您的GitHub仓库
4. 点击 "Deploy Now"

### 步骤2：自动配置
Railway会自动检测到这是一个Python项目，并：
- 自动安装依赖（从requirements.txt）
- 自动设置Python环境
- 自动配置启动命令

### 步骤3：环境变量设置
在项目设置中添加以下环境变量：
- `SECRET_KEY`: 生成一个随机字符串（至少32位）
- `FLASK_ENV`: production
- `PORT`: Railway会自动设置

### 步骤4：部署
1. Railway会自动开始构建和部署
2. 等待部署完成（通常2-5分钟）
3. 看到 "Deployed" 状态表示成功

## 🌐 访问您的应用

部署成功后，您会得到一个类似这样的URL：
```
https://qings-author-backend-production.up.railway.app
```

## 🔧 自定义域名（可选）

### 免费域名
Railway提供免费的 `.up.railway.app` 域名

### 自定义域名
1. 在项目设置中找到 "Domains"
2. 点击 "Generate Domain" 或添加自定义域名
3. 在域名提供商处配置DNS记录

## 📊 监控和维护

### 查看日志
- 在项目页面点击 "Deployments" 标签
- 选择最新的部署查看日志
- 实时监控应用运行状态

### 自动部署
- 每次推送到GitHub main分支
- Railway会自动重新部署
- 支持预览分支部署

### 性能监控
- 免费版包含基本监控
- 查看响应时间和资源使用
- 支持性能分析

## 💰 免费版限制

- **每月500小时**：足够大部分使用场景
- **512MB内存**：适合中小型应用
- **共享CPU**：响应速度良好
- **无休眠**：应用始终在线

## 🚨 注意事项

1. **数据库**：SQLite文件会在重启时重置，建议使用外部数据库
2. **文件存储**：本地文件不会持久化
3. **环境变量**：敏感信息通过环境变量设置
4. **日志**：定期清理日志避免占用空间

## 🔄 升级到付费版

当您的应用需要更多资源时：
- **Hobby**: $5/月，1GB内存，更好性能
- **Pro**: $20/月，2GB内存，专用资源
- **Team**: $50/月，4GB内存，团队协作

## 📞 获取帮助

- **官方文档**: [docs.railway.app](https://docs.railway.app/)
- **Discord社区**: [discord.gg/railway](https://discord.gg/railway)
- **GitHub**: [github.com/railwayapp](https://github.com/railwayapp)

## 🎉 部署完成后的下一步

1. **测试功能**：确保所有功能正常工作
2. **配置域名**：设置自定义域名（可选）
3. **监控性能**：关注应用响应时间
4. **备份数据**：定期备份重要数据
5. **用户反馈**：收集用户使用反馈

## 🔍 故障排除

### 常见问题

#### 构建失败
- 检查 `requirements.txt` 格式是否正确
- 确认Python版本兼容性
- 查看构建日志中的具体错误

#### 启动失败
- 检查启动命令是否正确
- 确认环境变量设置
- 查看应用日志

#### 应用无法访问
- 检查域名配置
- 确认部署状态为 "Deployed"
- 验证健康检查是否通过

### 获取支持
- 在Discord社区寻求帮助
- 查看官方文档
- 提交GitHub Issue
