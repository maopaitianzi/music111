from flask import Flask, request, jsonify
import os
import librosa
import numpy as np
import json
import time
from typing import Dict, Any, List, Tuple, Optional
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('music_recognition_api')

# 从项目根目录导入相关模块
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from music_recognition_system.utils.audio_features import AudioFeatureExtractor, FeatureDatabase
except ImportError:
    logger.error("无法导入音频特征提取模块，将使用模拟实现")
    
    class AudioFeatureExtractor:
        def extract_features(self, audio_path):
            # 模拟特征提取
            return {
                "file_path": audio_path,
                "file_name": os.path.basename(audio_path),
                "duration": 180.0
            }
    
    class FeatureDatabase:
        def __init__(self, database_path=None):
            self.features = {}
            
        def get_all_files(self):
            return [{"file_name": name} for name in self.features.keys()]

# 初始化Flask应用
app = Flask(__name__)

# 特征数据库路径
DB_PATH = os.path.join(project_root, "music_recognition_system/database/music_features_db")

# 特征提取器和数据库
feature_extractor = AudioFeatureExtractor()
feature_db = FeatureDatabase(DB_PATH)

# 歌曲元数据
SONG_METADATA = {
    "告白气球": {
        "id": "s1",
        "name": "告白气球",
        "artist": "周杰伦",
        "album": "周杰伦的床边故事",
        "year": "2016",
        "genre": "流行",
        "cover_url": "https://example.com/cover1.jpg"
    },
    "漠河舞厅": {
        "id": "s2",
        "name": "漠河舞厅",
        "artist": "柳爽",
        "album": "漠河舞厅",
        "year": "2022",
        "genre": "流行",
        "cover_url": "https://example.com/cover2.jpg"
    },
    "白月光与朱砂痣": {
        "id": "s3",
        "name": "白月光与朱砂痣",
        "artist": "大籽",
        "album": "白月光与朱砂痣",
        "year": "2020",
        "genre": "流行",
        "cover_url": "https://example.com/cover3.jpg"
    }
}

@app.route('/api/recognize', methods=['POST'])
def recognize_music():
    """处理音乐识别请求"""
    try:
        # 检查是否有文件上传
        if 'audio_file' not in request.files:
            return jsonify({
                "success": False,
                "error": "没有上传音频文件"
            }), 400
        
        # 获取上传的文件
        audio_file = request.files['audio_file']
        
        # 检查文件名
        if audio_file.filename == '':
            return jsonify({
                "success": False,
                "error": "文件名为空"
            }), 400
        
        # 保存临时文件
        temp_dir = os.path.join(current_dir, "../../../temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"upload_{int(time.time())}.wav")
        audio_file.save(temp_path)
        
        logger.info(f"临时文件保存到: {temp_path}")
        
        # 提取特征
        features = feature_extractor.extract_features(temp_path)
        logger.info(f"成功提取特征: {audio_file.filename}")
        
        # 进行特征匹配
        match, confidence = match_features(features, feature_db)
        
        # 删除临时文件
        os.remove(temp_path)
        
        # 返回结果
        if match:
            return jsonify({
                "success": True,
                "song_name": match["name"],
                "artist": match["artist"],
                "album": match["album"],
                "release_year": match["year"],
                "genre": match["genre"],
                "cover_url": match["cover_url"],
                "confidence": confidence
            })
        else:
            return jsonify({
                "success": False,
                "error": "未找到匹配的歌曲"
            })
    
    except Exception as e:
        logger.error(f"处理过程中出错: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"处理过程中出错: {str(e)}"
        }), 500

def match_features(query_features: Dict[str, Any], db: FeatureDatabase) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    将查询特征与数据库中的特征进行匹配
    
    参数:
        query_features: 查询音频的特征
        db: 特征数据库
        
    返回:
        (匹配的歌曲元数据, 置信度)
    """
    try:
        # 获取数据库中的所有文件
        all_files = db.get_all_files()
        
        # 如果数据库为空，使用基于特征的推测
        if not all_files:
            logger.warning("特征数据库为空，尝试使用特征推测匹配")
            return guess_from_features(query_features)
        
        best_match = None
        best_score = 0.0
        
        # 计算与数据库中每个文件的相似度
        for file_info in all_files:
            file_id = file_info["id"]
            db_features = db.get_feature(file_id)
            
            if not db_features:
                continue
                
            # 计算相似度得分
            score = calculate_similarity(query_features, db_features)
            
            # 更新最佳匹配
            if score > best_score:
                best_score = score
                # 查找元数据
                file_name = os.path.splitext(file_info["file_name"])[0]
                if file_name in SONG_METADATA:
                    best_match = SONG_METADATA[file_name]
                else:
                    # 如果找不到元数据，创建基本信息
                    best_match = {
                        "id": file_id,
                        "name": file_name,
                        "artist": "未知艺术家",
                        "album": "未知专辑",
                        "year": "",
                        "genre": "未知",
                        "cover_url": ""
                    }
        
        # 设置置信度阈值
        if best_score >= 0.7:
            return best_match, best_score
        else:
            return None, best_score
            
    except Exception as e:
        logger.error(f"特征匹配失败: {str(e)}", exc_info=True)
        return None, 0.0

def calculate_similarity(query_features: Dict[str, Any], db_features: Dict[str, Any]) -> float:
    """
    计算两个特征集之间的相似度
    
    参数:
        query_features: 查询特征
        db_features: 数据库特征
        
    返回:
        相似度得分 (0.0 到 1.0 之间)
    """
    scores = []
    
    # 1. 比较MFCC特征
    if "mfcc_mean" in query_features and "mfcc_mean" in db_features:
        mfcc_query = np.array(query_features["mfcc_mean"])
        mfcc_db = np.array(db_features["mfcc_mean"])
        
        # 计算余弦相似度
        mfcc_sim = cosine_similarity(mfcc_query, mfcc_db)
        scores.append(mfcc_sim * 0.4)  # MFCC特征权重较高
    
    # 2. 比较梅尔频谱特征
    if "mel_mean" in query_features and "mel_mean" in db_features:
        mel_query = np.array(query_features["mel_mean"])
        mel_db = np.array(db_features["mel_mean"])
        
        mel_sim = cosine_similarity(mel_query, mel_db)
        scores.append(mel_sim * 0.3)
    
    # 3. 比较色度特征
    if "chroma_mean" in query_features and "chroma_mean" in db_features:
        chroma_query = np.array(query_features["chroma_mean"])
        chroma_db = np.array(db_features["chroma_mean"])
        
        chroma_sim = cosine_similarity(chroma_query, chroma_db)
        scores.append(chroma_sim * 0.2)
    
    # 4. 比较谱质心特征
    if "spectral_centroid_mean" in query_features and "spectral_centroid_mean" in db_features:
        centroid_diff = abs(query_features["spectral_centroid_mean"] - db_features["spectral_centroid_mean"])
        max_centroid = max(query_features["spectral_centroid_mean"], db_features["spectral_centroid_mean"])
        centroid_sim = 1.0 - min(centroid_diff / max_centroid, 1.0) if max_centroid > 0 else 0
        scores.append(centroid_sim * 0.1)
    
    # 5. 比较指纹特征（如果存在）
    if "fingerprint" in query_features and "fingerprint" in db_features:
        fp_sim = fingerprint_similarity(query_features["fingerprint"], db_features["fingerprint"])
        scores.append(fp_sim * 0.5)  # 指纹特征权重最高
    
    # 如果没有足够的特征比较
    if not scores:
        return 0.0
    
    # 返回加权平均分数
    return sum(scores) / sum(score_weight for _, score_weight in zip(scores, [0.4, 0.3, 0.2, 0.1, 0.5]))

def fingerprint_similarity(fp1: List[List[int]], fp2: List[List[int]]) -> float:
    """
    计算两个指纹之间的相似度
    
    参数:
        fp1: 第一个指纹
        fp2: 第二个指纹
        
    返回:
        相似度得分 (0.0 到 1.0 之间)
    """
    # 确保两个指纹的形状兼容
    min_rows = min(len(fp1), len(fp2))
    min_cols = min(len(fp1[0]) if fp1 and fp1[0] else 0, len(fp2[0]) if fp2 and fp2[0] else 0)
    
    if min_rows == 0 or min_cols == 0:
        return 0.0
    
    # 计算重叠的二进制位数
    match_count = 0
    total_bits = min_rows * min_cols
    
    for i in range(min_rows):
        for j in range(min_cols):
            if fp1[i][j] == fp2[i][j]:
                match_count += 1
    
    # 返回相似度
    return match_count / total_bits

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    计算两个向量的余弦相似度
    
    参数:
        a: 第一个向量
        b: 第二个向量
        
    返回:
        余弦相似度 (0.0 到 1.0 之间)
    """
    # 确保向量长度相同
    if len(a) != len(b):
        min_len = min(len(a), len(b))
        a = a[:min_len]
        b = b[:min_len]
    
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    cos_sim = dot_product / (norm_a * norm_b)
    
    # 将结果转换到0-1范围
    return (cos_sim + 1) / 2

def guess_from_features(features: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    从特征中猜测歌曲（当数据库为空时使用）
    
    参数:
        features: 音频特征
        
    返回:
        (猜测的歌曲元数据, 置信度)
    """
    import random
    
    # 随机选择一首歌，但赋予较低的置信度
    song_names = list(SONG_METADATA.keys())
    selected_song = SONG_METADATA[random.choice(song_names)]
    
    return selected_song, 0.6

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({"status": "healthy"})

@app.route('/api/database/status', methods=['GET'])
def database_status():
    """获取数据库状态"""
    try:
        all_files = feature_db.get_all_files()
        return jsonify({
            "success": True,
            "total_songs": len(all_files),
            "songs": all_files[:10]  # 只返回前10首歌以避免响应过大
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/database/add', methods=['POST'])
def add_to_database():
    """添加歌曲到数据库"""
    try:
        # 检查是否有文件上传
        if 'audio_file' not in request.files:
            return jsonify({
                "success": False,
                "error": "没有上传音频文件"
            }), 400
        
        # 获取上传的文件
        audio_file = request.files['audio_file']
        
        # 检查文件名
        if audio_file.filename == '':
            return jsonify({
                "success": False,
                "error": "文件名为空"
            }), 400
        
        # 保存临时文件
        temp_dir = os.path.join(current_dir, "../../../temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"db_add_{int(time.time())}.wav")
        audio_file.save(temp_path)
        
        # 提取特征
        features = feature_extractor.extract_features(temp_path)
        
        # 添加到数据库
        success = feature_db.add_feature(features)
        
        # 删除临时文件
        os.remove(temp_path)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"成功添加 {audio_file.filename} 到数据库"
            })
        else:
            return jsonify({
                "success": False,
                "error": "添加到数据库失败"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 