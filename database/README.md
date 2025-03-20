# 音乐识别系统 - 数据库

此目录包含音乐识别系统的数据库相关配置和迁移脚本。

## 数据库技术栈

- 关系型数据库：PostgreSQL/MySQL
- 非关系型数据库：MongoDB（用于音频特征存储）
- 缓存：Redis
- 迁移工具：Alembic

## 目录结构

```
database/
  ├── migrations/            # 数据库迁移脚本
  │   ├── versions/          # 迁移版本
  │   ├── env.py             # 迁移环境
  │   └── script.py.mako     # 迁移脚本模板
  ├── scripts/               # 数据库脚本
  │   ├── backup.sh          # 备份脚本
  │   ├── restore.sh         # 恢复脚本
  │   └── seed_data.py       # 初始数据填充
  ├── schemas/               # 数据库模式
  │   ├── relational/        # 关系型数据库模式
  │   └── nosql/             # NoSQL数据库模式
  ├── config/                # 数据库配置
  │   ├── postgresql.conf    # PostgreSQL配置
  │   ├── mongodb.conf       # MongoDB配置
  │   └── redis.conf         # Redis配置
  ├── docker/                # 数据库Docker配置
  │   ├── docker-compose.yml # Docker Compose配置
  │   └── init.sql           # 初始化SQL
  ├── README.md              # 说明文档
  └── requirements.txt       # 数据库相关依赖
```

## 数据模型

### 1. 音乐元数据表 (Music)

存储音乐的基本信息：

```
Music:
  - id: INT (PK)
  - title: VARCHAR
  - artist: VARCHAR
  - album: VARCHAR
  - release_date: DATE
  - genre: VARCHAR
  - duration: INT (秒)
  - file_path: VARCHAR
  - cover_image: VARCHAR
```

### 2. 音频特征表 (AudioFingerprint)

存储音乐指纹数据：

```
AudioFingerprint:
  - id: INT (PK)
  - music_id: INT (FK)
  - fingerprint_data: BLOB/JSON
  - created_at: TIMESTAMP
```

### 3. 用户表 (User)

存储用户信息：

```
User:
  - id: INT (PK)
  - username: VARCHAR
  - email: VARCHAR
  - password: VARCHAR (加密)
  - created_at: TIMESTAMP
  - last_login: TIMESTAMP
```

### 4. 识别历史表 (RecognitionHistory)

存储用户识别历史：

```
RecognitionHistory:
  - id: INT (PK)
  - user_id: INT (FK, 可为NULL)
  - music_id: INT (FK)
  - timestamp: TIMESTAMP
  - confidence: FLOAT
  - audio_snippet: VARCHAR (可选)
```

## 开发指南

### 1. 数据库配置

1. 关系型数据库 (PostgreSQL/MySQL)：
   ```
   # 创建数据库
   CREATE DATABASE music_recognition;
   
   # 创建用户
   CREATE USER music_app WITH PASSWORD 'password';
   
   # 授权
   GRANT ALL PRIVILEGES ON DATABASE music_recognition TO music_app;
   ```

2. MongoDB配置：
   ```
   # 创建数据库
   use music_fingerprints
   
   # 创建集合
   db.createCollection("fingerprints")
   ```

3. Redis配置：
   ```
   # 配置示例
   maxmemory 256mb
   maxmemory-policy allkeys-lru
   ```

### 2. 数据库迁移

使用Alembic进行迁移管理：

```
# 初始化迁移
alembic init migrations

# 创建迁移
alembic revision --autogenerate -m "Initial migration"

# 应用迁移
alembic upgrade head
```

### 3. 数据库备份与恢复

使用提供的脚本：

```
# 备份
./scripts/backup.sh

# 恢复
./scripts/restore.sh backup_file.sql
```

## 性能优化

1. 索引策略：
   - 对频繁查询的字段创建索引
   - 音乐指纹数据使用特殊索引结构

2. 查询优化：
   - 使用预编译查询
   - 实现查询缓存机制

3. 存储优化：
   - 音乐指纹数据使用压缩存储
   - 大型二进制数据考虑外部存储 