from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView

class LibraryTab(QWidget):
    """音乐库选项卡 - 接入外部音乐网站"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 创建标题标签
        title_label = QLabel("音乐库 - 在线服务")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1DB954; margin-bottom: 10px;")
        
        # 创建Web视图组件
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("https://music.cpp-prog.com/"))
        
        # 添加到布局
        layout.addWidget(title_label)
        layout.addWidget(self.web_view)
        
        self.setLayout(layout) 