from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QSlider, QListWidget, QProgressBar, QFrame,
    QSizePolicy, QListWidgetItem, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, QUrl, QTimer, QSize
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPalette, QFont, QPainter, QBrush
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
import os
import sys
import traceback

class MusicPlayerWidget(QWidget):
    """音乐播放器小部件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_tab = parent  # 保存父级Tab的引用
        self.setup_ui()
        self.loop_mode = False  # 循环播放模式标志
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        
        # 播放器控制区域 - 单行布局
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # 上一曲按钮
        self.previous_button = QPushButton()
        self.previous_button.setFixedSize(32, 32)
        self.previous_button.setToolTip("上一曲")
        self.previous_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.previous_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #4285F4;
            }
            QPushButton:pressed {
                color: #3275E4;
            }
        """)
        self.previous_button.setText("◀◀")
        self.previous_button.clicked.connect(self.play_previous)
        
        # 播放/暂停按钮
        self.play_button = QPushButton()
        self.play_button.setFixedSize(32, 32)
        self.play_button.setToolTip("播放/暂停")
        self.play_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #4285F4;
            }
            QPushButton:pressed {
                color: #3275E4;
            }
        """)
        self.play_button.setText("▶")
        
        # 下一曲按钮
        self.next_button = QPushButton()
        self.next_button.setFixedSize(32, 32)
        self.next_button.setToolTip("下一曲")
        self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #4285F4;
            }
            QPushButton:pressed {
                color: #3275E4;
            }
        """)
        self.next_button.setText("▶▶")
        self.next_button.clicked.connect(self.play_next)
        
        # 循环播放按钮
        self.loop_button = QPushButton()
        self.loop_button.setFixedSize(32, 32)
        self.loop_button.setToolTip("循环播放")
        self.loop_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.loop_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #4285F4;
            }
            QPushButton:pressed {
                color: #3275E4;
            }
        """)
        self.loop_button.setText("⟳")
        self.loop_button.clicked.connect(self.toggle_loop)
        
        # 进度条
        self.progress_bar = QSlider(Qt.Orientation.Horizontal)
        self.progress_bar.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #555555;
                margin: 0px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #4285F4;
                border: none;
                width: 12px;
                height: 12px;
                margin: -3px 0;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background: #4285F4;
                border-radius: 3px;
            }
        """)
        
        # 时间标签
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #CCCCCC; font-size: 12px;")
        self.time_label.setFixedWidth(100)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # 添加所有控件到单行布局
        controls_layout.addWidget(self.previous_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addWidget(self.loop_button)
        controls_layout.addWidget(self.progress_bar, 1)  # 进度条占据剩余空间
        controls_layout.addWidget(self.time_label)
        
        layout.addLayout(controls_layout)
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
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        
    def toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_button.setText("▶")
        else:
            self.player.play()
            self.play_button.setText("=")
    
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
    
    def play_previous(self):
        """播放上一曲"""
        # 需要由父类MusicPlayerTab实现获取上一曲功能
        if self.parent_tab and hasattr(self.parent_tab, "play_previous"):
            self.parent_tab.play_previous()
    
    def play_next(self):
        """播放下一曲"""
        # 需要由父类MusicPlayerTab实现获取下一曲功能
        if self.parent_tab and hasattr(self.parent_tab, "play_next"):
            self.parent_tab.play_next()
    
    def toggle_loop(self):
        """切换循环播放模式"""
        self.loop_mode = not self.loop_mode
        if self.loop_mode:
            self.loop_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    color: #1DB954;
                    font-size: 18px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    color: #1ED760;
                }
                QPushButton:pressed {
                    color: #0A8C3C;
                }
            """)
        else:
            self.loop_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    color: #4285F4;
                }
                QPushButton:pressed {
                    color: #3275E4;
                }
            """)
    
    def on_media_status_changed(self, status):
        """媒体状态变化处理"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.loop_mode:
                # 如果是循环模式，重新播放当前歌曲
                self.player.setPosition(0)
                self.player.play()
                self.play_button.setText("=")
            else:
                # 否则播放下一曲
                self.play_next()

class MusicPlayerTab(QWidget):
    """歌曲播放选项卡，用于播放和控制音乐"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_music_path = None
        self.current_playlist_index = -1  # 当前播放歌曲的索引
        self.setObjectName("MusicPlayerTab")
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 使选项卡支持背景图片显示
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # 创建一个灰色背景面板
        self.panel = QFrame()
        self.panel.setObjectName("music_player_panel")
        self.panel.setStyleSheet("""
            #music_player_panel {
                background-color: rgba(50, 50, 50, 0.85);
                border-radius: 15px;
                border: 1px solid rgba(70, 70, 70, 0.9);
            }
        """)
        
        # 面板布局
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(25, 25, 25, 25)
        panel_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("歌曲播放")
        title_label.setObjectName("title_label")
        title_label.setStyleSheet("""
            #title_label {
                font-size: 28px; 
                font-weight: bold; 
                color: #1DB954;
                font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
                letter-spacing: 1px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # 内容布局
        content_layout = QHBoxLayout()
        content_layout.setSpacing(25)
        
        # 创建封面容器框架
        self.cover_frame = QFrame()
        self.cover_frame.setObjectName("cover_frame")
        self.cover_frame.setFixedSize(220, 220)  # 固定大小以保持一致
        self.cover_frame.setStyleSheet("""
            #cover_frame {
                background-color: #252525;
                border-radius: 10px;
                border: 2px solid #333333;
                padding: 0px;
            }
        """)
        
        # 封面框架布局
        cover_frame_layout = QVBoxLayout(self.cover_frame)
        cover_frame_layout.setContentsMargins(0, 0, 0, 0)  # 移除内边距使图片充满整个框架
        cover_frame_layout.setSpacing(0)
        
        # 音乐封面
        self.cover_label = QLabel("🎵")
        self.cover_label.setObjectName("cover_label")
        self.cover_label.setFixedSize(220, 220)  # 与框架大小一致
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet("""
            #cover_label {
                background-color: #252525; 
                font-size: 64px;
                color: #555555;
                padding: 0px;
                border-radius: 10px;
            }
        """)
        
        # 添加封面标签到框架
        cover_frame_layout.addWidget(self.cover_label)
        
        # 播放列表和控制区域
        right_layout = QVBoxLayout()
        
        # 歌曲信息显示
        self.song_info_label = QLabel("未选择歌曲")
        self.song_info_label.setObjectName("song_info_label")
        self.song_info_label.setWordWrap(True)
        self.song_info_label.setStyleSheet("""
            #song_info_label {
                font-size: 22px; 
                font-weight: bold; 
                color: #222222;
                font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
            }
        """)
        
        # 播放列表标签
        playlist_label = QLabel("播放列表")
        playlist_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #333333;
            margin-top: 10px;
        """)
        
        # 播放列表
        self.playlist = QListWidget()
        self.playlist.setMinimumHeight(150)
        self.playlist.setStyleSheet("""
            QListWidget {
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 8px;
                border: 1px solid #CCCCCC;
                padding: 5px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #EEEEEE;
                color: #000000;
            }
            QListWidget::item:selected {
                background-color: #1DB954;
                color: white;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #E0E0E0;
                border-radius: 4px;
            }
        """)
        self.playlist.itemDoubleClicked.connect(self.play_selected_item)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        
        # 添加歌曲按钮
        self.add_button = QPushButton("添加歌曲")
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: white;
                border-radius: 15px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1ED760;
            }
            QPushButton:pressed {
                background-color: #0A8C3C;
            }
        """)
        self.add_button.clicked.connect(self.add_music)
        
        # 移除歌曲按钮
        self.remove_button = QPushButton("移除歌曲")
        self.remove_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border-radius: 15px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F75C4C;
            }
            QPushButton:pressed {
                background-color: #D73C2C;
            }
        """)
        self.remove_button.clicked.connect(self.remove_music)
        
        # 添加按钮到布局
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.remove_button)
        
        # 添加到右侧布局
        right_layout.addWidget(self.song_info_label)
        right_layout.addWidget(playlist_label)
        right_layout.addWidget(self.playlist)
        right_layout.addLayout(buttons_layout)
        
        # 添加到内容布局
        content_layout.addWidget(self.cover_frame)
        content_layout.addLayout(right_layout, 1)
        
        # 创建音乐播放器小部件和背景面板
        self.player_widget_container = QFrame()
        self.player_widget_container.setObjectName("player_widget_container")
        self.player_widget_container.setStyleSheet("""
            #player_widget_container {
                background-color: rgba(25, 25, 25, 0.9);
                border-radius: 10px;
                border: 1px solid rgba(40, 40, 40, 0.9);
                padding: 5px;
            }
        """)
        player_container_layout = QVBoxLayout(self.player_widget_container)
        player_container_layout.setContentsMargins(10, 5, 10, 5)
        
        # 创建音乐播放器小部件
        self.player_widget = MusicPlayerWidget(self)
        
        # 添加播放器小部件到容器
        player_container_layout.addWidget(self.player_widget)
        
        # 添加所有组件到面板布局
        panel_layout.addWidget(title_label)
        panel_layout.addLayout(content_layout)
        panel_layout.addWidget(self.player_widget_container)
        
        # 添加面板到主布局
        main_layout.addWidget(self.panel)
        
        # 加载测试数据
        self.load_test_data()
    
    def load_test_data(self):
        """加载测试数据到播放列表"""
        sample_songs = [
            {"name": "午夜DJ", "path": ""},
            {"name": "示例歌曲1", "path": ""},
            {"name": "示例歌曲2", "path": ""},
            {"name": "示例歌曲3", "path": ""}
        ]
        
        for song in sample_songs:
            item = QListWidgetItem(song["name"])
            item.setData(Qt.ItemDataRole.UserRole, song["path"])
            self.playlist.addItem(item)
    
    def play_selected_item(self, item):
        """播放选中的歌曲"""
        # 获取选中项的行号
        row = self.playlist.row(item)
        self.current_playlist_index = row
        
        song_name = item.text()
        song_path = item.data(Qt.ItemDataRole.UserRole)
        
        self.song_info_label.setText(song_name)
        
        # 如果有实际文件路径，则播放歌曲
        if song_path and os.path.exists(song_path):
            self.current_music_path = song_path
            self.player_widget.set_media(song_path)
            self.player_widget.player.play()
            self.player_widget.play_button.setText("=")
            
            # 尝试从数据库中查找封面并设置背景
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.abspath(os.path.join(current_dir, "../../../../../"))
                database_path = os.path.join(project_root, "music_recognition_system/database/music_features_db")
                
                if os.path.exists(database_path):
                    sys.path.append(project_root)
                    from music_recognition_system.utils.audio_features import FeatureDatabase
                    
                    db = FeatureDatabase(database_path)
                    all_files = db.get_all_files()
                    
                    # 查找匹配的文件和封面
                    for file_info in all_files:
                        if file_info.get("file_path") == song_path:
                            cover_path = file_info.get("cover_path")
                            if cover_path and os.path.exists(cover_path):
                                self.set_cover_image(cover_path)
                                # 设置背景为封面图片
                                self.set_background_image(cover_path)
                                return
            except Exception as e:
                print(f"设置播放项的背景出错: {str(e)}")
            
            # 如果没找到封面或出错，使用默认背景
            self.reset_cover_display()
            self.set_default_background()
        else:
            # 显示提示
            self.song_info_label.setText(f"{song_name} (无可用音频)")
            # 使用默认背景
            self.reset_cover_display()
            self.set_default_background()
    
    def add_music(self):
        """添加音乐到播放列表"""
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("音频文件 (*.mp3 *.wav *.ogg *.flac)")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            for path in file_paths:
                file_name = os.path.basename(path)
                item = QListWidgetItem(file_name)
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.playlist.addItem(item)
    
    def remove_music(self):
        """从播放列表中移除选中的音乐"""
        selected_items = self.playlist.selectedItems()
        for item in selected_items:
            row = self.playlist.row(item)
            self.playlist.takeItem(row)
    
    def play_music(self, music_path):
        """播放音乐功能"""
        if music_path and os.path.exists(music_path):
            self.current_music_path = music_path
            self.player_widget.set_media(music_path)
            self.player_widget.player.play()
            self.player_widget.play_button.setText("=")
            
            # 更新界面信息
            file_name = os.path.basename(music_path)
            self.song_info_label.setText(file_name)
            
            # 将文件添加到播放列表（如果不存在）
            found = False
            for i in range(self.playlist.count()):
                item = self.playlist.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == music_path:
                    found = True
                    self.playlist.setCurrentItem(item)
                    self.current_playlist_index = i
                    break
            
            if not found:
                item = QListWidgetItem(file_name)
                item.setData(Qt.ItemDataRole.UserRole, music_path)
                self.playlist.addItem(item)
                self.playlist.setCurrentItem(item)
                self.current_playlist_index = self.playlist.count() - 1
                
            # 尝试获取封面和音乐信息
            try:
                # 尝试从数据库获取更丰富的信息
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.abspath(os.path.join(current_dir, "../../../../../"))
                database_path = os.path.join(project_root, "music_recognition_system/database/music_features_db")
                
                if os.path.exists(database_path):
                    # 动态导入
                    sys.path.append(project_root)
                    from music_recognition_system.utils.audio_features import FeatureDatabase
                    
                    # 获取数据库
                    db = FeatureDatabase(database_path)
                    all_files = db.get_all_files()
                    
                    # 查找匹配的音乐信息
                    matched_file = None
                    for file_info in all_files:
                        if file_info.get("file_path") == music_path:
                            matched_file = file_info
                            break
                    
                    # 如果找到匹配的文件，更新界面信息
                    if matched_file:
                        # 更新歌曲名称
                        song_name = matched_file.get("song_name", file_name)
                        self.song_info_label.setText(f"{song_name}")
                        
                        # 尝试加载封面
                        cover_path = matched_file.get("cover_path")
                        if cover_path and os.path.exists(cover_path):
                            self.set_cover_image(cover_path)
                            # 设置背景为封面图片
                            self.set_background_image(cover_path)
                        else:
                            # 没有封面，使用默认背景
                            self.reset_cover_display()
                            self.set_default_background()
                    else:
                        # 没有找到匹配的文件信息，使用默认背景
                        self.reset_cover_display()
                        self.set_default_background()
                else:
                    # 数据库路径不存在，使用默认背景
                    self.reset_cover_display()
                    self.set_default_background()
            except Exception as e:
                print(f"加载音乐信息和封面时出错: {str(e)}")
                print(f"堆栈信息: {traceback.format_exc()}")
                # 出错时使用默认背景
                self.reset_cover_display()
                self.set_default_background()
        
    def pause_music(self):
        """暂停音乐功能"""
        if self.player_widget.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player_widget.player.pause()
            self.player_widget.play_button.setText("▶")
        
    def stop_music(self):
        """停止音乐功能"""
        self.player_widget.player.stop()
        self.player_widget.play_button.setText("▶")
        
    def set_volume(self, volume):
        """设置音量功能"""
        if 0 <= volume <= 100:
            self.player_widget.audio_output.setVolume(volume / 100)
    
    def set_cover_image(self, image_path):
        """设置封面图片"""
        if not image_path or not os.path.exists(image_path):
            self.reset_cover_display()
            return False
        
        try:
            # 加载图片
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                self.reset_cover_display()
                return False
            
            # 创建一个正方形的图片(保持宽高比的情况下裁剪成正方形)
            square_pixmap = self.create_square_pixmap(pixmap)
            
            # 调整大小以完全填充封面框
            scaled_pixmap = square_pixmap.scaled(
                self.cover_frame.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # 应用样式并设置图片
            self.cover_label.setStyleSheet("""
                border-radius: 10px;
                background-color: transparent;
                padding: 0px;
            """)
            self.cover_label.setPixmap(scaled_pixmap)
            self.cover_label.setText("")
            
            return True
        except Exception as e:
            print(f"设置封面图片出错: {str(e)}")
            self.reset_cover_display()
            return False
    
    def create_square_pixmap(self, original_pixmap):
        """将图片裁剪成正方形"""
        width = original_pixmap.width()
        height = original_pixmap.height()
        
        # 取最小边作为正方形大小
        size = min(width, height)
        
        # 计算裁剪位置(居中裁剪)
        x = (width - size) // 2
        y = (height - size) // 2
        
        # 裁剪并返回正方形图片
        return original_pixmap.copy(x, y, size, size)
    
    def reset_cover_display(self):
        """重置封面显示为默认状态"""
        self.cover_label.setPixmap(QPixmap())  # 清除图片
        self.cover_label.setText("🎵")
        self.cover_label.setStyleSheet("""
            #cover_label {
                background-color: #252525; 
                font-size: 64px;
                color: #555555;
                border-radius: 10px;
                padding: 0px;
            }
        """)
    
    def set_background_image(self, image_path):
        """设置背景图像为歌曲封面"""
        if not image_path or not os.path.exists(image_path):
            # 如果图片路径不存在，重置为默认背景
            self.set_default_background()
            return False
        
        try:
            # 加载图片
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                self.set_default_background()
                return False
            
            # 创建调色板
            palette = self.palette()
            
            # 调整图片大小以适应窗口并居中
            scaled_pixmap = pixmap.scaled(self.size() * 1.2, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            
            # 创建一个新的带有半透明遮罩的图片
            darkened_pixmap = QPixmap(scaled_pixmap.size())
            darkened_pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(darkened_pixmap)
            painter.drawPixmap(0, 0, scaled_pixmap)
            # 添加一个黑色半透明遮罩，使UI元素更容易看清
            painter.fillRect(darkened_pixmap.rect(), QColor(0, 0, 0, 180))
            painter.end()
            
            # 设置背景
            brush = QBrush(darkened_pixmap)
            palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, brush)
            palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, brush)
            self.setPalette(palette)
            
            # 修改面板样式，使其更加透明
            self.panel.setStyleSheet("""
                #music_player_panel {
                    background-color: rgba(30, 30, 30, 0.7);
                    border-radius: 15px;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }
            """)
            
            return True
        except Exception as e:
            print(f"设置背景图像出错: {str(e)}")
            self.set_default_background()
            return False
     
    def set_default_background(self):
        """重置为默认背景"""
        # 清除背景图片
        palette = self.palette()
        palette.setBrush(QPalette.ColorGroup.All, QPalette.ColorRole.Window, QBrush(QColor(240, 240, 240)))
        self.setPalette(palette)
        
        # 恢复面板默认样式
        self.panel.setStyleSheet("""
            #music_player_panel {
                background-color: rgba(200, 200, 200, 0.75);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.9);
            }
        """)
    
    def play_previous(self):
        """播放上一曲"""
        # 检查播放列表是否为空
        if self.playlist.count() <= 0:
            return
            
        # 计算上一首歌曲的索引
        if self.current_playlist_index <= 0:
            prev_index = self.playlist.count() - 1  # 如果当前是第一首，循环到最后一首
        else:
            prev_index = self.current_playlist_index - 1
            
        # 播放上一首歌曲
        self.current_playlist_index = prev_index
        item = self.playlist.item(prev_index)
        self.playlist.setCurrentItem(item)
        self.play_selected_item(item)
        
    def play_next(self):
        """播放下一曲"""
        # 检查播放列表是否为空
        if self.playlist.count() <= 0:
            return
            
        # 计算下一首歌曲的索引
        if self.current_playlist_index >= self.playlist.count() - 1:
            next_index = 0  # 如果当前是最后一首，循环到第一首
        else:
            next_index = self.current_playlist_index + 1
            
        # 播放下一首歌曲
        self.current_playlist_index = next_index
        item = self.playlist.item(next_index)
        self.playlist.setCurrentItem(item)
        self.play_selected_item(item) 