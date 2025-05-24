"""
只测试搜索对话框，不使用控制器

用于确定问题是否出在对话框本身
"""

import sys
from PySide6.QtWidgets import QApplication
from quick_search_dialog import QuickSearchDialog

def main():
    app = QApplication(sys.argv)
    
    # 直接创建搜索对话框
    dialog = QuickSearchDialog()
    
    # 连接信号进行监控
    dialog.search_executed.connect(
        lambda text: print(f"[对话框] 搜索执行: '{text}'")
    )
    
    dialog.item_activated.connect(
        lambda path: print(f"[对话框] 项目激活: '{path}'")
    )
    
    dialog.open_main_window.connect(
        lambda text: print(f"[对话框] 主窗口打开请求: '{text}' - 这应该只在点击按钮时发生！")
    )
    
    print("测试说明：")
    print("1. 在搜索框中输入内容并按回车")
    print("2. 观察是否只触发一次搜索信号")
    print("3. 点击'在主窗口中打开'按钮测试该功能")
    print("4. 按ESC关闭窗口")
    print()
    
    # 设置一些测试结果，模拟搜索完成
    def set_test_results():
        results = [
            {
                'title': '测试文件1.txt',
                'path': 'D:/test1.txt',
                'preview': '这是测试文件1的预览内容...'
            },
            {
                'title': '测试文件2.txt',
                'path': 'D:/test2.txt',
                'preview': '这是测试文件2的预览内容...'
            }
        ]
        dialog.set_search_results(results)
    
    # 连接搜索信号到设置结果的函数
    dialog.search_executed.connect(lambda text: set_test_results())
    
    dialog.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 