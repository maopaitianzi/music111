#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging
from tqdm import tqdm
from typing import List, Dict, Any, Tuple
import json

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('batch_process')

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入特征提取模块
try:
    from music_recognition_system.utils.audio_features import AudioFeatureExtractor, FeatureDatabase, batch_extract_features
except ImportError:
    logger.error("无法导入音频特征提取模块")
    sys.exit(1)

def get_audio_files(directory: str) -> List[str]:
    """
    获取目录中的所有音频文件
    
    参数:
        directory: 目录路径
        
    返回:
        音频文件路径列表
    """
    supported_extensions = ('.mp3', '.wav', '.flac', '.ogg', '.m4a')
    audio_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(supported_extensions):
                audio_files.append(os.path.join(root, file))
    
    return audio_files

def process_audio_directory(audio_dir: str, db_path: str, metadata_file: str = None) -> Tuple[int, int, List[str]]:
    """
    处理音频目录，提取特征并添加到数据库
    
    参数:
        audio_dir: 音频文件目录
        db_path: 数据库路径
        metadata_file: 元数据文件路径（可选）
        
    返回:
        (成功数, 总数, 失败文件列表)
    """
    logger.info(f"开始处理音频目录: {audio_dir}")
    logger.info(f"数据库路径: {db_path}")
    
    # 获取元数据（如果提供）
    metadata = {}
    if metadata_file and os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            logger.info(f"已加载元数据，包含 {len(metadata)} 项")
        except Exception as e:
            logger.error(f"加载元数据文件失败: {str(e)}")
    
    # 批量提取特征
    success_count, total_files, failed_files = batch_extract_features(audio_dir, db_path)
    
    # 显示处理结果
    success_rate = (success_count / total_files * 100) if total_files > 0 else 0
    logger.info(f"处理完成: 成功 {success_count}/{total_files} ({success_rate:.2f}%)")
    
    if failed_files:
        logger.warning(f"有 {len(failed_files)} 个文件处理失败")
        for file in failed_files[:10]:  # 只显示前10个
            logger.warning(f"  - {os.path.basename(file)}")
        
        if len(failed_files) > 10:
            logger.warning(f"  ...以及其他 {len(failed_files) - 10} 个文件")
    
    return success_count, total_files, failed_files

def create_metadata_template(audio_dir: str, output_file: str) -> None:
    """
    为音频目录创建元数据模板
    
    参数:
        audio_dir: 音频文件目录
        output_file: 输出文件路径
    """
    audio_files = get_audio_files(audio_dir)
    
    metadata = {}
    for file_path in audio_files:
        file_name = os.path.basename(file_path)
        name_without_ext = os.path.splitext(file_name)[0]
        
        metadata[name_without_ext] = {
            "name": name_without_ext,
            "artist": "未知艺术家",
            "album": "未知专辑",
            "year": "",
            "genre": "未知",
            "cover_url": ""
        }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    logger.info(f"已创建元数据模板，包含 {len(metadata)} 首歌曲的信息")
    logger.info(f"请编辑 {output_file} 文件，填写正确的歌曲信息")

def main():
    parser = argparse.ArgumentParser(description="音乐识别系统批处理工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 批量处理命令
    process_parser = subparsers.add_parser("process", help="批量处理音频文件")
    process_parser.add_argument("audio_dir", help="音频文件目录")
    process_parser.add_argument("--db-path", dest="db_path", default=os.path.join(project_root, "music_recognition_system/database/music_features_db"), help="数据库路径")
    process_parser.add_argument("--metadata", dest="metadata_file", help="元数据文件路径")
    
    # 创建元数据模板命令
    metadata_parser = subparsers.add_parser("create-metadata", help="创建元数据模板")
    metadata_parser.add_argument("audio_dir", help="音频文件目录")
    metadata_parser.add_argument("--output", dest="output_file", default="metadata.json", help="输出文件路径")
    
    args = parser.parse_args()
    
    if args.command == "process":
        process_audio_directory(args.audio_dir, args.db_path, args.metadata_file)
    elif args.command == "create-metadata":
        create_metadata_template(args.audio_dir, args.output_file)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 