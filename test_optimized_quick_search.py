"""
测试优化版快速搜索窗口

演示新的UI设计和交互功能
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import QTimer, QSettings
from quick_search_dialog_optimized import OptimizedQuickSearchDialog

class TestMainWindow(QMainWindow):
    """测试主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文智搜 - 快速搜索测试")
        self.setGeometry(100, 100, 400, 300)
        
        # 设置中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel("快速搜索窗口优化测试")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(title_label)
        
        # 说明
        info_label = QLabel("""
优化内容：
• 现代化深色主题UI设计
• 实时搜索（500ms延迟）
• 改进的键盘导航体验
• 更友好的交互反馈
• 入场动画效果
• 文件类型图标显示
• 优化的右键菜单
• 支持Escape键直接关闭
        """)
        info_label.setStyleSheet("margin: 10px; line-height: 1.5;")
        layout.addWidget(info_label)
        
        # 测试按钮
        self.test_button = QPushButton("🔍 打开优化版快速搜索")
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                margin: 20px;
            }
            QPushButton:hover {
                background-color: #0086e6;
            }
            QPushButton:pressed {
                background-color: #0056b3;
            }
        """)
        self.test_button.clicked.connect(self.show_quick_search)
        layout.addWidget(self.test_button)
        
        # 状态标签
        self.status_label = QLabel("点击按钮测试快速搜索功能")
        self.status_label.setStyleSheet("margin: 10px; color: #666666;")
        layout.addWidget(self.status_label)
        
        # 快速搜索对话框
        self.quick_search_dialog = None
    
    def show_quick_search(self):
        """显示快速搜索对话框"""
        if self.quick_search_dialog:
            self.quick_search_dialog.close()
        
        # 创建新的对话框
        self.quick_search_dialog = OptimizedQuickSearchDialog(self)
        
        # 连接信号
        self.quick_search_dialog.search_executed.connect(self.on_search_executed)
        self.quick_search_dialog.open_file_signal.connect(self.on_open_file)
        self.quick_search_dialog.open_main_window.connect(self.on_open_main_window)
        self.quick_search_dialog.open_folder_signal.connect(self.on_open_folder)
        
        # 显示对话框
        self.quick_search_dialog.show()
        
        # 模拟搜索结果（延迟3秒）
        QTimer.singleShot(3000, self.simulate_search_results)
        
        self.status_label.setText("快速搜索窗口已打开，3秒后将显示模拟搜索结果")
    
    def simulate_search_results(self):
        """模拟搜索结果"""
        if not self.quick_search_dialog:
            return
        
        # 模拟搜索结果数据
        test_results = [
            {
                'title': '项目需求文档.docx',
                'path': 'D:/项目文档/项目需求文档.docx',
                'preview': '本文档详细描述了项目的功能需求、技术需求和业务需求，包括用户界面设计、数据库设计等内容...'
            },
            {
                'title': '2024年度财务报告.xlsx',
                'path': 'D:/财务/2024年度财务报告.xlsx',
                'preview': '包含2024年第一季度到第四季度的详细财务数据，收入、支出、利润分析等...'
            },
            {
                'title': '会议纪要_20241201.txt',
                'path': 'D:/会议记录/会议纪要_20241201.txt',
                'preview': '讨论了项目进度、资源分配、风险评估等议题，确定了下一阶段的工作重点...'
            },
            {
                'title': '产品演示.pptx',
                'path': 'D:/演示文稿/产品演示.pptx',
                'preview': '产品功能介绍、市场定位、竞争优势分析的演示文稿...'
            },
            {
                'title': '用户手册.pdf',
                'path': 'D:/文档/用户手册.pdf',
                'preview': '详细的用户操作指南，包括安装、配置、使用方法等...'
            },
            {
                'title': '数据备份_20241201.zip',
                'path': 'D:/备份/数据备份_20241201.zip',
                'preview': '重要数据的压缩备份文件...'
            },
            {
                'title': '项目截图.png',
                'path': 'D:/图片/项目截图.png',
                'preview': '项目界面的屏幕截图...'
            },
            {
                'title': '客户邮件.eml',
                'path': 'D:/邮件/客户邮件.eml',
                'preview': '来自重要客户的邮件通信记录...'
            }
        ]
        
        # 设置搜索结果
        self.quick_search_dialog.set_search_results(test_results)
        self.status_label.setText("已加载模拟搜索结果，可以测试各种交互功能")
    
    def on_search_executed(self, search_text):
        """处理搜索执行"""
        self.status_label.setText(f"执行搜索: '{search_text}'")
        print(f"主窗口收到搜索请求: {search_text}")
        
        # 模拟搜索延迟
        QTimer.singleShot(1000, lambda: self.simulate_search_results())
    
    def on_open_file(self, file_path):
        """处理打开文件"""
        self.status_label.setText(f"打开文件: {file_path}")
        print(f"主窗口收到打开文件请求: {file_path}")
    
    def on_open_main_window(self, search_text):
        """处理在主窗口中打开搜索"""
        if search_text:
            self.status_label.setText(f"在主窗口中搜索: '{search_text}'")
            print(f"主窗口收到搜索请求: {search_text}")
        else:
            self.status_label.setText("打开主窗口")
            print("主窗口被激活")
    
    def on_open_folder(self, folder_path):
        """处理打开文件夹"""
        self.status_label.setText(f"打开文件夹: {folder_path}")
        print(f"主窗口收到打开文件夹请求: {folder_path}")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setOrganizationName("WenZhiSou")
    app.setApplicationName("DocumentSearch")
    
    # 创建主窗口
    main_window = TestMainWindow()
    main_window.show()
    
    print("快速搜索优化测试启动")
    print("功能测试说明：")
    print("1. 点击按钮打开快速搜索窗口")
    print("2. 测试实时搜索（输入文字后等待500ms）")
    print("3. 测试键盘导航（上下键、回车键、Escape键）")
    print("4. 测试右键菜单功能")
    print("5. 测试拖动窗口")
    print("6. 测试各种按钮功能")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 