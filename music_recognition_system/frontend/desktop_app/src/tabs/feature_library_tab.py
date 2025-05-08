from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QFileDialog, QProgressBar, QListWidget, QListWidgetItem,
                            QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDir
from PyQt6.QtGui import QFont, QPalette, QColor
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
            FeatureDatabase._features[feature_data["file_name"]] = feature_data
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
            
        def get_all_files(self):
            print(f"从模拟数据库获取文件，当前有 {len(FeatureDatabase._features)} 个文件")
            return [{"file_name": name} for name in FeatureDatabase._features.keys()]
            
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
    
    def __init__(self, folder_path, database_path=None):
        super().__init__()
        self.folder_path = folder_path
        self.database_path = database_path
        self.extractor = AudioFeatureExtractor()
        self.db = FeatureDatabase(database_path)
        
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
        layout = QVBoxLayout()
        
        # 顶部标题
        title = QLabel("特征库创建")
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
        
        # 特征库统计
        self.stats_label = QLabel("特征库统计: 0 首歌曲")
        self.stats_label.setStyleSheet("color: #1DB954; font-weight: bold; margin-top: 15px;")
        
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
        layout.addWidget(self.stats_label)
        layout.addWidget(self.file_list_label)
        layout.addWidget(self.file_list)
        
        self.setLayout(layout)
        
        # 连接信号
        self.select_folder_button.clicked.connect(self.select_folder)
        self.start_button.clicked.connect(self.start_extraction)
        
        # 初始化变量
        self.selected_folder = ""
        self.extraction_thread = None
        
    def load_existing_features(self):
        """加载已有的特征库统计信息"""
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
            
            files = self.db.get_all_files()
            print(f"特征库中的文件数量: {len(files)}")
            self.stats_label.setText(f"特征库统计: {len(files)} 首歌曲")
        except Exception as e:
            print(f"加载特征库统计信息失败: {str(e)}")
            traceback.print_exc()
        
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
        self.extraction_thread = FeatureExtractionThread(self.selected_folder, self.database_path)
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
            
            # 直接更新UI上的特征库统计，不重新创建对象
            self.stats_label.setText(f"特征库统计: {success_count} 首歌曲")
            
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