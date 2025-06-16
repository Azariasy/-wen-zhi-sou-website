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
                             QProgressBar, QSizePolicy, QFrame, QMessageBox, QStyledItemDelegate, QStyle)
from PySide6.QtCore import Qt, QSize, QEvent, QPoint, QSettings, Signal, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QIcon, QColor, QFont, QPalette, QKeyEvent, QDesktopServices, QAction, QPainter, QPixmap, QClipboard, QFontMetrics
from pathlib import Path

# 导入主程序的常量
from search_gui_pyside import ORGANIZATION_NAME, APPLICATION_NAME

class SearchResultDelegate(QStyledItemDelegate):
    """自定义委托，支持不同字体大小的文本显示"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def paint(self, painter, option, index):
        """自定义绘制方法"""
        painter.save()
        
        # 获取显示文本
        text = index.data(Qt.DisplayRole)
        if not text:
            painter.restore()
            return
            
        # 分割文本为两行
        lines = text.split('\n', 1)
        if len(lines) < 2:
            # 如果只有一行，使用默认绘制
            super().paint(painter, option, index)
            painter.restore()
            return
            
        # 设置绘制区域
        rect = option.rect
        
        # 绘制背景
        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, option.palette.highlight())
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(rect, option.palette.alternateBase())
        else:
            painter.fillRect(rect, option.palette.base())
        
        # 设置文本颜色
        if option.state & QStyle.State_Selected:
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())
        
        # 绘制第一行（文件名）- 使用精致字体
        title_font = QFont()
        title_font.setPointSize(9)  # 再次减小到9，更精致
        title_font.setBold(True)
        painter.setFont(title_font)
        
        title_rect = QRect(rect.left() + 10, rect.top() + 5, rect.width() - 20, 16)  # 适应更小字体
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, lines[0])
        
        # 绘制第二行（路径和时间）- 使用更小字体
        if len(lines) > 1:
            detail_font = QFont()
            detail_font.setPointSize(7)  # 再次减小到7，更精致紧凑
            painter.setFont(detail_font)
            
            # 设置较淡的颜色
            detail_color = painter.pen().color()
            detail_color.setAlpha(130)  # 稍微调淡一些
            painter.setPen(detail_color)
            
            detail_rect = QRect(rect.left() + 10, rect.top() + 23, rect.width() - 20, 14)  # 适应更小字体和高度
            painter.drawText(detail_rect, Qt.AlignLeft | Qt.AlignVCenter, lines[1])
        
        painter.restore()
    
    def sizeHint(self, option, index):
        """返回项目的建议大小"""
        return QSize(0, 44)  # 进一步减小到44，更紧凑协调

class SearchResultItem(QListWidgetItem):
    """现代化搜索结果列表项 - 性能优化版"""
    
    def __init__(self, title, path, icon_path=None, content_preview="", file_type=""):
        super().__init__()
        
        self.title = title
        self.path = path
        self.content_preview = content_preview
        self.file_type = file_type
        
        # 设置项目标志 - 确保可以被选择和启用
        self.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        
        # 性能优化：延迟文件信息获取，只在需要时获取
        # 先设置基本显示文本，避免同步I/O操作
        display_text = self._create_fast_display_text(title, path, file_type)
        self.setText(display_text)
        
        # 设置图标（如果有）
        if icon_path and os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        
        # 存储额外数据
        self.setData(Qt.UserRole, path)
        self.setData(Qt.UserRole + 1, content_preview)
        
        # 设置项目高度 - 紧凑显示（文件名+路径+时间）
        self.setSizeHint(QSize(0, 44))  # 更紧凑协调的高度，适应两行信息
    
    def _create_fast_display_text(self, title, path, file_type):
        """创建快速显示文本（包含路径和修改时间）"""
        # 获取文件图标
        icon = self._get_file_icon(file_type if file_type else Path(path).suffix[1:] if path else '')
        
        # 获取文件信息
        file_info = self._get_file_info(path)
        
        # 构建显示文本：文件名 + 路径 + 修改时间
        if path:
            # 显示相对路径（更简洁）
            try:
                # 尝试获取相对于用户目录的路径
                from pathlib import Path
                import os
                home_path = Path.home()
                file_path_obj = Path(path)
                
                try:
                    # 如果在用户目录下，显示相对路径
                    relative_path = file_path_obj.relative_to(home_path)
                    display_path = f"~/{relative_path.parent}"
                except ValueError:
                    # 不在用户目录下，显示完整路径但简化
                    display_path = str(file_path_obj.parent)
                    # 如果路径太长，只显示最后两级目录
                    path_parts = Path(display_path).parts
                    if len(path_parts) > 2:
                        display_path = f".../{path_parts[-2]}/{path_parts[-1]}"
            except:
                display_path = str(Path(path).parent) if path else '未知目录'
        else:
            display_path = '未知目录'
        
        # 构建多行显示文本（使用更紧凑的格式）
        display_text = f"{icon} {title}\n    📁 {display_path} • 🕒 {file_info['modified_time']}"
        
        return display_text
    
    def get_detailed_info(self):
        """按需获取详细文件信息（延迟加载）"""
        if not hasattr(self, '_detailed_info'):
            self._detailed_info = self._get_file_info(self.path)
        return self._detailed_info
    
    def _get_file_info(self, file_path):
        """获取文件信息（延迟调用）"""
        import os
        from datetime import datetime
        
        if not file_path or not os.path.exists(file_path):
            return {
                'size': 0,
                'modified_time': '未知',
                'exists': False
            }
        
        try:
            stat = os.stat(file_path)
            size = stat.st_size
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            return {
                'size': size,
                'size_str': self._format_file_size(size),
                'modified_time': modified_time.strftime('%Y-%m-%d %H:%M'),
                'exists': True
            }
        except Exception as e:
            return {
                'size': 0,
                'size_str': '未知',
                'modified_time': '未知',
                'exists': False
            }
    
    def _format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    def _get_file_icon(self, file_type):
        """根据文件类型返回对应的图标（缓存优化）"""
        # 使用类级别缓存避免重复计算
        if not hasattr(SearchResultItem, '_icon_cache'):
            SearchResultItem._icon_cache = {
            # 文档类型
            'docx': '📝', 'doc': '📝',
            'xlsx': '📊', 'xls': '📊', 'csv': '📊',
                'pptx': '📋', 'ppt': '📋',
                'pdf': '📕',
            'txt': '📄', 'md': '📄', 'rtf': '📄',
            'zip': '📦', 'rar': '📦', '7z': '📦',
            'html': '🌐', 'htm': '🌐',
            'eml': '📧', 'msg': '📧',
            
            # 视频文件
            'mp4': '🎬', 'avi': '🎬', 'mkv': '🎬', 'wmv': '🎬', 
            'mov': '🎬', 'flv': '🎬', 'webm': '🎬', 'm4v': '🎬',
            
            # 音频文件
            'mp3': '🎵', 'wav': '🎵', 'flac': '🎵', 'aac': '🎵',
            'ogg': '🎵', 'wma': '🎵', 'm4a': '🎵',
            
            # 图片文件
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
            'bmp': '🖼️', 'tiff': '🖼️', 'webp': '🖼️', 'svg': '🖼️'
        }
        
        return SearchResultItem._icon_cache.get(file_type.lower(), '📄')

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
        self.setWindowTitle("文智搜 - 快速搜索")
        self.setMinimumSize(600, 450)
        self.setMaximumSize(800, 700)
        self.resize(650, 500)
        
        # 窗口拖动相关
        self._dragging = False
        self._drag_start_position = QPoint()
        
        # 加载设置
        self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        
        # 获取当前主题
        self.current_theme = self.settings.value("ui/theme", "现代蓝")
        
        # 初始化UI
        self._setup_ui()
        
        # 连接信号
        self._connect_signals()
        
        # 应用主题样式
        self._apply_theme_styles()
        
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
        
        # 搜索提示 - 明确说明这是文件名搜索
        self.search_hint_label = QLabel("🗂️ 快速文件名搜索 - 输入关键词快速找到文件")
        self.search_hint_label.setObjectName("searchHint")
        search_layout.addWidget(self.search_hint_label)
        
        # 搜索框容器
        search_container = QHBoxLayout()
        search_container.setSpacing(10)
        
        # 搜索框
        self.search_line_edit = QLineEdit()
        self.search_line_edit.setObjectName("modernSearchLineEdit")
        self.search_line_edit.setPlaceholderText("🔍 输入文件名或关键词...")
        self.search_line_edit.setMinimumHeight(40)
        search_container.addWidget(self.search_line_edit)
        
        # 清空按钮
        self.clear_button = QPushButton("✕")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.setFixedSize(35, 35)
        self.clear_button.setVisible(False)  # 初始隐藏
        search_container.addWidget(self.clear_button)
        
        search_layout.addLayout(search_container)
        
        # 搜索说明
        help_text = "💡 支持文件名模糊搜索，实时显示结果。需要全文搜索请使用主窗口。"
        self.help_label = QLabel(help_text)
        self.help_label.setObjectName("helpLabel")
        self.help_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 5px;")
        search_layout.addWidget(self.help_label)
        
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
        
        # 设置自定义委托以支持不同字体大小
        self.results_delegate = SearchResultDelegate(self.results_list)
        self.results_list.setItemDelegate(self.results_delegate)
        
        # 修复关键配置
        # 1. 启用自定义右键菜单
        self.results_list.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # 2. 设置正确的选择模式
        self.results_list.setSelectionMode(QListWidget.SingleSelection)
        
        # 3. 设置选择行为
        self.results_list.setSelectionBehavior(QListWidget.SelectRows)
        
        # 4. 设置焦点策略（移除鼠标跟踪，避免与选择冲突）
        self.results_list.setFocusPolicy(Qt.StrongFocus)
        
        results_layout.addWidget(self.results_list)
        
        # 空状态提示
        self.empty_state_label = QLabel(
            "🔍 输入关键词后按回车键搜索\n\n"
            "💡 操作提示：\n"
            "• Enter: 执行搜索\n"
            "• 双击结果: 打开文件\n"
            "• 右键结果: 更多选项\n"
            "• Ctrl+Enter: 主窗口搜索\n"
            "• F1: 查看完整帮助"
        )
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
        self.status_label = QLabel("就绪 - 快速文件名搜索")
        self.status_label.setObjectName("statusLabel")
        bottom_layout.addWidget(self.status_label)
        
        bottom_layout.addStretch()
        
        # 操作提示和按钮组
        button_container = QHBoxLayout()
        button_container.setSpacing(15)
        
        # 快捷键提示
        shortcut_label = QLabel("Enter: 搜索 | Ctrl+Enter: 主窗口 | F1: 帮助 | Esc: 关闭")
        shortcut_label.setObjectName("statusLabel")
        shortcut_label.setStyleSheet("color: #666; font-size: 11px;")
        button_container.addWidget(shortcut_label)
        
        # 主窗口搜索按钮
        self.main_window_button = QPushButton("🖥️ 主窗口搜索")
        self.main_window_button.setObjectName("primaryButton")
        self.main_window_button.setMinimumHeight(35)
        self.main_window_button.setDefault(False)
        self.main_window_button.setAutoDefault(False)
        self.main_window_button.setToolTip("在主窗口中搜索，支持全文搜索和高级功能")
        button_container.addWidget(self.main_window_button)
        
        bottom_layout.addLayout(button_container)
        layout.addWidget(bottom_frame)
    
    def _connect_signals(self):
        """连接信号"""
        # 窗口控制按钮
        self.minimize_button.clicked.connect(self.showMinimized)
        self.close_button.clicked.connect(self.close)
        
        # 搜索相关 - 移除自动搜索，只保留回车键搜索
        self.search_line_edit.textChanged.connect(self._on_search_text_changed_simple)
        self.search_line_edit.returnPressed.connect(self._on_search_enter)
        self.clear_button.clicked.connect(self._clear_search)
        
        # 结果列表
        self.results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.results_list.itemActivated.connect(self._on_item_activated)
        self.results_list.customContextMenuRequested.connect(self._show_context_menu)
        
        # 底部按钮
        if hasattr(self, 'main_window_button'):
            self.main_window_button.clicked.connect(self._on_main_window_button)
    
    def _apply_theme_styles(self):
        """应用主题样式"""
        colors = self._get_theme_colors()
        
        # 动态生成样式表
        style = f"""
            QDialog {{
                background-color: {colors['dialog_bg']};
                border-radius: 12px;
            }}
            
            #titleFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {colors['title_bg_start']}, stop:1 {colors['title_bg_end']});
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid {colors['border']};
            }}
            
            #searchIcon {{
                font-size: 18px;
                color: {colors['text_primary']};
            }}
            
            #titleLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {colors['surface']};
                margin-left: 8px;
            }}
            
            #subtitleLabel {{
                font-size: 12px;
                color: {colors['text_secondary']};
                margin-left: 5px;
                font-style: italic;
            }}
            
            #minimizeButton, #closeButton {{
                border: none;
                background: transparent;
                color: {colors['text_secondary']};
                font-size: 16px;
                font-weight: bold;
                border-radius: 4px;
                padding: 4px 8px;
            }}
            
            #minimizeButton:hover {{
                background-color: {colors['hover']};
                color: {colors['text_primary']};
            }}
            
            #closeButton:hover {{
                background-color: {colors['error']};
                color: {colors['surface']};
            }}
            
            #searchFrame {{
                background-color: {colors['dialog_bg']};
            }}
            
            #searchHint {{
                color: {colors['text_secondary']};
                font-size: 11px;
                margin-bottom: 8px;
            }}
            
            #modernSearchLineEdit {{
                padding: 12px 16px;
                border-radius: 20px;
                background-color: {colors['search_bg']};
                color: {colors['text_primary']};
                border: 2px solid {colors['search_border']};
                font-size: 14px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                min-height: 24px;
                line-height: 1.2;
            }}
            
            #modernSearchLineEdit:focus {{
                border: 2px solid {colors['search_focus']};
                background-color: {colors['surface']};
            }}
            
            #clearButton {{
                border: none;
                background: transparent;
                color: {colors['text_secondary']};
                font-size: 12px;
                border-radius: 17px;
                padding: 4px 8px;
            }}
            
            #clearButton:hover {{
                background-color: {colors['hover']};
                color: {colors['text_primary']};
            }}
            
            #searchProgress {{
                background-color: {colors['border']};
                border: none;
                border-radius: 2px;
            }}
            
            #searchProgress::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {colors['primary']}, stop:1 {colors['secondary']});
                border-radius: 2px;
            }}
            
            #resultsFrame {{
                background-color: {colors['dialog_bg']};
            }}
            
            #resultsHeader {{
                color: {colors['text_primary']};
                font-size: 13px;
                font-weight: bold;
                margin-bottom: 8px;
                margin-top: 10px;
            }}
            
            #modernResultsList {{
                background-color: {colors['results_bg']};
                alternate-background-color: {colors['hover']};
                color: {colors['text_primary']};
                border-radius: 8px;
                border: 1px solid {colors['border']};
                outline: none;
                font-size: 13px;
            }}
            
            #modernResultsList::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {colors['border']};
                min-height: 40px;
                line-height: 1.3;
            }}
            
            #modernResultsList::item:hover {{
                background-color: {colors['item_hover']};
                color: {colors['text_primary']};
            }}
            
            #modernResultsList::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {colors['item_selected']}, stop:1 {colors['secondary']});
                color: {colors['surface']};
            }}
            
            #modernResultsList::item:selected:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {colors['item_selected']}, stop:1 {colors['secondary']});
                color: {colors['surface']};
            }}
            
            #emptyStateLabel {{
                color: {colors['text_secondary']};
                font-size: 14px;
                line-height: 1.5;
            }}
            
            #bottomFrame {{
                background-color: {colors['dialog_bg']};
                border-top: 1px solid {colors['border']};
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
            
            #statusLabel {{
                color: {colors['text_secondary']};
                font-size: 11px;
            }}
            
            #primaryButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {colors['primary']}, stop:1 {colors['secondary']});
                color: {colors['surface']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }}
            
            #primaryButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {colors['gradient_start']}, stop:1 {colors['gradient_end']});
            }}
            
            #primaryButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {colors['secondary']}, stop:1 {colors['primary']});
            }}
        """
        
        self.setStyleSheet(style)
        
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
    
    def _on_search_text_changed_simple(self, text):
        """搜索文本改变时的简单处理（仅UI状态更新，不自动搜索）"""
        print(f"🔤 搜索文本变化：'{text}' (长度: {len(text)})")
        
        # 确保搜索框始终可编辑
        if not self.search_line_edit.isEnabled():
            print("🔧 重新启用搜索框")
            self.search_line_edit.setEnabled(True)
        
        # 显示/隐藏清空按钮
        self.clear_button.setVisible(bool(text))
        
        # 启用/禁用主窗口搜索按钮
        if hasattr(self, 'main_window_button'):
            self.main_window_button.setEnabled(bool(text.strip()))
        
        if not text.strip():
            # 文本为空时，立即清空结果并恢复待搜索状态
            self._clear_results()
            self._hide_search_progress()  # 立即隐藏进度条
            self._show_empty_state()      # 恢复待搜索状态
            
            # 更新状态标签
            if hasattr(self, 'status_label'):
                self.status_label.setText("准备就绪")
        else:
            # 有文本时，更新提示信息
            if hasattr(self, 'status_label'):
                self.status_label.setText("按回车键搜索")
    
    def _on_search_text_changed(self, text):
        """搜索文本改变时的处理（保留原方法名以兼容）"""
        self._on_search_text_changed_simple(text)
    
    def _clear_results(self):
        """清空搜索结果"""
        print("🧹 快速搜索对话框：清空结果")
        self.results_list.clear()
        self.empty_state_label.setVisible(True)
        self.results_list.setVisible(False)
        if hasattr(self, 'search_stats'):
            self.search_stats.setVisible(False)
        if hasattr(self, 'results_header'):
            self.results_header.setText("搜索结果")
        if hasattr(self, 'status_label'):
            self.status_label.setText("准备就绪")
    
    def _on_search_enter(self):
        """处理回车键搜索"""
        self._perform_search()
    
    def _perform_search(self):
        """执行搜索（优化版本）"""
        query = self.search_line_edit.text().strip()
        if not query:
            self._clear_results()
            return
        
        # 显示搜索进度
        self._show_search_progress()
        
        # 更新状态
        if hasattr(self, 'status_label'):
            self.status_label.setText("搜索中...")
        
        # 记录搜索开始时间
        import time
        start_time = time.time()
        
        try:
            # 发出搜索信号
            self.search_executed.emit(query)
            
            # 模拟搜索延迟（实际搜索在控制器中进行）
            QTimer.singleShot(100, lambda: self._hide_search_progress())
            
        except Exception as e:
            print(f"搜索执行失败: {str(e)}")
            self._hide_search_progress()
            if hasattr(self, 'status_label'):
                self.status_label.setText("搜索失败")
    
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
        if hasattr(self, 'search_hint_label'):
            self.search_hint_label.setText("输入关键词后按回车键搜索")
        if hasattr(self, 'status_label'):
            self.status_label.setText("准备就绪")
        if hasattr(self, 'results_header'):
            self.results_header.setText("搜索结果")
    
    def _clear_search(self):
        """清空搜索"""
        print("🧹 清空搜索框")
        
        # 确保搜索框可编辑
        if not self.search_line_edit.isEnabled():
            print("🔧 启用搜索框以便清空")
            self.search_line_edit.setEnabled(True)
        
        self.search_line_edit.clear()
        self.search_line_edit.setFocus()
        self._show_empty_state()
        
        # 确保清空按钮隐藏
        self.clear_button.setVisible(False)
    
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
        """键盘事件处理（增强版本）"""
        if event.key() == Qt.Key_Escape:
            print("🔑 快速搜索对话框：按下ESC键，关闭窗口")
            event.accept()  # 确保事件被处理
            self.close()
            return
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() == Qt.ControlModifier:
                # Ctrl+Enter: 在主窗口中搜索
                self._on_main_window_button()
            else:
                # Enter: 如果焦点在搜索框，执行搜索；如果在结果列表且有选中项，打开文件
                if self.search_line_edit.hasFocus():
                    # 搜索框有焦点：执行搜索
                    self._on_search_enter()
                else:
                    # 结果列表有焦点：打开选中的文件
                    current_item = self.results_list.currentItem()
                    if current_item and hasattr(current_item, 'data') and current_item.data(Qt.UserRole):
                        self._on_item_activated(current_item)
        elif event.key() == Qt.Key_Down:
            # 下箭头：移动到结果列表
            if self.results_list.count() > 0:
                self.results_list.setFocus()
                if self.results_list.currentRow() < 0:
                    self.results_list.setCurrentRow(0)
        elif event.key() == Qt.Key_Up:
            # 上箭头：如果在列表第一项，回到搜索框
            if self.sender() == self.results_list and self.results_list.currentRow() <= 0:
                self.search_line_edit.setFocus()
        elif event.key() == Qt.Key_F5:
            # F5: 刷新搜索
            self._perform_search()
        elif event.key() == Qt.Key_Delete:
            # Delete: 清空搜索框
            if self.search_line_edit.hasFocus():
                self.search_line_edit.clear()
        elif event.key() == Qt.Key_F1:
            # F1: 显示帮助
            self._show_help_dialog()
        elif event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_C:
                # Ctrl+C: 复制选中项的路径
                current_item = self.results_list.currentItem()
                if current_item and hasattr(current_item, 'data'):
                    file_path = current_item.data(Qt.UserRole)
                    if file_path:
                        self._copy_to_clipboard(file_path)
            elif event.key() == Qt.Key_O:
                # Ctrl+O: 打开选中的文件
                current_item = self.results_list.currentItem()
                if current_item:
                    self._on_item_activated(current_item)
            elif event.key() == Qt.Key_L:
                # Ctrl+L: 定位到搜索框
                self.search_line_edit.setFocus()
                self.search_line_edit.selectAll()
        else:
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
        """显示简化的右键菜单 - 突出最常用功能"""
        print(f"🖱️ 右键菜单被触发，位置: {position}")
        
        item = self.results_list.itemAt(position)
        if not item:
            print("⚠️ 右键点击位置没有项目")
            return
        
        print(f"✅ 找到项目: {type(item)}")
        
        # 从SearchResultItem获取文件路径
        file_path = None
        
        # 优先从SearchResultItem的属性获取
        if isinstance(item, SearchResultItem):
            file_path = item.path
            print(f"📄 从SearchResultItem获取路径: {file_path}")
        
        # 如果没有，从Qt.UserRole获取
        if not file_path:
            file_path = item.data(Qt.UserRole)
            print(f"📄 从UserRole获取路径: {file_path}")
        
        if not file_path:
            print("⚠️ 无法获取文件路径，跳过右键菜单")
            return
        
        print(f"✅ 显示简化右键菜单，文件路径: {file_path}")
        
        context_menu = QMenu(self)
        
        # 获取当前主题颜色
        colors = self._get_theme_colors()
        
        context_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {colors['surface']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
                min-width: 180px;
            }}
            QMenu::item {{
                padding: 10px 16px;
                border-radius: 4px;
                margin: 2px;
            }}
            QMenu::item:selected {{
                background-color: {colors['primary']};
                color: {colors['surface']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {colors['border']};
                margin: 6px 8px;
            }}
        """)
        
        # === 最常用的4个功能 ===
        
        # 1. 打开文件
        open_file_action = QAction("📄 打开文件", self)
        open_file_action.triggered.connect(lambda: self._open_file(file_path))
        context_menu.addAction(open_file_action)
        
        # 2. 打开目录
        open_folder_action = QAction("📁 打开目录", self)
        open_folder_action.triggered.connect(lambda: self._open_folder(file_path))
        context_menu.addAction(open_folder_action)
        
        context_menu.addSeparator()
        
        # 3. 复制文件路径
        copy_path_action = QAction("📋 复制文件路径", self)
        copy_path_action.triggered.connect(lambda: self._copy_to_clipboard(file_path))
        context_menu.addAction(copy_path_action)
        
        context_menu.addSeparator()
        
        # 4. 打开主窗口查看更多结果
        main_window_action = QAction("🖥️ 主窗口查看更多", self)
        main_window_action.triggered.connect(self._on_main_window_button)
        context_menu.addAction(main_window_action)
        
        context_menu.exec(self.results_list.mapToGlobal(position))
    
    def _copy_to_clipboard(self, text):
        """复制文本到剪贴板（简化版本）"""
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            
            # 简化提示信息
            self.status_label.setText("已复制文件路径")
            QTimer.singleShot(2000, lambda: self.status_label.setText("就绪 - 快速文件名搜索"))
    
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
    
    def _fulltext_search_in_main(self):
        """在主窗口中进行全文搜索（兼容原接口）"""
        self._on_main_window_button()
    
    def set_search_results(self, results):
        """设置搜索结果（修复版本）"""
        import time
        start_time = time.time()
        
        print(f"🔄 快速搜索对话框：开始更新结果，数量: {len(results) if results else 0}")
        
        # 性能优化：批量操作，减少UI更新
        self.results_list.setUpdatesEnabled(False)
        self.results_list.clear()
        
        # 隐藏搜索进度
        self._hide_search_progress()
        
        if not results:
            self.results_list.setUpdatesEnabled(True)
            self.empty_state_label.setVisible(True)
            self.results_list.setVisible(False)
            if hasattr(self, 'results_header'):
                self.results_header.setText("未找到结果")
            if hasattr(self, 'status_label'):
                self.status_label.setText("未找到匹配的文件")
            print("📭 快速搜索对话框：显示空结果状态")
            return
        
        # 显示结果列表，隐藏空状态提示
        self.empty_state_label.setVisible(False)
        self.results_list.setVisible(True)
        
        # 检查是否包含加载指示器
        has_loading_indicator = any(result.get('is_loading_indicator', False) for result in results)
        actual_results = [r for r in results if not r.get('is_loading_indicator', False)]
        
        # 快捷搜索显示限制
        display_limit = 50
        total_count = len(actual_results)
        
        print(f"📊 快速搜索对话框：处理结果 - 总数: {total_count}, 显示限制: {display_limit}, 加载指示器: {has_loading_indicator}")
        
        # 更新结果标题
        if hasattr(self, 'results_header'):
            if has_loading_indicator:
                self.results_header.setText(f"📁 搜索结果 (正在加载更多...)")
            elif total_count > display_limit:
                self.results_header.setText(f"📁 文件搜索结果 (显示前{display_limit}个，共找到{total_count}个)")
            else:
                self.results_header.setText(f"📁 文件搜索结果 (共{total_count}个)")
        
        try:
            # 性能优化：预分配列表，批量创建项目
            items_to_add = []
            
            # 添加实际搜索结果
            for result in actual_results[:display_limit]:
                file_path = result.get('file_path', '')
                content_preview = result.get('content_preview', '')
                
                # 创建结果项（现在更快，因为避免了文件I/O）
                item = SearchResultItem(
                    title=self._get_file_display_name(file_path),
                    path=file_path,
                    content_preview=content_preview,
                    file_type=self._get_file_type(file_path)
                )
                
                # 确保文件路径正确存储在UserRole中
                item.setData(Qt.UserRole, file_path)
                items_to_add.append(item)
            
            # 如果有加载指示器，添加加载提示项
            if has_loading_indicator:
                loading_item = QListWidgetItem()
                loading_item.setText("⏳ 正在搜索更多结果...\n  🔍 后台正在进行完整搜索，即将显示全部结果")
                loading_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # 不可选择
                loading_item.setBackground(QColor("#e3f2fd"))  # 浅蓝色背景
                loading_item.setForeground(QColor("#1976d2"))  # 蓝色文字
                loading_item.setSizeHint(QSize(0, 60))
                items_to_add.append(loading_item)
            
            # 如果有更多结果（且不是加载状态），添加提示项
            elif total_count > display_limit:
                more_item = QListWidgetItem()
                remaining = total_count - display_limit
                more_text = f"⚡ 还有 {remaining} 个文件\n\n🖥️ 右键「主窗口查看更多」获取全部结果"
                more_item.setText(more_text)
                more_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # 不可选择
                more_item.setBackground(QColor("#f8f9fa"))
                more_item.setForeground(QColor("#495057"))
                more_item.setSizeHint(QSize(0, 60))
                items_to_add.append(more_item)
            
            # 批量添加到列表（减少UI更新次数）
            for item in items_to_add:
                self.results_list.addItem(item)
        
        finally:
            # 重新启用UI更新
            self.results_list.setUpdatesEnabled(True)
        
        # 选中第一个结果（如果不是加载指示器）
        if self.results_list.count() > 0 and not has_loading_indicator:
            self.results_list.setCurrentRow(0)
        
        # 显示搜索统计
        elapsed_ms = int((time.time() - start_time) * 1000)
        self._show_search_stats(total_count, elapsed_ms, has_loading_indicator)
        
        # 更新状态
        if hasattr(self, 'status_label'):
            if has_loading_indicator:
                self.status_label.setText(f"找到 {total_count} 个文件，正在搜索更多...")
            elif total_count > display_limit:
                self.status_label.setText(f"显示前{display_limit}个文件，共{total_count}个 - 快速搜索")
            else:
                self.status_label.setText(f"找到 {total_count} 个文件 - 快速搜索")
        
        print(f"✅ 快速搜索对话框：结果更新完成，显示 {self.results_list.count()} 个项目")
    
    def _show_search_stats(self, count, time_ms, is_loading=False):
        """显示搜索统计信息（支持加载状态）"""
        if hasattr(self, 'search_stats'):
            if is_loading:
                self.search_stats.setText(f"找到 {count} 个结果，正在搜索更多... ({time_ms}ms)")
            elif count > 0:
                self.search_stats.setText(f"找到 {count} 个结果 ({time_ms}ms)")
            else:
                self.search_stats.setText("未找到匹配结果")
            self.search_stats.setVisible(True)
    
    def _get_file_display_name(self, file_path):
        """获取文件显示名称"""
        import os
        return os.path.basename(file_path) if file_path else "未知文件"
    
    def _get_file_type(self, file_path):
        """获取文件类型"""
        import os
        if not file_path:
            return "unknown"
        
        ext = os.path.splitext(file_path)[1].lower()
        type_map = {
            '.txt': 'text', '.md': 'text', '.py': 'code',
            '.doc': 'word', '.docx': 'word',
            '.xls': 'excel', '.xlsx': 'excel',
            '.ppt': 'powerpoint', '.pptx': 'powerpoint',
            '.pdf': 'pdf',
            '.jpg': 'image', '.png': 'image', '.gif': 'image',
            '.mp4': 'video', '.avi': 'video',
            '.mp3': 'audio', '.wav': 'audio'
        }
        return type_map.get(ext, 'file')
    
    def _get_theme_colors(self):
        """获取当前主题的颜色配置"""
        if self.current_theme == "现代蓝":
            return {
                "primary": "#007ACC",
                "secondary": "#005A9E",
                "background": "#F8FAFE",
                "surface": "#FFFFFF",
                "text_primary": "#1E1E1E",
                "text_secondary": "#6B7280",
                "border": "#E1E5E9",
                "hover": "#E3F2FD",
                "accent": "#FF6B35",
                "success": "#10B981",
                "warning": "#F59E0B",
                "error": "#EF4444",
                "info": "#3B82F6",
                "gradient_start": "#007ACC",
                "gradient_end": "#00A8E8",
                "dialog_bg": "#F8FAFE",
                "title_bg_start": "#007ACC",
                "title_bg_end": "#005A9E",
                "search_bg": "#FFFFFF",
                "search_border": "#E1E5E9",
                "search_focus": "#007ACC",
                "results_bg": "#FFFFFF",
                "item_hover": "#E3F2FD",
                "item_selected": "#007ACC"
            }
        elif self.current_theme == "现代紫":
            return {
                "primary": "#8B5CF6",
                "secondary": "#7C3AED",
                "background": "#FDFBFF",
                "surface": "#FFFFFF",
                "text_primary": "#1E1E1E",
                "text_secondary": "#6B7280",
                "border": "#E9E3FF",
                "hover": "#F3F0FF",
                "accent": "#06B6D4",
                "success": "#10B981",
                "warning": "#F59E0B",
                "error": "#EF4444",
                "info": "#8B5CF6",
                "gradient_start": "#8B5CF6",
                "gradient_end": "#A855F7",
                "dialog_bg": "#FDFBFF",
                "title_bg_start": "#8B5CF6",
                "title_bg_end": "#7C3AED",
                "search_bg": "#FFFFFF",
                "search_border": "#E9E3FF",
                "search_focus": "#8B5CF6",
                "results_bg": "#FFFFFF",
                "item_hover": "#F3F0FF",
                "item_selected": "#8B5CF6"
            }
        elif self.current_theme == "现代红":
            return {
                "primary": "#DC2626",
                "secondary": "#B91C1C",
                "background": "#FFFBFA",
                "surface": "#FFFFFF",
                "text_primary": "#1E1E1E",
                "text_secondary": "#6B7280",
                "border": "#FEE2E2",
                "hover": "#FEF2F2",
                "accent": "#059669",
                "success": "#10B981",
                "warning": "#F59E0B",
                "error": "#DC2626",
                "info": "#3B82F6",
                "gradient_start": "#DC2626",
                "gradient_end": "#F87171",
                "dialog_bg": "#FFFBFA",
                "title_bg_start": "#DC2626",
                "title_bg_end": "#B91C1C",
                "search_bg": "#FFFFFF",
                "search_border": "#FEE2E2",
                "search_focus": "#DC2626",
                "results_bg": "#FFFFFF",
                "item_hover": "#FEF2F2",
                "item_selected": "#DC2626"
            }
        elif self.current_theme == "现代橙":
            return {
                "primary": "#EA580C",
                "secondary": "#C2410C",
                "background": "#FFFBF5",
                "surface": "#FFFFFF",
                "text_primary": "#1E1E1E",
                "text_secondary": "#6B7280",
                "border": "#FED7AA",
                "hover": "#FFF7ED",
                "accent": "#0D9488",
                "success": "#10B981",
                "warning": "#EA580C",
                "error": "#EF4444",
                "info": "#3B82F6",
                "gradient_start": "#EA580C",
                "gradient_end": "#FB923C",
                "dialog_bg": "#FFFBF5",
                "title_bg_start": "#EA580C",
                "title_bg_end": "#C2410C",
                "search_bg": "#FFFFFF",
                "search_border": "#FED7AA",
                "search_focus": "#EA580C",
                "results_bg": "#FFFFFF",
                "item_hover": "#FFF7ED",
                "item_selected": "#EA580C"
            }

        else:
            # 默认现代蓝主题
            return self._get_theme_colors_for_theme("现代蓝")
    
    def _get_theme_colors_for_theme(self, theme_name):
        """获取指定主题的颜色配置（辅助方法）"""
        original_theme = self.current_theme
        self.current_theme = theme_name
        colors = self._get_theme_colors()
        self.current_theme = original_theme
        return colors
    
    def update_theme(self, theme_name):
        """更新主题（供外部调用）"""
        if theme_name != self.current_theme:
            self.current_theme = theme_name
            self._apply_theme_styles()
            
            # 更新搜索图标
            self._update_search_icon()
            
            # 刷新结果显示
            if hasattr(self, 'results_list') and self.results_list.count() > 0:
                self._refresh_results_display()
    
    def _update_search_icon(self):
        """更新搜索图标颜色"""
        colors = self._get_theme_colors()
        if hasattr(self, 'search_icon_label'):
            # 根据主题调整图标
            # 所有主题都使用相同的搜索图标
            self.search_icon_label.setText("🔍")
    
    def _refresh_results_display(self):
        """刷新结果显示以应用新主题"""
        # 触发重新渲染
        current_row = self.results_list.currentRow()
        self.results_list.update()
        if current_row >= 0:
            self.results_list.setCurrentRow(current_row)
    
    def _create_enhanced_search_area(self, layout):
        """创建增强的搜索区域"""
        search_frame = QFrame()
        search_frame.setObjectName("searchFrame")
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(20, 15, 20, 15)
        
        # 搜索提示
        self.search_hint = QLabel("输入关键词开始搜索...")
        self.search_hint.setObjectName("searchHint")
        search_layout.addWidget(self.search_hint)
        
        # 搜索输入框容器
        search_container = QHBoxLayout()
        
        # 搜索输入框
        self.search_line_edit = QLineEdit()
        self.search_line_edit.setObjectName("modernSearchLineEdit")
        self.search_line_edit.setPlaceholderText("搜索文档...")
        search_container.addWidget(self.search_line_edit)
        
        # 清空按钮
        self.clear_button = QPushButton("✖")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.setFixedSize(34, 34)
        self.clear_button.setVisible(False)
        search_container.addWidget(self.clear_button)
        
        search_layout.addLayout(search_container)
        
        # 搜索进度条
        self.search_progress = QProgressBar()
        self.search_progress.setObjectName("searchProgress")
        self.search_progress.setFixedHeight(3)
        self.search_progress.setVisible(False)
        search_layout.addWidget(self.search_progress)
        
        # 搜索统计信息
        self.search_stats = QLabel("")
        self.search_stats.setObjectName("searchStats")
        self.search_stats.setVisible(False)
        search_layout.addWidget(self.search_stats)
        
        layout.addWidget(search_frame)
    
    def _create_enhanced_results_area(self, layout):
        """创建增强的结果区域"""
        results_frame = QFrame()
        results_frame.setObjectName("resultsFrame")
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(20, 10, 20, 10)
        
        # 结果标题
        self.results_header = QLabel("搜索结果")
        self.results_header.setObjectName("resultsHeader")
        results_layout.addWidget(self.results_header)
        
        # 结果列表
        self.results_list = QListWidget()
        self.results_list.setObjectName("modernResultsList")
        self.results_list.setAlternatingRowColors(True)
        self.results_list.setContextMenuPolicy(Qt.CustomContextMenu)
        # 确保右键菜单信号连接
        self.results_list.customContextMenuRequested.connect(self._show_context_menu)
        results_layout.addWidget(self.results_list)
        
        # 空状态提示
        self.empty_state_label = QLabel(
            "🔍 输入关键词后按回车键搜索\n\n"
            "💡 操作提示：\n"
            "• Enter: 执行搜索\n"
            "• 双击结果: 打开文件\n"
            "• 右键结果: 更多选项\n"
            "• Ctrl+Enter: 主窗口搜索\n"
            "• F1: 查看完整帮助"
        )
        self.empty_state_label.setObjectName("emptyStateLabel")
        self.empty_state_label.setAlignment(Qt.AlignCenter)
        self.empty_state_label.setVisible(True)
        results_layout.addWidget(self.empty_state_label)
        
        layout.addWidget(results_frame)
    
    def _create_enhanced_bottom_bar(self, layout):
        """创建增强的底部操作栏"""
        bottom_frame = QFrame()
        bottom_frame.setObjectName("bottomFrame")
        bottom_frame.setFixedHeight(50)
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(20, 10, 20, 10)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("statusLabel")
        bottom_layout.addWidget(self.status_label)
        
        bottom_layout.addStretch()
        
        # 快捷键提示
        shortcut_label = QLabel("Enter: 搜索 | Ctrl+Enter: 主窗口 | F1: 帮助 | Esc: 关闭")
        shortcut_label.setObjectName("statusLabel")
        bottom_layout.addWidget(shortcut_label)
        
        # 在主窗口中搜索按钮
        self.main_window_button = QPushButton("在主窗口中搜索")
        self.main_window_button.setObjectName("primaryButton")
        self.main_window_button.setEnabled(False)
        bottom_layout.addWidget(self.main_window_button)
        
        layout.addWidget(bottom_frame)

    def _show_help_dialog(self):
        """显示帮助对话框"""
        help_text = """
🔍 快速搜索帮助

📝 基本操作：
• 输入关键词后按 Enter 键搜索
• 双击结果项打开文件
• 右键点击查看更多选项

⌨️ 快捷键：
• Enter: 执行搜索（搜索框有焦点时）
• Enter: 打开文件（结果列表有焦点时）
• Ctrl+Enter: 在主窗口中搜索
• ↓: 移动到结果列表
• ↑: 回到搜索框
• F5: 刷新搜索
• Delete: 清空搜索框
• Ctrl+C: 复制文件路径
• Ctrl+O: 打开选中文件
• Ctrl+L: 定位到搜索框
• Esc: 关闭窗口

🖱️ 鼠标操作：
• 双击结果: 打开文件
• 右键结果: 显示操作菜单
• 拖动标题栏: 移动窗口

💡 搜索提示：
• 支持中英文文件名搜索
• 搜索结果按相关性排序
• 只搜索文件名，不搜索文件内容
• 按回车键手动搜索，避免误搜索
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("快速搜索帮助")
        msg_box.setText(help_text)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        # 设置对话框样式
        colors = self._get_theme_colors()
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {colors['dialog_bg']};
                color: {colors['text_primary']};
            }}
            QMessageBox QPushButton {{
                background-color: {colors['primary']};
                color: {colors['surface']};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {colors['secondary']};
            }}
        """)
        
        msg_box.exec()


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