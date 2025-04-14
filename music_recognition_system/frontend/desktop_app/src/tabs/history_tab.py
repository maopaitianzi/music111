from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt

class HistoryTab(QWidget):
    """历史记录选项卡"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 顶部标题
        title = QLabel("历史记录")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px 0;")
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索历史记录...")
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
        
        search_layout.addWidget(self.search_box)
        
        # 历史记录列表
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 10px;
                background-color: white;
                padding: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #F0F0F0;
                padding: 10px;
            }
            QListWidget::item:selected {
                background-color: #F0F0F0;
                color: black;
            }
            QListWidget::item:hover {
                background-color: #F9F9F9;
            }
        """)
        
        # 添加模拟数据
        self.add_sample_history()
        
        # 添加到主布局
        layout.addWidget(title)
        layout.addLayout(search_layout)
        layout.addWidget(self.history_list)
        
        self.setLayout(layout)
    
    def add_sample_history(self):
        # 添加一些样本历史记录数据
        sample_data = [
            {"song": "告白气球", "artist": "周杰伦", "time": "2023-06-15 14:30"},
            {"song": "七里香", "artist": "周杰伦", "time": "2023-06-15 13:45"},
            {"song": "Blank Space", "artist": "Taylor Swift", "time": "2023-06-14 20:12"},
            {"song": "Shape of You", "artist": "Ed Sheeran", "time": "2023-06-14 18:30"},
            {"song": "Bad Guy", "artist": "Billie Eilish", "time": "2023-06-13 21:05"},
            {"song": "Uptown Funk", "artist": "Mark Ronson ft. Bruno Mars", "time": "2023-06-12 17:22"},
            {"song": "Blinding Lights", "artist": "The Weeknd", "time": "2023-06-11 19:48"},
            {"song": "Stay", "artist": "The Kid LAROI, Justin Bieber", "time": "2023-06-10 16:33"}
        ]
        
        for item in sample_data:
            list_item = QListWidgetItem()
            list_item.setText(f"{item['song']} - {item['artist']}\n{item['time']}")
            self.history_list.addItem(list_item) 