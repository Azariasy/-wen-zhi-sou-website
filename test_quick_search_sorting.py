#!/usr/bin/env python3
"""
测试快速搜索按修改时间排序和显示优化
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quick_filename_search import QuickFilenameSearcher

def test_quick_search_sorting():
    """测试快速搜索的排序和显示"""
    print("🧪 测试快速搜索按修改时间排序和显示优化...")
    
    # 测试目录
    test_directories = [
        "D:/OneDrive/person/文件搜索工具/测试文件夹",
        "D:/OneDrive/person/文件搜索工具/新建文件夹",
        "D:/OneDrive/工作/中移（成都）信息通信科技有限公司/内控及风险管理/内控矩阵相关/2025年上半年修订情况"
    ]
    
    # 创建搜索器
    searcher = QuickFilenameSearcher(test_directories)
    
    # 测试搜索词
    test_queries = ["手册", "计划", "制度"]
    
    for query in test_queries:
        print(f"\n🔍 测试搜索：'{query}'")
        results = searcher.search_filenames(query, max_results=10)
        
        if results:
            print(f"✅ 找到 {len(results)} 个结果（按修改时间排序）：")
            for i, result in enumerate(results, 1):
                # 格式化修改时间
                import datetime
                modified_time = datetime.datetime.fromtimestamp(result['modified_time'])
                formatted_time = modified_time.strftime('%Y-%m-%d %H:%M')
                
                # 格式化文件大小
                size_bytes = result['file_size']
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                
                # 简化路径显示
                file_path = Path(result['file_path'])
                try:
                    # 尝试显示相对路径
                    home_path = Path.home()
                    relative_path = file_path.relative_to(home_path)
                    display_path = f"~/{relative_path.parent}"
                except ValueError:
                    # 显示最后两级目录
                    parts = file_path.parts
                    if len(parts) > 2:
                        display_path = f".../{parts[-2]}/{parts[-1]}"
                    else:
                        display_path = str(file_path.parent)
                
                print(f"  {i}. {result['filename']}")
                print(f"     📁 {display_path}")
                print(f"     🕒 {formatted_time}  📊 {size_str}  ⭐ {result['match_score']:.1f}")
        else:
            print("  ❌ 未找到结果")
    
    print("\n✅ 快速搜索排序和显示测试完成")

if __name__ == "__main__":
    test_quick_search_sorting() 