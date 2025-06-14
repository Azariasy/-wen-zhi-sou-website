#!/usr/bin/env python3
"""
渐进式搜索测试脚本

测试新词搜索的渐进式加载效果
"""

import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from quick_search_dialog import QuickSearchDialog

def test_progressive_search():
    """测试渐进式搜索效果"""
    app = QApplication(sys.argv)
    
    # 创建快捷搜索对话框
    dialog = QuickSearchDialog()
    
    print("渐进式搜索测试开始...")
    
    # 模拟第一阶段：快速搜索结果（15个）
    quick_results = []
    for i in range(15):
        quick_results.append({
            'file_path': f'D:\\测试文件夹\\快速结果{i+1}.docx',
            'content_preview': f'这是第{i+1}个快速搜索结果...'
        })
    
    # 添加加载指示器
    quick_results.append({
        'file_path': '正在搜索更多结果...',
        'content_preview': '⏳ 正在后台搜索完整结果，请稍候...',
        'is_loading_indicator': True
    })
    
    # 模拟完整搜索结果（31个）
    complete_results = []
    for i in range(31):
        complete_results.append({
            'file_path': f'D:\\测试文件夹\\完整结果{i+1}.docx',
            'content_preview': f'这是第{i+1}个完整搜索结果...'
        })
    
    # 显示对话框
    dialog.show()
    
    print("第一阶段：显示快速搜索结果（带加载指示器）")
    dialog.set_search_results(quick_results)
    
    # 模拟延迟后显示完整结果
    def show_complete_results():
        print("第二阶段：显示完整搜索结果")
        dialog.set_search_results(complete_results)
    
    # 2秒后显示完整结果
    QTimer.singleShot(2000, show_complete_results)
    
    # 5秒后自动关闭
    QTimer.singleShot(5000, app.quit)
    
    print("观察渐进式搜索效果：")
    print("1. 立即显示快速结果（15个）+ 加载指示器")
    print("2. 2秒后更新为完整结果（31个）")
    print("3. 用户体验：先看到部分结果，避免长时间等待")
    
    return app.exec()

if __name__ == "__main__":
    test_progressive_search() 