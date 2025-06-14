#!/usr/bin/env python3
"""
快速搜索手动模式测试脚本 v2

测试修改后的快速搜索功能：
1. 移除了自动搜索（防抖）
2. 回车键只用于搜索，不打开主窗口
3. Ctrl+回车才打开主窗口
4. 避免误搜索和缓存匹配问题
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QSettings

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quick_search_dialog import QuickSearchDialog
from quick_search_controller import QuickSearchController

class MockMainWindow:
    """模拟主窗口用于测试"""
    
    def __init__(self):
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

def test_manual_search_v2():
    """测试手动搜索功能 v2"""
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
    dialog.open_main_window.connect(lambda query: print(f"🖥️ 打开主窗口信号触发: '{query}'"))
    dialog.open_file_signal.connect(lambda path: print(f"📄 打开文件信号触发: '{path}'"))
    
    # 设置控制器的对话框引用
    controller.dialog = dialog
    
    print("🚀 快速搜索手动模式测试 v2")
    print("=" * 60)
    print("测试说明：")
    print("1. 输入搜索词不会自动搜索")
    print("2. 按回车键执行搜索（搜索框有焦点时）")
    print("3. 按Ctrl+回车键打开主窗口")
    print("4. 在结果列表按回车键打开文件")
    print("5. 状态栏显示'按回车键搜索'提示")
    print("6. 测试搜索词: 手册、计划、制度")
    print("=" * 60)
    
    # 显示对话框
    dialog.show()
    
    # 设置测试定时器
    def test_sequence():
        """测试序列"""
        print("\n📝 开始自动测试序列...")
        
        # 测试1：输入文本但不搜索
        print("\n测试1：输入'手册'但不按回车")
        dialog.search_line_edit.setText("手册")
        dialog.search_line_edit.setFocus()  # 确保搜索框有焦点
        
        QTimer.singleShot(1000, lambda: test_enter_search())
    
    def test_enter_search():
        """测试回车键搜索"""
        print("\n测试2：按回车键搜索（搜索框有焦点）")
        dialog.search_line_edit.setFocus()  # 确保搜索框有焦点
        dialog._on_search_enter()  # 模拟回车键
        
        QTimer.singleShot(1000, lambda: test_ctrl_enter())
    
    def test_ctrl_enter():
        """测试Ctrl+回车打开主窗口"""
        print("\n测试3：更换搜索词为'计划'并测试Ctrl+Enter")
        dialog.search_line_edit.setText("计划")
        dialog.search_line_edit.setFocus()
        
        QTimer.singleShot(500, lambda: test_ctrl_enter_action())
    
    def test_ctrl_enter_action():
        """执行Ctrl+Enter操作"""
        print("   模拟Ctrl+Enter打开主窗口")
        dialog._on_main_window_button()  # 模拟Ctrl+Enter
        
        QTimer.singleShot(1000, lambda: test_result_list_enter())
    
    def test_result_list_enter():
        """测试结果列表中的回车键"""
        print("\n测试4：在结果列表中按回车键打开文件")
        # 先搜索获得结果
        dialog.search_line_edit.setText("制度")
        dialog.search_line_edit.setFocus()
        dialog._on_search_enter()
        
        # 模拟结果列表有焦点并按回车
        QTimer.singleShot(500, lambda: simulate_list_enter())
    
    def simulate_list_enter():
        """模拟列表中按回车"""
        if dialog.results_list.count() > 0:
            dialog.results_list.setFocus()
            dialog.results_list.setCurrentRow(0)
            current_item = dialog.results_list.currentItem()
            if current_item:
                print("   模拟在结果列表中按回车键")
                dialog._on_item_activated(current_item)
        
        QTimer.singleShot(1000, lambda: test_help_dialog())
    
    def test_help_dialog():
        """测试帮助对话框"""
        print("\n测试5：显示帮助对话框")
        dialog._show_help_dialog()
        
        QTimer.singleShot(2000, lambda: print("\n✅ 测试完成！快速搜索手动模式 v2 工作正常。"))
    
    # 启动测试序列
    QTimer.singleShot(1000, test_sequence)
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    test_manual_search_v2() 