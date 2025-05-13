"""
特征数据库修复脚本
用于修复特征数据库索引保存和加载问题

使用方法:
1. 在项目根目录运行: python -m music_recognition_system.fix_feature_db
"""

import os
import sys
import json
import traceback
import time
from datetime import datetime

def fix_feature_database():
    """修复特征数据库索引"""
    try:
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        database_path = os.path.join(current_dir, "database/music_features_db")
        
        print(f"正在修复特征数据库，路径: {database_path}")
        
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
        if os.path.exists(features_dir):
            for f in os.listdir(features_dir):
                if f.endswith('.json'):
                    feature_files.append(os.path.join(features_dir, f))
        
        print(f"找到 {len(feature_files)} 个特征文件")
        
        # 创建或更新索引文件
        index_files = ["index.json", "mock_index.json"]
        old_index = {}
        
        # 尝试加载现有索引
        for index_name in index_files:
            index_path = os.path.join(database_path, index_name)
            if os.path.exists(index_path):
                try:
                    with open(index_path, 'r', encoding='utf-8') as f:
                        temp_index = json.load(f)
                        print(f"现有索引 {index_name} 包含 {len(temp_index)} 条记录")
                        # 合并索引
                        old_index.update(temp_index)
                except Exception as e:
                    print(f"加载索引 {index_name} 失败: {str(e)}")
        
        print(f"合并后的现有索引包含 {len(old_index)} 条记录")
        
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
                        
                    print(f"处理特征文件: {file_name}")
            except Exception as e:
                print(f"处理特征文件 {os.path.basename(feature_file)} 失败: {str(e)}")
        
        # 合并索引
        if old_index:
            # 保留现有索引中的项，但优先使用新索引中的数据
            for file_id, data in old_index.items():
                if file_id not in new_index:
                    new_index[file_id] = data
                    print(f"从现有索引中添加: {data.get('file_name', 'unknown')}")
        
        # 保存新索引到所有索引文件
        for index_name in index_files:
            index_path = os.path.join(database_path, index_name)
            try:
                with open(index_path, 'w', encoding='utf-8') as f:
                    json.dump(new_index, f, ensure_ascii=False, indent=2)
                print(f"成功保存索引文件 {index_name}，包含 {len(new_index)} 条记录")
            except Exception as e:
                print(f"保存索引文件 {index_name} 失败: {str(e)}")
        
        print("特征数据库修复完成！")
        print(f"处理了 {processed} 个特征文件")
        print(f"最终索引包含 {len(new_index)} 条记录")
        
        return True
    
    except Exception as e:
        print(f"修复特征数据库时出错: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始修复特征数据库...")
    success = fix_feature_database()
    print(f"修复结果: {'成功' if success else '失败'}")
    
    # 如果成功，提示用户重启应用程序
    if success:
        print("\n请重启音乐识别系统应用程序，使修复生效。")
    else:
        print("\n修复失败，请尝试手动修复特征数据库。") 