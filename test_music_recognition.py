import requests
import os
import sys
import json
import time
import numpy as np
from typing import Dict, Any, List

def test_music_recognition(audio_file_path, detailed=False):
    """
    测试音乐识别API
    
    参数:
        audio_file_path: 音频文件路径
        detailed: 是否显示详细匹配信息
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
    start_time = time.time()
    
    try:
        response = requests.post(url, files=files)
        
        # 检查响应
        if response.status_code == 200:
            result = response.json()
            
            # 计算识别耗时
            elapsed_time = time.time() - start_time
            
            if result["success"]:
                print("\n识别结果:")
                print(f"歌曲名称: {result.get('song_name', '未知')}")
                print(f"艺术家: {result.get('artist', '未知')}")
                print(f"专辑: {result.get('album', '未知')}")
                print(f"发行年份: {result.get('release_year', '未知')}")
                print(f"流派: {result.get('genre', '未知')}")
                print(f"匹配置信度: {result.get('confidence', 0):.4f}")
                print(f"识别耗时: {elapsed_time:.2f} 秒")
                
                # 如果请求详细模式，显示匹配特征的详细信息
                if detailed and "feature_matches" in result:
                    print("\n匹配特征详情:")
                    for feature, score in result.get("feature_matches", {}).items():
                        print(f"- {feature}: {score:.4f}")
            else:
                print(f"识别失败: {result.get('error', '未知错误')}")
                
                # 即使识别失败也显示匹配分数（如果有的话）
                if detailed and "feature_matches" in result:
                    print("\n匹配特征详情 (尽管匹配失败):")
                    for feature, score in result.get("feature_matches", {}).items():
                        print(f"- {feature}: {score:.4f}")
                    print(f"总体匹配置信度: {result.get('confidence', 0):.4f}")
                    print("注意: 尽管特征匹配分数高，但可能因为置信度阈值设置或库中无此歌曲而匹配失败")
        else:
            print(f"请求失败: HTTP {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        # 关闭文件
        files['audio_file'][1].close()

def test_feature_extraction(audio_file_path):
    """
    测试特征提取，显示提取的特征信息
    
    参数:
        audio_file_path: 音频文件路径
    """
    # 导入特征提取器
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from music_recognition_system.utils.audio_features import AudioFeatureExtractor
    except ImportError:
        print("错误: 无法导入AudioFeatureExtractor")
        return
    
    # 检查文件是否存在
    if not os.path.exists(audio_file_path):
        print(f"错误: 文件不存在 - {audio_file_path}")
        return
    
    # 创建特征提取器
    extractor = AudioFeatureExtractor()
    
    # 开始计时
    start_time = time.time()
    
    # 提取特征
    print(f"正在提取特征: {os.path.basename(audio_file_path)}...")
    features = extractor.extract_features(audio_file_path)
    
    # 计算耗时
    elapsed_time = time.time() - start_time
    
    if "error" in features:
        print(f"提取特征失败: {features['error']}")
        return
    
    # 显示特征摘要
    print("\n特征提取结果摘要:")
    print(f"文件: {os.path.basename(audio_file_path)}")
    print(f"时长: {features.get('duration', 0):.2f} 秒")
    print(f"提取耗时: {elapsed_time:.2f} 秒")
    
    # 显示特征类型和大小
    print("\n提取的特征:")
    for key, value in features.items():
        if isinstance(value, list):
            if len(value) > 0 and isinstance(value[0], list):
                print(f"- {key}: 二维数组 [{len(value)}x{len(value[0])}]")
            else:
                print(f"- {key}: 数组 [{len(value)}]")
        elif isinstance(value, (int, float)):
            print(f"- {key}: {value}")
        elif isinstance(value, str) and key not in ["file_path", "file_name", "added_time"]:
            print(f"- {key}: {value}")
    
    # 展示一些特征的样本值
    print("\n特征样本值:")
    if "mfcc_mean" in features:
        print(f"MFCC均值前5个系数: {np.array(features['mfcc_mean'][:5])}")
    if "chroma_mean" in features:
        print(f"色度特征均值: {np.array(features['chroma_mean'])}")
    if "spectral_centroid_mean" in features:
        print(f"谱质心均值: {features['spectral_centroid_mean']}")
    if "tempo" in features:
        print(f"节奏: {features['tempo']} BPM")

def get_database_info():
    """
    获取数据库状态信息
    """
    # API端点
    url = "http://localhost:5000/api/database/status"
    
    try:
        print("查询特征数据库信息...")
        response = requests.get(url)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success", False):
                print(f"\n数据库状态:")
                print(f"总歌曲数: {result.get('total_songs', 0)}")
                
                songs = result.get("songs", [])
                if songs:
                    print("\n数据库中的歌曲示例:")
                    for i, song in enumerate(songs[:10], 1):
                        print(f"{i}. {song.get('song_name', 'N/A')} - {song.get('author', 'N/A')}")
                        print(f"   文件: {song.get('file_name', 'N/A')}")
                        print(f"   ID: {song.get('id', 'N/A')}")
                        print()
                else:
                    print("数据库中没有歌曲")
                    
                print("提示: 使用python add_to_database.py <音频文件路径>添加音乐到数据库")
            else:
                print(f"查询失败: {result.get('error', '未知错误')}")
        else:
            print(f"请求失败: HTTP {response.status_code}")
            print(response.text)
            print("\n提示: 请确保后端API服务正在运行")
    except Exception as e:
        print(f"查询数据库信息时出错: {str(e)}")
        print("提示: 请确保后端API服务正在运行 (python music_recognition_system/backend/run_api.py)")

def add_song_to_database(audio_file_path):
    """
    添加歌曲到特征数据库
    
    参数:
        audio_file_path: 音频文件路径
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
    
    # 发送请求
    print(f"正在添加文件到数据库: {os.path.basename(audio_file_path)}...")
    
    try:
        response = requests.post(url, files=files)
        
        # 检查响应
        if response.status_code == 200:
            result = response.json()
            if result.get("success", False):
                print(f"成功: {result.get('message', '添加成功')}")
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
    if len(sys.argv) < 2 or (len(sys.argv) >= 2 and sys.argv[1] == "--help"):
        print("使用方法:")
        print("  音乐识别测试: python test_music_recognition.py <音频文件路径> [--detailed]")
        print("  特征提取测试: python test_music_recognition.py --extract <音频文件路径>")
        print("  数据库信息: python test_music_recognition.py --database-info")
        print("  添加歌曲到数据库: python test_music_recognition.py --add <音频文件路径>")
        print("例如:")
        print("  python test_music_recognition.py ./Music/test.mp3")
        print("  python test_music_recognition.py ./Music/test.mp3 --detailed")
        print("  python test_music_recognition.py --extract ./Music/test.mp3")
        print("  python test_music_recognition.py --database-info")
        print("  python test_music_recognition.py --add ./Music/test.mp3")
        sys.exit(1)
    
    # 解析命令行参数
    if sys.argv[1] == "--extract" and len(sys.argv) >= 3:
        # 特征提取测试
        test_feature_extraction(sys.argv[2])
    elif sys.argv[1] == "--database-info":
        # 查询数据库信息
        get_database_info()
    elif sys.argv[1] == "--add" and len(sys.argv) >= 3:
        # 添加歌曲到数据库
        add_song_to_database(sys.argv[2])
    else:
        # 音乐识别测试
        detailed = "--detailed" in sys.argv
        audio_path = sys.argv[1] if sys.argv[1] != "--detailed" else sys.argv[2]
        test_music_recognition(audio_path, detailed) 