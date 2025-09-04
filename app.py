
import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import wraps

from db import get_db, init_db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")

_initialized = False

@app.before_request
def ensure_db_once():
	global _initialized
	if not _initialized:
		try:
			init_db()
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
				row = conn.execute("SELECT id, username, password_hash, role FROM users WHERE username=?", (username,)).fetchone()
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
			exists = conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
			if exists:
				flash("用户名已存在", "error")
				return render_template("register.html")
			conn.execute(
				"INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
				(username, generate_password_hash(password), "author"),
			)
			conn.commit()
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
		apps = conn.execute(
			"SELECT a.id, u.username, a.title, a.pen_name, a.contract_type, a.status, a.reject_reason, a.created_at FROM applications a JOIN users u ON a.author_id=u.id ORDER BY a.id DESC"
		).fetchall()
	if request.method == "POST":
		action = request.form.get("action")
		with get_db() as conn:
			if action == "approve_app":
				app_id = request.form.get("app_id")
				buyout_amount = request.form.get("buyout_amount")
				if app_id:
					row = conn.execute("SELECT author_id, title, pen_name, contract_type FROM applications WHERE id=?", (app_id,)).fetchone()
					if row:
						if row[3] == '买断':
							if not buyout_amount:
								flash("买断需要填写买断稿费", "error")
								return redirect(url_for("admin_apps"))
							conn.execute("UPDATE applications SET status='approved', processed_at=datetime('now') WHERE id=?", (app_id,))
							conn.execute(
								"INSERT INTO books (title, author_id, pen_name, contract_type, buyout_amount) VALUES (?, ?, ?, '买断', ?)",
								(row[1], row[0], row[2], buyout_amount),
							)
							conn.execute(
								"INSERT INTO notifications (recipient_id, message) VALUES (?, ?)",
								(row[0], f"您的签约申请已通过（买断），《{row[1]}》买断稿费：¥{buyout_amount}"),
							)
							conn.commit()
							flash("已同意买断并通知作者", "success")
						else:
							conn.execute("UPDATE applications SET status='approved', processed_at=datetime('now') WHERE id=?", (app_id,))
							conn.execute(
								"INSERT INTO books (title, author_id, pen_name, contract_type) VALUES (?, ?, ?, '保底')",
								(row[1], row[0], row[2]),
							)
							conn.execute(
								"INSERT INTO notifications (recipient_id, message) VALUES (?, ?)",
								(row[0], f"您的签约申请已通过（保底），《{row[1]}》后续按月设置稿费"),
							)
							conn.commit()
							flash("已同意保底并通知作者", "success")
			elif action == "reject_app":
				app_id = request.form.get("app_id")
				reason = request.form.get("reason", "").strip() or "未提供原因"
				if app_id:
					row = conn.execute("SELECT author_id, title FROM applications WHERE id=?", (app_id,)).fetchone()
					conn.execute("UPDATE applications SET status='rejected', reject_reason=?, processed_at=datetime('now') WHERE id=?", (reason, app_id))
					if row:
						conn.execute(
							"INSERT INTO notifications (recipient_id, message) VALUES (?, ?)",
							(row[0], f"您的签约申请被拒绝：《{row[1]}》，原因：{reason}"),
						)
					conn.commit()
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
		books = conn.execute(
			"SELECT b.id, b.title, u.username, b.contract_type, b.buyout_amount, b.created_at FROM books b JOIN users u ON b.author_id=u.id ORDER BY u.username ASC, b.id DESC"
		).fetchall()
	return render_template("admin_books.html", books=books)


@app.route("/admin")
@login_required(role="admin")
def admin_redirect():
	return redirect(url_for("admin_apps"))


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
