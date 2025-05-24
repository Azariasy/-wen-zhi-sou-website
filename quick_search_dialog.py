"""
文智搜优化版快速搜索窗口

优化内容：
1. 更现代化的UI设计
2. 更友好的交互体验
3. 更直观的操作方式
4. 支持实时搜索
5. 改进的键盘导航
"""

import sys
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QListWidget, QListWidgetItem, QLabel, QPushButton, 
                             QGraphicsDropShadowEffect, QApplication, QWidget, QMenu,
                             QProgressBar, QSizePolicy, QFrame)
from PySide6.QtCore import Qt, QSize, QEvent, QPoint, QSettings, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QColor, QFont, QPalette, QKeyEvent, QDesktopServices, QAction, QPainter, QPixmap
from pathlib import Path

class SearchResultItem(QListWidgetItem):
    """现代化搜索结果列表项"""
    
    def __init__(self, title, path, icon_path=None, content_preview="", file_type=""):
        super().__init__()
        
        self.title = title
        self.path = path
        self.content_preview = content_preview
        self.file_type = file_type
        
        # 设置显示文本 - 更美观的格式
        display_text = f"📄 {title}"
        if file_type:
            display_text = f"{self._get_file_icon(file_type)} {title}"
        elif path:
            # 从文件路径获取文件类型
            file_ext = Path(path).suffix[1:] if path else ''
            if file_ext:
                display_text = f"{self._get_file_icon(file_ext)} {title}"
        
        self.setText(display_text)
        
        # 设置图标（如果有）
        if icon_path and os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        
        # 存储额外数据
        self.setData(Qt.UserRole, path)
        self.setData(Qt.UserRole + 1, content_preview)
        
        # 设置工具提示 - 更丰富的信息
        tooltip_text = f"📄 {title}\n📁 {path}"
        if content_preview:
            preview_short = content_preview[:100] + "..." if len(content_preview) > 100 else content_preview
            tooltip_text += f"\n\n💬 预览:\n{preview_short}"
        self.setToolTip(tooltip_text)
        
        # 设置项目高度
        self.setSizeHint(QSize(0, 50))
    
    def _get_file_icon(self, file_type):
        """根据文件类型返回对应的图标"""
        icon_map = {
            'docx': '📝', 'doc': '📝',
            'xlsx': '📊', 'xls': '📊', 'csv': '📊',
            'pptx': '📊', 'ppt': '📊',
            'pdf': '📋',
            'txt': '📄', 'md': '📄',
            'zip': '📦', 'rar': '📦', '7z': '📦',
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
            'mp4': '🎬', 'avi': '🎬', 'mkv': '🎬',
            'mp3': '🎵', 'wav': '🎵', 'flac': '🎵',
            'html': '🌐', 'htm': '🌐',
            'eml': '📧', 'msg': '📧'
        }
        return icon_map.get(file_type.lower(), '📄')

class QuickSearchDialog(QDialog):
    """优化版快速搜索对话框"""
    
    # 定义信号
    search_executed = Signal(str)        # 执行搜索信号
    item_activated = Signal(str)         # 项目激活（打开）信号
    open_main_window = Signal(str)       # 在主窗口中打开搜索信号
    open_file_signal = Signal(str)       # 打开文件信号
    open_folder_signal = Signal(str)     # 打开文件夹信号
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # 设置窗口基本属性
        self.setWindowTitle("快速搜索")
        self.setMinimumSize(600, 450)
        self.setMaximumSize(800, 700)
        self.resize(650, 500)
        
        # 窗口拖动相关
        self._dragging = False
        self._drag_start_position = QPoint()
        
        # 实时搜索定时器
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        # 加载设置
        self.settings = QSettings("WenZhiSou", "DocumentSearch")
        
        # 初始化UI
        self._setup_ui()
        
        # 连接信号
        self._connect_signals()
        
        # 应用样式
        self._apply_styles()
        
        # 居中显示
        self._center_on_screen()
        
        # 入场动画
        self._setup_entrance_animation()
    
    def _setup_ui(self):
        """设置现代化UI组件"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 顶部标题栏
        self._create_title_bar(layout)
        
        # 搜索区域
        self._create_search_area(layout)
        
        # 结果区域
        self._create_results_area(layout)
        
        # 底部操作栏
        self._create_bottom_bar(layout)
        
        # 设置焦点到搜索框
        self.search_line_edit.setFocus()
    
    def _create_title_bar(self, layout):
        """创建现代化标题栏"""
        title_frame = QFrame()
        title_frame.setObjectName("titleFrame")
        title_frame.setFixedHeight(50)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(20, 10, 15, 10)
        
        # 搜索图标和标题
        title_container = QHBoxLayout()
        
        # 搜索图标
        self.search_icon_label = QLabel("🔍")
        self.search_icon_label.setObjectName("searchIcon")
        self.search_icon_label.setFixedSize(24, 24)
        title_container.addWidget(self.search_icon_label)
        
        # 标题
        self.title_label = QLabel("文智搜")
        self.title_label.setObjectName("titleLabel")
        title_container.addWidget(self.title_label)
        
        # 副标题
        self.subtitle_label = QLabel("快速搜索")
        self.subtitle_label.setObjectName("subtitleLabel")
        title_container.addWidget(self.subtitle_label)
        
        title_layout.addLayout(title_container)
        title_layout.addStretch()
        
        # 最小化和关闭按钮
        button_container = QHBoxLayout()
        button_container.setSpacing(5)
        
        # 最小化按钮
        self.minimize_button = QPushButton("−")
        self.minimize_button.setObjectName("minimizeButton")
        self.minimize_button.setFixedSize(30, 25)
        button_container.addWidget(self.minimize_button)
        
        # 关闭按钮
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(30, 25)
        button_container.addWidget(self.close_button)
        
        title_layout.addLayout(button_container)
        layout.addWidget(title_frame)
    
    def _create_search_area(self, layout):
        """创建搜索区域"""
        search_frame = QFrame()
        search_frame.setObjectName("searchFrame")
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(20, 15, 20, 15)
        
        # 搜索提示
        self.search_hint_label = QLabel("输入关键词开始搜索，支持实时搜索")
        self.search_hint_label.setObjectName("searchHint")
        search_layout.addWidget(self.search_hint_label)
        
        # 搜索框容器
        search_container = QHBoxLayout()
        search_container.setSpacing(10)
        
        # 搜索框
        self.search_line_edit = QLineEdit()
        self.search_line_edit.setObjectName("modernSearchLineEdit")
        self.search_line_edit.setPlaceholderText("🔍 输入搜索内容...")
        self.search_line_edit.setMinimumHeight(40)
        search_container.addWidget(self.search_line_edit)
        
        # 清空按钮
        self.clear_button = QPushButton("✕")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.setFixedSize(35, 35)
        self.clear_button.setVisible(False)  # 初始隐藏
        search_container.addWidget(self.clear_button)
        
        search_layout.addLayout(search_container)
        
        # 搜索进度条
        self.search_progress = QProgressBar()
        self.search_progress.setObjectName("searchProgress")
        self.search_progress.setVisible(False)
        self.search_progress.setMinimumHeight(3)
        self.search_progress.setMaximumHeight(3)
        search_layout.addWidget(self.search_progress)
        
        layout.addWidget(search_frame)
    
    def _create_results_area(self, layout):
        """创建结果显示区域"""
        results_frame = QFrame()
        results_frame.setObjectName("resultsFrame")
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(20, 0, 20, 10)
        
        # 结果标题
        self.results_header = QLabel("搜索结果")
        self.results_header.setObjectName("resultsHeader")
        results_layout.addWidget(self.results_header)
        
        # 结果列表
        self.results_list = QListWidget()
        self.results_list.setObjectName("modernResultsList")
        self.results_list.setAlternatingRowColors(True)
        results_layout.addWidget(self.results_list)
        
        # 空状态提示
        self.empty_state_label = QLabel("🔍\n\n开始输入以搜索文档\n支持文件名和内容搜索")
        self.empty_state_label.setObjectName("emptyStateLabel")
        self.empty_state_label.setAlignment(Qt.AlignCenter)
        self.empty_state_label.setVisible(True)
        results_layout.addWidget(self.empty_state_label)
        
        layout.addWidget(results_frame)
    
    def _create_bottom_bar(self, layout):
        """创建底部操作栏"""
        bottom_frame = QFrame()
        bottom_frame.setObjectName("bottomFrame")
        bottom_frame.setFixedHeight(60)
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(20, 10, 20, 10)
        
        # 状态信息
        self.status_label = QLabel("准备就绪")
        self.status_label.setObjectName("statusLabel")
        bottom_layout.addWidget(self.status_label)
        
        bottom_layout.addStretch()
        
        # 操作按钮组
        button_container = QHBoxLayout()
        button_container.setSpacing(10)
        
        # 主窗口搜索按钮
        self.main_window_button = QPushButton("📋 在主窗口中搜索")
        self.main_window_button.setObjectName("primaryButton")
        self.main_window_button.setMinimumHeight(35)
        self.main_window_button.setDefault(False)
        self.main_window_button.setAutoDefault(False)
        button_container.addWidget(self.main_window_button)
        
        bottom_layout.addLayout(button_container)
        layout.addWidget(bottom_frame)
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 标题栏按钮
        self.minimize_button.clicked.connect(self.showMinimized)
        self.close_button.clicked.connect(self.close)
        
        # 搜索相关
        self.search_line_edit.textChanged.connect(self._on_search_text_changed)
        self.search_line_edit.returnPressed.connect(self._on_search_enter)
        self.clear_button.clicked.connect(self._clear_search)
        
        # 结果列表
        self.results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.results_list.itemActivated.connect(self._on_item_activated)
        
        # 底部按钮
        self.main_window_button.clicked.connect(self._on_main_window_button)
        
        # 右键菜单
        self.results_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_list.customContextMenuRequested.connect(self._show_context_menu)
    
    def _apply_styles(self):
        """应用现代化样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                border-radius: 12px;
            }
            
            #titleFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d3d3d, stop:1 #353535);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid #4a4a4a;
            }
            
            #searchIcon {
                font-size: 18px;
            }
            
            #titleLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                margin-left: 8px;
            }
            
            #subtitleLabel {
                font-size: 12px;
                color: #b0b0b0;
                margin-left: 5px;
                font-style: italic;
            }
            
            #minimizeButton, #closeButton {
                border: none;
                background: transparent;
                color: #c0c0c0;
                font-size: 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            
            #minimizeButton:hover {
                background-color: #4a4a4a;
                color: #ffffff;
            }
            
            #closeButton:hover {
                background-color: #d32f2f;
                color: #ffffff;
            }
            
            #searchFrame {
                background-color: #2b2b2b;
            }
            
            #searchHint {
                color: #888888;
                font-size: 11px;
                margin-bottom: 8px;
            }
            
            #modernSearchLineEdit {
                padding: 12px 16px;
                border-radius: 20px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #404040, stop:1 #383838);
                color: #ffffff;
                border: 2px solid #555555;
                font-size: 14px;
            }
            
            #modernSearchLineEdit:focus {
                border: 2px solid #007acc;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #454545, stop:1 #3d3d3d);
            }
            
            #clearButton {
                border: none;
                background: transparent;
                color: #888888;
                font-size: 12px;
                border-radius: 17px;
            }
            
            #clearButton:hover {
                background-color: #555555;
                color: #ffffff;
            }
            
            #searchProgress {
                background-color: #404040;
                border: none;
                border-radius: 1px;
            }
            
            #searchProgress::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #007acc, stop:1 #0056b3);
                border-radius: 1px;
            }
            
            #resultsFrame {
                background-color: #2b2b2b;
            }
            
            #resultsHeader {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                margin-bottom: 8px;
                margin-top: 10px;
            }
            
            #modernResultsList {
                background-color: #323232;
                alternate-background-color: #373737;
                color: #ffffff;
                border-radius: 8px;
                border: 1px solid #4a4a4a;
                outline: none;
                font-size: 13px;
            }
            
            #modernResultsList::item {
                padding: 12px;
                border-bottom: 1px solid #404040;
                min-height: 35px;
            }
            
            #modernResultsList::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007acc, stop:1 #0056b3);
                color: #ffffff;
            }
            
            #modernResultsList::item:hover {
                background-color: #404040;
            }
            
            #emptyStateLabel {
                color: #666666;
                font-size: 14px;
                line-height: 1.5;
            }
            
            #bottomFrame {
                background-color: #2b2b2b;
                border-top: 1px solid #4a4a4a;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }
            
            #statusLabel {
                color: #888888;
                font-size: 11px;
            }
            
            #primaryButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007acc, stop:1 #0056b3);
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            
            #primaryButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0086e6, stop:1 #0066cc);
            }
            
            #primaryButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0056b3, stop:1 #004080);
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
    
    def _center_on_screen(self):
        """在屏幕中央显示窗口"""
        screen = QApplication.primaryScreen().geometry()
        window = self.geometry()
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        self.move(x, y)
    
    def _setup_entrance_animation(self):
        """设置入场动画"""
        # 初始设置窗口透明和稍微缩小
        self.setWindowOpacity(0.0)
        original_size = self.size()
        self.resize(int(original_size.width() * 0.9), int(original_size.height() * 0.9))
        
        # 透明度动画
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(200)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 启动动画
        self.opacity_animation.start()
        
        # 恢复原始尺寸
        QTimer.singleShot(50, lambda: self.resize(original_size))
    
    def _on_search_text_changed(self, text):
        """搜索文本改变时的处理"""
        # 显示/隐藏清空按钮
        self.clear_button.setVisible(bool(text.strip()))
        
        # 重置搜索定时器（实时搜索）
        self.search_timer.stop()
        if text.strip():
            self.search_timer.start(500)  # 500ms延迟
            self.search_hint_label.setText("正在输入...")
        else:
            self._show_empty_state()
    
    def _on_search_enter(self):
        """处理回车键搜索"""
        self.search_timer.stop()
        self._perform_search()
    
    def _perform_search(self):
        """执行搜索"""
        search_text = self.search_line_edit.text().strip()
        if not search_text:
            self._show_empty_state()
            return
        
        # 显示搜索进度
        self._show_search_progress()
        
        # 更新提示
        self.search_hint_label.setText(f"搜索: {search_text}")
        
        # 发出搜索信号
        self.search_executed.emit(search_text)
        
        print(f"优化版快速搜索: 执行搜索 '{search_text}'")
    
    def _show_search_progress(self):
        """显示搜索进度"""
        self.search_progress.setVisible(True)
        self.search_progress.setRange(0, 0)  # 无限进度条
        self.empty_state_label.setVisible(False)
        self.results_list.setVisible(True)
    
    def _hide_search_progress(self):
        """隐藏搜索进度"""
        self.search_progress.setVisible(False)
    
    def _show_empty_state(self):
        """显示空状态"""
        self.empty_state_label.setVisible(True)
        self.results_list.setVisible(False)
        self.search_hint_label.setText("输入关键词开始搜索，支持实时搜索")
        self.status_label.setText("准备就绪")
        self.results_header.setText("搜索结果")
    
    def _clear_search(self):
        """清空搜索"""
        self.search_line_edit.clear()
        self.search_line_edit.setFocus()
        self._show_empty_state()
    
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
            delta = event.position().toPoint() - self._drag_start_position
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
        """处理键盘事件 - 改进的导航体验"""
        key = event.key()
        
        # Escape键关闭窗口
        if key == Qt.Key_Escape:
            self.close()
            event.accept()
            return
        
        # 回车键处理
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            if self.search_line_edit.hasFocus():
                # 如果有搜索结果，选择第一个结果并打开
                if self.results_list.count() > 0:
                    self.results_list.setCurrentRow(0)
                    self._on_item_activated(self.results_list.currentItem())
                else:
                    # 否则执行搜索
                    self._on_search_enter()
                event.accept()
                return
            elif self.results_list.hasFocus() and self.results_list.currentItem():
                self._on_item_activated(self.results_list.currentItem())
                event.accept()
                return
        
        # 上下键导航
        elif key == Qt.Key_Down:
            if self.search_line_edit.hasFocus() and self.results_list.count() > 0:
                self.results_list.setCurrentRow(0)
                self.results_list.setFocus()
                event.accept()
                return
        elif key == Qt.Key_Up:
            if self.results_list.hasFocus() and self.results_list.currentRow() == 0:
                self.search_line_edit.setFocus()
                event.accept()
                return
        
        # Ctrl+F 聚焦搜索框
        elif key == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
            self.search_line_edit.setFocus()
            self.search_line_edit.selectAll()
            event.accept()
            return
        
        # Ctrl+W 或 Alt+F4 关闭窗口
        elif ((key == Qt.Key_W and event.modifiers() == Qt.ControlModifier) or
              (key == Qt.Key_F4 and event.modifiers() == Qt.AltModifier)):
            self.close()
            event.accept()
            return
        
        super().keyPressEvent(event)
    
    # 为了兼容原有接口，保留原方法名
    def _on_search(self):
        """搜索（兼容原接口）"""
        self._on_search_enter()
    
    def _on_item_double_clicked(self, item):
        """处理双击事件"""
        if not item:
            return
        
        file_path = item.data(Qt.UserRole)
        if file_path:
            print(f"优化版快速搜索: 双击打开文件 '{file_path}'")
            self.open_file_signal.emit(file_path)
            self.close()  # 打开文件后关闭对话框
    
    def _on_item_activated(self, item):
        """处理激活事件（回车键）"""
        if not item:
            return
        
        file_path = item.data(Qt.UserRole)
        if file_path:
            print(f"优化版快速搜索: 激活打开文件 '{file_path}'")
            self.open_file_signal.emit(file_path)
            self.close()  # 打开文件后关闭对话框
    
    def _on_main_window_button(self):
        """处理在主窗口中打开按钮"""
        search_text = self.search_line_edit.text().strip()
        if search_text:
            print(f"优化版快速搜索: 在主窗口中打开搜索 '{search_text}'")
            self.open_main_window.emit(search_text)
            self.close()
        else:
            # 即使没有搜索文本，也可以打开主窗口
            print("优化版快速搜索: 打开主窗口")
            self.open_main_window.emit("")
            self.close()
    
    def _show_context_menu(self, position):
        """显示优化的右键菜单"""
        item = self.results_list.itemAt(position)
        if not item:
            return
        
        file_path = item.data(Qt.UserRole)
        if not file_path:
            return
        
        context_menu = QMenu(self)
        context_menu.setStyleSheet("""
            QMenu {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QMenu::item {
                padding: 8px 16px;
            }
            QMenu::item:selected {
                background-color: #007acc;
            }
        """)
        
        # 打开文件
        open_file_action = QAction("📄 打开文件", self)
        open_file_action.triggered.connect(lambda: self._open_file(file_path))
        context_menu.addAction(open_file_action)
        
        # 打开文件所在目录
        open_folder_action = QAction("📁 打开文件所在目录", self)
        open_folder_action.triggered.connect(lambda: self._open_folder(file_path))
        context_menu.addAction(open_folder_action)
        
        context_menu.addSeparator()
        
        # 复制文件路径
        copy_path_action = QAction("📋 复制文件路径", self)
        copy_path_action.triggered.connect(lambda: self._copy_path(file_path))
        context_menu.addAction(copy_path_action)
        
        # 在主窗口中搜索
        main_search_action = QAction("🔍 在主窗口中搜索", self)
        main_search_action.triggered.connect(self._on_main_window_button)
        context_menu.addAction(main_search_action)
        
        context_menu.exec(self.results_list.mapToGlobal(position))
    
    def _open_file(self, file_path):
        """打开文件"""
        if file_path:
            self.open_file_signal.emit(file_path)
            self.close()
    
    def _open_folder(self, file_path):
        """打开文件所在目录"""
        if file_path:
            folder_path = str(Path(file_path).parent)
            self.open_folder_signal.emit(folder_path)
    
    def _copy_path(self, file_path):
        """复制文件路径到剪贴板"""
        if file_path:
            clipboard = QApplication.clipboard()
            clipboard.setText(file_path)
            self.status_label.setText("已复制文件路径")
            QTimer.singleShot(2000, lambda: self.status_label.setText("准备就绪"))
    
    def _fulltext_search_in_main(self):
        """在主窗口中进行全文搜索（兼容原接口）"""
        self._on_main_window_button()
    
    def set_search_results(self, results):
        """设置搜索结果"""
        self._hide_search_progress()
        self.results_list.clear()
        
        if not results:
            self.status_label.setText("未找到匹配结果")
            self.results_header.setText("搜索结果 (0)")
            self.empty_state_label.setText("🔍\n\n未找到匹配的文件\n请尝试其他关键词")
            self.empty_state_label.setVisible(True)
            self.results_list.setVisible(False)
            return
        
        # 显示结果
        self.empty_state_label.setVisible(False)
        self.results_list.setVisible(True)
        
        for result in results:
            title = result.get('title', '未知标题')
            path = result.get('path', '')
            preview = result.get('preview', '')
            file_type = Path(path).suffix[1:] if path else ''
            
            # 兼容原有接口：如果result有content_preview字段，也要支持
            if 'content_preview' in result:
                preview = result['content_preview']
            
            item = SearchResultItem(title, path, None, preview, file_type)
            self.results_list.addItem(item)
        
        # 更新状态
        self.status_label.setText(f"找到 {len(results)} 个匹配结果")
        self.results_header.setText(f"搜索结果 ({len(results)})")
        
        # 选中第一项
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)


# 简单测试代码
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    dialog = QuickSearchDialog()
    
    # 添加测试数据
    test_results = [
        {
            'title': '项目计划.docx', 
            'path': 'D:/文档/项目计划.docx',
            'preview': '这是一个重要的项目计划文档，包含详细的时间表和任务分配...'
        },
        {
            'title': '财务报告2024.xlsx', 
            'path': 'D:/文档/财务报告2024.xlsx',
            'preview': '2024年第一季度财务数据统计和分析报告...'
        },
        {
            'title': '会议纪要.txt', 
            'path': 'D:/文档/会议纪要.txt',
            'preview': '周例会讨论内容和决议事项记录...'
        }
    ]
    
    # 连接测试信号
    dialog.search_executed.connect(lambda text: print(f"搜索: {text}"))
    dialog.open_file_signal.connect(lambda path: print(f"打开文件: {path}"))
    dialog.open_main_window.connect(lambda text: print(f"在主窗口打开: {text}"))
    
    # 延迟设置测试结果以演示搜索效果
    QTimer.singleShot(2000, lambda: dialog.set_search_results(test_results))
    
    dialog.show()
    sys.exit(app.exec()) 