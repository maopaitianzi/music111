import os
import sys
import io
import time
import requests
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QFileDialog, QStackedWidget, QFrame, QSlider,
    QMessageBox, QStyleOption, QStyle, QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl, QTimer, QThread, pyqtSignal, QSize, QMimeData
from PyQt6.QtGui import QPixmap, QFont, QPalette, QColor, QPainter, QBrush, QDragEnterEvent, QDropEvent
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

# 导入PIL用于图像处理
from PIL import Image, ImageQt

# 引入服务
from music_recognition_system.frontend.desktop_app.src.services.music_recognition_service import MusicRecognitionService
from music_recognition_system.frontend.desktop_app.src.services.audio_recorder import AudioRecorder

# 确保系统路径包含项目根目录，以便导入utils包
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

# 现在可以从utils中导入音频特征相关类
# 导入会在实际需要时执行

class MusicRecognitionThread(QThread):
    """识别音乐的线程，避免UI卡顿"""
    result_ready = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, audio_path):
        super().__init__()
        self.audio_path = audio_path
        self.service = MusicRecognitionService()
        
    def run(self):
        try:
            # 初始化服务
            self.service.recognition_completed.connect(lambda result: self.result_ready.emit(result))
            self.service.recognition_error.connect(lambda error: self.error.emit(error))
            
            # 调用识别方法
            self.service.recognize_file(self.audio_path)
        
        except Exception as e:
            self.error.emit(f"识别过程中出错: {str(e)}")

class MusicPlayerWidget(QWidget):
    """音乐播放器小部件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 播放器控件
        player_layout = QHBoxLayout()
        
        # 播放/暂停按钮
        self.play_button = QPushButton()
        self.play_button.setText("播放")
        self.play_button.setFixedSize(80, 36)
        
        # 使用字体对象设置字体
        button_font = QFont()
        button_font.setPointSize(11)
        button_font.setBold(True)
        self.play_button.setFont(button_font)
        
        # 设置调色板强制文字颜色
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#FFFFFF"))
        self.play_button.setPalette(palette)
        
        # 将文本对齐方式设置为居中
        self.play_button.setProperty("text-align", "center")
        
        # 设置风格表
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: #FFFFFF;
                border-radius: 18px;
                border: 1px solid #0A8C3C;
                padding: 5px;
                text-align: center;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1ED760;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                color: #FFFFFF;
            }
        """)
        
        # 进度条
        self.progress_bar = QSlider(Qt.Orientation.Horizontal)
        self.progress_bar.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #E0E0E0;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #1DB954;
                border: 1px solid #1DB954;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
        """)
        
        # 时间标签
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #666666; font-size: 12px;")
        
        player_layout.addWidget(self.play_button)
        player_layout.addWidget(self.progress_bar)
        player_layout.addWidget(self.time_label)
        
        layout.addLayout(player_layout)
        self.setLayout(layout)
        
        # 音乐播放器
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # 连接信号
        self.play_button.clicked.connect(self.toggle_playback)
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.progress_bar.sliderMoved.connect(self.set_position)
        
    def toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_button.setText("播放")
        else:
            self.player.play()
            self.play_button.setText("暂停")
    
    def set_media(self, url):
        self.player.setSource(QUrl.fromLocalFile(url))
        self.audio_output.setVolume(50)
        self.progress_bar.setValue(0)
        self.time_label.setText("00:00 / 00:00")
        
    def update_position(self, position):
        # 更新进度条
        self.progress_bar.setValue(position)
        
        # 更新时间标签
        duration = self.player.duration()
        
        # 格式化位置和持续时间
        position_sec = position // 1000
        position_min = position_sec // 60
        position_sec %= 60
        
        duration_sec = duration // 1000
        duration_min = duration_sec // 60
        duration_sec %= 60
        
        time_text = f"{position_min:02d}:{position_sec:02d} / {duration_min:02d}:{duration_sec:02d}"
        self.time_label.setText(time_text)
    
    def update_duration(self, duration):
        # 设置进度条范围
        self.progress_bar.setRange(0, duration)
        
    def set_position(self, position):
        self.player.setPosition(position)

class RecordingWidget(QWidget):
    """录音小部件"""
    
    recording_finished = pyqtSignal(str)  # 录音完成信号，传递音频文件路径
    recording_cancelled = pyqtSignal()    # 录音取消信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_recorder()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 录音状态标签
        self.status_label = QLabel("准备录音...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px 0;")
        
        # 录音时间显示
        self.time_label = QLabel("00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #1DB954;")
        
        # 录音波形显示（占位）
        self.waveform_widget = QFrame()
        self.waveform_widget.setMinimumHeight(100)
        self.waveform_widget.setFrameShape(QFrame.Shape.StyledPanel)
        self.waveform_widget.setStyleSheet("background-color: #F0F0F0; border-radius: 5px;")
        
        # 录音说明
        self.instruction_label = QLabel("请对着麦克风说话或播放音乐...\n最长录音时间为20秒")
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setStyleSheet("color: #666666; margin: 10px 0;")
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 停止录音按钮
        self.stop_button = QPushButton("停止录音")
        self.stop_button.setFixedSize(120, 40)
        self.stop_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: #FFFFFF;
                border-radius: 20px;
                border: 1px solid #0A8C3C;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #1ED760;
            }
            QPushButton:pressed {
                background-color: #0A8C3C;
            }
        """)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setFixedSize(120, 40)
        self.cancel_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: #FFFFFF;
                border-radius: 20px;
                border: 1px solid #C0392B;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #FF5E52;
            }
            QPushButton:pressed {
                background-color: #C0392B;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.stop_button)
        button_layout.addSpacing(20)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        
        # 添加到主布局
        layout.addWidget(self.status_label)
        layout.addWidget(self.time_label)
        layout.addWidget(self.waveform_widget)
        layout.addWidget(self.instruction_label)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 连接信号
        self.stop_button.clicked.connect(self.stop_recording)
        self.cancel_button.clicked.connect(self.cancel_recording)
        
    def setup_recorder(self):
        """设置录音机"""
        self.recorder = AudioRecorder()
        
        # 连接信号
        self.recorder.recording_started.connect(self.on_recording_started)
        self.recorder.recording_stopped.connect(self.on_recording_stopped)
        self.recorder.recording_error.connect(self.on_recording_error)
        self.recorder.recording_progress.connect(self.on_recording_progress)
        
    def start_recording(self):
        """开始录音"""
        self.recorder.start_recording()
        
    def stop_recording(self):
        """停止录音"""
        self.recorder.stop_recording()
        
    def cancel_recording(self):
        """取消录音"""
        self.recorder.stop_recording()
        self.recording_cancelled.emit()
        
    def on_recording_started(self):
        """录音开始回调"""
        self.status_label.setText("正在录音...")
        
    def on_recording_stopped(self, file_path):
        """录音停止回调"""
        self.status_label.setText("录音完成")
        self.recording_finished.emit(file_path)
        
    def on_recording_error(self, error_message):
        """录音错误回调"""
        self.status_label.setText("录音出错")
        QMessageBox.critical(self, "录音错误", error_message)
        self.recording_cancelled.emit()
        
    def on_recording_progress(self, seconds, audio_data):
        """录音进度回调"""
        # 更新时间显示
        minutes = int(seconds) // 60
        seconds = int(seconds) % 60
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")
        
        # 更新波形显示
        # 在实际应用中，这里可以添加波形可视化
        # 简化版中我们只改变背景色来表示有音频在录制
        intensity = min(abs(audio_data).mean() / 5000, 1.0)  # 音量强度
        color = QColor(
            int(255 * (1 - intensity * 0.5)), 
            int(255 * (0.6 + intensity * 0.4)),
            int(255 * (1 - intensity)),
            255
        )
        self.waveform_widget.setStyleSheet(f"background-color: {color.name()}; border-radius: 5px;")

# 添加自定义拖放组件
class DropArea(QWidget):
    """支持拖放音频文件的小部件"""
    
    fileDropped = pyqtSignal(str)  # 文件放置信号，传递文件路径
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)  # 启用拖放
        
        # 设置样式
        self.setStyleSheet("""
            background-color: #F7F7F7;
            border: 2px dashed #999999;
            border-radius: 10px;
            padding: 20px;
        """)
        
        # 初始化
        self.normal_style = self.styleSheet()
        self.highlight_style = """
            background-color: #E6F7E6;
            border: 2px dashed #1DB954;
            border-radius: 10px;
            padding: 20px;
        """
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 添加图标
        self.icon_label = QLabel()
        self.icon_label.setText("🎵")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 72px; color: #444444;")
        
        # 添加文字说明
        self.text_label = QLabel("拖放音频文件到这里或点击选择文件")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("color: #444444; margin-top: 10px; font-size: 16px; font-weight: bold;")
        
        # 添加按钮区域
        self.buttons_layout = QHBoxLayout()
        
        # 上传音频按钮
        self.upload_button = QPushButton()
        self.upload_button.setText("选择文件")
        self.upload_button.setFixedSize(120, 40)
        self.upload_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: #FFFFFF;
                border-radius: 20px;
                border: 1px solid #0A8C3C;
                padding: 5px;
                text-align: center;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1ED760;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                color: #FFFFFF;
            }
        """)
        
        # 添加组件到布局中
        self.buttons_layout.addStretch()
        self.buttons_layout.addWidget(self.upload_button)
        self.buttons_layout.addStretch()
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addLayout(self.buttons_layout)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """当拖动进入组件区域时"""
        # 检查是否包含文件
        if event.mimeData().hasUrls():
            # 检查是否为支持的音频文件
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if self.is_audio_file(file_path):
                    event.acceptProposedAction()
                    # 切换到高亮样式
                    self.setStyleSheet(self.highlight_style)
                    self.text_label.setText("释放鼠标上传文件")
                    self.text_label.setStyleSheet("color: #1DB954; margin-top: 10px; font-size: 16px; font-weight: bold;")
                    return
        
        event.ignore()
    
    def dragLeaveEvent(self, event):
        """当拖动离开组件区域时"""
        # 恢复正常样式
        self.setStyleSheet(self.normal_style)
        self.text_label.setText("拖放音频文件到这里或点击选择文件")
        self.text_label.setStyleSheet("color: #444444; margin-top: 10px; font-size: 16px; font-weight: bold;")
        event.accept()
    
    def dragMoveEvent(self, event):
        """当拖动在组件内移动时"""
        # 判断是否包含文件
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """当放置文件时"""
        # 恢复正常样式
        self.setStyleSheet(self.normal_style)
        self.text_label.setText("拖放音频文件到这里或点击选择文件")
        self.text_label.setStyleSheet("color: #444444; margin-top: 10px; font-size: 16px; font-weight: bold;")
        
        # 获取文件路径
        urls = event.mimeData().urls()
        if urls:
            # 获取第一个文件
            file_path = urls[0].toLocalFile()
            if self.is_audio_file(file_path):
                # 发送信号
                self.fileDropped.emit(file_path)
                event.acceptProposedAction()
            else:
                QMessageBox.warning(self, "不支持的文件类型", "请上传MP3、WAV、OGG、FLAC或M4A格式的音频文件。")
                event.ignore()
        else:
            event.ignore()
    
    def is_audio_file(self, file_path: str) -> bool:
        """检查是否为支持的音频文件"""
        supported_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']
        return any(file_path.lower().endswith(ext) for ext in supported_extensions)

class RecognitionTab(QWidget):
    """音乐识别选项卡"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
        # 初始化音乐识别服务
        self.recognition_service = MusicRecognitionService()
        
    def reload_feature_database(self):
        """重新加载特征数据库"""
        try:
            print("正在重新加载特征数据库...")
            if hasattr(self, 'recognition_service'):
                self.recognition_service.reload_feature_database()
                print("特征数据库重新加载完成")
        except Exception as e:
            print(f"重新加载特征数据库出错: {str(e)}")
            traceback.print_exc()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 顶部标题
        title = QLabel("识别音乐")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px 0; color: #1DB954;")
        
        # 创建堆叠小部件来存放不同页面
        self.stacked_widget = QStackedWidget()
        
        # 上传页面
        self.upload_page = QWidget()
        self.setup_upload_page(self.upload_page)
        
        # 结果页面
        self.result_page = QWidget()
        self.setup_result_page(self.result_page)
        
        # 录音页面
        self.recording_page = QWidget()
        self.setup_recording_page(self.recording_page)
        
        # 将页面添加到堆叠部件
        self.stacked_widget.addWidget(self.upload_page)  # 索引0
        self.stacked_widget.addWidget(self.result_page)  # 索引1
        self.stacked_widget.addWidget(self.recording_page)  # 索引2
        
        # 默认显示上传页面
        self.stacked_widget.setCurrentIndex(0)
        
        # 处理识别进度的进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                text-align: center;
                background-color: #F7F7F7;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #1DB954;
                border-radius: 5px;
            }
        """)
        self.progress_bar.setVisible(False)
        
        # 添加到主布局
        layout.addWidget(title)
        layout.addWidget(self.stacked_widget)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
    
    def setup_upload_page(self, page):
        """设置上传页面"""
        layout = QVBoxLayout(page)
        
        # 创建拖放区域
        self.drop_area = DropArea()
        
        # 连接文件选择按钮
        self.drop_area.upload_button.clicked.connect(self.open_file_dialog)
        
        # 连接拖放信号
        self.drop_area.fileDropped.connect(self.start_recognition)
        
        # 添加拖放区域到上传页面
        layout.addWidget(self.drop_area)
    
    def setup_result_page(self, page):
        """设置结果页面"""
        # 使用网格布局替代垂直布局，提高自适应性
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)  # 减小外边距，增加可用空间
        
        # 使result_page支持背景图片显示
        page.setAutoFillBackground(True)
        page.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # 设置结果页面为透明面板，以便显示背景图片
        panel = QFrame()
        panel.setObjectName("result_panel")  # 设置对象名，方便样式表引用
        panel.setStyleSheet("""
            #result_panel {
                background-color: rgba(255, 255, 255, 0.75);  /* 更透明的白色背景 */
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.9);
            }
            
            /* 自适应小屏幕 */
            @media (max-width: 800px) {
                #result_panel {
                    border-radius: 10px;
                    margin: 10px;
                }
            }
        """)
        
        # 使用网格布局代替垂直布局
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(25, 25, 25, 25)  # 内边距
        panel_layout.setSpacing(15)  # 组件之间的间距
        
        # 结果标题
        result_title = QLabel("识别结果")
        result_title.setObjectName("result_title")
        result_title.setStyleSheet("""
            #result_title {
                font-size: 28px; 
                font-weight: bold; 
                color: #1DB954;
                font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
                letter-spacing: 1px;
            }
            
            /* 自适应小屏幕 */
            @media (max-width: 800px) {
                #result_title {
                    font-size: 22px; 
                }
            }
        """)
        result_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # 结果内容布局 - 使用网格布局替代水平布局，增强自适应性
        result_layout = QHBoxLayout()
        result_layout.setSpacing(25)  # 间距
        result_layout.setStretch(1, 1)  # 让右侧信息区域占据更多空间
        
        # 封面图像标签
        self.cover_label = QLabel("🎵")
        self.cover_label.setObjectName("cover_label")
        # 使用最小尺寸而不是固定尺寸
        self.cover_label.setMinimumSize(140, 140)  
        self.cover_label.setMaximumSize(200, 200)  # 限制最大尺寸
        self.cover_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet("""
            background-color: #EEEEEE; 
            border-radius: 10px; 
            font-size: 64px;
            border: 2px solid #FFFFFF;
        """)
        
        # 文本信息布局
        info_layout = QVBoxLayout()
        info_layout.setSpacing(12)  # 增加文本间距
        
        # 歌曲信息标签 - 美化样式
        self.song_label = QLabel("未识别")
        self.song_label.setObjectName("song_label")
        self.song_label.setWordWrap(True)  # 允许文本换行
        self.song_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.song_label.setStyleSheet("""
            #song_label {
                font-size: 26px; 
                font-weight: bold; 
                color: #222222;
                font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
            }
            
            /* 自适应小屏幕 */
            @media (max-width: 800px) {
                #song_label {
                    font-size: 20px; 
                }
            }
        """)
        
        self.artist_label = QLabel("歌手: 未知")
        self.artist_label.setObjectName("artist_label")
        self.artist_label.setWordWrap(True)  # 允许文本换行
        self.artist_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.artist_label.setStyleSheet("""
            #artist_label {
                font-size: 18px; 
                color: #333333; 
                font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
                font-weight: 500;
            }
            
            /* 自适应小屏幕 */
            @media (max-width: 800px) {
                #artist_label {
                    font-size: 16px; 
                }
            }
        """)
        
        self.album_label = QLabel("歌曲名: 未知")
        self.album_label.setObjectName("album_label")
        self.album_label.setWordWrap(True)
        self.album_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.album_label.setStyleSheet("""
            #album_label {
                font-size: 16px; 
                color: #444444; 
                font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
            }
        """)
        
        self.year_label = QLabel("发行年份: 未知")
        self.year_label.setObjectName("year_label")
        self.year_label.setWordWrap(True)
        self.year_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.year_label.setStyleSheet("""
            #year_label {
                font-size: 16px; 
                color: #444444; 
                font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
            }
        """)
        
        self.genre_label = QLabel("流派: 未知")
        self.genre_label.setObjectName("genre_label")
        self.genre_label.setWordWrap(True)
        self.genre_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.genre_label.setStyleSheet("""
            #genre_label {
                font-size: 16px; 
                color: #444444; 
                font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
            }
        """)
        
        self.confidence_label = QLabel("置信度: 0%")
        self.confidence_label.setObjectName("confidence_label")
        self.confidence_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.confidence_label.setStyleSheet("""
            #confidence_label {
                font-size: 16px; 
                color: #1DB954; 
                margin-top: 15px;
                font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
                font-weight: bold;
                border-radius: 10px;
                padding: 3px 8px;
                background-color: rgba(29, 185, 84, 0.1);
            }
        """)
        
        # 添加信息标签到布局
        info_layout.addWidget(self.song_label)
        info_layout.addWidget(self.artist_label)
        info_layout.addWidget(self.album_label)
        info_layout.addWidget(self.year_label)
        info_layout.addWidget(self.genre_label)
        info_layout.addWidget(self.confidence_label)
        info_layout.addStretch(1)  # 添加弹性空间
        
        # 操作按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 10, 0, 0)  # 添加上边距
        
        # 在歌曲库中搜索按钮
        self.search_button = QPushButton("在歌曲库中搜索")
        self.search_button.setObjectName("search_button")
        # 使用最小尺寸而不是固定尺寸
        self.search_button.setMinimumSize(140, 40)
        self.search_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.search_button.setStyleSheet("""
            #search_button {
                background-color: #1DB954;
                color: #FFFFFF;
                border-radius: 20px;
                border: none;
                padding: 5px 15px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
            }
            #search_button:hover {
                background-color: #1ED760;
            }
            #search_button:pressed {
                background-color: #0A8C3C;
            }
            
            /* 自适应小屏幕 */
            @media (max-width: 800px) {
                #search_button {
                    font-size: 12px;
                    padding: 3px 10px;
                }
            }
        """)
        self.search_button.clicked.connect(self.search_in_library)
        buttons_layout.addWidget(self.search_button)
        buttons_layout.addStretch(1)  # 添加弹性空间
        
        # 自动搜索复选框
        self.auto_search_enabled = False  # 默认关闭自动搜索
        
        # 添加到信息布局
        info_layout.addLayout(buttons_layout)
        
        # 将封面和信息添加到结果布局
        result_layout.addWidget(self.cover_label)
        result_layout.addLayout(info_layout, 1)  # 为信息布局添加伸缩因子
        
        # 创建音乐播放器部件
        self.player_widget = MusicPlayerWidget()
        self.player_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # 返回按钮
        self.back_button = QPushButton("返回")
        self.back_button.setObjectName("back_button")
        self.back_button.setMinimumSize(90, 36)
        self.back_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.back_button.setStyleSheet("""
            #back_button {
                background-color: #EEEEEE;
                color: #333333;
                border-radius: 18px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
            }
            #back_button:hover {
                background-color: #D0D0D0;
            }
            
            /* 自适应小屏幕 */
            @media (max-width: 800px) {
                #back_button {
                    font-size: 12px;
                    padding: 5px 10px;
                }
            }
        """)
        self.back_button.clicked.connect(self.show_upload_page)
        
        # 添加组件到面板布局
        panel_layout.addWidget(result_title)
        panel_layout.addLayout(result_layout, 1)  # 添加伸缩因子
        panel_layout.addWidget(self.player_widget)
        panel_layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # 将面板添加到结果页面
        layout.addWidget(panel, 1)  # 添加伸缩因子
    
    def setup_recording_page(self, page):
        """设置录音页面"""
        layout = QVBoxLayout(page)
        
        # 创建录音控件
        self.recording_widget = RecordingWidget()
        
        # 连接信号
        self.recording_widget.recording_finished.connect(self.on_recording_finished)
        self.recording_widget.recording_cancelled.connect(self.show_upload_page)
        
        # 添加到页面
        layout.addWidget(self.recording_widget)
    
    def show_upload_page(self):
        """显示上传页面"""
        self.stacked_widget.setCurrentIndex(0)
        self.progress_bar.setVisible(False)
        
        # 停止音乐播放
        if hasattr(self, 'player_widget') and self.player_widget.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player_widget.player.pause()
            self.player_widget.play_button.setText("播放")
    
    def show_result_page(self):
        """显示结果页面"""
        self.stacked_widget.setCurrentIndex(1)
    
    def show_recording_page(self):
        """显示录音页面并开始录音"""
        self.stacked_widget.setCurrentIndex(2)
        # 启动录音
        self.recording_widget.start_recording()
    
    def open_file_dialog(self):
        """打开文件选择对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "", "音频文件 (*.mp3 *.wav *.ogg *.flac *.m4a)"
        )
        
        if file_path:
            self.start_recognition(file_path)
    
    def start_recognition(self, file_path):
        """开始识别音频文件"""
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 模拟进度
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(50)
        
        # 启动识别线程
        self.recognition_thread = MusicRecognitionThread(file_path)
        self.recognition_thread.result_ready.connect(self.handle_recognition_result)
        self.recognition_thread.error.connect(self.handle_recognition_error)
        self.recognition_thread.start()
        
        # 设置播放器媒体
        self.player_widget.set_media(file_path)
    
    def on_recording_finished(self, file_path):
        """录音完成回调"""
        # 延迟一秒返回上传页面
        QTimer.singleShot(1000, lambda: self.start_recognition(file_path))
    
    def update_progress(self):
        """更新进度条"""
        current_value = self.progress_bar.value()
        if current_value < 100:
            self.progress_bar.setValue(current_value + 1)
        else:
            self.timer.stop()
    
    def handle_recognition_result(self, result):
        """处理识别结果"""
        self.progress_bar.setValue(100)
        self.timer.stop()
        
        # 无论识别成功与否，都显示结果页面和隐藏进度条
        # 切换到结果页面
        self.show_result_page()
            
        # 延迟隐藏进度条
        QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))
        
        if result.get("success", False):
            # 获取识别结果中的文件名或歌曲名
            original_song_name = result["song_name"]
            # 优先使用识别结果中的艺术家信息
            artist_name = result["artist"]
            cover_path = ""  # 初始化封面路径变量
            
            # 尝试从特征库中获取更详细的歌曲信息
            try:
                # 获取特征库路径
                current_dir = os.path.dirname(os.path.abspath(__file__))
                workspace_root = os.path.abspath(os.path.join(current_dir, "../../../../../"))
                database_path = os.path.join(workspace_root, "music_recognition_system/database/music_features_db")
                
                from music_recognition_system.utils.audio_features import FeatureDatabase
                db = FeatureDatabase(database_path)
                all_files = db.get_all_files()
                
                # 尝试根据文件名或歌曲名查找匹配项
                matched_file = None
                for file_info in all_files:
                    # 检查ID、文件名或歌曲名是否匹配
                    if (file_info["id"] == original_song_name or 
                        file_info["file_name"] == original_song_name or
                        file_info.get("song_name") == original_song_name):
                        matched_file = file_info
                        break
                    
                    # 如果文件名包含歌曲名，也视为匹配
                    if original_song_name and original_song_name in file_info.get("file_name", ""):
                        matched_file = file_info
                        break
                
                # 如果找到匹配项且有歌曲名
                if matched_file:
                    # 更新歌曲名
                    if matched_file.get("song_name"):
                        song_name = matched_file["song_name"]
                    else:
                        song_name = original_song_name
                        
                    # 如果特征库中有艺术家信息，也更新
                    if matched_file.get("author"):
                        artist_name = matched_file["author"]
                    
                    # 获取封面路径
                    if matched_file.get("cover_path") and os.path.exists(matched_file["cover_path"]):
                        cover_path = matched_file["cover_path"]
                        print(f"从特征库加载封面图片: {cover_path}")
                    
                    print(f"从特征库更新歌曲信息: {song_name} - {artist_name}")
                else:
                    song_name = original_song_name
                    print(f"无法从特征库获取歌曲信息，使用原始结果: {song_name}")
            except Exception as e:
                # 如果出现错误，使用原始识别结果
                song_name = original_song_name
                print(f"获取特征库歌曲信息出错: {str(e)}，使用原始结果: {song_name}")
            
            self.song_label.setText(song_name)
            # 确保显示歌手信息
            self.artist_label.setText(f"歌手: {artist_name}")
            
            # 专辑标签改为显示歌曲名
            self.album_label.setText(f"歌曲名: {song_name}")
            self.album_label.setVisible(True)
            
            # 发行年份可能为空
            if "release_year" in result and result["release_year"]:
                self.year_label.setText(f"发行年份: {result['release_year']}")
                self.year_label.setVisible(True)
            else:
                self.year_label.setText("")
                self.year_label.setVisible(False)
            
            # 流派可能为空
            if "genre" in result and result["genre"] and result["genre"] != "未知":
                self.genre_label.setText(f"流派: {result['genre']}")
                self.genre_label.setVisible(True)
            else:
                self.genre_label.setText("")
                self.genre_label.setVisible(False)
            
            # 显示置信度
            confidence = result.get('confidence', 0) * 100
            
            # 标记是否为本地识别结果并优化显示样式
            if result.get("is_local_recognition", False):
                self.confidence_label.setText(f"置信度: {confidence:.1f}% (本地识别)")
                self.confidence_label.setStyleSheet("""
                    font-size: 16px; 
                    color: #FF6B6B; 
                    margin-top: 15px;
                    font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
                    font-weight: bold;
                    border-radius: 10px;
                    padding: 3px 8px;
                    background-color: rgba(255, 107, 107, 0.1);
                """)
            else:
                self.confidence_label.setText(f"置信度: {confidence:.1f}%")
                self.confidence_label.setStyleSheet("""
                    font-size: 16px; 
                    color: #1DB954; 
                    margin-top: 15px;
                    font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
                    font-weight: bold;
                    border-radius: 10px;
                    padding: 3px 8px;
                    background-color: rgba(29, 185, 84, 0.1);
                """)
            
            # 加载封面图像
            # 优先使用特征库中的封面
            if cover_path:
                self.load_cover_image(cover_path)
            # 如果特征库没有封面，尝试使用API返回的封面URL
            elif "cover_url" in result and result["cover_url"]:
                self.load_cover_image(result["cover_url"])
            else:
                # 使用默认封面
                self.cover_label.setText("🎵")
                self.cover_label.setStyleSheet("""
                    background-color: #EEEEEE; 
                    border-radius: 10px; 
                    font-size: 64px;
                    border: 2px solid #FFFFFF;
                """)
            
            # 保存识别结果信息，用于搜索按钮
            self.current_song = song_name
            self.current_artist = artist_name
            
            # 添加到历史记录
            try:
                # 获取主窗口对象
                main_window = self.window()  # 使用window()获取主窗口
                print(f"主窗口对象: {main_window}")
                if main_window:
                    # 打印主窗口类型
                    print(f"主窗口类型: {type(main_window).__name__}")
                    print(f"主窗口属性: {dir(main_window)}")
                    
                    # 检查是否有profile_tab属性
                    has_profile_tab = hasattr(main_window, 'profile_tab')
                    print(f"是否有profile_tab属性: {has_profile_tab}")
                    
                    if has_profile_tab:
                        profile_tab = main_window.profile_tab
                        print(f"ProfileTab类型: {type(profile_tab).__name__}")
                        
                        # 创建历史记录项
                        history_item = {
                            "song_id": result.get('id', ''),
                            "song_name": song_name,
                            "artist": artist_name,
                            "file_path": result.get('file_path', ''),
                            "confidence": result.get('confidence', 0),
                            "album": result.get('album', '未知专辑'),
                            "cover_path": cover_path or result.get('cover_url', '')
                        }
                        print(f"准备添加历史记录: {history_item}")
                        
                        # 检查是否有add_to_history方法
                        has_add_method = hasattr(profile_tab, 'add_to_history')
                        print(f"是否有add_to_history方法: {has_add_method}")
                        
                        if has_add_method:
                            # 添加到历史记录
                            profile_tab.add_to_history(history_item)
                            print("历史记录添加成功")
                        else:
                            print("ProfileTab没有add_to_history方法")
                    else:
                        print("主窗口没有profile_tab属性")
                else:
                    print("未找到主窗口实例")
            except Exception as e:
                print(f"添加历史记录失败: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # 自动跳转到歌曲库并搜索（如果启用了自动搜索）
            if hasattr(self, 'auto_search_enabled') and self.auto_search_enabled:
                self.search_in_library()
        else:
            # 处理识别失败的情况
            error_message = result.get('error', '未找到匹配的歌曲')
            
            # 显示识别失败的提示
            self.song_label.setText("识别失败")
            self.artist_label.setText(f"原因: {error_message}")
            
            # 隐藏不需要的标签
            self.album_label.setVisible(False)
            self.year_label.setVisible(False)
            self.genre_label.setVisible(False)
            
            # 显示置信度
            confidence = result.get('confidence', 0) * 100
            self.confidence_label.setText(f"置信度: {confidence:.1f}% (识别失败)")
            self.confidence_label.setStyleSheet("""
                font-size: 16px; 
                color: #FF6B6B; 
                margin-top: 15px;
                font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
                font-weight: bold;
                border-radius: 10px;
                padding: 3px 8px;
                background-color: rgba(255, 107, 107, 0.1);
            """)
            
            # 使用默认封面
            self.cover_label.setText("❌")
            self.cover_label.setStyleSheet("""
                background-color: #FFEEEE; 
                border-radius: 10px; 
                font-size: 64px;
                border: 2px solid #FFCCCC;
            """)
            
            # 设置空的搜索关键词
            self.current_song = ""
            self.current_artist = ""
    
    def handle_recognition_error(self, error_message):
        """处理识别错误"""
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.timer.stop()
        
        # 显示错误消息
        QMessageBox.critical(self, "识别错误", error_message)
    
    def load_cover_image(self, url):
        """加载封面图像并设置背景"""
        try:
            if url.startswith("http://") or url.startswith("https://"):
                # 获取网络图像
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        # 将图像数据转换为PIL图像
                        image_data = response.content
                        image = Image.open(io.BytesIO(image_data))
                    else:
                        raise Exception(f"获取封面图像失败: HTTP {response.status_code}")
                except requests.exceptions.RequestException as e:
                    raise Exception(f"请求封面图像失败: {str(e)}")
            else:
                # 处理本地文件路径
                if os.path.exists(url):
                    image = Image.open(url)
                else:
                    raise Exception(f"封面图像文件不存在: {url}")
            
            # 创建一个副本用于封面显示
            cover_image = image.copy()
            
            # 调整封面大小
            cover_image = cover_image.resize((150, 150))
            
            # 转换为QPixmap
            qimage = ImageQt.ImageQt(cover_image)
            pixmap = QPixmap.fromImage(qimage)
            
            # 设置到标签
            self.cover_label.setPixmap(pixmap)
            self.cover_label.setStyleSheet("border-radius: 5px;")
            
            # 设置背景图片
            # 创建一个更大更模糊的版本用于背景
            bg_image = image.copy()
            # 调整尺寸，确保足够大以覆盖整个页面
            bg_image = bg_image.resize((1200, 800))
            # 应用模糊效果增强可读性
            from PIL import ImageFilter
            bg_image = bg_image.filter(ImageFilter.GaussianBlur(radius=10))
            
            # 将PIL图像转换为QPixmap
            bg_qimage = ImageQt.ImageQt(bg_image)
            bg_pixmap = QPixmap.fromImage(bg_qimage)
            
            # 创建调色板并设置背景
            palette = self.result_page.palette()
            palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, 
                            QBrush(bg_pixmap))
            palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, 
                            QBrush(bg_pixmap))
            self.result_page.setPalette(palette)
            
            print(f"成功设置背景图片: {url}")
            
        except Exception as e:
            print(f"加载封面图像失败: {str(e)}")
            # 使用默认封面
            self.cover_label.setText("🎵")
            self.cover_label.setStyleSheet("background-color: #EEEEEE; border-radius: 5px; font-size: 64px;")
            
            # 重置背景为默认
            self.result_page.setStyleSheet("background-color: #FFFFFF;")  # 白色背景
    
    def search_in_library(self):
        """在歌曲库中搜索当前识别的歌曲"""
        if hasattr(self, 'current_song') and self.current_song:
            # 获取主窗口
            main_window = self.window()  # 使用window()获取主窗口
            
            # 如果找到主窗口，获取歌曲库选项卡并执行搜索
            if main_window and hasattr(main_window, 'get_library_tab'):
                library_tab = main_window.get_library_tab()
                if library_tab:
                    # 切换到歌曲库选项卡
                    main_window.switch_to_tab(2)  # 索引2对应歌曲库选项卡
                    # 执行搜索
                    library_tab.search_music(self.current_song, self.current_artist)

    def display_recognition_result(self, result):
        """显示识别结果"""
        # 显示结果面板
        self.result_panel.show()
        self.result_title.setText("识别结果")
        
        if result.get('success', False):
            song_name = result.get('song_name', '未知歌曲')
            artist = result.get('artist', '未知艺术家')
            confidence = result.get('confidence', 0)
            
            # 显示基本信息
            self.song_label.setText(f"歌曲: {song_name}")
            self.artist_label.setText(f"艺术家: {artist}")
            
            # 显示封面
            cover_url = result.get('cover_url', '')
            if cover_url and os.path.exists(cover_url):
                pixmap = QPixmap(cover_url)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.cover_label.setPixmap(pixmap)
                else:
                    self.cover_label.setText("无法加载封面")
            else:
                self.cover_label.setText("无封面")
            
            # 信任度
            confidence_text = f"{confidence:.2%}" if isinstance(confidence, float) else str(confidence)
            self.confidence_label.setText(f"信任度: {confidence_text}")
            
            # 额外信息
            extra_info = []
            if 'album' in result and result['album']:
                extra_info.append(f"专辑: {result['album']}")
            if 'release_year' in result and result['release_year']:
                extra_info.append(f"年份: {result['release_year']}")
            if 'genre' in result and result['genre']:
                extra_info.append(f"流派: {result['genre']}")
            
            if extra_info:
                self.extra_info_label.setText('\n'.join(extra_info))
            else:
                self.extra_info_label.setText("无更多信息")
            
            # 保存结果以备后用
            self.current_result = result
            
            # 添加到历史记录
            try:
                # 获取主窗口对象
                main_window = self.window()  # 使用window()代替parent()
                print(f"主窗口对象: {main_window}")
                if main_window:
                    # 打印主窗口类型
                    print(f"主窗口类型: {type(main_window).__name__}")
                    print(f"主窗口属性: {dir(main_window)}")
                    
                    # 检查是否有profile_tab属性
                    has_profile_tab = hasattr(main_window, 'profile_tab')
                    print(f"是否有profile_tab属性: {has_profile_tab}")
                    
                    if has_profile_tab:
                        profile_tab = main_window.profile_tab
                        print(f"ProfileTab类型: {type(profile_tab).__name__}")
                        
                        # 创建历史记录项
                        history_item = {
                            "song_id": result.get('id', ''),
                            "song_name": song_name,
                            "artist": artist,
                            "file_path": result.get('file_path', ''),
                            "confidence": confidence,
                            "album": result.get('album', '未知专辑'),
                            "cover_path": cover_url
                        }
                        print(f"准备添加历史记录: {history_item}")
                        
                        # 检查是否有add_to_history方法
                        has_add_method = hasattr(profile_tab, 'add_to_history')
                        print(f"是否有add_to_history方法: {has_add_method}")
                        
                        if has_add_method:
                            # 添加到历史记录
                            profile_tab.add_to_history(history_item)
                            print("历史记录添加成功")
                        else:
                            print("ProfileTab没有add_to_history方法")
                    else:
                        print("主窗口没有profile_tab属性")
                else:
                    print("未找到主窗口实例")
            except Exception as e:
                print(f"添加历史记录失败: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # 显示操作按钮
            self.search_button.show()
            
            # 添加收藏按钮
            if not hasattr(self, 'favorite_button'):
                self.favorite_button = QPushButton("添加到收藏")
                self.favorite_button.setStyleSheet("""
                    QPushButton {
                        background-color: #e74c3c;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #c0392b;
                    }
                """)
                self.favorite_button.clicked.connect(self.add_current_to_favorite)
                self.result_buttons_layout.addWidget(self.favorite_button)
            self.favorite_button.show()
        else:
            # 识别失败
            self.song_label.setText("未能识别该音频")
            self.artist_label.setText("")
            self.cover_label.setText("无结果")
            self.confidence_label.setText("")
            self.extra_info_label.setText(result.get('message', '识别失败，请尝试使用更长的音频片段或更清晰的录音。'))
            
            # 隐藏按钮
            self.search_button.hide()
            if hasattr(self, 'favorite_button'):
                self.favorite_button.hide()
            
            # 清除当前结果
            self.current_result = None

    def add_current_to_favorite(self):
        """将当前识别结果添加到收藏"""
        if not self.current_result:
            return
        
        # 获取主窗口对象
        main_window = self.window()  # 使用window()代替parent()
        if not main_window:
            QMessageBox.warning(self, "错误", "无法获取主窗口实例，收藏功能无法使用")
            return
        
        # 检查是否有profile_tab属性
        if not hasattr(main_window, 'profile_tab'):
            QMessageBox.warning(self, "错误", "主窗口没有profile_tab属性，收藏功能无法使用")
            return
            
        # 获取ProfileTab实例
        profile_tab = main_window.profile_tab
        if not profile_tab:
            QMessageBox.warning(self, "错误", "无法获取用户档案选项卡实例，收藏功能无法使用")
            return
        
        try:
            # 准备收藏数据
            song_data = {
                "song_id": self.current_result.get('id', ''),
                "song_name": self.current_result.get('song_name', '未知歌曲'),
                "artist": self.current_result.get('artist', '未知艺术家'),
                "file_path": self.current_result.get('file_path', ''),
                "album": self.current_result.get('album', '未知专辑'),
                "cover_path": self.current_result.get('cover_url', '')
            }
            
            # 添加到收藏
            if profile_tab.add_to_favorites(song_data):
                QMessageBox.information(self, "收藏成功", "已将歌曲添加到收藏列表")
                
                # 更新按钮状态
                self.favorite_button.setText("已收藏")
                self.favorite_button.setEnabled(False)
                self.favorite_button.setStyleSheet("""
                    QPushButton {
                        background-color: #7f8c8d;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                    }
                """)
            else:
                QMessageBox.information(self, "收藏提示", "该歌曲已在收藏列表中")
        except Exception as e:
            QMessageBox.warning(self, "收藏失败", f"添加到收藏时出错: {str(e)}")
            print(f"添加收藏失败: {str(e)}")
            traceback.print_exc() 