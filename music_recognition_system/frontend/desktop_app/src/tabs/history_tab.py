from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class HistoryTab(QWidget):
    """历史记录选项卡 - 已移除"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 创建一个标签显示功能已移除的消息
        message_label = QLabel("历史记录功能已移除")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        message_label.setStyleSheet("color: #888888;")
        
        # 添加说明标签
        description_label = QLabel("此功能在当前版本中不可用")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setFont(QFont("Arial", 12))
        description_label.setStyleSheet("color: #AAAAAA; margin-top: 10px;")
        
        # 添加到布局
        layout.addStretch(1)
        layout.addWidget(message_label)
        layout.addWidget(description_label)
        layout.addStretch(1)
        
        self.setLayout(layout) 