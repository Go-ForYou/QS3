import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
from contextlib import contextmanager

def get_db_url():
    """获取数据库连接URL"""
    # 优先使用Vercel Postgres的DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    # 如果没有DATABASE_URL，尝试从Vercel Postgres环境变量构建
    host = os.getenv('POSTGRES_HOST')
    port = os.getenv('POSTGRES_PORT', '5432')
    database = os.getenv('POSTGRES_DATABASE')
    username = os.getenv('POSTGRES_USERNAME')
    password = os.getenv('POSTGRES_PASSWORD')
    
    if all([host, database, username, password]):
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    # 如果都没有，返回None（将使用内存数据库）
    return None

@contextmanager
def get_db():
    """获取数据库连接"""
    db_url = get_db_url()
    
    if not db_url:
        # 如果没有数据库URL，返回None（用于测试环境）
        yield None
        return
    
    try:
        # 解析数据库URL
        parsed = urlparse(db_url)
        
        # 创建连接
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # 移除开头的 '/'
            user=parsed.username,
            password=parsed.password,
            sslmode='require'  # Vercel Postgres需要SSL
        )
        
        # 设置自动提交
        conn.autocommit = True
        
        try:
            yield conn
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Database connection error: {e}")
        # 如果连接失败，返回None
        yield None

def init_db():
    """初始化数据库表"""
    with get_db() as conn:
        if conn is None:
            print("No database connection available, skipping initialization")
            return
        
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
                    reviewer_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    FOREIGN KEY(author_id) REFERENCES users(id),
                    FOREIGN KEY(reviewer_id) REFERENCES users(id)
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
            
            # 创建索引
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_royalties_book_month 
                ON royalties(book_id, month) WHERE book_id IS NOT NULL;
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_royalties_author_month_null 
                ON royalties(author_id, month) WHERE book_id IS NULL;
            """)
            
            print("Database tables initialized successfully")

def seed_admin_user():
    """创建默认管理员用户"""
    from werkzeug.security import generate_password_hash
    
    with get_db() as conn:
        if conn is None:
            print("No database connection available, skipping admin user creation")
            return
        
        with conn.cursor() as cur:
            # 检查是否已有管理员用户
            cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admin_count = cur.fetchone()[0]
            
            if admin_count == 0:
                # 创建默认管理员用户
                admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
                cur.execute("""
                    INSERT INTO users (username, password_hash, role) 
                    VALUES (%s, %s, %s)
                """, ('admin', generate_password_hash(admin_password), 'admin'))
                
                print("Default admin user created: admin / admin123")
            else:
                print("Admin user already exists")

# 数据库迁移函数（从SQLite到PostgreSQL）
def migrate_from_sqlite():
    """从SQLite迁移数据到PostgreSQL（如果存在SQLite文件）"""
    import sqlite3
    
    sqlite_path = os.path.join(os.path.dirname(__file__), "data.sqlite3")
    
    if not os.path.exists(sqlite_path):
        print("No SQLite file found, skipping migration")
        return
    
    print("Starting migration from SQLite to PostgreSQL...")
    
    # 连接SQLite数据库
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    
    with get_db() as pg_conn:
        if pg_conn is None:
            print("No PostgreSQL connection available, skipping migration")
            return
        
        with pg_conn.cursor() as pg_cur:
            # 迁移用户数据
            sqlite_cur = sqlite_conn.execute("SELECT * FROM users")
            for row in sqlite_cur.fetchall():
                try:
                    pg_cur.execute("""
                        INSERT INTO users (id, username, password_hash, role) 
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (row['id'], row['username'], row['password_hash'], row['role']))
                except Exception as e:
                    print(f"Error migrating user {row['username']}: {e}")
            
            # 迁移书籍数据
            sqlite_cur = sqlite_conn.execute("SELECT * FROM books")
            for row in sqlite_cur.fetchall():
                try:
                    pg_cur.execute("""
                        INSERT INTO books (id, title, author_id, pen_name, contract_type, buyout_amount, created_at) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (row['id'], row['title'], row['author_id'], row['pen_name'], 
                          row['contract_type'], row['buyout_amount'], row['created_at']))
                except Exception as e:
                    print(f"Error migrating book {row['title']}: {e}")
            
            # 迁移稿费数据
            sqlite_cur = sqlite_conn.execute("SELECT * FROM royalties")
            for row in sqlite_cur.fetchall():
                try:
                    pg_cur.execute("""
                        INSERT INTO royalties (id, author_id, month, amount, book_id) 
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (row['id'], row['author_id'], row['month'], row['amount'], row['book_id']))
                except Exception as e:
                    print(f"Error migrating royalty: {e}")
            
            # 迁移申请数据
            sqlite_cur = sqlite_conn.execute("SELECT * FROM applications")
            for row in sqlite_cur.fetchall():
                try:
                    pg_cur.execute("""
                        INSERT INTO applications (id, author_id, title, pen_name, contract_type, status, reject_reason, created_at, processed_at) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (row['id'], row['author_id'], row['title'], row['pen_name'], 
                          row['contract_type'], row['status'], row['reject_reason'], 
                          row['created_at'], row['processed_at']))
                except Exception as e:
                    print(f"Error migrating application: {e}")
            
            # 迁移通知数据
            sqlite_cur = sqlite_conn.execute("SELECT * FROM notifications")
            for row in sqlite_cur.fetchall():
                try:
                    pg_cur.execute("""
                        INSERT INTO notifications (id, recipient_id, message, created_at, is_read) 
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (row['id'], row['recipient_id'], row['message'], 
                          row['created_at'], bool(row['is_read'])))
                except Exception as e:
                    print(f"Error migrating notification: {e}")
    
    sqlite_conn.close()
    print("Migration completed successfully")
