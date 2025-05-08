import requests
import os
import sys
import json

def add_music_to_database(audio_file_path, metadata=None):
    """
    将音乐添加到识别数据库
    
    参数:
        audio_file_path: 音频文件路径
        metadata: 可选的元数据字典，包含歌曲信息
    """
    # API端点
    url = "http://localhost:5000/api/database/add"
    
    # 检查文件是否存在
    if not os.path.exists(audio_file_path):
        print(f"错误: 文件不存在 - {audio_file_path}")
        return
    
    # 准备文件
    files = {
        'audio_file': (os.path.basename(audio_file_path), open(audio_file_path, 'rb'), 'audio/mpeg')
    }
    
    # 如果没有提供元数据，则从文件名创建基本元数据
    if not metadata:
        basename = os.path.basename(audio_file_path)
        name = os.path.splitext(basename)[0]
        metadata = {
            "name": name,
            "artist": "未知艺术家",
            "album": "未知专辑",
            "year": "",
            "genre": "未知"
        }
    
    # 准备表单数据
    data = {
        'metadata': json.dumps(metadata)
    }
    
    # 发送请求
    print(f"正在添加文件到数据库: {os.path.basename(audio_file_path)}...")
    try:
        response = requests.post(url, files=files, data=data)
        
        # 检查响应
        if response.status_code == 200:
            result = response.json()
            if result.get("success", False):
                print(f"成功添加到数据库: {result.get('file_name', '')}")
                print(f"特征ID: {result.get('feature_id', '')}")
            else:
                print(f"添加失败: {result.get('error', '未知错误')}")
        else:
            print(f"请求失败: HTTP {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        # 关闭文件
        files['audio_file'][1].close()

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python add_to_database.py <音频文件路径> [歌曲名] [艺术家] [专辑]")
        print("例如: python add_to_database.py ./Music/test.mp3 \"测试歌曲\" \"测试艺术家\" \"测试专辑\"")
        sys.exit(1)
    
    # 获取音频文件路径
    audio_path = sys.argv[1]
    
    # 如果提供了其他元数据
    metadata = None
    if len(sys.argv) > 2:
        metadata = {
            "name": sys.argv[2],
            "artist": sys.argv[3] if len(sys.argv) > 3 else "未知艺术家",
            "album": sys.argv[4] if len(sys.argv) > 4 else "未知专辑",
            "year": sys.argv[5] if len(sys.argv) > 5 else "",
            "genre": sys.argv[6] if len(sys.argv) > 6 else "未知"
        }
    
    add_music_to_database(audio_path, metadata) 