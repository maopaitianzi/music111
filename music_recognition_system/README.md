# 音乐识别系统

本系统实现了基于音频特征的音乐识别功能，可以识别用户上传的音频片段并提供匹配的歌曲信息。

## 系统架构

系统主要由以下几个部分组成：

- **特征提取模块**：从音频文件中提取特征，包括MFCC、梅尔频谱、色度等特征
- **特征数据库**：存储已知歌曲的特征数据
- **特征匹配模块**：将查询音频与数据库中的特征进行匹配
- **API服务**：提供RESTful API接口，处理用户请求
- **批处理工具**：用于批量处理音频文件，建立特征数据库

## 安装与依赖

系统依赖以下Python库：

```bash
pip install flask numpy librosa scikit-learn tqdm
```

## 使用说明

### 1. 启动API服务

```bash
cd music_recognition_system/backend
python run_api.py
```

服务将在本地5000端口启动。

### 2. API接口说明

#### 2.1 识别音乐

- **URL**: `/api/recognize`
- **方法**: POST
- **参数**: 
  - `audio_file`: 要识别的音频文件（表单数据）
- **返回示例**:
  ```json
  {
    "success": true,
    "song_name": "告白气球",
    "artist": "周杰伦",
    "album": "周杰伦的床边故事",
    "release_year": "2016",
    "genre": "流行",
    "cover_url": "https://example.com/cover1.jpg",
    "confidence": 0.95
  }
  ```

#### 2.2 数据库状态

- **URL**: `/api/database/status`
- **方法**: GET
- **返回示例**:
  ```json
  {
    "success": true,
    "total_songs": 100,
    "songs": [
      {
        "id": "a1b2c3",
        "file_name": "example.mp3",
        "duration": 180.5,
        "added_time": "2023-01-01 12:00:00"
      }
    ]
  }
  ```

#### 2.3 添加歌曲到数据库

- **URL**: `/api/database/add`
- **方法**: POST
- **参数**: 
  - `audio_file`: 要添加的音频文件（表单数据）
- **返回示例**:
  ```json
  {
    "success": true,
    "message": "成功添加 example.mp3 到数据库"
  }
  ```

### 3. 批量处理工具

系统提供了批量处理工具，用于处理音频文件并建立特征数据库。

#### 3.1 创建元数据模板

```bash
cd music_recognition_system
python utils/batch_process.py create-metadata /path/to/music/folder --output metadata.json
```

这将为音乐文件夹中的所有音频文件生成元数据模板，可以手动编辑添加正确的歌曲信息。

#### 3.2 批量处理音频文件

```bash
cd music_recognition_system
python utils/batch_process.py process /path/to/music/folder --metadata metadata.json
```

这将处理音乐文件夹中的所有音频文件，提取特征并添加到数据库。

## 音乐识别算法

系统使用了多种音频特征进行匹配，包括：

1. **MFCC特征**：梅尔频率倒谱系数，捕捉音频的音色特征
2. **梅尔频谱特征**：表示音频在不同频率段的能量分布
3. **色度特征**：表示音乐的和声内容
4. **谱质心**：音频频谱的"重心"，反映音色的明亮度
5. **音频指纹**：基于梅尔频谱生成的二进制特征，用于快速匹配

算法使用加权相似度计算方法，综合考虑多种特征的匹配程度，得出最终的匹配结果。

## 性能和限制

- 当前版本最佳适用于10秒以上的音频片段
- 系统对背景噪音有一定的抵抗力，但强噪音环境可能影响识别准确率
- 识别准确率与特征数据库的规模和质量密切相关

## 未来改进

- 实现指纹索引，提高大规模数据库的搜索效率
- 添加实时音频流识别功能
- 改进噪声鲁棒性和部分匹配能力
- 增加自动元数据获取功能
