# Railway部署指南 - 国内访问稳定

## 🚀 为什么选择Railway？

- ✅ **国内访问稳定** - 无需VPN即可访问
- ✅ **免费额度充足** - 每月500小时免费
- ✅ **支持PostgreSQL** - 内置数据库服务
- ✅ **自动部署** - 连接GitHub自动部署
- ✅ **简单易用** - 配置简单，部署快速

## 📋 部署步骤

### 步骤1：准备项目文件

确保项目包含以下文件：
- `app.py` - 主应用文件
- `requirements.txt` - Python依赖
- `railway.json` - Railway配置
- `Procfile` - 启动命令
- `db_hybrid.py` - 数据库配置
- `db_postgres.py` - PostgreSQL配置

### 步骤2：创建Railway账号

1. 访问 [https://railway.app](https://railway.app)
2. 点击 "Login" 使用GitHub账号登录
3. 授权Railway访问您的GitHub仓库

### 步骤3：部署项目

1. **创建新项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择您的仓库 `qingS`

2. **配置环境变量**
   在Railway Dashboard中添加以下环境变量：
   ```
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=production
   VERCEL=1
   ```

3. **添加PostgreSQL数据库**
   - 在项目页面点击 "New"
   - 选择 "Database" → "PostgreSQL"
   - Railway会自动创建数据库并设置 `DATABASE_URL`

### 步骤4：获取部署URL

部署完成后，Railway会提供一个类似这样的URL：
```
https://your-project-name.railway.app
```

## 🔧 配置说明

### railway.json 配置
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python app.py",
    "healthcheckPath": "/",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Procfile 配置
```
web: python app.py
```

## 🎯 优势对比

| 特性 | Vercel | Railway |
|------|--------|---------|
| 国内访问 | ❌ 需要VPN | ✅ 直接访问 |
| 免费额度 | 有限 | 500小时/月 |
| 数据库 | 需要外部 | 内置PostgreSQL |
| 部署速度 | 快 | 中等 |
| 稳定性 | 高 | 高 |

## 🚀 快速部署命令

如果您想立即部署到Railway：

```bash
# 1. 安装Railway CLI
npm install -g @railway/cli

# 2. 登录Railway
railway login

# 3. 初始化项目
railway init

# 4. 部署
railway up
```

## 📱 测试访问

部署完成后：
1. 访问Railway提供的URL
2. 测试登录功能
3. 让朋友从不同网络测试访问

## 🔄 从Vercel迁移

如果您想从Vercel迁移到Railway：

1. **保持GitHub仓库同步**
2. **在Railway中重新部署**
3. **更新数据库连接**
4. **测试所有功能**

## 💡 额外建议

### 1. 使用自定义域名
Railway支持自定义域名，可以绑定您自己的域名：
- 在Railway Dashboard中添加自定义域名
- 配置DNS记录指向Railway

### 2. 监控和日志
- Railway提供实时日志查看
- 可以监控应用性能和错误

### 3. 备份策略
- 定期备份数据库
- 保持代码仓库同步

## 🎉 预期结果

使用Railway部署后：
- ✅ 国内用户无需VPN即可访问
- ✅ 访问速度更快
- ✅ 部署更稳定
- ✅ 维护更简单

## 📞 需要帮助？

如果在部署过程中遇到问题：
1. 检查Railway Dashboard中的日志
2. 确认环境变量配置正确
3. 验证数据库连接正常

Railway是解决国内访问问题的最佳选择！🚀
