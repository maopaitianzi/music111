from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QFileDialog, QProgressBar, QListWidget, QListWidgetItem,
                            QMessageBox, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QAbstractItemView, QTabWidget, QMenu, QDialog, QFormLayout,
                            QDialogButtonBox, QCheckBox, QSplitter, QMainWindow)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDir, QTimer, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QAction, QCursor, QPixmap, QImage, QPainter, QPen, QIcon
import os
import sys
import time
import traceback
import json
import shutil
from datetime import datetime
import hashlib
from PyQt6.QtWidgets import QApplication

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
    
    def __init__(self, folder_path, database_path=None, use_filename=False, default_author="", auto_find_cover=True, cover_format="", save_cover_image=None):
        super().__init__()
        self.folder_path = folder_path
        self.database_path = database_path
        self.extractor = AudioFeatureExtractor()
        try:
            self.db = FeatureDatabase(database_path)
            print(f"成功初始化特征数据库: {database_path}")
        except Exception as e:
            print(f"初始化特征数据库失败: {str(e)}")
            print(f"Stack trace: {traceback.format_exc()}")
            self.db = None
        self.use_filename = use_filename
        self.default_author = default_author
        self.auto_find_cover = auto_find_cover
        self.cover_format = cover_format
        self.save_cover_image = save_cover_image
        
    def run(self):
        try:
            # 验证数据库对象是否有效
            if self.db is None:
                self.extraction_completed.emit(False, "特征数据库初始化失败，无法继续处理", 0)
                return
            
            # 验证文件夹路径存在
            if not os.path.exists(self.folder_path):
                self.extraction_completed.emit(False, f"文件夹路径不存在: {self.folder_path}", 0)
                return
            
            # 获取文件夹中的所有音频文件
            audio_files = []
            try:
                for root, _, files in os.walk(self.folder_path):
                    for file in files:
                        if file.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a')):
                            audio_files.append(os.path.join(root, file))
            except Exception as e:
                self.extraction_completed.emit(False, f"扫描文件夹出错: {str(e)}", 0)
                print(f"扫描文件夹出错: {str(e)}")
                print(f"Stack trace: {traceback.format_exc()}")
                return
            
            total_files = len(audio_files)
            if total_files == 0:
                self.extraction_completed.emit(False, "所选文件夹中没有找到音频文件", 0)
                return
                
            success_count = 0
            error_count = 0
            errors = []
            
            # 处理每个音频文件
            for i, audio_file in enumerate(audio_files):
                try:
                    # 验证文件是否存在
                    if not os.path.exists(audio_file):
                        self.file_processed.emit(os.path.basename(audio_file), False)
                        errors.append(f"文件不存在: {audio_file}")
                        continue
                        
                    # 验证文件是否可读
                    if not os.access(audio_file, os.R_OK):
                        self.file_processed.emit(os.path.basename(audio_file), False)
                        errors.append(f"文件无法读取: {audio_file}")
                        continue
                    
                    # 提取特征
                    features = self.extractor.extract_features(audio_file)
                    
                    # 检查提取是否成功
                    if "error" in features:
                        self.file_processed.emit(os.path.basename(audio_file), False)
                        errors.append(f"提取特征失败: {features['error']}")
                        error_count += 1
                        continue
                    
                    # 尝试从音频文件元数据中提取歌曲名和艺术家信息
                    try:
                        metadata = self.extractor._extract_metadata(audio_file)
                        
                        # 使用元数据中的标题作为歌曲名
                        if metadata and metadata.get("title"):
                            features["song_name"] = metadata.get("title")
                            print(f"从元数据提取歌曲名: {features['song_name']}")
                            
                            # 提取艺术家信息
                            if metadata.get("artist"):
                                features["author"] = metadata.get("artist")
                                print(f"从元数据提取艺术家: {features['author']}")
                    except Exception as e:
                        print(f"提取元数据失败: {str(e)}")
                        # 提取失败则继续使用默认方式
                    
                    # 如果元数据中没有提取到歌曲名，且启用了使用文件名选项，则使用文件名作为歌曲名
                    if not features.get("song_name") and self.use_filename:
                        # 使用文件名作为歌曲名（去除扩展名）
                        base_name = os.path.basename(audio_file)
                        song_name = os.path.splitext(base_name)[0]
                        features["song_name"] = song_name
                    
                    # 添加默认作者（如果元数据中没有提取到，且用户指定了默认作者）
                    if not features.get("author") and self.default_author:
                        features["author"] = self.default_author
                    
                    # 添加时间戳
                    features["added_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 如果启用了自动查找封面
                    if self.auto_find_cover and self.save_cover_image:
                        # 获取文件ID以供保存封面
                        file_id = self.db._generate_file_id(features["file_name"])
                        
                        # 查找封面图片
                        cover_path = self._find_cover_image(audio_file)
                        
                        # 如果找到封面，保存并添加到特征
                        if cover_path:
                            saved_cover = self.save_cover_image(cover_path, file_id)
                            if saved_cover:
                                features["cover_path"] = saved_cover
                    
                    # 添加到数据库
                    if self.db.add_feature(features):
                        self.file_processed.emit(os.path.basename(audio_file), True)
                        success_count += 1
                    else:
                        self.file_processed.emit(os.path.basename(audio_file), False)
                        errors.append(f"添加到数据库失败: {os.path.basename(audio_file)}")
                        error_count += 1
                    
                    # 更新进度
                    self.progress_updated.emit(i + 1, total_files)
                    
                except Exception as e:
                    error_msg = str(e)
                    self.file_processed.emit(os.path.basename(audio_file), False)
                    errors.append(f"{os.path.basename(audio_file)}: {error_msg}")
                    error_count += 1
                    print(f"处理文件 {audio_file} 失败: {error_msg}")
                    print(f"Stack trace: {traceback.format_exc()}")
            
            # 完成处理
            if success_count > 0:
                message = f"成功处理了 {success_count} 个文件，失败 {error_count} 个"
                self.extraction_completed.emit(True, message, success_count)
            else:
                errors_str = "\n".join(errors[:5])
                if len(errors) > 5:
                    errors_str += f"\n...共有 {len(errors)} 个错误"
                message = f"没有成功处理任何文件。错误信息:\n{errors_str}"
                self.extraction_completed.emit(False, message, 0)
            
        except Exception as e:
            error_msg = str(e)
            print(f"特征提取线程出错: {error_msg}")
            print(f"Stack trace: {traceback.format_exc()}")
            self.extraction_completed.emit(False, f"处理过程中出现未预期的错误: {error_msg}", 0)

    def _find_cover_image(self, audio_file):
        """
        根据设置的策略查找音频文件的封面图片
        
        Args:
            audio_file: 音频文件的完整路径
            
        Returns:
            找到的封面图片路径，如果没找到则返回None
        """
        try:
            file_dir = os.path.dirname(audio_file)
            file_name = os.path.basename(audio_file)
            file_base, _ = os.path.splitext(file_name)
            
            # 图片文件扩展名
            img_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
            
            # 根据不同的封面查找策略
            if self.cover_format == "同名图片":
                # 尝试查找与音频文件同名的图片
                for ext in img_exts:
                    img_path = os.path.join(file_dir, file_base + ext)
                    if os.path.exists(img_path):
                        print(f"找到同名封面: {img_path}")
                        return img_path
                        
            elif self.cover_format == "cover.jpg":
                # 尝试查找目录中的cover.jpg
                cover_names = ["cover.jpg", "cover.jpeg", "cover.png"]
                for name in cover_names:
                    img_path = os.path.join(file_dir, name)
                    if os.path.exists(img_path):
                        print(f"找到封面文件: {img_path}")
                        return img_path
                        
            elif self.cover_format == "folder.jpg":
                # 尝试查找目录中的folder.jpg
                folder_names = ["folder.jpg", "folder.jpeg", "folder.png", "front.jpg", "front.jpeg", "front.png"]
                for name in folder_names:
                    img_path = os.path.join(file_dir, name)
                    if os.path.exists(img_path):
                        print(f"找到文件夹封面: {img_path}")
                        return img_path
                        
            elif self.cover_format == "同目录所有图片":
                # 查找同目录下的任意图片文件，使用第一个
                for f in os.listdir(file_dir):
                    f_lower = f.lower()
                    if any(f_lower.endswith(ext) for ext in img_exts):
                        img_path = os.path.join(file_dir, f)
                        print(f"找到目录中的图片: {img_path}")
                        return img_path
            
            # 没找到封面
            return None
        except Exception as e:
            print(f"查找封面图片失败: {str(e)}")
            return None

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
        
        # 创建默认封面图标
        self.default_cover = self._create_default_cover()
        
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
        
        # 添加元数据迁移按钮
        migrate_button = QPushButton("更新元数据")
        migrate_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9500;
                color: #FFFFFF;
                border-radius: 5px;
                border: none;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #FFA530;
            }
            QPushButton:pressed {
                background-color: #E08500;
            }
        """)
        migrate_button.setToolTip("手动更新歌曲名和作者信息")
        migrate_button.clicked.connect(self._migrate_and_refresh)
        
        # 添加批量删除按钮
        batch_delete_button = QPushButton("批量删除")
        batch_delete_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: #FFFFFF;
                border-radius: 5px;
                border: none;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #F75C4C;
            }
            QPushButton:pressed {
                background-color: #D73C2C;
            }
        """)
        batch_delete_button.setToolTip("删除选中的特征条目")
        batch_delete_button.clicked.connect(self.batch_delete_features)
        
        filter_layout.addWidget(search_label)
        filter_layout.addWidget(self.search_input, 3)
        filter_layout.addWidget(sort_label)
        filter_layout.addWidget(self.sort_combo, 1)
        filter_layout.addWidget(add_button)
        filter_layout.addWidget(refresh_button)
        filter_layout.addWidget(migrate_button)
        filter_layout.addWidget(batch_delete_button)
        
        # 特征列表表格
        self.feature_table = QTableWidget()
        self.feature_table.setColumnCount(8)
        self.feature_table.setHorizontalHeaderLabels(["ID", "封面", "歌曲名", "文件名", "作者", "文件路径", "时长(秒)", "添加时间"])
        self.feature_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.feature_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.feature_table.verticalHeader().setVisible(False)
        self.feature_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.feature_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.feature_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 设置图标大小 - 足够大以显示封面
        self.feature_table.setIconSize(QSize(60, 60))
        
        # 设置行高以适应图标大小
        self.feature_table.verticalHeader().setDefaultSectionSize(65)
        
        # 启用多选
        self.feature_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
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
        
        # 添加文件名和作者设置选项
        options_layout = QHBoxLayout()
        
        # 使用文件名作为歌曲名
        self.use_filename_checkbox = QCheckBox("使用文件名作为歌曲名")
        self.use_filename_checkbox.setChecked(True)
        
        # 默认作者输入
        author_layout = QHBoxLayout()
        author_label = QLabel("默认作者:")
        self.default_author_input = QLineEdit()
        self.default_author_input.setPlaceholderText("未知")
        author_layout.addWidget(author_label)
        author_layout.addWidget(self.default_author_input)
        
        options_layout.addWidget(self.use_filename_checkbox)
        options_layout.addLayout(author_layout)
        options_layout.addStretch()
        
        # 添加自动查找封面选项
        cover_options_layout = QHBoxLayout()
        
        self.auto_cover_checkbox = QCheckBox("自动查找封面图片")
        self.auto_cover_checkbox.setChecked(True)
        self.auto_cover_checkbox.setToolTip("查找与音频文件同名的图片文件(.jpg/.jpeg/.png)作为封面")
        
        cover_label = QLabel("封面搜索格式:")
        self.cover_format_combo = QComboBox()
        self.cover_format_combo.addItems(["同名图片", "cover.jpg", "folder.jpg", "同目录所有图片"])
        self.cover_format_combo.setToolTip("指定自动查找封面的方式")
        
        cover_options_layout.addWidget(self.auto_cover_checkbox)
        cover_options_layout.addWidget(cover_label)
        cover_options_layout.addWidget(self.cover_format_combo)
        cover_options_layout.addStretch()
        
        # 进度条
        self.progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% (%v/%m)")
        
        self.status_label = QLabel("准备就绪，请选择文件夹")
        self.status_label.setStyleSheet("color: #666666; margin: 5px 0;")
        
        self.progress_layout.addWidget(self.progress_bar)
        self.progress_layout.addWidget(self.status_label)
        
        # 处理文件列表
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                padding: 5px;
                background-color: #FFFFFF;
            }
            QListWidget::item:alternate {
                background-color: #F9F9F9;
            }
        """)
        
        # 绑定事件
        self.select_folder_button.clicked.connect(self.select_folder)
        self.start_button.clicked.connect(self.start_extraction)
        
        # 添加所有组件到主布局
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(button_layout)
        layout.addWidget(self.folder_label)
        layout.addLayout(options_layout)
        layout.addLayout(cover_options_layout)
        layout.addLayout(self.progress_layout)
        layout.addWidget(QLabel("处理结果:"))
        layout.addWidget(self.file_list)
        
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
            # 迁移旧数据
            self._migrate_old_features()
            
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
    
    def _migrate_old_features(self):
        """迁移旧特征数据，添加歌曲名和作者信息"""
        try:
            # 确保数据库已正确加载
            if not hasattr(self.db, 'feature_index') or not self.db.feature_index:
                print("数据库未正确加载或为空，无需迁移")
                return

            # 调试输出
            print(f"当前数据库包含 {len(self.db.feature_index)} 条记录")
            first_item = next(iter(self.db.feature_index.items())) if self.db.feature_index else None
            if first_item:
                file_id, info = first_item
                print(f"示例记录: ID={file_id}, 信息={info}")
                print(f"字段: {', '.join(info.keys())}")
            
            # 检查是否有需要迁移的数据
            need_migration = False
            for file_id, info in self.db.feature_index.items():
                if "song_name" not in info or "author" not in info or not info["song_name"]:
                    need_migration = True
                    print(f"找到需要迁移的记录: {file_id}")
                    break
            
            if not need_migration:
                print("没有需要迁移的记录")
                return
                
            print("检测到旧特征数据，开始迁移...")
            
            # 统计
            total_count = len(self.db.feature_index)
            migrated_count = 0
            
            # 遍历所有特征数据
            for file_id, info in list(self.db.feature_index.items()):
                try:
                    # 检查是否需要迁移
                    if "song_name" not in info or "author" not in info or not info["song_name"]:
                        # 获取文件路径
                        file_path = info.get("file_path", "")
                        
                        if file_path and os.path.exists(file_path):
                            # 尝试从音频文件中提取元数据
                            try:
                                extractor = AudioFeatureExtractor()
                                metadata = extractor._extract_metadata(file_path)
                                
                                # 提取歌曲标题
                                song_name = ""
                                if metadata and metadata.get("title"):
                                    song_name = metadata.get("title")
                                    print(f"从元数据提取歌曲名: {song_name}")
                                
                                # 如果无法从元数据中提取，使用文件名作为备选
                                if not song_name:
                                    file_name = info.get("file_name", "")
                                    song_name = os.path.splitext(file_name)[0] if file_name else ""
                                    print(f"使用文件名作为歌曲名: {song_name}")
                                
                                # 提取艺术家
                                author = metadata.get("artist", "") if metadata else ""
                                if author:
                                    print(f"从元数据提取艺术家: {author}")
                            except Exception as e:
                                print(f"提取元数据失败: {str(e)}")
                                # 提取失败，使用文件名和默认作者
                                file_name = info.get("file_name", "")
                                song_name = os.path.splitext(file_name)[0] if file_name else ""
                                author = ""
                            
                            # 更新特征数据
                            update_info = {
                                "song_name": song_name,
                                "author": author,
                                "update_feature": True
                            }
                            
                            if self.db.update_feature_info(file_id, update_info):
                                migrated_count += 1
                                print(f"已迁移 {file_id}: {song_name} - {author}")
                                
                                # 尝试查找并添加封面
                                if file_path and os.path.exists(file_path):
                                    try:
                                        # 尝试在音频文件所在目录查找同名图片
                                        file_dir = os.path.dirname(file_path)
                                        file_base = os.path.splitext(os.path.basename(file_path))[0]
                                        
                                        # 可能的图片扩展名
                                        img_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
                                        
                                        # 尝试查找同名图片或通用封面
                                        found_cover = None
                                        
                                        # 1. 尝试同名图片
                                        for ext in img_exts:
                                            img_path = os.path.join(file_dir, file_base + ext)
                                            if os.path.exists(img_path):
                                                found_cover = img_path
                                                print(f"迁移时找到同名封面: {img_path} 用于 {file_id}")
                                                break
                                        
                                        # 2. 尝试目录下的cover.jpg等通用封面
                                        if not found_cover:
                                            cover_names = ["cover.jpg", "cover.jpeg", "cover.png", 
                                                          "folder.jpg", "folder.jpeg", "album.jpg"]
                                            for name in cover_names:
                                                img_path = os.path.join(file_dir, name)
                                                if os.path.exists(img_path):
                                                    found_cover = img_path
                                                    print(f"迁移时找到通用封面: {img_path} 用于 {file_id}")
                                                    break
                                        
                                        # 如果找到封面，保存并设置
                                        if found_cover:
                                            saved_cover = self._save_cover_image(found_cover, file_id)
                                            if saved_cover:
                                                # 更新封面路径
                                                self.db.update_feature_info(file_id, {
                                                    "cover_path": saved_cover,
                                                    "update_feature": True
                                                })
                                                print(f"迁移时已添加封面: {saved_cover} 用于 {file_id}")
                                    except Exception as e:
                                        print(f"迁移时添加封面失败: {str(e)}")
                except Exception as e:
                    print(f"迁移特征 {file_id} 失败: {str(e)}")
            
            print(f"迁移完成，共 {total_count} 条记录，成功迁移 {migrated_count} 条")
            
        except Exception as e:
            print(f"迁移特征数据失败: {str(e)}")
            traceback.print_exc()
    
    def update_feature_table(self, features):
        """更新特征表格数据"""
        try:
            # 确保表格的列数正确
            num_columns = 8  # 8列: ID, 封面, 歌曲名, 文件名, 作者, 文件路径, 时长, 添加时间
            if self.feature_table.columnCount() != num_columns:
                print(f"调整表格列数: 从 {self.feature_table.columnCount()} 到 {num_columns}")
                self.feature_table.setColumnCount(num_columns)
                self.feature_table.setHorizontalHeaderLabels(["ID", "封面", "歌曲名", "文件名", "作者", "文件路径", "时长(秒)", "添加时间"])
            
            # 清空表格
            self.feature_table.setRowCount(0)
            
            if not features:
                print("没有特征数据需要显示")
                return
                
            print(f"更新表格：共有 {len(features)} 条记录")
            
            # 设置行高以适应图标大小
            self.feature_table.verticalHeader().setDefaultSectionSize(70)
            # 设置图标大小
            self.feature_table.setIconSize(QSize(60, 60))
            
            # 添加数据
            for i, feature in enumerate(features):
                try:
                    self.feature_table.insertRow(i)
                    
                    # 设置ID（隐藏但可用于操作）
                    id_item = QTableWidgetItem(str(feature.get("id", "")))
                    id_item.setToolTip(str(feature.get("id", "")))
                    self.feature_table.setItem(i, 0, id_item)
                    
                    # 设置封面
                    cover_item = QTableWidgetItem()
                    cover_path = feature.get("cover_path", "")
                    print(f"正在处理封面: {cover_path}, 是否存在: {os.path.exists(cover_path) if cover_path else False}")
                    
                    cover_loaded = False
                    if cover_path and os.path.exists(cover_path):
                        try:
                            # 直接使用QPixmap加载图片
                            pixmap = QPixmap(cover_path)
                            if not pixmap.isNull():
                                pixmap = pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                # 设置图标
                                icon = QIcon(pixmap)
                                cover_item.setIcon(icon)
                                cover_loaded = True
                                print(f"成功加载封面: {cover_path}, 尺寸: {pixmap.width()}x{pixmap.height()}")
                            else:
                                print(f"无法加载封面为QPixmap: {cover_path}")
                        except Exception as e:
                            print(f"加载封面图片异常: {str(e)}")
                    
                    if not cover_loaded:
                        # 如果没有封面或封面不存在，尝试查找匹配的图片文件
                        try:
                            file_path = feature.get("file_path", "")
                            file_id = feature.get("id", "")
                            if file_path and os.path.exists(file_path) and file_id:
                                # 尝试在音频文件所在目录查找同名图片
                                file_dir = os.path.dirname(file_path)
                                file_base = os.path.splitext(os.path.basename(file_path))[0]
                                
                                # 可能的图片扩展名
                                img_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
                                
                                # 尝试查找同名图片或通用封面
                                found_cover = None
                                
                                # 1. 尝试同名图片
                                for ext in img_exts:
                                    img_path = os.path.join(file_dir, file_base + ext)
                                    if os.path.exists(img_path):
                                        found_cover = img_path
                                        print(f"找到同名封面: {img_path}")
                                        break
                                
                                # 2. 尝试目录下的cover.jpg等通用封面
                                if not found_cover:
                                    cover_names = ["cover.jpg", "cover.jpeg", "cover.png", 
                                                  "folder.jpg", "folder.jpeg", "album.jpg"]
                                    for name in cover_names:
                                        img_path = os.path.join(file_dir, name)
                                        if os.path.exists(img_path):
                                            found_cover = img_path
                                            print(f"找到通用封面: {img_path}")
                                            break
                                
                                # 如果找到封面，保存并设置
                                if found_cover:
                                    # 保存找到的封面
                                    saved_cover = self._save_cover_image(found_cover, file_id)
                                    if saved_cover:
                                        # 更新数据库
                                        self.db.update_feature_info(file_id, {
                                            "cover_path": saved_cover,
                                            "update_feature": True
                                        })
                                        # 设置封面
                                        try:
                                            pixmap = QPixmap(saved_cover)
                                            if not pixmap.isNull():
                                                pixmap = pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                                cover_item.setIcon(QIcon(pixmap))
                                                cover_loaded = True
                                                print(f"自动添加封面成功: {saved_cover}")
                                            else:
                                                print(f"自动添加的封面无法加载为QPixmap: {saved_cover}")
                                        except Exception as e:
                                            print(f"设置自动封面异常: {str(e)}")
                        except Exception as e:
                            print(f"自动查找封面失败: {str(e)}")
                    
                    # 如果仍然没有封面，使用默认封面
                    if not cover_loaded and self.default_cover:
                        cover_item.setIcon(QIcon(self.default_cover))
                        print("使用默认封面图标")
                    
                    self.feature_table.setItem(i, 1, cover_item)
                    
                    # 设置歌曲名
                    song_name = feature.get("song_name", "")
                    file_name = str(feature.get("file_name", ""))
                    if not song_name and file_name:
                        # 如果歌曲名为空，使用文件名（不带扩展名）作为默认歌曲名
                        song_name = os.path.splitext(file_name)[0]
                    song_name_item = QTableWidgetItem(str(song_name))
                    self.feature_table.setItem(i, 2, song_name_item)
                    
                    # 设置文件名
                    name_item = QTableWidgetItem(file_name)
                    self.feature_table.setItem(i, 3, name_item)
                    
                    # 设置作者
                    author = feature.get("author", "")
                    if not author:
                        author = "未知艺术家"
                    author_item = QTableWidgetItem(str(author))
                    self.feature_table.setItem(i, 4, author_item)
                    
                    # 设置文件路径
                    path_item = QTableWidgetItem(str(feature.get("file_path", "")))
                    path_item.setToolTip(str(feature.get("file_path", "")))
                    self.feature_table.setItem(i, 5, path_item)
                    
                    # 设置时长
                    duration = feature.get("duration", 0)
                    duration_str = f"{duration:.2f}" if isinstance(duration, (int, float)) else str(duration)
                    duration_item = QTableWidgetItem(duration_str)
                    self.feature_table.setItem(i, 6, duration_item)
                    
                    # 设置添加时间
                    time_item = QTableWidgetItem(str(feature.get("added_time", "")))
                    self.feature_table.setItem(i, 7, time_item)
                except Exception as e:
                    print(f"添加行 {i} 时出错: {str(e)}")
                    traceback.print_exc()
            
            # 设置列宽
            self.feature_table.setColumnWidth(0, 100)   # ID列
            self.feature_table.setColumnWidth(1, 70)    # 封面列
            self.feature_table.setColumnWidth(2, 200)   # 歌曲名列
            self.feature_table.setColumnWidth(3, 200)   # 文件名列
            self.feature_table.setColumnWidth(4, 150)   # 作者列
            self.feature_table.setColumnWidth(6, 100)   # 时长列
            self.feature_table.setColumnWidth(7, 180)   # 添加时间列
            
            # 设置文件路径列自动拉伸
            self.feature_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
            
        except Exception as e:
            print(f"更新特征表格失败: {str(e)}")
            traceback.print_exc()
    
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
            selected_count = len(set(item.row() for item in self.feature_table.selectedItems()))
            
            edit_action = QAction("编辑歌曲信息", self)
            edit_action.triggered.connect(self.edit_song_info)
            context_menu.addAction(edit_action)
            
            # 添加从元数据更新选项
            update_from_metadata_action = QAction("从元数据更新信息", self)
            update_from_metadata_action.triggered.connect(self.update_from_metadata)
            context_menu.addAction(update_from_metadata_action)
            
            # 添加收藏功能
            favorite_action = QAction("添加到收藏", self)
            favorite_action.triggered.connect(self.add_to_favorite)
            context_menu.addAction(favorite_action)
            
            # 如果选中多行，显示批量删除选项
            if selected_count > 1:
                delete_action = QAction(f"删除所选({selected_count}项)", self)
                delete_action.triggered.connect(self.batch_delete_features)
            else:
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
    
    def add_to_favorite(self):
        """添加选中歌曲到收藏列表"""
        selected_rows = set(item.row() for item in self.feature_table.selectedItems())
        
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择要收藏的歌曲")
            return
        
        # 获取主窗口对象
        main_window = self.parent()
        while main_window and not isinstance(main_window, QMainWindow):
            main_window = main_window.parent()
        
        if not main_window or not hasattr(main_window, 'profile_tab'):
            QMessageBox.warning(self, "错误", "无法获取主窗口实例，收藏功能无法使用")
            return
        
        # 获取ProfileTab实例
        profile_tab = main_window.profile_tab
        if not profile_tab:
            QMessageBox.warning(self, "错误", "无法获取用户档案选项卡实例，收藏功能无法使用")
            return
        
        success_count = 0
        
        # 处理每个选中的行
        for row in selected_rows:
            try:
                # 获取歌曲数据
                file_id = self.feature_table.item(row, 0).text()
                song_name = self.feature_table.item(row, 2).text()
                artist = self.feature_table.item(row, 4).text()
                file_path = self.feature_table.item(row, 5).text()
                duration = self.feature_table.item(row, 6).text()
                
                # 获取封面路径
                cover_path = ""
                feature = self.db.get_feature(file_id)
                if feature and "cover_path" in feature:
                    cover_path = feature["cover_path"]
                    
                # 准备收藏数据
                song_data = {
                    "song_id": file_id,
                    "song_name": song_name,
                    "artist": artist,
                    "file_path": file_path,
                    "duration": float(duration) if duration else 0,
                    "album": feature.get("album", "未知专辑") if feature else "未知专辑",
                    "cover_path": cover_path
                }
                
                # 添加到收藏
                if profile_tab.add_to_favorites(song_data):
                    success_count += 1
            except Exception as e:
                print(f"添加收藏失败: {str(e)}")
                traceback.print_exc()
        
        # 显示结果
        if success_count > 0:
            QMessageBox.information(
                self, 
                "收藏结果", 
                f"成功添加 {success_count} 首歌曲到收藏列表。"
            )
        else:
            QMessageBox.warning(
                self, 
                "收藏结果", 
                "未能添加任何歌曲到收藏列表。"
            )
    
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
    
    def batch_delete_features(self):
        """批量删除选中的特征"""
        selected_rows = set(item.row() for item in self.feature_table.selectedItems())
        
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择要删除的条目")
            return
            
        # 确认删除
        confirm = QMessageBox.question(
            self, 
            "确认批量删除", 
            f"确定要删除选中的 {len(selected_rows)} 个特征吗？\n这将从特征库中永久删除这些数据，此操作无法撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # 显示进度对话框
            progress_dialog = QDialog(self)
            progress_dialog.setWindowTitle("正在删除")
            progress_dialog.setFixedSize(400, 100)
            progress_layout = QVBoxLayout(progress_dialog)
            
            progress_label = QLabel(f"正在删除 {len(selected_rows)} 个特征...")
            progress_bar = QProgressBar()
            progress_bar.setRange(0, len(selected_rows))
            progress_bar.setValue(0)
            
            progress_layout.addWidget(progress_label)
            progress_layout.addWidget(progress_bar)
            
            progress_dialog.show()
            QApplication.processEvents()
            
            # 收集要删除的ID
            ids_to_delete = [self.feature_table.item(row, 0).text() for row in selected_rows]
            
            # 执行删除
            delete_count = 0
            for i, file_id in enumerate(ids_to_delete):
                try:
                    if self.db.remove_feature(file_id):
                        delete_count += 1
                except Exception as e:
                    print(f"删除特征 {file_id} 失败: {str(e)}")
                
                # 更新进度
                progress_bar.setValue(i + 1)
                progress_label.setText(f"正在删除: {i+1}/{len(selected_rows)}")
                QApplication.processEvents()
            
            # 关闭进度对话框
            progress_dialog.close()
            
            # 刷新列表
            self.refresh_feature_list()
            
            # 显示结果
            QMessageBox.information(
                self, 
                "批量删除结果", 
                f"成功删除 {delete_count} 个特征，失败 {len(ids_to_delete) - delete_count} 个。"
            )
    
    def play_selected_feature(self):
        """播放选中的特征对应的音频文件"""
        selected_items = self.feature_table.selectedItems()
        if not selected_items:
            return
            
        # 获取选中行的文件路径
        row = selected_items[0].row()
        file_path = self.feature_table.item(row, 5).text()
        file_id = self.feature_table.item(row, 0).text()
        
        # 处理可能的相对路径
        if not os.path.isabs(file_path):
            # 计算绝对路径 - 相对于项目根目录
            current_file = os.path.abspath(__file__)
            # feature_library_tab.py -> tabs -> src -> desktop_app -> frontend -> music_recognition_system -> 项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))))
            # 将路径分隔符标准化
            normalized_file_path = file_path.replace('/', os.path.sep)
            absolute_path = os.path.join(project_root, normalized_file_path)
            print(f"原始路径: {file_path}")
            print(f"转换为绝对路径: {absolute_path}")
            file_path = absolute_path
        
        original_path = file_path
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            
            # 尝试修复路径 - 检查是否包含临时文件路径
            if "temp" in file_path and "db_add_" in file_path:
                print("检测到临时文件路径，尝试查找真实文件...")
                
                # 尝试在Music目录中查找同名文件
                try:
                    music_dir = os.path.join(project_root, "Music")
                    
                    if os.path.exists(music_dir):
                        # 获取原始特征信息以获取文件名线索
                        feature_data = self.db.get_feature(file_id)
                        file_name = feature_data.get("file_name", "") if feature_data else ""
                        
                        # 在Music目录中查找匹配文件
                        for root, _, files in os.walk(music_dir):
                            for file in files:
                                if file == file_name or file.endswith(os.path.splitext(file_name)[1]):
                                    # 找到可能的匹配文件
                                    potential_path = os.path.join(root, file)
                                    print(f"找到可能的替代文件: {potential_path}")
                                    file_path = potential_path
                                    
                                    # 如果找到有效文件，更新数据库中的路径
                                    if os.path.exists(file_path):
                                        print(f"使用替代文件路径: {file_path}")
                                        # 计算相对路径用于更新数据库
                                        relative_path = os.path.relpath(file_path, project_root).replace("\\", "/")
                                        print(f"更新数据库中的路径: {relative_path}")
                                        self.db.update_feature_info(file_id, {
                                            "file_path": relative_path,
                                            "update_feature": True
                                        })
                                        break
                            if os.path.exists(file_path):
                                break
                except Exception as search_error:
                    print(f"在Music目录中查找文件失败: {str(search_error)}")
            
            # 最终检查文件是否存在
            if not os.path.exists(file_path):
                error_msg = f"文件路径不存在或无效。\n\n原始路径: {original_path}"
                if original_path != file_path:
                    error_msg += f"\n\n尝试修复后路径: {file_path}"
                    
                QMessageBox.warning(
                    self, 
                    "无法播放", 
                    error_msg
                )
                return
        
        # 尝试首先使用歌曲播放选项卡播放
        try:
            # 获取主窗口
            main_window = self.window()
            
            # 检查是否实现了获取歌曲播放选项卡的方法
            if hasattr(main_window, 'get_music_player_tab'):
                # 获取歌曲播放选项卡
                music_player_tab = main_window.get_music_player_tab()
                
                # 切换到歌曲播放选项卡
                main_window.tab_widget.setCurrentWidget(music_player_tab)
                
                # 获取歌曲名称和艺术家
                song_name = None
                artist_name = None
                
                for i in range(self.feature_table.columnCount()):
                    header_text = self.feature_table.horizontalHeaderItem(i).text()
                    if header_text == "歌曲名":
                        song_name = self.feature_table.item(row, i).text()
                    elif header_text == "作者":
                        artist_name = self.feature_table.item(row, i).text()
                
                # 添加到播放列表并播放
                music_player_tab.play_music(file_path, song_name, artist_name)
                
                # 显示成功信息
                QMessageBox.information(
                    self,
                    "播放中",
                    f"歌曲已添加到播放列表并开始播放: {os.path.basename(file_path)}"
                )
                return
        except Exception as e:
            print(f"使用歌曲播放选项卡播放失败: {str(e)}")
            print(f"堆栈信息: {traceback.format_exc()}")
            # 如果失败，回退到使用系统默认程序播放
            
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
        """查看选中特征的详细信息"""
        selected_items = self.feature_table.selectedItems()
        if not selected_items:
            return
            
        # 获取选中行的特征ID
        row = selected_items[0].row()
        file_id = self.feature_table.item(row, 0).text()
        
        # 获取完整特征数据
        feature_data = self.db.get_feature(file_id)
        
        if not feature_data:
            QMessageBox.warning(
                self, 
                "未找到详情", 
                "无法获取所选特征的详细信息。"
            )
            return
            
        # 创建详情对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("特征详情")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout(dialog)
        
        # 分隔器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：封面和基本信息
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 显示封面
        cover_label = QLabel()
        cover_label.setFixedSize(200, 200)
        cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover_label.setStyleSheet("border: 1px solid #CCCCCC; background-color: #F5F5F5;")
        
        # 加载封面
        cover_path = feature_data.get("cover_path", "")
        if cover_path and os.path.exists(cover_path):
            try:
                # 使用QImage先加载验证
                image = QImage(cover_path)
                if not image.isNull():
                    # 转换为QPixmap并设置
                    pixmap = QPixmap.fromImage(image)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(190, 190, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        cover_label.setPixmap(pixmap)
                        print(f"详情窗口: 成功加载封面: {cover_path}, 尺寸: {pixmap.width()}x{pixmap.height()}")
                    else:
                        cover_label.setText("图片转换失败")
                        print(f"详情窗口: 图片无法转换为QPixmap: {cover_path}")
                else:
                    cover_label.setText("无法加载图片")
                    print(f"详情窗口: 图片无法加载为QImage: {cover_path}")
            except Exception as e:
                cover_label.setText("加载图片出错")
                print(f"详情窗口: 加载封面出错: {str(e)}")
        else:
            cover_label.setText("无封面")
            if cover_path:
                print(f"详情窗口: 封面路径存在但文件不存在: {cover_path}")
            else:
                print("详情窗口: 无封面路径")
        
        # 基本信息
        basic_info = QLabel(
            f"<b>文件名:</b> {feature_data.get('file_name', '')}<br>"
            f"<b>歌曲名:</b> {feature_data.get('song_name', '')}<br>"
            f"<b>作者:</b> {feature_data.get('author', '')}<br>"
            f"<b>时长:</b> {feature_data.get('duration', '0')} 秒<br>"
            f"<b>添加时间:</b> {feature_data.get('added_time', '')}<br>"
        )
        basic_info.setWordWrap(True)
        
        left_layout.addWidget(cover_label, 0, Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(basic_info)
        left_layout.addStretch()
        
        # 右侧：技术特征信息
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 特征信息
        details_label = QLabel("技术特征:")
        details_label.setStyleSheet("font-weight: bold;")
        
        # 创建一个表格来显示特征数据
        details_table = QTableWidget()
        details_table.setColumnCount(2)
        details_table.setHorizontalHeaderLabels(["特征", "值"])
        details_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        details_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # 添加技术特征数据
        tech_features = [
            ("梅尔频谱均值", "mel_mean"),
            ("梅尔频谱标准差", "mel_std"),
            ("MFCC均值", "mfcc_mean"),
            ("MFCC标准差", "mfcc_std"),
            ("色度特征均值", "chroma_mean"),
            ("谱质心均值", "spectral_centroid_mean"),
            ("谱质心标准差", "spectral_centroid_std"),
            ("过零率均值", "zero_crossing_rate_mean"),
            ("节奏/速度", "tempo")
        ]
        
        row = 0
        for label, key in tech_features:
            if key in feature_data:
                value = feature_data[key]
                
                # 对于数组类型，显示长度而不是具体内容
                if isinstance(value, list):
                    value_str = f"[数组，长度: {len(value)}]"
                else:
                    value_str = str(value)
                    
                details_table.insertRow(row)
                details_table.setItem(row, 0, QTableWidgetItem(label))
                details_table.setItem(row, 1, QTableWidgetItem(value_str))
                row += 1
        
        right_layout.addWidget(details_label)
        right_layout.addWidget(details_table)
        
        # 添加到分隔器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([200, 300])  # 设置初始大小比例
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.setFixedWidth(100)
        close_button.clicked.connect(dialog.accept)
        
        # 添加到布局
        layout.addWidget(splitter)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)
        
        # 显示对话框
        dialog.exec()
    
    def add_single_file(self):
        """添加单个音频文件"""
        # 选择音频文件
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择音频文件",
            "",
            "音频文件 (*.mp3 *.wav *.flac *.ogg *.m4a)"
        )
        
        if not file_path:
            return
            
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("添加到特征库")
        dialog.setMinimumWidth(500)
        
        # 主布局
        layout = QVBoxLayout(dialog)
        
        # 表单布局
        form_layout = QFormLayout()
        
        # 文件信息
        file_name = os.path.basename(file_path)
        file_label = QLabel(f"文件: {file_name}")
        file_label.setStyleSheet("font-weight: bold;")
        
        # 获取音频文件的元数据
        try:
            extractor = AudioFeatureExtractor()
            metadata = extractor._extract_metadata(file_path)
            default_title = metadata.get("title", "")
            default_artist = metadata.get("artist", "")
        except:
            default_title = ""
            default_artist = ""
        
        # 歌曲名输入
        song_name_input = QLineEdit()
        song_name_input.setText(default_title)
        song_name_input.setPlaceholderText("请输入歌曲名称")
        form_layout.addRow("歌曲名称:", song_name_input)
        
        # 作者输入
        author_input = QLineEdit()
        author_input.setText(default_artist)
        author_input.setPlaceholderText("请输入作者/艺术家")
        form_layout.addRow("作者/艺术家:", author_input)
        
        # 封面选择
        cover_layout = QHBoxLayout()
        cover_path_input = QLineEdit()
        cover_path_input.setReadOnly(True)
        cover_path_input.setPlaceholderText("可选")
        
        browse_button = QPushButton("浏览...")
        browse_button.setFixedWidth(80)
        
        # 封面预览
        cover_preview = QLabel()
        cover_preview.setFixedSize(150, 150)
        cover_preview.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ddd;")
        cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover_preview.setText("无封面")
        
        def browse_cover():
            """浏览封面图片"""
            cover_file, _ = QFileDialog.getOpenFileName(
                dialog,
                "选择封面图片",
                "",
                "图片文件 (*.jpg *.jpeg *.png *.gif *.bmp)"
            )
            
            if cover_file:
                cover_path_input.setText(cover_file)
                
                # 显示预览
                pixmap = QPixmap(cover_file)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio)
                    cover_preview.setPixmap(pixmap)
                    cover_preview.setToolTip(cover_file)
                else:
                    cover_preview.setText("无法加载封面")
        
        browse_button.clicked.connect(browse_cover)
        
        cover_layout.addWidget(cover_path_input)
        cover_layout.addWidget(browse_button)
        
        form_layout.addRow("封面图片:", cover_layout)
        form_layout.addRow("预览:", cover_preview)
        
        # 进度条
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setVisible(False)
        
        # 处理按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        # 添加到布局
        layout.addWidget(file_label)
        layout.addLayout(form_layout)
        layout.addWidget(progress_bar)
        layout.addWidget(button_box)
        
        def process_file():
            """处理单个文件"""
            progress_bar.setVisible(True)
            button_box.setEnabled(False)
            
            # 更新UI
            QApplication.processEvents()
            
            try:
                # 提取特征
                extractor = AudioFeatureExtractor()
                feature_data = extractor.extract_features(file_path)
                
                if not feature_data:
                    QMessageBox.warning(
                        dialog,
                        "提取失败",
                        f"无法从文件 {file_name} 提取特征"
                    )
                    return False
                
                # 添加用户输入的信息
                feature_data["song_name"] = song_name_input.text()
                feature_data["author"] = author_input.text()
                
                # 处理封面
                cover_path = cover_path_input.text()
                if cover_path and os.path.exists(cover_path):
                    # 生成文件ID
                    file_id = hashlib.md5(file_name.encode('utf-8')).hexdigest()
                    
                    # 保存封面图片到特征库
                    cover_save_path = self._save_cover_image(cover_path, file_id)
                    if cover_save_path:
                        feature_data["cover_path"] = cover_save_path
                
                # 添加到数据库
                self.db.add_feature(feature_data)
                
                # 更新UI
                self.refresh_feature_list()
                
                return True
                
            except Exception as e:
                print(f"处理文件失败: {str(e)}")
                traceback.print_exc()
                QMessageBox.critical(
                    dialog,
                    "处理出错",
                    f"处理文件时发生错误: {str(e)}"
                )
                return False
            finally:
                progress_bar.setVisible(False)
                button_box.setEnabled(True)
        
        # 显示对话框并处理结果
        if dialog.exec() == QDialog.DialogCode.Accepted:
            success = process_file()
            
            if success:
                QMessageBox.information(
                    self,
                    "添加成功",
                    f"文件 {file_name} 已成功添加到特征库"
                )
    
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
        auto_find_cover = self.auto_cover_checkbox.isChecked()
        cover_format = self.cover_format_combo.currentText()
        
        self.extraction_thread = FeatureExtractionThread(
            self.selected_folder, 
            self.database_path,
            use_filename,
            default_author,
            auto_find_cover,
            cover_format,
            self._save_cover_image  # 传递封面保存方法
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
        """编辑歌曲信息"""
        selected_items = self.feature_table.selectedItems()
        if not selected_items:
            return
            
        # 获取所选行
        selected_row = selected_items[0].row()
        
        # 获取文件ID
        file_id = self.feature_table.item(selected_row, 0).text()
        print(f"编辑歌曲信息，文件ID: {file_id}")
        
        # 获取当前信息
        current_info = {
            "file_name": self.feature_table.item(selected_row, 2).text(),
            "song_name": self.feature_table.item(selected_row, 3).text() if self.feature_table.item(selected_row, 3) else "",
            "author": self.feature_table.item(selected_row, 4).text() if self.feature_table.item(selected_row, 4) else "",
            "file_path": self.feature_table.item(selected_row, 5).text() if self.feature_table.item(selected_row, 5) else ""
        }
        
        # 获取封面路径
        feature_data = self.db.get_feature(file_id)
        if feature_data:
            current_info["cover_path"] = feature_data.get("cover_path", "")
            print(f"当前封面路径: {current_info['cover_path']}")
            
        # 创建编辑对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑歌曲信息")
        dialog.setMinimumWidth(500)
        
        # 设置布局
        layout = QFormLayout(dialog)
        
        # 歌曲名输入框
        song_name_input = QLineEdit(dialog)
        song_name_input.setText(current_info.get("song_name", ""))
        song_name_input.setPlaceholderText("请输入歌曲名称")
        layout.addRow("歌曲名称:", song_name_input)
        
        # 作者输入框
        author_input = QLineEdit(dialog)
        author_input.setText(current_info.get("author", ""))
        author_input.setPlaceholderText("请输入作者/艺术家")
        layout.addRow("作者/艺术家:", author_input)
        
        # 文件名（只读）
        file_name_label = QLineEdit(dialog)
        file_name_label.setText(current_info.get("file_name", ""))
        file_name_label.setReadOnly(True)
        layout.addRow("文件名:", file_name_label)
        
        # 文件路径（只读）
        file_path_label = QLineEdit(dialog)
        file_path_label.setText(current_info.get("file_path", ""))
        file_path_label.setReadOnly(True)
        layout.addRow("文件路径:", file_path_label)
        
        # 封面图片选择
        cover_layout = QHBoxLayout()
        cover_label = QLabel("封面图片:")
        cover_path_input = QLineEdit(dialog)
        cover_path_input.setText(current_info.get("cover_path", ""))
        cover_path_input.setReadOnly(True)
        
        browse_cover_btn = QPushButton("浏览...", dialog)
        clear_cover_btn = QPushButton("清除", dialog)
        cover_layout.addWidget(cover_path_input)
        cover_layout.addWidget(browse_cover_btn)
        cover_layout.addWidget(clear_cover_btn)
        layout.addRow(cover_label, cover_layout)
        
        # 封面预览
        cover_preview = QLabel(dialog)
        cover_preview.setFixedSize(150, 150)
        cover_preview.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ddd;")
        cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 如果有封面则显示
        if current_info.get("cover_path", "") and os.path.exists(current_info["cover_path"]):
            try:
                # 使用QImage先加载
                image = QImage(current_info["cover_path"])
                if not image.isNull():
                    # 转换为QPixmap
                    pixmap = QPixmap.fromImage(image)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        cover_preview.setPixmap(pixmap)
                        print(f"编辑对话框: 成功加载封面预览: {current_info['cover_path']}, 尺寸: {pixmap.width()}x{pixmap.height()}")
                    else:
                        cover_preview.setText("无法转换图片")
                        print(f"编辑对话框: 图片无法转换为QPixmap: {current_info['cover_path']}")
                else:
                    cover_preview.setText("无法加载封面")
                    print(f"编辑对话框: 无法加载封面预览为QImage: {current_info['cover_path']}")
            except Exception as e:
                cover_preview.setText("加载错误")
                print(f"编辑对话框: 加载封面预览出错: {str(e)}")
        else:
            cover_preview.setText("无封面")
            if current_info.get("cover_path", ""):
                print(f"编辑对话框: 封面路径存在但文件不存在: {current_info['cover_path']}")
            else:
                print("编辑对话框: 无封面路径")
        
        layout.addRow("", cover_preview)
        
        # 为浏览按钮添加功能
        def browse_cover():
            """浏览封面图片"""
            file_path, _ = QFileDialog.getOpenFileName(
                dialog,
                "选择封面图片",
                "",
                "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif)"
            )
            
            if file_path:
                cover_path_input.setText(file_path)
                print(f"编辑对话框: 选择新封面: {file_path}")
                
                # 更新预览
                try:
                    # 使用QImage先加载
                    image = QImage(file_path)
                    if not image.isNull():
                        # 转换为QPixmap
                        pixmap = QPixmap.fromImage(image)
                        if not pixmap.isNull():
                            pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            cover_preview.setPixmap(pixmap)
                            print(f"编辑对话框: 成功加载新封面预览: {file_path}, 尺寸: {pixmap.width()}x{pixmap.height()}")
                        else:
                            cover_preview.setText("无法转换图片")
                            print(f"编辑对话框: 无法将新封面转换为QPixmap: {file_path}")
                    else:
                        cover_preview.setText("无法加载封面")
                        print(f"编辑对话框: 无法加载新封面预览为QImage: {file_path}")
                except Exception as e:
                    cover_preview.setText("加载错误")
                    print(f"编辑对话框: 加载新封面预览出错: {str(e)}")
        
        # 为清除按钮添加功能
        def clear_cover():
            """清除封面图片"""
            cover_path_input.setText("")
            cover_preview.clear()
            cover_preview.setText("无封面")
            print("清除封面图片")
        
        browse_cover_btn.clicked.connect(browse_cover)
        clear_cover_btn.clicked.connect(clear_cover)
        
        # 确定和取消按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            dialog
        )
        layout.addWidget(button_box)
        
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        # 显示对话框并处理结果
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 获取编辑后的信息
            updated_info = {
                "song_name": song_name_input.text(),
                "author": author_input.text(),
                "update_feature": True
            }
            print(f"更新歌曲信息: 歌曲名={updated_info['song_name']}, 作者={updated_info['author']}")
            
            # 处理封面
            new_cover_path = cover_path_input.text()
            if new_cover_path and os.path.exists(new_cover_path):
                if new_cover_path != current_info.get("cover_path", ""):
                    # 保存新封面
                    saved_cover_path = self._save_cover_image(new_cover_path, file_id)
                    if saved_cover_path:
                        updated_info["cover_path"] = saved_cover_path
                        print(f"更新封面路径: {saved_cover_path}")
            elif not new_cover_path and current_info.get("cover_path", ""):
                # 清除封面
                updated_info["cover_path"] = ""
                print("清除封面路径")
            
            # 更新数据库
            try:
                success = self.db.update_feature_info(file_id, updated_info)
                
                if success:
                    # 刷新表格
                    self.refresh_feature_list()
                    QMessageBox.information(self, "更新成功", "歌曲信息已更新")
                    print("成功更新歌曲信息")
                else:
                    QMessageBox.warning(self, "更新失败", "无法更新歌曲信息")
                    print("更新歌曲信息失败")
            except Exception as e:
                QMessageBox.critical(self, "更新错误", f"更新过程中发生错误: {str(e)}")
                print(f"更新歌曲信息异常: {str(e)}")
                traceback.print_exc()

    def _get_cover_directory(self):
        """获取封面图片存储目录"""
        cover_dir = os.path.join(self.database_path, "covers")
        os.makedirs(cover_dir, exist_ok=True)
        print(f"封面存储目录: {cover_dir}, 是否存在: {os.path.exists(cover_dir)}")
        return cover_dir

    def _save_cover_image(self, image_path, file_id):
        """保存封面图片
        
        Args:
            image_path: 源图片路径
            file_id: 文件ID，用于生成封面文件名
            
        Returns:
            成功返回保存后的图片路径，失败返回空字符串
        """
        try:
            if not image_path or not os.path.exists(image_path):
                print(f"源图片不存在: {image_path}")
                return ""
            
            # 统一使用PNG格式
            cover_dir = self._get_cover_directory()
            cover_filename = f"cover_{file_id}.png"
            cover_path = os.path.join(cover_dir, cover_filename)
            
            print(f"正在保存封面: {image_path} -> {cover_path}")
            
            # 加载并处理图片
            image = QImage(image_path)
            if not image.isNull():
                print(f"成功加载源图片: {image_path}, 尺寸: {image.width()}x{image.height()}")
                
                # 调整大小以保持一致性
                max_size = 300  # 限制最大尺寸
                if image.width() > max_size or image.height() > max_size:
                    image = image.scaled(max_size, max_size, 
                                        Qt.AspectRatioMode.KeepAspectRatio, 
                                        Qt.TransformationMode.SmoothTransformation)
                    print(f"调整图片尺寸为: {image.width()}x{image.height()}")
                
                # 强制保存为PNG格式
                success = image.save(cover_path, "PNG")
                print(f"保存图片结果: {success}")
                
                # 验证保存结果
                if success and os.path.exists(cover_path):
                    test_image = QImage(cover_path)
                    if not test_image.isNull():
                        print(f"封面保存成功并验证: {cover_path}")
                        return cover_path
                    else:
                        print(f"保存的图片无法验证，尝试备用方案")
            
            # 备用方案：直接复制
            print(f"使用复制方式保存封面")
            shutil.copy2(image_path, cover_path)
            print(f"完成复制: {image_path} -> {cover_path}")
            return cover_path if os.path.exists(cover_path) else ""
                
        except Exception as e:
            print(f"保存封面图片失败: {str(e)}")
            traceback.print_exc()
            return ""

    def _migrate_and_refresh(self):
        """手动触发元数据迁移并刷新"""
        try:
            QMessageBox.information(self, "更新元数据", "开始更新歌曲名和作者信息，请稍候...")
            self._migrate_old_features()
            self.refresh_feature_list()
            QMessageBox.information(self, "更新完成", "歌曲信息已更新")
        except Exception as e:
            QMessageBox.warning(self, "更新失败", f"更新元数据失败: {str(e)}")
            print(f"手动迁移失败: {str(e)}")
            traceback.print_exc()

    def _create_default_cover(self):
        """创建默认封面图标"""
        try:
            # 创建40x40的图像
            image = QImage(40, 40, QImage.Format.Format_ARGB32)
            image.fill(QColor(200, 200, 200))  # 设置背景色为浅灰色
            
            # 创建绘图对象
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 设置笔刷
            painter.setPen(QPen(QColor(100, 100, 100), 2))
            
            # 绘制音符图标
            painter.drawEllipse(10, 20, 8, 8)  # 音符的头部
            painter.drawLine(18, 24, 18, 10)   # 音符的柄
            painter.drawLine(18, 10, 25, 8)    # 音符的旗帜
            
            painter.drawEllipse(23, 23, 7, 7)  # 第二个音符的头部
            
            # 完成绘制
            painter.end()
            
            # 转换为QPixmap
            pixmap = QPixmap.fromImage(image)
            return pixmap
        except Exception as e:
            print(f"创建默认封面失败: {str(e)}")
            return None

    def update_from_metadata(self):
        """从选中音频文件的元数据中更新歌曲信息"""
        selected_rows = set(item.row() for item in self.feature_table.selectedItems())
        
        if not selected_rows:
            return
            
        # 确认操作
        confirm = QMessageBox.question(
            self, 
            "确认更新", 
            f"确定要从元数据重新提取所选 {len(selected_rows)} 个文件的歌曲信息吗？\n这将覆盖当前的歌曲名和艺术家信息。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.No:
            return
        
        # 显示进度对话框
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("正在更新")
        progress_dialog.setFixedSize(400, 100)
        progress_layout = QVBoxLayout(progress_dialog)
        
        progress_label = QLabel(f"正在更新 {len(selected_rows)} 个文件的信息...")
        progress_bar = QProgressBar()
        progress_bar.setRange(0, len(selected_rows))
        progress_bar.setValue(0)
        
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(progress_bar)
        
        progress_dialog.show()
        QApplication.processEvents()
        
        # 收集要更新的文件ID
        success_count = 0
        failed_count = 0
        
        for i, row in enumerate(selected_rows):
            try:
                # 获取文件ID和路径
                file_id = self.feature_table.item(row, 0).text()
                file_path = self.feature_table.item(row, 5).text()
                
                # 检查文件是否存在
                if file_path and os.path.exists(file_path):
                    # 提取元数据
                    extractor = AudioFeatureExtractor()
                    metadata = extractor._extract_metadata(file_path)
                    
                    # 获取歌曲名和艺术家信息
                    song_name = ""
                    author = ""
                    
                    # 从元数据中提取歌曲名
                    if metadata and metadata.get("title"):
                        song_name = metadata.get("title")
                        print(f"从元数据提取歌曲名: {song_name}")
                    
                    # 如果元数据中没有歌曲名，保留原有的或使用文件名
                    if not song_name:
                        current_song_name = self.feature_table.item(row, 2).text()
                        if current_song_name:
                            song_name = current_song_name
                        else:
                            file_name = os.path.basename(file_path)
                            song_name = os.path.splitext(file_name)[0]
                        print(f"使用已有歌曲名或文件名: {song_name}")
                    
                    # 从元数据中提取艺术家
                    if metadata and metadata.get("artist"):
                        author = metadata.get("artist")
                        print(f"从元数据提取艺术家: {author}")
                    
                    # 更新数据库
                    update_info = {
                        "song_name": song_name,
                        "author": author,
                        "update_feature": True
                    }
                    
                    if self.db.update_feature_info(file_id, update_info):
                        success_count += 1
                        print(f"已更新 {file_id}: {song_name} - {author}")
                    else:
                        failed_count += 1
                        print(f"更新 {file_id} 失败")
                else:
                    failed_count += 1
                    print(f"文件不存在: {file_path}")
            except Exception as e:
                failed_count += 1
                print(f"更新文件信息失败: {str(e)}")
                traceback.print_exc()
            
            # 更新进度
            progress_bar.setValue(i + 1)
            progress_label.setText(f"正在更新: {i+1}/{len(selected_rows)}")
            QApplication.processEvents()
        
        # 关闭进度对话框
        progress_dialog.close()
        
        # 刷新表格
        self.refresh_feature_list()
        
        # 显示结果
        if success_count > 0:
            QMessageBox.information(
                self, 
                "更新完成", 
                f"成功更新了 {success_count} 个文件的信息，失败 {failed_count} 个。"
            )
        else:
            QMessageBox.warning(
                self, 
                "更新失败", 
                f"没有成功更新任何文件，失败 {failed_count} 个。"
            )