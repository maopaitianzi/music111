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

@app.route('/api', methods=['GET'])
def api_index():
    """API根路径，返回可用端点信息"""
    return jsonify({
        "status": "API服务正在运行",
        "available_endpoints": [
            {"path": "/api/health", "method": "GET", "description": "健康检查"},
            {"path": "/api/database/status", "method": "GET", "description": "获取数据库状态"},
            {"path": "/api/database/add", "method": "POST", "description": "添加歌曲到数据库"},
            {"path": "/api/recognize", "method": "POST", "description": "识别音乐"}
        ],
        "version": "1.0.0"
    })

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
        match, confidence, feature_matches = match_features(features, feature_db)
        
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
                "confidence": confidence,
                "feature_matches": feature_matches
            })
        else:
            return jsonify({
                "success": False,
                "error": "未找到匹配的歌曲",
                "confidence": confidence,
                "feature_matches": feature_matches
            })
    
    except Exception as e:
        logger.error(f"处理过程中出错: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"处理过程中出错: {str(e)}"
        }), 500

def match_features(query_features: Dict[str, Any], db: FeatureDatabase) -> Tuple[Optional[Dict[str, Any]], float, Dict[str, float]]:
    """
    将查询特征与数据库中的特征进行匹配
    
    参数:
        query_features: 查询音频的特征
        db: 特征数据库
        
    返回:
        (匹配的歌曲元数据, 置信度, 特征匹配分数)
    """
    try:
        # 获取数据库中的所有文件
        all_files = db.get_all_files()
        
        # 如果数据库为空，使用基于特征的推测
        if not all_files:
            logger.warning("特征数据库为空，尝试使用特征推测匹配")
            guess_result, confidence, feature_scores = guess_from_features(query_features)
            return guess_result, confidence, feature_scores
        
        best_match = None
        best_score = 0.0
        best_feature_scores = {}
        
        # 计算与数据库中每个文件的相似度
        for file_info in all_files:
            file_id = file_info.get("id")
            if not file_id:
                continue
                
            db_features = db.get_feature(file_id)
            
            if not db_features:
                continue
                
            # 计算相似度得分和详细特征分数
            score, feature_scores = calculate_similarity_with_details(query_features, db_features)
            
            # 更新最佳匹配
            if score > best_score:
                best_score = score
                best_feature_scores = feature_scores
                
                # 查找元数据
                file_name = os.path.splitext(file_info.get("file_name", ""))[0]
                if file_name in SONG_METADATA:
                    best_match = SONG_METADATA[file_name]
                else:
                    # 如果找不到元数据，使用默认值
                    best_match = {
                        "id": file_id,
                        "name": file_info.get("song_name", "未知歌曲"),
                        "artist": file_info.get("author", "未知艺术家"),
                        "album": "未知专辑",
                        "year": "",
                        "genre": "未知",
                        "cover_url": ""
                    }
        
        # 设置置信度阈值 - 降低阈值使识别更宽松
        if best_score >= 0.5:  # 原来是0.7，现在降低到0.5
            return best_match, best_score, best_feature_scores
        else:
            return None, best_score, best_feature_scores
            
    except Exception as e:
        logger.error(f"特征匹配失败: {str(e)}", exc_info=True)
        return None, 0.0, {}

def calculate_similarity_with_details(query_features: Dict[str, Any], db_features: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """
    计算两个特征集之间的相似度，同时返回详细的特征匹配分数
    
    参数:
        query_features: 查询特征
        db_features: 数据库特征
        
    返回:
        (总相似度得分, 详细特征分数字典)
    """
    scores = []
    feature_scores = {}
    
    # 特征权重 - 为不同特征设置不同权重
    feature_weights = {
        "mfcc": 1.0,           # MFCC特征 (基本音色)
        "mfcc_delta": 0.8,     # MFCC一阶导数 (音色变化)
        "mel": 0.7,            # Mel频谱特征
        "chroma": 0.9,         # 色度特征 (音调相关)
        "spectral": 0.6,       # 频谱特征
        "rhythm": 0.8,         # 节奏特征
        "tonal": 0.85,         # 调性特征
        "energy": 0.5,         # 能量分布
        "fingerprint": 1.2     # 音频指纹 (最高权重)
    }
    
    # 1. 比较MFCC特征
    if "mfcc_mean" in query_features and "mfcc_mean" in db_features:
        mfcc_query = np.array(query_features["mfcc_mean"])
        mfcc_db = np.array(db_features["mfcc_mean"])
        
        # 确保两个特征向量长度相同
        min_length = min(len(mfcc_query), len(mfcc_db))
        if min_length > 0:
            mfcc_query = mfcc_query[:min_length]
            mfcc_db = mfcc_db[:min_length]
            
            # 计算余弦相似度
            mfcc_sim = cosine_similarity(mfcc_query, mfcc_db)
            feature_scores["mfcc"] = float(mfcc_sim)
            scores.append(mfcc_sim * feature_weights["mfcc"])
            
            # 如果有标准差信息，也计算其相似度
            if "mfcc_std" in query_features and "mfcc_std" in db_features:
                std_query = np.array(query_features["mfcc_std"])[:min_length]
                std_db = np.array(db_features["mfcc_std"])[:min_length]
                std_sim = cosine_similarity(std_query, std_db)
                feature_scores["mfcc_std"] = float(std_sim)
                scores.append(std_sim * feature_weights["mfcc"] * 0.5)
                
            # 比较MFCC偏度特征
            if "mfcc_skew" in query_features and "mfcc_skew" in db_features:
                skew_query = np.array(query_features["mfcc_skew"])[:min_length]
                skew_db = np.array(db_features["mfcc_skew"])[:min_length]
                skew_sim = cosine_similarity(skew_query, skew_db)
                feature_scores["mfcc_skew"] = float(skew_sim)
                scores.append(skew_sim * feature_weights["mfcc_delta"])
    
    # 2. 比较Mel频谱特征
    if "mel_mean" in query_features and "mel_mean" in db_features:
        mel_query = np.array(query_features["mel_mean"])
        mel_db = np.array(db_features["mel_mean"])
        
        min_length = min(len(mel_query), len(mel_db))
        if min_length > 0:
            mel_query = mel_query[:min_length]
            mel_db = mel_db[:min_length]
            
            mel_sim = cosine_similarity(mel_query, mel_db)
            feature_scores["mel"] = float(mel_sim)
            scores.append(mel_sim * feature_weights["mel"])
            
            # 比较Mel频谱偏度
            if "mel_skew" in query_features and "mel_skew" in db_features:
                mel_skew_query = np.array(query_features["mel_skew"])[:min_length]
                mel_skew_db = np.array(db_features["mel_skew"])[:min_length]
                mel_skew_sim = cosine_similarity(mel_skew_query, mel_skew_db)
                feature_scores["mel_skew"] = float(mel_skew_sim)
                scores.append(mel_skew_sim * feature_weights["mel"] * 0.7)
    
    # 3. 比较色度特征
    if "chroma_mean" in query_features and "chroma_mean" in db_features:
        chroma_query = np.array(query_features["chroma_mean"])
        chroma_db = np.array(db_features["chroma_mean"])
        
        min_length = min(len(chroma_query), len(chroma_db))
        if min_length > 0:
            chroma_query = chroma_query[:min_length]
            chroma_db = chroma_db[:min_length]
            
            chroma_sim = cosine_similarity(chroma_query, chroma_db)
            feature_scores["chroma"] = float(chroma_sim)
            scores.append(chroma_sim * feature_weights["chroma"])
    
    # 4. 比较谱质心轮廓特征
    if "centroid_profile" in query_features and "centroid_profile" in db_features:
        profile_query = np.array(query_features["centroid_profile"])
        profile_db = np.array(db_features["centroid_profile"])
        
        min_length = min(len(profile_query), len(profile_db))
        if min_length > 0:
            profile_query = profile_query[:min_length]
            profile_db = profile_db[:min_length]
            
            profile_sim = cosine_similarity(profile_query, profile_db)
            feature_scores["spectral_profile"] = float(profile_sim)
            scores.append(profile_sim * feature_weights["spectral"])
    
    # 5. 比较节奏特征
    if "tempo" in query_features and "tempo" in db_features:
        # 计算节奏差异 - 使用相对差异
        query_tempo = query_features["tempo"]
        db_tempo = db_features["tempo"]
        
        # 节奏相似度 - 考虑音乐通常在73-180 BPM之间
        tempo_diff = abs(query_tempo - db_tempo)
        tempo_range = 180 - 73
        tempo_sim = max(0.0, 1.0 - tempo_diff / tempo_range)
        feature_scores["tempo"] = float(tempo_sim)
        scores.append(tempo_sim * feature_weights["rhythm"] * 0.5)
        
        # 节奏脉冲清晰度
        if "pulse_clarity" in query_features and "pulse_clarity" in db_features:
            pc_query = query_features["pulse_clarity"]
            pc_db = db_features["pulse_clarity"]
            pc_sim = 1.0 - min(1.0, abs(pc_query - pc_db) / max(pc_query, pc_db, 0.001))
            feature_scores["pulse_clarity"] = float(pc_sim)
            scores.append(pc_sim * feature_weights["rhythm"] * 0.3)
    
    # 6. 比较调性特征
    if "tonal_features_mean" in query_features and "tonal_features_mean" in db_features:
        tonal_query = np.array(query_features["tonal_features_mean"])
        tonal_db = np.array(db_features["tonal_features_mean"])
        
        min_length = min(len(tonal_query), len(tonal_db))
        if min_length > 0:
            tonal_query = tonal_query[:min_length]
            tonal_db = tonal_db[:min_length]
            
            tonal_sim = cosine_similarity(tonal_query, tonal_db)
            feature_scores["tonal"] = float(tonal_sim)
            scores.append(tonal_sim * feature_weights["tonal"])
    
    # 7. 比较能量分布特征
    if "energy_distribution" in query_features and "energy_distribution" in db_features:
        energy_query = np.array(query_features["energy_distribution"])
        energy_db = np.array(db_features["energy_distribution"])
        
        min_length = min(len(energy_query), len(energy_db))
        if min_length > 0:
            energy_query = energy_query[:min_length]
            energy_db = energy_db[:min_length]
            
            energy_sim = cosine_similarity(energy_query, energy_db)
            feature_scores["energy"] = float(energy_sim)
            scores.append(energy_sim * feature_weights["energy"])
    
    # 8. 比较指纹特征 (最重要的特征)
    if "fingerprint" in query_features and "fingerprint" in db_features:
        fp_sim = fingerprint_similarity(query_features["fingerprint"], db_features["fingerprint"])
        feature_scores["fingerprint"] = float(fp_sim)
        scores.append(fp_sim * feature_weights["fingerprint"])
    
    # 如果没有任何得分，返回0
    if not scores:
        return 0.0, feature_scores
    
    # 计算最终相似度得分
    final_score = sum(scores) / len(scores)
    
    return final_score, feature_scores

def calculate_similarity(query_features: Dict[str, Any], db_features: Dict[str, Any]) -> float:
    """
    计算两个特征集之间的相似度
    
    参数:
        query_features: 查询特征
        db_features: 数据库特征
        
    返回:
        相似度得分 (0.0 到 1.0 之间)
    """
    # 调用有详细信息的函数但只返回总分
    score, _ = calculate_similarity_with_details(query_features, db_features)
    return score

def fingerprint_similarity(fp1: List[List[int]], fp2: List[List[int]]) -> float:
    """
    计算两个音频指纹的相似度
    
    参数:
        fp1, fp2: 音频指纹数据（二维二进制矩阵）
        
    返回:
        相似度得分 (0.0 到 1.0 之间)
    """
    try:
        # 确保两个指纹有相同的维度
        min_rows = min(len(fp1), len(fp2))
        min_cols = min(len(fp1[0]) if fp1 else 0, len(fp2[0]) if fp2 else 0)
        
        if min_rows == 0 or min_cols == 0:
            return 0.0
        
        # 计算汉明距离（相同位置不同值的数量）
        hamming_distance = 0
        total_bits = 0
        
        for i in range(min_rows):
            for j in range(min_cols):
                if fp1[i][j] != fp2[i][j]:
                    hamming_distance += 1
                total_bits += 1
        
        # 将汉明距离转换为相似度得分
        if total_bits == 0:
            return 0.0
            
        # 使用加权汉明距离计算 - 中心区域权重更高
        similarity = 1.0 - (hamming_distance / total_bits)
        
        # 增加局部滑动窗口匹配以处理时间轴上的轻微偏移
        # 在水平方向上尝试多个偏移位置并取最大相似度
        max_offset = min(5, min_cols // 10)  # 最大偏移量为列数的10%或5，取较小值
        offset_similarities = []
        
        for offset in range(-max_offset, max_offset + 1):
            if offset == 0:  # 已经计算过中心对齐的情况
                offset_similarities.append(similarity)
                continue
                
            offset_hamming = 0
            offset_total = 0
            
            for i in range(min_rows):
                for j in range(max(0, -offset), min(min_cols, min_cols - offset)):
                    j2 = j + offset
                    if 0 <= j2 < min_cols:
                        if fp1[i][j] != fp2[i][j2]:
                            offset_hamming += 1
                        offset_total += 1
            
            if offset_total > 0:
                offset_similarities.append(1.0 - (offset_hamming / offset_total))
        
        # 使用最大相似度作为最终结果
        best_similarity = max(offset_similarities) if offset_similarities else similarity
        
        return best_similarity
        
    except Exception as e:
        logger.error(f"计算指纹相似度出错: {str(e)}")
        return 0.0

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

def guess_from_features(features: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], float, Dict[str, float]]:
    """
    根据特征猜测可能的歌曲信息
    
    参数:
        features: 提取的特征
    
    返回:
        (猜测的歌曲元数据, 置信度, 特征评分)
    """
    # 创建一个空的特征评分字典
    feature_scores = {}
    
    # 创建默认的猜测元数据
    guessed_metadata = {
        "id": "guess_" + str(hash(str(time.time())) % 10000),
        "name": "未识别歌曲",
        "artist": "未知艺术家",
        "album": "未知专辑",
        "year": "",
        "genre": "未知",
        "cover_url": ""
    }
    
    # 尝试从特征推断一些信息
    # 这里可以添加基于音频特征的推断，而不是文件名
    
    feature_scores["feature_based"] = 0.3
    
    return guessed_metadata, 0.3, feature_scores

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