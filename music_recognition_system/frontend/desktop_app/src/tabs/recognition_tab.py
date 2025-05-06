from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFileDialog, QProgressBar, QSlider, QStackedWidget)
from PyQt6.QtCore import Qt, QTimer, QUrl, QThread, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QFont, QPalette, QColor

class MusicRecognitionThread(QThread):
    """识别音乐的线程，避免UI卡顿"""
    result_ready = pyqtSignal(dict)
    
    def __init__(self, audio_path):
        super().__init__()
        self.audio_path = audio_path
        
    def run(self):
        # 在实际应用中，这里会调用后端API进行音乐识别
        # 这里仅作为示例返回模拟数据
        import time
        time.sleep(2)  # 模拟识别过程
        
        result = {
            "success": True,
            "song_name": "告白气球",
            "artist": "周杰伦",
            "album": "周杰伦的床边故事",
            "release_year": "2016",
            "cover_url": "",  # 实际应用中会返回封面URL
            "confidence": 0.95
        }
        
        self.result_ready.emit(result)

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

class RecognitionTab(QWidget):
    """音乐识别选项卡"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 顶部标题
        title = QLabel("识别音乐")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px 0;")
        
        # 创建堆叠小部件来存放上传界面和结果界面
        self.stacked_widget = QStackedWidget()
        
        # 上传页面
        upload_page = QWidget()
        upload_page_layout = QVBoxLayout(upload_page)
        
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
        
        # 上传音频按钮 - 彻底解决文字显示问题
        self.upload_button = QPushButton()
        self.upload_button.setText("选择文件")
        self.upload_button.setFixedSize(120, 40)
        
        # 使用字体对象设置字体
        button_font = QFont()
        button_font.setPointSize(11)
        button_font.setBold(True)
        self.upload_button.setFont(button_font)
        
        # 设置调色板强制文字颜色
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#FFFFFF"))
        self.upload_button.setPalette(palette)
        
        # 将文本对齐方式设置为居中
        self.upload_button.setProperty("text-align", "center")
        
        # 设置风格表
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
        
        # 麦克风录制按钮 - 彻底解决文字显示问题
        self.record_button = QPushButton()
        self.record_button.setText("使用麦克风")
        self.record_button.setFixedSize(120, 40)
        self.record_button.setFont(button_font)
        self.record_button.setPalette(palette)
        
        # 将文本对齐方式设置为居中
        self.record_button.setProperty("text-align", "center")
        
        # 设置风格表
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
        upload_page_layout.addWidget(upload_widget)
        
        # 结果页面
        result_page = QWidget()
        result_page_layout = QVBoxLayout(result_page)
        
        # 结果区域
        result_title = QLabel("识别结果")
        result_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        
        self.result_info = QLabel()
        self.result_info.setStyleSheet("font-size: 16px; margin: 5px 0;")
        self.result_info.setWordWrap(True)
        
        self.result_confidence = QLabel()
        self.result_confidence.setStyleSheet("font-size: 14px; color: #666666;")
        
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
        result_page_layout.addWidget(result_title)
        result_page_layout.addWidget(self.result_info)
        result_page_layout.addWidget(self.result_confidence)
        result_page_layout.addWidget(self.player_widget)
        result_page_layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # 将页面添加到堆叠部件
        self.stacked_widget.addWidget(upload_page)
        self.stacked_widget.addWidget(result_page)
        
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
    
    def show_upload_page(self):
        """显示上传页面"""
        self.stacked_widget.setCurrentIndex(0)
    
    def show_result_page(self):
        """显示结果页面"""
        self.stacked_widget.setCurrentIndex(1)
    
    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "", "音频文件 (*.mp3 *.wav *.ogg *.flac *.m4a)"
        )
        
        if file_path:
            self.start_recognition(file_path)
    
    def start_recognition(self, file_path):
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
        self.recognition_thread.start()
        
        # 设置播放器媒体
        self.player_widget.set_media(file_path)
    
    def update_progress(self):
        current_value = self.progress_bar.value()
        if current_value < 100:
            self.progress_bar.setValue(current_value + 1)
        else:
            self.timer.stop()
    
    def handle_recognition_result(self, result):
        self.progress_bar.setValue(100)
        self.timer.stop()
        
        if result["success"]:
            # 显示结果
            self.result_info.setText(
                f"歌曲: {result['song_name']}\n"
                f"歌手: {result['artist']}\n"
                f"专辑: {result['album']}\n"
                f"发行年份: {result['release_year']}"
            )
            
            self.result_confidence.setText(f"置信度: {result['confidence']*100:.1f}%")
            
            # 切换到结果页面
            self.show_result_page()
            
            # 延迟隐藏进度条
            QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False)) 