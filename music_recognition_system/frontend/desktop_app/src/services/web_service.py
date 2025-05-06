import requests
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtWidgets import QMessageBox
import json
import re
from bs4 import BeautifulSoup

class MusicWebService(QObject):
    """与music.cpp-prog.com网站交互的服务类"""
    
    # 定义信号
    songs_loaded = pyqtSignal(list)
    playlists_loaded = pyqtSignal(list)
    search_completed = pyqtSignal(list)
    album_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_url = "https://music.cpp-prog.com"
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_network_reply)
        self.current_request_type = None
    
    def get_featured_albums(self):
        """获取推荐专辑列表"""
        self.current_request_type = "featured_albums"
        url = f"{self.base_url}/"
        
        try:
            # 使用requests库直接获取数据（简化演示）
            response = requests.get(url)
            if response.status_code == 200:
                # 解析HTML内容
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 模拟解析网页内容获取专辑列表
                # 在实际应用中需要根据网站的实际HTML结构进行调整
                albums = []
                # 这里假设网站有一个专辑列表的结构
                for album_elem in soup.select('.album-item')[:12]:  # 限制获取12个
                    album = {
                        "title": album_elem.select_one('.album-title').text.strip(),
                        "artist": album_elem.select_one('.album-artist').text.strip(),
                        "cover_url": album_elem.select_one('img').get('src'),
                        "year": 2023,  # 假设年份
                        "genre": "流行"  # 假设流派
                    }
                    albums.append(album)
                
                # 如果没有找到专辑或解析失败，使用模拟数据
                if not albums:
                    albums = self._get_mock_albums()
                
                self.songs_loaded.emit(albums)
            else:
                # 如果请求失败，使用模拟数据
                self.songs_loaded.emit(self._get_mock_albums())
                
        except Exception as e:
            print(f"获取推荐专辑失败: {str(e)}")
            # 出错时使用模拟数据
            self.songs_loaded.emit(self._get_mock_albums())
    
    def search_songs(self, query):
        """搜索歌曲"""
        self.current_request_type = "search"
        url = f"{self.base_url}/search?q={query}"
        
        try:
            # 使用requests库直接获取数据（简化演示）
            response = requests.get(url)
            if response.status_code == 200:
                # 解析HTML内容
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 模拟解析网页内容获取搜索结果
                # 在实际应用中需要根据网站的实际HTML结构进行调整
                search_results = []
                for result_elem in soup.select('.search-result-item'):
                    result = {
                        "title": result_elem.select_one('.song-title').text.strip(),
                        "artist": result_elem.select_one('.song-artist').text.strip(),
                        "duration": result_elem.select_one('.song-duration').text.strip(),
                        "album": result_elem.select_one('.song-album').text.strip()
                    }
                    search_results.append(result)
                
                # 如果没有找到结果或解析失败，使用模拟数据
                if not search_results:
                    search_results = self._get_mock_search_results(query)
                
                self.search_completed.emit(search_results)
            else:
                # 如果请求失败，使用模拟数据
                self.search_completed.emit(self._get_mock_search_results(query))
                
        except Exception as e:
            print(f"搜索歌曲失败: {str(e)}")
            # 出错时使用模拟数据
            self.search_completed.emit(self._get_mock_search_results(query))
    
    def get_album_details(self, album_id):
        """获取专辑详情"""
        self.current_request_type = "album_details"
        url = f"{self.base_url}/album/{album_id}"
        
        try:
            # 使用requests库直接获取数据（简化演示）
            response = requests.get(url)
            if response.status_code == 200:
                # 解析HTML内容
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 模拟解析网页内容获取专辑详情
                # 在实际应用中需要根据网站的实际HTML结构进行调整
                album_details = {
                    "id": album_id,
                    "title": soup.select_one('.album-title').text.strip(),
                    "artist": soup.select_one('.album-artist').text.strip(),
                    "cover_url": soup.select_one('.album-cover img').get('src'),
                    "year": int(soup.select_one('.album-year').text.strip()),
                    "genre": soup.select_one('.album-genre').text.strip(),
                    "songs": []
                }
                
                # 解析歌曲列表
                for idx, song_elem in enumerate(soup.select('.album-track')):
                    song = {
                        "track": idx + 1,
                        "title": song_elem.select_one('.track-title').text.strip(),
                        "duration": song_elem.select_one('.track-duration').text.strip(),
                        "popularity": float(song_elem.select_one('.track-popularity').text.strip())
                    }
                    album_details["songs"].append(song)
                
                # 如果解析失败，使用模拟数据
                if not album_details["songs"]:
                    album_details = self._get_mock_album_details(album_id)
                
                self.album_loaded.emit(album_details)
            else:
                # 如果请求失败，使用模拟数据
                self.album_loaded.emit(self._get_mock_album_details(album_id))
                
        except Exception as e:
            print(f"获取专辑详情失败: {str(e)}")
            # 出错时使用模拟数据
            self.album_loaded.emit(self._get_mock_album_details(album_id))
    
    def handle_network_reply(self, reply):
        """处理网络请求的回复"""
        if reply.error() != QNetworkReply.NetworkError.NoError:
            error_msg = f"网络请求错误: {reply.errorString()}"
            self.error_occurred.emit(error_msg)
            return
        
        # 获取回复数据
        data = reply.readAll().data().decode('utf-8')
        
        # 根据请求类型处理数据
        if self.current_request_type == "featured_albums":
            # 解析专辑数据并发送信号
            try:
                albums = self._parse_album_data(data)
                self.songs_loaded.emit(albums)
            except Exception as e:
                self.error_occurred.emit(f"解析专辑数据失败: {str(e)}")
        
        elif self.current_request_type == "search":
            # 解析搜索结果并发送信号
            try:
                results = self._parse_search_results(data)
                self.search_completed.emit(results)
            except Exception as e:
                self.error_occurred.emit(f"解析搜索结果失败: {str(e)}")
        
        elif self.current_request_type == "album_details":
            # 解析专辑详情并发送信号
            try:
                album = self._parse_album_details(data)
                self.album_loaded.emit(album)
            except Exception as e:
                self.error_occurred.emit(f"解析专辑详情失败: {str(e)}")
    
    def _parse_album_data(self, data):
        """解析专辑数据（需要根据实际API响应格式调整）"""
        # 这里应该根据网站实际返回的数据格式进行解析
        # 由于我们不知道具体格式，这里使用模拟数据
        return self._get_mock_albums()
    
    def _parse_search_results(self, data):
        """解析搜索结果（需要根据实际API响应格式调整）"""
        # 这里应该根据网站实际返回的数据格式进行解析
        # 由于我们不知道具体格式，这里使用模拟数据
        return self._get_mock_search_results("示例查询")
    
    def _parse_album_details(self, data):
        """解析专辑详情（需要根据实际API响应格式调整）"""
        # 这里应该根据网站实际返回的数据格式进行解析
        # 由于我们不知道具体格式，这里使用模拟数据
        return self._get_mock_album_details("1")
    
    def _get_mock_albums(self):
        """获取模拟专辑数据"""
        return [
            {"title": "热门华语", "artist": "Various Artists", "year": 2023, "cover_url": "", "genre": "流行"},
            {"title": "欧美经典", "artist": "Various Artists", "year": 2023, "cover_url": "", "genre": "流行/摇滚"},
            {"title": "最新上架", "artist": "Various Artists", "year": 2023, "cover_url": "", "genre": "流行"},
            {"title": "古典音乐", "artist": "Various Artists", "year": 2023, "cover_url": "", "genre": "古典"},
            {"title": "爵士音乐", "artist": "Various Artists", "year": 2023, "cover_url": "", "genre": "爵士"},
            {"title": "流行金曲", "artist": "Various Artists", "year": 2023, "cover_url": "", "genre": "流行"},
            {"title": "怀旧专区", "artist": "Various Artists", "year": 2023, "cover_url": "", "genre": "流行/摇滚"},
            {"title": "独立音乐", "artist": "Various Artists", "year": 2023, "cover_url": "", "genre": "独立"},
            {"title": "电影原声", "artist": "Various Artists", "year": 2023, "cover_url": "", "genre": "原声"},
            {"title": "轻音乐", "artist": "Various Artists", "year": 2023, "cover_url": "", "genre": "轻音乐"},
            {"title": "摇滚专区", "artist": "Various Artists", "year": 2023, "cover_url": "", "genre": "摇滚"},
            {"title": "民谣精选", "artist": "Various Artists", "year": 2023, "cover_url": "", "genre": "民谣"}
        ]
    
    def _get_mock_search_results(self, query):
        """获取模拟搜索结果"""
        return [
            {"title": f"{query} - 搜索结果1", "artist": "艺术家1", "duration": "3:45", "album": "专辑1"},
            {"title": f"{query} - 搜索结果2", "artist": "艺术家2", "duration": "4:12", "album": "专辑2"},
            {"title": f"{query} - 搜索结果3", "artist": "艺术家3", "duration": "3:30", "album": "专辑3"},
            {"title": f"{query} - 搜索结果4", "artist": "艺术家4", "duration": "5:20", "album": "专辑4"},
            {"title": f"{query} - 搜索结果5", "artist": "艺术家5", "duration": "3:55", "album": "专辑5"}
        ]
    
    def _get_mock_album_details(self, album_id):
        """获取模拟专辑详情"""
        mock_albums = {
            "热门华语": {
                "id": "热门华语",
                "title": "热门华语",
                "artist": "Various Artists",
                "year": 2023,
                "cover_url": "",
                "genre": "流行",
                "songs": [
                    {"track": 1, "title": "稻香", "artist": "周杰伦", "duration": "3:42", "popularity": 9.8},
                    {"track": 2, "title": "倒影", "artist": "陈奕迅", "duration": "4:15", "popularity": 9.5},
                    {"track": 3, "title": "光年之外", "artist": "邓紫棋", "duration": "3:55", "popularity": 9.6},
                    {"track": 4, "title": "小城夏天", "artist": "LBI利比", "duration": "3:48", "popularity": 9.3},
                    {"track": 5, "title": "句号", "artist": "邓紫棋", "duration": "4:02", "popularity": 9.7},
                    {"track": 6, "title": "爱你", "artist": "陈芳语", "duration": "3:49", "popularity": 9.4},
                    {"track": 7, "title": "起风了", "artist": "买辣椒也用券", "duration": "5:11", "popularity": 9.9},
                    {"track": 8, "title": "漠河舞厅", "artist": "柳爽", "duration": "4:40", "popularity": 9.7}
                ]
            },
            "欧美经典": {
                "id": "欧美经典",
                "title": "欧美经典",
                "artist": "Various Artists",
                "year": 2023,
                "cover_url": "",
                "genre": "流行/摇滚",
                "songs": [
                    {"track": 1, "title": "Billie Jean", "artist": "Michael Jackson", "duration": "4:54", "popularity": 9.9},
                    {"track": 2, "title": "Hotel California", "artist": "Eagles", "duration": "6:30", "popularity": 9.8},
                    {"track": 3, "title": "Bohemian Rhapsody", "artist": "Queen", "duration": "5:55", "popularity": 9.9},
                    {"track": 4, "title": "Yesterday", "artist": "The Beatles", "duration": "2:05", "popularity": 9.7},
                    {"track": 5, "title": "Every Breath You Take", "artist": "The Police", "duration": "4:13", "popularity": 9.6},
                    {"track": 6, "title": "Smells Like Teen Spirit", "artist": "Nirvana", "duration": "5:01", "popularity": 9.8},
                    {"track": 7, "title": "Sweet Child O' Mine", "artist": "Guns N' Roses", "duration": "5:55", "popularity": 9.7},
                    {"track": 8, "title": "Like a Rolling Stone", "artist": "Bob Dylan", "duration": "6:13", "popularity": 9.5}
                ]
            }
        }
        
        # 如果找到对应ID的专辑，返回详情
        if album_id in mock_albums:
            return mock_albums[album_id]
        
        # 否则返回默认专辑
        return {
            "id": album_id,
            "title": f"专辑{album_id}",
            "artist": "Various Artists",
            "year": 2023,
            "cover_url": "",
            "genre": "流行",
            "songs": [
                {"track": 1, "title": "歌曲1", "duration": "3:45", "popularity": 8.5},
                {"track": 2, "title": "歌曲2", "duration": "4:12", "popularity": 8.7},
                {"track": 3, "title": "歌曲3", "duration": "3:30", "popularity": 9.1},
                {"track": 4, "title": "歌曲4", "duration": "4:05", "popularity": 8.9},
                {"track": 5, "title": "歌曲5", "duration": "3:58", "popularity": 9.2}
            ]
        } 