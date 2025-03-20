# 音乐识别系统 - 后端

此目录包含音乐识别系统的后端代码。

## 技术栈

- 编程语言：Python
- Web框架：FastAPI/Flask
- 音频处理：librosa, pytorch
- 特征提取：MFCC, Mel Spectrogram
- 音乐指纹算法：卷积神经网络 (CNN)
- 数据库ORM：SQLAlchemy

## 目录结构

```
backend/
  ├── app/                  # 应用核心代码
  │   ├── api/              # API路由
  │   │   ├── endpoints/    # API端点
  │   │   └── deps.py       # 依赖项
  │   ├── core/             # 核心配置
  │   │   ├── config.py     # 配置文件
  │   │   └── security.py   # 安全相关
  │   ├── db/               # 数据库
  │   │   ├── base.py       # 基础模型
  │   │   └── session.py    # 数据库会话
  │   ├── models/           # 数据模型
  │   ├── schemas/          # Pydantic模式
  │   ├── services/         # 业务逻辑
  │   │   ├── recognition/  # 音乐识别服务
  │   │   └── user/         # 用户服务
  │   └── utils/            # 实用工具
  ├── audio_processing/     # 音频处理
  │   ├── feature_extraction.py  # 特征提取
  │   ├── fingerprinting.py      # 指纹生成
  │   └── preprocessing.py       # 音频预处理
  ├── ml_models/            # 机器学习模型
  │   ├── cnn_model.py      # CNN模型定义
  │   ├── training.py       # 模型训练
  │   └── inference.py      # 推理代码
  ├── tests/                # 测试代码
  ├── requirements.txt      # 依赖项
  ├── main.py               # 应用入口
  └── README.md             # 说明文档
```

## 开发指南

1. 创建虚拟环境：
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

3. 启动开发服务器：
   ```
   uvicorn main:app --reload
   ```

## 主要功能

- 音频处理和特征提取
- 音乐指纹生成与匹配
- 用户认证与授权
- 历史记录管理
- 数据库交互

## 核心API

- `/api/recognize` - 上传音频识别
- `/api/recognize/record` - 录制音频识别
- `/api/users/*` - 用户管理
- `/api/history/*` - 历史记录管理

## 音频处理流程

1. 音频预处理（采样率转换、降噪等）
2. 特征提取（MFCC, Mel Spectrogram）
3. 指纹生成
4. 数据库匹配
5. 结果排序与返回 