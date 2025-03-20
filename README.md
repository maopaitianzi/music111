# 音乐识别系统

基于深度学习的音乐识别系统，类似于Shazam和网易云音乐听歌识曲功能。通过录制或上传的音频片段，识别出对应的音乐作品。

## 项目概述

本项目实现了一个完整的音乐识别系统，包括以下核心功能：

- 音频录制和上传
- 音频特征提取和指纹生成
- 音乐匹配和识别
- 用户管理和历史记录
- 相似音乐推荐

## 系统架构

系统采用前后端分离的架构，由三个主要部分组成：

- **前端**：用户界面，提供音频录制、上传和结果展示功能
- **后端**：音频处理、特征提取、音乐匹配算法和API服务
- **数据库**：存储音乐指纹、用户数据和识别历史

## 技术栈

### 前端
- React/Vue.js
- Ant Design/Element UI
- Web Audio API

### 后端
- Python
- FastAPI/Flask
- Librosa, PyTorch
- 深度学习模型 (CNN)

### 数据库
- PostgreSQL/MySQL
- MongoDB (用于音频特征存储)
- Redis (缓存)

## 目录结构

```
/
├── frontend/             # 前端代码
├── backend/              # 后端代码
├── database/             # 数据库配置和迁移脚本
├── docs/                 # 文档
└── README.md             # 项目说明
```

## 开发指南

请参阅各目录下的README文件获取详细的开发指南：

- [前端开发指南](frontend/README.md)
- [后端开发指南](backend/README.md)
- [数据库配置指南](database/README.md)
- [完整开发文档](docs/开发文档.md)

## 快速开始

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### 数据库

按照 [数据库配置指南](database/README.md) 设置数据库。

## 核心算法

本系统使用基于卷积神经网络(CNN)的音乐指纹识别算法，处理流程包括：

1. 音频预处理
2. 特征提取 (MFCC, Mel Spectrogram)
3. 指纹生成
4. 数据库匹配
5. 结果排序与返回

详细算法说明请参阅 [开发文档](docs/开发文档.md)。

## 贡献指南

欢迎提交问题报告和功能请求。对于代码贡献，请遵循以下步骤：

1. Fork 本仓库
2. 创建新的分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。 