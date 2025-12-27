@echo off
echo ========================================
echo 工业产品质量检测系统
echo ========================================
echo.
echo 正在检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.7或更高版本
    pause
    exit /b 1
)
echo.
echo 正在安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo 警告: 依赖包安装可能有问题，请检查
)
echo.
echo 正在启动服务器...
echo 请在浏览器中访问: http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo.
python app.py
pause

