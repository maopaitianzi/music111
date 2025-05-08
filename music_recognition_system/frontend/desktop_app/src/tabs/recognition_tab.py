from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFileDialog, QProgressBar, QSlider, QStackedWidget,
                            QMessageBox, QFrame)
from PyQt6.QtCore import Qt, QTimer, QUrl, QThread, pyqtSignal, QSize
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QFont, QPalette, QColor, QPixmap, QIcon
import os
import sys
import time
import requests
import io
from PIL import Image, ImageQt

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入服务
try:
    from music_recognition_system.frontend.desktop_app.src.services import MusicRecognitionService, AudioRecorder
except ImportError:
    from services import MusicRecognitionService, AudioRecorder

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

class RecognitionTab(QWidget):
    """音乐识别选项卡"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化服务
        self.recognition_service = MusicRecognitionService()
        # 初始化UI
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 顶部标题
        title = QLabel("识别音乐")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px 0;")
        
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
        
        # 上传区域
        upload_widget = QWidget()
        upload_widget.setStyleSheet("""
            background-color: #F7F7F7;
            border: 2px dashed #999999;
            border-radius: 10px;
            padding: 20px;
        """)
        upload_layout = QVBoxLayout(upload_widget)
        
        upload_icon = QLabel()
        # 实际应用中应该加载一个图标
        upload_icon.setText("🎵")
        upload_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_icon.setStyleSheet("font-size: 72px; color: #444444;")
        
        upload_text = QLabel("拖放音频文件到这里或点击选择文件")
        upload_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_text.setStyleSheet("color: #444444; margin-top: 10px; font-size: 16px; font-weight: bold;")
        
        # 创建水平布局放置两个按钮
        buttons_layout = QHBoxLayout()
        
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
        self.upload_button.clicked.connect(self.open_file_dialog)
        
        # 麦克风录制按钮
        self.record_button = QPushButton()
        self.record_button.setText("使用麦克风")
        self.record_button.setFixedSize(120, 40)
        self.record_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.record_button.setStyleSheet("""
            QPushButton {
                background-color: #FF6B6B;
                color: #FFFFFF;
                border-radius: 20px;
                border: 1px solid #E55555;
                padding: 5px;
                text-align: center;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF8080;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                color: #FFFFFF;
            }
        """)
        self.record_button.clicked.connect(self.show_recording_page)
        
        # 将两个按钮添加到水平布局，并加入间距
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.upload_button)
        buttons_layout.addSpacing(20)  # 在两个按钮之间添加20像素的间距
        buttons_layout.addWidget(self.record_button)
        buttons_layout.addStretch()
        
        upload_layout.addWidget(upload_icon)
        upload_layout.addWidget(upload_text)
        upload_layout.addLayout(buttons_layout)  # 将按钮布局添加到上传区域布局
        
        # 添加上传部件到上传页面
        layout.addWidget(upload_widget)
    
    def setup_result_page(self, page):
        """设置结果页面"""
        layout = QVBoxLayout(page)
        
        # 结果区域
        result_title = QLabel("识别结果")
        result_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        
        # 结果布局
        result_layout = QHBoxLayout()
        
        # 专辑封面
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(150, 150)
        self.cover_label.setStyleSheet("background-color: #EEEEEE; border-radius: 5px;")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 歌曲信息
        info_layout = QVBoxLayout()
        
        self.song_label = QLabel()
        self.song_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.song_label.setWordWrap(True)
        
        self.artist_label = QLabel()
        self.artist_label.setStyleSheet("font-size: 16px;")
        
        self.album_label = QLabel()
        self.album_label.setStyleSheet("font-size: 14px; color: #666666;")
        
        self.year_label = QLabel()
        self.year_label.setStyleSheet("font-size: 14px; color: #666666;")
        
        self.genre_label = QLabel()
        self.genre_label.setStyleSheet("font-size: 14px; color: #666666;")
        
        self.confidence_label = QLabel()
        self.confidence_label.setStyleSheet("font-size: 14px; color: #666666; margin-top: 10px;")
        
        info_layout.addWidget(self.song_label)
        info_layout.addWidget(self.artist_label)
        info_layout.addWidget(self.album_label)
        info_layout.addWidget(self.year_label)
        info_layout.addWidget(self.genre_label)
        info_layout.addWidget(self.confidence_label)
        info_layout.addStretch()
        
        result_layout.addWidget(self.cover_label)
        result_layout.addSpacing(15)
        result_layout.addLayout(info_layout)
        
        # 音乐播放器
        self.player_widget = MusicPlayerWidget()
        
        # 返回按钮 - 返回到上传界面
        self.back_button = QPushButton("返回上传")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                color: #333333;
                border-radius: 18px;
                padding: 8px 15px;
                font-weight: bold;
                max-width: 120px;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
        """)
        self.back_button.clicked.connect(self.show_upload_page)
        
        # 添加组件到结果页面
        layout.addWidget(result_title)
        layout.addLayout(result_layout)
        layout.addWidget(self.player_widget)
        layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)
    
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
        
        if result["success"]:
            # 更新界面信息
            self.song_label.setText(result["song_name"])
            self.artist_label.setText(f"歌手: {result['artist']}")
            self.album_label.setText(f"专辑: {result['album']}")
            self.year_label.setText(f"发行年份: {result['release_year']}")
            
            if "genre" in result:
                self.genre_label.setText(f"流派: {result['genre']}")
            else:
                self.genre_label.setText("")
                
            self.confidence_label.setText(f"置信度: {result['confidence']*100:.1f}%")
            
            # 加载封面图像
            if "cover_url" in result and result["cover_url"]:
                self.load_cover_image(result["cover_url"])
            else:
                # 使用默认封面
                self.cover_label.setText("🎵")
                self.cover_label.setStyleSheet("background-color: #EEEEEE; border-radius: 5px; font-size: 64px;")
            
            # 切换到结果页面
            self.show_result_page()
            
            # 延迟隐藏进度条
            QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))
    
    def handle_recognition_error(self, error_message):
        """处理识别错误"""
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.timer.stop()
        
        # 显示错误消息
        QMessageBox.critical(self, "识别错误", error_message)
    
    def load_cover_image(self, url):
        """加载封面图像"""
        try:
            # 获取图像
            response = requests.get(url)
            if response.status_code == 200:
                # 将图像数据转换为PIL图像
                image_data = response.content
                image = Image.open(io.BytesIO(image_data))
                
                # 调整大小
                image = image.resize((150, 150))
                
                # 转换为QPixmap
                qimage = ImageQt.ImageQt(image)
                pixmap = QPixmap.fromImage(qimage)
                
                # 设置到标签
                self.cover_label.setPixmap(pixmap)
                self.cover_label.setStyleSheet("border-radius: 5px;")
            else:
                # 使用默认封面
                self.cover_label.setText("🎵")
                self.cover_label.setStyleSheet("background-color: #EEEEEE; border-radius: 5px; font-size: 64px;")
                
        except Exception as e:
            print(f"加载封面图像失败: {str(e)}")
            # 使用默认封面
            self.cover_label.setText("🎵")
            self.cover_label.setStyleSheet("background-color: #EEEEEE; border-radius: 5px; font-size: 64px;") 