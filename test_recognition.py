import os
import sys
import time

# 确保能够导入MusicRecognitionService
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
if "music_recognition_system" not in current_dir:
    sys.path.append(os.path.join(current_dir, "music_recognition_system"))

# 导入音乐识别服务
from music_recognition_system.frontend.desktop_app.src.services.music_recognition_service import MusicRecognitionService

# 创建结果回调函数
def on_recognition_completed(result):
    print("\n===== 识别结果 =====")
    print(f"歌曲名: {result['song_name']}")
    print(f"艺术家: {result['artist']}")
    print(f"准确率: {result['confidence']:.4f} ({result['confidence']*100:.2f}%)")
    print(f"专辑: {result['album']}")
    print(f"是否本地识别: {result.get('is_local_recognition', False)}")
    print("===================\n")
    
def on_recognition_error(error_msg):
    print(f"识别错误: {error_msg}")

def main():
    print("开始测试音乐识别服务...")
    
    # 创建服务实例
    service = MusicRecognitionService()
    
    # 连接信号
    service.recognition_completed.connect(on_recognition_completed)
    service.recognition_error.connect(on_recognition_error)
    
    # 测试不同音频文件
    test_files = []
    
    # 查找测试用音频文件
    for root, _, files in os.walk(current_dir):
        for file in files:
            if file.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
                test_files.append(os.path.join(root, file))
    
    if not test_files:
        print("未找到测试用音频文件，请确保有mp3/wav/ogg/flac格式的音频文件")
        print("正在创建测试文件...")
        # 创建一个简单的测试文件
        import numpy as np
        import soundfile as sf
        
        # 生成一些简单的音频数据
        sr = 44100  # 采样率
        t = np.linspace(0, 5, sr*5)  # 5秒时长
        
        # 创建三个不同的测试音频
        # 1. 简单的正弦波
        audio1 = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440Hz的A音符
        sf.write("test_sine.wav", audio1, sr)
        test_files.append(os.path.join(current_dir, "test_sine.wav"))
        
        # 2. 复杂的混合波
        audio2 = 0.3 * np.sin(2 * np.pi * 440 * t) + 0.2 * np.sin(2 * np.pi * 880 * t)
        sf.write("test_complex.wav", audio2, sr)
        test_files.append(os.path.join(current_dir, "test_complex.wav"))
        
        # 3. 随机噪声
        audio3 = 0.1 * np.random.randn(len(t))
        sf.write("test_noise.wav", audio3, sr)
        test_files.append(os.path.join(current_dir, "test_noise.wav"))
        
        print(f"创建了3个测试文件")
        
    # 测试每个文件
    print(f"找到{len(test_files)}个测试文件:")
    for i, file_path in enumerate(test_files[:3]):  # 只测试前3个文件
        print(f"\n测试文件 {i+1}: {os.path.basename(file_path)}")
        service.recognize_file(file_path)
        time.sleep(2)  # 等待结果处理完成
    
    print("\n测试完成!")

if __name__ == "__main__":
    main() 