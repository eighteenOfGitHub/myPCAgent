@echo off
echo 正在以 DEBUG 模式启动 PC Agent 项目...

set PROJECT_ROOT=%~dp0

:: 后端启动（DEBUG）
echo 后端启动中（DEBUG）...
start "PC Agent Backend (Debug)" cmd /k "cd /d "%PROJECT_ROOT%" && set PYTHONPATH=%PROJECT_ROOT% && python -X dev backend/main.py"

:: 前端启动（DEBUG）
echo 前端启动中（DEBUG）...
start "PC Agent Frontend (Debug)" cmd /k "cd /d "%PROJECT_ROOT%" && set PYTHONPATH=%PROJECT_ROOT% && set GRADIO_DEBUG=1 && python -X dev frontend/app.py"

echo 调试模式启动完成。
echo 后端地址: http://127.0.0.1:8000
echo 前端地址: http://127.0.0.1:7860