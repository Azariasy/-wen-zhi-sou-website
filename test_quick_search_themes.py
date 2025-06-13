#!/usr/bin/env python3
"""
快捷搜索主题集成测试脚本

测试快捷搜索窗口与主程序主题系统的集成效果
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QComboBox, QLabel
from PySide6.QtCore import QSettings

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quick_search_dialog import QuickSearchDialog
from search_gui_pyside import ORGANIZATION_NAME, APPLICATION_NAME

class ThemeTestWindow(QMainWindow):
    """主题测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("快捷搜索主题测试")
        self.setGeometry(100, 100, 400, 300)
        
        # 设置
        self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        
        # 快捷搜索对话框
        self.quick_search_dialog = None
        
        # 创建UI
        self._create_ui()
        
    def _create_ui(self):
        """创建用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel("快捷搜索主题集成测试")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # 主题选择
        theme_label = QLabel("选择主题:")
        layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "现代蓝", "现代紫", "现代红", "现代橙"
        ])
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        layout.addWidget(self.theme_combo)
        
        # 显示快捷搜索按钮
        self.show_quick_search_btn = QPushButton("显示快捷搜索窗口")
        self.show_quick_search_btn.clicked.connect(self._show_quick_search)
        layout.addWidget(self.show_quick_search_btn)
        
        # 测试不同主题按钮
        themes = ["现代蓝", "现代紫", "现代红", "现代橙"]
        for theme in themes:
            btn = QPushButton(f"测试 {theme} 主题")
            btn.clicked.connect(lambda checked, t=theme: self._test_theme(t))
            layout.addWidget(btn)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: gray; margin: 10px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def _on_theme_changed(self, theme_name):
        """主题变化处理"""
        self.settings.setValue("ui/theme", theme_name)
        self.status_label.setText(f"主题已切换为: {theme_name}")
        
        # 如果快捷搜索窗口已打开，更新其主题
        if self.quick_search_dialog and hasattr(self.quick_search_dialog, 'update_theme'):
            self.quick_search_dialog.update_theme(theme_name)
    
    def _show_quick_search(self):
        """显示快捷搜索窗口"""
        try:
            if not self.quick_search_dialog:
                self.quick_search_dialog = QuickSearchDialog()
                
                # 设置当前主题
                current_theme = self.theme_combo.currentText()
                if hasattr(self.quick_search_dialog, 'update_theme'):
                    self.quick_search_dialog.update_theme(current_theme)
                
                # 连接信号
                if hasattr(self.quick_search_dialog, 'search_executed'):
                    self.quick_search_dialog.search_executed.connect(self._handle_search)
            
            self.quick_search_dialog.show()
            self.quick_search_dialog.raise_()
            self.quick_search_dialog.activateWindow()
            
            self.status_label.setText("快捷搜索窗口已显示")
            
        except Exception as e:
            self.status_label.setText(f"显示快捷搜索窗口失败: {str(e)}")
            print(f"错误详情: {e}")
            import traceback
            traceback.print_exc()
    
    def _test_theme(self, theme_name):
        """测试指定主题"""
        self.theme_combo.setCurrentText(theme_name)
        self._show_quick_search()
    
    def _handle_search(self, query):
        """处理搜索请求"""
        self.status_label.setText(f"搜索请求: {query}")
        
        # 模拟搜索结果
        mock_results = [
            {
                'file_path': f'/path/to/file1_{query}.txt',
                'content_preview': f'这是包含 "{query}" 的文件内容预览...'
            },
            {
                'file_path': f'/path/to/file2_{query}.docx',
                'content_preview': f'Word文档中包含关键词 "{query}" 的内容...'
            },
            {
                'file_path': f'/path/to/file3_{query}.pdf',
                'content_preview': f'PDF文档中的 "{query}" 相关内容摘要...'
            }
        ]
        
        # 设置搜索结果
        if self.quick_search_dialog and hasattr(self.quick_search_dialog, 'set_search_results'):
            self.quick_search_dialog.set_search_results(mock_results)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName(APPLICATION_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)
    
    # 创建测试窗口
    window = ThemeTestWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 