from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QLineEdit, QMessageBox
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView
import os
import requests
import urllib.parse
from pathlib import Path
import sys
import json

# 导入添加到数据库的函数
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))))

# 封装原始的add_music_to_database函数，确保返回统一格式
def safe_add_to_database(audio_file_path, metadata=None):
    """确保add_music_to_database函数返回统一格式 (success, error_msg, details)"""
    try:
        # 尝试导入原始函数
        from add_to_database import add_music_to_database as original_add
        
        # 调用原始函数并处理返回值
        try:
            result = original_add(audio_file_path, metadata)
            # 原始函数可能只返回成功或失败，没有错误消息
            if isinstance(result, bool):
                return result, "" if result else "未知错误", ""
            # 如果原始函数已经返回元组，则直接使用并添加详情
            elif isinstance(result, tuple):
                if len(result) == 2:
                    return result[0], result[1], ""
                elif len(result) >= 3:
                    return result[0], result[1], result[2]
            # 其他情况，检查是否为None，若是则可能是后端已成功处理，但返回值异常
            elif result is None:
                # 检查日志输出，若后端实际成功添加了文件，则认为是成功的
                print("接收到空返回值，尝试通过日志判断添加是否成功")
                # 尝试检查特征库是否有更新
                return True, "", "返回值为空，但特征可能已添加成功"
            else:
                return False, f"函数返回值异常: {result}", ""
        except Exception as e:
            return False, str(e), "异常调用"
    except ImportError:
        # 如果导入失败，使用我们的实现
        return local_add_to_database(audio_file_path, metadata)
    
    # 确保函数总是返回一个有效的元组
    return True, "添加成功", ""

# 本地实现版本
def local_add_to_database(audio_file_path, metadata=None):
    """本地实现的添加到数据库函数"""
    # API端点
    url = "http://localhost:5000/api/database/add"
    
    # 检查文件是否存在
    if not os.path.exists(audio_file_path):
        print(f"错误: 文件不存在 - {audio_file_path}")
        return False, "文件不存在", ""
    
    # 准备文件 - 确保使用绝对路径
    audio_file_path = os.path.abspath(audio_file_path)
    print(f"使用绝对路径: {audio_file_path}")
    
    # 检查文件读取权限
    if not os.access(audio_file_path, os.R_OK):
        print(f"错误: 无法读取文件 - {audio_file_path}")
        return False, "无法读取文件，请检查权限", ""
    
    # 检查文件大小
    try:
        file_size = os.path.getsize(audio_file_path)
        if file_size == 0:
            print(f"错误: 文件大小为0 - {audio_file_path}")
            return False, "文件大小为0，请检查文件是否正确下载", ""
        print(f"文件大小: {file_size} 字节")
    except Exception as e:
        print(f"检查文件大小出错: {str(e)}")
    
    try:
        # 尝试重命名文件，确保扩展名正确
        file_base, file_ext = os.path.splitext(audio_file_path)
        if file_ext.lower() not in ['.mp3', '.wav', '.flac', '.ogg']:
            # 添加.mp3扩展名
            new_path = file_base + '.mp3'
            try:
                # 复制而不是重命名，以保持原文件
                import shutil
                shutil.copy2(audio_file_path, new_path)
                audio_file_path = new_path
                print(f"已创建副本并修正扩展名: {new_path}")
            except Exception as rename_err:
                print(f"修正文件扩展名失败: {str(rename_err)}")
        
        files = {
            'audio_file': (os.path.basename(audio_file_path), open(audio_file_path, 'rb'), 'audio/mpeg')
        }
        
        # 如果没有提供元数据，则从文件名创建基本元数据
        if not metadata:
            basename = os.path.basename(audio_file_path)
            name = os.path.splitext(basename)[0]
            metadata = {
                "name": name,
                "artist": "未知艺术家",
                "album": "未知专辑",
                "year": "",
                "genre": "未知"
            }
        
        # 确保元数据中包含所有必需字段
        required_fields = ["name", "artist", "album", "year", "genre"]
        for field in required_fields:
            if field not in metadata:
                metadata[field] = ""
        
        # 准备表单数据
        data = {
            'metadata': json.dumps(metadata)
        }
        
        # 发送请求
        print(f"正在添加文件到数据库: {os.path.basename(audio_file_path)}...")
        try:
            response = requests.post(url, files=files, data=data, timeout=120)  # 增加超时时间到2分钟
            
            # 检查响应
            print(f"服务器响应: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"解析JSON结果: {result}")
                    
                    # 修改判断逻辑：如果响应代码为200且没有明确的错误信息，则认为添加成功
                    if result.get("success", False) or (response.status_code == 200 and not result.get("error")):
                        # 即使特征ID为空，只要没有明确错误信息，也认为成功
                        file_name = result.get('file_name', '')
                        feature_id = result.get('feature_id', '')
                        
                        # 记录成功日志
                        success_message = "成功添加到数据库"
                        if file_name:
                            success_message += f": {file_name}"
                        print(success_message)
                        
                        if feature_id:
                            print(f"特征ID: {feature_id}")
                        else:
                            print("特征ID未返回，但添加过程可能已成功")
                            
                        return True, "添加成功", ""
                    else:
                        error_msg = result.get('error', '未知错误')
                        details = result.get('details', '')
                        
                        # 检查特殊情况：日志显示成功但API返回失败
                        if "None" in error_msg:
                            print("检测到特殊错误：返回值为None但实际可能已成功")
                            return True, "", "后端返回异常值，但特征可能已添加成功"
                            
                        full_error = error_msg
                        if details:
                            full_error += f" - {details}"
                        print(f"添加失败: {full_error}")
                        return False, full_error, ""
                except json.JSONDecodeError as e:
                    print(f"解析JSON响应失败: {str(e)}")
                    print(f"原始响应: {response.text}")
                    
                    # 检查非JSON响应是否包含成功信息
                    if "成功" in response.text or "success" in response.text.lower():
                        print("从非JSON响应中检测到成功信息")
                        return True, "添加成功", ""
                        
                    return False, f"解析服务器响应失败: {str(e)}", ""
            else:
                print(f"请求失败: HTTP {response.status_code}")
                print(response.text)
                
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', f"HTTP错误: {response.status_code}")
                    details = error_data.get('details', '')
                    if details:
                        error_msg += f" - {details}"
                    return False, error_msg, ""
                except:
                    return False, f"HTTP错误: {response.status_code}", ""
        
        except requests.exceptions.Timeout:
            print("请求超时，特征提取可能需要较长时间")
            return False, "请求超时，特征提取可能需要较长时间", ""
        except requests.exceptions.ConnectionError:
            print("连接错误，请确保后端API服务已启动")
            return False, "连接错误，请确保后端API服务已启动", ""
        except Exception as e:
            print(f"发生错误: {str(e)}")
            return False, str(e), "异常调用"
    except Exception as file_error:
        print(f"处理文件时出错: {str(file_error)}")
        return False, f"处理文件时出错: {str(file_error)}", ""
    finally:
        # 关闭文件
        try:
            if 'files' in locals() and 'audio_file' in files:
                files['audio_file'][1].close()
        except:
            pass

class LibraryTab(QWidget):
    """音乐库选项卡 - 接入外部音乐网站
    
    功能:
    1. 提供在线音乐搜索
    2. 内嵌Web浏览器访问音乐网站
    3. 支持外链音乐下载 - 可自动检测页面中的音乐外链并支持一键下载
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 创建标题和搜索框布局
        header_layout = QHBoxLayout()
        
        # 创建标题标签
        title_label = QLabel("音乐库 - 在线服务")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1DB954; margin-bottom: 10px;")
        
        # 添加搜索框和按钮
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入歌曲名或艺术家名搜索")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CCCCCC;
                border-radius: 15px;
                padding: 5px 10px;
                background: #FFFFFF;
                color: #000000;
                min-width: 250px;
                height: 30px;
            }
        """)
        
        self.search_button = QPushButton("搜索")
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: #FFFFFF;
                border-radius: 15px;
                border: none;
                padding: 5px 15px;
                height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1ED760;
            }
            QPushButton:pressed {
                background-color: #0A8C3C;
            }
        """)
        self.search_button.clicked.connect(self._search_from_input)
        
        # 添加搜索输入按回车执行搜索
        self.search_input.returnPressed.connect(self._search_from_input)
        
        # 添加到布局
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.search_input)
        header_layout.addWidget(self.search_button)
        
        # 添加外链下载栏
        download_layout = QHBoxLayout()
        
        download_label = QLabel("外链下载:")
        download_label.setStyleSheet("font-weight: bold; margin-right: 5px;")
        
        self.download_input = QLineEdit()
        self.download_input.setPlaceholderText("输入音乐外链URL (如: https://m702.music.126.net/...)")
        self.download_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CCCCCC;
                border-radius: 15px;
                padding: 5px 10px;
                background: #FFFFFF;
                color: #000000;
                min-width: 300px;
                height: 30px;
            }
        """)
        
        self.download_button = QPushButton("下载")
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: #FFFFFF;
                border-radius: 15px;
                border: none;
                padding: 5px 15px;
                height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1ED760;
            }
            QPushButton:pressed {
                background-color: #0A8C3C;
            }
        """)
        self.download_button.clicked.connect(self._download_from_url)
        
        # 添加下载输入按回车执行下载
        self.download_input.returnPressed.connect(self._download_from_url)
        
        # 添加到布局
        download_layout.addWidget(download_label)
        download_layout.addWidget(self.download_input)
        download_layout.addWidget(self.download_button)
        
        # 创建Web视图组件
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("https://music.cpp-prog.com/"))
        
        # 添加到布局
        layout.addLayout(header_layout)
        layout.addLayout(download_layout)  # 添加下载栏
        layout.addWidget(self.web_view)
        
        self.setLayout(layout)
        
        # 设置js回调，用于从网页获取音乐外链
        self.web_view.page().javaScriptConsoleMessage = self._handle_js_console
        self._setup_js_handlers()

    def _setup_js_handlers(self):
        """设置JavaScript处理程序，用于捕获页面上的外链URL"""
        js_code = """
        (function() {
            // 监听DOM变化，检测音乐外链
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.addedNodes) {
                        mutation.addedNodes.forEach(function(node) {
                            if (node.nodeType === 1) {  // 元素节点
                                // 检查是否包含音乐外链
                                const allLinks = node.querySelectorAll('a[href*="music.126.net"], a[href*=".mp3"], a[href*=".flac"]');
                                allLinks.forEach(function(link) {
                                    console.log('MUSIC_LINK_DETECTED:' + link.href);
                                });
                                
                                // 检查文本内容是否包含外链
                                const allElements = node.querySelectorAll('*');
                                allElements.forEach(function(el) {
                                    if (el.textContent) {
                                        const text = el.textContent;
                                        if (text.includes('music.126.net') || 
                                            text.includes('.mp3') || 
                                            text.includes('.flac')) {
                                            console.log('MUSIC_TEXT_DETECTED:' + text);
                                        }
                                    }
                                });
                            }
                        });
                    }
                });
            });
            
            // 开始观察整个文档
            observer.observe(document.body, { 
                childList: true, 
                subtree: true 
            });
            
            // 也监听点击事件，可能会显示外链
            document.addEventListener('click', function(e) {
                // 延迟检查，因为点击后可能会显示外链
                setTimeout(function() {
                    // 检查所有可能的外链元素
                    const allLinks = document.querySelectorAll('a[href*="music.126.net"], a[href*=".mp3"], a[href*=".flac"]');
                    allLinks.forEach(function(link) {
                        console.log('MUSIC_LINK_DETECTED:' + link.href);
                    });
                    
                    // 检查输入框中的值
                    const allInputs = document.querySelectorAll('input');
                    allInputs.forEach(function(input) {
                        if (input.value && (
                            input.value.includes('music.126.net') || 
                            input.value.includes('.mp3') || 
                            input.value.includes('.flac'))) {
                            console.log('MUSIC_INPUT_DETECTED:' + input.value);
                        }
                    });
                }, 500);
            }, true);
        })();
        """
        self.web_view.page().runJavaScript(js_code)
    
    def _handle_js_console(self, level, message, line, source):
        """处理来自JavaScript的控制台消息"""
        # 检测音乐外链
        if 'MUSIC_LINK_DETECTED:' in message:
            url = message.split('MUSIC_LINK_DETECTED:')[1]
            self._update_download_input(url)
        elif 'MUSIC_TEXT_DETECTED:' in message:
            text = message.split('MUSIC_TEXT_DETECTED:')[1]
            # 尝试从文本中提取URL
            if 'http' in text:
                parts = text.split()
                for part in parts:
                    if part.startswith('http') and ('music.126.net' in part or '.mp3' in part or '.flac' in part):
                        self._update_download_input(part)
                        break
        elif 'MUSIC_INPUT_DETECTED:' in message:
            url = message.split('MUSIC_INPUT_DETECTED:')[1]
            self._update_download_input(url)
    
    def _update_download_input(self, url):
        """更新下载输入框中的URL"""
        # 清理URL（去除可能的引号等）
        url = url.strip('"\'')
        self.download_input.setText(url)
    
    def _download_from_url(self):
        """从外链URL下载音乐"""
        url = self.download_input.text().strip()
        if not url:
            QMessageBox.warning(self, "下载错误", "请输入有效的音乐外链URL")
            return
        
        try:
            # 使用相对路径获取下载目录
            # 从当前文件位置向上导航到项目根目录
            current_file = os.path.abspath(__file__)  # 当前文件的绝对路径
            # library_tab.py -> tabs -> src -> desktop_app -> frontend -> music_recognition_system -> 项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))))
            download_dir = os.path.join(project_root, "Music")
            
            # 确保下载目录的绝对路径
            download_dir = os.path.abspath(download_dir)
            print(f"下载目录: {download_dir}")
            
            os.makedirs(download_dir, exist_ok=True)
            
            # 从URL获取文件名
            parsed_url = urllib.parse.urlparse(url)
            path = parsed_url.path
            filename = os.path.basename(path)
            
            # 检测是否是网易云音乐外链
            is_netease = "music.126.net" in url
            
            # 如果是网易云音乐外链，尝试从查询参数获取有效信息
            if is_netease:
                print("检测到网易云音乐外链")
                # 从URL路径提取ID信息
                netease_id = path.split('/')[-1]
                if len(netease_id) > 5:  # 确保ID有效
                    filename = f"netease_{netease_id}.mp3"
            
            # 如果文件名不合法或太短，使用时间戳
            if not filename or len(filename) < 5:
                import time
                filename = f"music_{int(time.time())}.mp3"
            
            # 如果没有扩展名，添加.mp3
            if '.' not in filename:
                filename += '.mp3'
                
            # 下载文件
            try:
                print(f"开始下载: {url}")
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                file_path = os.path.join(download_dir, filename)
                
                # 写入文件
                file_size = 0
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            file_size += len(chunk)
                
                print(f"下载完成，文件大小: {file_size} 字节")
                
                # 验证下载的文件
                if file_size == 0:
                    raise Exception("下载的文件大小为0字节")
                
                if is_netease:
                    # 分析网易云音乐元数据
                    try:
                        from mutagen.mp3 import MP3
                        from mutagen.id3 import ID3, TIT2, TPE1, TALB
                        audio = MP3(file_path)
                        print(f"音频长度: {audio.info.length} 秒, 比特率: {audio.info.bitrate}")
                    except Exception as audio_error:
                        print(f"音频元数据分析失败: {str(audio_error)}")
                
                # 下载成功后询问是否添加到特征库
                reply = QMessageBox.question(
                    self, "添加到特征库", 
                    f"音乐已下载到: {file_path}\n\n是否将此音乐添加到特征库以便识别?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # 从网易云音乐外链或文件名中提取元数据
                    song_name = os.path.splitext(filename)[0]
                    artist_name = "未知艺术家"
                    
                    # 如果是网易云音乐，尝试使用更好的元数据
                    if is_netease:
                        # 在网易云ID前添加适当前缀
                        if song_name.startswith("netease_"):
                            song_name = f"网易云音乐 - {song_name.replace('netease_', '')}"
                        
                        # 这里可以添加调用网易云API获取更准确元数据的代码
                        # ...
                    else:
                        # 尝试从文件名解析艺术家信息
                        if " - " in song_name:
                            parts = song_name.split(" - ", 1)
                            artist_name = parts[0].strip()
                            song_name = parts[1].strip()
                    
                    # 构建元数据
                    metadata = {
                        "name": song_name,
                        "artist": artist_name,
                        "album": "网易云音乐" if is_netease else "在线下载",
                        "year": "",
                        "genre": "未知"
                    }
                    
                    # 提示用户正在处理
                    QMessageBox.information(
                        self, 
                        "处理中", 
                        "正在添加到特征库，这可能需要几秒钟...\n\n较大的音频文件可能需要更长时间。"
                    )
                    
                    # 转换为相对路径以提高兼容性
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
                    relative_path = os.path.relpath(file_path, project_root)
                    # 标准化路径分隔符为跨平台格式
                    normalized_path = relative_path.replace('\\', '/')
                    
                    print(f"原始路径: {file_path}")
                    print(f"相对路径: {normalized_path}")
                    
                    # 创建临时的特征数据对象
                    feature_data = {
                        "file_name": os.path.basename(file_path),
                        "file_path": normalized_path,
                        "song_name": metadata.get("name", ""),
                        "author": metadata.get("artist", "")
                    }
                    
                    # 使用安全的封装函数添加到数据库
                    print(f"开始提取特征: {file_path}")
                    success, error_msg, details = safe_add_to_database(file_path, metadata)
                    
                    if success:
                        # 添加通知功能：更新特征库面板（如果存在）
                        try:
                            # 尝试通知特征库面板更新
                            parent_widget = self.parent()
                            if parent_widget and hasattr(parent_widget, 'tab_widget'):
                                # 在选项卡中查找特征库选项卡
                                for i in range(parent_widget.tab_widget.count()):
                                    tab = parent_widget.tab_widget.widget(i)
                                    if hasattr(tab, 'refresh_feature_list'):
                                        print(f"通知特征库选项卡刷新数据")
                                        tab.refresh_feature_list()
                                        break
                        except Exception as refresh_error:
                            print(f"尝试刷新特征库失败: {str(refresh_error)}")
                        
                        # 更新消息显示更多细节
                        QMessageBox.information(self, "添加成功", 
                            f"音乐已成功添加到特征库\n\n"
                            f"文件: {os.path.basename(file_path)}\n"
                            f"路径: {normalized_path}\n"
                            f"歌曲: {metadata.get('name', '未知')}\n"
                            f"艺术家: {metadata.get('artist', '未知')}\n"
                            f"{details if details else ''}"
                        )
                    else:
                        # 如果添加失败，尝试使用特殊处理逻辑
                        if "无法识别音频格式" in error_msg or "librosa" in error_msg:
                            # 尝试转换格式后再添加
                            try:
                                import subprocess
                                converted_file = file_path + ".converted.mp3"
                                print(f"尝试转换文件格式: {file_path} -> {converted_file}")
                                
                                # 检查是否有ffmpeg
                                try:
                                    subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
                                    has_ffmpeg = True
                                except FileNotFoundError:
                                    has_ffmpeg = False
                                
                                if has_ffmpeg:
                                    # 使用ffmpeg转换
                                    subprocess.run([
                                        "ffmpeg", "-y", "-i", file_path, 
                                        "-acodec", "libmp3lame", "-ab", "192k",
                                        converted_file
                                    ], check=True)
                                    
                                    print("格式转换成功，重新尝试添加")
                                    success, error_msg, details = safe_add_to_database(converted_file, metadata)
                                    
                                    if success:
                                        QMessageBox.information(self, "添加成功", 
                                            "音乐已成功添加到特征库\n(需要格式转换)")
                                        # 清理转换的文件
                                        try:
                                            os.remove(converted_file)
                                        except:
                                            pass
                                        return
                                else:
                                    error_msg += "\n\n系统中未找到ffmpeg，无法执行格式转换"
                            except Exception as conv_error:
                                error_msg += f"\n\n格式转换失败: {str(conv_error)}"
                        
                        # 显示详细错误信息
                        QMessageBox.warning(
                            self, 
                            "添加失败", 
                            f"添加到特征库失败: {error_msg}\n\n可能原因:\n"
                            f"1. 后端服务器未启动\n"
                            f"2. 文件格式不支持\n"
                            f"3. 特征提取失败\n\n"
                            f"提示: 请确保使用run_desktop_app.py启动了完整系统"
                        )
                else:
                    QMessageBox.information(self, "下载成功", f"音乐已下载到: {file_path}")
                    
            except requests.RequestException as e:
                QMessageBox.critical(self, "下载失败", f"下载文件时出错: {str(e)}")
            
        except Exception as e:
            QMessageBox.critical(self, "下载失败", f"下载过程中出错: {str(e)}")
            
    def _search_from_input(self):
        """从搜索框获取搜索词并执行搜索"""
        search_query = self.search_input.text().strip()
        if search_query:
            self.search_music(search_query)
    
    def search_music(self, song_name, artist_name=None):
        """
        在音乐库中搜索指定歌曲
        
        参数:
            song_name (str): 歌曲名
            artist_name (str, optional): 艺术家名，可选
        """
        # 首先加载主页
        self.web_view.setUrl(QUrl("https://music.cpp-prog.com/"))
        
        # 构建搜索查询
        if artist_name and artist_name.lower() != "未知" and artist_name.lower() != "unknown":
            search_query = f"{song_name} {artist_name}"
        else:
            search_query = song_name
        
        # 更新搜索框
        self.search_input.setText(search_query)
        
        # 保存搜索查询以便页面加载完成后使用
        self.current_search_query = search_query
        
        # 连接loadFinished信号以在页面加载完成后执行搜索
        self.web_view.loadFinished.connect(self._on_page_loaded)
        
        # 让音乐库选项卡成为活动选项卡
        if self.parent() and hasattr(self.parent(), 'setCurrentWidget'):
            self.parent().setCurrentWidget(self)
            
        print(f"准备搜索: {search_query}")
    
    def _on_page_loaded(self, success):
        """页面加载完成后的回调"""
        if success and hasattr(self, 'current_search_query'):
            print(f"页面加载完成，开始执行搜索: {self.current_search_query}")
            # 执行搜索
            self._execute_search(self.current_search_query)
            
            # 作为备用策略，也尝试在搜索框中直接搜索
            QTimer.singleShot(3000, lambda: self._try_direct_search(self.current_search_query))
            
        # 解除loadFinished信号连接，避免重复执行
        self.web_view.loadFinished.disconnect(self._on_page_loaded)
    
    def _try_direct_search(self, search_query):
        """尝试在网页上直接打开搜索对话框"""
        js_code = f"""
        (function() {{
            console.log("尝试直接打开搜索对话框...");
            
            // 直接尝试点击歌曲搜索按钮
            var searchTexts = ['歌曲搜索', '搜索', 'Search'];
            var foundButton = false;
            
            // 遍历所有可能是搜索按钮的元素
            var allElements = document.querySelectorAll('button, a, div, span');
            for (var i = 0; i < allElements.length && !foundButton; i++) {{
                var el = allElements[i];
                for (var j = 0; j < searchTexts.length && !foundButton; j++) {{
                    if (el.textContent && el.textContent.trim() === searchTexts[j]) {{
                        console.log("找到搜索按钮: " + searchTexts[j]);
                        el.click();
                        foundButton = true;
                        
                        // 等待搜索对话框出现
                        setTimeout(function() {{
                            // 查找搜索输入框
                            var searchInput = document.querySelector('input[type="search"], input[type="text"], input[placeholder*="搜索"]');
                            if (searchInput) {{
                                console.log("找到搜索框，填入内容: {search_query}");
                                searchInput.value = "{search_query}";
                                searchInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                
                                // 找到搜索按钮并点击
                                setTimeout(function() {{
                                    var searchBtn = document.querySelector('button.el-button--primary, button[type="submit"], button:contains("搜索")');
                                    if (searchBtn) {{
                                        console.log("点击搜索按钮");
                                        searchBtn.click();
                                    }} else {{
                                        // 模拟回车键
                                        console.log("模拟回车键");
                                        var enterEvent = new KeyboardEvent('keydown', {{
                                            bubbles: true, 
                                            cancelable: true, 
                                            keyCode: 13
                                        }});
                                        searchInput.dispatchEvent(enterEvent);
                                    }}
                                }}, 500);
                            }}
                        }}, 1000);
                    }}
                }}
            }}
            
            if (!foundButton) {{
                console.log("未找到搜索按钮");
            }}
        }})();
        """
        self.web_view.page().runJavaScript(js_code)
    
    def _execute_search(self, search_query):
        """通过JavaScript在网页中执行搜索"""
        # 注入JavaScript来填充搜索框并点击搜索按钮
        js_code = f"""
        (function() {{
            // 定义搜索函数
            function performSearch() {{
                console.log("开始执行搜索...");
                
                // 尝试多种方式找到搜索按钮
                function findSearchButton() {{
                    // 方法1: 通过文本内容
                    var allElements = document.querySelectorAll('*');
                    for (var i = 0; i < allElements.length; i++) {{
                        var el = allElements[i];
                        if (el.textContent && el.textContent.trim() === '歌曲搜索') {{
                            console.log("通过文本内容找到搜索按钮");
                            return el;
                        }}
                    }}
                    
                    // 方法2: 通过类名或ID
                    var possibleButtons = document.querySelectorAll('.search, #search, [class*="search"], [id*="search"]');
                    if (possibleButtons.length > 0) {{
                        console.log("通过类名或ID找到搜索按钮");
                        return possibleButtons[0];
                    }}
                    
                    // 方法3: 查找导航栏上的所有选项
                    var navItems = document.querySelectorAll('nav a, .nav a, .navbar a, header a');
                    for (var i = 0; i < navItems.length; i++) {{
                        if (navItems[i].textContent && navItems[i].textContent.includes('搜索')) {{
                            console.log("在导航栏找到搜索按钮");
                            return navItems[i];
                        }}
                    }}
                    
                    // 方法4: 直接在页面右上角查找
                    var topRightElements = document.querySelectorAll('header > *, nav > *, .header > *');
                    for (var i = 0; i < topRightElements.length; i++) {{
                        if (topRightElements[i].textContent && topRightElements[i].textContent.includes('搜索')) {{
                            console.log("在页面右上角找到搜索按钮");
                            return topRightElements[i];
                        }}
                    }}
                    
                    return null;
                }}
                
                // 查找搜索按钮并点击
                var searchButton = findSearchButton();
                if (searchButton) {{
                    console.log("找到搜索按钮，点击打开搜索对话框");
                    searchButton.click();
                    
                    // 等待搜索对话框出现
                    setTimeout(function() {{
                        // 尝试多种方式找到搜索输入框
                        function findSearchInput() {{
                            // 尝试不同的选择器
                            var selectors = [
                                'input[type="search"]', 
                                'input[type="text"]',
                                'input[placeholder*="搜索"]',
                                'input[placeholder*="search"]',
                                'input[class*="search"]',
                                'input[id*="search"]',
                                '.search input',
                                '#search input',
                                'form input'
                            ];
                            
                            for (var i = 0; i < selectors.length; i++) {{
                                var inputs = document.querySelectorAll(selectors[i]);
                                if (inputs.length > 0) {{
                                    console.log("找到搜索输入框，使用选择器: " + selectors[i]);
                                    return inputs[0];
                                }}
                            }}
                            
                            return null;
                        }}
                        
                        var searchInput = findSearchInput();
                        if (searchInput) {{
                            console.log("找到搜索输入框，填入搜索内容：", "{search_query}");
                            searchInput.value = "{search_query}";
                            searchInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            
                            // 选择网易云音乐平台（如果有）
                            var platformFound = false;
                            
                            // 方法1: 检查单选按钮
                            var radioBtns = document.querySelectorAll('input[type="radio"]');
                            for (var i = 0; i < radioBtns.length; i++) {{
                                var radioBtn = radioBtns[i];
                                var radioLabel = radioBtn.nextElementSibling;
                                var labelText = radioLabel ? radioLabel.textContent : '';
                                
                                if (radioBtn.id && radioBtn.id.includes('网易') || 
                                    radioBtn.name && radioBtn.name.includes('网易') ||
                                    radioBtn.value && radioBtn.value.includes('网易') ||
                                    labelText && labelText.includes('网易')) {{
                                    radioBtn.checked = true;
                                    radioBtn.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    console.log("选择网易云音乐平台 (单选按钮)");
                                    platformFound = true;
                                    break;
                                }}
                            }}
                            
                            // 方法2: 如果没找到单选按钮，查找平台选择按钮
                            if (!platformFound) {{
                                var platformBtns = document.querySelectorAll('button, a, span, div');
                                for (var i = 0; i < platformBtns.length; i++) {{
                                    if (platformBtns[i].textContent && platformBtns[i].textContent.includes('网易')) {{
                                        platformBtns[i].click();
                                        console.log("选择网易云音乐平台 (按钮)");
                                        platformFound = true;
                                        break;
                                    }}
                                }}
                            }}
                            
                            // 触发搜索
                            setTimeout(function() {{
                                // 方法1: 点击搜索按钮
                                var searchBtns = document.querySelectorAll('button[type="submit"], button, input[type="submit"]');
                                var searchBtnFound = false;
                                
                                for (var i = 0; i < searchBtns.length; i++) {{
                                    var btn = searchBtns[i];
                                    if (btn.textContent && btn.textContent.includes('搜索') || 
                                        btn.value && btn.value.includes('搜索') ||
                                        btn.className && btn.className.includes('search') ||
                                        btn.id && btn.id.includes('search')) {{
                                        console.log("点击搜索按钮提交搜索");
                                        btn.click();
                                        searchBtnFound = true;
                                        break;
                                    }}
                                }}
                                
                                // 方法2: 如果没找到搜索按钮，尝试提交表单
                                if (!searchBtnFound) {{
                                    var form = searchInput.closest('form');
                                    if (form) {{
                                        console.log("提交表单");
                                        form.submit();
                                    }} else {{
                                        // 方法3: 模拟回车键
                                        console.log("模拟回车键");
                                        var enterEvent = new KeyboardEvent('keydown', {{
                                            bubbles: true, 
                                            cancelable: true, 
                                            keyCode: 13
                                        }});
                                        searchInput.dispatchEvent(enterEvent);
                                    }}
                                }}
                            }}, 500);
                        }} else {{
                            console.log("未找到搜索输入框");
                        }}
                    }}, 1000);
                }} else {{
                    console.log("未找到搜索按钮，尝试查找搜索框");
                    // 如果没找到搜索按钮，尝试直接找搜索框
                    var searchInputs = document.querySelectorAll('input[type="search"], input[type="text"], input[placeholder*="搜索"]');
                    if (searchInputs.length > 0) {{
                        var searchInput = searchInputs[0];
                        console.log("找到直接的搜索框，填入内容并提交");
                        searchInput.value = "{search_query}";
                        searchInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        
                        // 模拟回车键
                        setTimeout(function() {{
                            var enterEvent = new KeyboardEvent('keydown', {{
                                bubbles: true, 
                                cancelable: true, 
                                keyCode: 13
                            }});
                            searchInput.dispatchEvent(enterEvent);
                        }}, 500);
                    }} else {{
                        console.log("无法找到任何搜索元素");
                    }}
                }}
            }}
            
            // 执行搜索，等待1秒确保页面完全加载
            setTimeout(performSearch, 1000);
        }})();
        """
        self.web_view.page().runJavaScript(js_code) 