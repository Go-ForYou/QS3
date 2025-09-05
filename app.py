
import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import wraps

# 使用混合数据库配置（本地SQLite，生产PostgreSQL）
from db_hybrid import get_db, init_db, seed_admin_user, add_reviewer_field, POSTGRES_AVAILABLE

def execute_query(conn, query, params=None):
	"""执行数据库查询，兼容PostgreSQL和SQLite"""
	if POSTGRES_AVAILABLE and IS_VERCEL:
		# PostgreSQL查询
		with conn.cursor() as cur:
			cur.execute(query, params or ())
			return cur.fetchone()
	else:
		# SQLite查询
		return conn.execute(query, params or ()).fetchone()

def execute_query_all(conn, query, params=None):
	"""执行数据库查询并返回所有结果，兼容PostgreSQL和SQLite"""
	if POSTGRES_AVAILABLE and IS_VERCEL:
		# PostgreSQL查询
		with conn.cursor() as cur:
			cur.execute(query, params or ())
			return cur.fetchall()
	else:
		# SQLite查询
		return conn.execute(query, params or ()).fetchall()

def execute_update(conn, query, params=None):
	"""执行数据库更新操作，兼容PostgreSQL和SQLite"""
	if POSTGRES_AVAILABLE and IS_VERCEL:
		# PostgreSQL查询
		with conn.cursor() as cur:
			cur.execute(query, params or ())
	else:
		# SQLite查询
		conn.execute(query, params or ())
		conn.commit()

load_dotenv()

# 检测是否在Vercel环境中运行
IS_VERCEL = os.getenv("VERCEL") is not None

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")

_initialized = False

@app.before_request
def ensure_db_once():
	global _initialized
	if not _initialized:
		try:
			init_db()
			# 创建默认管理员用户
			seed_admin_user()
			# 添加审核者字段（如果不存在）
			add_reviewer_field()
			_initialized = True
		except Exception as e:
			app.logger.error(f"Database initialization failed: {e}")
			flash("数据库初始化失败，请联系管理员", "error")
			return render_template("500.html"), 500


def login_required(role=None):
	def decorator(view_func):
		@wraps(view_func)
		def wrapped(*args, **kwargs):
			user_id = session.get("user_id")
			user_role = session.get("role")
			if not user_id:
				return redirect(url_for("login"))
			if role and user_role != role:
				flash("无权限访问该页面", "error")
				return redirect(url_for("index"))
			return view_func(*args, **kwargs)
		return wrapped
	return decorator


@app.route("/")
def index():
	try:
		role = session.get("role")
		if role == "admin":
			return redirect(url_for("admin_apps"))
		elif role == "author":
			return redirect(url_for("author_contracts"))
		else:
			# 未登录用户重定向到登录页面
			return redirect(url_for("login"))
	except Exception as e:
		app.logger.error(f"Index route error: {e}")
		# 如果出现错误，直接显示登录页面
		return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		username = request.form.get("username", "").strip()
		password = request.form.get("password", "")
		try:
			with get_db() as conn:
				if conn is None:
					flash("数据库连接失败", "error")
					return render_template("login.html")
				
				# 使用兼容的查询函数
				if POSTGRES_AVAILABLE and IS_VERCEL:
					row = execute_query(conn, "SELECT id, username, password_hash, role FROM users WHERE username = %s", (username,))
				else:
					row = execute_query(conn, "SELECT id, username, password_hash, role FROM users WHERE username=?", (username,))
				
				if row and check_password_hash(row[2], password):
					session["user_id"] = row[0]
					session["username"] = row[1]
					session["role"] = row[3]
					flash("登录成功", "success")
					return redirect(url_for("index"))
				else:
					flash("用户名或密码错误", "error")
		except Exception as e:
			app.logger.error(f"Login error: {e}")
			flash("登录时发生错误，请稍后再试", "error")
	return render_template("login.html")


@app.route("/logout")
def logout():
	session.clear()
	flash("已退出登录", "info")
	return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
	if request.method == "POST":
		username = request.form.get("username", "").strip()
		password = request.form.get("password", "")
		
		if not username or not password:
			flash("请输入用户名和密码", "error")
			return render_template("register.html")
		
		with get_db() as conn:
			if conn is None:
				flash("数据库连接失败", "error")
				return render_template("register.html")
			
			# 检查用户名是否已存在
			if POSTGRES_AVAILABLE and IS_VERCEL:
				exists = execute_query(conn, "SELECT 1 FROM users WHERE username = %s", (username,))
			else:
				exists = execute_query(conn, "SELECT 1 FROM users WHERE username=?", (username,))
			
			if exists:
				flash("用户名已存在", "error")
				return render_template("register.html")
			
			# 创建作者用户
			if POSTGRES_AVAILABLE and IS_VERCEL:
				execute_update(conn, 
					"INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
					(username, generate_password_hash(password), "author")
				)
			else:
				execute_update(conn,
					"INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
					(username, generate_password_hash(password), "author")
				)
			
			flash("注册成功，请登录", "success")
			return redirect(url_for("login"))
	
	return render_template("register.html")


@app.route("/author")
@login_required(role="author")
def author_dashboard():
	return redirect(url_for("author_contracts"))


@app.route("/author/contracts")
@login_required(role="author")
def author_contracts():
	user_id = session.get("user_id")
	month_key = datetime.now().strftime("%Y-%m")
	with get_db() as conn:
		books = conn.execute(
			"SELECT id, title, contract_type, buyout_amount FROM books WHERE author_id=? ORDER BY id DESC",
			(user_id,),
		).fetchall()
		royalties_curr = conn.execute(
			"SELECT book_id, amount FROM royalties WHERE author_id=? AND month=? AND book_id IS NOT NULL",
			(user_id, month_key),
		).fetchall()
		curr_map = {r[0]: r[1] for r in royalties_curr}
		history_rows = conn.execute(
			"SELECT book_id, month, amount FROM royalties WHERE author_id=? AND book_id IS NOT NULL AND month<>? ORDER BY month DESC",
			(user_id, month_key),
		).fetchall()
		history = {}
		for r in history_rows:
			book_id, m, amt = r
			history.setdefault(book_id, []).append((m, amt))
	return render_template(
		"author_contracts.html",
		books=books,
		month=month_key,
		bookIdToRoyalty=curr_map,
		history=history,
	)


@app.route("/author/apply", methods=["GET", "POST"])
@login_required(role="author")
def author_apply():
	if request.method == "POST":
		title = request.form.get("title", "").strip()
		pen_name = request.form.get("pen_name", "").strip()
		contract_type = request.form.get("contract_type", "").strip()
		if not title or not pen_name or contract_type not in ("保底", "买断"):
			flash("请完整填写申请信息并选择正确签约方式", "error")
			return redirect(url_for("author_apply"))
		with get_db() as conn:
			conn.execute(
				"INSERT INTO applications (author_id, title, pen_name, contract_type) VALUES (?, ?, ?, ?)",
				(session.get("user_id"), title, pen_name, contract_type),
			)
			conn.commit()
		flash("申请已提交，等待审核", "success")
		return redirect(url_for("author_results"))
	return render_template("author_apply.html")


@app.route("/author/results")
@login_required(role="author")
def author_results():
	user_id = session.get("user_id")
	with get_db() as conn:
		applications = conn.execute(
			"SELECT id, title, pen_name, contract_type, status, reject_reason, created_at FROM applications WHERE author_id=? ORDER BY id DESC",
			(user_id,),
		).fetchall()
	return render_template("author_results.html", applications=applications)


@app.route("/author/notifications")
@login_required(role="author")
def author_notifications():
	user_id = session.get("user_id")
	with get_db() as conn:
		notifications = conn.execute(
			"SELECT id, message, created_at, is_read FROM notifications WHERE recipient_id=? ORDER BY id DESC",
			(user_id,),
		).fetchall()
	return render_template("author_notifications.html", notifications=notifications)


@app.route("/author/notifications/read", methods=["POST"])
@login_required(role="author")
def author_mark_notifications_read():
	with get_db() as conn:
		conn.execute(
			"UPDATE notifications SET is_read=1 WHERE recipient_id=?",
			(session.get("user_id"),),
		)
		conn.commit()
	return redirect(url_for("author_notifications"))


@app.route("/author/notifications/read_one", methods=["POST"])
@login_required(role="author")
def author_mark_notification_one():
	nid = request.form.get("id")
	with get_db() as conn:
		conn.execute("UPDATE notifications SET is_read=1 WHERE id=? AND recipient_id=?", (nid, session.get("user_id")))
		conn.commit()
	return redirect(url_for("author_notifications"))


# 管理端删除书籍
@app.route("/admin/books/delete", methods=["POST"])
@login_required(role="admin")
def admin_delete_book():
	book_id = request.form.get("book_id")
	with get_db() as conn:
		conn.execute("DELETE FROM books WHERE id=?", (book_id,))
		conn.execute("DELETE FROM royalties WHERE book_id=?", (book_id,))
		conn.commit()
		flash("已删除书籍及稿费记录", "success")
	return redirect(url_for("admin_books"))


@app.route("/admin/apps", methods=["GET", "POST"])
@login_required(role="admin")
def admin_apps():
	with get_db() as conn:
		if POSTGRES_AVAILABLE and IS_VERCEL:
			apps = execute_query_all(conn, """
				SELECT a.id, u.username, a.title, a.pen_name, a.contract_type, a.status, a.reject_reason, a.created_at, 
					   r.username as reviewer_name
				FROM applications a 
				JOIN users u ON a.author_id=u.id 
				LEFT JOIN users r ON a.reviewer_id=r.id 
				ORDER BY a.id DESC
			""")
		else:
			apps = execute_query_all(conn, """
				SELECT a.id, u.username, a.title, a.pen_name, a.contract_type, a.status, a.reject_reason, a.created_at, 
					   r.username as reviewer_name
				FROM applications a 
				JOIN users u ON a.author_id=u.id 
				LEFT JOIN users r ON a.reviewer_id=r.id 
				ORDER BY a.id DESC
			""")
	if request.method == "POST":
		action = request.form.get("action")
		with get_db() as conn:
			if action == "approve_app":
				app_id = request.form.get("app_id")
				buyout_amount = request.form.get("buyout_amount")
				if app_id:
					if POSTGRES_AVAILABLE and IS_VERCEL:
						row = execute_query(conn, "SELECT author_id, title, pen_name, contract_type FROM applications WHERE id = %s", (app_id,))
					else:
						row = execute_query(conn, "SELECT author_id, title, pen_name, contract_type FROM applications WHERE id=?", (app_id,))
					if row:
						# 获取当前管理员ID
						current_admin_id = session.get('user_id')
						if row[3] == '买断':
							if not buyout_amount:
								flash("买断需要填写买断稿费", "error")
								return redirect(url_for("admin_apps"))
							if POSTGRES_AVAILABLE and IS_VERCEL:
								execute_update(conn, "UPDATE applications SET status='approved', processed_at=NOW(), reviewer_id=%s WHERE id=%s", (current_admin_id, app_id))
								execute_update(conn,
									"INSERT INTO books (title, author_id, pen_name, contract_type, buyout_amount) VALUES (%s, %s, %s, '买断', %s)",
									(row[1], row[0], row[2], buyout_amount),
								)
								execute_update(conn,
									"INSERT INTO notifications (recipient_id, message) VALUES (%s, %s)",
									(row[0], f"您的签约申请已通过（买断），《{row[1]}》买断稿费：¥{buyout_amount}"),
								)
							else:
								execute_update(conn, "UPDATE applications SET status='approved', processed_at=datetime('now'), reviewer_id=? WHERE id=?", (current_admin_id, app_id))
								execute_update(conn,
									"INSERT INTO books (title, author_id, pen_name, contract_type, buyout_amount) VALUES (?, ?, ?, '买断', ?)",
									(row[1], row[0], row[2], buyout_amount),
								)
								execute_update(conn,
									"INSERT INTO notifications (recipient_id, message) VALUES (?, ?)",
									(row[0], f"您的签约申请已通过（买断），《{row[1]}》买断稿费：¥{buyout_amount}"),
								)
							flash("已同意买断并通知作者", "success")
						else:
							if POSTGRES_AVAILABLE and IS_VERCEL:
								execute_update(conn, "UPDATE applications SET status='approved', processed_at=NOW(), reviewer_id=%s WHERE id=%s", (current_admin_id, app_id))
								execute_update(conn,
									"INSERT INTO books (title, author_id, pen_name, contract_type) VALUES (%s, %s, %s, '保底')",
									(row[1], row[0], row[2]),
								)
								execute_update(conn,
									"INSERT INTO notifications (recipient_id, message) VALUES (%s, %s)",
									(row[0], f"您的签约申请已通过（保底），《{row[1]}》后续按月设置稿费"),
								)
							else:
								execute_update(conn, "UPDATE applications SET status='approved', processed_at=datetime('now'), reviewer_id=? WHERE id=?", (current_admin_id, app_id))
								execute_update(conn,
									"INSERT INTO books (title, author_id, pen_name, contract_type) VALUES (?, ?, ?, '保底')",
									(row[1], row[0], row[2]),
								)
								execute_update(conn,
									"INSERT INTO notifications (recipient_id, message) VALUES (?, ?)",
									(row[0], f"您的签约申请已通过（保底），《{row[1]}》后续按月设置稿费"),
								)
							flash("已同意保底并通知作者", "success")
			elif action == "reject_app":
				app_id = request.form.get("app_id")
				reason = request.form.get("reason", "").strip() or "未提供原因"
				if app_id:
					if POSTGRES_AVAILABLE and IS_VERCEL:
						row = execute_query(conn, "SELECT author_id, title FROM applications WHERE id = %s", (app_id,))
					else:
						row = execute_query(conn, "SELECT author_id, title FROM applications WHERE id=?", (app_id,))
					# 获取当前管理员ID
					current_admin_id = session.get('user_id')
					if POSTGRES_AVAILABLE and IS_VERCEL:
						execute_update(conn, "UPDATE applications SET status='rejected', reject_reason=%s, processed_at=NOW(), reviewer_id=%s WHERE id=%s", (reason, current_admin_id, app_id))
						if row:
							execute_update(conn,
								"INSERT INTO notifications (recipient_id, message) VALUES (%s, %s)",
								(row[0], f"您的签约申请被拒绝：《{row[1]}》，原因：{reason}"),
							)
					else:
						execute_update(conn, "UPDATE applications SET status='rejected', reject_reason=?, processed_at=datetime('now'), reviewer_id=? WHERE id=?", (reason, current_admin_id, app_id))
						if row:
							execute_update(conn,
								"INSERT INTO notifications (recipient_id, message) VALUES (?, ?)",
								(row[0], f"您的签约申请被拒绝：《{row[1]}》，原因：{reason}"),
							)
					flash("已拒绝并通知作者", "success")
		return redirect(url_for("admin_apps"))
	return render_template("admin_apps.html", apps=apps)


@app.route("/admin/royalties", methods=["GET", "POST"])
@login_required(role="admin")
def admin_royalties():
	month_key = request.args.get("month") or datetime.now().strftime("%Y-%m")
	with get_db() as conn:
		books = conn.execute(
			"SELECT b.id, b.title, u.username, b.contract_type FROM books b JOIN users u ON b.author_id=u.id ORDER BY u.username ASC, b.id DESC"
		).fetchall()
	if request.method == "POST":
		book_id_raw = request.form.get("book_id")
		amount_raw = request.form.get("amount")
		month = request.form.get("month") or month_key
		try:
			book_id = int(book_id_raw)
		except (TypeError, ValueError):
			flash("请选择有效的书籍", "error")
			return redirect(url_for("admin_royalties", month=month))
		try:
			amount = float(amount_raw)
		except (TypeError, ValueError):
			flash("请输入有效的金额", "error")
			return redirect(url_for("admin_royalties", month=month))
		try:
			datetime.strptime(month, "%Y-%m")
		except ValueError:
			flash("月份格式应为 YYYY-MM", "error")
			return redirect(url_for("admin_royalties", month=month_key))
		try:
			with get_db() as conn:
				row = conn.execute("SELECT author_id, title, contract_type FROM books WHERE id=?", (book_id,)).fetchone()
				if not row:
					flash("书籍不存在", "error")
					return redirect(url_for("admin_royalties", month=month))
				if row[2] != '保底':
					flash("仅保底合同需要设置月度稿费", "error")
					return redirect(url_for("admin_royalties", month=month))
				exists = conn.execute("SELECT 1 FROM royalties WHERE book_id=? AND month=?", (book_id, month)).fetchone()
				if exists:
					conn.execute("UPDATE royalties SET amount=? WHERE book_id=? AND month=?", (amount, book_id, month))
				else:
					conn.execute("INSERT INTO royalties (author_id, month, amount, book_id) VALUES (?, ?, ?, ?)", (row[0], month, amount, book_id))
				conn.execute("INSERT INTO notifications (recipient_id, message) VALUES (?, ?)", (row[0], f"已设置《{row[1]}》 {month} 稿费：¥{amount:.2f}"))
				conn.commit()
				flash("已设置书籍月度稿费并通知作者", "success")
		except Exception as e:
			flash(f"设置失败：{e}", "error")
		return redirect(url_for("admin_royalties", month=month))
	return render_template("admin_royalties.html", books=books, month=month_key)


@app.route("/admin/books")
@login_required(role="admin")
def admin_books():
	with get_db() as conn:
		books = execute_query_all(conn,
			"SELECT b.id, b.title, u.username, b.contract_type, b.buyout_amount, b.created_at FROM books b JOIN users u ON b.author_id=u.id ORDER BY u.username ASC, b.id DESC"
		)
	return render_template("admin_books.html", books=books)


@app.route("/admin")
@login_required(role="admin")
def admin_redirect():
	return redirect(url_for("admin_apps"))

@app.route("/admin/users")
@login_required(role="admin")
def admin_users():
	with get_db() as conn:
		if conn is None:
			flash("数据库连接失败", "error")
			return redirect(url_for("admin_apps"))
		
		if POSTGRES_AVAILABLE and IS_VERCEL:
			with conn.cursor() as cur:
				cur.execute("SELECT id, username, role, created_at FROM users ORDER BY id DESC")
				users = cur.fetchall()
		else:
			users = conn.execute("SELECT id, username, role, created_at FROM users ORDER BY id DESC").fetchall()
	
	return render_template("admin_users.html", users=users)

@app.route("/admin/users/delete", methods=["POST"])
@login_required(role="admin")
def admin_delete_user():
	user_id = request.form.get("user_id")
	
	# 不能删除自己
	if int(user_id) == session.get("user_id"):
		flash("不能删除自己的账号", "error")
		return redirect(url_for("admin_users"))
	
	with get_db() as conn:
		if conn is None:
			flash("数据库连接失败", "error")
			return redirect(url_for("admin_users"))
		
		if POSTGRES_AVAILABLE and IS_VERCEL:
			with conn.cursor() as cur:
				# 检查用户是否存在且为管理员
				cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
				user = cur.fetchone()
				
				if not user:
					flash("用户不存在", "error")
					return redirect(url_for("admin_users"))
				
				if user[0] != 'admin':
					flash("只能删除管理员账号", "error")
					return redirect(url_for("admin_users"))
				
				# 删除用户
				cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
				flash("用户删除成功", "success")
		else:
			# 检查用户是否存在且为管理员
			user = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
			
			if not user:
				flash("用户不存在", "error")
				return redirect(url_for("admin_users"))
			
			if user[0] != 'admin':
				flash("只能删除管理员账号", "error")
				return redirect(url_for("admin_users"))
			
			# 删除用户
			conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
			conn.commit()
			flash("用户删除成功", "success")
	
	return redirect(url_for("admin_users"))

# 管理员管理页面（需要密钥访问）
@app.route("/admin/management", methods=["GET", "POST"])
def admin_management():
	if request.method == "POST":
		access_key = request.form.get("access_key", "").strip()
		if access_key == "kaqia111":
			session["admin_verified"] = True
			flash("密钥验证成功", "success")
		else:
			flash("密钥错误", "error")
	
	# 获取所有管理员列表
	admins = []
	if session.get("admin_verified"):
		with get_db() as conn:
			if conn:
				if POSTGRES_AVAILABLE and IS_VERCEL:
					with conn.cursor() as cur:
						cur.execute("SELECT id, username FROM users WHERE role = 'admin' ORDER BY id")
						admins = cur.fetchall()
				else:
					admins = conn.execute("SELECT id, username FROM users WHERE role = 'admin' ORDER BY id").fetchall()
	
	return render_template("admin_management.html", admins=admins)

# 注册新管理员（需要密钥验证）
@app.route("/admin/register", methods=["POST"])
def admin_register():
	if not session.get("admin_verified"):
		flash("需要先验证访问密钥", "error")
		return redirect(url_for("admin_management"))
	
	username = request.form.get("username", "").strip()
	password = request.form.get("password", "")
	
	if not username or not password:
		flash("请输入用户名和密码", "error")
		return redirect(url_for("admin_management"))
	
	with get_db() as conn:
		if conn is None:
			flash("数据库连接失败", "error")
			return redirect(url_for("admin_management"))
		
		# 检查用户名是否已存在
		if POSTGRES_AVAILABLE and IS_VERCEL:
			with conn.cursor() as cur:
				cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
				exists = cur.fetchone()
		else:
			exists = conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
		
		if exists:
			flash("用户名已存在", "error")
			return redirect(url_for("admin_management"))
		
		# 创建管理员用户
		if POSTGRES_AVAILABLE and IS_VERCEL:
			with conn.cursor() as cur:
				cur.execute(
					"INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
					(username, generate_password_hash(password), "admin")
				)
		else:
			conn.execute(
				"INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
				(username, generate_password_hash(password), "admin")
			)
			conn.commit()
		
		flash("管理员账号创建成功", "success")
	
	return redirect(url_for("admin_management"))

# 删除管理员（需要删除密钥）
@app.route("/admin/delete", methods=["POST"])
def admin_delete():
	if not session.get("admin_verified"):
		flash("需要先验证访问密钥", "error")
		return redirect(url_for("admin_management"))
	
	delete_key = request.form.get("delete_key", "").strip()
	admin_id = request.form.get("admin_id")
	
	if delete_key != "kaqia222":
		flash("删除密钥错误", "error")
		return redirect(url_for("admin_management"))
	
	if not admin_id:
		flash("无效的管理员ID", "error")
		return redirect(url_for("admin_management"))
	
	with get_db() as conn:
		if conn is None:
			flash("数据库连接失败", "error")
			return redirect(url_for("admin_management"))
		
		# 检查管理员是否存在
		if POSTGRES_AVAILABLE and IS_VERCEL:
			with conn.cursor() as cur:
				cur.execute("SELECT username FROM users WHERE id = %s AND role = 'admin'", (admin_id,))
				admin = cur.fetchone()
				
				if not admin:
					flash("管理员不存在", "error")
					return redirect(url_for("admin_management"))
				
				# 删除管理员
				cur.execute("DELETE FROM users WHERE id = %s", (admin_id,))
				flash(f"管理员 {admin[0]} 删除成功", "success")
		else:
			admin = conn.execute("SELECT username FROM users WHERE id = ? AND role = 'admin'", (admin_id,)).fetchone()
			
			if not admin:
				flash("管理员不存在", "error")
				return redirect(url_for("admin_management"))
			
			# 删除管理员
			conn.execute("DELETE FROM users WHERE id = ?", (admin_id,))
			conn.commit()
			flash(f"管理员 {admin[0]} 删除成功", "success")
	
	return redirect(url_for("admin_management"))

# 退出管理员验证
@app.route("/admin/logout", methods=["POST"])
def admin_logout():
	session.pop("admin_verified", None)
	flash("已退出管理员验证", "info")
	return redirect(url_for("admin_management"))


# 静态文件路由 - 确保在Vercel上正确工作
@app.route("/static/<path:filename>")
def static_files(filename):
	return send_from_directory(app.static_folder, filename)

# 静态文件测试路由
@app.route("/test-static")
def test_static():
	return send_from_directory('.', 'test_static.html')

# Vercel环境检测路由
@app.route("/vercel-info")
def vercel_info():
	return {
		"is_vercel": IS_VERCEL,
		"environment": os.getenv("VERCEL_ENV", "unknown"),
		"status": "ok"
	}, 200

# 健康检查路由
@app.route("/health")
def health_check():
	return {"status": "ok", "message": "应用运行正常"}, 200




@app.errorhandler(404)
def not_found(error):
	app.logger.warning(f"404 error: {request.url} - {request.method}")
	return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
	app.logger.error(f"500 error: {error}")
	return render_template("500.html"), 500


# Vercel兼容性配置
if __name__ == "__main__":
	# 在生产环境中禁用debug模式
	debug_mode = os.getenv("FLASK_ENV") != "production"
	app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=debug_mode)

# 为Vercel导出应用实例
# 这确保Vercel可以正确导入和运行应用
