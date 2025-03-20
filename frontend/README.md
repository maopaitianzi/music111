# 音乐识别系统 - 前端

此目录包含音乐识别系统的前端代码。

## 技术栈

- 框架：React/Vue.js
- UI库：Ant Design/Element UI
- 音频处理：Web Audio API
- 状态管理：Redux/Vuex

## 目录结构

```
frontend/
  ├── public/           # 静态资源
  ├── src/              # 源代码
  │   ├── assets/       # 图片、字体等资源
  │   ├── components/   # 可复用组件
  │   ├── pages/        # 页面组件
  │   ├── services/     # API服务
  │   ├── store/        # 状态管理
  │   ├── utils/        # 工具函数
  │   ├── App.js        # 应用入口
  │   └── main.js       # 主入口文件
  ├── .env              # 环境变量
  ├── package.json      # 项目依赖
  └── README.md         # 说明文档
```

## 开发指南

1. 安装依赖：
   ```
   npm install
   ```

2. 启动开发服务器：
   ```
   npm run dev
   ```

3. 构建生产版本：
   ```
   npm run build
   ```

## 主要功能

- 音频录制与上传界面
- 识别结果展示
- 用户登录与注册
- 历史记录管理
- 个人收藏

## 核心组件

- AudioRecorder：音频录制组件
- AudioUploader：音频上传组件
- MusicPlayer：音乐播放器
- RecognitionResult：识别结果展示
- HistoryList：历史记录列表 