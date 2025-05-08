import sys
import os

# 获取绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
workspace_root = os.path.abspath(os.path.join(current_dir, "../../.."))

# 确保可以导入 src 目录下的模块
sys.path.insert(0, src_dir)

# 添加项目根目录到sys.path以便可以导入music_recognition_system模块
sys.path.insert(0, workspace_root)

print(f"添加到sys.path的路径:")
print(f"1. src_dir: {src_dir}")
print(f"2. workspace_root: {workspace_root}")
print(f"当前sys.path: {sys.path}")

try:
    from PyQt6.QtWidgets import QApplication
    print("PyQt6 已成功导入")
except ImportError:
    print("未安装 PyQt6，正在尝试安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt6"])
    from PyQt6.QtWidgets import QApplication
    print("PyQt6 安装完成")

# 验证是否可以导入 music_recognition_system 模块
try:
    import music_recognition_system
    print(f"成功导入 music_recognition_system 模块，位置: {music_recognition_system.__file__}")
except ImportError as e:
    print(f"无法导入 music_recognition_system 模块: {str(e)}")
    print("将继续使用模拟类...")

# 导入主应用
from main import main

if __name__ == "__main__":
    main() 