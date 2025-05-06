from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                            QListWidget, QListWidgetItem, QPushButton, QComboBox, 
                            QScrollArea, QGridLayout, QFrame, QStackedWidget, QTableWidget,
                            QTableWidgetItem, QHeaderView, QSplitter, QMessageBox)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

# 使用相对导入
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.web_service import MusicWebService

class AlbumCard(QFrame):
    """专辑卡片组件"""
    
    def __init__(self, album_data, parent=None):
        super().__init__(parent)
        self.album_data = album_data
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedSize(180, 240)
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setStyleSheet("""
            AlbumCard {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 10px;
            }
            AlbumCard:hover {
                border: 1px solid #1DB954;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # 专辑封面
        album_cover = QLabel()
        album_cover.setFixedSize(160, 160)
        album_cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        album_cover.setStyleSheet("""
            background-color: #F0F0F0;
            border-radius: 5px;
            color: #666666;
        """)
        # 在实际应用中，这里会显示专辑封面图片
        album_cover.setText("🎵")
        album_cover.setFont(QFont("Arial", 36))
        
        # 专辑标题
        album_title = QLabel(self.album_data["title"])
        album_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        album_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        album_title.setWordWrap(True)
        
        # 歌手名称
        artist_name = QLabel(self.album_data["artist"])
        artist_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        artist_name.setStyleSheet("color: #666666; font-size: 12px;")
        
        # 发行年份
        release_year = QLabel(str(self.album_data["year"]))
        release_year.setAlignment(Qt.AlignmentFlag.AlignCenter)
        release_year.setStyleSheet("color: #888888; font-size: 11px;")
        
        # 添加到布局
        layout.addWidget(album_cover)
        layout.addWidget(album_title)
        layout.addWidget(artist_name)
        layout.addWidget(release_year)
        layout.setContentsMargins(10, 10, 10, 10)

class AlbumDetailView(QWidget):
    """专辑详情视图，显示专辑中的歌曲列表"""
    
    def __init__(self, album_data, parent=None):
        super().__init__(parent)
        self.album_data = album_data
        self.setup_media_player()
        self.setup_ui()
        
    def setup_media_player(self):
        """设置媒体播放器"""
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(50)
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 顶部区域：返回按钮和专辑信息
        top_layout = QHBoxLayout()
        
        # 返回按钮
        self.back_button = QPushButton("返回音乐库")
        self.back_button.setStyleSheet("""
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
        """)
        
        # 专辑信息区域
        album_info = QWidget()
        album_info_layout = QHBoxLayout(album_info)
        
        # 专辑封面
        album_cover = QLabel()
        album_cover.setFixedSize(200, 200)
        album_cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        album_cover.setStyleSheet("""
            background-color: #F0F0F0;
            border-radius: 10px;
            color: #666666;
        """)
        album_cover.setText("🎵")
        album_cover.setFont(QFont("Arial", 48))
        
        # 专辑详细信息
        album_details = QWidget()
        album_details_layout = QVBoxLayout(album_details)
        
        album_title = QLabel(self.album_data["title"])
        album_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        artist_name = QLabel(self.album_data["artist"])
        artist_name.setStyleSheet("font-size: 18px; color: #666666;")
        
        album_info_text = QLabel(f"发行年份: {self.album_data['year']} • {len(self.album_data.get('songs', []))} 首歌曲")
        album_info_text.setStyleSheet("font-size: 14px; color: #888888;")
        
        # 播放按钮
        play_button = QPushButton("播放全部")
        play_button.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: white;
                border-radius: 15px;
                padding: 8px 15px;
                font-weight: bold;
                max-width: 120px;
            }
            QPushButton:hover {
                background-color: #1ED760;
            }
        """)
        play_button.clicked.connect(self.play_all_songs)
        
        album_details_layout.addWidget(album_title)
        album_details_layout.addWidget(artist_name)
        album_details_layout.addWidget(album_info_text)
        album_details_layout.addWidget(play_button)
        album_details_layout.addStretch()
        
        album_info_layout.addWidget(album_cover)
        album_info_layout.addWidget(album_details, 1)
        
        top_layout.addWidget(self.back_button)
        top_layout.addStretch()
        
        # 歌曲表格
        self.songs_table = QTableWidget()
        self.songs_table.setColumnCount(5)
        self.songs_table.setHorizontalHeaderLabels(["#", "歌曲名", "时长", "热度", "操作"])
        self.songs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.songs_table.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: white; }")
        self.songs_table.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #F0F0F0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F0F0F0;
            }
            QTableWidget::item:selected {
                background-color: #F0F0F0;
                color: black;
            }
        """)
        self.songs_table.cellClicked.connect(self.handle_song_click)
        
        self.load_songs()
        
        # 添加到主布局
        layout.addLayout(top_layout)
        layout.addWidget(album_info)
        layout.addWidget(self.songs_table)
        
        self.setLayout(layout)
    
    def load_songs(self):
        """加载专辑中的歌曲（示例数据）"""
        if "songs" not in self.album_data:
            # 为不同的专辑添加示例歌曲
            if "周杰伦" in self.album_data["artist"]:
                if "床边故事" in self.album_data["title"]:
                    self.album_data["songs"] = [
                        {"track": 1, "title": "告白气球", "duration": "3:35", "popularity": 9.8},
                        {"track": 2, "title": "前世情人", "duration": "4:15", "popularity": 8.9},
                        {"track": 3, "title": "床边故事", "duration": "3:45", "popularity": 8.7},
                        {"track": 4, "title": "说走就走", "duration": "3:59", "popularity": 8.5},
                        {"track": 5, "title": "一点点", "duration": "3:29", "popularity": 8.6},
                        {"track": 6, "title": "前世情人", "duration": "4:22", "popularity": 8.4},
                        {"track": 7, "title": "土耳其冰淇淋", "duration": "3:48", "popularity": 8.3},
                        {"track": 8, "title": "不该", "duration": "4:05", "popularity": 9.5},
                        {"track": 9, "title": "英雄", "duration": "4:12", "popularity": 8.8},
                        {"track": 10, "title": "Now You See Me", "duration": "3:56", "popularity": 8.2}
                    ]
                elif "七里香" in self.album_data["title"]:
                    self.album_data["songs"] = [
                        {"track": 1, "title": "七里香", "duration": "4:59", "popularity": 9.9},
                        {"track": 2, "title": "借口", "duration": "4:15", "popularity": 9.2},
                        {"track": 3, "title": "外婆", "duration": "3:26", "popularity": 8.8},
                        {"track": 4, "title": "将军", "duration": "3:52", "popularity": 8.7},
                        {"track": 5, "title": "搁浅", "duration": "4:08", "popularity": 9.5},
                        {"track": 6, "title": "乱舞春秋", "duration": "3:28", "popularity": 8.6},
                        {"track": 7, "title": "困兽之斗", "duration": "3:40", "popularity": 8.8},
                        {"track": 8, "title": "园游会", "duration": "4:14", "popularity": 9.7},
                        {"track": 9, "title": "止战之殇", "duration": "3:53", "popularity": 9.3},
                        {"track": 10, "title": "夜曲", "duration": "3:45", "popularity": 9.8}
                    ]
                else:
                    self.album_data["songs"] = [
                        {"track": 1, "title": "以父之名", "duration": "5:41", "popularity": 9.8},
                        {"track": 2, "title": "懦夫", "duration": "3:44", "popularity": 8.8},
                        {"track": 3, "title": "晴天", "duration": "4:29", "popularity": 10.0},
                        {"track": 4, "title": "梯田", "duration": "3:56", "popularity": 8.7},
                        {"track": 5, "title": "双截棍", "duration": "3:22", "popularity": 9.4},
                        {"track": 6, "title": "东风破", "duration": "5:15", "popularity": 9.7},
                        {"track": 7, "title": "你听得到", "duration": "3:04", "popularity": 8.9},
                        {"track": 8, "title": "同一种调调", "duration": "3:10", "popularity": 8.8},
                        {"track": 9, "title": "她的睫毛", "duration": "3:56", "popularity": 8.6},
                        {"track": 10, "title": "爱情悬崖", "duration": "4:00", "popularity": 8.8}
                    ]
            else:
                # 为其他艺术家创建一些示例歌曲
                self.album_data["songs"] = [
                    {"track": 1, "title": "第1首歌", "duration": "3:45", "popularity": 9.2},
                    {"track": 2, "title": "第2首歌", "duration": "4:12", "popularity": 8.9},
                    {"track": 3, "title": "第3首歌", "duration": "3:30", "popularity": 9.5},
                    {"track": 4, "title": "第4首歌", "duration": "4:05", "popularity": 8.7},
                    {"track": 5, "title": "第5首歌", "duration": "3:58", "popularity": 9.0}
                ]
        
        # 清空表格
        self.songs_table.setRowCount(0)
        
        # 添加歌曲到表格
        for song in self.album_data["songs"]:
            row_position = self.songs_table.rowCount()
            self.songs_table.insertRow(row_position)
            
            # 添加曲目编号
            self.songs_table.setItem(row_position, 0, QTableWidgetItem(str(song["track"])))
            
            # 添加歌曲名称
            self.songs_table.setItem(row_position, 1, QTableWidgetItem(song["title"]))
            
            # 添加歌曲时长
            self.songs_table.setItem(row_position, 2, QTableWidgetItem(song["duration"]))
            
            # 添加歌曲热度
            self.songs_table.setItem(row_position, 3, QTableWidgetItem(str(song["popularity"])))
            
            # 添加播放按钮（使用文本替代，实际应用中可以使用图标按钮）
            self.songs_table.setItem(row_position, 4, QTableWidgetItem("播放"))
        
        # 调整列宽
        self.songs_table.setColumnWidth(0, 40)
        self.songs_table.setColumnWidth(2, 80)
        self.songs_table.setColumnWidth(3, 80)
        self.songs_table.setColumnWidth(4, 80)

    def play_all_songs(self):
        """播放专辑中的所有歌曲（从第一首开始）"""
        if "songs" in self.album_data and len(self.album_data["songs"]) > 0:
            # 在实际应用中，这里会加载并播放实际的音频文件
            # 这里仅作为示例，显示正在播放的消息
            song = self.album_data["songs"][0]
            self.play_song(song)
    
    def play_song(self, song):
        """播放单首歌曲"""
        # 在实际应用中，这里会播放实际的音频文件
        # 这里仅模拟播放
        print(f"播放: {song['title']} - {self.album_data['artist']}")
        
        # 模拟设置媒体源
        # 实际情况下，会使用类似以下代码：
        # self.player.setSource(QUrl.fromLocalFile("path/to/audio/file.mp3"))
        # self.player.play()
        
        # 更新表格状态（将当前播放的歌曲高亮）
        for row in range(self.songs_table.rowCount()):
            track_item = self.songs_table.item(row, 0)
            if track_item and int(track_item.text()) == song["track"]:
                # 高亮当前播放的行
                for col in range(self.songs_table.columnCount()):
                    cell = self.songs_table.item(row, col)
                    if cell:
                        cell.setBackground(QColor("#E8F5E9"))  # 淡绿色背景
                        
                # 更新操作按钮为"暂停"
                self.songs_table.item(row, 4).setText("暂停")
            else:
                # 恢复其他行的正常状态
                for col in range(self.songs_table.columnCount()):
                    cell = self.songs_table.item(row, col)
                    if cell:
                        cell.setBackground(QColor("#FFFFFF"))  # 白色背景
                        
                # 恢复操作按钮为"播放"
                self.songs_table.item(row, 4).setText("播放")
    
    def handle_song_click(self, row, column):
        """处理歌曲表格的点击事件"""
        # 只有当点击操作列（第5列）时才响应
        if column == 4:
            # 获取当前点击的歌曲信息
            track_number = int(self.songs_table.item(row, 0).text())
            song = next((s for s in self.album_data["songs"] if s["track"] == track_number), None)
            
            if song:
                # 如果当前歌曲正在播放，则暂停；否则播放
                if self.songs_table.item(row, column).text() == "暂停":
                    self.player.pause()
                    self.songs_table.item(row, column).setText("播放")
                    
                    # 恢复背景色
                    for col in range(self.songs_table.columnCount()):
                        cell = self.songs_table.item(row, col)
                        if cell:
                            cell.setBackground(QColor("#FFFFFF"))
                else:
                    self.play_song(song)

class LibraryTab(QWidget):
    """音乐库选项卡"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_web_service()
        self.setup_ui()
        
    def setup_web_service(self):
        """设置网络服务"""
        self.web_service = MusicWebService(self)
        self.web_service.songs_loaded.connect(self.update_albums)
        self.web_service.album_loaded.connect(self.show_album_detail_from_web)
        self.web_service.error_occurred.connect(self.show_error)
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        # 创建堆叠部件用于切换不同视图
        self.stacked_widget = QStackedWidget()
        
        # 主页面（专辑网格）
        self.main_page = QWidget()
        main_page_layout = QVBoxLayout(self.main_page)
        
        # 创建分类选项卡
        category_layout = QHBoxLayout()
        
        # 创建分类标签
        categories = ["全部", "专辑", "艺术家", "流派"]
        self.category_buttons = []
        
        for category in categories:
            button = QPushButton(category)
            button.setCheckable(True)
            button.setFixedHeight(36)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet("""
                QPushButton {
                    border: none;
                    background-color: transparent;
                    color: #666666;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 5px 10px;
                    margin-right: 20px;
                }
                QPushButton:checked {
                    color: #1DB954;
                    border-bottom: 2px solid #1DB954;
                }
                QPushButton:hover:!checked {
                    color: #333333;
                    border-bottom: 2px solid #E0E0E0;
                }
            """)
            if category == "全部":
                button.setChecked(True)
            
            # 连接分类按钮的点击事件
            button.clicked.connect(lambda checked, c=category: self.filter_by_category(c))
            
            self.category_buttons.append(button)
            category_layout.addWidget(button)
        
        category_layout.addStretch()
        
        # 顶部标题
        title = QLabel("音乐库")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px 0;")
        
        # 搜索和过滤区域
        filter_layout = QHBoxLayout()
        
        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索歌曲、专辑或艺术家...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CCCCCC;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #1DB954;
            }
        """)
        # 连接搜索框的文本变化信号
        self.search_box.textChanged.connect(self.filter_albums)
        
        # 过滤下拉菜单
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "专辑", "艺术家", "流派"])
        self.filter_combo.setFixedWidth(120)
        self.filter_combo.setFixedHeight(40)
        self.filter_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: white;
                font-size: 14px;
                color: #333333;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #CCCCCC;
            }
            QComboBox:hover {
                border: 1px solid #1DB954;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                selection-background-color: #F0F0F0;
                color: #333333;
            }
        """)
        # 连接过滤选择变化信号
        self.filter_combo.currentIndexChanged.connect(self.filter_albums)
        
        # 排序下拉菜单
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["按名称排序", "按发行日期排序", "按热度排序"])
        self.sort_combo.setFixedWidth(140)
        self.sort_combo.setFixedHeight(40)
        self.sort_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: white;
                font-size: 14px;
                color: #333333;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #CCCCCC;
            }
            QComboBox:hover {
                border: 1px solid #1DB954;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                selection-background-color: #F0F0F0;
                color: #333333;
            }
        """)
        # 连接排序选择变化信号
        self.sort_combo.currentIndexChanged.connect(self.filter_albums)
        
        filter_layout.addWidget(self.search_box)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addWidget(self.sort_combo)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #F0F0F0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #BBBBBB;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # 创建网格布局用于显示专辑
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(20)
        scroll_area.setWidget(self.grid_widget)
        
        # 添加到主页面布局
        main_page_layout.addWidget(title)
        main_page_layout.addLayout(category_layout)
        main_page_layout.addLayout(filter_layout)
        main_page_layout.addWidget(scroll_area)
        
        # 创建详情页（将在选择专辑时创建）
        self.detail_page = QWidget()
        
        # 添加页面到堆叠部件
        self.stacked_widget.addWidget(self.main_page)
        self.stacked_widget.addWidget(self.detail_page)
        
        # 添加堆叠部件到主布局
        main_layout.addWidget(self.stacked_widget)
        
        self.setLayout(main_layout)
        
        # 加载专辑
        self.load_albums_from_web()
    
    def load_albums_from_web(self):
        """从web服务加载专辑数据"""
        try:
            # 显示加载中提示
            self.clear_grid()
            loading_label = QLabel("正在加载音乐数据...")
            loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_label.setStyleSheet("color: #666666; font-size: 16px; margin: 20px;")
            self.grid_layout.addWidget(loading_label, 0, 0, 1, 4)
            
            # 从web服务获取专辑列表
            self.web_service.get_featured_albums()
        except Exception as e:
            self.show_error(f"加载专辑数据失败: {str(e)}")
            # 使用本地模拟数据作为后备方案
            self.load_local_albums()
    
    def load_local_albums(self):
        """加载本地模拟专辑数据（作为后备方案）"""
        self.sample_albums = [
            {"title": "周杰伦的床边故事", "artist": "周杰伦", "year": 2016, "cover_url": "", "genre": "流行"},
            {"title": "七里香", "artist": "周杰伦", "year": 2004, "cover_url": "", "genre": "流行"},
            {"title": "叶惠美", "artist": "周杰伦", "year": 2003, "cover_url": "", "genre": "流行"},
            {"title": "Red", "artist": "Taylor Swift", "year": 2012, "cover_url": "", "genre": "乡村/流行"},
            {"title": "1989", "artist": "Taylor Swift", "year": 2014, "cover_url": "", "genre": "流行"},
            {"title": "÷ (Divide)", "artist": "Ed Sheeran", "year": 2017, "cover_url": "", "genre": "流行/民谣"},
            {"title": "25", "artist": "Adele", "year": 2015, "cover_url": "", "genre": "流行/灵魂乐"},
            {"title": "Discovery", "artist": "Daft Punk", "year": 2001, "cover_url": "", "genre": "电子"},
            {"title": "Random Access Memories", "artist": "Daft Punk", "year": 2013, "cover_url": "", "genre": "电子"},
            {"title": "After Hours", "artist": "The Weeknd", "year": 2020, "cover_url": "", "genre": "R&B/流行"},
            {"title": "Born to Die", "artist": "Lana Del Rey", "year": 2012, "cover_url": "", "genre": "另类/流行"},
            {"title": "Future Nostalgia", "artist": "Dua Lipa", "year": 2020, "cover_url": "", "genre": "流行/舞曲"}
        ]
        
        # 显示所有专辑
        self.update_albums(self.sample_albums)
    
    def update_albums(self, albums):
        """更新专辑列表显示"""
        self.sample_albums = albums
        self.filter_albums()
    
    def clear_grid(self):
        """清空网格布局"""
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
    
    def filter_by_category(self, category):
        """根据分类过滤专辑"""
        # 更新按钮状态
        for button in self.category_buttons:
            button.setChecked(button.text() == category)
        
        # 设置过滤下拉框的值
        index = self.filter_combo.findText(category)
        if index >= 0:
            self.filter_combo.setCurrentIndex(index)
        
        # 过滤专辑
        self.filter_albums()
    
    def filter_albums(self):
        """根据搜索关键词和过滤条件筛选专辑"""
        search_text = self.search_box.text().lower()
        filter_option = self.filter_combo.currentText()
        sort_option = self.sort_combo.currentText()
        
        # 首先根据筛选条件过滤
        filtered_albums = []
        for album in self.sample_albums:
            # 如果没有搜索词或搜索词匹配专辑标题/艺术家名称
            if (search_text == "" or 
                search_text in album["title"].lower() or 
                search_text in album["artist"].lower()):
                
                # 应用过滤器类型
                if filter_option == "全部":
                    filtered_albums.append(album)
                elif filter_option == "专辑" and "title" in album:
                    filtered_albums.append(album)
                elif filter_option == "艺术家" and "artist" in album:
                    filtered_albums.append(album)
                elif filter_option == "流派" and "genre" in album:
                    filtered_albums.append(album)
        
        # 根据排序选项排序
        if sort_option == "按名称排序":
            filtered_albums.sort(key=lambda x: x["title"])
        elif sort_option == "按发行日期排序":
            filtered_albums.sort(key=lambda x: x["year"], reverse=True)
        elif sort_option == "按热度排序":
            # 这里假设所有的专辑都有热度值，为了简单起见，我们使用发行年份作为替代
            filtered_albums.sort(key=lambda x: x["year"], reverse=True)
        
        # 清空网格
        self.clear_grid()
        
        # 添加过滤后的专辑卡片到网格
        row, col = 0, 0
        max_cols = 4  # 每行最多4张专辑卡片
        
        for album in filtered_albums:
            album_card = AlbumCard(album)
            album_card.mousePressEvent = lambda event, a=album: self.album_clicked(a)
            self.grid_layout.addWidget(album_card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # 如果没有找到任何专辑，显示一个消息
        if not filtered_albums:
            no_results_label = QLabel("没有找到符合条件的专辑")
            no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_results_label.setStyleSheet("color: #888888; font-size: 16px; margin: 20px;")
            self.grid_layout.addWidget(no_results_label, 0, 0, 1, max_cols)
    
    def album_clicked(self, album):
        """处理专辑点击事件"""
        # 尝试从网络加载专辑详情
        try:
            # 显示加载中提示
            loading_view = QWidget()
            loading_layout = QVBoxLayout(loading_view)
            loading_label = QLabel("正在加载专辑详情...")
            loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_label.setStyleSheet("color: #666666; font-size: 18px; margin: 100px;")
            loading_layout.addWidget(loading_label)
            
            # 显示加载视图
            self.stacked_widget.removeWidget(self.detail_page)
            self.detail_page = loading_view
            self.stacked_widget.addWidget(self.detail_page)
            self.stacked_widget.setCurrentWidget(self.detail_page)
            
            # 从web服务获取专辑详情
            self.web_service.get_album_details(album["title"])
        except Exception as e:
            self.show_error(f"加载专辑详情失败: {str(e)}")
            # 使用本地显示作为后备方案
            self.show_album_detail(album)
    
    def show_album_detail_from_web(self, album_data):
        """显示从web获取的专辑详情"""
        # 创建新的详情页
        detail_view = AlbumDetailView(album_data)
        detail_view.back_button.clicked.connect(self.show_main_page)
        
        # 移除旧的详情页
        self.stacked_widget.removeWidget(self.detail_page)
        
        # 添加新的详情页
        self.detail_page = detail_view
        self.stacked_widget.addWidget(self.detail_page)
        
        # 显示详情页
        self.stacked_widget.setCurrentWidget(self.detail_page)
    
    def show_error(self, error_message):
        """显示错误消息"""
        QMessageBox.critical(self, "错误", error_message)
    
    def show_main_page(self):
        """返回主页面"""
        self.stacked_widget.setCurrentWidget(self.main_page) 