#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为测试创建索引的脚本
"""

import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

import document_search
import os

def create_index():
    """创建索引"""
    # 检查工作目录是否存在
    work_dir = r"D:\OneDrive\工作"
    if not os.path.exists(work_dir):
        print(f"❌ 工作目录不存在: {work_dir}")
        # 尝试其他目录
        alternative_dirs = [
            r"D:\OneDrive\person",
            r"C:\Users",
            "."
        ]
        
        for alt_dir in alternative_dirs:
            if os.path.exists(alt_dir):
                work_dir = alt_dir
                print(f"✅ 使用替代目录: {work_dir}")
                break
        else:
            print("❌ 找不到任何可用的目录")
            return
    
    print(f"🔧 开始为目录创建索引: {work_dir}")
    print("📁 索引目录: index")
    
    try:
        # 创建索引
        progress_generator = document_search.create_or_update_index(
            directories=[work_dir],
            index_dir_path='index',
            enable_ocr=False,
            max_workers=2,
            incremental=False  # 强制重建
        )
        
        # 显示进度
        for progress in progress_generator:
            stage = progress.get('stage', 'unknown')
            message = progress.get('message', '')
            current = progress.get('current', 0)
            total = progress.get('total', 0)
            
            if total > 0:
                percentage = (current / total) * 100
                print(f"📊 {stage}: {message} ({current}/{total}, {percentage:.1f}%)")
            else:
                print(f"📊 {stage}: {message}")
                
        print("✅ 索引创建完成！")
        
    except Exception as e:
        print(f"❌ 索引创建失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_index() 