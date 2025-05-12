import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel
from PyQt6.QtCore import Qt

# 导入选项卡
from tabs.recognition_tab import RecognitionTab
from tabs.library_tab import LibraryTab
from tabs.feature_library_tab import FeatureLibraryTab
from tabs.music_player_tab import MusicPlayerTab

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
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # 初始化各选项卡实例并保存引用
        self.recognition_tab = RecognitionTab(self)
        self.feature_library_tab = FeatureLibraryTab()
        self.library_tab = LibraryTab()
        self.profile_tab = ProfileTab()
        self.music_player_tab = MusicPlayerTab(self)
        
        # 添加选项卡
        self.tab_widget.addTab(self.recognition_tab, "识别")
        self.tab_widget.addTab(self.feature_library_tab, "音乐库")
        self.tab_widget.addTab(self.library_tab, "在线音乐")
        self.tab_widget.addTab(self.music_player_tab, "歌曲播放")
        self.tab_widget.addTab(self.profile_tab, "我的")
        
        main_layout.addWidget(self.tab_widget)
    
    def switch_to_tab(self, tab_index):
        """切换到指定的选项卡"""
        if 0 <= tab_index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(tab_index)
    
    def get_library_tab(self):
        """获取音乐库选项卡实例"""
        return self.library_tab
        
    def get_music_player_tab(self):
        """获取歌曲播放选项卡实例"""
        return self.music_player_tab

def main():
    app = QApplication(sys.argv)
    window = MusicRecognitionApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 