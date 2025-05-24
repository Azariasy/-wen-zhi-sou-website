"""
简单的轻量级搜索测试

用于确定搜索后是否会自动跳转到主窗口
"""

import sys
from PySide6.QtWidgets import QApplication
from quick_search_controller import QuickSearchController

class TestMainWindow:
    """测试主窗口"""
    
    def __init__(self):
        self.search_line_edit = type('obj', (object,), {
            'setText': lambda self, text: print(f"[主窗口] 设置搜索文本: {text}")
        })()
    
    def showNormal(self):
        print("[主窗口] 显示窗口")
    
    def activateWindow(self):
        print("[主窗口] 激活窗口")
    
    def start_search_slot(self):
        print("[主窗口] 执行搜索")
    
    def _perform_search(self, query, max_results=20, quick_search=False):
        print(f"[主窗口] 执行搜索: '{query}', 最大结果: {max_results}")
        
        # 返回测试结果
        return [
            {
                'file_path': f'test_file_{i}.txt',
                'content_preview': f'测试内容 {i} 包含关键词 "{query}"'
            }
            for i in range(1, 4)
        ]
    
    def open_file(self, path):
        print(f"[主窗口] 打开文件: {path}")

def main():
    app = QApplication(sys.argv)
    
    # 创建测试主窗口
    main_window = TestMainWindow()
    
    # 创建控制器
    controller = QuickSearchController(main_window)
    
    # 监控主窗口打开信号
    controller.show_main_window_signal.connect(
        lambda text: print(f"[信号] 主窗口打开请求: '{text}' - 这应该只在点击按钮时发生！")
    )
    
    print("测试说明：")
    print("1. 将显示轻量级搜索窗口")
    print("2. 在搜索框中输入内容并按回车")
    print("3. 观察是否自动跳转到主窗口")
    print("4. 按ESC关闭窗口")
    print()
    
    # 只显示窗口，不预设搜索内容
    controller.show_quick_search()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 