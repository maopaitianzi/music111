import numpy as np
import librosa
import os
import pickle
import json
from typing import Dict, List, Any, Tuple, Optional
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from mutagen.wave import WAVE
from mutagen.oggvorbis import OggVorbis
from datetime import datetime

class AudioFeatureExtractor:
    """音频特征提取器类"""
    
    def __init__(self, sample_rate: int = 22050, n_fft: int = 2048, 
                 hop_length: int = 512, n_mels: int = 128):
        """
        初始化特征提取器
        
        参数:
            sample_rate: 采样率
            n_fft: FFT窗口大小
            hop_length: 帧移
            n_mels: Mel频谱的频带数量
        """
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels
    
    def extract_features(self, audio_path: str) -> Dict[str, Any]:
        """
        从音频文件中提取特征
        
        参数:
            audio_path: 音频文件路径
            
        返回:
            包含各种音频特征的字典
        """
        try:
            # 加载音频文件
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # 提取特征
            # 1. 梅尔频谱
            mel_spec = librosa.feature.melspectrogram(
                y=y, sr=sr, n_fft=self.n_fft, 
                hop_length=self.hop_length, n_mels=self.n_mels
            )
            log_mel_spec = librosa.power_to_db(mel_spec)
            
            # 2. MFCC特征
            mfcc = librosa.feature.mfcc(
                S=librosa.power_to_db(mel_spec), 
                n_mfcc=20
            )
            
            # 3. 色度特征
            chroma = librosa.feature.chroma_stft(
                y=y, sr=sr, n_fft=self.n_fft, 
                hop_length=self.hop_length
            )
            
            # 4. 谱质心
            spectral_centroid = librosa.feature.spectral_centroid(
                y=y, sr=sr, n_fft=self.n_fft, 
                hop_length=self.hop_length
            )
            
            # 5. 时域统计特征
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
            
            # 6. 节奏特征
            onset_env = librosa.onset.onset_strength(
                y=y, sr=sr, hop_length=self.hop_length
            )
            tempo, _ = librosa.beat.beat_track(
                onset_envelope=onset_env, sr=sr, 
                hop_length=self.hop_length
            )
            
            # 从音频文件中获取元数据
            metadata = self._extract_metadata(audio_path)
            duration = metadata.get('duration', 0)
            
            # 计算聚合统计特征
            features = {
                # 基本信息
                "file_path": audio_path,
                "file_name": os.path.basename(audio_path),
                "duration": duration,
                "added_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                
                # 梅尔频谱聚合特征
                "mel_mean": np.mean(log_mel_spec, axis=1).tolist(),
                "mel_std": np.std(log_mel_spec, axis=1).tolist(),
                
                # MFCC聚合特征
                "mfcc_mean": np.mean(mfcc, axis=1).tolist(),
                "mfcc_std": np.std(mfcc, axis=1).tolist(),
                
                # 色度特征聚合
                "chroma_mean": np.mean(chroma, axis=1).tolist(),
                
                # 谱质心聚合
                "spectral_centroid_mean": float(np.mean(spectral_centroid)),
                "spectral_centroid_std": float(np.std(spectral_centroid)),
                
                # 时域特征
                "zero_crossing_rate_mean": float(np.mean(zero_crossing_rate)),
                
                # 节奏特征
                "tempo": float(tempo),
                
                # 指纹特征 (梅尔频谱的简化版本)
                "fingerprint": self._create_fingerprint(log_mel_spec),
                
                # 元数据
                "song_name": metadata.get("title", ""),
                "author": metadata.get("artist", "")
            }
            
            return features
            
        except Exception as e:
            print(f"提取特征失败: {str(e)}")
            return {"error": str(e)}
    
    def _create_fingerprint(self, mel_spec: np.ndarray) -> List[List[int]]:
        """
        创建音频指纹
        将梅尔频谱图转换为更简洁的二进制表示
        
        参数:
            mel_spec: 梅尔频谱图
            
        返回:
            音频指纹
        """
        # 降采样梅尔频谱
        # 选择较少的频带和时间帧来减小指纹大小
        reduced_mel = mel_spec[::4, ::8]  # 每4个梅尔频带取1个，每8个时间帧取1个
        
        # 将频谱值二值化
        # 如果大于局部平均值，则为1，否则为0
        fingerprint = []
        for i in range(reduced_mel.shape[0]):
            row_mean = np.mean(reduced_mel[i])
            binary_row = [1 if val > row_mean else 0 for val in reduced_mel[i]]
            fingerprint.append(binary_row)
            
        return fingerprint

    def _extract_metadata(self, audio_path):
        """从音频文件中提取元数据"""
        metadata = {"duration": 0, "title": "", "artist": ""}
        
        try:
            file_ext = os.path.splitext(audio_path)[1].lower()
            
            if file_ext == '.mp3':
                try:
                    audio = MP3(audio_path)
                    metadata["duration"] = audio.info.length
                    
                    # 尝试读取ID3标签
                    try:
                        id3 = ID3(audio_path)
                        if 'TIT2' in id3:  # 标题
                            metadata["title"] = str(id3['TIT2'])
                        if 'TPE1' in id3:  # 艺术家
                            metadata["artist"] = str(id3['TPE1'])
                    except:
                        pass
                except:
                    warnings.warn(f"无法读取MP3文件元数据: {audio_path}")
                    
            elif file_ext == '.flac':
                try:
                    audio = FLAC(audio_path)
                    metadata["duration"] = audio.info.length
                    
                    if 'title' in audio:
                        metadata["title"] = audio['title'][0]
                    if 'artist' in audio:
                        metadata["artist"] = audio['artist'][0]
                except:
                    warnings.warn(f"无法读取FLAC文件元数据: {audio_path}")
                    
            elif file_ext == '.wav':
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        audio = WAVE(audio_path)
                    metadata["duration"] = audio.info.length
                except:
                    warnings.warn(f"无法读取WAV文件元数据: {audio_path}")
                    
            elif file_ext == '.ogg':
                try:
                    audio = OggVorbis(audio_path)
                    metadata["duration"] = audio.info.length
                    
                    if 'title' in audio:
                        metadata["title"] = audio['title'][0]
                    if 'artist' in audio:
                        metadata["artist"] = audio['artist'][0]
                except:
                    warnings.warn(f"无法读取OGG文件元数据: {audio_path}")
                    
            else:
                # 对于不支持的格式，尝试使用librosa获取时长
                try:
                    y, sr = librosa.load(audio_path, sr=None, duration=1.0)  # 只加载一小部分来提高效率
                    metadata["duration"] = librosa.get_duration(y=y, sr=sr)
                except:
                    warnings.warn(f"无法读取文件元数据: {audio_path}")
                    
        except Exception as e:
            print(f"提取元数据时出错: {str(e)}")
            
        return metadata

class FeatureDatabase:
    """特征数据库类，用于管理提取的特征"""
    
    def __init__(self, database_path: str = "music_features_db"):
        """
        初始化特征数据库
        
        参数:
            database_path: 数据库文件路径
        """
        self.database_path = database_path
        self.features_dir = os.path.join(database_path, "features")
        self.covers_dir = os.path.join(database_path, "covers")
        self.index_path = os.path.join(database_path, "index.json")
        self.feature_index = {}
        
        # 确保目录存在
        os.makedirs(self.features_dir, exist_ok=True)
        os.makedirs(self.covers_dir, exist_ok=True)
        print(f"初始化特征数据库，covers_dir={self.covers_dir}, 是否存在: {os.path.exists(self.covers_dir)}")
        
        # 加载索引（如果存在）
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    self.feature_index = json.load(f)
                    
                # 确保每个条目都有cover_path字段
                updated = False
                for file_id, info in self.feature_index.items():
                    if "cover_path" not in info:
                        info["cover_path"] = ""
                        updated = True
                
                # 如果有更新，保存回文件
                if updated:
                    self._save_index()
                    print("已为特征索引添加cover_path字段")
            except Exception as e:
                print(f"加载索引文件失败: {str(e)}")
                self.feature_index = {}
    
    def add_feature(self, feature_data: Dict[str, Any]) -> bool:
        """
        添加特征到数据库
        
        参数:
            feature_data: 特征数据字典
            
        返回:
            是否成功添加
        """
        try:
            if "file_name" not in feature_data or "file_path" not in feature_data:
                return False
                
            file_name = feature_data["file_name"]
            file_id = self._generate_file_id(file_name)
            
            # 保存特征数据
            feature_path = os.path.join(self.features_dir, f"{file_id}.pkl")
            with open(feature_path, 'wb') as f:
                pickle.dump(feature_data, f)
                
            # 更新索引
            self.feature_index[file_id] = {
                "file_name": file_name,
                "file_path": feature_data["file_path"],
                "duration": feature_data.get("duration", 0),
                "feature_path": feature_path,
                "added_time": self._get_current_time(),
                "song_name": feature_data.get("song_name", ""),
                "author": feature_data.get("author", ""),
                "cover_path": feature_data.get("cover_path", "")
            }
            
            # 保存索引
            self._save_index()
            
            return True
            
        except Exception as e:
            print(f"添加特征失败: {str(e)}")
            return False
    
    def get_feature(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取特征数据
        
        参数:
            file_id: 文件ID
            
        返回:
            特征数据字典或None
        """
        if file_id not in self.feature_index:
            return None
            
        try:
            feature_path = self.feature_index[file_id]["feature_path"]
            with open(feature_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"读取特征失败: {str(e)}")
            return None
    
    def get_all_files(self) -> List[Dict[str, Any]]:
        """
        获取所有文件的基本信息
        
        返回:
            文件信息列表
        """
        result = []
        for file_id, info in self.feature_index.items():
            # 确保歌曲名和作者字段存在
            if "song_name" not in info:
                info["song_name"] = ""
            if "author" not in info:
                info["author"] = ""
                
            result.append({
                "id": file_id,
                "file_name": info["file_name"],
                "file_path": info["file_path"],
                "duration": info.get("duration", 0),
                "added_time": info.get("added_time", ""),
                "song_name": info.get("song_name", ""),
                "author": info.get("author", ""),
                "cover_path": info.get("cover_path", "")
            })
        return result
    
    def remove_feature(self, file_id: str) -> bool:
        """
        从数据库中删除特征
        
        参数:
            file_id: 文件ID
            
        返回:
            是否成功删除
        """
        if file_id not in self.feature_index:
            return False
            
        try:
            # 删除特征文件
            feature_path = self.feature_index[file_id]["feature_path"]
            if os.path.exists(feature_path):
                os.remove(feature_path)
                
            # 获取封面路径
            cover_path = self.feature_index[file_id].get("cover_path", "")
            
            # 删除封面文件
            if cover_path and os.path.exists(cover_path):
                os.remove(cover_path)
                
            # 更新索引
            del self.feature_index[file_id]
            self._save_index()
            
            return True
            
        except Exception as e:
            print(f"删除特征失败: {str(e)}")
            return False
    
    def _generate_file_id(self, file_name: str) -> str:
        """生成文件的唯一ID"""
        import hashlib
        return hashlib.md5(file_name.encode()).hexdigest()
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _save_index(self) -> None:
        """保存索引到文件"""
        try:
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(self.feature_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存索引失败: {str(e)}")

    def update_feature_info(self, file_id, info):
        """
        更新特征文件信息
        
        Parameters:
        -----------
        file_id : str
            文件ID
        info : dict
            需要更新的信息
            
        Returns:
        --------
        bool
            是否成功更新
        """
        if file_id not in self.feature_index:
            print(f"找不到ID为 {file_id} 的特征")
            return False
            
        try:
            # 更新索引信息
            for key, value in info.items():
                if key in ["song_name", "author", "cover_path"]:
                    self.feature_index[file_id][key] = value
            
            # 如果需要更新特征文件本身
            if info.get("update_feature", False):
                feature_path = self.feature_index[file_id].get("feature_path", "")
                if feature_path and os.path.exists(feature_path):
                    try:
                        # 读取特征文件
                        with open(feature_path, 'rb') as f:
                            feature_data = pickle.load(f)
                            
                        # 更新特征数据
                        for key, value in info.items():
                            if key in ["song_name", "author", "cover_path"]:
                                feature_data[key] = value
                                
                        # 保存更新后的特征文件
                        with open(feature_path, 'wb') as f:
                            pickle.dump(feature_data, f)
                    except Exception as e:
                        print(f"更新特征文件失败: {str(e)}")
                        return False
            
            # 保存索引
            self._save_index()
            return True
            
        except Exception as e:
            print(f"更新特征信息失败: {str(e)}")
            return False

def batch_extract_features(folder_path: str, output_path: str = None) -> Tuple[int, int, List[str]]:
    """
    批量提取文件夹中所有音频文件的特征
    
    参数:
        folder_path: 音频文件夹路径
        output_path: 输出数据库路径，默认为None，使用默认路径
        
    返回:
        (成功数, 总数, 失败文件列表)
    """
    extractor = AudioFeatureExtractor()
    db = FeatureDatabase(output_path or "music_features_db")
    
    # 获取所有音频文件
    audio_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a')):
                audio_files.append(os.path.join(root, file))
    
    total_files = len(audio_files)
    success_count = 0
    failed_files = []
    
    # 处理每个文件
    for audio_file in audio_files:
        try:
            # 提取特征
            features = extractor.extract_features(audio_file)
            
            # 添加到数据库
            if "error" not in features and db.add_feature(features):
                success_count += 1
            else:
                failed_files.append(audio_file)
                
        except Exception as e:
            print(f"处理文件 {audio_file} 失败: {str(e)}")
            failed_files.append(audio_file)
    
    return success_count, total_files, failed_files 