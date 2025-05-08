from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QLineEdit
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView

class LibraryTab(QWidget):
    """音乐库选项卡 - 接入外部音乐网站"""
    
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
        
        # 创建Web视图组件
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("https://music.cpp-prog.com/"))
        
        # 添加到布局
        layout.addLayout(header_layout)
        layout.addWidget(self.web_view)
        
        self.setLayout(layout)
    
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