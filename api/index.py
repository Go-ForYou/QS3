import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置Vercel环境变量
os.environ["VERCEL"] = "1"

# 导入Flask应用
from app import app

# Vercel需要这个文件作为入口点
# 这个文件会被Vercel自动识别为API路由的入口
