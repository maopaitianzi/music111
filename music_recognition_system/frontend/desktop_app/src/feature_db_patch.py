"""
特征数据库补丁文件
用于修复特征数据库索引保存和加载问题
"""

import os
import json
import traceback
import time
from datetime import datetime

def patch_feature_database():
    """修补特征数据库，确保特征索引正确加载和保存"""
    try:
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.abspath(os.path.join(current_dir, "../../../../"))
        database_path = os.path.join(workspace_root, "music_recognition_system/database/music_features_db")
        
        print(f"[补丁] 修复特征数据库，路径: {database_path}")
        
        # 确保目录存在
        os.makedirs(database_path, exist_ok=True)
        
        # 确保features目录存在
        features_dir = os.path.join(database_path, "features")
        os.makedirs(features_dir, exist_ok=True)
        
        # 确保covers目录存在
        covers_dir = os.path.join(database_path, "covers")
        os.makedirs(covers_dir, exist_ok=True)
        
        # 获取所有特征文件
        feature_files = []
        for f in os.listdir(features_dir):
            if f.endswith('.json'):
                feature_files.append(os.path.join(features_dir, f))
        
        print(f"[补丁] 找到 {len(feature_files)} 个特征文件")
        
        # 创建或更新索引文件
        index_path = os.path.join(database_path, "mock_index.json")
        old_index = {}
        
        # 尝试加载现有索引
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    old_index = json.load(f)
                print(f"[补丁] 现有索引包含 {len(old_index)} 条记录")
            except Exception as e:
                print(f"[补丁] 加载现有索引失败: {str(e)}")
                old_index = {}
        
        # 检查所有特征文件并更新索引
        new_index = {}
        processed = 0
        
        for feature_file in feature_files:
            try:
                with open(feature_file, 'r', encoding='utf-8') as f:
                    feature_data = json.load(f)
                
                # 生成文件ID
                file_name = feature_data.get("file_name", "")
                if file_name:
                    import hashlib
                    file_id = hashlib.md5(file_name.encode('utf-8')).hexdigest()
                    
                    # 使用文件ID作为索引键
                    new_index[file_id] = feature_data
                    processed += 1
                    
                    # 更新添加时间（如果没有）
                    if "added_time" not in feature_data:
                        new_index[file_id]["added_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 添加作者和歌曲名（如果没有）
                    if "song_name" not in feature_data or not feature_data["song_name"]:
                        new_index[file_id]["song_name"] = os.path.splitext(file_name)[0]
                    
                    if "author" not in feature_data or not feature_data["author"]:
                        new_index[file_id]["author"] = "未知艺术家"
            except Exception as e:
                print(f"[补丁] 处理特征文件 {os.path.basename(feature_file)} 失败: {str(e)}")
        
        # 合并索引
        if old_index:
            # 保留现有索引中的项，但优先使用新索引中的数据
            for file_id, data in old_index.items():
                if file_id not in new_index:
                    new_index[file_id] = data
        
        # 保存新索引
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(new_index, f, ensure_ascii=False, indent=2)
            print(f"[补丁] 成功保存索引文件，包含 {len(new_index)} 条记录")
            return True
        except Exception as e:
            print(f"[补丁] 保存索引文件失败: {str(e)}")
            traceback.print_exc()
            return False
    
    except Exception as e:
        print(f"[补丁] 执行数据库修复时出错: {str(e)}")
        traceback.print_exc()
        return False

# 创建静态变量以模拟FeatureDatabase类的静态存储
_patched_features = {}
_patched_initialized = False

def apply_database_patches(database_instance):
    """应用补丁到FeatureDatabase实例"""
    global _patched_features, _patched_initialized
    
    try:
        if not database_instance:
            print("[补丁] 数据库实例为空，无法应用补丁")
            return False
        
        database_path = database_instance.database_path if hasattr(database_instance, 'database_path') else None
        
        if not database_path:
            print("[补丁] 无法获取数据库路径，无法应用补丁")
            return False
        
        # 首次运行时修复索引
        if not _patched_initialized:
            # 运行特征数据库修复
            patch_feature_database()
            
            # 尝试加载索引文件
            index_path = os.path.join(database_path, "mock_index.json")
            if os.path.exists(index_path):
                try:
                    with open(index_path, 'r', encoding='utf-8') as f:
                        _patched_features = json.load(f)
                    print(f"[补丁] 加载索引文件成功，包含 {len(_patched_features)} 条记录")
                    
                    # 更新实例的feature_index
                    if hasattr(database_instance, 'feature_index'):
                        database_instance.feature_index = _patched_features.copy()
                        print("[补丁] 已将修复后的索引应用到数据库实例")
                except Exception as e:
                    print(f"[补丁] 加载索引文件失败: {str(e)}")
                    traceback.print_exc()
            
            _patched_initialized = True
            return True
        
        # 已经初始化过，确保实例索引是最新的
        if hasattr(database_instance, 'feature_index'):
            database_instance.feature_index = _patched_features.copy()
            return True
        
        return False
    
    except Exception as e:
        print(f"[补丁] 应用补丁时出错: {str(e)}")
        traceback.print_exc()
        return False

# 修补save_index方法
def patched_save_index(database_instance):
    """修补的保存索引方法"""
    global _patched_features
    
    try:
        if not database_instance:
            print("[补丁] 数据库实例为空，无法保存索引")
            return False
        
        database_path = database_instance.database_path if hasattr(database_instance, 'database_path') else None
        
        if not database_path:
            print("[补丁] 无法获取数据库路径，无法保存索引")
            return False
        
        # 从实例获取最新索引
        if hasattr(database_instance, 'feature_index'):
            _patched_features = database_instance.feature_index.copy()
        
        # 保存索引
        index_path = os.path.join(database_path, "mock_index.json")
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(_patched_features, f, ensure_ascii=False, indent=2)
            print(f"[补丁] 成功保存索引文件，包含 {len(_patched_features)} 条记录")
            return True
        except Exception as e:
            print(f"[补丁] 保存索引文件失败: {str(e)}")
            traceback.print_exc()
            return False
    
    except Exception as e:
        print(f"[补丁] 保存索引时出错: {str(e)}")
        traceback.print_exc()
        return False 