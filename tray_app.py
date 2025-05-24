"""
文智搜托盘应用程序模块

本模块提供系统托盘功能，包括托盘图标、托盘菜单和命令行参数解析。
"""

import os
import sys
import argparse
from pathlib import Path

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Signal, QObject, QSettings

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，适用于开发环境和打包后的环境"""
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # 如果不是通过PyInstaller打包，则使用当前文件夹
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class TrayIcon(QSystemTrayIcon):
    """系统托盘图标类"""
    
    # 定义信号
    show_main_window_signal = Signal()    # 显示主窗口信号
    hide_main_window_signal = Signal()    # 隐藏主窗口信号
    quit_app_signal = Signal()            # 退出应用信号
    quick_search_signal = Signal(str)     # 快速搜索信号，参数为搜索文本
    light_search_signal = Signal(str)     # 轻量级搜索信号，参数为初始搜索文本（可选）
    
    def __init__(self, parent=None):
        """初始化托盘图标"""
        # 加载图标
        icon_path = get_resource_path("app_icon.ico")
        if not os.path.exists(icon_path):
            # 尝试使用PNG作为备选
            icon_path = get_resource_path("app_icon.png")
            if not os.path.exists(icon_path):
                # 如果都找不到，使用系统默认图标
                super().__init__(parent)
                return
        
        icon = QIcon(icon_path)
        super().__init__(icon, parent)
        
        # 设置工具提示
        self.setToolTip("文智搜")
        
        # 热键管理器引用（将由外部设置）
        self.hotkey_manager = None
        
        # 创建托盘菜单
        self.setup_menu()
        
        # 连接信号
        self.activated.connect(self._on_activated)
        
        # 加载设置
        self.settings = QSettings("WenZhiSou", "DocumentSearch")
        
        # 最近搜索列表
        self.recent_searches = []
        self._load_recent_searches()
    
    def set_hotkey_manager(self, hotkey_manager):
        """设置热键管理器引用，用于动态更新热键显示
        
        Args:
            hotkey_manager: 热键管理器实例
        """
        self.hotkey_manager = hotkey_manager
        # 更新菜单显示
        self.update_hotkey_display()
    
    def update_hotkey_display(self):
        """更新托盘菜单中的热键显示"""
        if self.hotkey_manager and hasattr(self, 'light_search_action'):
            # 获取当前轻量级搜索热键设置
            hotkey_info = self.hotkey_manager.get_hotkey_info()
            quick_search_config = hotkey_info.get('quick_search', {})
            
            if quick_search_config.get('enabled', False):
                # 格式化热键显示
                hotkey_text = quick_search_config.get('key', 'alt+space')
                # 转换为更友好的显示格式
                display_hotkey = self._format_hotkey_display(hotkey_text)
                self.light_search_action.setText(f"快速搜索 ({display_hotkey})")
            else:
                self.light_search_action.setText("快速搜索 (未启用)")
    
    def _format_hotkey_display(self, hotkey_text):
        """格式化热键显示文本
        
        Args:
            hotkey_text: 热键文本，如 "alt+space"
            
        Returns:
            str: 格式化后的显示文本，如 "Alt+Space"
        """
        if not hotkey_text:
            return "未设置"
        
        # 分割热键组合
        parts = hotkey_text.lower().split('+')
        formatted_parts = []
        
        for part in parts:
            if part == 'ctrl':
                formatted_parts.append('Ctrl')
            elif part == 'alt':
                formatted_parts.append('Alt')
            elif part == 'shift':
                formatted_parts.append('Shift')
            elif part == 'space':
                formatted_parts.append('Space')
            elif part == 'tab':
                formatted_parts.append('Tab')
            elif part == 'enter':
                formatted_parts.append('Enter')
            else:
                # 其他键直接首字母大写
                formatted_parts.append(part.capitalize())
        
        return '+'.join(formatted_parts)
    
    def _load_recent_searches(self):
        """从设置加载最近搜索列表"""
        # 首先尝试从主要键名加载历史
        primary_key = "history/searchQueries"
        recent_searches = self.settings.value(primary_key, [])
        
        # 如果历史记录不为空，则使用它
        if recent_searches:
            if isinstance(recent_searches, str):
                self.recent_searches = [recent_searches]
            elif isinstance(recent_searches, list):
                self.recent_searches = recent_searches[:5]  # 最多显示5个
            else:
                self.recent_searches = []
        else:
            # 如果主键名没有数据，尝试备用键名（向后兼容）
            backup_keys = ["unified_search/history", "search/history", "search_history", "recent_searches"]
            for key in backup_keys:
                value = self.settings.value(key, [])
                if value:
                    if isinstance(value, str):
                        self.recent_searches = [value]
                    elif isinstance(value, list):
                        self.recent_searches = value[:5]  # 最多显示5个
                    break
            else:
                # 如果所有键都没有找到数据
                self.recent_searches = []
    
    def setup_menu(self):
        """设置托盘菜单"""
        menu = QMenu()
        
        # 添加显示/隐藏窗口菜单项
        self.show_action = menu.addAction("显示主窗口")
        self.show_action.setObjectName("show_main_window_action")  # 设置objectName用于动态更新
        self.show_action.triggered.connect(self.show_main_window_signal.emit)
        
        self.hide_action = menu.addAction("隐藏主窗口")
        self.hide_action.triggered.connect(self.hide_main_window_signal.emit)
        
        # 动态获取快速搜索热键显示文本
        from dynamic_tray_menu import get_hotkey_display_text
        quick_search_hotkey = get_hotkey_display_text("show_quick_search")
        self.light_search_action = menu.addAction(f"快速搜索 ({quick_search_hotkey})")
        self.light_search_action.setObjectName("quick_search_action")  # 设置objectName用于动态更新
        self.light_search_action.triggered.connect(lambda: self.light_search_signal.emit(""))
        
        # 添加分隔线
        menu.addSeparator()
        
        # 添加最近搜索子菜单（将在显示菜单前动态更新）
        self.recent_searches_menu = menu.addMenu("最近搜索")
        # 使用菜单本身的aboutToShow信号
        self.recent_searches_menu.aboutToShow.connect(self._update_recent_searches_menu)
        
        # 添加分隔线
        menu.addSeparator()
        
        # 添加退出菜单项
        exit_action = menu.addAction("退出")
        exit_action.triggered.connect(self.quit_app_signal.emit)
        
        # 设置菜单
        self.setContextMenu(menu)
        
        # 初始化热键显示
        self.update_hotkey_display_from_settings()
    
    def _update_recent_searches_menu(self):
        """更新最近搜索子菜单"""
        # 重新加载最近搜索
        self._load_recent_searches()
        
        # 清空现有菜单项
        self.recent_searches_menu.clear()
        
        # 添加新的菜单项
        if self.recent_searches and len(self.recent_searches) > 0:
            # 添加主窗口搜索选项
            for search in self.recent_searches:
                # 截断过长的搜索文本
                display_text = search
                if len(display_text) > 30:
                    display_text = display_text[:27] + "..."
                    
                action = self.recent_searches_menu.addAction(display_text)
                # 使用lambda的默认参数来捕获当前值
                action.triggered.connect(lambda checked=False, text=search: self.quick_search_signal.emit(text))
            
            # 添加分隔线和轻量级搜索选项
            self.recent_searches_menu.addSeparator()
            
            # 为每个最近搜索添加轻量级搜索选项
            light_search_submenu = self.recent_searches_menu.addMenu("使用轻量级搜索")
            for search in self.recent_searches:
                # 截断过长的搜索文本
                display_text = search
                if len(display_text) > 30:
                    display_text = display_text[:27] + "..."
                    
                action = light_search_submenu.addAction(display_text)
                # 使用lambda的默认参数来捕获当前值
                action.triggered.connect(lambda checked=False, text=search: self.light_search_signal.emit(text))
        else:
            # 如果没有最近搜索，添加禁用的菜单项
            action = self.recent_searches_menu.addAction("无最近搜索")
            action.setEnabled(False)
    
    def _on_activated(self, reason):
        """处理托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # 单击托盘图标，显示主窗口
            self.show_main_window_signal.emit()
    
    def update_hotkey_display_from_settings(self):
        """从设置更新热键显示"""
        try:
            from dynamic_tray_menu import get_quick_search_hotkey_text, get_main_window_hotkey_text
            
            # 更新快速搜索热键显示
            if hasattr(self, 'light_search_action'):
                quick_search_text = get_quick_search_hotkey_text()
                self.light_search_action.setText(quick_search_text)
                
            # 更新显示主窗口热键显示
            if hasattr(self, 'show_action'):
                main_window_text = get_main_window_hotkey_text()
                self.show_action.setText(main_window_text)
                
        except ImportError:
            print("无法导入dynamic_tray_menu模块，使用默认热键显示")
        except Exception as e:
            print(f"更新热键显示时出错: {e}")
            
    def refresh_hotkey_display(self):
        """刷新热键显示（供外部调用）"""
        self.update_hotkey_display_from_settings()

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="文智搜 - 文档搜索工具")
    parser.add_argument("--minimized", action="store_true", 
                        help="以最小化模式启动，仅显示托盘图标")
    parser.add_argument("--search", type=str, 
                        help="启动时立即执行搜索查询")
    parser.add_argument("--quick-search", action="store_true", 
                        help="启动时显示轻量级搜索窗口")
    return parser.parse_args() 