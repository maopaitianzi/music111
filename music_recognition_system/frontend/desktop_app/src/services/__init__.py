"""服务模块"""

from .web_service import MusicWebService
from .music_recognition_service import MusicRecognitionService
from .audio_recorder import AudioRecorder

__all__ = ['MusicWebService', 'MusicRecognitionService', 'AudioRecorder']

# 服务模块包
# 此文件使services目录被识别为Python包 