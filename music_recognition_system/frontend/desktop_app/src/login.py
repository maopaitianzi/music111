import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QFrame, QCheckBox,
                             QStackedWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon
import os
import json

# 导入注册界面
from register import RegisterWidget

class LoginWidget(QWidget):
    # 定义登录成功的信号
    login_successful = pyqtSignal(str)  # 传递当前登录用户的昵称
    # 定义注册按钮点击的信号
    register_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # 创建注册界面
        self.register_widget = RegisterWidget()
        self.register_widget.back_to_login.connect(self.show_login_page)
        self.register_widget.register_successful.connect(self.auto_fill_credentials)
        self.register_widget.hide()
        
        # 加载用户凭证
        self.valid_credentials = self.load_users()
        
        # 加载记住的登录信息
        self.load_remembered_credential()
        
    def setup_ui(self):
        self.setWindowTitle("音乐识别系统 - 登录")
        self.setFixedSize(400, 480)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                font-family: 'Microsoft YaHei', Arial;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: #F5F5F5;
                font-size: 14px;
                color: #000000;
                min-height: 20px;
            }
            QPushButton {
                background-color: #1DB954;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #1ED760;
            }
            QPushButton:pressed {
                background-color: #1AA34A;
            }
            QPushButton#register_button {
                background-color: #FFFFFF;
                color: #1DB954;
                border: 1px solid #1DB954;
            }
            QPushButton#register_button:hover {
                background-color: #F5F5F5;
            }
            QPushButton#register_button:pressed {
                background-color: #E0E0E0;
            }
            QCheckBox {
                color: #555555;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                border: 1px solid #CCCCCC;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                background-color: #1DB954;
                border-color: #1DB954;
            }
            #title_label {
                font-size: 24px;
                font-weight: bold;
                color: #1DB954;
            }
            #error_label {
                color: #E74C3C;
                font-size: 12px;
                margin-top: 5px;
            }
        """)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(5)  # 减小默认间距
        
        # 标题
        title_label = QLabel("音乐识别系统")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 添加一些空间
        main_layout.addSpacing(15)
        
        # 用户名输入框
        username_label = QLabel("用户名")
        self.username_input = QLineEdit()
        self.username_input.setFixedHeight(40)
        self.username_input.setPlaceholderText("请输入用户名")
        main_layout.addWidget(username_label)
        main_layout.addWidget(self.username_input)
        main_layout.addSpacing(8)  # 添加额外空间
        
        # 密码输入框
        password_label = QLabel("密码")
        self.password_input = QLineEdit()
        self.password_input.setFixedHeight(40)
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        # 回车键触发登录
        self.password_input.returnPressed.connect(self.handle_login)
        main_layout.addWidget(password_label)
        main_layout.addWidget(self.password_input)
        main_layout.addSpacing(5)  # 添加额外空间
        
        # 记住密码选项
        checkbox_layout = QHBoxLayout()
        self.remember_checkbox = QCheckBox("记住密码")
        checkbox_layout.addWidget(self.remember_checkbox)
        
        # 添加记住用户名选项
        self.remember_username_checkbox = QCheckBox("记住用户名")
        checkbox_layout.addWidget(self.remember_username_checkbox)
        
        checkbox_layout.addStretch(1)
        main_layout.addLayout(checkbox_layout)
        
        # 错误消息标签
        self.error_label = QLabel("")
        self.error_label.setObjectName("error_label")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.error_label)
        
        # 添加一些空间
        main_layout.addSpacing(10)
        
        # 登录按钮
        self.login_button = QPushButton("登录")
        self.login_button.setFixedHeight(40)
        self.login_button.clicked.connect(self.handle_login)
        main_layout.addWidget(self.login_button)
        
        # 添加一些空间
        main_layout.addSpacing(8)
        
        # 注册按钮
        self.register_button = QPushButton("注册")
        self.register_button.setFixedHeight(40)
        self.register_button.setObjectName("register_button")
        self.register_button.clicked.connect(self.handle_register)
        main_layout.addWidget(self.register_button)
        
        # 添加弹性空间
        main_layout.addStretch(1)
        
        # 版权信息
        copyright_label = QLabel("© 2025 音乐识别系统")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setStyleSheet("color: #999999; font-size: 12px;")
        main_layout.addWidget(copyright_label)
        
        # 设置初始焦点到用户名输入框
        self.username_input.setFocus()
        
    def handle_login(self):
        """处理登录逻辑"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        # 验证输入不为空
        if not username or not password:
            self.error_label.setText("用户名和密码不能为空")
            return
            
        # 验证用户名和密码
        if username in self.valid_credentials and self.valid_credentials[username]["password"] == password:
            self.error_label.setText("")
            
            # 根据复选框状态处理记住用户名和密码
            remember_password = self.remember_checkbox.isChecked()
            remember_username = self.remember_username_checkbox.isChecked()
            
            if remember_password or remember_username:
                self.save_remembered_credential(username, password if remember_password else "", remember_username)
            else:
                self.clear_remembered_credential()
            
            # 登录成功，发射信号
            self.login_successful.emit(self.valid_credentials[username]["nickname"])
        else:
            self.error_label.setText("用户名或密码错误")
    
    def show_register_page(self):
        """显示注册界面"""
        # 清空登录界面的错误信息
        self.error_label.setText("")
        
        # 显示注册界面，隐藏登录界面
        screen_geometry = self.screen().geometry()
        x = (screen_geometry.width() - self.register_widget.width()) // 2
        y = (screen_geometry.height() - self.register_widget.height()) // 2
        self.register_widget.move(x, y)
        
        self.register_widget.show()
        self.hide()
    
    def show_login_page(self):
        """显示登录界面"""
        # 隐藏注册界面，显示登录界面
        self.register_widget.hide()
        self.show()
    
    def auto_fill_credentials(self, username, password, nickname):
        """自动填充注册成功的用户名和密码"""
        # 将新注册的用户添加到有效凭证中
        self.valid_credentials[username] = {"password": password, "nickname": nickname}
        
        # 保存用户信息到文件
        self.save_users()
        
        # 自动填充到登录表单
        self.username_input.setText(username)
        self.password_input.setText(password)
        
        # 设置为记住密码
        self.remember_checkbox.setChecked(True)
        
    def save_users(self):
        """保存用户凭证到文件"""
        # 获取用户数据文件路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        user_data_dir = os.path.join(current_dir, "..", "data")
        user_file = os.path.join(user_data_dir, "users.json")
        
        # 确保目录存在
        os.makedirs(user_data_dir, exist_ok=True)
        
        # 保存用户数据
        try:
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(self.valid_credentials, f, ensure_ascii=False, indent=2)
            print(f"用户数据已保存到: {user_file}")
        except Exception as e:
            print(f"保存用户数据失败: {str(e)}")

    def handle_register(self):
        """处理注册逻辑"""
        # 发射注册按钮点击信号
        print("注册按钮被点击")
        self.register_clicked.emit()
        
        # 显示注册界面，隐藏登录界面
        screen_geometry = self.screen().geometry()
        x = (screen_geometry.width() - self.register_widget.width()) // 2
        y = (screen_geometry.height() - self.register_widget.height()) // 2
        self.register_widget.move(x, y)
        
        self.register_widget.show()
        self.hide()

    def load_users(self):
        """从文件加载用户凭证"""
        # 获取用户数据文件路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        user_data_dir = os.path.join(current_dir, "..", "data")
        user_file = os.path.join(user_data_dir, "users.json")
        
        # 确保目录存在
        os.makedirs(user_data_dir, exist_ok=True)
        
        # 如果文件不存在，创建默认用户
        if not os.path.exists(user_file):
            default_users = {
                "admin": {"password": "admin123", "nickname": "管理员"},
                "user": {"password": "user123", "nickname": "普通用户"}
            }
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(default_users, f, ensure_ascii=False, indent=2)
            return default_users
        
        # 读取用户数据
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                # 兼容旧版格式 (扁平字典) 和新版格式 (带nickname的嵌套字典)
                users = json.load(f)
                formatted_users = {}
                for username, data in users.items():
                    if isinstance(data, str):  # 旧格式: "username": "password"
                        formatted_users[username] = {"password": data, "nickname": username}
                    else:  # 新格式: "username": {"password": "xxx", "nickname": "xxx"}
                        formatted_users[username] = data
                return formatted_users
        except Exception as e:
            print(f"读取用户数据失败: {str(e)}")
            # 创建默认用户
            default_users = {
                "admin": {"password": "admin123", "nickname": "管理员"},
                "user": {"password": "user123", "nickname": "普通用户"}
            }
            return default_users

    def save_remembered_credential(self, username, password, remember_username=True):
        """保存记住的用户名和密码"""
        try:
            # 获取保存记住用户文件的路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            user_data_dir = os.path.join(current_dir, "..", "data")
            remember_file = os.path.join(user_data_dir, "remembered_user.json")
            
            # 确保目录存在
            os.makedirs(user_data_dir, exist_ok=True)
            
            # 保存凭证数据
            remembered_data = {
                "username": username if remember_username else "",
                "password": password,
                "remember_username": remember_username
            }
            
            with open(remember_file, 'w', encoding='utf-8') as f:
                json.dump(remembered_data, f, ensure_ascii=False, indent=2)
                
            print(f"已保存记住的用户凭证: 用户名={bool(remember_username)}, 密码={bool(password)}")
        except Exception as e:
            print(f"保存记住的用户凭证失败: {str(e)}")
    
    def load_remembered_credential(self):
        """加载记住的用户名和密码"""
        try:
            # 获取记住用户文件的路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            user_data_dir = os.path.join(current_dir, "..", "data")
            remember_file = os.path.join(user_data_dir, "remembered_user.json")
            
            # 如果文件存在，则加载记住的凭证
            if os.path.exists(remember_file):
                with open(remember_file, 'r', encoding='utf-8') as f:
                    remembered_data = json.load(f)
                    
                username = remembered_data.get("username", "")
                password = remembered_data.get("password", "")
                remember_username = remembered_data.get("remember_username", True)
                
                # 自动填充用户名和密码
                if username:
                    self.username_input.setText(username)
                    self.remember_username_checkbox.setChecked(True)
                    
                if password:
                    self.password_input.setText(password)
                    self.remember_checkbox.setChecked(True)
                    
                print(f"已加载记住的用户凭证: 用户名={bool(username)}, 密码={bool(password)}")
        except Exception as e:
            print(f"加载记住的用户凭证失败: {str(e)}")
    
    def clear_remembered_credential(self):
        """清除记住的用户名和密码"""
        try:
            # 获取记住用户文件的路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            user_data_dir = os.path.join(current_dir, "..", "data")
            remember_file = os.path.join(user_data_dir, "remembered_user.json")
            
            # 如果文件存在，则删除它
            if os.path.exists(remember_file):
                os.remove(remember_file)
                print("已清除记住的用户凭证")
        except Exception as e:
            print(f"清除记住的用户凭证失败: {str(e)}")

# 如果直接运行这个文件，则显示登录窗口用于测试
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    login_widget = LoginWidget()
    login_widget.show()
    sys.exit(app.exec()) 