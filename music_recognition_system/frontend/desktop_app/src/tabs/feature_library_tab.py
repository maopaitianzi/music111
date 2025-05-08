from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QFileDialog, QProgressBar, QListWidget, QListWidgetItem,
                            QMessageBox, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QAbstractItemView, QTabWidget, QMenu, QDialog, QFormLayout,
                            QDialogButtonBox, QCheckBox, QSplitter)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDir, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QAction, QCursor
import os
import sys
import time
import traceback
import json

# 将项目根目录添加到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from music_recognition_system.utils.audio_features import AudioFeatureExtractor, FeatureDatabase
    print("成功导入音频特征提取模块")
except ImportError as e:
    print(f"导入音频特征提取模块失败: {str(e)}")
    print(f"当前sys.path: {sys.path}")
    print(f"尝试导入路径: {os.path.join(project_root, 'music_recognition_system/utils/audio_features.py')}")
    traceback.print_exc()
    
    # 如果导入失败，则创建模拟类
    class AudioFeatureExtractor:
        def extract_features(self, audio_path):
            time.sleep(0.5)  # 模拟处理时间
            return {
                "file_path": audio_path,
                "file_name": os.path.basename(audio_path),
                "duration": 180.0  # 模拟3分钟长度
            }
    
    # 使用类静态变量来模拟持久化存储
    class FeatureDatabase:
        # 静态类变量，所有实例共享
        _features = {}
        _initialized = False
        
        def __init__(self, database_path=None):
            print(f"使用模拟特征数据库，路径: {database_path}")
            self.database_path = database_path
            
            # 尝试从文件加载已存储的特征（如果存在）
            if not FeatureDatabase._initialized and database_path:
                try:
                    features_dir = os.path.join(database_path, "features")
                    os.makedirs(features_dir, exist_ok=True)
                    
                    # 尝试加载模拟索引文件
                    mock_index_path = os.path.join(database_path, "mock_index.json")
                    if os.path.exists(mock_index_path):
                        with open(mock_index_path, 'r', encoding='utf-8') as f:
                            FeatureDatabase._features = json.load(f)
                            print(f"从模拟索引文件加载了 {len(FeatureDatabase._features)} 个特征")
                except Exception as e:
                    print(f"加载模拟特征文件失败: {str(e)}")
                
                FeatureDatabase._initialized = True
            
        def add_feature(self, feature_data):
            file_id = self._generate_file_id(feature_data["file_name"])
            FeatureDatabase._features[file_id] = feature_data
            print(f"添加特征到模拟数据库: {feature_data['file_name']}")
            
            # 尝试保存到模拟索引文件
            if self.database_path:
                try:
                    os.makedirs(self.database_path, exist_ok=True)
                    mock_index_path = os.path.join(self.database_path, "mock_index.json")
                    with open(mock_index_path, 'w', encoding='utf-8') as f:
                        json.dump(FeatureDatabase._features, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"保存模拟索引文件失败: {str(e)}")
                    
            return True
        
        def get_feature(self, file_id):
            if file_id in FeatureDatabase._features:
                return FeatureDatabase._features[file_id]
            return None
            
        def get_all_files(self):
            print(f"从模拟数据库获取文件，当前有 {len(FeatureDatabase._features)} 个文件")
            return [
                {
                    "id": self._generate_file_id(info["file_name"]),
                    "file_name": info["file_name"],
                    "file_path": info.get("file_path", ""),
                    "duration": info.get("duration", 0),
                    "added_time": info.get("added_time", ""),
                    "song_name": info.get("song_name", ""),
                    "author": info.get("author", "")
                }
                for file_id, info in FeatureDatabase._features.items()
            ]
        
        def remove_feature(self, file_id):
            if file_id in FeatureDatabase._features:
                del FeatureDatabase._features[file_id]
                
                # 保存更新后的索引
                if self.database_path:
                    try:
                        mock_index_path = os.path.join(self.database_path, "mock_index.json")
                        with open(mock_index_path, 'w', encoding='utf-8') as f:
                            json.dump(FeatureDatabase._features, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"保存模拟索引文件失败: {str(e)}")
                
                return True
            return False
            
        def _generate_file_id(self, file_name):
            import hashlib
            # 简单地使用文件名的哈希作为ID
            return hashlib.md5(file_name.encode('utf-8')).hexdigest()
            
        @property
        def index_path(self):
            if self.database_path:
                return os.path.join(self.database_path, "mock_index.json")
            return None

class FeatureExtractionThread(QThread):
    """特征提取线程，避免UI卡顿"""
    progress_updated = pyqtSignal(int, int)  # 当前进度，总数
    file_processed = pyqtSignal(str, bool)  # 处理完成的文件名，是否成功
    extraction_completed = pyqtSignal(bool, str, int)  # 是否成功，消息，成功提取的数量
    
    def __init__(self, folder_path, database_path=None, use_filename=False, default_author=""):
        super().__init__()
        self.folder_path = folder_path
        self.database_path = database_path
        self.extractor = AudioFeatureExtractor()
        self.db = FeatureDatabase(database_path)
        self.use_filename = use_filename
        self.default_author = default_author
        
    def run(self):
        try:
            # 获取文件夹中的所有音频文件
            audio_files = []
            for root, _, files in os.walk(self.folder_path):
                for file in files:
                    if file.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a')):
                        audio_files.append(os.path.join(root, file))
            
            total_files = len(audio_files)
            if total_files == 0:
                self.extraction_completed.emit(False, "所选文件夹中没有找到音频文件", 0)
                return
                
            success_count = 0
            # 处理每个音频文件
            for i, audio_file in enumerate(audio_files):
                try:
                    # 提取特征
                    features = self.extractor.extract_features(audio_file)
                    
                    # 添加歌曲信息
                    if self.use_filename:
                        # 使用文件名（不含扩展名）作为歌曲名
                        base_name = os.path.basename(audio_file)
                        song_name = os.path.splitext(base_name)[0]
                        features["song_name"] = song_name
                    
                    # 设置默认作者
                    features["author"] = self.default_author
                    
                    # 添加到数据库
                    success = "error" not in features and self.db.add_feature(features)
                    if success:
                        success_count += 1
                        self.file_processed.emit(os.path.basename(audio_file), True)
                    else:
                        self.file_processed.emit(os.path.basename(audio_file), False)
                except Exception as e:
                    self.file_processed.emit(os.path.basename(audio_file), False)
                
                # 更新进度
                self.progress_updated.emit(i + 1, total_files)
            
            self.extraction_completed.emit(
                success_count > 0, 
                f"成功提取 {success_count}/{total_files} 个音频文件的特征",
                success_count
            )
            
        except Exception as e:
            self.extraction_completed.emit(False, f"特征提取过程中出错: {str(e)}", 0)

class FeatureLibraryTab(QWidget):
    """特征库创建选项卡"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置固定的数据库路径，使用项目根目录的绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.abspath(os.path.join(current_dir, "../../../../../"))
        self.database_path = os.path.join(workspace_root, "music_recognition_system/database/music_features_db")
        print(f"使用特征数据库路径: {self.database_path}")
        
        # 确保数据库目录存在
        os.makedirs(self.database_path, exist_ok=True)
        
        self.db = FeatureDatabase(self.database_path)
        self.setup_ui()
        self.load_existing_features()
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        # 创建选项卡小部件
        self.tab_widget = QTabWidget()
        
        # 创建库管理选项卡
        self.library_tab = QWidget()
        self.setup_library_tab()
        
        # 创建批量添加选项卡
        self.batch_add_tab = QWidget()
        self.setup_batch_add_tab()
        
        # 添加选项卡
        self.tab_widget.addTab(self.library_tab, "音频特征库")
        self.tab_widget.addTab(self.batch_add_tab, "批量添加特征")
        
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)
    
    def setup_library_tab(self):
        """设置特征库管理选项卡"""
        layout = QVBoxLayout(self.library_tab)
        
        # 顶部标题和统计信息
        header_layout = QHBoxLayout()
        
        title = QLabel("特征库管理")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1DB954;")
        
        self.stats_label = QLabel("特征库统计: 0 首歌曲")
        self.stats_label.setStyleSheet("color: #1DB954; font-weight: bold;")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.stats_label)
        
        # 搜索和筛选区域
        filter_layout = QHBoxLayout()
        
        search_label = QLabel("搜索:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入文件名、路径等关键词搜索")
        self.search_input.textChanged.connect(self.filter_features)
        
        sort_label = QLabel("排序:")
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["文件名", "添加时间", "时长"])
        self.sort_combo.currentIndexChanged.connect(self.sort_features)
        
        add_button = QPushButton("添加音频")
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: #FFFFFF;
                border-radius: 5px;
                border: none;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #1ED760;
            }
            QPushButton:pressed {
                background-color: #0A8C3C;
            }
        """)
        add_button.clicked.connect(self.add_single_file)
        
        refresh_button = QPushButton("刷新列表")
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: #FFFFFF;
                border-radius: 5px;
                border: none;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #5A9FF2;
            }
            QPushButton:pressed {
                background-color: #3A80D2;
            }
        """)
        refresh_button.clicked.connect(self.refresh_feature_list)
        
        filter_layout.addWidget(search_label)
        filter_layout.addWidget(self.search_input, 3)
        filter_layout.addWidget(sort_label)
        filter_layout.addWidget(self.sort_combo, 1)
        filter_layout.addWidget(add_button)
        filter_layout.addWidget(refresh_button)
        
        # 特征列表表格
        self.feature_table = QTableWidget()
        self.feature_table.setColumnCount(6)
        self.feature_table.setHorizontalHeaderLabels(["ID", "文件名", "歌曲名", "作者", "文件路径", "时长(秒)", "添加时间"])
        self.feature_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.feature_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.feature_table.verticalHeader().setVisible(False)
        self.feature_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.feature_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.feature_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 将组件添加到布局
        layout.addLayout(header_layout)
        layout.addLayout(filter_layout)
        layout.addWidget(self.feature_table)
    
    def setup_batch_add_tab(self):
        """设置批量添加特征选项卡"""
        layout = QVBoxLayout(self.batch_add_tab)
        
        # 顶部标题
        title = QLabel("批量添加特征")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px 0;")
        
        # 描述文本
        description = QLabel("选择音乐文件夹，提取其中所有音频文件的特征，用于后续歌曲识别")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setStyleSheet("color: #666666; margin-bottom: 20px;")
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 选择文件夹按钮
        self.select_folder_button = QPushButton("选择文件夹")
        self.select_folder_button.setFixedSize(150, 40)
        self.select_folder_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.select_folder_button.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: #FFFFFF;
                border-radius: 5px;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #1ED760;
            }
            QPushButton:pressed {
                background-color: #0A8C3C;
            }
        """)
        
        # 开始提取按钮
        self.start_button = QPushButton("开始提取")
        self.start_button.setFixedSize(150, 40)
        self.start_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.start_button.setEnabled(False)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: #FFFFFF;
                border-radius: 5px;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #1ED760;
            }
            QPushButton:pressed {
                background-color: #0A8C3C;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #888888;
            }
        """)
        
        button_layout.addWidget(self.select_folder_button)
        button_layout.addWidget(self.start_button)
        
        # 当前选择的文件夹显示
        self.folder_label = QLabel("未选择文件夹")
        self.folder_label.setStyleSheet("color: #666666; margin: 10px 0;")
        
        # 进度条
        self.progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #1DB954;
            }
        """)
        
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("color: #666666; margin: 5px 0;")
        
        self.progress_layout.addWidget(self.progress_bar)
        self.progress_layout.addWidget(self.status_label)
        
        # 处理文件列表
        self.file_list_label = QLabel("处理文件:")
        self.file_list_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #EEEEEE;
            }
        """)
        
        # 添加组件到主布局
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(button_layout)
        layout.addWidget(self.folder_label)
        layout.addLayout(self.progress_layout)
        layout.addWidget(self.file_list_label)
        layout.addWidget(self.file_list)
        
        # 连接信号
        self.select_folder_button.clicked.connect(self.select_folder)
        self.start_button.clicked.connect(self.start_extraction)
        
        # 初始化变量
        self.selected_folder = ""
        self.extraction_thread = None
        
    def load_existing_features(self):
        """加载已有的特征库统计信息并显示在表格中"""
        try:
            print(f"正在加载特征库，数据库路径: {self.database_path}")
            print(f"数据库类型: {type(self.db).__name__}")
            
            # 打印数据库文件是否存在
            if hasattr(self.db, 'index_path') and self.db.index_path:
                index_exists = os.path.exists(self.db.index_path)
                print(f"索引文件路径: {self.db.index_path}, 是否存在: {index_exists}")
                
                if index_exists:
                    try:
                        import json
                        with open(self.db.index_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            print(f"索引文件内容: 包含 {len(data)} 个条目")
                    except Exception as e:
                        print(f"读取索引文件失败: {str(e)}")
            
            self.refresh_feature_list()
            
        except Exception as e:
            print(f"加载特征库统计信息失败: {str(e)}")
            traceback.print_exc()
    
    def refresh_feature_list(self):
        """刷新特征列表显示"""
        try:
            # 获取所有特征文件
            files = self.db.get_all_files()
            self.current_features = files
            
            # 更新统计信息
            self.stats_label.setText(f"特征库统计: {len(files)} 首歌曲")
            
            # 更新表格
            self.update_feature_table(files)
            
        except Exception as e:
            print(f"刷新特征列表失败: {str(e)}")
            traceback.print_exc()
    
    def update_feature_table(self, features):
        """更新特征表格数据"""
        # 清空表格
        self.feature_table.setRowCount(0)
        
        # 添加数据
        for i, feature in enumerate(features):
            self.feature_table.insertRow(i)
            
            # 设置ID（隐藏但可用于操作）
            id_item = QTableWidgetItem(feature.get("id", ""))
            id_item.setToolTip(feature.get("id", ""))
            self.feature_table.setItem(i, 0, id_item)
            
            # 设置文件名
            name_item = QTableWidgetItem(feature.get("file_name", ""))
            self.feature_table.setItem(i, 1, name_item)
            
            # 设置歌曲名
            song_name_item = QTableWidgetItem(feature.get("song_name", ""))
            self.feature_table.setItem(i, 2, song_name_item)
            
            # 设置作者
            author_item = QTableWidgetItem(feature.get("author", ""))
            self.feature_table.setItem(i, 3, author_item)
            
            # 设置文件路径
            path_item = QTableWidgetItem(feature.get("file_path", ""))
            path_item.setToolTip(feature.get("file_path", ""))
            self.feature_table.setItem(i, 4, path_item)
            
            # 设置时长
            duration = feature.get("duration", 0)
            duration_str = f"{duration:.2f}" if isinstance(duration, (int, float)) else str(duration)
            duration_item = QTableWidgetItem(duration_str)
            self.feature_table.setItem(i, 5, duration_item)
            
            # 设置添加时间
            time_item = QTableWidgetItem(feature.get("added_time", ""))
            self.feature_table.setItem(i, 6, time_item)
        
        # 设置列宽
        self.feature_table.setColumnWidth(0, 60)  # ID列
        self.feature_table.setColumnWidth(1, 200)  # 文件名列
        self.feature_table.setColumnWidth(3, 80)   # 时长列
        self.feature_table.setColumnWidth(4, 150)  # 添加时间列
    
    def filter_features(self):
        """根据搜索条件筛选特征"""
        search_text = self.search_input.text().lower()
        
        # 如果搜索框为空，显示所有特征
        if not search_text:
            self.update_feature_table(self.current_features)
            return
        
        # 筛选匹配的特征
        filtered_features = []
        for feature in self.current_features:
            # 在文件名和路径中搜索
            if (search_text in feature.get("file_name", "").lower() or 
                search_text in feature.get("file_path", "").lower()):
                filtered_features.append(feature)
        
        # 更新表格
        self.update_feature_table(filtered_features)
    
    def sort_features(self):
        """根据选定的条件排序特征"""
        sort_by = self.sort_combo.currentText()
        
        if sort_by == "文件名":
            sorted_features = sorted(self.current_features, key=lambda x: x.get("file_name", "").lower())
        elif sort_by == "添加时间":
            sorted_features = sorted(self.current_features, key=lambda x: x.get("added_time", ""), reverse=True)
        elif sort_by == "时长":
            sorted_features = sorted(self.current_features, key=lambda x: float(x.get("duration", 0)) if x.get("duration", 0) else 0)
        else:
            sorted_features = self.current_features
        
        # 更新表格
        self.update_feature_table(sorted_features)
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        context_menu = QMenu()
        
        # 检查是否有选中的项
        if self.feature_table.selectedItems():
            edit_action = QAction("编辑歌曲信息", self)
            edit_action.triggered.connect(self.edit_song_info)
            context_menu.addAction(edit_action)
            
            delete_action = QAction("删除", self)
            delete_action.triggered.connect(self.delete_selected_features)
            context_menu.addAction(delete_action)
            
            play_action = QAction("播放", self)
            play_action.triggered.connect(self.play_selected_feature)
            context_menu.addAction(play_action)
            
            view_action = QAction("查看详情", self)
            view_action.triggered.connect(self.view_feature_details)
            context_menu.addAction(view_action)
        
        refresh_action = QAction("刷新列表", self)
        refresh_action.triggered.connect(self.refresh_feature_list)
        context_menu.addAction(refresh_action)
        
        # 显示菜单
        context_menu.exec(QCursor.pos())
    
    def delete_selected_features(self):
        """删除选中的特征"""
        selected_rows = set(item.row() for item in self.feature_table.selectedItems())
        
        if not selected_rows:
            return
            
        # 确认删除
        confirm = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除选中的 {len(selected_rows)} 个特征吗？这将从特征库中永久删除这些数据。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # 收集要删除的ID
            ids_to_delete = [self.feature_table.item(row, 0).text() for row in selected_rows]
            
            # 执行删除
            delete_count = 0
            for file_id in ids_to_delete:
                if self.db.remove_feature(file_id):
                    delete_count += 1
            
            # 刷新列表
            self.refresh_feature_list()
            
            # 显示结果
            QMessageBox.information(
                self, 
                "删除结果", 
                f"成功删除 {delete_count} 个特征。"
            )
    
    def play_selected_feature(self):
        """播放选中的特征对应的音频文件"""
        selected_items = self.feature_table.selectedItems()
        if not selected_items:
            return
            
        # 获取选中行的文件路径
        row = selected_items[0].row()
        file_path = self.feature_table.item(row, 2).text()
        
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(
                self, 
                "无法播放", 
                "文件路径不存在或无效。"
            )
            return
            
        # 尝试使用系统默认程序打开音频文件
        try:
            from PyQt6.QtGui import QDesktopServices
            from PyQt6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        except Exception as e:
            QMessageBox.warning(
                self, 
                "播放错误", 
                f"无法播放文件: {str(e)}"
            )
    
    def view_feature_details(self):
        """查看特征详情"""
        selected_items = self.feature_table.selectedItems()
        if not selected_items:
            return
            
        # 获取选中行的特征ID
        row = selected_items[0].row()
        file_id = self.feature_table.item(row, 0).text()
        
        # 获取特征详情
        feature_data = self.db.get_feature(file_id)
        
        if not feature_data:
            QMessageBox.warning(
                self, 
                "无法查看详情", 
                "未找到相关特征数据。"
            )
            return
            
        # 创建详情对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("特征详情")
        dialog.setMinimumWidth(600)
        
        layout = QVBoxLayout(dialog)
        
        # 基本信息区域
        form_layout = QFormLayout()
        
        file_name_label = QLabel(feature_data.get("file_name", ""))
        file_name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form_layout.addRow("文件名:", file_name_label)
        
        song_name_label = QLabel(feature_data.get("song_name", ""))
        song_name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form_layout.addRow("歌曲名:", song_name_label)
        
        author_label = QLabel(feature_data.get("author", ""))
        author_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form_layout.addRow("作者:", author_label)
        
        file_path_label = QLabel(feature_data.get("file_path", ""))
        file_path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form_layout.addRow("文件路径:", file_path_label)
        
        duration_label = QLabel(f"{feature_data.get('duration', 0):.2f} 秒")
        form_layout.addRow("时长:", duration_label)
        
        # 添加其他特征数据
        features_text = QTableWidget()
        features_text.setColumnCount(2)
        features_text.setHorizontalHeaderLabels(["特征名", "值"])
        features_text.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # 填充特征数据
        row = 0
        for key, value in feature_data.items():
            # 跳过基本信息和大型特征数据
            if key in ["file_name", "file_path", "duration", "error", "fingerprint", 
                      "mel_mean", "mel_std", "mfcc_mean", "mfcc_std", "chroma_mean", 
                      "song_name", "author"]:
                continue
                
            features_text.insertRow(row)
            features_text.setItem(row, 0, QTableWidgetItem(key))
            
            # 处理不同类型的值
            if isinstance(value, (list, dict)):
                value_str = f"{type(value).__name__} (长度: {len(value)})"
            else:
                value_str = str(value)
                
            features_text.setItem(row, 1, QTableWidgetItem(value_str))
            row += 1
        
        # 创建按钮盒
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.reject)
        
        # 添加组件到布局
        layout.addLayout(form_layout)
        layout.addWidget(QLabel("特征数据:"))
        layout.addWidget(features_text)
        layout.addWidget(button_box)
        
        # 显示对话框
        dialog.exec()
    
    def add_single_file(self):
        """添加单个音频文件到特征库"""
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择音频文件", 
            "", 
            "音频文件 (*.mp3 *.wav *.flac *.ogg *.m4a)"
        )
        
        if not file_path:
            return
        
        # 创建对话框收集歌曲信息
        info_dialog = QDialog(self)
        info_dialog.setWindowTitle("输入歌曲信息")
        info_dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(info_dialog)
        
        # 文件名显示
        file_label = QLabel(f"文件: {os.path.basename(file_path)}")
        file_label.setStyleSheet("font-weight: bold;")
        
        # 表单布局
        form_layout = QFormLayout()
        
        # 歌曲名输入
        song_name_input = QLineEdit()
        song_name_input.setPlaceholderText("请输入歌曲名")
        form_layout.addRow("歌曲名:", song_name_input)
        
        # 作者输入
        author_input = QLineEdit()
        author_input.setPlaceholderText("请输入作者名")
        form_layout.addRow("作者:", author_input)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(info_dialog.accept)
        button_box.rejected.connect(info_dialog.reject)
        
        # 添加组件到布局
        layout.addWidget(file_label)
        layout.addLayout(form_layout)
        layout.addWidget(button_box)
        
        # 显示对话框
        song_name = ""
        author = ""
        if info_dialog.exec() == QDialog.DialogCode.Accepted:
            song_name = song_name_input.text()
            author = author_input.text()
        else:
            return  # 用户取消了输入
            
        # 显示处理对话框
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("提取特征")
        progress_dialog.setFixedSize(400, 100)
        
        dialog_layout = QVBoxLayout(progress_dialog)
        
        progress_label = QLabel(f"正在提取 {os.path.basename(file_path)} 的特征...")
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # 不确定进度
        
        dialog_layout.addWidget(progress_label)
        dialog_layout.addWidget(progress_bar)
        
        # 使用延迟调用来允许对话框显示
        def process_file():
            try:
                # 创建特征提取器
                extractor = AudioFeatureExtractor()
                
                # 提取特征
                features = extractor.extract_features(file_path)
                
                # 添加歌曲信息
                features["song_name"] = song_name
                features["author"] = author
                
                # 添加到数据库
                if "error" not in features and self.db.add_feature(features):
                    # 关闭对话框
                    progress_dialog.accept()
                    
                    # 刷新列表
                    self.refresh_feature_list()
                    
                    # 显示成功消息
                    QMessageBox.information(
                        self, 
                        "提取成功", 
                        f"成功提取 {os.path.basename(file_path)} 的特征。"
                    )
                else:
                    # 显示错误
                    error_msg = features.get("error", "未知错误")
                    progress_dialog.reject()
                    QMessageBox.warning(
                        self, 
                        "提取失败", 
                        f"无法提取特征: {error_msg}"
                    )
            except Exception as e:
                # 显示错误
                progress_dialog.reject()
                QMessageBox.warning(
                    self, 
                    "提取失败", 
                    f"提取特征过程中出错: {str(e)}"
                )
        
        # 显示对话框并延迟执行处理
        QTimer.singleShot(100, process_file)
        progress_dialog.exec()
    
    def select_folder(self):
        """选择文件夹对话框"""
        folder = QFileDialog.getExistingDirectory(self, "选择音乐文件夹")
        if folder:
            self.selected_folder = folder
            self.folder_label.setText(f"已选择: {folder}")
            self.start_button.setEnabled(True)
            self.status_label.setText(f"已选择文件夹: {folder}")
    
    def start_extraction(self):
        """开始特征提取过程"""
        if not self.selected_folder:
            return
            
        # 清空文件列表
        self.file_list.clear()
        
        # 禁用按钮
        self.select_folder_button.setEnabled(False)
        self.start_button.setEnabled(False)
        
        # 更新状态
        self.status_label.setText("正在提取特征...")
        
        # 创建并启动提取线程，使用固定的数据库路径
        use_filename = self.use_filename_checkbox.isChecked()
        default_author = self.default_author_input.text()
        
        self.extraction_thread = FeatureExtractionThread(
            self.selected_folder, 
            self.database_path,
            use_filename,
            default_author
        )
        self.extraction_thread.progress_updated.connect(self.update_progress)
        self.extraction_thread.file_processed.connect(self.add_processed_file)
        self.extraction_thread.extraction_completed.connect(self.extraction_finished)
        self.extraction_thread.start()
    
    def update_progress(self, current, total):
        """更新进度条"""
        progress = int(current / total * 100)
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"正在处理: {current}/{total}")
    
    def add_processed_file(self, filename, success):
        """添加处理完成的文件到列表"""
        if success:
            item = QListWidgetItem(f"✓ {filename}")
            item.setForeground(QColor("#1DB954"))
        else:
            item = QListWidgetItem(f"✗ {filename}")
            item.setForeground(QColor("#FF0000"))
        self.file_list.addItem(item)
        self.file_list.scrollToBottom()
    
    def extraction_finished(self, success, message, success_count):
        """特征提取完成回调"""
        # 重新启用按钮
        self.select_folder_button.setEnabled(True)
        self.start_button.setEnabled(True)
        
        # 更新状态
        if success:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: #1DB954; font-weight: bold;")
            
            # 刷新特征库列表
            self.refresh_feature_list()
            
            # 显示完成消息
            QMessageBox.information(self, "特征提取完成", 
                                   f"成功提取了 {success_count} 个音频文件的特征。\n"
                                   "现在可以使用识别功能来识别音乐了。")
        else:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: #FF0000; font-weight: bold;")
            
            # 显示错误消息
            QMessageBox.warning(self, "特征提取失败", 
                                f"特征提取过程中出现错误: {message}\n"
                                "请检查音频文件格式或选择其他文件夹。")
    
    def edit_song_info(self):
        """编辑选中音频的歌曲信息"""
        selected_items = self.feature_table.selectedItems()
        if not selected_items:
            return
            
        # 获取选中行的特征ID和当前信息
        row = selected_items[0].row()
        file_id = self.feature_table.item(row, 0).text()
        file_name = self.feature_table.item(row, 1).text()
        current_song_name = self.feature_table.item(row, 2).text()
        current_author = self.feature_table.item(row, 3).text()
        
        # 获取完整特征数据
        feature_data = self.db.get_feature(file_id)
        
        if not feature_data:
            QMessageBox.warning(
                self, 
                "无法编辑", 
                "未找到相关特征数据。"
            )
            return
            
        # 创建编辑对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑歌曲信息")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # 文件名显示（不可编辑）
        file_label = QLabel(f"文件: {file_name}")
        file_label.setStyleSheet("font-weight: bold;")
        
        # 表单布局
        form_layout = QFormLayout()
        
        # 歌曲名输入
        song_name_input = QLineEdit(current_song_name)
        form_layout.addRow("歌曲名:", song_name_input)
        
        # 作者输入
        author_input = QLineEdit(current_author)
        form_layout.addRow("作者:", author_input)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        # 添加组件到布局
        layout.addWidget(file_label)
        layout.addLayout(form_layout)
        layout.addWidget(button_box)
        
        # 显示对话框并处理结果
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 获取用户输入
            new_song_name = song_name_input.text()
            new_author = author_input.text()
            
            # 更新特征数据
            feature_data["song_name"] = new_song_name
            feature_data["author"] = new_author
            
            # 保存到数据库
            self.db.add_feature(feature_data)
            
            # 更新表格显示
            self.refresh_feature_list()
            
            # 显示成功消息
            QMessageBox.information(
                self, 
                "更新成功", 
                f"成功更新 {file_name} 的歌曲信息。"
            )