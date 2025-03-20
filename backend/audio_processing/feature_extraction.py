"""
音频特征提取模块

该模块提供音频信号特征提取的功能，包括:
- MFCC (梅尔频率倒谱系数)
- Mel频谱图
- 色度图
- 零交叉率
- 频谱质心
等音频特征的计算和处理。
"""

import numpy as np
import librosa
import torch
from typing import Dict, List, Tuple, Union, Optional


class FeatureExtractor:
    """音频特征提取器类"""
    
    def __init__(self, 
                 sample_rate: int = 22050,
                 n_fft: int = 2048,
                 hop_length: int = 512,
                 n_mels: int = 128,
                 n_mfcc: int = 20):
        """
        初始化特征提取器
        
        参数:
            sample_rate: 采样率
            n_fft: FFT窗口大小
            hop_length: 帧移
            n_mels: Mel滤波器组数量
            n_mfcc: MFCC系数数量
        """
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels
        self.n_mfcc = n_mfcc
    
    def extract_features(self, 
                         audio_signal: np.ndarray, 
                         features: List[str] = ['mfcc']) -> Dict[str, np.ndarray]:
        """
        从音频信号中提取指定的特征
        
        参数:
            audio_signal: 音频信号
            features: 需要提取的特征列表
            
        返回:
            包含所有提取特征的字典
        """
        result = {}
        
        # 确保音频长度足够
        if len(audio_signal) < self.n_fft:
            # 如果音频太短，使用零填充
            audio_signal = np.pad(audio_signal, (0, self.n_fft - len(audio_signal)), 'constant')
        
        for feature_name in features:
            if feature_name == 'mfcc':
                result['mfcc'] = self._extract_mfcc(audio_signal)
            elif feature_name == 'mel_spectrogram':
                result['mel_spectrogram'] = self._extract_mel_spectrogram(audio_signal)
            elif feature_name == 'chroma':
                result['chroma'] = self._extract_chroma(audio_signal)
            elif feature_name == 'zcr':
                result['zcr'] = self._extract_zero_crossing_rate(audio_signal)
            elif feature_name == 'spectral_centroid':
                result['spectral_centroid'] = self._extract_spectral_centroid(audio_signal)
            elif feature_name == 'all':
                # 提取所有特征
                result['mfcc'] = self._extract_mfcc(audio_signal)
                result['mel_spectrogram'] = self._extract_mel_spectrogram(audio_signal)
                result['chroma'] = self._extract_chroma(audio_signal)
                result['zcr'] = self._extract_zero_crossing_rate(audio_signal)
                result['spectral_centroid'] = self._extract_spectral_centroid(audio_signal)
        
        return result
    
    def _extract_mfcc(self, audio_signal: np.ndarray) -> np.ndarray:
        """
        提取MFCC特征
        
        参数:
            audio_signal: 音频信号
            
        返回:
            MFCC特征矩阵
        """
        mfccs = librosa.feature.mfcc(
            y=audio_signal, 
            sr=self.sample_rate, 
            n_mfcc=self.n_mfcc,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )
        # 标准化MFCC
        mfccs = librosa.util.normalize(mfccs, axis=1)
        return mfccs
    
    def _extract_mel_spectrogram(self, audio_signal: np.ndarray) -> np.ndarray:
        """
        提取Mel频谱图特征
        
        参数:
            audio_signal: 音频信号
            
        返回:
            Mel频谱图特征矩阵
        """
        mel_spec = librosa.feature.melspectrogram(
            y=audio_signal,
            sr=self.sample_rate,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            n_mels=self.n_mels
        )
        # 转换为分贝单位
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        return mel_spec_db
    
    def _extract_chroma(self, audio_signal: np.ndarray) -> np.ndarray:
        """
        提取色度图特征
        
        参数:
            audio_signal: 音频信号
            
        返回:
            色度图特征矩阵
        """
        chroma = librosa.feature.chroma_stft(
            y=audio_signal,
            sr=self.sample_rate,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )
        return chroma
    
    def _extract_zero_crossing_rate(self, audio_signal: np.ndarray) -> np.ndarray:
        """
        提取零交叉率特征
        
        参数:
            audio_signal: 音频信号
            
        返回:
            零交叉率特征向量
        """
        zcr = librosa.feature.zero_crossing_rate(
            y=audio_signal,
            frame_length=self.n_fft,
            hop_length=self.hop_length
        )
        return zcr
    
    def _extract_spectral_centroid(self, audio_signal: np.ndarray) -> np.ndarray:
        """
        提取频谱质心特征
        
        参数:
            audio_signal: 音频信号
            
        返回:
            频谱质心特征向量
        """
        centroid = librosa.feature.spectral_centroid(
            y=audio_signal,
            sr=self.sample_rate,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )
        return centroid


def extract_batch_features(audio_batch: List[np.ndarray], 
                          feature_names: List[str] = ['mfcc'],
                          sample_rate: int = 22050) -> List[Dict[str, np.ndarray]]:
    """
    批量提取音频特征
    
    参数:
        audio_batch: 音频信号列表
        feature_names: 需要提取的特征名称列表
        sample_rate: 采样率
        
    返回:
        包含每个音频特征的字典列表
    """
    extractor = FeatureExtractor(sample_rate=sample_rate)
    features_list = []
    
    for audio in audio_batch:
        features = extractor.extract_features(audio, feature_names)
        features_list.append(features)
    
    return features_list


def normalize_features(features: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """
    对特征进行标准化处理
    
    参数:
        features: 特征字典
        
    返回:
        标准化后的特征字典
    """
    normalized_features = {}
    
    for name, feature in features.items():
        if feature.ndim > 1:
            # 对多维特征，沿第一个轴标准化
            normalized_features[name] = librosa.util.normalize(feature, axis=1)
        else:
            # 对一维特征，直接标准化
            mean = np.mean(feature)
            std = np.std(feature)
            normalized_features[name] = (feature - mean) / (std if std > 0 else 1)
    
    return normalized_features


def convert_to_tensor(features: Dict[str, np.ndarray]) -> Dict[str, torch.Tensor]:
    """
    将NumPy数组特征转换为PyTorch张量
    
    参数:
        features: 特征字典
        
    返回:
        张量特征字典
    """
    tensor_features = {}
    
    for name, feature in features.items():
        tensor_features[name] = torch.from_numpy(feature).float()
    
    return tensor_features


# 使用示例
if __name__ == "__main__":
    # 加载音频文件
    audio_file = "example.wav"
    audio, sr = librosa.load(audio_file, sr=22050)
    
    # 创建特征提取器
    extractor = FeatureExtractor(sample_rate=sr)
    
    # 提取多种特征
    features = extractor.extract_features(
        audio, 
        features=['mfcc', 'mel_spectrogram', 'chroma']
    )
    
    # 标准化特征
    norm_features = normalize_features(features)
    
    # 转换为PyTorch张量
    tensor_features = convert_to_tensor(norm_features)
    
    # 打印特征形状
    for name, feature in tensor_features.items():
        print(f"{name} shape: {feature.shape}") 