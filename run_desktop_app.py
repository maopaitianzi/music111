import os
import sys
import subprocess
import time

def start_backend_api():
    """启动后端API服务"""
    print("正在启动后端API服务...")
    backend_dir = os.path.join(os.getcwd(), "music_recognition_system", "backend")
    cmd = ["python", "run_api.py"]
    
    # 使用Popen启动后台进程
    try:
        process = subprocess.Popen(
            cmd, 
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print(f"后端API服务已启动，PID: {process.pid}")
        return process
    except Exception as e:
        print(f"启动后端API服务失败: {str(e)}")
        return None

def start_desktop_app():
    """启动桌面应用"""
    print("正在启动桌面应用...")
    app_dir = os.path.join(os.getcwd(), "music_recognition_system", "frontend", "desktop_app")
    cmd = ["python", "run.py"]
    
    try:
        process = subprocess.Popen(
            cmd, 
            cwd=app_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print(f"桌面应用已启动 e:，PID: {process.pid}")
        return process
    except Exception as e:
        print(f"启动桌面应用失败: {str(e)}")
        return None

def main():
    """主函数"""
    # 启动后端API
    api_process = start_backend_api()
    if not api_process:
        print("无法启动后端API，程序退出")
        return
    
    # 等待API启动完成
    print("等待后端API服务就绪...")
    time.sleep(3)
    
    # 启动桌面应用
    app_process = start_desktop_app()
    if not app_process:
        print("无法启动桌面应用，正在终止后端API服务...")
        api_process.terminate()
        return
    
    print("\n=====================================================")
    print("音乐识别系统已启动")
    print("使用桌面应用上传音乐文件或使用麦克风录制进行识别")
    print("按Ctrl+C终止程序")
    print("=====================================================\n")
    
    try:
        # 等待用户终止程序
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n用户终止程序，正在关闭服务...")
    finally:
        # 清理进程
        if app_process:
            app_process.terminate()
            print("桌面应用已关闭")
        
        if api_process:
            api_process.terminate()
            print("后端API服务已关闭")
        
        print("程序已退出")

if __name__ == "__main__":
    main() 