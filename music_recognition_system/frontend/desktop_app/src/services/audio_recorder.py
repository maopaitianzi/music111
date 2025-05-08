import pyaudio
import wave
import numpy as np
import threading
import time
import os
from PyQt6.QtCore import QObject, pyqtSignal

class AudioRecorder(QObject):
    """音频录制服务类，提供麦克风录音功能"""
    
    # 定义信号
    recording_started = pyqtSignal()            # 录音开始信号
    recording_stopped = pyqtSignal(str)         # 录音停止信号，传递录音文件路径
    recording_error = pyqtSignal(str)           # 录音错误信号
    recording_progress = pyqtSignal(float, np.ndarray)  # 录音进度信号（秒数，音频数据）
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置录制参数
        self.format = pyaudio.paInt16  # 16位
        self.channels = 1              # 单声道
        self.sample_rate = 22050       # 采样率
        self.chunk = 1024              # 每次读取的块大小
        
        # 初始化状态
        self.recording = False
        self.audio = None
        self.stream = None
        self.frames = []
        self.record_thread = None
        self.output_dir = os.path.join(os.path.expanduser("~"), "Music", "Recordings")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 最大录制时间（秒）
        self.max_record_time = 20
    
    def start_recording(self):
        """开始录音"""
        if self.recording:
            return
            
        try:
            # 初始化PyAudio
            self.audio = pyaudio.PyAudio()
            
            # 打开音频流
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            # 重置帧列表
            self.frames = []
            
            # 设置录音状态
            self.recording = True
            
            # 发出开始录音的信号
            self.recording_started.emit()
            
            # 在单独的线程中开始录音
            self.record_thread = threading.Thread(target=self._record)
            self.record_thread.daemon = True
            self.record_thread.start()
            
        except Exception as e:
            self.recording_error.emit(f"启动录音失败: {str(e)}")
    
    def stop_recording(self):
        """停止录音"""
        if not self.recording:
            return
            
        # 设置录音状态
        self.recording = False
        
        # 等待录音线程结束
        if self.record_thread and self.record_thread.is_alive():
            self.record_thread.join(1.0)
        
        # 关闭音频流
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        # 关闭PyAudio
        if self.audio:
            self.audio.terminate()
            self.audio = None
        
        # 保存录音文件
        if self.frames:
            try:
                # 生成文件名
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(self.output_dir, f"recording_{timestamp}.wav")
                
                # 保存为WAV文件
                with wave.open(file_path, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(self.audio.get_sample_size(self.format))
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(b''.join(self.frames))
                
                # 发出停止录音的信号
                self.recording_stopped.emit(file_path)
                
            except Exception as e:
                self.recording_error.emit(f"保存录音文件失败: {str(e)}")
    
    def _record(self):
        """录音线程的执行函数"""
        start_time = time.time()
        
        try:
            # 录音循环
            while self.recording:
                # 检查是否超过最大录制时间
                if time.time() - start_time > self.max_record_time:
                    self.recording = False
                    break
                
                # 读取音频数据
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
                
                # 将数据转换为numpy数组以便处理和可视化
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # 计算当前录制时间
                current_time = time.time() - start_time
                
                # 发出进度信号
                self.recording_progress.emit(current_time, audio_data)
                
        except Exception as e:
            self.recording_error.emit(f"录音过程中出错: {str(e)}")
            self.recording = False
            
        # 如果录音停止，确保调用stop_recording来清理资源
        if not self.recording:
            # 在主线程中调用stop_recording
            # 注意：这里可能需要使用QTimer或其他方法在主线程中调用
            self.stop_recording() 