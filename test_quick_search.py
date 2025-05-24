#!/usr/bin/env python3
"""
测试轻量级搜索对话框功能
"""

import sys
from PySide6.QtWidgets import QApplication
from quick_search_dialog import QuickSearchDialog

def test_quick_search_dialog():
    """测试轻量级搜索对话框"""
    app = QApplication(sys.argv)
    
    # 创建对话框
    dialog = QuickSearchDialog()
    
    # 连接信号用于测试
    dialog.search_executed.connect(lambda text: print(f"搜索执行: {text}"))
    dialog.item_activated.connect(lambda path: print(f"文件激活: {path}"))
    dialog.open_main_window.connect(lambda text: print(f"在主窗口打开: {text}"))
    dialog.open_file_signal.connect(lambda path: print(f"打开文件: {path}"))
    dialog.open_folder_signal.connect(lambda folder_path: print(f"打开文件夹: {folder_path}"))
    
    # 添加测试数据
    test_results = [
        {
            'title': '测试文档1.docx',
            'path': 'D:/OneDrive/person/文智搜/test1.docx',
            'preview': '这是一个测试文档，包含搜索关键词...'
        },
        {
            'title': '测试文档2.pdf',
            'path': 'D:/OneDrive/person/文智搜/test2.pdf',
            'preview': '这是另一个测试文档，用于验证搜索功能...'
        },
        {
            'title': 'README.md',
            'path': 'D:/OneDrive/person/文智搜/README.md',
            'preview': '项目说明文档，介绍了项目的基本功能...'
        }
    ]
    
    # 设置搜索结果
    dialog.set_search_results(test_results)
    
    # 显示对话框
    dialog.show()
    
    print("轻量级搜索对话框已打开")
    print("测试功能:")
    print("1. 在搜索框输入内容并按回车")
    print("2. 双击结果项或按回车键打开文件")
    print("3. 右键点击结果项查看菜单选项")
    print("4. 点击'在主窗口中打开'按钮")
    print("5. 按ESC键关闭对话框")
    
    return app.exec()

if __name__ == "__main__":
    test_quick_search_dialog() 