@echo off
REM 设置批处理脚本的编码为 UTF-8，以更好地处理中文路径和文件名
chcp 65001 >nul

REM 检查是否存在 clear_cache.py
if not exist "clear_cache.py" (
    echo 警告: 未找到 clear_cache.py 文件，跳过执行。
    goto :run_tree
)

REM 运行 clear_cache.py
echo 正在运行 clear_cache.py...
python clear_cache.py
if %errorlevel% neq 0 (
    echo 错误: 运行 clear_cache.py 失败，退出。
    pause
    exit /b %errorlevel%
)
echo clear_cache.py 执行完毕。

REM 标签：开始运行 tree 命令
:run_tree
echo 正在生成目录树到 tree.txt...

REM 使用 tree 命令生成目录结构
REM /f 参数表示包含文件名
REM /a 参数表示使用 ASCII 字符绘制树状图（适用于大多数控制台）
REM 将输出重定向到 tree.txt
tree /f /a > tree.txt

REM 检查 tree 命令是否成功执行
if %errorlevel% equ 0 (
    echo 目录树已成功保存到 tree.txt。
) else (
    echo 错误: 生成目录树时出现问题。
)

echo 完成。