from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QGridLayout, QSpacerItem, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QFileDialog, QLineEdit, QComboBox, QCheckBox, QSlider, QInputDialog,
    QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor, QAction

import os
import json
import time

class ProfileTab(QWidget):
    """用户的'我的'选项卡"""
    
    # 信号定义
    play_song_signal = pyqtSignal(str, str)  # 播放歌曲信号(歌曲路径, 歌曲名)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.user_data = self.load_user_data()
        self.setup_ui()
        
        # 设置深灰色背景
        self.setStyleSheet("""
            QWidget {
                background-color: #333333;
                color: #FFFFFF;
            }
        """)
        
    def setup_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 顶部用户信息区域
        self.create_user_info_section(main_layout)
        
        # 内容选项卡
        self.content_tabs = QTabWidget()
        self.content_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
                background-color: #333333;
            }
            QTabBar::tab {
                background-color: #444444;
                color: #000000;  /* 修改为黑色文字 */
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #555555;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #555555;
                color: #FFFFFF;
                font-weight: bold;
                border-bottom: 2px solid #1DB954;
            }
        """)
        
        # 创建各个子选项卡
        self.favorite_tab = self.create_favorite_tab()
        self.history_tab = self.create_history_tab()
        self.settings_tab = self.create_settings_tab()
        
        # 添加子选项卡到内容选项卡
        self.content_tabs.addTab(self.favorite_tab, "我的收藏")
        self.content_tabs.addTab(self.history_tab, "历史记录")
        self.content_tabs.addTab(self.settings_tab, "设置")
        
        main_layout.addWidget(self.content_tabs)
        
        # 加载用户数据
        self.load_favorites()
        self.load_history()
        
    def create_user_info_section(self, parent_layout):
        """创建顶部用户信息区域"""
        user_frame = QFrame()
        user_frame.setStyleSheet("""
            QFrame {
                background-color: #444444;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        user_layout = QHBoxLayout(user_frame)
        
        # 用户头像
        avatar_label = QLabel()
        avatar_pixmap = QPixmap(os.path.join("assets", "icons", "user_avatar.png"))
        if avatar_pixmap.isNull():
            # 如果找不到图像文件，则创建一个彩色方块作为替代
            avatar_pixmap = QPixmap(80, 80)
            avatar_pixmap.fill(QColor("#1DB954"))
        avatar_pixmap = avatar_pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        avatar_label.setPixmap(avatar_pixmap)
        avatar_label.setFixedSize(80, 80)
        
        # 用户信息
        info_layout = QVBoxLayout()
        
        username_label = QLabel(self.user_data.get("username", "音乐爱好者"))
        username_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        username_label.setStyleSheet("color: #FFFFFF;")
        
        stats_layout = QHBoxLayout()
        
        favorites_count = len(self.user_data.get("favorites", []))
        history_count = len(self.user_data.get("history", []))
        
        # 保存标签引用以便后续更新
        self.favorites_count_label = QLabel(f"收藏: {favorites_count}")
        self.favorites_count_label.setStyleSheet("color: #CCCCCC;")
        
        self.history_count_label = QLabel(f"历史: {history_count}")
        self.history_count_label.setStyleSheet("color: #CCCCCC;")
        
        stats_layout.addWidget(self.favorites_count_label)
        stats_layout.addWidget(QLabel("|"))
        stats_layout.addWidget(self.history_count_label)
        stats_layout.addStretch(1)
        
        info_layout.addWidget(username_label)
        info_layout.addLayout(stats_layout)
        info_layout.addStretch(1)
        
        # 编辑资料按钮
        edit_button = QPushButton("编辑资料")
        edit_button.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #18a549;
            }
        """)
        edit_button.clicked.connect(self.edit_profile)
        
        # 组合所有元素
        user_layout.addWidget(avatar_label)
        user_layout.addLayout(info_layout)
        user_layout.addStretch(1)
        user_layout.addWidget(edit_button)
        
        parent_layout.addWidget(user_frame)
        
    def create_favorite_tab(self):
        """创建收藏选项卡"""
        favorite_widget = QWidget()
        favorite_layout = QVBoxLayout(favorite_widget)
        
        # 创建收藏表格
        self.favorites_table = QTableWidget()
        self.favorites_table.setColumnCount(5)  # 减少一列，移除操作列
        self.favorites_table.setHorizontalHeaderLabels(["封面", "歌曲名", "歌手", "专辑", "收藏时间"])
        self.favorites_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.favorites_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.favorites_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # 封面列固定大小
        self.favorites_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 歌曲名可伸缩
        self.favorites_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.favorites_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.favorites_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.favorites_table.verticalHeader().setVisible(False)
        # 设置图标大小和行高
        self.favorites_table.setIconSize(QSize(50, 50))
        self.favorites_table.verticalHeader().setDefaultSectionSize(60)  # 设置行高适应封面图片
        self.favorites_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #555555;
                gridline-color: #555555;
                background-color: #333333;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #444444;
                padding: 5px;
                font-weight: bold;
                color: #FFFFFF;
                border: none;
                border-right: 1px solid #555555;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #1DB954;
                color: #FFFFFF;
            }
        """)
        
        # 添加双击播放和右键菜单功能
        self.favorites_table.doubleClicked.connect(self.play_selected_favorite)
        self.favorites_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.favorites_table.customContextMenuRequested.connect(self.show_favorite_context_menu)
        
        favorite_layout.addWidget(self.favorites_table)
        
        return favorite_widget
        
    def create_history_tab(self):
        """创建历史记录选项卡"""
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        
        # 创建历史记录表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)  # 减少一列，移除操作列
        self.history_table.setHorizontalHeaderLabels(["封面", "歌曲名", "歌手", "识别时间", "准确度"])
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # 封面列固定大小
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 歌曲名可伸缩
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.verticalHeader().setVisible(False)
        # 设置图标大小和行高
        self.history_table.setIconSize(QSize(50, 50))
        self.history_table.verticalHeader().setDefaultSectionSize(60)  # 设置行高适应封面图片
        self.history_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #555555;
                gridline-color: #555555;
                background-color: #333333;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #444444;
                padding: 5px;
                font-weight: bold;
                color: #FFFFFF;
                border: none;
                border-right: 1px solid #555555;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #1DB954;
                color: #FFFFFF;
            }
        """)
        
        # 添加双击播放和右键菜单功能
        self.history_table.doubleClicked.connect(self.play_selected_history)
        self.history_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self.show_history_context_menu)
        
        # 清除历史记录按钮
        clear_button = QPushButton("清除历史记录")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                max-width: 150px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        clear_button.clicked.connect(self.clear_history)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(clear_button)
        
        history_layout.addWidget(self.history_table)
        history_layout.addLayout(button_layout)
        
        return history_widget
        
    def create_settings_tab(self):
        """创建设置选项卡"""
        settings_widget = QWidget()
        
        # 使用滚动区域来确保在窗口缩小时可以滚动查看所有内容
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # 创建内容区域容器
        content_widget = QWidget()
        settings_layout = QVBoxLayout(content_widget)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        settings_layout.setSpacing(15)
        
        # 常规设置组
        general_frame = QFrame()
        general_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #555555;
                border-radius: 5px;
                background-color: #444444;
                padding: 10px;
            }
            QLabel {
                color: #FFFFFF;
                min-width: 80px;
            }
            QComboBox {
                background-color: #333333;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                min-width: 120px;
            }
            QComboBox:hover {
                border: 1px solid #1DB954;
            }
            QComboBox QAbstractItemView {
                background-color: #333333;
                color: #FFFFFF;
                selection-background-color: #1DB954;
            }
        """)
        general_layout = QVBoxLayout(general_frame)
        general_layout.setSpacing(12)
        
        title = QLabel("常规设置")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        general_layout.addWidget(title)
        
        # 创建一个网格布局来更好地对齐标签和下拉框
        options_grid = QGridLayout()
        options_grid.setColumnStretch(0, 0)  # 第一列（标签）不拉伸
        options_grid.setColumnStretch(1, 1)  # 第二列（下拉框）可以拉伸
        options_grid.setHorizontalSpacing(15)
        options_grid.setVerticalSpacing(10)
        
        # 主题设置
        theme_label = QLabel("主题:")
        theme_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色模式", "深色模式", "跟随系统"])
        self.theme_combo.setCurrentText(self.user_data.get("settings", {}).get("theme", "浅色模式"))
        self.theme_combo.currentTextChanged.connect(self.save_settings)
        self.theme_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 语言设置
        language_label = QLabel("语言:")
        language_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English", "日本語"])
        self.language_combo.setCurrentText(self.user_data.get("settings", {}).get("language", "简体中文"))
        self.language_combo.currentTextChanged.connect(self.save_settings)
        self.language_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 启动设置
        startup_label = QLabel("启动时:")
        startup_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.startup_combo = QComboBox()
        self.startup_combo.addItems(["默认显示识别页面", "记住上次退出页面"])
        self.startup_combo.setCurrentText(self.user_data.get("settings", {}).get("startup", "默认显示识别页面"))
        self.startup_combo.currentTextChanged.connect(self.save_settings)
        self.startup_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 将选项添加到网格布局
        options_grid.addWidget(theme_label, 0, 0)
        options_grid.addWidget(self.theme_combo, 0, 1)
        options_grid.addWidget(language_label, 1, 0)
        options_grid.addWidget(self.language_combo, 1, 1)
        options_grid.addWidget(startup_label, 2, 0)
        options_grid.addWidget(self.startup_combo, 2, 1)
        
        general_layout.addLayout(options_grid)
        
        # 音频设置组
        audio_frame = QFrame()
        audio_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #555555;
                border-radius: 5px;
                background-color: #444444;
                padding: 10px;
                margin-top: 15px;
            }
            QLabel {
                color: #FFFFFF;
                min-width: 100px;
            }
            QComboBox {
                background-color: #333333;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                min-width: 120px;
            }
            QComboBox:hover {
                border: 1px solid #1DB954;
            }
            QComboBox QAbstractItemView {
                background-color: #333333;
                color: #FFFFFF;
                selection-background-color: #1DB954;
            }
        """)
        audio_layout = QVBoxLayout(audio_frame)
        audio_layout.setSpacing(12)
        
        audio_title = QLabel("音频设置")
        audio_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        audio_layout.addWidget(audio_title)
        
        # 创建一个网格布局来更好地对齐标签和下拉框
        audio_grid = QGridLayout()
        audio_grid.setColumnStretch(0, 0)  # 第一列（标签）不拉伸
        audio_grid.setColumnStretch(1, 1)  # 第二列（下拉框）可以拉伸
        audio_grid.setHorizontalSpacing(15)
        audio_grid.setVerticalSpacing(10)
        
        # 音质设置
        quality_label = QLabel("音质:")
        quality_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["标准质量", "高质量", "超高质量"])
        self.quality_combo.setCurrentText(self.user_data.get("settings", {}).get("audio_quality", "标准质量"))
        self.quality_combo.currentTextChanged.connect(self.save_settings)
        self.quality_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 识别时长设置
        duration_label = QLabel("默认识别时长:")
        duration_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(["5秒", "10秒", "15秒", "20秒", "30秒"])
        self.duration_combo.setCurrentText(self.user_data.get("settings", {}).get("recognition_duration", "10秒"))
        self.duration_combo.currentTextChanged.connect(self.save_settings)
        self.duration_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 录音设备设置
        device_label = QLabel("默认录音设备:")
        device_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.device_combo = QComboBox()
        self.device_combo.addItems(["默认系统设备", "麦克风 (Realtek HD Audio)", "其他设备..."])
        self.device_combo.setCurrentText(self.user_data.get("settings", {}).get("recording_device", "默认系统设备"))
        self.device_combo.currentTextChanged.connect(self.save_settings)
        self.device_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 将选项添加到网格布局
        audio_grid.addWidget(quality_label, 0, 0)
        audio_grid.addWidget(self.quality_combo, 0, 1)
        audio_grid.addWidget(duration_label, 1, 0)
        audio_grid.addWidget(self.duration_combo, 1, 1)
        audio_grid.addWidget(device_label, 2, 0)
        audio_grid.addWidget(self.device_combo, 2, 1)
        
        audio_layout.addLayout(audio_grid)
        
        # 添加到主布局
        settings_layout.addWidget(general_frame)
        settings_layout.addWidget(audio_frame)
        settings_layout.addStretch(1)
        
        # 恢复默认设置按钮
        reset_button = QPushButton("恢复默认设置")
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                max-width: 150px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        reset_button.clicked.connect(self.reset_settings)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(reset_button)
        
        settings_layout.addLayout(button_layout)
        
        # 设置滚动区域的内容
        scroll_area.setWidget(content_widget)
        
        # 设置主布局
        main_layout = QVBoxLayout(settings_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
        return settings_widget
        
    def load_user_data(self):
        """加载用户数据"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        user_data_dir = os.path.join(current_dir, "..", "..", "data")
        user_data_file = os.path.join(user_data_dir, "user_data.json")
        
        # 确保数据目录存在
        os.makedirs(user_data_dir, exist_ok=True)
        
        # 如果用户数据文件不存在，创建默认数据
        if not os.path.exists(user_data_file):
            default_data = {
                "username": "音乐爱好者",
                "favorites": [],
                "history": [],
                "settings": {
                    "theme": "浅色模式",
                    "language": "简体中文",
                    "startup": "默认显示识别页面",
                    "audio_quality": "标准质量",
                    "recognition_duration": "10秒",
                    "recording_device": "默认系统设备"
                }
            }
            
            with open(user_data_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
                
            return default_data
        
        # 读取用户数据
        try:
            with open(user_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取用户数据错误: {str(e)}")
            return {
                "username": "音乐爱好者",
                "favorites": [],
                "history": [],
                "settings": {}
            }
    
    def save_user_data(self):
        """保存用户数据"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        user_data_dir = os.path.join(current_dir, "..", "..", "data")
        user_data_file = os.path.join(user_data_dir, "user_data.json")
        
        # 确保数据目录存在
        os.makedirs(user_data_dir, exist_ok=True)
        
        try:
            with open(user_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存用户数据错误: {str(e)}")
    
    def add_to_favorites(self, song_data):
        """添加歌曲到收藏列表"""
        # 检查歌曲是否已在收藏中
        for favorite in self.user_data.get("favorites", []):
            if favorite.get("song_id") == song_data.get("song_id") or \
               (favorite.get("song_name") == song_data.get("song_name") and 
                favorite.get("artist") == song_data.get("artist")):
                # 歌曲已存在于收藏夹
                return False
        
        # 添加收藏时间
        song_data["favorite_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 添加到收藏列表
        if "favorites" not in self.user_data:
            self.user_data["favorites"] = []
        
        self.user_data["favorites"].append(song_data)
        self.save_user_data()
        
        # 刷新显示
        self.load_favorites()
        
        # 更新统计信息
        self.update_stats_display()
        
        return True
    
    def remove_from_favorites(self, song_id):
        """从收藏夹中移除歌曲"""
        if "favorites" not in self.user_data:
            return
        
        self.user_data["favorites"] = [
            item for item in self.user_data["favorites"] 
            if item.get("song_id") != song_id
        ]
        
        self.save_user_data()
        
        # 刷新显示
        self.load_favorites()
    
    def add_to_history(self, history_item):
        """添加记录到历史记录"""
        # 添加识别时间
        history_item["recognition_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 添加到历史记录
        if "history" not in self.user_data:
            self.user_data["history"] = []
        
        # 将新记录添加到开头
        self.user_data["history"].insert(0, history_item)
        
        # 限制历史记录数量为最新的50条
        if len(self.user_data["history"]) > 50:
            self.user_data["history"] = self.user_data["history"][:50]
        
        self.save_user_data()
        
        # 刷新显示
        self.load_history()
        
        # 更新统计信息
        self.update_stats_display()
    
    def clear_history(self):
        """清除历史记录"""
        self.user_data["history"] = []
        self.save_user_data()
        
        # 刷新显示
        self.load_history()
        
        # 更新统计信息
        self.update_stats_display()
    
    def load_favorites(self):
        """加载收藏列表到表格"""
        self.favorites_table.setRowCount(0)
        
        favorites = self.user_data.get("favorites", [])
        self.favorites_table.setRowCount(len(favorites))
        
        for row, item in enumerate(favorites):
            # 封面
            cover_item = QTableWidgetItem()
            cover_path = item.get("cover_path", "")
            if cover_path and os.path.exists(cover_path):
                # 加载封面图片
                pixmap = QPixmap(cover_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    cover_item.setIcon(QIcon(pixmap))
            else:
                # 使用默认音乐图标
                default_icon = QIcon(os.path.join("assets", "icons", "play.png"))
                cover_item.setIcon(default_icon)
            
            self.favorites_table.setItem(row, 0, cover_item)
            
            # 歌曲名
            song_name = QTableWidgetItem(item.get("song_name", "未知歌曲"))
            self.favorites_table.setItem(row, 1, song_name)
            
            # 歌手
            artist = QTableWidgetItem(item.get("artist", "未知歌手"))
            self.favorites_table.setItem(row, 2, artist)
            
            # 专辑
            album = QTableWidgetItem(item.get("album", "未知专辑"))
            self.favorites_table.setItem(row, 3, album)
            
            # 收藏时间
            favorite_time = QTableWidgetItem(item.get("favorite_time", ""))
            self.favorites_table.setItem(row, 4, favorite_time)
            
            # 存储歌曲数据，用于后续操作
            for col in range(5):
                self.favorites_table.item(row, col).setData(Qt.ItemDataRole.UserRole, item)
            
            # 设置封面列宽
            self.favorites_table.setColumnWidth(0, 60)
    
    def load_history(self):
        """加载历史记录到表格"""
        self.history_table.setRowCount(0)
        
        history = self.user_data.get("history", [])
        self.history_table.setRowCount(len(history))
        
        for row, item in enumerate(history):
            # 封面
            cover_item = QTableWidgetItem()
            cover_path = item.get("cover_path", "")
            if cover_path and os.path.exists(cover_path):
                # 加载封面图片
                pixmap = QPixmap(cover_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    cover_item.setIcon(QIcon(pixmap))
            else:
                # 使用默认音乐图标
                default_icon = QIcon(os.path.join("assets", "icons", "play.png"))
                cover_item.setIcon(default_icon)
            
            self.history_table.setItem(row, 0, cover_item)
            
            # 歌曲名
            song_name = QTableWidgetItem(item.get("song_name", "未知歌曲"))
            self.history_table.setItem(row, 1, song_name)
            
            # 歌手
            artist = QTableWidgetItem(item.get("artist", "未知歌手"))
            self.history_table.setItem(row, 2, artist)
            
            # 识别时间
            recognition_time = QTableWidgetItem(item.get("recognition_time", ""))
            self.history_table.setItem(row, 3, recognition_time)
            
            # 准确度
            confidence = item.get("confidence", 0)
            confidence_item = QTableWidgetItem(f"{confidence:.2%}" if isinstance(confidence, float) else str(confidence))
            self.history_table.setItem(row, 4, confidence_item)
            
            # 存储歌曲数据，用于后续操作
            for col in range(5):
                self.history_table.item(row, col).setData(Qt.ItemDataRole.UserRole, item)
            
            # 设置封面列宽
            self.history_table.setColumnWidth(0, 60)
    
    def play_song(self, song_data):
        """播放歌曲"""
        # 获取歌曲路径和名称
        song_path = song_data.get("file_path", "")
        song_name = song_data.get("song_name", "未知歌曲")
        
        if not song_path or not os.path.exists(song_path):
            print(f"无法播放歌曲，文件路径不存在: {song_path}")
            return
            
        # 获取主窗口
        main_window = self.window()
        if not main_window:
            print("未找到主窗口，无法播放歌曲")
            return
            
        # 获取音乐播放器选项卡
        music_player_tab = None
        if hasattr(main_window, 'get_music_player_tab'):
            music_player_tab = main_window.get_music_player_tab()
        elif hasattr(main_window, 'music_player_tab'):
            music_player_tab = main_window.music_player_tab
            
        if not music_player_tab:
            print("未找到音乐播放器选项卡，无法播放歌曲")
            # 尝试使用信号播放（兼容旧方法）
            self.play_song_signal.emit(song_path, song_name)
            return
            
        # 切换到音乐播放器选项卡
        if hasattr(main_window, 'switch_to_tab'):
            try:
                # 歌曲播放选项卡通常是索引3
                main_window.switch_to_tab(3)
            except Exception as e:
                print(f"切换到音乐播放选项卡失败: {str(e)}")
        
        # 播放歌曲
        cover_path = song_data.get("cover_path", "")
        
        try:
            # 调用音乐播放器的播放方法
            if hasattr(music_player_tab, 'play_music'):
                # 传递完整的歌曲信息，包括封面路径
                music_player_tab.play_music(
                    song_path, 
                    song_name=song_name, 
                    artist=song_data.get("artist", "未知艺术家"),
                    cover_path=cover_path if os.path.exists(cover_path) else None
                )
                print(f"正在播放: {song_name}")
            else:
                print("音乐播放器没有play_music方法")
                # 尝试使用信号播放（兼容旧方法）
                self.play_song_signal.emit(song_path, song_name)
        except Exception as e:
            print(f"播放歌曲时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def edit_profile(self):
        """编辑用户资料"""
        # 这里可以弹出一个编辑资料的对话框
        # 简化实现，仅更改用户名
        username, ok = QInputDialog.getText(
            self, "编辑资料", "请输入新的用户名:", 
            QLineEdit.EchoMode.Normal, self.user_data.get("username", "音乐爱好者")
        )
        
        if ok and username:
            self.user_data["username"] = username
            self.save_user_data()
            self.setup_ui()  # 刷新UI
    
    def save_settings(self):
        """保存设置"""
        if "settings" not in self.user_data:
            self.user_data["settings"] = {}
        
        self.user_data["settings"]["theme"] = self.theme_combo.currentText()
        self.user_data["settings"]["language"] = self.language_combo.currentText()
        self.user_data["settings"]["startup"] = self.startup_combo.currentText()
        self.user_data["settings"]["audio_quality"] = self.quality_combo.currentText()
        self.user_data["settings"]["recognition_duration"] = self.duration_combo.currentText()
        self.user_data["settings"]["recording_device"] = self.device_combo.currentText()
        
        self.save_user_data()
    
    def reset_settings(self):
        """恢复默认设置"""
        default_settings = {
            "theme": "浅色模式",
            "language": "简体中文",
            "startup": "默认显示识别页面",
            "audio_quality": "标准质量",
            "recognition_duration": "10秒",
            "recording_device": "默认系统设备"
        }
        
        self.user_data["settings"] = default_settings
        self.save_user_data()
        
        # 更新界面
        self.theme_combo.setCurrentText(default_settings["theme"])
        self.language_combo.setCurrentText(default_settings["language"])
        self.startup_combo.setCurrentText(default_settings["startup"])
        self.quality_combo.setCurrentText(default_settings["audio_quality"])
        self.duration_combo.setCurrentText(default_settings["recognition_duration"])
        self.device_combo.setCurrentText(default_settings["recording_device"])
    
    # 添加新方法处理表格双击播放
    def play_selected_favorite(self, index):
        """播放选中的收藏歌曲"""
        row = index.row()
        item = self.favorites_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if item:
            self.play_song(item)
    
    def play_selected_history(self, index):
        """播放选中的历史记录歌曲"""
        row = index.row()
        item = self.history_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if item:
            self.play_song(item)
    
    # 添加右键菜单
    def show_favorite_context_menu(self, position):
        """显示收藏表格右键菜单"""
        current_row = self.favorites_table.currentRow()
        if current_row < 0:
            return
            
        item = self.favorites_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        if not item:
            return
            
        from PyQt6.QtWidgets import QMenu
        
        context_menu = QMenu(self)
        
        # 播放选项
        play_action = QAction("播放", self)
        play_action.triggered.connect(lambda: self.play_song(item))
        context_menu.addAction(play_action)
        
        # 移除选项
        remove_action = QAction("取消收藏", self)
        remove_action.triggered.connect(lambda: self.remove_from_favorites(item.get("song_id")))
        context_menu.addAction(remove_action)
        
        # 在光标位置显示菜单
        context_menu.exec(self.favorites_table.viewport().mapToGlobal(position))
    
    def show_history_context_menu(self, position):
        """显示历史记录上下文菜单"""
        menu = QMenu()
        
        # 获取选中的项
        selected_rows = set(item.row() for item in self.history_table.selectedItems())
        if not selected_rows:
            return
            
        # 获取选中行的第一行
        row = next(iter(selected_rows))
        
        # 获取歌曲数据
        song_data = self.history_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        # 播放菜单项
        play_action = QAction("播放", self)
        play_action.triggered.connect(lambda: self.play_song(song_data))
        menu.addAction(play_action)
        
        # 添加到收藏菜单项
        add_to_favorite_action = QAction("添加到收藏", self)
        add_to_favorite_action.triggered.connect(lambda: self.add_history_to_favorite(song_data))
        menu.addAction(add_to_favorite_action)
        
        # 从历史记录中删除
        remove_action = QAction("从历史记录中删除", self)
        remove_action.triggered.connect(lambda: self.remove_from_history(row))
        menu.addAction(remove_action)
        
        # 显示菜单
        menu.exec(self.history_table.viewport().mapToGlobal(position))
    
    def add_history_to_favorite(self, song_data):
        """将历史记录项添加到收藏"""
        # 检查歌曲是否已在收藏中
        for favorite in self.user_data.get("favorites", []):
            if favorite.get("song_id") == song_data.get("song_id") or \
               (favorite.get("song_name") == song_data.get("song_name") and 
                favorite.get("artist") == song_data.get("artist")):
                # 歌曲已存在于收藏夹
                QMessageBox.information(self, "提示", "该歌曲已在收藏列表中")
                return False
        
        # 添加收藏时间
        song_data["favorite_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 添加到收藏列表
        if "favorites" not in self.user_data:
            self.user_data["favorites"] = []
        
        self.user_data["favorites"].append(song_data)
        self.save_user_data()
        
        # 刷新显示
        self.load_favorites()
        
        QMessageBox.information(self, "提示", f"已将 {song_data.get('song_name', '未知歌曲')} 添加到收藏")
        return True
    
    def remove_from_history(self, row):
        """从历史记录中删除指定行"""
        if row < 0 or row >= len(self.user_data.get("history", [])):
            return
        
        # 从数据结构中删除
        del self.user_data["history"][row]
        self.save_user_data()
        
        # 从表格中删除
        self.history_table.removeRow(row)
        
        # 更新用户界面中的历史记录数量显示
        self.update_stats_display()
    
    def update_stats_display(self):
        """更新用户界面中的统计数量显示"""
        favorites_count = len(self.user_data.get("favorites", []))
        history_count = len(self.user_data.get("history", []))
        
        # 使用成员变量更新统计信息
        if hasattr(self, 'favorites_count_label'):
            self.favorites_count_label.setText(f"收藏: {favorites_count}")
        
        if hasattr(self, 'history_count_label'):
            self.history_count_label.setText(f"历史: {history_count}") 