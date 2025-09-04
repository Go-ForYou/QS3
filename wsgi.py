import os
from dotenv import load_dotenv

# 加载环境变量（可选）
load_dotenv()

# 暴露 application 给 WSGI 服务器
from app import app as application  # noqa: E402

# 也可在此设置生产环境变量，例如：
# os.environ.setdefault("SECRET_KEY", "please-change")
