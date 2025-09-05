# 数据库迁移指南

## 问题说明

⚠️ **重要提醒**：当前项目使用SQLite数据库，但Vercel是无服务器环境，文件系统是只读的，因此SQLite数据库无法在Vercel上正常工作。

## 解决方案

### 方案一：使用Vercel Postgres（推荐）

1. **在Vercel控制台添加Postgres数据库**
   - 进入项目设置
   - 选择 "Storage" 标签
   - 点击 "Create Database"
   - 选择 "Postgres"

2. **获取数据库连接信息**
   - 复制连接字符串
   - 记录数据库URL

3. **修改数据库配置**

创建新文件 `db_postgres.py`：

```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

def get_db_url():
    """获取数据库连接URL"""
    return os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/dbname')

def get_db():
    """获取数据库连接"""
    url = get_db_url()
    parsed = urlparse(url)
    
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password,
        sslmode='require'
    )
    conn.autocommit = True
    return conn

def init_db():
    """初始化数据库表"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # 创建用户表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL CHECK(role IN ('admin','author'))
                );
            """)
            
            # 创建书籍表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    author_id INTEGER NOT NULL,
                    pen_name VARCHAR(100),
                    contract_type VARCHAR(20) CHECK(contract_type IN ('保底','买断')),
                    buyout_amount DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(author_id) REFERENCES users(id)
                );
            """)
            
            # 创建稿费表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS royalties (
                    id SERIAL PRIMARY KEY,
                    author_id INTEGER NOT NULL,
                    month VARCHAR(7) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL DEFAULT 0,
                    book_id INTEGER,
                    FOREIGN KEY(author_id) REFERENCES users(id),
                    FOREIGN KEY(book_id) REFERENCES books(id),
                    UNIQUE(book_id, month) WHERE book_id IS NOT NULL,
                    UNIQUE(author_id, month) WHERE book_id IS NULL
                );
            """)
            
            # 创建申请表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id SERIAL PRIMARY KEY,
                    author_id INTEGER NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    pen_name VARCHAR(100) NOT NULL,
                    contract_type VARCHAR(20) NOT NULL CHECK(contract_type IN ('保底','买断')),
                    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
                    reject_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    FOREIGN KEY(author_id) REFERENCES users(id)
                );
            """)
            
            # 创建通知表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    recipient_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN NOT NULL DEFAULT FALSE,
                    FOREIGN KEY(recipient_id) REFERENCES users(id)
                );
            """)
```

4. **更新requirements.txt**
```
Flask==3.0.2
python-dotenv==1.0.1
gunicorn==21.2.0
Werkzeug==3.0.1
psycopg2-binary==2.9.9
```

5. **修改app.py**
```python
# 将
from db import get_db, init_db

# 改为
from db_postgres import get_db, init_db
```

6. **设置环境变量**
在Vercel控制台添加：
- `DATABASE_URL`: 您的Postgres连接字符串

### 方案二：使用其他云数据库

#### 使用PlanetScale (MySQL)
1. 注册PlanetScale账户
2. 创建数据库
3. 获取连接字符串
4. 修改数据库配置

#### 使用Supabase (PostgreSQL)
1. 注册Supabase账户
2. 创建项目
3. 获取连接字符串
4. 修改数据库配置

## 数据迁移

如果您已有SQLite数据需要迁移：

1. **导出SQLite数据**
```python
import sqlite3
import csv

# 导出用户数据
conn = sqlite3.connect('data.sqlite3')
cursor = conn.cursor()

# 导出各个表的数据
tables = ['users', 'books', 'royalties', 'applications', 'notifications']
for table in tables:
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    
    with open(f'{table}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

conn.close()
```

2. **导入到新数据库**
```python
import psycopg2
import csv

# 连接到Postgres
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# 导入数据
tables = ['users', 'books', 'royalties', 'applications', 'notifications']
for table in tables:
    with open(f'{table}.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            # 根据表结构插入数据
            # 这里需要根据具体表结构调整
            pass

conn.commit()
conn.close()
```

## 测试数据库连接

创建测试文件 `test_db.py`：

```python
from db_postgres import get_db, init_db

try:
    # 测试连接
    conn = get_db()
    print("数据库连接成功！")
    
    # 初始化表
    init_db()
    print("数据库表初始化成功！")
    
    conn.close()
except Exception as e:
    print(f"数据库连接失败: {e}")
```

## 注意事项

1. **连接池管理**
   - 使用连接池避免频繁创建连接
   - 及时关闭连接释放资源

2. **SSL连接**
   - 云数据库通常需要SSL连接
   - 确保连接字符串包含SSL参数

3. **环境变量安全**
   - 不要在代码中硬编码数据库密码
   - 使用环境变量存储敏感信息

4. **备份策略**
   - 定期备份数据库
   - 设置自动备份

---

**完成数据库迁移后，您的应用就可以在Vercel上正常运行了！**
