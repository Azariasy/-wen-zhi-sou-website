"""
测试轻量级搜索窗口的搜索行为

此脚本用于诊断轻量级搜索窗口是否正确显示搜索结果，而不是直接跳转到主窗口。
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget
from PySide6.QtCore import Qt

from quick_search_controller import QuickSearchController
from main_window_tray import TrayMainWindow

class TestSearchBehavior(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("测试轻量级搜索行为")
        self.setGeometry(100, 100, 500, 300)
        
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 说明标签
        info_label = QLabel(
            "此窗口用于测试轻量级搜索窗口的搜索行为。\n"
            "正确的行为应该是：\n"
            "1. 点击下面的按钮显示轻量级搜索窗口\n"
            "2. 在轻量级搜索窗口中输入搜索关键词并按回车\n"
            "3. 搜索结果应该显示在轻量级窗口中，而不是立即跳转到主窗口\n"
            "4. 只有点击'在主窗口中打开'按钮才应该跳转到主窗口"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)
        
        # 测试按钮
        self.create_components_btn = QPushButton("创建测试组件")
        self.create_components_btn.clicked.connect(self.create_components)
        layout.addWidget(self.create_components_btn)
        
        self.show_search_btn = QPushButton("显示轻量级搜索窗口")
        self.show_search_btn.clicked.connect(self.show_search_window)
        layout.addWidget(self.show_search_btn)
        
        self.test_search_btn = QPushButton("执行测试搜索（关键词：测试）")
        self.test_search_btn.clicked.connect(self.test_search)
        layout.addWidget(self.test_search_btn)
        
        # 组件
        self.main_window = None
        self.search_controller = None
    
    def create_components(self):
        """创建测试组件"""
        try:
            # 创建一个简化的主窗口模拟
            self.main_window = SimplifiedMainWindow()
            
            # 创建轻量级搜索控制器
            self.search_controller = QuickSearchController(self.main_window)
            
            # 连接信号以监控行为
            self.search_controller.show_main_window_signal.connect(self.on_main_window_requested)
            
            self.status_label.setText("测试组件已创建")
            
        except Exception as e:
            self.status_label.setText(f"创建组件失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def show_search_window(self):
        """显示轻量级搜索窗口"""
        if not self.search_controller:
            self.status_label.setText("请先创建测试组件")
            return
        
        try:
            self.search_controller.show_quick_search()
            self.status_label.setText("轻量级搜索窗口已显示")
        except Exception as e:
            self.status_label.setText(f"显示搜索窗口失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def test_search(self):
        """执行测试搜索"""
        if not self.search_controller:
            self.status_label.setText("请先创建测试组件")
            return
        
        try:
            # 显示搜索窗口并执行搜索
            self.search_controller.show_quick_search("测试")
            self.status_label.setText("已显示搜索窗口并执行搜索：测试")
        except Exception as e:
            self.status_label.setText(f"执行搜索失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def on_main_window_requested(self, query):
        """主窗口请求处理"""
        self.status_label.setText(f"检测到主窗口请求：'{query}' - 这应该只在点击'在主窗口中打开'时发生")
        print(f"主窗口请求：'{query}'")


class SimplifiedMainWindow:
    """简化的主窗口模拟"""
    
    def __init__(self):
        self.search_line_edit = type('obj', (object,), {
            'setText': lambda text: print(f"设置搜索文本: {text}")
        })()
        
        print("创建简化主窗口模拟")
    
    def showNormal(self):
        print("显示主窗口")
    
    def activateWindow(self):
        print("激活主窗口")
    
    def start_search_slot(self):
        print("在主窗口中执行搜索")
    
    def _perform_search(self, query, max_results=20, quick_search=False):
        """模拟搜索方法"""
        print(f"执行搜索: '{query}', 最大结果: {max_results}, 快速搜索: {quick_search}")
        
        # 返回一些测试结果
        results = []
        for i in range(1, 6):
            results.append({
                'file_path': f'D:/测试/文档{i}.txt',
                'content_preview': f'这是测试文档{i}，包含关键词"{query}"的内容示例...'
            })
        
        print(f"模拟搜索返回 {len(results)} 个结果")
        return results
    
    def open_file(self, path):
        """模拟打开文件方法"""
        print(f"打开文件: {path}")


def main():
    app = QApplication(sys.argv)
    
    window = TestSearchBehavior()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 