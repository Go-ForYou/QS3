# 作者后台（Flask + SQLite）

## 快速开始（Windows）

1. 安装依赖（需要 Python 3.10+）：
	```powershell
	py -m venv .venv
	.\.venv\Scripts\activate
	pip install -r requirements.txt
	```

2. 初始化数据库并创建管理员：
	```powershell
	py seed_admin.py
	```
	根据提示输入管理员用户名与密码。

3. 运行应用：
	```powershell
	set FLASK_APP=app.py
	py app.py
	```

4. 访问：
	- 管理员：`/admin`（登录后自动跳转）
	- 作者：`/author`（登录后自动跳转）
	- 登录：`/login`
	- 注册（作者）：`/register`

## 功能
- 作者：登录后查看签约书籍与当月稿费
- 管理员：后台添加书籍、设置稿费（我们维护数据）

## 配置
- 可在 `.env` 中设置：
	- `SECRET_KEY`：会话密钥
	- `PORT`：服务端口（默认 5000）

## 数据库文件
- `data.sqlite3` 位于项目根目录自动创建。

