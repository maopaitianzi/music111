import sys
import os

# 确保可以导入 src 目录下的模块
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

try:
    from PyQt6.QtWidgets import QApplication
    print("PyQt6 已成功导入")
except ImportError:
    print("未安装 PyQt6，正在尝试安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt6"])
    from PyQt6.QtWidgets import QApplication
    print("PyQt6 安装完成")

# 导入主应用
from main import main

if __name__ == "__main__":
    main() 