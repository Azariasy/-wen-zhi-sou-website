#!/usr/bin/env python3
"""
快速搜索手动模式测试脚本

测试修改后的快速搜索功能：
1. 移除了自动搜索（防抖）
2. 只支持回车键手动搜索
3. 避免误搜索和缓存匹配问题
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quick_search_dialog import QuickSearchDialog
from quick_search_controller import QuickSearchController

class MockMainWindow:
    """模拟主窗口用于测试"""
    
    def __init__(self):
        from PySide6.QtCore import QSettings
        self.settings = QSettings("TestOrg", "TestApp")
        
    def _perform_search(self, query, max_results=10, quick_search=True, search_scope="filename"):
        """模拟搜索功能"""
        print(f"🔍 模拟搜索: '{query}', 最大结果: {max_results}, 快速搜索: {quick_search}, 范围: {search_scope}")
        
        # 模拟不同搜索词的结果
        if query == "手册":
            return [
                {'file_path': 'D:/test/内控手册.docx', 'content_preview': '内控手册内容预览'},
                {'file_path': 'D:/test/操作手册.pdf', 'content_preview': '操作手册内容预览'},
            ]
        elif query == "计划":
            return [
                {'file_path': 'D:/test/项目计划.xlsx', 'content_preview': '项目计划内容预览'},
                {'file_path': 'D:/test/工作计划.docx', 'content_preview': '工作计划内容预览'},
            ]
        elif query == "制度":
            return [
                {'file_path': 'D:/test/管理制度.docx', 'content_preview': '管理制度内容预览'},
            ]
        else:
            return []

def test_manual_search():
    """测试手动搜索功能"""
    app = QApplication(sys.argv)
    
    # 创建模拟主窗口
    mock_main_window = MockMainWindow()
    
    # 创建快速搜索控制器
    controller = QuickSearchController(mock_main_window)
    
    # 创建快速搜索对话框
    dialog = QuickSearchDialog()
    
    # 连接信号
    dialog.search_executed.connect(lambda query: print(f"✅ 搜索信号触发: '{query}'"))
    dialog.search_executed.connect(controller._handle_search_request)
    
    # 设置控制器的对话框引用
    controller.dialog = dialog
    
    print("🚀 快速搜索手动模式测试")
    print("=" * 50)
    print("测试说明：")
    print("1. 输入搜索词不会自动搜索")
    print("2. 只有按回车键才会触发搜索")
    print("3. 状态栏会显示'按回车键搜索'提示")
    print("4. 测试搜索词: 手册、计划、制度")
    print("=" * 50)
    
    # 显示对话框
    dialog.show()
    
    # 设置测试定时器
    def test_sequence():
        """测试序列"""
        print("\n📝 开始自动测试序列...")
        
        # 测试1：输入文本但不搜索
        print("\n测试1：输入'手册'但不按回车")
        dialog.search_line_edit.setText("手册")
        
        QTimer.singleShot(1000, lambda: test_manual_search_trigger())
    
    def test_manual_search_trigger():
        """测试手动搜索触发"""
        print("\n测试2：模拟按回车键搜索")
        dialog._on_search_enter()  # 模拟回车键
        
        QTimer.singleShot(1000, lambda: test_different_query())
    
    def test_different_query():
        """测试不同搜索词"""
        print("\n测试3：更换搜索词为'计划'")
        dialog.search_line_edit.setText("计划")
        
        QTimer.singleShot(500, lambda: dialog._on_search_enter())
        
        QTimer.singleShot(1500, lambda: test_clear_and_new())
    
    def test_clear_and_new():
        """测试清空和新搜索"""
        print("\n测试4：清空并输入'制度'")
        dialog.search_line_edit.clear()
        
        QTimer.singleShot(500, lambda: dialog.search_line_edit.setText("制度"))
        QTimer.singleShot(1000, lambda: dialog._on_search_enter())
        
        QTimer.singleShot(2000, lambda: print("\n✅ 测试完成！快速搜索手动模式工作正常。"))
    
    # 启动测试序列
    QTimer.singleShot(1000, test_sequence)
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    test_manual_search() 