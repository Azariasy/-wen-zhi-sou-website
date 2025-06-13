#!/usr/bin/env python3
"""
快捷搜索性能测试脚本

测试优化后的快捷搜索UI渲染性能
"""

import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from quick_search_dialog import QuickSearchDialog

def test_ui_rendering_performance():
    """测试UI渲染性能"""
    app = QApplication(sys.argv)
    
    # 创建快捷搜索对话框
    dialog = QuickSearchDialog()
    
    # 模拟搜索结果
    mock_results = []
    for i in range(31):  # 模拟31个结果（与实际"手册"搜索结果数量一致）
        mock_results.append({
            'file_path': f'D:\\测试文件夹\\测试文件{i+1}.docx',
            'content_preview': f'这是第{i+1}个测试文件的内容预览...'
        })
    
    print("开始UI渲染性能测试...")
    
    # 测试多次渲染的平均时间
    render_times = []
    
    for test_round in range(5):
        print(f"\n第 {test_round + 1} 轮测试:")
        
        # 清空结果
        dialog.results_list.clear()
        
        # 测试渲染时间
        start_time = time.time()
        dialog.set_search_results(mock_results)
        end_time = time.time()
        
        render_time_ms = (end_time - start_time) * 1000
        render_times.append(render_time_ms)
        
        print(f"  渲染时间: {render_time_ms:.2f}ms")
        print(f"  显示项目数: {dialog.results_list.count()}")
        
        # 等待一下再进行下一轮测试
        QTimer.singleShot(100, lambda: None)
        app.processEvents()
    
    # 计算平均性能
    avg_render_time = sum(render_times) / len(render_times)
    min_render_time = min(render_times)
    max_render_time = max(render_times)
    
    print(f"\n性能测试结果:")
    print(f"  平均渲染时间: {avg_render_time:.2f}ms")
    print(f"  最快渲染时间: {min_render_time:.2f}ms")
    print(f"  最慢渲染时间: {max_render_time:.2f}ms")
    print(f"  性能评级: {'优秀' if avg_render_time < 50 else '良好' if avg_render_time < 100 else '需要优化'}")
    
    # 显示对话框进行视觉检查
    dialog.show()
    
    # 设置自动关闭
    QTimer.singleShot(3000, app.quit)
    
    return app.exec()

if __name__ == "__main__":
    test_ui_rendering_performance() 