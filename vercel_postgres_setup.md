# Vercel Postgres 数据库配置指南

## 🗄️ 项目已更新为使用PostgreSQL

您的项目现在已经完全配置为使用Vercel Postgres数据库，不再依赖SQLite。

## 📋 已完成的配置

### 1. 数据库配置 (`db_postgres.py`)
- ✅ 支持Vercel Postgres连接
- ✅ 自动SSL连接
- ✅ 完整的表结构迁移
- ✅ 数据迁移功能
- ✅ 默认管理员用户创建

### 2. 应用配置更新
- ✅ 更新了 `app.py` 使用PostgreSQL
- ✅ 添加了 `psycopg2-binary` 依赖
- ✅ 恢复了完整的应用功能

### 3. Vercel配置
- ✅ 恢复了使用 `api/index.py`
- ✅ 配置了环境变量

## 🚀 在Vercel中设置Postgres数据库

### 步骤1：在Vercel控制台添加Postgres数据库

1. **访问Vercel控制台**
   - 进入您的项目
   - 点击 "Storage" 标签

2. **创建Postgres数据库**
   - 点击 "Create Database"
   - 选择 "Postgres"
   - 选择免费套餐（如果可用）或付费套餐

3. **获取连接信息**
   - 复制 `DATABASE_URL` 连接字符串
   - 记录其他环境变量（如果需要）

### 步骤2：设置环境变量

在Vercel项目设置中添加以下环境变量：

**必需的环境变量：**
- `DATABASE_URL`: 您的Postgres连接字符串
- `SECRET_KEY`: 您的应用密钥（例如：`your-super-secret-key-12345`）
- `FLASK_ENV`: `production`

**可选的环境变量：**
- `ADMIN_PASSWORD`: 默认管理员密码（默认：`admin123`）

### 步骤3：部署应用

1. **推送代码到GitHub**
   ```bash
   git add .
   git commit -m "配置PostgreSQL数据库支持"
   git push origin master
   ```

2. **等待Vercel自动部署**
   - Vercel会自动检测到代码更改
   - 开始构建和部署过程

3. **检查部署状态**
   - 查看Vercel部署日志
   - 确认没有错误

## 🧪 测试部署

### 1. 基础功能测试
访问以下URL测试应用：
- `https://your-app.vercel.app/` - 主页面
- `https://your-app.vercel.app/health` - 健康检查
- `https://your-app.vercel.app/vercel-info` - Vercel环境信息

### 2. 数据库功能测试
- 访问登录页面
- 使用默认管理员账户登录：
  - 用户名：`admin`
  - 密码：`admin123`（或您设置的ADMIN_PASSWORD）

### 3. 静态文件测试
- 访问 `https://your-app.vercel.app/test-static`
- 检查页面样式是否正常加载

## 📊 数据库表结构

应用会自动创建以下表：

### users（用户表）
- `id`: 主键
- `username`: 用户名（唯一）
- `password_hash`: 密码哈希
- `role`: 角色（admin/author）

### books（书籍表）
- `id`: 主键
- `title`: 书名
- `author_id`: 作者ID
- `pen_name`: 笔名
- `contract_type`: 合同类型（保底/买断）
- `buyout_amount`: 买断金额
- `created_at`: 创建时间

### royalties（稿费表）
- `id`: 主键
- `author_id`: 作者ID
- `month`: 月份
- `amount`: 金额
- `book_id`: 书籍ID

### applications（申请表）
- `id`: 主键
- `author_id`: 作者ID
- `title`: 书名
- `pen_name`: 笔名
- `contract_type`: 合同类型
- `status`: 状态（pending/approved/rejected）
- `reject_reason`: 拒绝原因
- `created_at`: 创建时间
- `processed_at`: 处理时间

### notifications（通知表）
- `id`: 主键
- `recipient_id`: 接收者ID
- `message`: 消息内容
- `created_at`: 创建时间
- `is_read`: 是否已读

## 🔧 故障排除

### 问题1：数据库连接失败
**解决方案：**
- 检查 `DATABASE_URL` 环境变量是否正确设置
- 确认Postgres数据库已创建并运行
- 检查网络连接

### 问题2：表创建失败
**解决方案：**
- 检查数据库权限
- 查看应用日志中的具体错误信息
- 确认Postgres版本兼容性

### 问题3：数据迁移失败
**解决方案：**
- 检查SQLite文件是否存在
- 查看迁移日志
- 手动验证数据完整性

## 📈 性能优化建议

### 1. 连接池管理
- 使用连接池避免频繁创建连接
- 设置合适的连接超时时间

### 2. 索引优化
- 为常用查询字段添加索引
- 定期分析查询性能

### 3. 数据备份
- 定期备份数据库
- 设置自动备份策略

## 🎯 预期结果

配置完成后，您应该看到：
- ✅ 应用成功部署到Vercel
- ✅ 数据库连接正常
- ✅ 所有功能正常工作
- ✅ 静态文件正常加载
- ✅ 用户认证系统正常

---

**现在您的应用已经完全支持Vercel Postgres数据库，可以正常部署和运行了！**
