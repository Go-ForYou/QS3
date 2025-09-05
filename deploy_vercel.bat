@echo off
echo ========================================
echo        Vercel 部署脚本
echo ========================================
echo.

echo 1. 检查 Vercel CLI 是否已安装...
vercel --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Vercel CLI 未安装
    echo 请先运行: npm install -g vercel
    pause
    exit /b 1
)

echo 2. 登录 Vercel...
vercel login

echo 3. 部署到 Vercel...
vercel

echo 4. 设置环境变量...
echo 请手动设置以下环境变量:
echo - SECRET_KEY: 您的应用密钥
echo - FLASK_ENV: production
echo.
echo 运行以下命令设置环境变量:
echo vercel env add SECRET_KEY
echo vercel env add FLASK_ENV
echo.

echo 5. 生产环境部署...
vercel --prod

echo.
echo ========================================
echo        部署完成！
echo ========================================
echo 您的应用已部署到 Vercel
echo 请检查 Vercel 控制台获取部署URL
echo.
pause
