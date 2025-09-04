# Vercel部署指南

## 环境变量设置

在Vercel控制台中设置以下环境变量：

1. 登录Vercel控制台
2. 选择您的项目
3. 进入 Settings > Environment Variables
4. 添加以下变量：

```
SECRET_KEY = your-secret-key-here-change-this-in-production
FLASK_ENV = production
```

## 部署步骤

1. 确保所有文件已提交到Git仓库
2. 在Vercel中连接您的Git仓库
3. 部署会自动开始
4. 等待部署完成

## 测试部署

部署完成后，测试以下URL：

- `https://your-domain.vercel.app/` - 应该重定向到登录页面
- `https://your-domain.vercel.app/health` - 应该返回健康检查状态
- `https://your-domain.vercel.app/login` - 应该显示登录表单

## 常见问题

### 404错误
- 检查vercel.json配置是否正确
- 确保api/index.py文件存在
- 检查环境变量是否设置

### 静态文件不加载
- 检查static文件夹是否在根目录
- 确保CSS文件路径正确

### 数据库错误
- 确保SQLite文件权限正确
- 检查数据库初始化是否成功
