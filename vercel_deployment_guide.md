# Vercel 部署指南

## 项目概述
这是一个Flask应用，用于作者签约管理系统。项目已经配置好Vercel部署所需的文件。

## 部署前准备

### 1. 环境变量配置
在Vercel控制台中设置以下环境变量：

- `SECRET_KEY`: Flask应用的密钥（用于session加密）
- `FLASK_ENV`: 设置为 `production`

### 2. 项目结构
```
qingS/
├── api/
│   └── index.py          # Vercel入口文件
├── app.py                # Flask主应用
├── db.py                 # 数据库配置
├── requirements.txt      # Python依赖
├── vercel.json          # Vercel配置
├── static/              # 静态文件
└── templates/           # HTML模板
```

## 部署步骤

### 方法一：通过Vercel CLI（推荐）

1. **安装Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **登录Vercel**
   ```bash
   vercel login
   ```

3. **在项目目录中部署**
   ```bash
   cd C:\Users\darling\Desktop\qingS
   vercel
   ```

4. **设置环境变量**
   ```bash
   vercel env add SECRET_KEY
   # 输入一个强密钥，例如：your-super-secret-key-here-12345
   
   vercel env add FLASK_ENV
   # 输入：production
   ```

5. **重新部署**
   ```bash
   vercel --prod
   ```

### 方法二：通过Vercel网站

1. **访问 [vercel.com](https://vercel.com)**
2. **连接GitHub/GitLab/Bitbucket**
3. **导入项目**
   - 选择您的仓库
   - 框架预设选择 "Other"
   - 构建命令留空
   - 输出目录留空
4. **设置环境变量**
   - 在项目设置中添加环境变量
5. **部署**

## 配置说明

### vercel.json 配置
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/static/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/api/index.py"
    }
  ],
  "env": {
    "FLASK_ENV": "production",
    "SECRET_KEY": "@secret_key"
  },
  "functions": {
    "api/index.py": {
      "maxDuration": 30
    }
  }
}
```

### api/index.py 入口文件
```python
from app import app

# Vercel需要这个文件作为入口点
# 这个文件会被Vercel自动识别为API路由的入口
```

## 数据库注意事项

⚠️ **重要提醒**：
- 当前项目使用SQLite数据库（`data.sqlite3`）
- Vercel是无服务器环境，文件系统是只读的
- **SQLite数据库在Vercel上无法正常工作**

### 解决方案

1. **使用外部数据库**（推荐）
   - PostgreSQL（推荐使用Vercel Postgres）
   - MySQL
   - 或其他云数据库服务

2. **修改数据库配置**
   - 更新 `db.py` 文件以使用外部数据库
   - 安装相应的数据库驱动

## 部署后测试

1. **访问健康检查端点**
   ```
   https://your-app.vercel.app/health
   ```

2. **测试主要功能**
   - 访问首页
   - 测试登录/注册
   - 检查静态文件加载

## 常见问题

### 1. 数据库连接错误
- 确保使用外部数据库服务
- 检查数据库连接字符串

### 2. 静态文件404
- 检查 `vercel.json` 中的路由配置
- 确保静态文件路径正确

### 3. 环境变量未生效
- 在Vercel控制台检查环境变量设置
- 重新部署应用

## 性能优化建议

1. **启用CDN**
   - Vercel自动提供全球CDN
   - 静态文件会自动优化

2. **数据库连接池**
   - 使用连接池管理数据库连接
   - 避免频繁创建/关闭连接

3. **缓存策略**
   - 设置适当的缓存头
   - 使用Vercel的Edge Functions

## 监控和维护

1. **查看日志**
   ```bash
   vercel logs
   ```

2. **监控性能**
   - 使用Vercel Analytics
   - 监控函数执行时间

3. **定期更新**
   - 更新依赖包
   - 检查安全更新

## 联系支持

如果遇到问题，可以：
1. 查看Vercel文档
2. 在Vercel社区寻求帮助
3. 检查项目日志

---

**部署完成后，您的应用将在 `https://your-app-name.vercel.app` 上运行**