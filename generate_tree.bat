@echo off
REM 先运行同目录下的clear_cache.py文件
python clear_cache.py
if %errorlevel% neq 0 (
    echo 错误: 运行clear_cache.py失败，请检查Python环境及脚本。
    pause
    exit /b %errorlevel%
)

REM 然后生成当前目录的文件树结构并保存到tree.txt
tree /f /a > tree.txt
chcp 65001 >nul

REM 检查是否成功生成文件树
if %errorlevel% equ 0 (
    echo 目录树已成功保存到tree.txt。
) else (
    echo 错误: 生成目录树时出现问题。
)