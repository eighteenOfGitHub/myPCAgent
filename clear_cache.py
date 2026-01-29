# claer_cache.py

import os
import shutil
import sys
from pathlib import Path

def clear_python_cache(root_dir: Path):
    deleted_count = 0
    print(f"[INFO] 开始清理缓存（根目录: {root_dir.absolute()}）...")

    # 遍历所有文件和目录
    for path in root_dir.rglob("*"):
        if path.is_file():
            # 删除 .pyc, .pyo, .pyd 等字节码文件
            if path.suffix in (".pyc", ".pyo", ".pyd"):
                try:
                    path.unlink()
                    print(f"[INFO]  删除文件: {path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"[WARNING]  无法删除 {path}: {e}")

        elif path.is_dir():
            # 删除 __pycache__ 目录
            if path.name == "__pycache__":
                try:
                    shutil.rmtree(path)
                    print(f"[INFO]  删除目录: {path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"[WARNING]  无法删除 {path}: {e}")

    print(f"[INFO] 清理完成！共删除 {deleted_count} 个缓存项。")

if __name__ == "__main__":
    # 支持传入根目录
    if len(sys.argv) > 1:
        root = Path(sys.argv[1]).resolve()
        if not root.exists():
            print(f"[ERROR] 错误: 路径不存在 - {root}")
            sys.exit(1)
    else:
        root = Path.cwd()

    clear_python_cache(root)