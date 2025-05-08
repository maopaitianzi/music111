import requests
import os
import sys

def test_music_recognition(audio_file_path):
    """
    测试音乐识别API
    
    参数:
        audio_file_path: 音频文件路径
    """
    # API端点
    url = "http://localhost:5000/api/recognize"
    
    # 检查文件是否存在
    if not os.path.exists(audio_file_path):
        print(f"错误: 文件不存在 - {audio_file_path}")
        return
    
    # 准备文件
    files = {
        'audio_file': (os.path.basename(audio_file_path), open(audio_file_path, 'rb'), 'audio/mpeg')
    }
    
    # 发送请求
    print(f"正在发送文件: {os.path.basename(audio_file_path)}...")
    try:
        response = requests.post(url, files=files)
        
        # 检查响应
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print("\n识别结果:")
                print(f"歌曲名称: {result.get('song_name', '未知')}")
                print(f"艺术家: {result.get('artist', '未知')}")
                print(f"专辑: {result.get('album', '未知')}")
                print(f"发行年份: {result.get('release_year', '未知')}")
                print(f"流派: {result.get('genre', '未知')}")
                print(f"匹配置信度: {result.get('confidence', 0):.2f}")
            else:
                print(f"识别失败: {result.get('error', '未知错误')}")
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
        print("使用方法: python test_music_recognition.py <音频文件路径>")
        print("例如: python test_music_recognition.py ./Music/test.mp3")
        sys.exit(1)
    
    # 获取音频文件路径
    audio_path = sys.argv[1]
    test_music_recognition(audio_path) 