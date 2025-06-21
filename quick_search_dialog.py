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
        self.parent_dialog = parent
        
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
        
        # 获取主题颜色
        colors = self._get_theme_colors()
        
        # 绘制背景
        if option.state & QStyle.State_Selected:
            # 使用主题的选中颜色
            painter.fillRect(rect, QColor(colors['item_selected']))
        elif option.state & QStyle.State_MouseOver:
            # 使用主题的悬停颜色
            painter.fillRect(rect, QColor(colors['item_hover']))
        else:
            # 使用主题的背景颜色
            painter.fillRect(rect, QColor(colors['results_bg']))
        
        # 设置文本颜色
        if option.state & QStyle.State_Selected:
            painter.setPen(QColor(colors['surface']))  # 选中时使用白色文字
        else:
            painter.setPen(QColor(colors['text_primary']))  # 正常时使用主题文字颜色
        
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
    
    def _get_theme_colors(self):
        """获取主题颜色"""
        if self.parent_dialog and hasattr(self.parent_dialog, '_get_theme_colors'):
            return self.parent_dialog._get_theme_colors()
        else:
            # 默认蓝色主题
            return {
                "primary": "#007ACC",
                "secondary": "#005A9E",
                "surface": "#FFFFFF",
                "text_primary": "#1E1E1E",
                "results_bg": "#FFFFFF",
                "item_hover": "#E3F2FD",
                "item_selected": "#007ACC"
            }
    
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
        # 移除最大尺寸限制，允许用户自由调整窗口大小
        # self.setMaximumSize(800, 700)  # 注释掉最大尺寸限制
        self.resize(650, 500)
        
        # 允许调整窗口大小
        self.setSizeGripEnabled(True)
        
        # 窗口拖动相关
        self._dragging = False
        self._drag_start_position = QPoint()
        
        # 窗口调整大小相关
        self._resizing = False
        self._resize_direction = None
        self._resize_margin = 8  # 边框调整区域宽度，稍微减小让操作更精确
        self._resize_start_pos = None
        self._resize_start_geometry = None
        
        # 启用鼠标跟踪以实时更新光标
        self.setMouseTracking(True)
        
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
        # 设置副标题颜色，在红色主题下更清晰可见
        self.subtitle_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
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
        
        # 操作提示标签 - 显示快捷键和操作方式
        self.shortcut_hint_label = QLabel("")
        self.shortcut_hint_label.setObjectName("shortcutHint")
        self.shortcut_hint_label.setStyleSheet("color: #ff6b35; font-weight: bold; font-size: 12px; margin: 5px 0; padding: 8px; background-color: #fff3cd; border-radius: 4px; border: 1px solid #ffeaa7;")
        self.shortcut_hint_label.setVisible(False)  # 初始隐藏
        search_layout.addWidget(self.shortcut_hint_label)
        
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
        self.results_delegate = SearchResultDelegate(self)  # 传递对话框本身作为父对象
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
        print("🔑 _on_search_enter 被调用")
        import traceback
        print("📍 调用堆栈:")
        for line in traceback.format_stack()[-3:-1]:  # 显示最近的2层调用
            print(f"   {line.strip()}")
        self._perform_search()
    
    def _perform_search(self):
        """执行搜索（优化版本）"""
        query = self.search_line_edit.text().strip()
        print(f"🔍 _perform_search 被调用: '{query}'")
        import traceback
        print("📍 调用堆栈:")
        for line in traceback.format_stack()[-3:-1]:  # 显示最近的2层调用
            print(f"   {line.strip()}")
            
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
            print(f"📡 发出搜索信号: '{query}'")
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
    
    def _get_resize_direction(self, pos):
        """获取鼠标位置对应的调整方向"""
        rect = self.rect()
        margin = self._resize_margin
        
        # 检查各个边缘和角落
        left = pos.x() <= margin
        right = pos.x() >= rect.width() - margin
        top = pos.y() <= margin
        bottom = pos.y() >= rect.height() - margin
        
        # 优先检查角落（角落区域优先级更高）
        if top and left:
            return 'top-left'
        elif top and right:
            return 'top-right'
        elif bottom and left:
            return 'bottom-left'
        elif bottom and right:
            return 'bottom-right'
        # 然后检查边缘
        elif top:
            return 'top'
        elif bottom:
            return 'bottom'
        elif left:
            return 'left'
        elif right:
            return 'right'
        
        return None
    
    def _get_resize_cursor(self, direction):
        """根据调整方向获取相应的鼠标光标"""
        cursors = {
            'top': Qt.SizeVerCursor,
            'bottom': Qt.SizeVerCursor,
            'left': Qt.SizeHorCursor,
            'right': Qt.SizeHorCursor,
            'top-left': Qt.SizeFDiagCursor,
            'bottom-right': Qt.SizeFDiagCursor,
            'top-right': Qt.SizeBDiagCursor,
            'bottom-left': Qt.SizeBDiagCursor,
        }
        return cursors.get(direction, Qt.ArrowCursor)
    
    def _is_in_resize_area(self, pos):
        """快速检查鼠标是否在调整大小区域"""
        rect = self.rect()
        margin = self._resize_margin
        
        # 快速检查是否在边缘区域
        return (pos.x() <= margin or pos.x() >= rect.width() - margin or
                pos.y() <= margin or pos.y() >= rect.height() - margin)
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件，用于拖动窗口和调整大小"""
        if event.button() == Qt.LeftButton:
            # 检查是否在调整大小区域
            resize_direction = self._get_resize_direction(event.position().toPoint())
            if resize_direction:
                self._resizing = True
                self._resize_direction = resize_direction
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geometry = self.geometry()
                self.setCursor(self._get_resize_cursor(resize_direction))
                event.accept()
                return
            
            # 检查是否点击在标题栏区域（拖动窗口）
            title_frame = self.findChild(QFrame, "titleFrame")
            if title_frame and title_frame.geometry().contains(event.position().toPoint()):
                self._dragging = True
                self._drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，用于窗口拖动和调整大小"""
        if self._resizing and self._resize_start_pos and self._resize_start_geometry:
            # 处理窗口大小调整
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self._resize_start_pos
            
            # 使用QRect进行更精确的几何计算
            original_rect = self._resize_start_geometry
            new_rect = QRect(original_rect)
            
            # 根据调整方向计算新的几何尺寸
            if 'left' in self._resize_direction:
                new_rect.setLeft(original_rect.left() + delta.x())
            if 'right' in self._resize_direction:
                new_rect.setRight(original_rect.right() + delta.x())
            if 'top' in self._resize_direction:
                new_rect.setTop(original_rect.top() + delta.y())
            if 'bottom' in self._resize_direction:
                new_rect.setBottom(original_rect.bottom() + delta.y())
            
            # 应用最小尺寸限制
            min_size = self.minimumSize()
            if new_rect.width() < min_size.width():
                if 'left' in self._resize_direction:
                    new_rect.setLeft(new_rect.right() - min_size.width())
                else:
                    new_rect.setRight(new_rect.left() + min_size.width())
            
            if new_rect.height() < min_size.height():
                if 'top' in self._resize_direction:
                    new_rect.setTop(new_rect.bottom() - min_size.height())
                else:
                    new_rect.setBottom(new_rect.top() + min_size.height())
            
            # 使用setGeometry而不是resize/move组合，减少重绘次数
            self.setGeometry(new_rect)
            event.accept()
            return
            
        elif self._dragging and self._drag_start_position:
            # 处理窗口拖动
            new_pos = event.globalPosition().toPoint() - self._drag_start_position
            self.move(new_pos)
            event.accept()
            return
        
        # 实时更新鼠标光标（只有在不进行拖拽操作时）
        if not self._resizing and not self._dragging:
            # 首先快速检查是否在调整区域
            if self._is_in_resize_area(event.position().toPoint()):
                resize_direction = self._get_resize_direction(event.position().toPoint())
                cursor = self._get_resize_cursor(resize_direction)
            else:
                cursor = Qt.ArrowCursor
            
            # 只有当光标需要改变时才设置
            if self.cursor().shape() != cursor:
                self.setCursor(cursor)
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件，用于窗口拖动和调整大小"""
        if event.button() == Qt.LeftButton:
            if self._resizing:
                self._resizing = False
                self._resize_direction = None
                self.setCursor(Qt.ArrowCursor)
            elif self._dragging:
                self._dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        """键盘事件处理（增强版本）"""
        if event.key() == Qt.Key_Escape:
            print("🔑 快速搜索对话框：按下ESC键，隐藏窗口")
            event.accept()  # 确保事件被处理
            self.hide()     # 隐藏而不是关闭
            return
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() == Qt.ControlModifier:
                # Ctrl+Enter: 在主窗口中搜索
                self._on_main_window_button()
            else:
                # Enter: 如果焦点在搜索框，不要重复处理（已由returnPressed信号处理）
                if self.search_line_edit.hasFocus():
                    # 搜索框有焦点：回车键已经被returnPressed信号处理，这里不重复处理
                    print("🔑 keyPressEvent: 搜索框回车键事件，已由returnPressed信号处理，跳过")
                    event.accept()  # 标记事件已处理，避免传播
                    return
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
            # F5: 刷新搜索（添加防重复检查）
            query = self.search_line_edit.text().strip()
            if query:
                # 检查是否刚刚执行过相同的搜索
                import time
                current_time = time.time()
                
                # 获取上次搜索的时间和查询（如果有的话）
                last_search_time = getattr(self, '_last_f5_search_time', 0)
                last_search_query = getattr(self, '_last_f5_search_query', '')
                
                # 如果3秒内执行过相同的搜索，跳过
                if (query == last_search_query and 
                    current_time - last_search_time < 3.0):
                    print(f"🚫 F5刷新：跳过重复搜索 '{query}' (间隔: {(current_time - last_search_time)*1000:.0f}ms)")
                    return
                
                # 记录本次F5搜索
                self._last_f5_search_time = current_time
                self._last_f5_search_query = query
                print(f"🔄 F5刷新：执行搜索 '{query}'")
                self._perform_search()
            else:
                print("🚫 F5刷新：搜索框为空，跳过刷新")
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
            self.hide()  # 打开文件后隐藏对话框
    
    def _on_item_activated(self, item):
        """处理激活事件（回车键）"""
        if not item:
            return
        
        file_path = item.data(Qt.UserRole)
        if file_path:
            print(f"优化版快速搜索: 激活打开文件 '{file_path}'")
            self.open_file_signal.emit(file_path)
            self.hide()  # 打开文件后隐藏对话框
    
    def _on_main_window_button(self):
        """处理在主窗口中打开按钮"""
        search_text = self.search_line_edit.text().strip()
        if search_text:
            print(f"优化版快速搜索: 在主窗口中打开搜索 '{search_text}'")
            self.open_main_window.emit(search_text)
            self.hide()
        else:
            # 即使没有搜索文本，也可以打开主窗口
            print("优化版快速搜索: 打开主窗口")
            self.open_main_window.emit("")
            self.hide()
    
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
            self.hide()
    
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
        
        # 检查是否包含加载指示器和元数据
        has_loading_indicator = any(result.get('is_loading_indicator', False) for result in results)
        
        # 检查是否有元数据（总数量信息）
        metadata = None
        if results and results[0].get('is_metadata', False):
            metadata = results[0]
            results = results[1:]  # 移除元数据项
        
        actual_results = [r for r in results if not r.get('is_loading_indicator', False)]
        
        # 快捷搜索显示限制
        display_limit = 50
        
        # 如果有元数据，使用元数据中的总数量，否则使用实际结果数量
        if metadata:
            total_count = metadata['total_found']
            print(f"📊 快捷搜索：从元数据获取总数量 {total_count}，显示 {len(actual_results)} 个")
        else:
            total_count = len(actual_results)
        
        # 对结果按时间降序排序
        actual_results = self._sort_results_by_time(actual_results)
        
        print(f"📊 快速搜索对话框：处理结果 - 总数: {total_count}, 显示限制: {display_limit}, 加载指示器: {has_loading_indicator}")
        
        # 更新结果标题和提示信息
        if hasattr(self, 'results_header'):
            if has_loading_indicator:
                self.results_header.setText(f"📁 搜索结果 (正在加载更多...)")
            elif total_count > display_limit:
                self.results_header.setText(f"📁 文件搜索结果 (显示前{display_limit}个，共找到{total_count}个)")
                # 在搜索框上方显示操作提示
                if hasattr(self, 'shortcut_hint_label'):
                    self.shortcut_hint_label.setText(f"⚠️ 快捷搜索找到{total_count}个文件，仅显示前{display_limit}个，如要查看更多文件，请使用主窗口搜索。")
                    self.shortcut_hint_label.setVisible(True)
                # 隐藏常规提示
                if hasattr(self, 'search_hint_label'):
                    self.search_hint_label.setVisible(False)
            else:
                self.results_header.setText(f"📁 文件搜索结果 (共{total_count}个)")
                # 隐藏操作提示
                if hasattr(self, 'shortcut_hint_label'):
                    self.shortcut_hint_label.setVisible(False)
                # 恢复正常提示
                if hasattr(self, 'search_hint_label'):
                    self.search_hint_label.setText("🗂️ 快速文件名搜索 - 输入关键词快速找到文件")
                    self.search_hint_label.setVisible(True)
        
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
                more_text = f"⚠️ 搜索结果超过{display_limit}条限制\n\n📊 已找到 {total_count} 个文件，快捷搜索仅显示前 {display_limit} 个\n🖥️ 点击「主窗口搜索」或按 Ctrl+Enter 查看全部 {total_count} 个结果"
                more_item.setText(more_text)
                more_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # 不可选择
                more_item.setBackground(QColor("#fff3cd"))  # 警告色背景
                more_item.setForeground(QColor("#856404"))  # 警告色文字
                more_item.setSizeHint(QSize(0, 80))  # 增加高度
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
                self.status_label.setText(f"显示前{display_limit}个，共{total_count}个 - 按时间降序排列")
                self.status_label.setStyleSheet("")  # 使用默认样式
            else:
                self.status_label.setText(f"找到 {total_count} 个文件 - 按时间降序排列")
                self.status_label.setStyleSheet("")  # 恢复默认样式
        
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
    
    def _sort_results_by_time(self, results):
        """按修改时间降序排序搜索结果"""
        import os
        import time
        
        # 过滤掉元数据项和加载指示器，只对实际文件结果排序
        actual_results = [r for r in results if not r.get('is_metadata', False) and not r.get('is_loading_indicator', False)]
        
        def get_sort_key(result):
            # 确保result是字典且包含file_path字段
            if not isinstance(result, dict) or 'file_path' not in result:
                print(f"⚠️ 排序：跳过无效结果项: {type(result)} - {result}")
                return 0
                
            file_path = result.get('file_path', '')
            
            # 首先尝试从结果中获取修改时间
            modified_time = result.get('modified_time', 0)
            if modified_time <= 0:
                modified_time = result.get('last_modified', 0)
            if modified_time <= 0:
                modified_time = result.get('mtime', 0)
            
            # 如果结果中没有时间信息，尝试从文件系统获取
            if modified_time <= 0 and file_path and os.path.exists(file_path):
                try:
                    modified_time = os.path.getmtime(file_path)
                except (OSError, FileNotFoundError):
                    modified_time = 0
            
            # 如果还是没有时间信息，使用当前时间作为默认值
            if modified_time <= 0:
                modified_time = time.time()
            
            return modified_time
        
        try:
            # 再次过滤，确保只有有效的字典结果
            valid_results = [r for r in actual_results if isinstance(r, dict) and 'file_path' in r]
            
            # 按修改时间降序排序（最新的在前）
            sorted_results = sorted(valid_results, key=get_sort_key, reverse=True)
            print(f"✅ 快捷搜索：已按时间降序排序 {len(sorted_results)} 个结果（从 {len(actual_results)} 个有效结果中）")
            return sorted_results
        except Exception as e:
            print(f"⚠️ 快捷搜索：排序失败，返回原始结果: {str(e)}")
            # 返回有效的字典结果
            return [r for r in actual_results if isinstance(r, dict) and 'file_path' in r]
    
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

    def closeEvent(self, event):
        """重写关闭事件，隐藏窗口而不是关闭"""
        print("🔒 快速搜索对话框：接收到关闭事件，隐藏窗口")
        event.ignore()  # 忽略关闭事件
        self.hide()     # 只是隐藏窗口


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