"""
音乐识别CNN模型定义

该模块定义了用于音乐识别的CNN模型架构，包括:
- 基础CNN模型
- 音乐指纹提取模型
- 多尺度特征融合模型
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Union


class ConvBlock(nn.Module):
    """卷积块，包含卷积层、批归一化、激活函数和可选的池化层"""
    
    def __init__(self, 
                 in_channels: int, 
                 out_channels: int,
                 kernel_size: int = 3,
                 stride: int = 1,
                 padding: int = 1,
                 pool_size: int = 2,
                 use_pool: bool = True):
        """
        初始化卷积块
        
        参数:
            in_channels: 输入通道数
            out_channels: 输出通道数
            kernel_size: 卷积核大小
            stride: 卷积步长
            padding: 卷积填充
            pool_size: 池化层大小
            use_pool: 是否使用池化
        """
        super(ConvBlock, self).__init__()
        
        self.conv = nn.Conv2d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=kernel_size,
            stride=stride,
            padding=padding
        )
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.use_pool = use_pool
        
        if use_pool:
            self.pool = nn.MaxPool2d(kernel_size=pool_size)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        参数:
            x: 输入张量 [batch_size, in_channels, height, width]
            
        返回:
            卷积块输出张量
        """
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)
        
        if self.use_pool:
            x = self.pool(x)
        
        return x


class MusicCNN(nn.Module):
    """基础音乐识别CNN模型"""
    
    def __init__(self,
                 input_channels: int = 1,
                 num_classes: int = 1000,
                 embedding_dim: int = 128):
        """
        初始化音乐识别CNN模型
        
        参数:
            input_channels: 输入通道数
            num_classes: 音乐类别数
            embedding_dim: 嵌入向量维度
        """
        super(MusicCNN, self).__init__()
        
        # 卷积层
        self.conv_layers = nn.Sequential(
            ConvBlock(input_channels, 32, kernel_size=3, padding=1),
            ConvBlock(32, 64, kernel_size=3, padding=1),
            ConvBlock(64, 128, kernel_size=3, padding=1),
            ConvBlock(128, 256, kernel_size=3, padding=1),
            ConvBlock(256, 512, kernel_size=3, padding=1, use_pool=False)
        )
        
        # 全局平均池化
        self.global_pool = nn.AdaptiveAvgPool2d(1)
        
        # 嵌入层
        self.embedding = nn.Linear(512, embedding_dim)
        
        # 分类层
        self.fc = nn.Linear(embedding_dim, num_classes)
        
        # Dropout层，防止过拟合
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, x: torch.Tensor, extract_embedding: bool = False) -> Union[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        前向传播
        
        参数:
            x: 输入张量 [batch_size, channels, height, width]
            extract_embedding: 是否提取嵌入向量
            
        返回:
            如果extract_embedding为True，返回(logits, embedding)
            否则返回logits
        """
        # 卷积层特征提取
        x = self.conv_layers(x)
        
        # 全局平均池化
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        
        # 嵌入层
        embedding = self.embedding(x)
        
        # Dropout
        x = self.dropout(embedding)
        
        # 分类层
        logits = self.fc(x)
        
        if extract_embedding:
            return logits, embedding
        else:
            return logits


class MultiScaleCNN(nn.Module):
    """多尺度特征融合CNN模型"""
    
    def __init__(self,
                 input_channels: int = 1,
                 num_classes: int = 1000,
                 embedding_dim: int = 128):
        """
        初始化多尺度特征融合CNN模型
        
        参数:
            input_channels: 输入通道数
            num_classes: 音乐类别数
            embedding_dim: 嵌入向量维度
        """
        super(MultiScaleCNN, self).__init__()
        
        # 小尺度卷积块
        self.small_scale = nn.Sequential(
            ConvBlock(input_channels, 32, kernel_size=3, padding=1),
            ConvBlock(32, 64, kernel_size=3, padding=1)
        )
        
        # 中尺度卷积块
        self.medium_scale = nn.Sequential(
            ConvBlock(input_channels, 32, kernel_size=5, padding=2),
            ConvBlock(32, 64, kernel_size=5, padding=2)
        )
        
        # 大尺度卷积块
        self.large_scale = nn.Sequential(
            ConvBlock(input_channels, 32, kernel_size=7, padding=3),
            ConvBlock(32, 64, kernel_size=7, padding=3)
        )
        
        # 融合后的卷积层
        self.fusion_layers = nn.Sequential(
            ConvBlock(64*3, 128, kernel_size=3, padding=1),
            ConvBlock(128, 256, kernel_size=3, padding=1),
            ConvBlock(256, 512, kernel_size=3, padding=1, use_pool=False)
        )
        
        # 全局平均池化
        self.global_pool = nn.AdaptiveAvgPool2d(1)
        
        # 嵌入层
        self.embedding = nn.Linear(512, embedding_dim)
        
        # 分类层
        self.fc = nn.Linear(embedding_dim, num_classes)
        
        # Dropout层
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, x: torch.Tensor, extract_embedding: bool = False) -> Union[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        前向传播
        
        参数:
            x: 输入张量 [batch_size, channels, height, width]
            extract_embedding: 是否提取嵌入向量
            
        返回:
            如果extract_embedding为True，返回(logits, embedding)
            否则返回logits
        """
        # 多尺度特征提取
        x_small = self.small_scale(x)
        x_medium = self.medium_scale(x)
        x_large = self.large_scale(x)
        
        # 特征融合
        x_fusion = torch.cat([x_small, x_medium, x_large], dim=1)
        
        # 融合后特征提取
        x = self.fusion_layers(x_fusion)
        
        # 全局平均池化
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        
        # 嵌入层
        embedding = self.embedding(x)
        
        # Dropout
        x = self.dropout(embedding)
        
        # 分类层
        logits = self.fc(x)
        
        if extract_embedding:
            return logits, embedding
        else:
            return logits


class FingerprintCNN(nn.Module):
    """音乐指纹提取CNN模型"""
    
    def __init__(self,
                 input_channels: int = 1,
                 embedding_dim: int = 256):
        """
        初始化音乐指纹提取CNN模型
        
        参数:
            input_channels: 输入通道数
            embedding_dim: 指纹向量维度
        """
        super(FingerprintCNN, self).__init__()
        
        # 使用深度可分离卷积提高效率
        self.depthwise_separable_conv1 = nn.Sequential(
            nn.Conv2d(input_channels, input_channels, kernel_size=3, padding=1, groups=input_channels),
            nn.Conv2d(input_channels, 32, kernel_size=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2)
        )
        
        self.depthwise_separable_conv2 = nn.Sequential(
            nn.Conv2d(32, 32, kernel_size=3, padding=1, groups=32),
            nn.Conv2d(32, 64, kernel_size=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2)
        )
        
        self.depthwise_separable_conv3 = nn.Sequential(
            nn.Conv2d(64, 64, kernel_size=3, padding=1, groups=64),
            nn.Conv2d(64, 128, kernel_size=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2)
        )
        
        self.depthwise_separable_conv4 = nn.Sequential(
            nn.Conv2d(128, 128, kernel_size=3, padding=1, groups=128),
            nn.Conv2d(128, 256, kernel_size=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2)
        )
        
        # 全局平均池化
        self.global_pool = nn.AdaptiveAvgPool2d(1)
        
        # 嵌入层，生成音乐指纹
        self.embedding = nn.Linear(256, embedding_dim)
        
        # L2标准化
        self.l2_norm = lambda x: F.normalize(x, p=2, dim=1)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        参数:
            x: 输入张量 [batch_size, channels, height, width]
            
        返回:
            音乐指纹向量 [batch_size, embedding_dim]
        """
        # 特征提取
        x = self.depthwise_separable_conv1(x)
        x = self.depthwise_separable_conv2(x)
        x = self.depthwise_separable_conv3(x)
        x = self.depthwise_separable_conv4(x)
        
        # 全局平均池化
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        
        # 生成指纹向量
        fingerprint = self.embedding(x)
        
        # L2标准化
        fingerprint = self.l2_norm(fingerprint)
        
        return fingerprint


# 使用示例
if __name__ == "__main__":
    # 创建模型
    basic_model = MusicCNN(input_channels=1, num_classes=1000)
    multi_scale_model = MultiScaleCNN(input_channels=1, num_classes=1000)
    fingerprint_model = FingerprintCNN(input_channels=1, embedding_dim=256)
    
    # 创建示例输入
    batch_size = 16
    channels = 1
    height = 128
    width = 646  # 例如，使用MFCC特征，20个MFCC系数，646帧
    x = torch.randn(batch_size, channels, height, width)
    
    # 前向传播
    output1 = basic_model(x)
    output2 = multi_scale_model(x)
    fingerprint = fingerprint_model(x)
    
    # 打印输出形状
    print(f"Basic CNN output shape: {output1.shape}")
    print(f"Multi-Scale CNN output shape: {output2.shape}")
    print(f"Fingerprint shape: {fingerprint.shape}") 