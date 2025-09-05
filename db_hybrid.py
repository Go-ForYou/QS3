import os
import sqlite3
from contextlib import contextmanager

# 检测是否在Vercel环境中运行
IS_VERCEL = os.getenv("VERCEL") is not None

if IS_VERCEL:
    # 在Vercel环境中，尝试使用PostgreSQL
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        from urllib.parse import urlparse
        POSTGRES_AVAILABLE = True
    except ImportError:
        POSTGRES_AVAILABLE = False
        print("PostgreSQL not available, using fallback")
else:
    # 在本地环境中，使用SQLite
    POSTGRES_AVAILABLE = False

def get_db_url():
    """获取PostgreSQL数据库连接URL"""
    if not POSTGRES_AVAILABLE:
        return None
    
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
    
    return None

@contextmanager
def get_db():
    """获取数据库连接"""
    if POSTGRES_AVAILABLE and IS_VERCEL:
        # 在Vercel环境中，使用PostgreSQL
        db_url = get_db_url()
        
        if not db_url:
            print("No PostgreSQL URL available, using fallback")
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
            print(f"PostgreSQL connection error: {e}")
            # 如果连接失败，返回None
            yield None
    else:
        # 在本地环境中，使用SQLite
        db_path = os.path.join(os.path.dirname(__file__), "data.sqlite3")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

def init_db():
    """初始化数据库表"""
    with get_db() as conn:
        if conn is None:
            print("No database connection available, skipping initialization")
            return
        
        if POSTGRES_AVAILABLE and IS_VERCEL:
            # PostgreSQL表结构
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
                        FOREIGN KEY(book_id) REFERENCES books(id)
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
                
                print("PostgreSQL tables initialized successfully")
        else:
            # SQLite表结构
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin','author'))
                );
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author_id INTEGER NOT NULL,
                    pen_name TEXT,
                    contract_type TEXT CHECK(contract_type IN ('保底','买断')),
                    buyout_amount REAL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY(author_id) REFERENCES users(id)
                );
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS royalties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author_id INTEGER NOT NULL,
                    month TEXT NOT NULL,
                    amount REAL NOT NULL DEFAULT 0,
                    book_id INTEGER,
                    FOREIGN KEY(author_id) REFERENCES users(id),
                    FOREIGN KEY(book_id) REFERENCES books(id)
                );
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    pen_name TEXT NOT NULL,
                    contract_type TEXT NOT NULL CHECK(contract_type IN ('保底','买断')),
                    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
                    reject_reason TEXT,
                    reviewer_id INTEGER,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    processed_at TEXT,
                    FOREIGN KEY(author_id) REFERENCES users(id),
                    FOREIGN KEY(reviewer_id) REFERENCES users(id)
                );
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    is_read INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(recipient_id) REFERENCES users(id)
                );
            """)
            
            conn.commit()
            print("SQLite tables initialized successfully")

def add_reviewer_field():
    """为现有数据库添加审核者字段"""
    try:
        with get_db() as conn:
            if conn:
                if POSTGRES_AVAILABLE and IS_VERCEL:
                    # PostgreSQL
                    with conn.cursor() as cur:
                        # 检查字段是否已存在
                        cur.execute("""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name='applications' AND column_name='reviewer_id'
                        """)
                        if not cur.fetchone():
                            # 添加审核者字段
                            cur.execute("""
                                ALTER TABLE applications 
                                ADD COLUMN reviewer_id INTEGER REFERENCES users(id)
                            """)
                            print("PostgreSQL: 已添加审核者字段")
                        else:
                            print("PostgreSQL: 审核者字段已存在")
                else:
                    # SQLite
                    try:
                        conn.execute("ALTER TABLE applications ADD COLUMN reviewer_id INTEGER REFERENCES users(id)")
                        conn.commit()
                        print("SQLite: 已添加审核者字段")
                    except Exception as e:
                        if "duplicate column name" in str(e).lower():
                            print("SQLite: 审核者字段已存在")
                        else:
                            print(f"SQLite: 添加审核者字段时出错: {e}")
    except Exception as e:
        print(f"添加审核者字段时出错: {e}")

def seed_admin_user():
    """创建默认管理员用户"""
    from werkzeug.security import generate_password_hash
    
    with get_db() as conn:
        if conn is None:
            print("No database connection available, skipping admin user creation")
            return
        
        if POSTGRES_AVAILABLE and IS_VERCEL:
            # PostgreSQL
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
        else:
            # SQLite
            # 检查是否已有管理员用户
            admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
            
            if admin_count == 0:
                # 创建默认管理员用户
                admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
                conn.execute("""
                    INSERT INTO users (username, password_hash, role) 
                    VALUES (?, ?, ?)
                """, ('admin', generate_password_hash(admin_password), 'admin'))
                
                conn.commit()
                print("Default admin user created: admin / admin123")
            else:
                print("Admin user already exists")
