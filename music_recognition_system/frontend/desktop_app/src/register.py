import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QFrame, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon

class RegisterWidget(QWidget):
    # 定义注册成功的信号
    register_successful = pyqtSignal(str, str, str)  # 参数为用户名、密码和昵称
    # 定义返回登录界面的信号
    back_to_login = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("音乐识别系统 - 注册")
        self.setFixedSize(400, 720)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                font-family: 'Microsoft YaHei', Arial;
            }
            QLabel {
                color: #333333;
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
            QPushButton#back_button {
                background-color: #FFFFFF;
                color: #1DB954;
                border: 1px solid #1DB954;
            }
            QPushButton#back_button:hover {
                background-color: #F5F5F5;
            }
            QPushButton#back_button:pressed {
                background-color: #E0E0E0;
            }
            QCheckBox {
                font-size: 13px;
                color: #555555;
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
            #info_label {
                font-size: 12px;
                color: #666666;
                margin-top: 2px;
                margin-bottom: 8px;
            }
        """)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(5)  # 减小默认间距
        
        # 标题
        title_label = QLabel("注册新账号")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 添加一些空间
        main_layout.addSpacing(15)
        
        # 用户名输入框
        username_label = QLabel("用户名")
        self.username_input = QLineEdit()
        self.username_input.setFixedHeight(40)
        self.username_input.setPlaceholderText("请输入用户名（4-16个字符）")
        main_layout.addWidget(username_label)
        main_layout.addWidget(self.username_input)
        
        # 用户名提示
        username_info = QLabel("用户名只能包含字母、数字和下划线")
        username_info.setObjectName("info_label")
        main_layout.addWidget(username_info)
        main_layout.addSpacing(3) # 添加额外空间
        
        # 昵称输入框
        nickname_label = QLabel("昵称")
        self.nickname_input = QLineEdit()
        self.nickname_input.setFixedHeight(40)
        self.nickname_input.setPlaceholderText("请输入您的昵称（显示给其他用户）")
        main_layout.addWidget(nickname_label)
        main_layout.addWidget(self.nickname_input)
        main_layout.addSpacing(3) # 添加额外空间
        
        # 密码输入框
        password_label = QLabel("密码")
        self.password_input = QLineEdit()
        self.password_input.setFixedHeight(40)
        self.password_input.setPlaceholderText("请输入密码（8-20个字符）")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        main_layout.addWidget(password_label)
        main_layout.addWidget(self.password_input)
        
        # 密码提示
        password_info = QLabel("密码应包含字母、数字和特殊字符")
        password_info.setObjectName("info_label")
        main_layout.addWidget(password_info)
        main_layout.addSpacing(3) # 添加额外空间
        
        # 确认密码输入框
        confirm_password_label = QLabel("确认密码")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setFixedHeight(40)
        self.confirm_password_input.setPlaceholderText("请再次输入密码")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        main_layout.addWidget(confirm_password_label)
        main_layout.addWidget(self.confirm_password_input)
        main_layout.addSpacing(5) # 添加额外空间
        
        # 邮箱输入框（可选）
        email_label = QLabel("邮箱（可选）")
        self.email_input = QLineEdit()
        self.email_input.setFixedHeight(40)
        self.email_input.setPlaceholderText("请输入您的邮箱地址")
        main_layout.addWidget(email_label)
        main_layout.addWidget(self.email_input)
        main_layout.addSpacing(5) # 添加额外空间
        
        # 用户协议复选框
        self.agreement_checkbox = QCheckBox("我已阅读并同意《用户协议》和《隐私政策》")
        main_layout.addWidget(self.agreement_checkbox)
        
        # 错误消息标签
        self.error_label = QLabel("")
        self.error_label.setObjectName("error_label")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.error_label)
        
        # 添加一些空间
        main_layout.addSpacing(10)
        
        # 注册按钮
        self.register_button = QPushButton("注册")
        self.register_button.setFixedHeight(40)
        self.register_button.clicked.connect(self.handle_register)
        main_layout.addWidget(self.register_button)
        
        # 返回登录按钮
        self.back_button = QPushButton("返回登录")
        self.back_button.setFixedHeight(40)
        self.back_button.setObjectName("back_button")
        self.back_button.clicked.connect(self.handle_back)
        main_layout.addWidget(self.back_button)
        
        # 添加弹性空间
        main_layout.addStretch(1)
        
        # 版权信息
        copyright_label = QLabel("© 2025 音乐识别系统")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setStyleSheet("color: #999999; font-size: 12px;")
        main_layout.addWidget(copyright_label)
        
        # 设置初始焦点到用户名输入框
        self.username_input.setFocus()
        
    def handle_register(self):
        """处理注册逻辑"""
        # 获取用户输入
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()
        email = self.email_input.text().strip()
        nickname = self.nickname_input.text().strip()
        
        # 验证用户名
        if not username:
            self.error_label.setText("请输入用户名")
            return
            
        if len(username) < 4 or len(username) > 16:
            self.error_label.setText("用户名长度应为4-16个字符")
            return
            
        # 简单验证用户名格式（只允许字母、数字和下划线）
        if not all(c.isalnum() or c == '_' for c in username):
            self.error_label.setText("用户名只能包含字母、数字和下划线")
            return
            
        # 验证密码
        if not password:
            self.error_label.setText("请输入密码")
            return
            
        if len(password) < 8 or len(password) > 20:
            self.error_label.setText("密码长度应为8-20个字符")
            return
            
        # 验证密码复杂度（简单版）
        has_letter = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if not (has_letter and has_digit):
            self.error_label.setText("密码必须同时包含字母和数字")
            return
            
        # 验证两次密码是否一致
        if password != confirm_password:
            self.error_label.setText("两次输入的密码不一致")
            return
            
        # 验证邮箱格式（简单验证）
        if email and '@' not in email:
            self.error_label.setText("邮箱格式不正确")
            return
            
        # 验证昵称
        if not nickname:
            # 如果昵称为空，使用用户名作为默认昵称
            nickname = username
        elif len(nickname) > 20:
            self.error_label.setText("昵称长度不能超过20个字符")
            return
            
        # 验证是否同意用户协议
        if not self.agreement_checkbox.isChecked():
            self.error_label.setText("请阅读并同意用户协议")
            return
            
        # 注册成功，发送信号并显示成功消息
        self.error_label.setText("")
        
        # 显示注册成功消息
        QMessageBox.information(
            self,
            "注册成功",
            f"恭喜您，账号 {username} 注册成功！\n您现在可以使用新账号登录系统。",
            QMessageBox.StandardButton.Ok
        )
        
        # 发射注册成功信号，将用户名、密码和昵称传递给登录界面
        self.register_successful.emit(username, password, nickname)
        
        # 返回登录界面
        self.handle_back()
    
    def handle_back(self):
        """返回登录界面"""
        # 清空输入框
        self.username_input.clear()
        self.password_input.clear()
        self.confirm_password_input.clear()
        self.email_input.clear()
        self.nickname_input.clear()
        self.agreement_checkbox.setChecked(False)
        self.error_label.setText("")
        
        # 发射返回登录界面信号
        self.back_to_login.emit()

# 如果直接运行这个文件，则显示注册窗口用于测试
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    register_widget = RegisterWidget()
    register_widget.show()
    sys.exit(app.exec()) 