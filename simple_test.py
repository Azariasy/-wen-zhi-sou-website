#!/usr/bin/env python3
"""
简单测试轻量级搜索功能
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_window_tray import TrayMainWindow

def main():
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = TrayMainWindow()
    
    def test_search():
        print("开始测试文件名搜索...")
        
        # 测试搜索
        results = window._perform_search(
            query="规划",
            max_results=5,
            quick_search=True,
            search_scope="filename"
        )
        
        print(f"搜索完成，结果数量: {len(results)}")
        
        if results:
            for i, result in enumerate(results, 1):
                file_path = result.get('file_path', '')
                file_name = os.path.basename(file_path)
                print(f"{i}. {file_name}")
                print(f"   路径: {file_path}")
        else:
            print("未找到结果")
        
        # 退出应用
        QTimer.singleShot(1000, app.quit)
    
    # 延迟执行测试
    QTimer.singleShot(2000, test_search)
    
    return app.exec()

if __name__ == "__main__":
    main() 