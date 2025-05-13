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
        
    返回:
        成功返回True，失败返回False或(False, error_message)
    """
    # API端点
    url = "http://localhost:5000/api/database/add"
    
    # 检查文件是否存在
    if not os.path.exists(audio_file_path):
        print(f"错误: 文件不存在 - {audio_file_path}")
        return False, "文件不存在"
    
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
        response = requests.post(url, files=files, data=data, timeout=60)
        
        # 检查响应
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("success", False):
                    file_name = result.get('file_name', '')
                    feature_id = result.get('feature_id', '')
                    print(f"成功添加到数据库: {file_name}")
                    print(f"特征ID: {feature_id}")
                    return True
                else:
                    error_msg = result.get('error', '未知错误')
                    details = result.get('details', '')
                    if details:
                        error_msg += f" - {details}"
                    print(f"添加失败: {error_msg}")
                    return False, error_msg
            except json.JSONDecodeError:
                # 无法解析JSON时，检查响应文本
                if "成功" in response.text:
                    print("检测到成功响应（非JSON格式）")
                    return True
                print(f"解析响应失败: {response.text}")
                return False, f"服务器返回非JSON响应: {response.text[:100]}"
        else:
            print(f"请求失败: HTTP {response.status_code}")
            print(response.text)
            return False, f"HTTP错误: {response.status_code}"
    
    except requests.exceptions.Timeout:
        print("请求超时，特征提取可能需要较长时间")
        return False, "请求超时，特征提取可能需要较长时间"
    except requests.exceptions.ConnectionError:
        print("连接错误，请确保后端API服务已启动")
        return False, "连接错误，请确保后端API服务已启动"
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return False, str(e)
    finally:
        # 关闭文件
        try:
            files['audio_file'][1].close()
        except:
            pass

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