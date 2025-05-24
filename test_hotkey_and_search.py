"""
文智搜热键和轻量级搜索测试脚本

此脚本用于测试热键注册和轻量级搜索功能是否正常工作。
"""

import sys
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget
from PySide6.QtCore import Qt

from main_window_tray import TrayMainWindow
from hotkey_manager import HotkeyManager
from quick_search_dialog import QuickSearchDialog
from quick_search_controller import QuickSearchController

class TestHotkeyAndSearch(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("文智搜热键和轻量级搜索测试")
        self.setGeometry(100, 100, 500, 400)
        
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 添加说明标签
        info_label = QLabel(
            "此窗口用于测试热键和轻量级搜索功能。\n"
            "1. 首先会创建热键管理器并注册alt+space热键\n"
            "2. 然后会创建轻量级搜索控制器\n"
            "3. 点击按钮可以测试不同功能"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)
        
        # 热键状态
        self.hotkey_status = QLabel("热键状态: 未启动")
        layout.addWidget(self.hotkey_status)
        
        # 测试按钮
        self.test_hotkey_btn = QPushButton("注册并测试热键")
        self.test_hotkey_btn.clicked.connect(self.setup_hotkey)
        layout.addWidget(self.test_hotkey_btn)
        
        # 轻量级搜索按钮
        self.show_search_btn = QPushButton("显示轻量级搜索窗口")
        self.show_search_btn.clicked.connect(self.show_quick_search)
        layout.addWidget(self.show_search_btn)
        
        # 执行搜索按钮
        self.execute_search_btn = QPushButton("执行模拟搜索 (测试关键词)")
        self.execute_search_btn.clicked.connect(self.execute_test_search)
        layout.addWidget(self.execute_search_btn)
        
        # 创建热键管理器和搜索控制器
        self.hotkey_manager = None
        self.search_controller = None
        self.search_dialog = None
        self.initialized = False
        
    def setup_hotkey(self):
        """设置热键管理器"""
        try:
            # 创建热键管理器
            if not self.hotkey_manager:
                self.hotkey_manager = HotkeyManager()
                
                # 注册热键
                self.hotkey_manager.register_hotkey(
                    "test_search",
                    "alt+space",  # Alt+空格
                    callback=self.on_hotkey_triggered,
                    enabled=True
                )
                
                # 启动监听
                self.hotkey_manager.start_listener()
                self.hotkey_status.setText("热键状态: 已注册 alt+space")
                self.status_label.setText("热键注册成功！按下Alt+Space测试热键")
            else:
                self.status_label.setText("热键管理器已创建")
        except Exception as e:
            self.status_label.setText(f"设置热键失败: {str(e)}")
    
    def on_hotkey_triggered(self):
        """热键触发回调"""
        self.status_label.setText(f"热键已触发！时间: {time.strftime('%H:%M:%S')}")
        self.show_quick_search()
    
    def show_quick_search(self):
        """显示轻量级搜索窗口"""
        try:
            if not self.search_controller:
                # 创建轻量级搜索控制器
                self.search_controller = QuickSearchController(self)
            
            # 显示搜索窗口
            self.search_controller.show_quick_search()
            self.status_label.setText("已显示轻量级搜索窗口")
        except Exception as e:
            self.status_label.setText(f"显示轻量级搜索失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def execute_test_search(self):
        """执行测试搜索"""
        try:
            if not self.search_controller:
                # 创建轻量级搜索控制器
                self.search_controller = QuickSearchController(self)
            
            # 模拟搜索调用
            search_term = "测试关键词"
            self.status_label.setText(f"执行搜索: {search_term}")
            
            # 使用控制器的内部方法直接执行搜索
            self.search_controller._handle_search_request(search_term)
        except Exception as e:
            self.status_label.setText(f"执行测试搜索失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _perform_search(self, query, max_results=20, quick_search=True):
        """模拟主窗口的搜索方法，供轻量级搜索控制器调用"""
        self.status_label.setText(f"执行搜索: {query}, 最大结果数: {max_results}")
        
        # 返回一些测试结果
        return [
            {
                'file_path': f'D:/文档/测试文档{i}.txt',
                'content_preview': f'这是包含"{query}"关键词的示例内容...' * 2
            }
            for i in range(1, 6)
        ]
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止热键监听
        if self.hotkey_manager:
            self.hotkey_manager.stop_listener()
        event.accept()


def main():
    # 创建应用
    app = QApplication(sys.argv)
    
    # 创建并显示测试窗口
    window = TestHotkeyAndSearch()
    window.show()
    
    # 运行应用
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 