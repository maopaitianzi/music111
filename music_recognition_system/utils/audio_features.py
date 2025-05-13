import numpy as np
import librosa
import os
import pickle
import json
import warnings
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
                 hop_length: int = 512, n_mels: int = 128, 
                 mfcc_count: int = 40, n_chroma: int = 36):
        """
        初始化特征提取器
        
        参数:
            sample_rate: 采样率
            n_fft: FFT窗口大小
            hop_length: 帧移
            n_mels: Mel频谱的频带数量
            mfcc_count: MFCC特征数量
            n_chroma: 色度特征数量
        """
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels
        self.mfcc_count = mfcc_count
        self.n_chroma = n_chroma
    
    def extract_features(self, audio_path: str) -> Dict[str, Any]:
        """
        从音频文件中提取特征
        
        参数:
            audio_path: 音频文件路径
            
        返回:
            包含各种音频特征的字典
        """
        try:
            # 加载音频文件，使用kaiser_fast选项加快加载速度
            y, sr = librosa.load(audio_path, sr=self.sample_rate, res_type='kaiser_fast')
            
            # 分割音频为多个片段，提取更稳定的特征（避免只分析一小部分）
            # 提取起始、中部、结尾三个部分
            segments = []
            segment_length = min(len(y) // 3, 10 * sr)  # 最多10秒片段
            if len(y) >= 3 * segment_length:
                segments = [
                    y[:segment_length],  # 开头片段
                    y[len(y)//2-segment_length//2:len(y)//2+segment_length//2],  # 中间片段
                    y[-segment_length:]  # 结尾片段
                ]
            else:
                # 音频较短，只使用完整音频
                segments = [y]
            
            # 1. 梅尔频谱
            mel_specs = []
            log_mel_specs = []
            for segment in segments:
                mel_spec = librosa.feature.melspectrogram(
                    y=segment, sr=sr, n_fft=self.n_fft, 
                    hop_length=self.hop_length, n_mels=self.n_mels
                )
                log_mel_spec = librosa.power_to_db(mel_spec)
                mel_specs.append(mel_spec)
                log_mel_specs.append(log_mel_spec)
            
            # 2. MFCC特征 - 使用更多的MFCC系数
            mfccs = []
            for mel_spec in mel_specs:
                mfcc = librosa.feature.mfcc(
                    S=librosa.power_to_db(mel_spec), 
                    n_mfcc=self.mfcc_count
                )
                # 添加MFCC的一阶和二阶导数特征(Delta和Delta-Delta)
                mfcc_delta = librosa.feature.delta(mfcc)
                mfcc_delta2 = librosa.feature.delta(mfcc, order=2)
                # 合并所有MFCC特征
                full_mfcc = np.concatenate((mfcc, mfcc_delta, mfcc_delta2))
                mfccs.append(full_mfcc)
            
            # 3. 色度特征 - 增加色度特征分辨率
            chromas = []
            for segment in segments:
                chroma = librosa.feature.chroma_cqt(
                    y=segment, sr=sr, hop_length=self.hop_length,
                    n_chroma=self.n_chroma
                )
                chromas.append(chroma)
            
            # 4. 谱质心和其他谱特征
            spectral_features = []
            for segment in segments:
                spectral_centroid = librosa.feature.spectral_centroid(
                    y=segment, sr=sr, n_fft=self.n_fft, 
                    hop_length=self.hop_length
                )
                spectral_bandwidth = librosa.feature.spectral_bandwidth(
                    y=segment, sr=sr, n_fft=self.n_fft,
                    hop_length=self.hop_length
                )
                spectral_rolloff = librosa.feature.spectral_rolloff(
                    y=segment, sr=sr, n_fft=self.n_fft,
                    hop_length=self.hop_length
                )
                spectral_contrast = librosa.feature.spectral_contrast(
                    y=segment, sr=sr, n_fft=self.n_fft,
                    hop_length=self.hop_length
                )
                spectral_flatness = librosa.feature.spectral_flatness(
                    y=segment, n_fft=self.n_fft,
                    hop_length=self.hop_length
                )
                spectral_features.append({
                    'centroid': spectral_centroid,
                    'bandwidth': spectral_bandwidth,
                    'rolloff': spectral_rolloff,
                    'contrast': spectral_contrast,
                    'flatness': spectral_flatness
                })
            
            # 5. 基于谱质心构建的谱质心轮廓
            spectral_centroids = [feat['centroid'] for feat in spectral_features]
            centroid_profiles = []
            for centroid in spectral_centroids:
                # 计算质心的归一化分布
                centroid_norm = (centroid - np.mean(centroid)) / np.std(centroid)
                centroid_profiles.append(centroid_norm)
            
            # 6. 时域和节奏特征
            tempo_features = []
            for segment in segments:
                # 过零率
                zero_crossing_rate = librosa.feature.zero_crossing_rate(segment)
                
                # RMS能量
                rms = librosa.feature.rms(y=segment)
                
                # 节奏特征 - 使用更强大的多重解析度分析
                onset_env = librosa.onset.onset_strength(
                    y=segment, sr=sr, hop_length=self.hop_length,
                    feature=librosa.feature.melspectrogram
                )
                
                tempo, beats = librosa.beat.beat_track(
                    onset_envelope=onset_env, sr=sr, 
                    hop_length=self.hop_length,
                    tightness=100  # 增加紧密度提高准确性
                )
                
                # 节奏统计
                beat_intervals = np.diff(beats) * self.hop_length / sr
                if len(beat_intervals) > 0:
                    beat_std = np.std(beat_intervals)
                else:
                    beat_std = 0
                
                # 节奏强度 
                pulse_clarity = np.mean(onset_env)
                
                tempo_features.append({
                    'zero_crossing_rate': zero_crossing_rate,
                    'rms': rms,
                    'tempo': tempo,
                    'beat_std': beat_std,
                    'pulse_clarity': pulse_clarity
                })
            
            # 7. 频谱对比度：突出显示音乐中的音色变化
            contrasts = []
            for segment in segments:
                contrast = librosa.feature.spectral_contrast(
                    y=segment, sr=sr, n_fft=self.n_fft,
                    hop_length=self.hop_length
                )
                contrasts.append(contrast)
            
            # 8. 调性特征：提取音乐的调性信息
            tonal_features = []
            for segment in segments:
                # 和弦检测
                chroma_cq = librosa.feature.chroma_cqt(y=segment, sr=sr)
                
                # 调性中心
                key_strengths = librosa.feature.tonnetz(
                    y=segment, sr=sr
                )
                tonal_features.append(key_strengths)
            
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
                
                # 梅尔频谱聚合特征 (提取每个分段的平均值和标准差)
                "mel_mean": np.mean([np.mean(log_spec, axis=1) for log_spec in log_mel_specs], axis=0).tolist(),
                "mel_std": np.mean([np.std(log_spec, axis=1) for log_spec in log_mel_specs], axis=0).tolist(),
                "mel_skew": np.mean([self._compute_skewness(log_spec) for log_spec in log_mel_specs], axis=0).tolist(),
                
                # MFCC特征 (包含一阶和二阶导数)
                "mfcc_mean": np.mean([np.mean(mfcc, axis=1) for mfcc in mfccs], axis=0).tolist(),
                "mfcc_std": np.mean([np.std(mfcc, axis=1) for mfcc in mfccs], axis=0).tolist(),
                "mfcc_skew": np.mean([self._compute_skewness(mfcc) for mfcc in mfccs], axis=0).tolist(),
                
                # 色度特征聚合
                "chroma_mean": np.mean([np.mean(chroma, axis=1) for chroma in chromas], axis=0).tolist(),
                "chroma_std": np.mean([np.std(chroma, axis=1) for chroma in chromas], axis=0).tolist(),
                
                # 光谱特征聚合
                "spectral_centroid_mean": np.mean([np.mean(feat['centroid']) for feat in spectral_features]),
                "spectral_centroid_std": np.mean([np.std(feat['centroid']) for feat in spectral_features]),
                "spectral_bandwidth_mean": np.mean([np.mean(feat['bandwidth']) for feat in spectral_features]),
                "spectral_rolloff_mean": np.mean([np.mean(feat['rolloff']) for feat in spectral_features]),
                "spectral_contrast_mean": np.mean([np.mean(feat['contrast'], axis=1) for feat in spectral_features], axis=0).tolist(),
                "spectral_flatness_mean": np.mean([np.mean(feat['flatness']) for feat in spectral_features]),
                
                # 时域和节奏特征
                "zero_crossing_rate_mean": np.mean([np.mean(feat['zero_crossing_rate']) for feat in tempo_features]),
                "rms_mean": np.mean([np.mean(feat['rms']) for feat in tempo_features]),
                "tempo": np.mean([feat['tempo'] for feat in tempo_features]),
                "beat_std": np.mean([feat['beat_std'] for feat in tempo_features]),
                "pulse_clarity": np.mean([feat['pulse_clarity'] for feat in tempo_features]),
                
                # 调性特征
                "tonal_features_mean": np.mean([np.mean(tonal, axis=1) for tonal in tonal_features], axis=0).tolist(),
                
                # 高级特征 - 谱质心轮廓的自相关
                "centroid_profile": np.mean([self._compute_autocorrelation(profile.flatten())[:20] for profile in centroid_profiles], axis=0).tolist(),
                
                # 光谱对比度总体特征
                "contrast_profile": np.mean([np.mean(contrast, axis=1) for contrast in contrasts], axis=0).tolist(),
                
                # 分段能量分布 - 提供歌曲结构信息
                "energy_distribution": self._compute_energy_distribution(y),
                
                # 指纹特征 (增强版)
                "fingerprint": self._create_enhanced_fingerprint(log_mel_specs),
                
                # 元数据
                "song_name": metadata.get("title", ""),
                "author": metadata.get("artist", "")
            }
            
            return features
            
        except Exception as e:
            print(f"提取特征失败: {str(e)}")
            return {"error": str(e)}
    
    def _compute_skewness(self, feature: np.ndarray) -> np.ndarray:
        """计算特征的偏度，用于捕获分布的不对称性"""
        mean = np.mean(feature, axis=1, keepdims=True)
        std = np.std(feature, axis=1, keepdims=True)
        skew = np.mean(((feature - mean) / std) ** 3, axis=1)
        return skew
    
    def _compute_autocorrelation(self, signal: np.ndarray, max_lag: int = 100) -> np.ndarray:
        """计算信号的自相关，用于捕获周期性模式"""
        result = np.correlate(signal, signal, mode='full')
        # 只保留中心和正相关部分
        center = len(result) // 2
        return result[center:center + max_lag] / result[center]
    
    def _compute_energy_distribution(self, y: np.ndarray, n_segments: int = 10) -> List[float]:
        """计算音频在时间轴上的能量分布"""
        segment_length = len(y) // n_segments
        energy_dist = []
        
        for i in range(n_segments):
            start = i * segment_length
            end = start + segment_length
            segment = y[start:end]
            energy = np.sum(segment ** 2)
            energy_dist.append(float(energy))
            
        # 归一化能量分布
        total_energy = sum(energy_dist)
        if total_energy > 0:
            energy_dist = [e / total_energy for e in energy_dist]
            
        return energy_dist
    
    def _create_enhanced_fingerprint(self, mel_specs: List[np.ndarray]) -> List[List[int]]:
        """
        创建增强版音频指纹
        使用多段梅尔频谱图并应用更复杂的处理
        
        参数:
            mel_specs: 梅尔频谱图列表
            
        返回:
            增强的音频指纹
        """
        # 将所有频谱图合并成一个
        combined_mel = np.concatenate([spec for spec in mel_specs], axis=1)
        
        # 降采样梅尔频谱，但保留更多细节
        reduced_mel = combined_mel[::2, ::4]  # 每2个梅尔频带取1个，每4个时间帧取1个
        
        # 使用自适应阈值进行二值化
        fingerprint = []
        window_size = 5  # 局部窗口大小
        
        for i in range(reduced_mel.shape[0]):
            binary_row = []
            for j in range(reduced_mel.shape[1]):
                # 计算局部窗口
                start_col = max(0, j - window_size)
                end_col = min(reduced_mel.shape[1], j + window_size + 1)
                window = reduced_mel[i, start_col:end_col]
                
                # 使用加权局部阈值
                center_weight = 1.5  # 中心点权重更高
                threshold = (np.mean(window) + center_weight * reduced_mel[i, j]) / (1 + center_weight)
                
                # 二值化
                binary_row.append(1 if reduced_mel[i, j] > threshold else 0)
                
            fingerprint.append(binary_row)
        
        # 对指纹进行稳定处理 - 去除孤立点
        for i in range(1, len(fingerprint) - 1):
            for j in range(1, len(fingerprint[i]) - 1):
                # 检查周围8个点
                neighbors = [
                    fingerprint[i-1][j-1], fingerprint[i-1][j], fingerprint[i-1][j+1],
                    fingerprint[i][j-1], fingerprint[i][j+1],
                    fingerprint[i+1][j-1], fingerprint[i+1][j], fingerprint[i+1][j+1]
                ]
                # 如果周围大多数点与当前点不同，则翻转当前点
                if sum(neighbors) >= 6 and fingerprint[i][j] == 0:
                    fingerprint[i][j] = 1
                elif sum(neighbors) <= 2 and fingerprint[i][j] == 1:
                    fingerprint[i][j] = 0
            
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
                        try:
                            # 首先尝试使用mutagen读取
                            audio = WAVE(audio_path)
                            metadata["duration"] = audio.info.length
                        except Exception:
                            # 如果mutagen失败，尝试使用librosa获取持续时间
                            y, sr = librosa.load(audio_path, sr=None, duration=1.0)
                            metadata["duration"] = librosa.get_duration(y=y, sr=sr)
                            # 获取文件名作为基本元数据（不再提示警告）
                            metadata["title"] = os.path.splitext(os.path.basename(audio_path))[0]
                except Exception:
                    # 如果两种方法都失败，使用librosa预估持续时间
                    try:
                        y, sr = librosa.load(audio_path, sr=None, duration=1.0)
                        # 预估整个文件的持续时间
                        import soundfile as sf
                        file_info = sf.info(audio_path)
                        metadata["duration"] = file_info.duration
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
            
            # 处理文件路径 - 确保同时处理相对路径和绝对路径
            file_path = feature_data["file_path"]
            
            # 检查路径是否为临时文件路径，并且文件不存在
            if ("temp" in file_path and "db_add_" in file_path) or not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(self.database_path)), file_path)):
                print(f"检测到临时文件路径或文件不存在: {file_path}")
                # 尝试在Music目录中查找真实文件
                try:
                    # 获取项目根目录
                    project_root = os.path.abspath(os.path.join(os.path.dirname(self.database_path), "../.."))
                    music_dir = os.path.join(project_root, "Music")
                    
                    if os.path.exists(music_dir):
                        # 在Music目录中查找同名文件
                        for root, _, files in os.walk(music_dir):
                            for file in files:
                                if file == file_name:
                                    # 找到同名文件
                                    real_path = os.path.join(root, file)
                                    # 计算相对路径
                                    relative_path = os.path.relpath(real_path, project_root)
                                    # 标准化分隔符
                                    file_path = relative_path.replace("\\", "/")
                                    print(f"找到真实文件路径: {file_path}")
                                    feature_data["file_path"] = file_path
                                    break
                            if file_path != feature_data["file_path"]:
                                break
                except Exception as e:
                    print(f"尝试查找真实文件路径时出错: {str(e)}")
            
            # 检查路径是否为绝对路径
            if os.path.isabs(file_path):
                # 如果是绝对路径，尝试转换为相对路径以提高兼容性
                try:
                    # 从特征数据库路径向上两级（utils -> 项目根目录）
                    project_root = os.path.abspath(os.path.join(os.path.dirname(self.database_path), "../.."))
                    file_path = os.path.relpath(file_path, project_root)
                    # 标准化路径分隔符为跨平台格式
                    file_path = file_path.replace('\\', '/')
                    print(f"将绝对路径转换为相对路径: {file_path}")
                    feature_data["file_path"] = file_path
                except Exception as path_error:
                    print(f"路径转换出错: {str(path_error)}")
                    # 保持原始路径
            else:
                # 已经是相对路径，确保路径分隔符是标准化的
                file_path = file_path.replace('\\', '/')
                feature_data["file_path"] = file_path
                print(f"使用相对路径: {file_path}")
            
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