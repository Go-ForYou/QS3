import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置生产环境变量
os.environ.setdefault("FLASK_ENV", "production")

# 暴露 application 给 WSGI 服务器
from app import app as application  # noqa: E402

# 确保应用正确初始化
if __name__ == "__main__":
    application.run()
