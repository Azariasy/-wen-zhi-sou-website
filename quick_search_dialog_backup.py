"""
文智搜轻量级搜索窗口

此模块实现了一个无边框、置顶的轻量级搜索窗口，提供快速搜索功能。
特点:
1. 无边框设计，简洁美观
2. 置顶显示，方便快速访问
3. 支持键盘导航
4. 显示精简的搜索结果
"""

import sys
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QListWidget, QListWidgetItem, QLabel, QPushButton, 
                             QGraphicsDropShadowEffect, QApplication, QWidget, QMenu)
from PySide6.QtCore import Qt, QSize, QEvent, QPoint, QSettings, Signal
from PySide6.QtGui import QIcon, QColor, QFont, QPalette, QKeyEvent, QDesktopServices, QAction
from pathlib import Path

class SearchResultItem(QListWidgetItem):
    """自定义搜索结果列表项"""
    
    def __init__(self, title, path, icon_path=None, content_preview=""):
        super().__init__()
        
        self.title = title
        self.path = path
        self.content_preview = content_preview
        
        # 设置文本
        self.setText(title)
        
        # 设置图标（如果有）
        if icon_path and os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        
        # 存储额外数据
        self.setData(Qt.UserRole, path)
        self.setData(Qt.UserRole + 1, content_preview)
        
        # 设置工具提示（文件名搜索模式下显示完整路径）
        tooltip_text = f"文件: {title}\n路径: {path}"
        if content_preview:
            tooltip_text += f"\n\n预览: {content_preview}"
        self.setToolTip(tooltip_text)

class QuickSearchDialog(QDialog):
    """轻量级搜索对话框"""
    
    # 定义信号
    search_executed = Signal(str)        # 执行搜索信号
    item_activated = Signal(str)         # 项目激活（打开）信号
    open_main_window = Signal(str)       # 在主窗口中打开搜索信号
    open_file_signal = Signal(str)        # 打开文件信号
    open_folder_signal = Signal(str)      # 打开文件夹信号
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # 设置窗口基本属性
        self.setWindowTitle("快速搜索")
        self.setMinimumSize(500, 400)
        self.setMaximumSize(700, 600)
        
        # 窗口拖动相关
        self._dragging = False
        self._drag_start_position = QPoint()
        
        # 加载设置
        self.settings = QSettings("WenZhiSou", "DocumentSearch")
        
        # 初始化UI
        self._setup_ui()
        
        # 连接信号
        self._connect_signals()
        
        # 应用样式
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI组件"""
        layout = QVBoxLayout(self)
        
        # 标题栏区域
        title_layout = QHBoxLayout()
        
        # 搜索图标
        self.search_icon_label = QLabel()
        self.search_icon_label.setFixedSize(24, 24)
        # 这里可以设置搜索图标，如果有的话
        title_layout.addWidget(self.search_icon_label)
        
        # 标题
        self.title_label = QLabel("文智搜 - 快速搜索")
        self.title_label.setObjectName("titleLabel")
        title_layout.addWidget(self.title_label)
        
        # 添加伸缩项，让关闭按钮靠右
        title_layout.addStretch()
        
        # 关闭按钮
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(24, 24)
        title_layout.addWidget(self.close_button)
        
        layout.addLayout(title_layout)
        
        # 搜索框
        self.search_line_edit = QLineEdit()
        self.search_line_edit.setObjectName("searchLineEdit")
        self.search_line_edit.setPlaceholderText("输入搜索内容...")
        layout.addWidget(self.search_line_edit)
        
        # 结果列表
        self.results_list = QListWidget()
        self.results_list.setObjectName("resultsList")
        layout.addWidget(self.results_list)
        
        # 状态/底部区域
        bottom_layout = QHBoxLayout()
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        self.status_label.setObjectName("statusLabel")
        bottom_layout.addWidget(self.status_label)
        
        # 添加伸缩项，让下面的按钮靠右
        bottom_layout.addStretch()
        
        # "在主窗口中打开"按钮
        self.main_window_button = QPushButton("在主窗口中打开")
        self.main_window_button.setObjectName("mainWindowButton")
        # 明确设置这个按钮不是默认按钮，防止回车键误触发
        self.main_window_button.setDefault(False)
        self.main_window_button.setAutoDefault(False)
        bottom_layout.addWidget(self.main_window_button)
        
        layout.addLayout(bottom_layout)
        
        # 设置布局边距
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 设置焦点到搜索框
        self.search_line_edit.setFocus()
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 关闭按钮
        self.close_button.clicked.connect(self.close)
        
        # 搜索框回车
        self.search_line_edit.returnPressed.connect(self._on_search)
        
        # 结果列表双击
        self.results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # 结果列表回车
        self.results_list.itemActivated.connect(self._on_item_activated)
        
        # 在主窗口打开按钮
        self.main_window_button.clicked.connect(self._on_main_window_button)
        
        # 设置右键菜单
        self.results_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_list.customContextMenuRequested.connect(self._show_context_menu)
    
    def _apply_styles(self):
        """应用样式"""
        # 窗口背景
        self.setStyleSheet("""
            QDialog {
                background-color: #333333;
                color: #FFFFFF;
                border-radius: 10px;
            }
            
            QLabel {
                color: #FFFFFF;
            }
            
            #titleLabel {
                font-size: 14px;
                font-weight: bold;
            }
            
            #closeButton {
                border: none;
                background: none;
                color: #FFFFFF;
                font-size: 16px;
                font-weight: bold;
            }
            
            #closeButton:hover {
                color: #FF5555;
            }
            
            QLineEdit {
                padding: 8px;
                border-radius: 4px;
                background-color: #4D4D4D;
                color: #FFFFFF;
                border: 1px solid #555555;
            }
            
            QLineEdit:focus {
                border: 1px solid #7D7D7D;
            }
            
            QListWidget {
                background-color: #3A3A3A;
                alternate-background-color: #404040;
                color: #FFFFFF;
                border-radius: 4px;
                border: 1px solid #555555;
            }
            
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #555555;
            }
            
            QListWidget::item:selected {
                background-color: #555555;
            }
            
            QPushButton {
                padding: 6px 12px;
                background-color: #4D4D4D;
                color: #FFFFFF;
                border-radius: 4px;
                border: none;
            }
            
            QPushButton:hover {
                background-color: #5A5A5A;
            }
            
            QPushButton:pressed {
                background-color: #333333;
            }
            
            #statusLabel {
                color: #AAAAAA;
                font-style: italic;
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
        
    def mousePressEvent(self, event):
        """处理鼠标按下事件，用于窗口拖动"""
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_start_position = event.position().toPoint()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，用于窗口拖动"""
        if self._dragging:
            # 计算移动的距离
            delta = event.position().toPoint() - self._drag_start_position
            # 移动窗口
            self.move(self.pos() + delta)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件，用于窗口拖动"""
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        key = event.key()
        
        # Escape键关闭窗口
        if key == Qt.Key_Escape:
            self.close()
            event.accept()
            return
        # 回车键处理
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            # 如果搜索框有焦点，执行搜索
            if self.search_line_edit.hasFocus():
                self._on_search()
                event.accept()
                return
            # 如果结果列表有焦点且有选中项，打开文件
            elif self.results_list.hasFocus() and self.results_list.currentItem():
                self._on_item_activated(self.results_list.currentItem())
                event.accept()
                return
            # 其他情况，阻止事件传播
            event.accept()
            return
        # 上下键在搜索框和结果列表之间导航
        elif key == Qt.Key_Down and self.search_line_edit.hasFocus():
            # 从搜索框移动到结果列表
            if self.results_list.count() > 0:
                self.results_list.setCurrentRow(0)
                self.results_list.setFocus()
                event.accept()
                return
        elif key == Qt.Key_Up and self.results_list.hasFocus() and self.results_list.currentRow() == 0:
            # 从结果列表的第一项移回搜索框
            self.search_line_edit.setFocus()
            event.accept()
            return
        
        # 其他键事件传递给父类处理
        super().keyPressEvent(event)
    
    def _on_search(self):
        """处理搜索请求"""
        search_text = self.search_line_edit.text().strip()
        if not search_text:
            return
        
        # 清空结果列表
        self.results_list.clear()
        
        # 更新状态
        self.status_label.setText("正在搜索...")
        
        # 打印调试信息
        print(f"轻量级搜索对话框: 触发搜索请求 '{search_text}'")
        
        # 发出搜索信号
        self.search_executed.emit(search_text)
    
    def _on_item_double_clicked(self, item):
        """处理双击事件"""
        result = item.data(Qt.UserRole)
        if result:
            print(f"轻量级搜索对话框: 双击打开文件 '{result}'")
            # 从结果字典中提取文件路径
            if isinstance(result, dict) and 'file_path' in result:
                file_path = result['file_path']
                self.open_file_signal.emit(file_path)
            else:
                # 兼容旧格式
                self.open_file_signal.emit(str(result))
    
    def _on_item_activated(self, item):
        """处理激活事件（回车键）"""
        result = item.data(Qt.UserRole)
        if result:
            print(f"轻量级搜索对话框: 激活打开文件 '{result}'")
            # 从结果字典中提取文件路径
            if isinstance(result, dict) and 'file_path' in result:
                file_path = result['file_path']
                self.open_file_signal.emit(file_path)
            else:
                # 兼容旧格式
                self.open_file_signal.emit(str(result))
    
    def _on_main_window_button(self):
        """处理在主窗口中打开按钮"""
        search_text = self.search_line_edit.text().strip()
        if search_text:
            print(f"轻量级搜索对话框: 在主窗口中打开搜索 '{search_text}'")
            self.open_main_window.emit(search_text)
            self.close()
        else:
            print("轻量级搜索对话框: 尝试在主窗口中打开，但搜索文本为空")
    
    def _show_context_menu(self, position):
        """显示右键菜单"""
        item = self.results_list.itemAt(position)
        if not item:
            return
            
        # 获取文件路径
        file_path = item.data(Qt.UserRole)
        if not file_path:
            return
            
        # 创建右键菜单
        context_menu = QMenu(self)
        
        # 打开文件
        open_file_action = QAction("打开文件", self)
        open_file_action.triggered.connect(lambda: self._open_file(file_path))
        context_menu.addAction(open_file_action)
        
        # 打开文件所在目录
        open_folder_action = QAction("打开文件所在目录", self)
        open_folder_action.triggered.connect(lambda: self._open_folder(file_path))
        context_menu.addAction(open_folder_action)
        
        context_menu.addSeparator()
        
        # 复制文件路径
        copy_path_action = QAction("复制文件路径", self)
        copy_path_action.triggered.connect(lambda: self._copy_path(file_path))
        context_menu.addAction(copy_path_action)
        
        # 在主窗口中搜索（全文搜索）
        fulltext_search_action = QAction("在主窗口中进行全文搜索", self)
        fulltext_search_action.triggered.connect(lambda: self._fulltext_search_in_main())
        context_menu.addAction(fulltext_search_action)
        
        # 显示菜单
        context_menu.exec(self.results_list.mapToGlobal(position))
    
    def _open_file(self, file_path):
        """打开文件"""
        if not file_path:
            return
        try:
            print(f"轻量级搜索对话框: 打开文件 '{file_path}'")
            self.open_file_signal.emit(file_path)
        except Exception as e:
            print(f"打开文件失败: {str(e)}")
    
    def _open_folder(self, file_path):
        """打开文件所在目录"""
        if not file_path:
            return
        try:
            folder_path = str(Path(file_path).parent)
            print(f"轻量级搜索对话框: 打开文件夹 '{folder_path}'")
            self.open_folder_signal.emit(folder_path)
        except Exception as e:
            print(f"打开文件夹失败: {str(e)}")
    
    def _copy_path(self, file_path):
        """复制文件路径到剪贴板"""
        if not file_path:
            return
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(file_path)
            print(f"轻量级搜索对话框: 已复制路径 '{file_path}'")
        except Exception as e:
            print(f"复制路径失败: {str(e)}")
    
    def _fulltext_search_in_main(self):
        """在主窗口中进行全文搜索"""
        search_text = self.search_line_edit.text().strip()
        if search_text:
            print(f"轻量级搜索对话框: 在主窗口中进行全文搜索 '{search_text}'")
            self.open_main_window.emit(search_text)
            self.close()
        else:
            print("轻量级搜索对话框: 尝试全文搜索，但搜索文本为空")
    
    def set_search_results(self, results):
        """设置搜索结果
        
        Args:
            results: 搜索结果列表，每项应包含标题、路径和预览内容
        """
        # 清空结果列表
        self.results_list.clear()
        
        if not results:
            self.status_label.setText("未找到结果")
            return
        
        # 添加结果
        for result in results:
            title = result.get('title', '未知标题')
            path = result.get('path', '')
            preview = result.get('preview', '')
            icon_path = result.get('icon', None)
            
            item = SearchResultItem(title, path, icon_path, preview)
            self.results_list.addItem(item)
        
        # 更新状态
        self.status_label.setText(f"找到 {len(results)} 个结果")
        
        # 选中第一项
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)


# 简单测试代码
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    dialog = QuickSearchDialog()
    
    # 添加一些测试数据
    results = [
        {
            'title': '示例文档1.docx', 
            'path': 'D:/文档/示例文档1.docx',
            'preview': '这是一个示例文档，包含一些关键词...'
        },
        {
            'title': '测试报告.pdf', 
            'path': 'D:/文档/测试报告.pdf',
            'preview': '测试报告中包含了相关关键词的描述和分析...'
        },
        {
            'title': '会议记录.txt', 
            'path': 'D:/文档/会议记录.txt',
            'preview': '在昨天的会议中讨论了关键词相关的项目进展...'
        }
    ]
    
    # 连接测试信号
    dialog.search_executed.connect(lambda text: print(f"搜索: {text}"))
    dialog.item_activated.connect(lambda path: print(f"打开: {path}"))
    dialog.open_main_window.connect(lambda text: print(f"在主窗口打开: {text}"))
    dialog.open_file_signal.connect(lambda path: print(f"打开文件: {path}"))
    
    # 设置测试结果
    dialog.set_search_results(results)
    
    dialog.show()
    
    sys.exit(app.exec()) 