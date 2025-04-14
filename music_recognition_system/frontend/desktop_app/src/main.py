import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel
from PyQt6.QtCore import Qt

# 导入选项卡
from tabs.recognition_tab import RecognitionTab
from tabs.history_tab import HistoryTab

class LibraryTab(QWidget):
    """音乐库选项卡"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        label = QLabel("音乐库 - 开发中")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class SettingsTab(QWidget):
    """设置选项卡"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        label = QLabel("设置 - 开发中")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class ProfileTab(QWidget):
    """用户档案选项卡"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        label = QLabel("用户档案 - 开发中")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class MusicRecognitionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("音乐识别系统")
        self.setMinimumSize(800, 600)
        
        # 设置应用整体样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QTabWidget::pane {
                border: none;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #FFFFFF;
                padding: 10px 20px;
                margin-right: 5px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 14px;
                color: #333333; /* 确保常态下文字可见 */
            }
            QTabBar::tab:selected {
                color: #1DB954;
                border-bottom: 2px solid #1DB954;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                color: #333333;
                border-bottom: 2px solid #E0E0E0;
            }
        """)
        
        # 主部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建选项卡部件
        tab_widget = QTabWidget()
        tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # 添加选项卡
        tab_widget.addTab(RecognitionTab(), "识别")
        tab_widget.addTab(HistoryTab(), "历史记录")
        tab_widget.addTab(LibraryTab(), "音乐库")
        tab_widget.addTab(SettingsTab(), "设置")
        tab_widget.addTab(ProfileTab(), "我的")
        
        main_layout.addWidget(tab_widget)

def main():
    app = QApplication(sys.argv)
    window = MusicRecognitionApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 