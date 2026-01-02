@echo off
echo 正在启动 PC Agent 项目...

set PROJECT_ROOT=%~dp0

:: ? 后端：在项目根目录运行，不设 PYTHONPATH
echo 后端启动中...
start "PC Agent Backend" cmd /k "cd /d "%PROJECT_ROOT%" && uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend --reload-dir shared --reload-dir config"
timeout /t 1 /nobreak >nul

:: ? 前端：在 frontend 目录运行，需要 PYTHONPATH 访问 shared/backend
echo 前端启动中...
start "PC Agent Frontend" cmd /k "cd /d "%PROJECT_ROOT%frontend" && set PYTHONPATH=%PROJECT_ROOT% && gradio app.py --watch-dirs . --watch-dirs ../shared --watch-dirs ../config"
timeout /t 1 /nobreak >nul
echo 项目启动命令已发送。


