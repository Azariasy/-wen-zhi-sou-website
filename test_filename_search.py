#!/usr/bin/env python3
"""
测试轻量级搜索的文件名搜索功能
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from main_window_tray import TrayMainWindow
from quick_search_controller import QuickSearchController

def test_filename_search():
    """测试文件名搜索功能"""
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = TrayMainWindow()
    
    # 测试搜索功能
    def run_test():
        print("=== 测试轻量级搜索的文件名搜索功能 ===")
        
        # 测试不同的搜索关键词
        test_queries = [
            "十四五",
            "规划", 
            "国民",
            "计划",
            "资产"
        ]
        
        for query in test_queries:
            print(f"\n--- 测试搜索关键词: '{query}' ---")
            
            # 执行文件名搜索
            results = window._perform_search(
                query=query,
                max_results=10,
                quick_search=True,
                search_scope="filename"
            )
            
            print(f"搜索结果数量: {len(results)}")
            
            if results:
                print("搜索结果:")
                for i, result in enumerate(results[:5], 1):
                    file_path = result.get('file_path', '')
                    file_name = os.path.basename(file_path) if file_path else '未知文件'
                    preview = result.get('content_preview', '')[:100]
                    print(f"  {i}. {file_name}")
                    print(f"     路径: {file_path}")
                    print(f"     预览: {preview}")
            else:
                print("  未找到匹配的文件")
        
        print("\n=== 测试完成 ===")
        
        # 延迟关闭应用
        QTimer.singleShot(2000, app.quit)
    
    # 延迟执行测试，等待窗口完全初始化
    QTimer.singleShot(1000, run_test)
    
    return app.exec()

if __name__ == "__main__":
    test_filename_search() 