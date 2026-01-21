@echo off
echo 正在启动 PC Agent 项目...

set PROJECT_ROOT=%~dp0

:: 后端启动
echo 后端启动中...
start "PC Agent Backend" cmd /k "cd /d "%PROJECT_ROOT%" && python backend/main.py"

:: 前端启动 - 设置 PYTHONPATH 为项目根目录
echo 前端启动中...
start "PC Agent Frontend" cmd /k "cd /d "%PROJECT_ROOT%" && set PYTHONPATH=%PROJECT_ROOT% && python frontend/app.py"

echo 项目启动完成。
echo 后端地址: http://127.0.0.1:8000
echo 前端地址: http://127.0.0.1:7860


