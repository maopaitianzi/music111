import os
import sys
import subprocess
import time

def start_backend_api():
    """启动后端API服务"""
    print("正在启动后端API服务...")
    # 使用相对路径获取后端目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(current_dir, "music_recognition_system", "backend")
    cmd = ["python", "run_api.py"]
    
    # 使用Popen启动后台进程
    try:
        process = subprocess.Popen(
            cmd, 
            cwd=backend_dir,
            text=True
        )
        print(f"后端API服务已启动，PID: {process.pid}")
        return process
    except Exception as e:
        print(f"启动后端API服务失败: {str(e)}")
        return None

def start_desktop_app():
    """启动桌面应用"""
    print("正在启动桌面应用...")
    # 使用相对路径获取桌面应用目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.join(current_dir, "music_recognition_system", "frontend", "desktop_app")
    cmd = ["python", "run.py"]
    
    try:
        process = subprocess.Popen(
            cmd, 
            cwd=app_dir,
            text=True
        )
        print(f"桌面应用已启动，PID: {process.pid}")
        return process
    except Exception as e:
        print(f"启动桌面应用失败: {str(e)}")
        return None

def refresh_feature_database():
    """刷新特征库数据，确保歌曲名和作者信息正确显示"""
    print("正在刷新特征库数据结构...")
    
    try:
        # 获取特征库路径，使用相对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        database_path = os.path.join(current_dir, "music_recognition_system/database/music_features_db")
        
        # 验证数据库目录是否存在
        if not os.path.exists(database_path):
            print(f"特征库目录不存在: {database_path}")
            return False
            
        # 检查索引文件
        index_path = os.path.join(database_path, "index.json")
        if not os.path.exists(index_path):
            print(f"特征库索引文件不存在: {index_path}")
            return False
            
        # 尝试加载和更新索引
        try:
            import json
            with open(index_path, 'r', encoding='utf-8') as f:
                feature_index = json.load(f)
                
            # 检查并添加缺失的字段
            updated = False
            for file_id, info in feature_index.items():
                if "song_name" not in info:
                    info["song_name"] = ""
                    updated = True
                if "author" not in info:
                    info["author"] = ""
                    updated = True
                if "cover_path" not in info:
                    info["cover_path"] = ""
                    updated = True
            
            # 如果有更新，保存回文件
            if updated:
                with open(index_path, 'w', encoding='utf-8') as f:
                    json.dump(feature_index, f, ensure_ascii=False, indent=2)
                print("特征库索引已更新")
            else:
                print("特征库索引已是最新格式")
                
            return True
        except Exception as e:
            print(f"更新特征库索引失败: {str(e)}")
            return False
    except Exception as e:
        print(f"刷新特征库失败: {str(e)}")
        return False

def main():
    """主函数"""
    # 刷新特征库数据
    refresh_feature_database()
    
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