@echo off
echo 正在启动 PC Agent 项目...

REM 获取项目根目录的绝对路径 (即当前脚本所在目录)
set PROJECT_ROOT=%~dp0

REM 设置环境变量 PYTHONPATH 为项目根目录
REM 这样 Python 在 frontend 目录下也能找到 'frontend' 包
set PYTHONPATH=%PROJECT_ROOT%

REM 启动后端服务 (在新窗口中)
start "PC Agent Backend" cmd /k "python -m backend.main"

REM 等待一段时间，确保后端服务器有时间启动
echo 等待后端启动...
timeout /t 1 /nobreak >nul

REM 启动前端服务 (在新窗口中)，设置 PYTHONPATH 并使用 gradio 命令启用热重载
REM 使用 %PROJECT_ROOT% 确保 gradio 在正确的上下文中运行
start "PC Agent Frontend" cmd /k "cd /d %PROJECT_ROOT%frontend && set PYTHONPATH=%PROJECT_ROOT% && gradio app.py"

echo 项目启动命令已发送。请检查新打开的窗口。
pause