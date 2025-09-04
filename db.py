import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "data.sqlite3")


def get_db():
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	return conn


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
	# 注意：SQLite 的 PRAGMA 不支持参数绑定，这里表名来自受信任代码，不是用户输入
	cur = conn.execute(f"PRAGMA table_info({table})")
	for row in cur.fetchall():
		if row[1] == column:
			return True
	return False


def _needs_royalties_migration(conn: sqlite3.Connection) -> bool:
	row = conn.execute(
		"SELECT sql FROM sqlite_master WHERE type='table' AND name='royalties'"
	).fetchone()
	if not row or not row[0]:
		return False
	ddl = row[0]
	return "PRIMARY KEY(author_id, month)" in ddl and "id INTEGER PRIMARY KEY" not in ddl


def _migrate_royalties(conn: sqlite3.Connection) -> None:
	conn.execute(
		"""
		CREATE TABLE IF NOT EXISTS royalties_new (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			author_id INTEGER NOT NULL,
			month TEXT NOT NULL,
			amount REAL NOT NULL DEFAULT 0,
			book_id INTEGER,
			FOREIGN KEY(author_id) REFERENCES users(id),
			FOREIGN KEY(book_id) REFERENCES books(id)
		);
		"""
	)
	conn.execute(
		"CREATE UNIQUE INDEX IF NOT EXISTS idx_royalties_book_month ON royalties_new(book_id, month) WHERE book_id IS NOT NULL"
	)
	conn.execute(
		"CREATE UNIQUE INDEX IF NOT EXISTS idx_royalties_author_month_null ON royalties_new(author_id, month) WHERE book_id IS NULL"
	)
	conn.execute(
		"INSERT INTO royalties_new(author_id, month, amount, book_id) SELECT author_id, month, amount, NULL FROM royalties"
	)
	conn.execute("DROP TABLE royalties")
	conn.execute("ALTER TABLE royalties_new RENAME TO royalties")


def init_db():
	with get_db() as conn:
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS users (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT UNIQUE NOT NULL,
				password_hash TEXT NOT NULL,
				role TEXT NOT NULL CHECK(role IN ('admin','author'))
			);
			"""
		)
		conn.execute(
			"""
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
			"""
		)
		if not _column_exists(conn, "books", "pen_name"):
			conn.execute("ALTER TABLE books ADD COLUMN pen_name TEXT")
		if not _column_exists(conn, "books", "contract_type"):
			conn.execute("ALTER TABLE books ADD COLUMN contract_type TEXT")
		if not _column_exists(conn, "books", "buyout_amount"):
			conn.execute("ALTER TABLE books ADD COLUMN buyout_amount REAL")
		if not _column_exists(conn, "books", "created_at"):
			# 注意：ALTER TABLE 时不使用表达式默认值，避免报错
			conn.execute("ALTER TABLE books ADD COLUMN created_at TEXT")
			conn.execute("UPDATE books SET created_at = datetime('now') WHERE created_at IS NULL")

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS royalties (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				author_id INTEGER NOT NULL,
				month TEXT NOT NULL,
				amount REAL NOT NULL DEFAULT 0,
				book_id INTEGER,
				FOREIGN KEY(author_id) REFERENCES users(id),
				FOREIGN KEY(book_id) REFERENCES books(id)
			);
			"""
		)
		if _needs_royalties_migration(conn):
			_migrate_royalties(conn)
		conn.execute(
			"CREATE UNIQUE INDEX IF NOT EXISTS idx_royalties_book_month ON royalties(book_id, month) WHERE book_id IS NOT NULL"
		)
		conn.execute(
			"CREATE UNIQUE INDEX IF NOT EXISTS idx_royalties_author_month_null ON royalties(author_id, month) WHERE book_id IS NULL"
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS applications (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				author_id INTEGER NOT NULL,
				title TEXT NOT NULL,
				pen_name TEXT NOT NULL,
				contract_type TEXT NOT NULL CHECK(contract_type IN ('保底','买断')),
				status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
				reject_reason TEXT,
				created_at TEXT NOT NULL DEFAULT (datetime('now')),
				processed_at TEXT,
				FOREIGN KEY(author_id) REFERENCES users(id)
			);
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS notifications (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				recipient_id INTEGER NOT NULL,
				message TEXT NOT NULL,
				created_at TEXT NOT NULL DEFAULT (datetime('now')),
				is_read INTEGER NOT NULL DEFAULT 0,
				FOREIGN KEY(recipient_id) REFERENCES users(id)
			);
			"""
		)

		conn.commit()

