from getpass import getpass
from werkzeug.security import generate_password_hash
from db import get_db, init_db

if __name__ == "__main__":
	init_db()
	username = input("管理员用户名: ") or "admin"
	password = getpass("管理员密码: ")
	if not password:
		print("密码不能为空")
		exit(1)
	with get_db() as conn:
		conn.execute(
			"INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
			(username, generate_password_hash(password)),
		)
		conn.commit()
	print("管理员创建完成或已存在")

