import os
import sys

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 添加src/main/python目录到Python路径
python_dir = os.path.join(current_dir, "src", "main", "python")
if python_dir not in sys.path:
    sys.path.insert(0, python_dir)

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # 导入并运行API
    from music_recognition_api import app
    
    print("启动音乐识别API服务...")
    print(f"项目根目录: {project_root}")
    print(f"Python路径: {sys.path}")
    
    # 创建临时目录，使用相对路径
    temp_dir = os.path.join(current_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 运行Flask应用
    app.run(debug=True, host='0.0.0.0', port=5000)
    
except ImportError as e:
    print(f"导入失败: {str(e)}")
    print("检查Python路径和依赖项是否正确安装")
    sys.exit(1)
except Exception as e:
    print(f"启动服务失败: {str(e)}")
    sys.exit(1) 