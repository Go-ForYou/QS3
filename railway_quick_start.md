# 🚀 Railway快速部署指南

## ⚡ 5分钟快速部署

### 1️⃣ 准备工作（1分钟）
- 确保代码已推送到GitHub
- 访问 [railway.app](https://railway.app/)
- 使用GitHub账号登录

### 2️⃣ 创建项目（2分钟）
1. 点击 "Start a New Project"
2. 选择 "Deploy from GitHub repo"
3. 选择您的仓库
4. 点击 "Deploy Now"

### 3️⃣ 配置环境变量（1分钟）
在项目设置中添加：
```
SECRET_KEY=your-very-long-random-secret-key-here
FLASK_ENV=production
```

### 4️⃣ 等待部署（1分钟）
- Railway自动构建和部署
- 看到 "Deployed" 状态即可

## 🔑 生成SECRET_KEY

### 方法1：在线生成器
访问 [randomkeygen.com](https://randomkeygen.com/) 生成32位随机字符串

### 方法2：Python生成
```python
import secrets
print(secrets.token_hex(32))
```

### 方法3：命令行生成
```bash
# Linux/Mac
openssl rand -hex 32

# Windows PowerShell
[System.Web.Security.Membership]::GeneratePassword(32,0)
```

## 🌐 获取访问地址

部署成功后，您会看到：
- **免费域名**: `https://your-app-name-production.up.railway.app`
- **自定义域名**: 可在设置中添加

## 🧪 快速测试

### 基础功能测试
1. 访问部署地址
2. 测试用户注册
3. 测试用户登录
4. 测试作者申请功能

### 管理员功能测试
1. 使用管理员账号登录
2. 测试申请审核
3. 测试稿费设置

## 🚨 常见问题解决

### 部署失败
- 检查 `requirements.txt` 格式
- 确认Python版本兼容
- 查看构建日志

### 应用无法启动
- 检查环境变量设置
- 确认启动命令正确
- 查看应用日志

### 功能异常
- 检查数据库连接
- 验证文件权限
- 确认配置正确

## 📞 获取帮助

- **Discord社区**: [discord.gg/railway](https://discord.gg/railway)
- **官方文档**: [docs.railway.app](https://docs.railway.app/)
- **GitHub**: [github.com/railwayapp](https://github.com/railwayapp)

## 🎯 下一步计划

### 短期目标
- [ ] 完成基础部署
- [ ] 测试所有功能
- [ ] 配置自定义域名

### 长期规划
- [ ] 优化性能
- [ ] 添加监控
- [ ] 用户反馈收集
- [ ] 功能迭代更新

---

**现在就开始部署吧！** 🚀

如果遇到任何问题，随时在Discord社区寻求帮助！
