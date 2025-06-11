





# --- 导入统一路径处理工具 ---
from path_utils import normalize_path_for_display, normalize_path_for_index, PathStandardizer

# --- 导入统一主题管理工具 ---
from theme_manager import ThemeManager
# ------------------------

import sys
import io # 新增导入

# 确保 stdout 和 stderr 在非控制台模式下是可写的
# 这应该在几乎所有其他导入之前完成，特别是在 logging 和 jieba 导入之前
if sys.stdout is None:
    sys.stdout = io.StringIO()  # 重定向到一个内存字符串缓冲区
if sys.stderr is None:
    sys.stderr = io.StringIO()  # 同样重定向到内存缓冲区，避免与您后续的文件重定向冲突

# Import necessary classes from PySide6
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextBrowser, QProgressBar,
    QFileDialog, QMessageBox, QDateEdit, QCheckBox, QComboBox, QRadioButton, QDialog, QDialogButtonBox, QSpinBox,
    QButtonGroup, QListWidget, QListWidgetItem, QAbstractItemView, QGroupBox, QMenuBar, QToolBar, # ADDED QListWidget, QListWidgetItem, QAbstractItemView, QGroupBox, QMenuBar, QToolBar
    QStatusBar, # Ensure QProgressBar is imported if not already
    QTableWidget, QHeaderView, QTableWidgetItem,
    QTreeView, QSplitter, # 添加文件夹树视图所需的组件
    QSizePolicy, QFrame,
    QInputDialog,
    QTabWidget, QScrollArea, QTabBar, QTabWidget,
    QGridLayout, QMenu, # 添加QMenu用于右键菜单
    QListView, QStyledItemDelegate, QStackedWidget, QStyle, # 虚拟滚动所需组件
)
from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot, QUrl, QSettings, QDate, QTimer, QSize, QDir, QModelIndex, QRect, QAbstractListModel # Added QSize, QDir, QModelIndex, QRect, QAbstractListModel 
from PySide6.QtGui import QDesktopServices, QAction, QIntValidator, QShortcut, QKeySequence, QIcon, QColor, QStandardItemModel, QStandardItem, QTextDocument, QTextCursor, QPainter, QCursor # Added QStandardItemModel and QStandardItem, QTextDocument, QPainter, QCursor
import html  # Import html module for escaping

# --- ADDED: Network and Version Comparison Imports ---
import requests
from packaging import version
# -----------------------------------------------------

# Standard library imports
from pathlib import Path  # Added
import document_search  # Uncommented backend import
import traceback  # Keep for worker error reporting
import json  # Needed for structure map parsing
import functools # ADDED for LRU cache
import os  # Added for os.path.normpath
import time # Added for sleep
import datetime
import logging # Import logging module
import re
import subprocess
import shutil
import math
import codecs
import webbrowser
import requests.adapters  # 添加requests的适配器和重试策略导入
import urllib3.util  # 替换过时的requests.packages导入

# --- ADDED: 导入许可证管理器和对话框 ---
from license_manager import get_license_manager, Features, LicenseStatus
from license_dialog import LicenseDialog
# --------------------------------------

# --- ADDED: Try importing qdarkstyle --- 
_qdarkstyle_available = False
try:
    import qdarkstyle
    _qdarkstyle_available = True
except ImportError:
    pass # qdarkstyle not installed, will use basic dark theme
# -------------------------------------

# --- 添加资源文件路径解析器 ---
def get_resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和打包后的环境
    
    Args:
        relative_path (str): 相对于应用程序根目录的资源文件路径
        
    Returns:
        str: 资源文件的绝对路径
    """
    # 如果路径带有特殊前缀，则移除
    if relative_path.startswith('qss-resource:'):
        relative_path = relative_path[len('qss-resource:'):]
    
    # 如果路径被引号包围，则移除引号
    if (relative_path.startswith('"') and relative_path.endswith('"')) or \
       (relative_path.startswith("'") and relative_path.endswith("'")):
        relative_path = relative_path[1:-1]
    
    # 判断是否在PyInstaller环境中运行
    if getattr(sys, 'frozen', False):
        # 在PyInstaller环境中
        base_path = sys._MEIPASS
    else:
        # 在开发环境中
        base_path = os.path.dirname(__file__)
    
    # 组合路径并返回
    resource_path = os.path.join(base_path, relative_path)
    print(f"资源路径解析: {relative_path} -> {resource_path}")
    return resource_path
# ------------------------------

# ====================
# UI设计常量体系
# ====================

# 字体大小常量
UI_FONT_SIZES = {
    'normal': '12px',        # 标准文本
    'small': '11px',         # 小号文本
    'large': '14px',         # 大号文本
    'icon': '14px',          # 图标
    'extra_small': '10px',   # 额外小号文本
    'file_header': '16px',   # 文件标题
    'section_header': '13px', # 章节标题
    'table_cell': '11px',    # 表格单元格
    'file_info': '10px'      # 文件信息
}

# 间距和尺寸常量
UI_SPACING = {
    'small': '6px',
    'normal': '8px',
    'large': '12px',
    'extra_large': '16px'
}

# 圆角常量
UI_BORDER_RADIUS = {
    'small': '4px',
    'normal': '6px',
    'large': '8px'
}

# 颜色透明度
UI_ALPHA = {
    'light': '0.05',
    'medium': '0.1',
    'strong': '0.2'
}

# --- Constants ---
ORGANIZATION_NAME = "YourOrganizationName"  # Replace with your actual org name or identifier
APPLICATION_NAME = "DocumentSearchToolPySide"
CONFIG_FILE = 'search_config.ini'  # Keep for reference, but QSettings handles location
DEFAULT_DOC_DIR = ""

# --- Settings Keys --- (Define keys for QSettings)
SETTINGS_LAST_SEARCH_DIR = "history/lastSearchDirectory"
SETTINGS_WINDOW_GEOMETRY = "window/geometry"
SETTINGS_INDEX_DIRECTORY = "indexing/indexDirectory" # New key for index path
SETTINGS_SOURCE_DIRECTORIES = "indexing/sourceDirectories"
SETTINGS_ENABLE_OCR = "indexing/enableOcr"
SETTINGS_EXTRACTION_TIMEOUT = "indexing/extractionTimeout"
SETTINGS_TXT_CONTENT_LIMIT = "indexing/txtContentLimitKb"
SETTINGS_CASE_SENSITIVE = "search/caseSensitive"

# --- ADDED: Version Info ---
CURRENT_VERSION = "1.0.0"  # <--- Update this for each new release!
UPDATE_INFO_URL = "https://azariasy.github.io/-wen-zhi-sou-website/latest_version.json" # URL to your version info file
# -------------------------

# === 虚拟滚动相关类实现 ===
class VirtualResultsModel(QAbstractListModel):
    """虚拟滚动结果模型，完全兼容传统模式的文件分组和章节折叠功能"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results = []
        self.display_items = []  # 存储显示项目列表（文件组/章节组/内容项）
        self.current_theme = "现代蓝"
        self.parent_window = parent  # 存储父窗口引用以访问collapse_states
        
    def rowCount(self, parent=QModelIndex()):
        """返回显示项目总数"""
        return len(self.display_items)
        
    def data(self, index, role=Qt.DisplayRole):
        """返回指定索引的数据"""
        if not index.isValid() or index.row() >= len(self.display_items):
            return None
            
        if role == Qt.DisplayRole:
            item = self.display_items[index.row()]
            return self._generate_item_html(item, index.row())
        elif role == Qt.UserRole:
            # 返回原始项目数据
            return self.display_items[index.row()]
        
        return None
    
    def _process_results_for_display(self, results):
        """将原始搜索结果处理成显示项目列表，完全兼容传统模式逻辑"""
        self.beginResetModel()
        self.display_items = []
        
        if not results:
            # 添加一个友好的空状态显示项
            self.display_items.append({
                'type': 'empty_state',
                'content': '🔍 未找到匹配的搜索结果'
            })
            self.endResetModel()
            return
            
        try:
            # 检查搜索范围
            if hasattr(self.parent_window, 'last_search_scope') and self.parent_window.last_search_scope == 'filename':
                # 文件名搜索 - 简化显示
                self._process_filename_results(results)
            else:
                # 全文搜索 - 复杂分组显示
                self._process_fulltext_results(results)
                
        except Exception as e:
            print(f"Error processing results for virtual display: {e}")
            # 添加错误显示项
            self.display_items.append({
                'type': 'error',
                'content': f'处理搜索结果时出错: {e}'
            })
        
        self.endResetModel()
    
    def _process_grouped_results_for_display(self, grouped_results):
        """处理分组结果为虚拟滚动显示项目"""
        self.beginResetModel()
        self.display_items = []
        
        if not grouped_results:
            # 添加一个友好的空状态显示项
            self.display_items.append({
                'type': 'empty_state',
                'content': '🔍 未找到匹配的搜索结果'
            })
            self.endResetModel()
            return
        
        # 初始化分组折叠状态（如果不存在）
        if not hasattr(self.parent_window, 'group_collapse_states'):
            self.parent_window.group_collapse_states = {}
        
        # 处理分组结果
        for group_name, group_results in grouped_results.items():
            if not group_results:
                continue
                
            # 检查分组的折叠状态
            group_key = f"vgroup::{group_name}"
            is_collapsed = self.parent_window.group_collapse_states.get(group_key, False)
            
            # 添加分组标题（带折叠功能）
            self.display_items.append({
                'type': 'group_header',
                'group_name': group_name,
                'group_key': group_key,
                'result_count': len(group_results),
                'is_collapsed': is_collapsed
            })
            
            # 只有在未折叠时才显示分组中的结果
            if not is_collapsed:
                if self._is_filename_search():
                    # 文件名搜索：简化显示
                    for result in group_results:
                        self.display_items.append({
                            'type': 'filename_result',
                            'result': result
                        })
                else:
                    # 全文搜索：完整显示
                    self._process_fulltext_group_results(group_results)
        
        self.endResetModel()
    
    def _process_fulltext_group_results(self, results):
        """处理全文搜索的分组结果"""
        # 使用传统模式的逻辑进行文件和章节分组
        file_groups = {}
        
        for result in results:
            file_path = result.get('file_path', '')
            
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(result)
        
        # 为每个文件组生成显示项
        for file_path, file_results in file_groups.items():
            if not file_results:
                continue
                
            file_key = f"f::{file_path}"
            is_collapsed = self._get_collapse_state(file_key)
            
            # 添加文件组头部
            self.display_items.append({
                'type': 'file_group',
                'file_path': file_path,
                'file_key': file_key,
                'file_number': len(file_groups),
                'is_collapsed': is_collapsed
            })
            
            if not is_collapsed:
                # 文件未折叠，继续处理章节
                chapter_groups = {}
                
                for result in file_results:
                    # 确定章节键
                    heading = result.get('heading')
                    chapter_key = f"c::{file_path}::{heading if heading else '(无章节)'}"
                    
                    if chapter_key not in chapter_groups:
                        chapter_groups[chapter_key] = []
                    chapter_groups[chapter_key].append(result)
                
                # 为每个章节组生成显示项
                for chapter_key, chapter_results in chapter_groups.items():
                    if not chapter_results:
                        continue
                        
                    is_chapter_collapsed = self._get_collapse_state(chapter_key)
                    heading = chapter_results[0].get('heading', '(无章节)')
                    
                    # 添加章节组头部
                    self.display_items.append({
                        'type': 'chapter_group',
                        'chapter_key': chapter_key,
                        'heading': heading,
                        'is_collapsed': is_chapter_collapsed,
                        'result': chapter_results[0]  # 用于标题标记
                    })
                    
                    if not is_chapter_collapsed:
                        # 章节未折叠，添加内容
                        for result in chapter_results:
                            self.display_items.append({
                                'type': 'content',
                                'result': result
                            })
    
    def _is_filename_search(self):
        """检查是否为文件名搜索"""
        return (hasattr(self.parent_window, 'last_search_scope') and 
                self.parent_window.last_search_scope == 'filename')
    
    def _get_collapse_state(self, key):
        """获取折叠状态"""
        if self.parent_window and hasattr(self.parent_window, 'collapse_states'):
            return self.parent_window.collapse_states.get(key, False)
        return False
    
    def _process_filename_results(self, results):
        """处理文件名搜索结果"""
        processed_paths = set()
        
        # 添加美观的标题项
        self.display_items.append({
            'type': 'title',
            'content': f'📄 文件名搜索结果 ({len(results)} 个文件)'
        })
        
        for result in results:
            file_path = result.get('file_path', '(未知文件)')
            if file_path in processed_paths:
                continue
            processed_paths.add(file_path)
            
            self.display_items.append({
                'type': 'filename_result',
                'file_path': file_path,
                'result': result
            })
    
    def _process_fulltext_results(self, results):
        """处理全文搜索结果 - 完全兼容传统模式的文件分组和章节折叠"""
        last_file_path = None
        last_displayed_heading = None
        file_group_counter = 0
        
        for i, result in enumerate(results):
            file_path = result.get('file_path', '(未知文件)')
            original_heading = result.get('heading', '(无章节标题)')
            
            is_new_file = (file_path != last_file_path)
            is_new_heading = (original_heading != last_displayed_heading)
            
            # 处理新文件
            if is_new_file:
                file_group_counter += 1
                file_key = f"f::{file_path}"
                
                # 创建文件组项
                file_item = {
                    'type': 'file_group',
                    'file_path': file_path,
                    'file_key': file_key,
                    'file_number': file_group_counter,
                    'is_collapsed': self.parent_window.collapse_states.get(file_key, False) if self.parent_window else False,
                    'result': result
                }
                self.display_items.append(file_item)
                
                last_displayed_heading = None
                last_file_path = file_path
            
            # 处理章节（如果文件未折叠）
            file_key = f"f::{file_path}"
            is_file_collapsed = self.parent_window.collapse_states.get(file_key, False) if self.parent_window else False
            
            if not is_file_collapsed and (is_new_file or is_new_heading):
                # 检查是否是Excel数据
                if result.get('excel_sheet') is None:
                    # 修复：统一章节键格式，去除索引以确保同一章节的一致性
                    chapter_key = f"c::{file_path}::{original_heading if original_heading else '(无章节)'}"
                    is_chapter_collapsed = self.parent_window.collapse_states.get(chapter_key, False) if self.parent_window else False
                    
                    chapter_item = {
                        'type': 'chapter_group',
                        'file_path': file_path,
                        'chapter_key': chapter_key,
                        'heading': original_heading,
                        'is_collapsed': is_chapter_collapsed,
                        'result': result
                    }
                    self.display_items.append(chapter_item)
                    last_displayed_heading = original_heading
                else:
                    last_displayed_heading = None
            
            # 处理内容（段落或Excel数据）
            if not is_file_collapsed:
                # 修复：统一章节键格式，去除索引以确保同一章节的一致性
                chapter_key = f"c::{file_path}::{original_heading if original_heading else '(无章节)'}"
                is_chapter_collapsed = self.parent_window.collapse_states.get(chapter_key, False) if self.parent_window else False
                
                # 修复BUG：无论是否是Excel数据，只要章节被折叠就不显示内容
                if not is_chapter_collapsed:
                    content_item = {
                        'type': 'content',
                        'file_path': file_path,
                        'result': result,
                        'index': i
                    }
                    self.display_items.append(content_item)
    
    def _generate_item_html(self, item, index):
        """生成显示项的HTML内容"""
        try:
            item_type = item.get('type', 'unknown')
            
            if item_type == 'title':
                theme_colors = self._get_theme_colors()
                return f'''
                <div style="margin: 15px 5px 20px 5px; padding: 15px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 8px; border-left: 4px solid {theme_colors["primary"]};">
                    <h3 style="margin: 0; color: {theme_colors["primary"]}; font-size: 16px; font-weight: bold;">
                        {item["content"]}
                    </h3>
                </div>
                '''
                
            elif item_type == 'filename_result':
                return self._generate_filename_result_html(item)
                
            elif item_type == 'file_group':
                return self._generate_file_group_html(item)
                
            elif item_type == 'chapter_group':
                return self._generate_chapter_group_html(item)
                
            elif item_type == 'content':
                return self._generate_content_html(item)
                
            elif item_type == 'error':
                return f'<div style="margin: 10px; padding: 10px; background: #ffebee; border: 1px solid #f44336; border-radius: 4px; color: #c62828;">{item["content"]}</div>'
                
            elif item_type == 'group_header':
                theme_colors = self._get_theme_colors()
                group_name = item.get('group_name', '未知分组')
                group_key = item.get('group_key', 'unknown')
                result_count = item.get('result_count', 0)
                is_collapsed = item.get('is_collapsed', False)
                
                import html
                toggle_char = "▶" if is_collapsed else "▼"
                toggle_href = f'toggle::{html.escape(group_key, quote=True)}'
                escaped_group_name = html.escape(str(group_name))
                
                return f'''
                <div style="margin: 15px 10px 10px 10px; padding: 12px 16px; background: linear-gradient(135deg, {theme_colors["link_color"]}22, {theme_colors["link_color"]}11); border-left: 4px solid {theme_colors["link_color"]}; border-radius: 6px;">
                    <div style="font-size: 16px; font-weight: bold; color: {theme_colors["text_color"]}; margin-bottom: 4px;">
                        <a href="{toggle_href}" style="color: {theme_colors["link_color"]}; text-decoration:none; font-weight:bold; margin-right: 8px;">{toggle_char}</a>
                        📂 {escaped_group_name}
                    </div>
                    <div style="font-size: 13px; color: #666; font-style: italic;">
                        {result_count} 个结果
                    </div>
                </div>
                '''
                
            elif item_type == 'empty_state':
                theme_colors = self._get_theme_colors()
                return f'''
                <div style="margin: 50px 20px; padding: 40px; text-align: center; background: #f8f9fa; border-radius: 8px; border: 2px dashed #dee2e6;">
                    <div style="font-size: 48px; margin-bottom: 20px; color: #6c757d;">{item["content"].split()[0]}</div>
                    <div style="font-size: 18px; color: {theme_colors["text_color"]}; margin-bottom: 10px;">
                        {" ".join(item["content"].split()[1:])}
                    </div>
                    <div style="font-size: 14px; color: #6c757d; margin-top: 20px;">
                        请尝试调整搜索词或筛选条件
                    </div>
                </div>
                '''
                
            else:
                return f'<div style="margin: 10px; padding: 10px;">未知项目类型: {item_type}</div>'
                
        except Exception as e:
            print(f"Error generating item HTML: {e}")
            return f'<div style="margin: 10px; padding: 10px; background: #ffebee;">生成HTML时出错: {str(e)}</div>'
    
    def _get_theme_colors(self):
        """获取当前主题的颜色配置 - 扩展版本包含更多语义颜色"""
        if self.current_theme == "现代蓝":
            return {
                "highlight_bg": "#E3F2FD",
                "highlight_text": "#1565C0", 
                "link_color": "#2196F3",
                "text_color": "#333333",
                "primary": "#007ACC",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#F59E0B",
                "danger": "#EF4444"
            }
        elif self.current_theme == "现代紫":
            return {
                "highlight_bg": "#F3E5F5",
                "highlight_text": "#7B1FA2",
                "link_color": "#9C27B0", 
                "text_color": "#333333",
                "primary": "#8B5CF6",
                "success": "#10B981",
                "info": "#8B5CF6",
                "warning": "#F59E0B",
                "danger": "#EF4444"
            }
        elif self.current_theme == "现代红":
            return {
                "highlight_bg": "#FFE0E0",
                "highlight_text": "#C62828",
                "link_color": "#E53935",
                "text_color": "#333333",
                "primary": "#DC2626",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#F59E0B",
                "danger": "#DC2626"
            }
        elif self.current_theme == "现代橙":
            return {
                "highlight_bg": "#FFF3E0",
                "highlight_text": "#FF6F00",
                "link_color": "#FF9800",
                "text_color": "#333333",
                "primary": "#EA580C",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#EA580C",
                "danger": "#EF4444"
            }
        elif self.current_theme == "深色模式":
            return {
                "highlight_bg": "#374151",
                "highlight_text": "#60A5FA",
                "link_color": "#3B82F6",
                "text_color": "#F9FAFB",
                "primary": "#3B82F6",
                "success": "#059669",
                "info": "#3B82F6",
                "warning": "#D97706",
                "danger": "#DC2626"
            }
        elif self.current_theme == "护眼绿":
            return {
                "highlight_bg": "#DCFCE7",
                "highlight_text": "#047857",
                "link_color": "#059669",
                "text_color": "#1E1E1E",
                "primary": "#059669",
                "success": "#059669",
                "info": "#0891B2",
                "warning": "#D97706",
                "danger": "#DC2626"
            }
        else:
            return {
                "highlight_bg": "#FFECB3",
                "highlight_text": "#FF6F00",
                "link_color": "#FF9800",
                "text_color": "#333333",
                "primary": "#FF9800",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#F59E0B",
                "danger": "#EF4444"
            }
    
    def _generate_filename_result_html(self, item):
        """生成文件名搜索结果的HTML - 美观现代化样式"""
        file_path = item['file_path']
        result = item.get('result', {})
        theme_colors = self._get_theme_colors()
        
        # 计算文件信息
        import os
        from pathlib import Path
        try:
            file_name = os.path.basename(file_path)
            file_size = result.get('file_size', result.get('size', 0))
            mtime = result.get('last_modified', result.get('mtime', 0))

            # 格式化文件大小
            if file_size > 0:
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
            else:
                size_str = '未知大小'

            # 格式化修改时间
            if mtime > 0:
                import datetime
                mtime_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            else:
                mtime_str = '未知时间'

            # 获取文件类型图标
            file_ext = Path(file_path).suffix.lower()
            type_icon = "📄"
            if file_ext in ['.docx', '.doc']:
                type_icon = "📝"
            elif file_ext in ['.xlsx', '.xls']:
                type_icon = "📊"
            elif file_ext in ['.pptx', '.ppt']:
                type_icon = "📋"
            elif file_ext in ['.pdf']:
                type_icon = "📕"
            elif file_ext in ['.txt', '.md']:
                type_icon = "📄"
            elif file_ext in ['.jpg', '.png', '.gif', '.bmp']:
                type_icon = "🖼️"
            elif file_ext in ['.mp4', '.avi', '.mov']:
                type_icon = "🎬"
            elif file_ext in ['.mp3', '.wav', '.flac']:
                type_icon = "🎵"

        except Exception as e:
            file_name = file_path
            size_str = '未知大小'
            mtime_str = '未知时间'
            type_icon = "📄"

        # 计算文件夹路径
        folder_path_str = ""
        is_archive_member = "::" in file_path
        try:
            if is_archive_member:
                archive_file_path = file_path.split("::", 1)[0]
                folder_path_str = str(Path(archive_file_path).parent)
            else:
                path_obj = Path(file_path)
                if path_obj.is_file():
                    folder_path_str = str(path_obj.parent)
        except Exception:
            pass
        
        import html
        escaped_file_name = html.escape(file_name)
        escaped_file_path = html.escape(file_path)
        
        # 构建操作链接 - 使用现代化按钮样式
        links = [f'<a href="openfile:{html.escape(file_path, quote=True)}" style="color: #fff; text-decoration: none; padding: 6px 12px; background: {theme_colors["success"]}; border-radius: 4px; font-size: 12px; margin-right: 8px;">🔍 打开文件</a>']
        if folder_path_str:
            links.append(f'<a href="openfolder:{html.escape(folder_path_str, quote=True)}" style="color: #fff; text-decoration: none; padding: 6px 12px; background: {theme_colors["info"]}; border-radius: 4px; font-size: 12px;">📁 打开目录</a>')
        
        return f'''
        <div style="margin: 6px 5px; padding: 10px; background: #fff; border: 1px solid #e9ecef; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 18px; margin-right: 8px;">{type_icon}</span>
                    <span style="color: {theme_colors["text_color"]}; font-size: 13px; font-weight: bold;">{escaped_file_name}</span>
                </div>
                <div style="white-space: nowrap;">
                    {" ".join(links)}
                </div>
            </div>

            <div style="margin-left: 26px;">
                <p style="margin: 0 0 5px 0; color: #6c757d; font-size: 10px; font-family: monospace; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    {escaped_file_path}
                </p>
                <div style="padding: 5px 8px; background: #f8f9fa; border-radius: 3px;">
                    <span style="font-size: 11px; color: #6c757d;">📏 {size_str}</span>
                    <span style="margin-left: 20px; font-size: 11px; color: #6c757d;">🕒 {mtime_str}</span>
                </div>
            </div>
        </div>
        '''
    





# --- 导入统一路径处理工具 ---
from path_utils import normalize_path_for_display, normalize_path_for_index, PathStandardizer

# --- 导入统一主题管理工具 ---
from theme_manager import ThemeManager
# ------------------------

import sys
import io # 新增导入

# 确保 stdout 和 stderr 在非控制台模式下是可写的
# 这应该在几乎所有其他导入之前完成，特别是在 logging 和 jieba 导入之前
if sys.stdout is None:
    sys.stdout = io.StringIO()  # 重定向到一个内存字符串缓冲区
if sys.stderr is None:
    sys.stderr = io.StringIO()  # 同样重定向到内存缓冲区，避免与您后续的文件重定向冲突

# Import necessary classes from PySide6
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextBrowser, QProgressBar,
    QFileDialog, QMessageBox, QDateEdit, QCheckBox, QComboBox, QRadioButton, QDialog, QDialogButtonBox, QSpinBox,
    QButtonGroup, QListWidget, QListWidgetItem, QAbstractItemView, QGroupBox, QMenuBar, QToolBar, # ADDED QListWidget, QListWidgetItem, QAbstractItemView, QGroupBox, QMenuBar, QToolBar
    QStatusBar, # Ensure QProgressBar is imported if not already
    QTableWidget, QHeaderView, QTableWidgetItem,
    QTreeView, QSplitter, # 添加文件夹树视图所需的组件
    QSizePolicy, QFrame,
    QInputDialog,
    QTabWidget, QScrollArea, QTabBar, QTabWidget,
    QGridLayout, QMenu, # 添加QMenu用于右键菜单
    QListView, QStyledItemDelegate, QStackedWidget, QStyle, # 虚拟滚动所需组件
)
from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot, QUrl, QSettings, QDate, QTimer, QSize, QDir, QModelIndex, QRect, QAbstractListModel # Added QSize, QDir, QModelIndex, QRect, QAbstractListModel 
from PySide6.QtGui import QDesktopServices, QAction, QIntValidator, QShortcut, QKeySequence, QIcon, QColor, QStandardItemModel, QStandardItem, QTextDocument, QTextCursor, QPainter, QCursor # Added QStandardItemModel and QStandardItem, QTextDocument, QPainter, QCursor
import html  # Import html module for escaping

# --- ADDED: Network and Version Comparison Imports ---
import requests
from packaging import version
# -----------------------------------------------------

# Standard library imports
from pathlib import Path  # Added
import document_search  # Uncommented backend import
import traceback  # Keep for worker error reporting
import json  # Needed for structure map parsing
import functools # ADDED for LRU cache
import os  # Added for os.path.normpath
import time # Added for sleep
import datetime
import logging # Import logging module
import re
import subprocess
import shutil
import math
import codecs
import webbrowser
import requests.adapters  # 添加requests的适配器和重试策略导入
import urllib3.util  # 替换过时的requests.packages导入

# --- ADDED: 导入许可证管理器和对话框 ---
from license_manager import get_license_manager, Features, LicenseStatus
from license_dialog import LicenseDialog
# --------------------------------------

# --- ADDED: Try importing qdarkstyle --- 
_qdarkstyle_available = False
try:
    import qdarkstyle
    _qdarkstyle_available = True
except ImportError:
    pass # qdarkstyle not installed, will use basic dark theme
# -------------------------------------

# --- 添加资源文件路径解析器 ---
def get_resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和打包后的环境
    
    Args:
        relative_path (str): 相对于应用程序根目录的资源文件路径
        
    Returns:
        str: 资源文件的绝对路径
    """
    # 如果路径带有特殊前缀，则移除
    if relative_path.startswith('qss-resource:'):
        relative_path = relative_path[len('qss-resource:'):]
    
    # 如果路径被引号包围，则移除引号
    if (relative_path.startswith('"') and relative_path.endswith('"')) or \
       (relative_path.startswith("'") and relative_path.endswith("'")):
        relative_path = relative_path[1:-1]
    
    # 判断是否在PyInstaller环境中运行
    if getattr(sys, 'frozen', False):
        # 在PyInstaller环境中
        base_path = sys._MEIPASS
    else:
        # 在开发环境中
        base_path = os.path.dirname(__file__)
    
    # 组合路径并返回
    resource_path = os.path.join(base_path, relative_path)
    print(f"资源路径解析: {relative_path} -> {resource_path}")
    return resource_path
# ------------------------------

# ====================
# UI设计常量体系
# ====================

# 字体大小常量
UI_FONT_SIZES = {
    'normal': '12px',        # 标准文本
    'small': '11px',         # 小号文本
    'large': '14px',         # 大号文本
    'icon': '14px',          # 图标
    'extra_small': '10px',   # 额外小号文本
    'file_header': '16px',   # 文件标题
    'section_header': '13px', # 章节标题
    'table_cell': '11px',    # 表格单元格
    'file_info': '10px'      # 文件信息
}

# 间距和尺寸常量
UI_SPACING = {
    'small': '6px',
    'normal': '8px',
    'large': '12px',
    'extra_large': '16px'
}

# 圆角常量
UI_BORDER_RADIUS = {
    'small': '4px',
    'normal': '6px',
    'large': '8px'
}

# 颜色透明度
UI_ALPHA = {
    'light': '0.05',
    'medium': '0.1',
    'strong': '0.2'
}

# --- Constants ---
ORGANIZATION_NAME = "YourOrganizationName"  # Replace with your actual org name or identifier
APPLICATION_NAME = "DocumentSearchToolPySide"
CONFIG_FILE = 'search_config.ini'  # Keep for reference, but QSettings handles location
DEFAULT_DOC_DIR = ""

# --- Settings Keys --- (Define keys for QSettings)
SETTINGS_LAST_SEARCH_DIR = "history/lastSearchDirectory"
SETTINGS_WINDOW_GEOMETRY = "window/geometry"
SETTINGS_INDEX_DIRECTORY = "indexing/indexDirectory" # New key for index path
SETTINGS_SOURCE_DIRECTORIES = "indexing/sourceDirectories"
SETTINGS_ENABLE_OCR = "indexing/enableOcr"
SETTINGS_EXTRACTION_TIMEOUT = "indexing/extractionTimeout"
SETTINGS_TXT_CONTENT_LIMIT = "indexing/txtContentLimitKb"
SETTINGS_CASE_SENSITIVE = "search/caseSensitive"

# --- ADDED: Version Info ---
CURRENT_VERSION = "1.0.0"  # <--- Update this for each new release!
UPDATE_INFO_URL = "https://azariasy.github.io/-wen-zhi-sou-website/latest_version.json" # URL to your version info file
# -------------------------

# === 虚拟滚动相关类实现 ===
class VirtualResultsModel(QAbstractListModel):
    """虚拟滚动结果模型，完全兼容传统模式的文件分组和章节折叠功能"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results = []
        self.display_items = []  # 存储显示项目列表（文件组/章节组/内容项）
        self.current_theme = "现代蓝"
        self.parent_window = parent  # 存储父窗口引用以访问collapse_states
        
    def rowCount(self, parent=QModelIndex()):
        """返回显示项目总数"""
        return len(self.display_items)
        
    def data(self, index, role=Qt.DisplayRole):
        """返回指定索引的数据"""
        if not index.isValid() or index.row() >= len(self.display_items):
            return None
            
        if role == Qt.DisplayRole:
            item = self.display_items[index.row()]
            return self._generate_item_html(item, index.row())
        elif role == Qt.UserRole:
            # 返回原始项目数据
            return self.display_items[index.row()]
        
        return None
    
    def _process_results_for_display(self, results):
        """将原始搜索结果处理成显示项目列表，完全兼容传统模式逻辑"""
        self.beginResetModel()
        self.display_items = []
        
        if not results:
            # 添加一个友好的空状态显示项
            self.display_items.append({
                'type': 'empty_state',
                'content': '🔍 未找到匹配的搜索结果'
            })
            self.endResetModel()
            return
            
        try:
            # 检查搜索范围
            if hasattr(self.parent_window, 'last_search_scope') and self.parent_window.last_search_scope == 'filename':
                # 文件名搜索 - 简化显示
                self._process_filename_results(results)
            else:
                # 全文搜索 - 复杂分组显示
                self._process_fulltext_results(results)
                
        except Exception as e:
            print(f"Error processing results for virtual display: {e}")
            # 添加错误显示项
            self.display_items.append({
                'type': 'error',
                'content': f'处理搜索结果时出错: {e}'
            })
        
        self.endResetModel()
    
    def _process_grouped_results_for_display(self, grouped_results):
        """处理分组结果为虚拟滚动显示项目"""
        self.beginResetModel()
        self.display_items = []
        
        if not grouped_results:
            # 添加一个友好的空状态显示项
            self.display_items.append({
                'type': 'empty_state',
                'content': '🔍 未找到匹配的搜索结果'
            })
            self.endResetModel()
            return
        
        # 初始化分组折叠状态（如果不存在）
        if not hasattr(self.parent_window, 'group_collapse_states'):
            self.parent_window.group_collapse_states = {}
        
        # 处理分组结果
        for group_name, group_results in grouped_results.items():
            if not group_results:
                continue
                
            # 检查分组的折叠状态
            group_key = f"vgroup::{group_name}"
            is_collapsed = self.parent_window.group_collapse_states.get(group_key, False)
            
            # 添加分组标题（带折叠功能）
            self.display_items.append({
                'type': 'group_header',
                'group_name': group_name,
                'group_key': group_key,
                'result_count': len(group_results),
                'is_collapsed': is_collapsed
            })
            
            # 只有在未折叠时才显示分组中的结果
            if not is_collapsed:
                if self._is_filename_search():
                    # 文件名搜索：简化显示
                    for result in group_results:
                        self.display_items.append({
                            'type': 'filename_result',
                            'result': result
                        })
                else:
                    # 全文搜索：完整显示
                    self._process_fulltext_group_results(group_results)
        
        self.endResetModel()
    
    def _process_fulltext_group_results(self, results):
        """处理全文搜索的分组结果"""
        # 使用传统模式的逻辑进行文件和章节分组
        file_groups = {}
        
        for result in results:
            file_path = result.get('file_path', '')
            
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(result)
        
        # 为每个文件组生成显示项
        for file_path, file_results in file_groups.items():
            if not file_results:
                continue
                
            file_key = f"f::{file_path}"
            is_collapsed = self._get_collapse_state(file_key)
            
            # 添加文件组头部
            self.display_items.append({
                'type': 'file_group',
                'file_path': file_path,
                'file_key': file_key,
                'file_number': len(file_groups),
                'is_collapsed': is_collapsed
            })
            
            if not is_collapsed:
                # 文件未折叠，继续处理章节
                chapter_groups = {}
                
                for result in file_results:
                    # 确定章节键
                    heading = result.get('heading')
                    chapter_key = f"c::{file_path}::{heading if heading else '(无章节)'}"
                    
                    if chapter_key not in chapter_groups:
                        chapter_groups[chapter_key] = []
                    chapter_groups[chapter_key].append(result)
                
                # 为每个章节组生成显示项
                for chapter_key, chapter_results in chapter_groups.items():
                    if not chapter_results:
                        continue
                        
                    is_chapter_collapsed = self._get_collapse_state(chapter_key)
                    heading = chapter_results[0].get('heading', '(无章节)')
                    
                    # 添加章节组头部
                    self.display_items.append({
                        'type': 'chapter_group',
                        'chapter_key': chapter_key,
                        'heading': heading,
                        'is_collapsed': is_chapter_collapsed,
                        'result': chapter_results[0]  # 用于标题标记
                    })
                    
                    if not is_chapter_collapsed:
                        # 章节未折叠，添加内容
                        for result in chapter_results:
                            self.display_items.append({
                                'type': 'content',
                                'result': result
                            })
    
    def _is_filename_search(self):
        """检查是否为文件名搜索"""
        return (hasattr(self.parent_window, 'last_search_scope') and 
                self.parent_window.last_search_scope == 'filename')
    
    def _get_collapse_state(self, key):
        """获取折叠状态"""
        if self.parent_window and hasattr(self.parent_window, 'collapse_states'):
            return self.parent_window.collapse_states.get(key, False)
        return False
    
    def _process_filename_results(self, results):
        """处理文件名搜索结果"""
        processed_paths = set()
        
        # 添加美观的标题项
        self.display_items.append({
            'type': 'title',
            'content': f'📄 文件名搜索结果 ({len(results)} 个文件)'
        })
        
        for result in results:
            file_path = result.get('file_path', '(未知文件)')
            if file_path in processed_paths:
                continue
            processed_paths.add(file_path)
            
            self.display_items.append({
                'type': 'filename_result',
                'file_path': file_path,
                'result': result
            })
    
    def _process_fulltext_results(self, results):
        """处理全文搜索结果 - 完全兼容传统模式的文件分组和章节折叠"""
        last_file_path = None
        last_displayed_heading = None
        file_group_counter = 0
        
        for i, result in enumerate(results):
            file_path = result.get('file_path', '(未知文件)')
            original_heading = result.get('heading', '(无章节标题)')
            
            is_new_file = (file_path != last_file_path)
            is_new_heading = (original_heading != last_displayed_heading)
            
            # 处理新文件
            if is_new_file:
                file_group_counter += 1
                file_key = f"f::{file_path}"
                
                # 创建文件组项
                file_item = {
                    'type': 'file_group',
                    'file_path': file_path,
                    'file_key': file_key,
                    'file_number': file_group_counter,
                    'is_collapsed': self.parent_window.collapse_states.get(file_key, False) if self.parent_window else False,
                    'result': result
                }
                self.display_items.append(file_item)
                
                last_displayed_heading = None
                last_file_path = file_path
            
            # 处理章节（如果文件未折叠）
            file_key = f"f::{file_path}"
            is_file_collapsed = self.parent_window.collapse_states.get(file_key, False) if self.parent_window else False
            
            if not is_file_collapsed and (is_new_file or is_new_heading):
                # 检查是否是Excel数据
                if result.get('excel_sheet') is None:
                    # 修复：统一章节键格式，去除索引以确保同一章节的一致性
                    chapter_key = f"c::{file_path}::{original_heading if original_heading else '(无章节)'}"
                    is_chapter_collapsed = self.parent_window.collapse_states.get(chapter_key, False) if self.parent_window else False
                    
                    chapter_item = {
                        'type': 'chapter_group',
                        'file_path': file_path,
                        'chapter_key': chapter_key,
                        'heading': original_heading,
                        'is_collapsed': is_chapter_collapsed,
                        'result': result
                    }
                    self.display_items.append(chapter_item)
                    last_displayed_heading = original_heading
                else:
                    last_displayed_heading = None
            
            # 处理内容（段落或Excel数据）
            if not is_file_collapsed:
                # 修复：统一章节键格式，去除索引以确保同一章节的一致性
                chapter_key = f"c::{file_path}::{original_heading if original_heading else '(无章节)'}"
                is_chapter_collapsed = self.parent_window.collapse_states.get(chapter_key, False) if self.parent_window else False
                
                # 修复BUG：无论是否是Excel数据，只要章节被折叠就不显示内容
                if not is_chapter_collapsed:
                    content_item = {
                        'type': 'content',
                        'file_path': file_path,
                        'result': result,
                        'index': i
                    }
                    self.display_items.append(content_item)
    
    def _generate_item_html(self, item, index):
        """生成显示项的HTML内容"""
        try:
            item_type = item.get('type', 'unknown')
            
            if item_type == 'title':
                theme_colors = self._get_theme_colors()
                return f'''
                <div style="margin: 15px 5px 20px 5px; padding: 15px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 8px; border-left: 4px solid {theme_colors["primary"]};">
                    <h3 style="margin: 0; color: {theme_colors["primary"]}; font-size: 16px; font-weight: bold;">
                        {item["content"]}
                    </h3>
                </div>
                '''
                
            elif item_type == 'filename_result':
                return self._generate_filename_result_html(item)
                
            elif item_type == 'file_group':
                return self._generate_file_group_html(item)
                
            elif item_type == 'chapter_group':
                return self._generate_chapter_group_html(item)
                
            elif item_type == 'content':
                return self._generate_content_html(item)
                
            elif item_type == 'error':
                return f'<div style="margin: 10px; padding: 10px; background: #ffebee; border: 1px solid #f44336; border-radius: 4px; color: #c62828;">{item["content"]}</div>'
                
            elif item_type == 'group_header':
                theme_colors = self._get_theme_colors()
                group_name = item.get('group_name', '未知分组')
                group_key = item.get('group_key', 'unknown')
                result_count = item.get('result_count', 0)
                is_collapsed = item.get('is_collapsed', False)
                
                import html
                toggle_char = "▶" if is_collapsed else "▼"
                toggle_href = f'toggle::{html.escape(group_key, quote=True)}'
                escaped_group_name = html.escape(str(group_name))
                
                return f'''
                <div style="margin: 15px 10px 10px 10px; padding: 12px 16px; background: linear-gradient(135deg, {theme_colors["link_color"]}22, {theme_colors["link_color"]}11); border-left: 4px solid {theme_colors["link_color"]}; border-radius: 6px;">
                    <div style="font-size: 16px; font-weight: bold; color: {theme_colors["text_color"]}; margin-bottom: 4px;">
                        <a href="{toggle_href}" style="color: {theme_colors["link_color"]}; text-decoration:none; font-weight:bold; margin-right: 8px;">{toggle_char}</a>
                        📂 {escaped_group_name}
                    </div>
                    <div style="font-size: 13px; color: #666; font-style: italic;">
                        {result_count} 个结果
                    </div>
                </div>
                '''
                
            elif item_type == 'empty_state':
                theme_colors = self._get_theme_colors()
                return f'''
                <div style="margin: 50px 20px; padding: 40px; text-align: center; background: #f8f9fa; border-radius: 8px; border: 2px dashed #dee2e6;">
                    <div style="font-size: 48px; margin-bottom: 20px; color: #6c757d;">{item["content"].split()[0]}</div>
                    <div style="font-size: 18px; color: {theme_colors["text_color"]}; margin-bottom: 10px;">
                        {" ".join(item["content"].split()[1:])}
                    </div>
                    <div style="font-size: 14px; color: #6c757d; margin-top: 20px;">
                        请尝试调整搜索词或筛选条件
                    </div>
                </div>
                '''
                
            else:
                return f'<div style="margin: 10px; padding: 10px;">未知项目类型: {item_type}</div>'
                
        except Exception as e:
            print(f"Error generating item HTML: {e}")
            return f'<div style="margin: 10px; padding: 10px; background: #ffebee;">生成HTML时出错: {str(e)}</div>'
    
    def _get_theme_colors(self):
        """获取当前主题的颜色配置 - 扩展版本包含更多语义颜色"""
        if self.current_theme == "现代蓝":
            return {
                "highlight_bg": "#E3F2FD",
                "highlight_text": "#1565C0", 
                "link_color": "#2196F3",
                "text_color": "#333333",
                "primary": "#007ACC",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#F59E0B",
                "danger": "#EF4444"
            }
        elif self.current_theme == "现代紫":
            return {
                "highlight_bg": "#F3E5F5",
                "highlight_text": "#7B1FA2",
                "link_color": "#9C27B0", 
                "text_color": "#333333",
                "primary": "#8B5CF6",
                "success": "#10B981",
                "info": "#8B5CF6",
                "warning": "#F59E0B",
                "danger": "#EF4444"
            }
        elif self.current_theme == "现代红":
            return {
                "highlight_bg": "#FFE0E0",
                "highlight_text": "#C62828",
                "link_color": "#E53935",
                "text_color": "#333333",
                "primary": "#DC2626",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#F59E0B",
                "danger": "#DC2626"
            }
        elif self.current_theme == "现代橙":
            return {
                "highlight_bg": "#FFF3E0",
                "highlight_text": "#FF6F00",
                "link_color": "#FF9800",
                "text_color": "#333333",
                "primary": "#EA580C",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#EA580C",
                "danger": "#EF4444"
            }
        elif self.current_theme == "深色模式":
            return {
                "highlight_bg": "#374151",
                "highlight_text": "#60A5FA",
                "link_color": "#3B82F6",
                "text_color": "#F9FAFB",
                "primary": "#3B82F6",
                "success": "#059669",
                "info": "#3B82F6",
                "warning": "#D97706",
                "danger": "#DC2626"
            }
        elif self.current_theme == "护眼绿":
            return {
                "highlight_bg": "#DCFCE7",
                "highlight_text": "#047857",
                "link_color": "#059669",
                "text_color": "#1E1E1E",
                "primary": "#059669",
                "success": "#059669",
                "info": "#0891B2",
                "warning": "#D97706",
                "danger": "#DC2626"
            }
        else:
            return {
                "highlight_bg": "#FFECB3",
                "highlight_text": "#FF6F00",
                "link_color": "#FF9800",
                "text_color": "#333333",
                "primary": "#FF9800",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#F59E0B",
                "danger": "#EF4444"
            }
    
    def _generate_filename_result_html(self, item):
        """生成文件名搜索结果的HTML - 美观现代化样式"""
        file_path = item['file_path']
        result = item.get('result', {})
        theme_colors = self._get_theme_colors()
        
        # 计算文件信息
        import os
        from pathlib import Path
        try:
            file_name = os.path.basename(file_path)
            file_size = result.get('file_size', result.get('size', 0))
            mtime = result.get('last_modified', result.get('mtime', 0))

            # 格式化文件大小
            if file_size > 0:
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
            else:
                size_str = '未知大小'

            # 格式化修改时间
            if mtime > 0:
                import datetime
                mtime_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            else:
                mtime_str = '未知时间'

            # 获取文件类型图标
            file_ext = Path(file_path).suffix.lower()
            type_icon = "📄"
            if file_ext in ['.docx', '.doc']:
                type_icon = "📝"
            elif file_ext in ['.xlsx', '.xls']:
                type_icon = "📊"
            elif file_ext in ['.pptx', '.ppt']:
                type_icon = "📋"
            elif file_ext in ['.pdf']:
                type_icon = "📕"
            elif file_ext in ['.txt', '.md']:
                type_icon = "📄"
            elif file_ext in ['.jpg', '.png', '.gif', '.bmp']:
                type_icon = "🖼️"
            elif file_ext in ['.mp4', '.avi', '.mov']:
                type_icon = "🎬"
            elif file_ext in ['.mp3', '.wav', '.flac']:
                type_icon = "🎵"

        except Exception as e:
            file_name = file_path
            size_str = '未知大小'
            mtime_str = '未知时间'
            type_icon = "📄"
        
        # 计算文件夹路径
        folder_path_str = ""
        is_archive_member = "::" in file_path
        try:
            if is_archive_member:
                archive_file_path = file_path.split("::", 1)[0]
                folder_path_str = str(Path(archive_file_path).parent)
            else:
                path_obj = Path(file_path)
                if path_obj.is_file():
                    folder_path_str = str(path_obj.parent)
        except Exception:
            pass
        
        import html
        escaped_file_name = html.escape(file_name)
        escaped_file_path = html.escape(file_path)
        
        # 构建操作链接 - 使用现代化按钮样式
        links = [f'<a href="openfile:{html.escape(file_path, quote=True)}" style="color: #fff; text-decoration: none; padding: 6px 12px; background: {theme_colors["success"]}; border-radius: 4px; font-size: 12px; margin-right: 8px;">🔍 打开文件</a>']
        if folder_path_str:
            links.append(f'<a href="openfolder:{html.escape(folder_path_str, quote=True)}" style="color: #fff; text-decoration: none; padding: 6px 12px; background: {theme_colors["info"]}; border-radius: 4px; font-size: 12px;">📁 打开目录</a>')
        
        return f'''
        <div style="margin: 6px 5px; padding: 10px; background: #fff; border: 1px solid #e9ecef; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 18px; margin-right: 8px;">{type_icon}</span>
                    <span style="color: {theme_colors["text_color"]}; font-size: 13px; font-weight: bold;">{escaped_file_name}</span>
                </div>
                <div style="white-space: nowrap;">
                    {" ".join(links)}
                </div>
            </div>

            <div style="margin-left: 26px;">
                <p style="margin: 0 0 5px 0; color: #6c757d; font-size: 10px; font-family: monospace; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    {escaped_file_path}
                </p>
                <div style="padding: 5px 8px; background: #f8f9fa; border-radius: 3px;">
                    <span style="font-size: 11px; color: #6c757d;">📏 {size_str}</span>
                    <span style="margin-left: 20px; font-size: 11px; color: #6c757d;">🕒 {mtime_str}</span>
                </div>
            </div>
        </div>
        '''
    
    def _generate_file_group_html(self, item):
        """生成文件组头部的HTML"""
        file_path = item['file_path']
        file_key = item['file_key']
        file_number = item['file_number']
        is_collapsed = item['is_collapsed']
        theme_colors = self._get_theme_colors()
        
        import html
        
        toggle_char = "[+]" if is_collapsed else "[-]"
        toggle_href = f'toggle::{html.escape(file_key, quote=True)}'
        escaped_path = html.escape(file_path)
        
        # 计算文件夹路径
        folder_path_str = ""
        is_archive_member = "::" in file_path
        try:
            if is_archive_member:
                archive_file_path = file_path.split("::", 1)[0]
                from pathlib import Path
                folder_path_str = str(Path(archive_file_path).parent)
            else:
                from pathlib import Path
                path_obj = Path(file_path)
                if path_obj.is_file():
                    folder_path_str = str(path_obj.parent)
        except Exception:
            pass
        
        # 构建现代化操作按钮 - 与文件名搜索保持一致
        links = [f'<a href="openfile:{html.escape(file_path, quote=True)}" style="color: #fff; text-decoration: none; padding: 6px 12px; background: {theme_colors["success"]}; border-radius: 4px; font-size: 12px; margin-right: 8px;">🔍 打开文件</a>']
        if folder_path_str:
            links.append(f'<a href="openfolder:{html.escape(folder_path_str, quote=True)}" style="color: #fff; text-decoration: none; padding: 6px 12px; background: {theme_colors["info"]}; border-radius: 4px; font-size: 12px;">📁 打开目录</a>')

        # 提取文件名和路径，类似文件名搜索的处理方式
        import os
        file_name = os.path.basename(file_path)
        file_directory = os.path.dirname(file_path)
        escaped_file_name = html.escape(file_name)
        escaped_directory = html.escape(file_directory)

        # 获取文件类型图标
        from pathlib import Path
        file_ext = Path(file_path).suffix.lower()
        type_icon = "📄"
        if file_ext in ['.docx', '.doc']:
            type_icon = "📝"
        elif file_ext in ['.xlsx', '.xls']:
            type_icon = "📊"
        elif file_ext in ['.pptx', '.ppt']:
            type_icon = "📋"
        elif file_ext in ['.pdf']:
            type_icon = "📕"
        elif file_ext in ['.txt', '.md']:
            type_icon = "📄"
        elif file_ext in ['.jpg', '.png', '.gif', '.bmp']:
            type_icon = "🖼️"
        elif file_ext in ['.mp4', '.avi', '.mov']:
            type_icon = "🎬"
        elif file_ext in ['.mp3', '.wav', '.flac']:
            type_icon = "🎵"
        
        return f'''
        <div style="margin: 15px 5px 5px 5px; padding: 12px; background: #f8f9fa; border-radius: 6px; border: 1px solid #e9ecef;">
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="vertical-align: middle;">
                                                <h3 style="margin: 0; color: {theme_colors["text_color"]}; font-size: 14px; font-weight: bold; display: inline-block;">
                            <a href="{toggle_href}" style="color: {theme_colors["link_color"]}; text-decoration:none; font-weight:bold; margin-right: 8px; font-size: 14px;">{toggle_char}</a>
                            <span style="font-size: 16px; margin-right: 8px;">{type_icon}</span>
                {file_number}. {escaped_path}
            </h3>
                        <div style="margin-left: 38px;">
                            <p style="margin: 0; color: #6c757d; font-size: 11px; font-family: monospace;">
                                📁 {escaped_directory}
                            </p>
            </div>
                    </td>
                    <td style="text-align: right; vertical-align: top; white-space: nowrap; padding-top: 8px;">
                        {" ".join(links)}
                    </td>
                </tr>
            </table>
        </div>
        '''
    
    def _generate_chapter_group_html(self, item):
        """生成章节组头部的HTML"""
        chapter_key = item['chapter_key']
        heading = item['heading']
        is_collapsed = item['is_collapsed']
        result = item['result']
        theme_colors = self._get_theme_colors()
        
        import html
        
        toggle_char = "[+]" if is_collapsed else "[-]"
        toggle_href = f'toggle::{html.escape(chapter_key, quote=True)}'
        
        # 处理标记的标题
        marked_heading = result.get('marked_heading')
        heading_to_display = marked_heading if marked_heading is not None else heading
        if heading_to_display is None:
            heading_to_display = '(无章节标题)'
        escaped_heading = html.escape(str(heading_to_display))
        
        # 处理高亮
        if marked_heading and "__HIGHLIGHT_START__" in escaped_heading:
            escaped_heading = escaped_heading.replace(
                html.escape("__HIGHLIGHT_START__"), 
                f'<span style="background-color: {theme_colors["highlight_bg"]}; color: {theme_colors["highlight_text"]};">'
            )
            escaped_heading = escaped_heading.replace(html.escape("__HIGHLIGHT_END__"), '</span>')
        
        return f'''
        <div style="margin: 8px 15px 5px 25px; padding: 6px;">
            <p style="margin: 0; color: {theme_colors["text_color"]};">
                <a href="{toggle_href}" style="color: {theme_colors["link_color"]}; text-decoration:none; font-weight:bold; margin-right: 6px;">{toggle_char}</a>
                <b>章节:</b> {escaped_heading}
            </p>
        </div>
        '''
    
    def _generate_content_html(self, item):
        """生成内容的HTML（段落或Excel表格）"""
        result = item['result']
        theme_colors = self._get_theme_colors()
        
        # 检查是否是Excel数据
        excel_headers = result.get('excel_headers')
        excel_values = result.get('excel_values')
        
        if excel_headers is not None and excel_values is not None:
            return self._generate_excel_content_html(result, theme_colors)
        else:
            return self._generate_paragraph_content_html(result, theme_colors)
    
    def _generate_excel_content_html(self, result, theme_colors):
        """生成Excel内容的HTML - 现代化样式"""
        excel_headers = result.get('excel_headers', [])
        excel_values = result.get('excel_values', [])
        excel_sheet = result.get('excel_sheet', '')
        excel_row_idx = result.get('excel_row_idx', 0)
        
        import html
        
        html_parts = []
        html_parts.append(f'''
        <div style="margin: {UI_SPACING['normal']} {UI_SPACING['extra_large']}; padding: {UI_SPACING['large']};
                    background: linear-gradient(145deg, #ffffff, #f8f9fa);
                    border: 1px solid #e3e7ea; border-radius: {UI_BORDER_RADIUS['normal']};
                    box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
            <div style="margin-bottom: {UI_SPACING['normal']}; padding: {UI_SPACING['small']};
                        background: {theme_colors["primary"]}15; border-radius: {UI_BORDER_RADIUS['small']};
                        border-left: 4px solid {theme_colors["primary"]};">
                <h4 style="margin: 0; font-size: {UI_FONT_SIZES['section_header']}; color: {theme_colors["text_color"]};">
                    📊 表格: {html.escape(str(excel_sheet) if excel_sheet is not None else "未知表格")} | 行: {excel_row_idx}
                </h4>
            </div>
        ''')

        # 生成现代化表格
        html_parts.append(f'''
            <table style="width: 100%; border-collapse: collapse; background: white;
                         border-radius: {UI_BORDER_RADIUS['small']}; overflow: hidden;
                         box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        ''')

        # 表头
        html_parts.append(f"<tr style='background: linear-gradient(135deg, {theme_colors['primary']}20, {theme_colors['primary']}15);'>")
        for header in excel_headers:
            header_text = str(header) if header is not None else ''
            html_parts.append(f'''
                <th style="padding: {UI_SPACING['normal']}; border: none;
                          font-size: {UI_FONT_SIZES['table_cell']}; font-weight: 600;
                          color: {theme_colors["text_color"]}; text-align: left;">
                    {html.escape(header_text)}
                </th>
            ''')
        html_parts.append("</tr>")
        
        # 数据行
        html_parts.append("<tr style='background: white;'>")
        escaped_start_marker = html.escape("__HIGHLIGHT_START__")
        escaped_end_marker = html.escape("__HIGHLIGHT_END__")
        
        for value in excel_values:
            value_text = str(value) if value is not None else ''
            escaped_value = html.escape(value_text)
            
            # 处理高亮
            if escaped_start_marker in escaped_value:
                highlighted_value = escaped_value.replace(
                    escaped_start_marker,
                    f'<mark style="background: linear-gradient(120deg, {theme_colors["highlight_bg"]}60, {theme_colors["highlight_bg"]}); color: {theme_colors["highlight_text"]}; border-radius: 3px; padding: 2px 4px;">'
                ).replace(escaped_end_marker, '</mark>')
            else:
                highlighted_value = escaped_value
                
            html_parts.append(f'''
                <td style="padding: {UI_SPACING['normal']}; border: none;
                          font-size: {UI_FONT_SIZES['table_cell']}; color: {theme_colors["text_color"]};
                          border-bottom: 1px solid #f0f0f0;">
                    {highlighted_value}
                </td>
            ''')
        html_parts.append("</tr>")
        html_parts.append("</table>")
        html_parts.append('</div>')
        
        return "".join(html_parts)
    
    def _generate_paragraph_content_html(self, result, theme_colors):
        """生成段落内容的HTML - 现代化样式"""
        original_paragraph = result.get('paragraph')
        marked_paragraph = result.get('marked_paragraph')
        match_start = result.get('match_start')
        match_end = result.get('match_end')
        
        if original_paragraph is None:
            return ''
        
        # 确定要显示的段落文本
        paragraph_text_for_highlight = marked_paragraph if marked_paragraph is not None else original_paragraph
        if paragraph_text_for_highlight is None:
            paragraph_text_for_highlight = str(original_paragraph) if original_paragraph is not None else ''
        else:
            paragraph_text_for_highlight = str(paragraph_text_for_highlight)
        
        import html
        escaped_paragraph = html.escape(paragraph_text_for_highlight)
        
        # 处理高亮
        highlighted_paragraph_display = escaped_paragraph
        
        # 短语搜索的精确高亮
        if match_start is not None and match_end is not None:
            if 0 <= match_start < match_end <= len(escaped_paragraph):
                pre = escaped_paragraph[:match_start]
                mat = escaped_paragraph[match_start:match_end]
                post = escaped_paragraph[match_end:]
                highlighted_paragraph_display = f'{pre}<mark style="background: linear-gradient(120deg, {theme_colors["highlight_bg"]}60, {theme_colors["highlight_bg"]}); color: {theme_colors["highlight_text"]}; border-radius: 3px; padding: 2px 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">{mat}</mark>{post}'
        # 模糊搜索的标记高亮
        elif marked_paragraph:
            escaped_start_marker = html.escape("__HIGHLIGHT_START__")
            escaped_end_marker = html.escape("__HIGHLIGHT_END__")
            if escaped_start_marker in escaped_paragraph:
                highlighted_paragraph_display = escaped_paragraph.replace(
                    escaped_start_marker,
                    f'<mark style="background: linear-gradient(120deg, {theme_colors["highlight_bg"]}60, {theme_colors["highlight_bg"]}); color: {theme_colors["highlight_text"]}; border-radius: 3px; padding: 2px 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">'
                ).replace(escaped_end_marker, '</mark>')
        
        return f'''
        <div style="margin: {UI_SPACING['normal']} {UI_SPACING['extra_large']}; padding: {UI_SPACING['large']};
                    background: linear-gradient(145deg, #ffffff, #fafbfc);
                    border: 1px solid #e8ecef; border-radius: {UI_BORDER_RADIUS['normal']};
                    border-left: 4px solid {theme_colors["success"]};
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="margin-bottom: {UI_SPACING['small']};">
                <span style="font-size: {UI_FONT_SIZES['small']}; color: {theme_colors["success"]}; font-weight: 600;">
                    📄 段落内容
                </span>
            </div>
            <div style="font-size: {UI_FONT_SIZES['normal']}; line-height: 1.6; color: {theme_colors["text_color"]};
                        word-wrap: break-word; overflow-wrap: break-word;">
                {highlighted_paragraph_display}
            </div>
        </div>
        '''

    def set_results(self, results):
        """设置搜索结果并处理成显示项目 - 支持完整的查看方式"""
        self.results = results
        
        # 从父窗口获取查看方式设置并应用完整的处理流程
        if self.parent_window:
            # 使用默认相关性排序（搜索引擎返回顺序）
            sorted_results = results
            
            # 检查是否需要分组显示
            if (hasattr(self.parent_window, 'grouping_enabled') and 
                self.parent_window.grouping_enabled and 
                hasattr(self.parent_window, 'current_grouping_mode') and 
                self.parent_window.current_grouping_mode != 'none'):
                
                # 应用分组，然后转换为虚拟滚动可以处理的格式
                grouped_results = self.parent_window._group_results(sorted_results, self.parent_window.current_grouping_mode)
                self._process_grouped_results_for_display(grouped_results)
            else:
                # 不分组，直接处理
                self._process_results_for_display(sorted_results)
        else:
            self._process_results_for_display(results)
        
    def set_theme(self, theme_name):
        """设置主题"""
        self.current_theme = theme_name
        # 通知视图更新显示
        if self.display_items:
            self.dataChanged.emit(self.index(0), self.index(len(self.display_items) - 1))


class HtmlItemDelegate(QStyledItemDelegate):
    """HTML内容委托，用于在列表视图中渲染HTML"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def paint(self, painter, option, index):
        """绘制HTML内容"""
        try:
            html_content = index.data(Qt.DisplayRole)
            if not html_content:
                super().paint(painter, option, index)
                return
                
            # 创建QTextDocument来渲染HTML
            document = QTextDocument()
            document.setHtml(html_content)
            document.setTextWidth(option.rect.width())
            
            painter.save()
            painter.translate(option.rect.topLeft())
            
            # 如果项被选中，绘制选中背景
            if option.state & QStyle.State_Selected:
                painter.fillRect(QRect(0, 0, option.rect.width(), int(document.size().height())), 
                               option.palette.highlight())
            
            # 绘制HTML内容
            document.drawContents(painter)
            painter.restore()
            
        except Exception as e:
            print(f"Error painting HTML item: {e}")
            super().paint(painter, option, index)
    
    def sizeHint(self, option, index):
        """返回项的大小提示"""
        try:
            html_content = index.data(Qt.DisplayRole)
            if not html_content:
                return super().sizeHint(option, index)
                
            document = QTextDocument()
            document.setHtml(html_content)
            document.setTextWidth(option.rect.width() if option.rect.width() > 0 else 400)
            
            return QSize(int(document.idealWidth()), int(document.size().height()))
            
        except Exception as e:
            print(f"Error calculating size hint: {e}")
            return QSize(400, 100)  # 默认大小


class VirtualResultsView(QListView):
    """虚拟滚动结果视图"""
    
    # 信号定义
    linkClicked = Signal(QUrl)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置基本属性
        self.setAlternatingRowColors(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 启用鼠标跟踪以支持链接悬停
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)

        # 启用右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # 设置HTML委托
        self.html_delegate = HtmlItemDelegate(self)
        self.setItemDelegate(self.html_delegate)
        
        # 连接点击信号
        self.clicked.connect(self._handle_item_clicked)
        
    def _handle_item_clicked(self, index):
        """处理项点击，目前由mousePressEvent处理链接点击"""
        pass  # 链接点击由mousePressEvent处理
    
    def mousePressEvent(self, event):
        """处理鼠标点击事件，特别是链接点击"""
        if event.button() == Qt.LeftButton:
            index = self.indexAt(event.position().toPoint())
            if index.isValid():
                # 使用QTextDocument来精确检测链接点击
                html_content = index.data(Qt.DisplayRole)
                if html_content:
                    clicked_link = self._detect_link_at_position(event.position().toPoint(), index, html_content)
                    if clicked_link:
                        self.linkClicked.emit(QUrl(clicked_link))
                        return

        # 调用父类处理
        super().mousePressEvent(event)

    def _detect_link_at_position(self, global_pos, index, html_content):
        """使用QTextDocument精确检测点击位置的链接"""
        try:
            # QTextDocument, QTextCursor 已在文件顶部导入
            from PySide6.QtCore import QPointF

            # 创建临时的QTextDocument来处理HTML
            doc = QTextDocument()
            doc.setHtml(html_content)

            # 获取项目的矩形区域
            item_rect = self.visualRect(index)
            if not item_rect.isValid():
                print(f"无效的项目矩形，使用备选方案")
                return self._find_clicked_link_fallback(html_content)

            # 计算相对于项目的点击位置
            relative_pos = global_pos - item_rect.topLeft()
            print(f"点击位置: 全局{global_pos.x()},{global_pos.y()}, 相对{relative_pos.x()},{relative_pos.y()}")

            # 尝试多个hitTest策略
            hit_strategies = [
                (Qt.HitTestAccuracy.ExactHit, "精确命中"),
                (Qt.HitTestAccuracy.FuzzyHit, "模糊命中")
            ]

            for strategy, strategy_name in hit_strategies:
                hit_point = QPointF(relative_pos.x(), relative_pos.y())
                cursor_pos = doc.documentLayout().hitTest(hit_point, strategy)
                print(f"{strategy_name}测试: 光标位置 {cursor_pos}")

                if cursor_pos >= 0:
                    # 创建光标并检查格式
                    cursor = QTextCursor(doc)
                    cursor.setPosition(cursor_pos)

                    # 获取字符格式
                    char_format = cursor.charFormat()

                    # 检查是否是链接
                    if char_format.isAnchor():
                        anchor_href = char_format.anchorHref()
                        print(f"检测到链接点击({strategy_name}): {anchor_href}")
                        return anchor_href
                    else:
                        # 尝试扩展选择范围，查找附近的链接
                        for offset in [-1, 1, -2, 2]:
                            try_pos = cursor_pos + offset
                            if try_pos >= 0:
                                cursor.setPosition(try_pos)
                                char_format = cursor.charFormat()
                                if char_format.isAnchor():
                                    anchor_href = char_format.anchorHref()
                                    print(f"检测到附近链接({strategy_name}, 偏移{offset}): {anchor_href}")
                                    return anchor_href

            print(f"精确检测失败，使用备选方案")
            # 如果精确检测失败，使用备选方案
            return self._find_clicked_link_fallback(html_content)

        except Exception as e:
            print(f"链接检测出错，使用备选方案: {e}")
            return self._find_clicked_link_fallback(html_content)

    def _find_clicked_link_fallback(self, html_content):
        """备选的链接检测方案"""
        import re
        
        # 提取所有链接
        link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
        links = re.findall(link_pattern, html_content)
        if not links:
            return None

        # 使用简单的轮换策略或者随机选择，避免总是选择同一个
        import time
        openfile_links = [url for url, text in links if url.startswith('openfile:')]
        openfolder_links = [url for url, text in links if url.startswith('openfolder:')]
        toggle_links = [url for url, text in links if url.startswith('toggle::')]

        # 如果同时有文件和目录链接，使用时间戳来轮换选择
        if openfile_links and openfolder_links:
            # 使用毫秒数的奇偶性来决定选择哪个
            ms = int(time.time() * 1000) % 1000
            if ms % 2 == 0:
                print(f"备选检测：选择打开文件链接")
                return openfile_links[0]
            else:
                print(f"备选检测：选择打开目录链接")
                return openfolder_links[0]

        # 如果只有一种类型，直接返回
        if openfile_links:
            print(f"备选检测：只有打开文件链接")
            return openfile_links[0]
        if openfolder_links:
            print(f"备选检测：只有打开目录链接")
            return openfolder_links[0]
        if toggle_links:
            print(f"备选检测：只有折叠链接")
            return toggle_links[0]

        return links[0][0] if links else None



    def mouseDoubleClickEvent(self, event):
        """处理双击事件，显示文本选择对话框"""
        if event.button() == Qt.LeftButton:
            index = self.indexAt(event.position().toPoint())
            if index.isValid():
                # 获取HTML内容
                html_content = index.data(Qt.DisplayRole)
                if html_content:
                    self._show_text_selection_dialog(html_content)
                    return
        # 调用父类处理
        super().mouseDoubleClickEvent(event)

    def _show_text_selection_dialog(self, html_content):
        """显示文本选择对话框"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QMessageBox

        dialog = QDialog(self)
        dialog.setWindowTitle("文本选择")
        dialog.resize(800, 500)

        layout = QVBoxLayout(dialog)

        # 创建文本编辑器显示内容
        text_edit = QTextEdit()
        text_edit.setHtml(html_content)
        text_edit.setReadOnly(False)  # 允许选择
        layout.addWidget(text_edit)

        # 按钮布局
        button_layout = QHBoxLayout()

        # 复制全部按钮
        copy_all_btn = QPushButton("复制全部内容")
        copy_all_btn.clicked.connect(lambda: self._copy_all_text(text_edit, dialog))
        button_layout.addWidget(copy_all_btn)

        # 复制选中按钮
        copy_selected_btn = QPushButton("复制选中文本")
        copy_selected_btn.clicked.connect(lambda: self._copy_selected_text(text_edit, dialog))
        button_layout.addWidget(copy_selected_btn)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        dialog.exec()

    def _copy_all_text(self, text_edit, dialog):
        """复制全部文本内容"""
        plain_text = text_edit.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(plain_text)
        QMessageBox.information(dialog, "复制成功", f"已复制 {len(plain_text)} 个字符到剪贴板")

    def _copy_selected_text(self, text_edit, dialog):
        """复制选中的文本"""
        cursor = text_edit.textCursor()
        selected_text = cursor.selectedText()

        if selected_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(selected_text)
            QMessageBox.information(dialog, "复制成功", f"已复制 {len(selected_text)} 个字符到剪贴板")
        else:
            QMessageBox.warning(dialog, "未选择文本", "请先选择要复制的文本")

    def _show_context_menu(self, position):
        """显示虚拟滚动视图的右键菜单"""
        index = self.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)

        # 获取HTML内容
        html_content = index.data(Qt.DisplayRole)
        if html_content:
            # 复制内容选项
            copy_action = menu.addAction("复制内容")
            copy_action.triggered.connect(lambda: self._copy_item_content(html_content))

            menu.addSeparator()

            # 文本选择对话框选项
            select_action = menu.addAction("文本选择...")
            select_action.triggered.connect(lambda: self._show_text_selection_dialog(html_content))

            # 显示菜单
            menu.exec(self.mapToGlobal(position))

    def _copy_item_content(self, html_content):
        """复制项目的纯文本内容"""
        from PySide6.QtGui import QTextDocument

        # 将HTML转换为纯文本
        doc = QTextDocument()
        doc.setHtml(html_content)
        plain_text = doc.toPlainText()

        # 复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(plain_text)

        # 显示成功消息（可选）
        if hasattr(self, 'parent') and hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"已复制 {len(plain_text)} 个字符到剪贴板", 3000)







# --- 导入统一路径处理工具 ---
from path_utils import normalize_path_for_display, normalize_path_for_index, PathStandardizer

# --- 导入统一主题管理工具 ---
from theme_manager import ThemeManager
# ------------------------

import sys
import io # 新增导入

# 确保 stdout 和 stderr 在非控制台模式下是可写的
# 这应该在几乎所有其他导入之前完成，特别是在 logging 和 jieba 导入之前
if sys.stdout is None:
    sys.stdout = io.StringIO()  # 重定向到一个内存字符串缓冲区
if sys.stderr is None:
    sys.stderr = io.StringIO()  # 同样重定向到内存缓冲区，避免与您后续的文件重定向冲突

# Import necessary classes from PySide6
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextBrowser, QProgressBar,
    QFileDialog, QMessageBox, QDateEdit, QCheckBox, QComboBox, QRadioButton, QDialog, QDialogButtonBox, QSpinBox,
    QButtonGroup, QListWidget, QListWidgetItem, QAbstractItemView, QGroupBox, QMenuBar, QToolBar, # ADDED QListWidget, QListWidgetItem, QAbstractItemView, QGroupBox, QMenuBar, QToolBar
    QStatusBar, # Ensure QProgressBar is imported if not already
    QTableWidget, QHeaderView, QTableWidgetItem,
    QTreeView, QSplitter, # 添加文件夹树视图所需的组件
    QSizePolicy, QFrame,
    QInputDialog,
    QTabWidget, QScrollArea, QTabBar, QTabWidget,
    QGridLayout, QMenu, # 添加QMenu用于右键菜单
    QListView, QStyledItemDelegate, QStackedWidget, QStyle, # 虚拟滚动所需组件
)
from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot, QUrl, QSettings, QDate, QTimer, QSize, QDir, QModelIndex, QRect, QAbstractListModel # Added QSize, QDir, QModelIndex, QRect, QAbstractListModel 
from PySide6.QtGui import QDesktopServices, QAction, QIntValidator, QShortcut, QKeySequence, QIcon, QColor, QStandardItemModel, QStandardItem, QTextDocument, QTextCursor, QPainter, QCursor # Added QStandardItemModel and QStandardItem, QTextDocument, QPainter, QCursor
import html  # Import html module for escaping

# --- ADDED: Network and Version Comparison Imports ---
import requests
from packaging import version
# -----------------------------------------------------

# Standard library imports
from pathlib import Path  # Added
import document_search  # Uncommented backend import
import traceback  # Keep for worker error reporting
import json  # Needed for structure map parsing
import functools # ADDED for LRU cache
import os  # Added for os.path.normpath
import time # Added for sleep
import datetime
import logging # Import logging module
import re
import subprocess
import shutil
import math
import codecs
import webbrowser
import requests.adapters  # 添加requests的适配器和重试策略导入
import urllib3.util  # 替换过时的requests.packages导入

# --- ADDED: 导入许可证管理器和对话框 ---
from license_manager import get_license_manager, Features, LicenseStatus
from license_dialog import LicenseDialog
# --------------------------------------

# --- ADDED: Try importing qdarkstyle --- 
_qdarkstyle_available = False
try:
    import qdarkstyle
    _qdarkstyle_available = True
except ImportError:
    pass # qdarkstyle not installed, will use basic dark theme
# -------------------------------------

# --- 添加资源文件路径解析器 ---
def get_resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和打包后的环境
    
    Args:
        relative_path (str): 相对于应用程序根目录的资源文件路径
        
    Returns:
        str: 资源文件的绝对路径
    """
    # 如果路径带有特殊前缀，则移除
    if relative_path.startswith('qss-resource:'):
        relative_path = relative_path[len('qss-resource:'):]
    
    # 如果路径被引号包围，则移除引号
    if (relative_path.startswith('"') and relative_path.endswith('"')) or \
       (relative_path.startswith("'") and relative_path.endswith("'")):
        relative_path = relative_path[1:-1]
    
    # 判断是否在PyInstaller环境中运行
    if getattr(sys, 'frozen', False):
        # 在PyInstaller环境中
        base_path = sys._MEIPASS
    else:
        # 在开发环境中
        base_path = os.path.dirname(__file__)
    
    # 组合路径并返回
    resource_path = os.path.join(base_path, relative_path)
    print(f"资源路径解析: {relative_path} -> {resource_path}")
    return resource_path
# ------------------------------

# ====================
# UI设计常量体系
# ====================

# 字体大小常量
UI_FONT_SIZES = {
    'normal': '12px',        # 标准文本
    'small': '11px',         # 小号文本
    'large': '14px',         # 大号文本
    'icon': '14px',          # 图标
    'extra_small': '10px',   # 额外小号文本
    'file_header': '16px',   # 文件标题
    'section_header': '13px', # 章节标题
    'table_cell': '11px',    # 表格单元格
    'file_info': '10px'      # 文件信息
}

# 间距和尺寸常量
UI_SPACING = {
    'small': '6px',
    'normal': '8px',
    'large': '12px',
    'extra_large': '16px'
}

# 圆角常量
UI_BORDER_RADIUS = {
    'small': '4px',
    'normal': '6px',
    'large': '8px'
}

# 颜色透明度
UI_ALPHA = {
    'light': '0.05',
    'medium': '0.1',
    'strong': '0.2'
}

# --- Constants ---
ORGANIZATION_NAME = "YourOrganizationName"  # Replace with your actual org name or identifier
APPLICATION_NAME = "DocumentSearchToolPySide"
CONFIG_FILE = 'search_config.ini'  # Keep for reference, but QSettings handles location
DEFAULT_DOC_DIR = ""

# --- Settings Keys --- (Define keys for QSettings)
SETTINGS_LAST_SEARCH_DIR = "history/lastSearchDirectory"
SETTINGS_WINDOW_GEOMETRY = "window/geometry"
SETTINGS_INDEX_DIRECTORY = "indexing/indexDirectory" # New key for index path
SETTINGS_SOURCE_DIRECTORIES = "indexing/sourceDirectories"
SETTINGS_ENABLE_OCR = "indexing/enableOcr"
SETTINGS_EXTRACTION_TIMEOUT = "indexing/extractionTimeout"
SETTINGS_TXT_CONTENT_LIMIT = "indexing/txtContentLimitKb"
SETTINGS_CASE_SENSITIVE = "search/caseSensitive"

# --- ADDED: Version Info ---
CURRENT_VERSION = "1.0.0"  # <--- Update this for each new release!
UPDATE_INFO_URL = "https://azariasy.github.io/-wen-zhi-sou-website/latest_version.json" # URL to your version info file
# -------------------------

# === 虚拟滚动相关类实现 ===
class VirtualResultsModel(QAbstractListModel):
    """虚拟滚动结果模型，完全兼容传统模式的文件分组和章节折叠功能"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results = []
        self.display_items = []  # 存储显示项目列表（文件组/章节组/内容项）
        self.current_theme = "现代蓝"
        self.parent_window = parent  # 存储父窗口引用以访问collapse_states
        
    def rowCount(self, parent=QModelIndex()):
        """返回显示项目总数"""
        return len(self.display_items)
        
    def data(self, index, role=Qt.DisplayRole):
        """返回指定索引的数据"""
        if not index.isValid() or index.row() >= len(self.display_items):
            return None
            
        if role == Qt.DisplayRole:
            item = self.display_items[index.row()]
            return self._generate_item_html(item, index.row())
        elif role == Qt.UserRole:
            # 返回原始项目数据
            return self.display_items[index.row()]
        
        return None
    
    def _process_results_for_display(self, results):
        """将原始搜索结果处理成显示项目列表，完全兼容传统模式逻辑"""
        self.beginResetModel()
        self.display_items = []
        
        if not results:
            # 添加一个友好的空状态显示项
            self.display_items.append({
                'type': 'empty_state',
                'content': '🔍 未找到匹配的搜索结果'
            })
            self.endResetModel()
            return
            
        try:
            # 检查搜索范围
            if hasattr(self.parent_window, 'last_search_scope') and self.parent_window.last_search_scope == 'filename':
                # 文件名搜索 - 简化显示
                self._process_filename_results(results)
            else:
                # 全文搜索 - 复杂分组显示
                self._process_fulltext_results(results)
                
        except Exception as e:
            print(f"Error processing results for virtual display: {e}")
            # 添加错误显示项
            self.display_items.append({
                'type': 'error',
                'content': f'处理搜索结果时出错: {e}'
            })
        
        self.endResetModel()
    
    def _process_grouped_results_for_display(self, grouped_results):
        """处理分组结果为虚拟滚动显示项目"""
        self.beginResetModel()
        self.display_items = []
        
        if not grouped_results:
            # 添加一个友好的空状态显示项
            self.display_items.append({
                'type': 'empty_state',
                'content': '🔍 未找到匹配的搜索结果'
            })
            self.endResetModel()
            return
        
        # 初始化分组折叠状态（如果不存在）
        if not hasattr(self.parent_window, 'group_collapse_states'):
            self.parent_window.group_collapse_states = {}
        
        # 处理分组结果
        for group_name, group_results in grouped_results.items():
            if not group_results:
                continue
                
            # 检查分组的折叠状态
            group_key = f"vgroup::{group_name}"
            is_collapsed = self.parent_window.group_collapse_states.get(group_key, False)
            
            # 添加分组标题（带折叠功能）
            self.display_items.append({
                'type': 'group_header',
                'group_name': group_name,
                'group_key': group_key,
                'result_count': len(group_results),
                'is_collapsed': is_collapsed
            })
            
            # 只有在未折叠时才显示分组中的结果
            if not is_collapsed:
                if self._is_filename_search():
                    # 文件名搜索：简化显示
                    for result in group_results:
                        self.display_items.append({
                            'type': 'filename_result',
                            'result': result
                        })
                else:
                    # 全文搜索：完整显示
                    self._process_fulltext_group_results(group_results)
        
        self.endResetModel()
    
    def _process_fulltext_group_results(self, results):
        """处理全文搜索的分组结果"""
        # 使用传统模式的逻辑进行文件和章节分组
        file_groups = {}
        
        for result in results:
            file_path = result.get('file_path', '')
            
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(result)
        
        # 为每个文件组生成显示项
        for file_path, file_results in file_groups.items():
            if not file_results:
                continue
                
            file_key = f"f::{file_path}"
            is_collapsed = self._get_collapse_state(file_key)
            
            # 添加文件组头部
            self.display_items.append({
                'type': 'file_group',
                'file_path': file_path,
                'file_key': file_key,
                'file_number': len(file_groups),
                'is_collapsed': is_collapsed
            })
            
            if not is_collapsed:
                # 文件未折叠，继续处理章节
                chapter_groups = {}
                
                for result in file_results:
                    # 确定章节键
                    heading = result.get('heading')
                    chapter_key = f"c::{file_path}::{heading if heading else '(无章节)'}"
                    
                    if chapter_key not in chapter_groups:
                        chapter_groups[chapter_key] = []
                    chapter_groups[chapter_key].append(result)
                
                # 为每个章节组生成显示项
                for chapter_key, chapter_results in chapter_groups.items():
                    if not chapter_results:
                        continue
                        
                    is_chapter_collapsed = self._get_collapse_state(chapter_key)
                    heading = chapter_results[0].get('heading', '(无章节)')
                    
                    # 添加章节组头部
                    self.display_items.append({
                        'type': 'chapter_group',
                        'chapter_key': chapter_key,
                        'heading': heading,
                        'is_collapsed': is_chapter_collapsed,
                        'result': chapter_results[0]  # 用于标题标记
                    })
                    
                    if not is_chapter_collapsed:
                        # 章节未折叠，添加内容
                        for result in chapter_results:
                            self.display_items.append({
                                'type': 'content',
                                'result': result
                            })
    
    def _is_filename_search(self):
        """检查是否为文件名搜索"""
        return (hasattr(self.parent_window, 'last_search_scope') and 
                self.parent_window.last_search_scope == 'filename')
    
    def _get_collapse_state(self, key):
        """获取折叠状态"""
        if self.parent_window and hasattr(self.parent_window, 'collapse_states'):
            return self.parent_window.collapse_states.get(key, False)
        return False
    
    def _process_filename_results(self, results):
        """处理文件名搜索结果"""
        processed_paths = set()
        
        # 添加美观的标题项
        self.display_items.append({
            'type': 'title',
            'content': f'📄 文件名搜索结果 ({len(results)} 个文件)'
        })
        
        for result in results:
            file_path = result.get('file_path', '(未知文件)')
            if file_path in processed_paths:
                continue
            processed_paths.add(file_path)
            
            self.display_items.append({
                'type': 'filename_result',
                'file_path': file_path,
                'result': result
            })
    
    def _process_fulltext_results(self, results):
        """处理全文搜索结果 - 完全兼容传统模式的文件分组和章节折叠"""
        last_file_path = None
        last_displayed_heading = None
        file_group_counter = 0
        
        for i, result in enumerate(results):
            file_path = result.get('file_path', '(未知文件)')
            original_heading = result.get('heading', '(无章节标题)')
            
            is_new_file = (file_path != last_file_path)
            is_new_heading = (original_heading != last_displayed_heading)
            
            # 处理新文件
            if is_new_file:
                file_group_counter += 1
                file_key = f"f::{file_path}"
                
                # 创建文件组项
                file_item = {
                    'type': 'file_group',
                    'file_path': file_path,
                    'file_key': file_key,
                    'file_number': file_group_counter,
                    'is_collapsed': self.parent_window.collapse_states.get(file_key, False) if self.parent_window else False,
                    'result': result
                }
                self.display_items.append(file_item)
                
                last_displayed_heading = None
                last_file_path = file_path
            
            # 处理章节（如果文件未折叠）
            file_key = f"f::{file_path}"
            is_file_collapsed = self.parent_window.collapse_states.get(file_key, False) if self.parent_window else False
            
            if not is_file_collapsed and (is_new_file or is_new_heading):
                # 检查是否是Excel数据
                if result.get('excel_sheet') is None:
                    # 修复：统一章节键格式，去除索引以确保同一章节的一致性
                    chapter_key = f"c::{file_path}::{original_heading if original_heading else '(无章节)'}"
                    is_chapter_collapsed = self.parent_window.collapse_states.get(chapter_key, False) if self.parent_window else False
                    
                    chapter_item = {
                        'type': 'chapter_group',
                        'file_path': file_path,
                        'chapter_key': chapter_key,
                        'heading': original_heading,
                        'is_collapsed': is_chapter_collapsed,
                        'result': result
                    }
                    self.display_items.append(chapter_item)
                    last_displayed_heading = original_heading
                else:
                    last_displayed_heading = None
            
            # 处理内容（段落或Excel数据）
            if not is_file_collapsed:
                # 修复：统一章节键格式，去除索引以确保同一章节的一致性
                chapter_key = f"c::{file_path}::{original_heading if original_heading else '(无章节)'}"
                is_chapter_collapsed = self.parent_window.collapse_states.get(chapter_key, False) if self.parent_window else False
                
                # 修复BUG：无论是否是Excel数据，只要章节被折叠就不显示内容
                if not is_chapter_collapsed:
                    content_item = {
                        'type': 'content',
                        'file_path': file_path,
                        'result': result,
                        'index': i
                    }
                    self.display_items.append(content_item)
    
    def _generate_item_html(self, item, index):
        """生成显示项的HTML内容"""
        try:
            item_type = item.get('type', 'unknown')
            
            if item_type == 'title':
                theme_colors = self._get_theme_colors()
                return f'''
                <div style="margin: 15px 5px 20px 5px; padding: 15px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 8px; border-left: 4px solid {theme_colors["primary"]};">
                    <h3 style="margin: 0; color: {theme_colors["primary"]}; font-size: 16px; font-weight: bold;">
                        {item["content"]}
                    </h3>
                </div>
                '''
                
            elif item_type == 'filename_result':
                return self._generate_filename_result_html(item)
                
            elif item_type == 'file_group':
                return self._generate_file_group_html(item)
                
            elif item_type == 'chapter_group':
                return self._generate_chapter_group_html(item)
                
            elif item_type == 'content':
                return self._generate_content_html(item)
                
            elif item_type == 'error':
                return f'<div style="margin: 10px; padding: 10px; background: #ffebee; border: 1px solid #f44336; border-radius: 4px; color: #c62828;">{item["content"]}</div>'
                
            elif item_type == 'group_header':
                theme_colors = self._get_theme_colors()
                group_name = item.get('group_name', '未知分组')
                group_key = item.get('group_key', 'unknown')
                result_count = item.get('result_count', 0)
                is_collapsed = item.get('is_collapsed', False)
                
                import html
                toggle_char = "▶" if is_collapsed else "▼"
                toggle_href = f'toggle::{html.escape(group_key, quote=True)}'
                escaped_group_name = html.escape(str(group_name))
                
                return f'''
                <div style="margin: 15px 10px 10px 10px; padding: 12px 16px; background: linear-gradient(135deg, {theme_colors["link_color"]}22, {theme_colors["link_color"]}11); border-left: 4px solid {theme_colors["link_color"]}; border-radius: 6px;">
                    <div style="font-size: 16px; font-weight: bold; color: {theme_colors["text_color"]}; margin-bottom: 4px;">
                            <a href="{toggle_href}" style="color: {theme_colors["link_color"]}; text-decoration:none; font-weight:bold; margin-right: 8px;">{toggle_char}</a>
                        📂 {escaped_group_name}
                    </div>
                    <div style="font-size: 13px; color: #666; font-style: italic;">
                        {result_count} 个结果
                    </div>
                </div>
                '''
                
            elif item_type == 'empty_state':
                theme_colors = self._get_theme_colors()
                return f'''
                <div style="margin: 50px 20px; padding: 40px; text-align: center; background: #f8f9fa; border-radius: 8px; border: 2px dashed #dee2e6;">
                    <div style="font-size: 48px; margin-bottom: 20px; color: #6c757d;">{item["content"].split()[0]}</div>
                    <div style="font-size: 18px; color: {theme_colors["text_color"]}; margin-bottom: 10px;">
                        {" ".join(item["content"].split()[1:])}
                    </div>
                    <div style="font-size: 14px; color: #6c757d; margin-top: 20px;">
                        请尝试调整搜索词或筛选条件
                    </div>
                </div>
                '''
                
            else:
                return f'<div style="margin: 10px; padding: 10px;">未知项目类型: {item_type}</div>'
                
        except Exception as e:
            print(f"Error generating item HTML: {e}")
            return f'<div style="margin: 10px; padding: 10px; background: #ffebee;">生成HTML时出错: {str(e)}</div>'
    
    def _get_theme_colors(self):
        """获取当前主题的颜色配置 - 扩展版本包含更多语义颜色"""
        if self.current_theme == "现代蓝":
            return {
                "highlight_bg": "#E3F2FD",
                "highlight_text": "#1565C0", 
                "link_color": "#2196F3",
                "text_color": "#333333",
                "primary": "#007ACC",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#F59E0B",
                "danger": "#EF4444"
            }
        elif self.current_theme == "现代紫":
            return {
                "highlight_bg": "#F3E5F5",
                "highlight_text": "#7B1FA2",
                "link_color": "#9C27B0", 
                "text_color": "#333333",
                "primary": "#8B5CF6",
                "success": "#10B981",
                "info": "#8B5CF6",
                "warning": "#F59E0B",
                "danger": "#EF4444"
            }
        elif self.current_theme == "现代红":
            return {
                "highlight_bg": "#FFE0E0",
                "highlight_text": "#C62828",
                "link_color": "#E53935",
                "text_color": "#333333",
                "primary": "#DC2626",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#F59E0B",
                "danger": "#DC2626"
            }
        elif self.current_theme == "现代橙":
            return {
                "highlight_bg": "#FFF3E0",
                "highlight_text": "#FF6F00",
                "link_color": "#FF9800",
                "text_color": "#333333",
                "primary": "#EA580C",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#EA580C",
                "danger": "#EF4444"
            }
        elif self.current_theme == "深色模式":
            return {
                "highlight_bg": "#374151",
                "highlight_text": "#60A5FA",
                "link_color": "#3B82F6",
                "text_color": "#F9FAFB",
                "primary": "#3B82F6",
                "success": "#059669",
                "info": "#3B82F6",
                "warning": "#D97706",
                "danger": "#DC2626"
            }
        elif self.current_theme == "护眼绿":
            return {
                "highlight_bg": "#DCFCE7",
                "highlight_text": "#047857",
                "link_color": "#059669",
                "text_color": "#1E1E1E",
                "primary": "#059669",
                "success": "#059669",
                "info": "#0891B2",
                "warning": "#D97706",
                "danger": "#DC2626"
            }
        else:
            return {
                "highlight_bg": "#FFECB3",
                "highlight_text": "#FF6F00",
                "link_color": "#FF9800",
                "text_color": "#333333",
                "primary": "#FF9800",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#F59E0B",
                "danger": "#EF4444"
            }
    
    def _generate_filename_result_html(self, item):
        """生成文件名搜索结果的HTML - 美观现代化样式"""
        file_path = item['file_path']
        result = item.get('result', {})
        theme_colors = self._get_theme_colors()
        
        # 计算文件信息
        import os
        from pathlib import Path
        try:
            file_name = os.path.basename(file_path)
            file_size = result.get('file_size', result.get('size', 0))
            mtime = result.get('last_modified', result.get('mtime', 0))

            # 格式化文件大小
            if file_size > 0:
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
            else:
                size_str = '未知大小'

            # 格式化修改时间
            if mtime > 0:
                import datetime
                mtime_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            else:
                mtime_str = '未知时间'

            # 获取文件类型图标
            file_ext = Path(file_path).suffix.lower()
            type_icon = "📄"
            if file_ext in ['.docx', '.doc']:
                type_icon = "📝"
            elif file_ext in ['.xlsx', '.xls']:
                type_icon = "📊"
            elif file_ext in ['.pptx', '.ppt']:
                type_icon = "📋"
            elif file_ext in ['.pdf']:
                type_icon = "📕"
            elif file_ext in ['.txt', '.md']:
                type_icon = "📄"
            elif file_ext in ['.jpg', '.png', '.gif', '.bmp']:
                type_icon = "🖼️"
            elif file_ext in ['.mp4', '.avi', '.mov']:
                type_icon = "🎬"
            elif file_ext in ['.mp3', '.wav', '.flac']:
                type_icon = "🎵"

        except Exception as e:
            file_name = file_path
            size_str = '未知大小'
            mtime_str = '未知时间'
            type_icon = "📄"
        
        # 计算文件夹路径
        folder_path_str = ""
        is_archive_member = "::" in file_path
        try:
            if is_archive_member:
                archive_file_path = file_path.split("::", 1)[0]
                folder_path_str = str(Path(archive_file_path).parent)
            else:
                path_obj = Path(file_path)
                if path_obj.is_file():
                    folder_path_str = str(path_obj.parent)
        except Exception:
            pass
        
        import html
        escaped_file_name = html.escape(file_name)
        escaped_file_path = html.escape(file_path)
        
        # 构建操作链接 - 使用现代化按钮样式
        links = [f'<a href="openfile:{html.escape(file_path, quote=True)}" style="color: #fff; text-decoration: none; padding: 6px 12px; background: {theme_colors["success"]}; border-radius: 4px; font-size: 12px; margin-right: 8px;">🔍 打开文件</a>']
        if folder_path_str:
            links.append(f'<a href="openfolder:{html.escape(folder_path_str, quote=True)}" style="color: #fff; text-decoration: none; padding: 6px 12px; background: {theme_colors["info"]}; border-radius: 4px; font-size: 12px;">📁 打开目录</a>')
        
        return f'''
        <div style="margin: 6px 5px; padding: 10px; background: #fff; border: 1px solid #e9ecef; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 18px; margin-right: 8px;">{type_icon}</span>
                    <span style="color: {theme_colors["text_color"]}; font-size: 13px; font-weight: bold;">{escaped_file_name}</span>
                </div>
                <div style="white-space: nowrap;">
                    {" ".join(links)}
                </div>
            </div>

            <div style="margin-left: 26px;">
                <p style="margin: 0 0 5px 0; color: #6c757d; font-size: 10px; font-family: monospace; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    {escaped_file_path}
                </p>
                <div style="padding: 5px 8px; background: #f8f9fa; border-radius: 3px;">
                    <span style="font-size: 11px; color: #6c757d;">📏 {size_str}</span>
                    <span style="margin-left: 20px; font-size: 11px; color: #6c757d;">🕒 {mtime_str}</span>
                </div>
            </div>
        </div>
        '''
    
    def _generate_file_group_html(self, item):
        """生成文件组头部的HTML"""
        file_path = item['file_path']
        file_key = item['file_key']
        file_number = item['file_number']
        is_collapsed = item['is_collapsed']
        theme_colors = self._get_theme_colors()
        
        import html
        
        toggle_char = "[+]" if is_collapsed else "[-]"
        toggle_href = f'toggle::{html.escape(file_key, quote=True)}'
        escaped_path = html.escape(file_path)
        
        # 计算文件夹路径
        folder_path_str = ""
        is_archive_member = "::" in file_path
        try:
            if is_archive_member:
                archive_file_path = file_path.split("::", 1)[0]
                from pathlib import Path
                folder_path_str = str(Path(archive_file_path).parent)
            else:
                from pathlib import Path
                path_obj = Path(file_path)
                if path_obj.is_file():
                    folder_path_str = str(path_obj.parent)
        except Exception:
            pass
        
        # 构建现代化操作按钮 - 与文件名搜索保持一致
        links = [f'<a href="openfile:{html.escape(file_path, quote=True)}" style="color: #fff; text-decoration: none; padding: 6px 12px; background: {theme_colors["success"]}; border-radius: 4px; font-size: 12px; margin-right: 8px;">🔍 打开文件</a>']
        if folder_path_str:
            links.append(f'<a href="openfolder:{html.escape(folder_path_str, quote=True)}" style="color: #fff; text-decoration: none; padding: 6px 12px; background: {theme_colors["info"]}; border-radius: 4px; font-size: 12px;">📁 打开目录</a>')

        # 提取文件名和路径，类似文件名搜索的处理方式
        import os
        file_name = os.path.basename(file_path)
        file_directory = os.path.dirname(file_path)
        escaped_file_name = html.escape(file_name)
        escaped_directory = html.escape(file_directory)

        # 获取文件类型图标
        from pathlib import Path
        file_ext = Path(file_path).suffix.lower()
        type_icon = "📄"
        if file_ext in ['.docx', '.doc']:
            type_icon = "📝"
        elif file_ext in ['.xlsx', '.xls']:
            type_icon = "📊"
        elif file_ext in ['.pptx', '.ppt']:
            type_icon = "📋"
        elif file_ext in ['.pdf']:
            type_icon = "📕"
        elif file_ext in ['.txt', '.md']:
            type_icon = "📄"
        elif file_ext in ['.jpg', '.png', '.gif', '.bmp']:
            type_icon = "🖼️"
        elif file_ext in ['.mp4', '.avi', '.mov']:
            type_icon = "🎬"
        elif file_ext in ['.mp3', '.wav', '.flac']:
            type_icon = "🎵"
        
        return f'''
        <div style="margin: 15px 5px 5px 5px; padding: 12px; background: #f8f9fa; border-radius: 6px; border: 1px solid #e9ecef;">
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="vertical-align: middle;">
                                                <h3 style="margin: 0; color: {theme_colors["text_color"]}; font-size: 14px; font-weight: bold; display: inline-block;">
                            <a href="{toggle_href}" style="color: {theme_colors["link_color"]}; text-decoration:none; font-weight:bold; margin-right: 8px; font-size: 14px;">{toggle_char}</a>
                            <span style="font-size: 16px; margin-right: 8px;">{type_icon}</span>
                {file_number}. {escaped_path}
                        </h3>
                        <div style="margin-left: 38px;">
                            <p style="margin: 0; color: #6c757d; font-size: 11px; font-family: monospace;">
                            📁 {escaped_directory}
                        </p>
            </div>
                    </td>
                    <td style="text-align: right; vertical-align: top; white-space: nowrap; padding-top: 8px;">
                        {" ".join(links)}
                    </td>
                </tr>
            </table>
        </div>
        '''
    
    def _generate_chapter_group_html(self, item):
        """生成章节组头部的HTML"""
        chapter_key = item['chapter_key']
        heading = item['heading']
        is_collapsed = item['is_collapsed']
        result = item['result']
        theme_colors = self._get_theme_colors()
        
        import html
        
        toggle_char = "[+]" if is_collapsed else "[-]"
        toggle_href = f'toggle::{html.escape(chapter_key, quote=True)}'
        
        # 处理标记的标题
        marked_heading = result.get('marked_heading')
        heading_to_display = marked_heading if marked_heading is not None else heading
        if heading_to_display is None:
            heading_to_display = '(无章节标题)'
        escaped_heading = html.escape(str(heading_to_display))
        
        # 处理高亮
        if marked_heading and "__HIGHLIGHT_START__" in escaped_heading:
            escaped_heading = escaped_heading.replace(
                html.escape("__HIGHLIGHT_START__"), 
                f'<span style="background-color: {theme_colors["highlight_bg"]}; color: {theme_colors["highlight_text"]};">'
            )
            escaped_heading = escaped_heading.replace(html.escape("__HIGHLIGHT_END__"), '</span>')
        
        return f'''
        <div style="margin: 8px 15px 5px 25px; padding: 6px;">
            <p style="margin: 0; color: {theme_colors["text_color"]};">
                <a href="{toggle_href}" style="color: {theme_colors["link_color"]}; text-decoration:none; font-weight:bold; margin-right: 6px;">{toggle_char}</a>
                <b>章节:</b> {escaped_heading}
            </p>
        </div>
        '''
    
    def _generate_content_html(self, item):
        """生成内容的HTML（段落或Excel表格）"""
        result = item['result']
        theme_colors = self._get_theme_colors()
        
        # 检查是否是Excel数据
        excel_headers = result.get('excel_headers')
        excel_values = result.get('excel_values')
        
        if excel_headers is not None and excel_values is not None:
            return self._generate_excel_content_html(result, theme_colors)
        else:
            return self._generate_paragraph_content_html(result, theme_colors)
    
    def _generate_excel_content_html(self, result, theme_colors):
        """生成Excel内容的HTML - 现代化样式"""
        excel_headers = result.get('excel_headers', [])
        excel_values = result.get('excel_values', [])
        excel_sheet = result.get('excel_sheet', '')
        excel_row_idx = result.get('excel_row_idx', 0)
        
        import html
        
        html_parts = []
        html_parts.append(f'''
        <div style="margin: {UI_SPACING['normal']} {UI_SPACING['extra_large']}; padding: {UI_SPACING['large']};
                    background: linear-gradient(145deg, #ffffff, #f8f9fa);
                    border: 1px solid #e3e7ea; border-radius: {UI_BORDER_RADIUS['normal']};
                    box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
            <div style="margin-bottom: {UI_SPACING['normal']}; padding: {UI_SPACING['small']};
                        background: {theme_colors["primary"]}15; border-radius: {UI_BORDER_RADIUS['small']};
                        border-left: 4px solid {theme_colors["primary"]};">
                <h4 style="margin: 0; font-size: {UI_FONT_SIZES['section_header']}; color: {theme_colors["text_color"]};">
                    📊 表格: {html.escape(str(excel_sheet) if excel_sheet is not None else "未知表格")} | 行: {excel_row_idx}
                </h4>
            </div>
        ''')

        # 生成现代化表格
        html_parts.append(f'''
            <table style="width: 100%; border-collapse: collapse; background: white;
                         border-radius: {UI_BORDER_RADIUS['small']}; overflow: hidden;
                         box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        ''')

        # 表头
        html_parts.append(f"<tr style='background: linear-gradient(135deg, {theme_colors['primary']}20, {theme_colors['primary']}15);'>")
        for header in excel_headers:
            header_text = str(header) if header is not None else ''
            html_parts.append(f'''
                <th style="padding: {UI_SPACING['normal']}; border: none;
                          font-size: {UI_FONT_SIZES['table_cell']}; font-weight: 600;
                          color: {theme_colors["text_color"]}; text-align: left;">
                    {html.escape(header_text)}
                </th>
            ''')
        html_parts.append("</tr>")
        
        # 数据行
        html_parts.append("<tr style='background: white;'>")
        escaped_start_marker = html.escape("__HIGHLIGHT_START__")
        escaped_end_marker = html.escape("__HIGHLIGHT_END__")
        
        for value in excel_values:
            value_text = str(value) if value is not None else ''
            escaped_value = html.escape(value_text)
            
            # 处理高亮
            if escaped_start_marker in escaped_value:
                highlighted_value = escaped_value.replace(
                    escaped_start_marker,
                    f'<mark style="background: linear-gradient(120deg, {theme_colors["highlight_bg"]}60, {theme_colors["highlight_bg"]}); color: {theme_colors["highlight_text"]}; border-radius: 3px; padding: 2px 4px;">'
                ).replace(escaped_end_marker, '</mark>')
            else:
                highlighted_value = escaped_value
                
            html_parts.append(f'''
                <td style="padding: {UI_SPACING['normal']}; border: none;
                          font-size: {UI_FONT_SIZES['table_cell']}; color: {theme_colors["text_color"]};
                          border-bottom: 1px solid #f0f0f0;">
                    {highlighted_value}
                </td>
            ''')
        html_parts.append("</tr>")
        html_parts.append("</table>")
        html_parts.append('</div>')
        
        return "".join(html_parts)
    
    def _generate_paragraph_content_html(self, result, theme_colors):
        """生成段落内容的HTML - 现代化样式"""
        original_paragraph = result.get('paragraph')
        marked_paragraph = result.get('marked_paragraph')
        match_start = result.get('match_start')
        match_end = result.get('match_end')
        
        if original_paragraph is None:
            return ''
        
        # 确定要显示的段落文本
        paragraph_text_for_highlight = marked_paragraph if marked_paragraph is not None else original_paragraph
        if paragraph_text_for_highlight is None:
            paragraph_text_for_highlight = str(original_paragraph) if original_paragraph is not None else ''
        else:
            paragraph_text_for_highlight = str(paragraph_text_for_highlight)
        
        import html
        escaped_paragraph = html.escape(paragraph_text_for_highlight)
        
        # 处理高亮
        highlighted_paragraph_display = escaped_paragraph
        
        # 短语搜索的精确高亮
        if match_start is not None and match_end is not None:
            if 0 <= match_start < match_end <= len(escaped_paragraph):
                pre = escaped_paragraph[:match_start]
                mat = escaped_paragraph[match_start:match_end]
                post = escaped_paragraph[match_end:]
                highlighted_paragraph_display = f'{pre}<mark style="background: linear-gradient(120deg, {theme_colors["highlight_bg"]}60, {theme_colors["highlight_bg"]}); color: {theme_colors["highlight_text"]}; border-radius: 3px; padding: 2px 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">{mat}</mark>{post}'
        # 模糊搜索的标记高亮
        elif marked_paragraph:
            escaped_start_marker = html.escape("__HIGHLIGHT_START__")
            escaped_end_marker = html.escape("__HIGHLIGHT_END__")
            if escaped_start_marker in escaped_paragraph:
                highlighted_paragraph_display = escaped_paragraph.replace(
                    escaped_start_marker,
                    f'<mark style="background: linear-gradient(120deg, {theme_colors["highlight_bg"]}60, {theme_colors["highlight_bg"]}); color: {theme_colors["highlight_text"]}; border-radius: 3px; padding: 2px 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">'
                ).replace(escaped_end_marker, '</mark>')
        
        return f'''
        <div style="margin: {UI_SPACING['normal']} {UI_SPACING['extra_large']}; padding: {UI_SPACING['large']};
                    background: linear-gradient(145deg, #ffffff, #fafbfc);
                    border: 1px solid #e8ecef; border-radius: {UI_BORDER_RADIUS['normal']};
                    border-left: 4px solid {theme_colors["success"]};
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="margin-bottom: {UI_SPACING['small']};">
                <span style="font-size: {UI_FONT_SIZES['small']}; color: {theme_colors["success"]}; font-weight: 600;">
                    📄 段落内容
                </span>
            </div>
            <div style="font-size: {UI_FONT_SIZES['normal']}; line-height: 1.6; color: {theme_colors["text_color"]};
                        word-wrap: break-word; overflow-wrap: break-word;">
                {highlighted_paragraph_display}
            </div>
        </div>
        '''

    def set_results(self, results):
        """设置搜索结果并处理成显示项目 - 支持完整的查看方式"""
        self.results = results
        
        # 从父窗口获取查看方式设置并应用完整的处理流程
        if self.parent_window:
            # 使用默认相关性排序（搜索引擎返回顺序）
            sorted_results = results
            
            # 检查是否需要分组显示
            if (hasattr(self.parent_window, 'grouping_enabled') and 
                self.parent_window.grouping_enabled and 
                hasattr(self.parent_window, 'current_grouping_mode') and 
                self.parent_window.current_grouping_mode != 'none'):
                
                # 应用分组，然后转换为虚拟滚动可以处理的格式
                grouped_results = self.parent_window._group_results(sorted_results, self.parent_window.current_grouping_mode)
                self._process_grouped_results_for_display(grouped_results)
            else:
                # 不分组，直接处理
                self._process_results_for_display(sorted_results)
        else:
            self._process_results_for_display(results)
        
    def set_theme(self, theme_name):
        """设置主题"""
        self.current_theme = theme_name
        # 通知视图更新显示
        if self.display_items:
            self.dataChanged.emit(self.index(0), self.index(len(self.display_items) - 1))


class HtmlItemDelegate(QStyledItemDelegate):
    """HTML内容委托，用于在列表视图中渲染HTML"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def paint(self, painter, option, index):
        """绘制HTML内容"""
        try:
            html_content = index.data(Qt.DisplayRole)
            if not html_content:
                super().paint(painter, option, index)
                return
                
            # 创建QTextDocument来渲染HTML
            document = QTextDocument()
            document.setHtml(html_content)
            document.setTextWidth(option.rect.width())
            
            painter.save()
            painter.translate(option.rect.topLeft())
            
            # 如果项被选中，绘制选中背景
            if option.state & QStyle.State_Selected:
                painter.fillRect(QRect(0, 0, option.rect.width(), int(document.size().height())), 
                               option.palette.highlight())
            
            # 绘制HTML内容
            document.drawContents(painter)
            painter.restore()
            
        except Exception as e:
            print(f"Error painting HTML item: {e}")
            super().paint(painter, option, index)
    
    def sizeHint(self, option, index):
        """返回项的大小提示"""
        try:
            html_content = index.data(Qt.DisplayRole)
            if not html_content:
                return super().sizeHint(option, index)
                
            document = QTextDocument()
            document.setHtml(html_content)
            document.setTextWidth(option.rect.width() if option.rect.width() > 0 else 400)
            
            return QSize(int(document.idealWidth()), int(document.size().height()))
            
        except Exception as e:
            print(f"Error calculating size hint: {e}")
            return QSize(400, 100)  # 默认大小


class VirtualResultsView(QListView):
    """虚拟滚动结果视图"""
    
    # 信号定义
    linkClicked = Signal(QUrl)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置基本属性
        self.setAlternatingRowColors(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 启用鼠标跟踪以支持链接悬停
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)

        # 启用右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # 设置HTML委托
        self.html_delegate = HtmlItemDelegate(self)
        self.setItemDelegate(self.html_delegate)
        
        # 连接点击信号
        self.clicked.connect(self._handle_item_clicked)
        
    def _handle_item_clicked(self, index):
        """处理项点击，目前由mousePressEvent处理链接点击"""
        pass  # 链接点击由mousePressEvent处理
    
    def mousePressEvent(self, event):
        """处理鼠标点击事件，特别是链接点击"""
        if event.button() == Qt.LeftButton:
            index = self.indexAt(event.position().toPoint())
            if index.isValid():
                # 使用QTextDocument来精确检测链接点击
                html_content = index.data(Qt.DisplayRole)
                if html_content:
                    clicked_link = self._detect_link_at_position(event.position().toPoint(), index, html_content)
                    if clicked_link:
                        self.linkClicked.emit(QUrl(clicked_link))
                        return

        # 调用父类处理
        super().mousePressEvent(event)

    def _detect_link_at_position(self, global_pos, index, html_content):
        """使用QTextDocument精确检测点击位置的链接"""
        try:
            # QTextDocument, QTextCursor 已在文件顶部导入
            from PySide6.QtCore import QPointF

            # 创建临时的QTextDocument来处理HTML
            doc = QTextDocument()
            doc.setHtml(html_content)

            # 获取项目的矩形区域
            item_rect = self.visualRect(index)
            if not item_rect.isValid():
                print(f"无效的项目矩形，使用备选方案")
                return self._find_clicked_link_fallback(html_content)

            # 计算相对于项目的点击位置
            relative_pos = global_pos - item_rect.topLeft()
            print(f"点击位置: 全局{global_pos.x()},{global_pos.y()}, 相对{relative_pos.x()},{relative_pos.y()}")

            # 尝试多个hitTest策略
            hit_strategies = [
                (Qt.HitTestAccuracy.ExactHit, "精确命中"),
                (Qt.HitTestAccuracy.FuzzyHit, "模糊命中")
            ]

            for strategy, strategy_name in hit_strategies:
                hit_point = QPointF(relative_pos.x(), relative_pos.y())
                cursor_pos = doc.documentLayout().hitTest(hit_point, strategy)
                print(f"{strategy_name}测试: 光标位置 {cursor_pos}")

                if cursor_pos >= 0:
                    # 创建光标并检查格式
                    cursor = QTextCursor(doc)
                    cursor.setPosition(cursor_pos)

                    # 获取字符格式
                    char_format = cursor.charFormat()

                    # 检查是否是链接
                    if char_format.isAnchor():
                        anchor_href = char_format.anchorHref()
                        print(f"检测到链接点击({strategy_name}): {anchor_href}")
                        return anchor_href
                    else:
                        # 尝试扩展选择范围，查找附近的链接
                        for offset in [-1, 1, -2, 2]:
                            try_pos = cursor_pos + offset
                            if try_pos >= 0:
                                cursor.setPosition(try_pos)
                                char_format = cursor.charFormat()
                                if char_format.isAnchor():
                                    anchor_href = char_format.anchorHref()
                                    print(f"检测到附近链接({strategy_name}, 偏移{offset}): {anchor_href}")
                                    return anchor_href

            print(f"精确检测失败，使用备选方案")
            # 如果精确检测失败，使用备选方案
            return self._find_clicked_link_fallback(html_content)

        except Exception as e:
            print(f"链接检测出错，使用备选方案: {e}")
            return self._find_clicked_link_fallback(html_content)

    def _find_clicked_link_fallback(self, html_content):
        """备选的链接检测方案"""
                    import re
        
        # 提取所有链接
        link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
        links = re.findall(link_pattern, html_content)
        if not links:
            return None

        # 使用简单的轮换策略或者随机选择，避免总是选择同一个
        import time
        openfile_links = [url for url, text in links if url.startswith('openfile:')]
        openfolder_links = [url for url, text in links if url.startswith('openfolder:')]
        toggle_links = [url for url, text in links if url.startswith('toggle::')]

        # 如果同时有文件和目录链接，使用时间戳来轮换选择
        if openfile_links and openfolder_links:
            # 使用毫秒数的奇偶性来决定选择哪个
            ms = int(time.time() * 1000) % 1000
            if ms % 2 == 0:
                print(f"备选检测：选择打开文件链接")
                return openfile_links[0]
            else:
                print(f"备选检测：选择打开目录链接")
                return openfolder_links[0]

        # 如果只有一种类型，直接返回
        if openfile_links:
            print(f"备选检测：只有打开文件链接")
            return openfile_links[0]
        if openfolder_links:
            print(f"备选检测：只有打开目录链接")
            return openfolder_links[0]
        if toggle_links:
            print(f"备选检测：只有折叠链接")
            return toggle_links[0]

        return links[0][0] if links else None



    def mouseDoubleClickEvent(self, event):
        """处理双击事件，显示文本选择对话框"""
        if event.button() == Qt.LeftButton:
            index = self.indexAt(event.position().toPoint())
            if index.isValid():
                # 获取HTML内容
                html_content = index.data(Qt.DisplayRole)
                if html_content:
                    self._show_text_selection_dialog(html_content)
                    return
        # 调用父类处理
        super().mouseDoubleClickEvent(event)

    def _show_text_selection_dialog(self, html_content):
        """显示文本选择对话框"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QMessageBox

        dialog = QDialog(self)
        dialog.setWindowTitle("文本选择")
        dialog.resize(800, 500)

        layout = QVBoxLayout(dialog)

        # 创建文本编辑器显示内容
        text_edit = QTextEdit()
        text_edit.setHtml(html_content)
        text_edit.setReadOnly(False)  # 允许选择
        layout.addWidget(text_edit)

        # 按钮布局
        button_layout = QHBoxLayout()

        # 复制全部按钮
        copy_all_btn = QPushButton("复制全部内容")
        copy_all_btn.clicked.connect(lambda: self._copy_all_text(text_edit, dialog))
        button_layout.addWidget(copy_all_btn)

        # 复制选中按钮
        copy_selected_btn = QPushButton("复制选中文本")
        copy_selected_btn.clicked.connect(lambda: self._copy_selected_text(text_edit, dialog))
        button_layout.addWidget(copy_selected_btn)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        dialog.exec()

    def _copy_all_text(self, text_edit, dialog):
        """复制全部文本内容"""
        plain_text = text_edit.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(plain_text)
        QMessageBox.information(dialog, "复制成功", f"已复制 {len(plain_text)} 个字符到剪贴板")

    def _copy_selected_text(self, text_edit, dialog):
        """复制选中的文本"""
        cursor = text_edit.textCursor()
        selected_text = cursor.selectedText()

        if selected_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(selected_text)
            QMessageBox.information(dialog, "复制成功", f"已复制 {len(selected_text)} 个字符到剪贴板")
        else:
            QMessageBox.warning(dialog, "未选择文本", "请先选择要复制的文本")

    def _show_context_menu(self, position):
        """显示虚拟滚动视图的右键菜单"""
        index = self.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)

        # 获取HTML内容
        html_content = index.data(Qt.DisplayRole)
        if html_content:
            # 复制内容选项
            copy_action = menu.addAction("复制内容")
            copy_action.triggered.connect(lambda: self._copy_item_content(html_content))

            menu.addSeparator()

            # 文本选择对话框选项
            select_action = menu.addAction("文本选择...")
            select_action.triggered.connect(lambda: self._show_text_selection_dialog(html_content))

            # 显示菜单
            menu.exec(self.mapToGlobal(position))

    def _copy_item_content(self, html_content):
        """复制项目的纯文本内容"""
        from PySide6.QtGui import QTextDocument

        # 将HTML转换为纯文本
        doc = QTextDocument()
        doc.setHtml(html_content)
        plain_text = doc.toPlainText()

        # 复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(plain_text)

        # 显示成功消息（可选）
        if hasattr(self, 'parent') and hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"已复制 {len(plain_text)} 个字符到剪贴板", 3000)

# --- Worker Class for Background Tasks ---
class Worker(QObject):
    # Signals to communicate with the main thread
    statusChanged = Signal(str)       # For general status updates
    # --- MODIFIED: Added detail parameter to progressUpdated signal ---
    progressUpdated = Signal(int, int, str, str) # current, total, phase, detail
    # -----------------------------------------------------------------
    resultsReady = Signal(object)     # Search results dict with pagination info
    indexingComplete = Signal(dict)   # Summary dict from backend
    errorOccurred = Signal(str)       # Error message
    # --- ADDED: Signals for update check --- 
    updateAvailableSignal = Signal(dict) # Sends dict with version info
    upToDateSignal = Signal()
    updateCheckFailedSignal = Signal(str) # Sends error message
    # ---------------------------------------
    
    def __init__(self):
        super().__init__()
        # 防止重复发送完成信号的标志
        self._indexing_completed = False
        # 添加一个标志位，用于指示是否请求停止操作
        self.stop_requested = False
        
    def _check_stop_requested(self):
        """检查是否请求了停止操作，如果是则抛出异常"""
        if self.stop_requested:
            raise InterruptedError("操作被用户中断")

    @Slot(list, str, bool, int, int, object) # Added object for file_type_config
    @Slot(list, str, bool, int, int) # Added int for txt_content_limit_kb
    def run_indexing(self, source_directories, index_dir_path, enable_ocr, extraction_timeout, txt_content_limit_kb, file_type_config=None):
        """Runs the indexing process in the background for multiple source directories."""
        try:
            # 重置完成标志，防止重复发送信号
            self._indexing_completed = False
            # 重置停止标志位（用于索引操作）
            self.stop_requested = False
            print("🔄 开始索引操作，取消标志已重置")
            
            # --- Clear search cache before indexing ---
            self.clear_search_cache()
            # -----------------------------------------

            # --- Status message for multiple directories ---
            ocr_status_text = "启用OCR" if enable_ocr else "禁用OCR"
            dir_count = len(source_directories)
            dir_text = f"{dir_count} 个源目录" if dir_count != 1 else f"源目录 '{source_directories[0]}'"
            self.statusChanged.emit(f"开始索引 ({ocr_status_text}): {dir_text} -> {index_dir_path}")
            # ------------------------------------------------------

            # --- RESTORED Actual Backend Call and Generator Processing ---
            # 创建取消回调函数
            def cancel_check():
                # --- FIXED: 添加调试信息和更频繁的检查 ---
                if self.stop_requested:
                    print("🚨 检测到取消请求 - 停止索引操作")
                    return True
                return False
            
            # Extract file type configuration if provided
            full_index_types = []
            filename_only_types = []

            if file_type_config and isinstance(file_type_config, dict):
                full_index_types = file_type_config.get('full_index_types', [])
                filename_only_types = file_type_config.get('filename_only_types', [])
                print(f"完整索引文件类型: {full_index_types}")
                print(f"仅文件名索引文件类型: {filename_only_types}")
            else:
                print("使用默认设置：索引所有支持的文件类型（完整索引）")

            generator = document_search.create_or_update_index_legacy(
                source_directories,
                index_dir_path,
                enable_ocr,
                extraction_timeout=extraction_timeout, # Pass timeout here
                txt_content_limit_kb=txt_content_limit_kb, # Pass txt limit here
                file_types_to_index=full_index_types, # 仅传递完整索引的文件类型
                filename_only_types=filename_only_types, # 新增：仅文件名索引的文件类型
                cancel_callback=cancel_check  # Pass cancel callback
            )

            for update in generator:
                # 检查是否请求了停止
                self._check_stop_requested()
                
                # 添加更强的类型检查
                if not isinstance(update, dict):
                    print(f"WARNING: Received non-dict update: {type(update)}")
                    continue
                
                msg_type = update.get('type')
                message = update.get('message', '')

                if msg_type == 'status': # Only emit simple status for clarity
                     self.statusChanged.emit(message) # Emit raw status message from backend
                # Optional: Add back more specific status handling if needed
                # elif msg_type == 'add' or msg_type == 'update' or msg_type == 'delete' or msg_type == 'skip':
                #     self.statusChanged.emit(f"[{msg_type.upper()}] {message}")
                elif msg_type == 'progress':
                    current = update.get('current', 0)
                    total = update.get('total', 0)  # Use 0 for indeterminate
                    phase = update.get('phase', '') # Get phase info
                    # --- ADDED: Get detail text from update ---
                    detail = update.get('detail', '') # Get detail, default to empty
                    # --- MODIFIED: Emit progressUpdated with detail ---
                    # --- FIXED: 添加参数验证 ---
                    try:
                        # 确保参数类型正确
                        current = int(current) if current is not None else 0
                        total = int(total) if total is not None else 0
                        phase = str(phase) if phase is not None else "处理中"
                        detail = str(detail) if detail is not None else ""
                        
                        # 确保参数类型正确并处理可能的解包错误
                        try:
                            current = int(current) if current is not None else 0
                            total = int(total) if total is not None else 0
                            phase = str(phase) if phase is not None else "处理中"
                            detail = str(detail) if detail is not None else ""
                            self.progressUpdated.emit(current, total, phase, detail)
                        except (ValueError, TypeError) as e:
                            print(f"Progress emit error: {e}, using defaults")
                            self.progressUpdated.emit(0, 100, "处理中", "")
                    except Exception as e:
                        print(f"Error emitting progress: {e}")
                        # 发射安全的默认值
                        self.progressUpdated.emit(0, 100, "处理中", "")
                    # --------------------------------------------------
                elif msg_type == 'warning':
                    self.statusChanged.emit(f"[警告] {message}")  # Warnings can also be status messages
                elif msg_type == 'error':
                    self.errorOccurred.emit(f"索引错误: {message}")
                elif msg_type == 'complete': # Check for 'complete' type
                    summary_dict = update.get('summary', {}) # Get the summary dict
                    if not self._indexing_completed:
                        self._indexing_completed = True
                        self.indexingComplete.emit(summary_dict) # Emit the summary dict
            # -------------------------------------------------------------

        except InterruptedError as e:
            # 捕获用户中断，发送取消通知
            self.statusChanged.emit("操作已被用户取消")
            summary_dict = {
                'message': '索引已被用户取消。',
                'added': 0,
                'updated': 0,
                'deleted': 0,
                'errors': 0,
                'cancelled': True
            }
            if not self._indexing_completed:
                self._indexing_completed = True
                self.indexingComplete.emit(summary_dict)
        except Exception as e:
            # Catch any unexpected errors during the backend call itself
            tb = traceback.format_exc()
            print(f"WORKER EXCEPTION in run_indexing: {e}\n{tb}", file=sys.stderr)
            self.errorOccurred.emit(f"启动或执行索引时发生意外错误: {e}")

    @Slot(str, str, object, object, object, object, object, str, bool, str, object, int, int)
    def run_search(self, query_str, search_mode, min_size, max_size, start_date, end_date, file_type_filter, index_dir_path, case_sensitive, search_scope, search_dirs, page_number=1, page_size=50):
        """Runs the search process in the background with optional filters, using cache."""
        try:
            # 重置停止标志位（仅用于搜索操作）
            self.stop_requested = False
            print("🔄 开始搜索操作，取消标志已重置")
            
            # --- Convert arguments to hashable types for caching --- 
            # Dates are already QDate, convert to string or None (hashable)
            start_date_str = None
            end_date_str = None
            if isinstance(start_date, QDate) and start_date != QDate(1900, 1, 1): # Check against default
                start_date_str = start_date.toString('yyyy-MM-dd')
            if isinstance(end_date, QDate) and end_date != QDate.currentDate(): # Check against default
                end_date_str = end_date.toString('yyyy-MM-dd')

            # Convert file_type_filter list to a tuple (hashable)
            file_type_filter_tuple = tuple(sorted(file_type_filter)) if file_type_filter else None
            
            # Convert search_dirs to a tuple if it's a list (to make it hashable for caching)
            search_dirs_tuple = tuple(search_dirs) if isinstance(search_dirs, list) else search_dirs
            
            # min_size/max_size are int/None (hashable)
            # query_str, search_mode, index_dir_path, case_sensitive are str/bool (hashable)

            # --- Construct User-Friendly Status Message --- 
            filter_parts = []
            if min_size is not None: filter_parts.append(f"最小大小: {min_size}KB")
            if max_size is not None: filter_parts.append(f"最大大小: {max_size}KB")
            if start_date_str: filter_parts.append(f"开始日期: {start_date_str}")
            if end_date_str: filter_parts.append(f"结束日期: {end_date_str}")
            if file_type_filter: filter_parts.append(f"文件类型: {', '.join(file_type_filter)}")
            filter_desc = ", ".join(filter_parts)
            search_desc = f"'{query_str}'" if query_str else "(所有文档)"  # Put query in quotes
            mode_desc = "精确" if search_mode == 'phrase' else "模糊"
            case_desc = " (区分大小写)" if case_sensitive else ""
            # -- Added scope description --
            scope_ui_map = {'fulltext': '全文', 'filename': '文件名'}
            scope_text = scope_ui_map.get(search_scope, search_scope) # Get display name
            scope_desc = f" (范围: {scope_text})"
            # ---------------------------
            status_msg = f"正在进行 {mode_desc} {case_desc}{scope_desc}: {search_desc}"
            if filter_desc:
                status_msg += f" (筛选条件: {filter_desc})"
            status_msg += "..."
            self.statusChanged.emit(status_msg)
            # ---------------------------------------------------------------

            # 检查是否请求了停止
            self._check_stop_requested()

            # --- Call the cached search function --- 
            results = self._perform_search_with_cache(
                query_str,
                search_mode,
                min_size,
                max_size,
                start_date_str,
                end_date_str,
                file_type_filter_tuple,
                index_dir_path,
                case_sensitive,
                search_scope, # Pass scope here
                search_dirs_tuple, # Pass the tuple version instead of the list
                page_number,
                page_size
            )
            # -------------------------------------------
            
            # 再次检查是否请求了停止
            self._check_stop_requested()
            
            self.resultsReady.emit(results)

        except InterruptedError:
            # 捕获用户中断，发送取消通知
            self.statusChanged.emit("搜索已被用户取消")
            self.resultsReady.emit([])  # 发送空结果列表
        except Exception as e:
            error_info = traceback.format_exc()
            self.errorOccurred.emit(f"搜索过程中发生意外错误: {e}\n{error_info}")

    # --- NEW: Cached Search Function ---
    @functools.lru_cache(maxsize=128) # Cache up to 128 recent search results
    def _perform_search_with_cache(self, query_str, search_mode, min_size, max_size, start_date_str, end_date_str, file_type_filter_tuple, index_dir_path, case_sensitive, search_scope, search_dirs_tuple, page_number=1, page_size=50):
        """Internal method that performs the actual search and caches results.
           Args must be hashable, hence file_type_filter_tuple.
        """

        print(f"--- Cache MISS: Performing backend search for: '{query_str}' (Scope: {search_scope}) ---") # Debug with scope
        # Convert tuple back to list for backend function if needed (check backend signature)
        file_type_filter_list = list(file_type_filter_tuple) if file_type_filter_tuple else None
        
        # 检查是否需要过滤目录
        search_dirs_list = list(search_dirs_tuple) if search_dirs_tuple else None
        if search_dirs_list:
            print(f"--- Search will be filtered to {len(search_dirs_list)} directories ---")
        
        # Call the actual backend search function, passing scope
        try:
            import inspect
<<<<<<< HEAD
            # --- ADDED: 使用优化的搜索引擎 ---
            print(f"🚀 使用优化搜索引擎: {query_str}")
            
            # 构建搜索参数
            search_params = {
                'search_mode': search_mode,
                'search_scope': search_scope,
                'case_sensitive': case_sensitive,
                'limit': 1200  # 调整到1200条，平衡性能与完整性
            }
            
            # 添加详细调试信息
            print(f"🔍 精确搜索调试信息:")
            print(f"   查询词: '{query_str}'")
            print(f"   搜索模式: {search_mode}")
            print(f"   搜索范围: {search_scope}")
            print(f"   区分大小写: {case_sensitive}")
            if search_mode == 'phrase':
                print(f"   精确搜索: 将查找包含完整短语 '{query_str}' 的内容")

            # 添加可选参数
            if min_size is not None:
                search_params['min_size_kb'] = min_size
            if max_size is not None:
                search_params['max_size_kb'] = max_size  
            if start_date_str:
                search_params['start_date'] = start_date_str
            if end_date_str:
                search_params['end_date'] = end_date_str
            if file_type_filter_list:
                search_params['file_type_filter'] = file_type_filter_list
            if search_dirs_list:
                search_params['current_source_dirs'] = search_dirs_list
            
            # 尝试使用优化搜索引擎，降级到原始搜索
            try:
                results = document_search.optimized_search_sync(
                    query_str, index_dir_path, **search_params
=======
            backend_params = inspect.signature(document_search.search_index).parameters
            if 'search_dirs' in backend_params:
                # 后端支持search_dirs参数
                search_result = document_search.search_index(
                    query_str=query_str, 
                    index_dir_path=index_dir_path, 
                    search_mode=search_mode,
                    search_scope=search_scope,
                    min_size_kb=min_size,
                    max_size_kb=max_size,
                    start_date=start_date_str, 
                    end_date=end_date_str, 
                    file_type_filter=file_type_filter_list,
                    case_sensitive=case_sensitive,
                    search_dirs=search_dirs_list,
                    page_size=page_size,
                    page_number=page_number,
                    return_total=(page_number == 1)
                )
            else:
                # 后端不支持search_dirs参数
                search_result = document_search.search_index(
                    query_str=query_str, 
                    index_dir_path=index_dir_path, 
                    search_mode=search_mode,
                    search_scope=search_scope,
                    min_size_kb=min_size,
                    max_size_kb=max_size,
                    start_date=start_date_str, 
                    end_date=end_date_str, 
                    file_type_filter=file_type_filter_list,
                    case_sensitive=case_sensitive,
                    page_size=page_size,
                    page_number=page_number,
                    return_total=(page_number == 1)
>>>>>>> 205d800b1db2b33deca56ba17897fa8699e7318f
                )
            except Exception as e:
                print(f"⚠️ 优化搜索失败，降级到传统搜索: {e}")
                # 降级到原始搜索方法
                backend_params = inspect.signature(document_search.search_index).parameters
                if 'current_source_dirs' in backend_params:
                    # 后端支持current_source_dirs参数
                    results = document_search.search_index(
                        query_str=query_str, 
                        index_dir_path=index_dir_path, 
                        search_mode=search_mode,
                        search_scope=search_scope,
                        min_size_kb=min_size,
                        max_size_kb=max_size,
                        start_date=start_date_str, 
                        end_date=end_date_str, 
                        file_type_filter=file_type_filter_list,
                        case_sensitive=case_sensitive,
                        current_source_dirs=search_dirs_list
                    )
                else:
                    # 后端不支持current_source_dirs参数
                    results = document_search.search_index(
                        query_str=query_str, 
                        index_dir_path=index_dir_path, 
                        search_mode=search_mode,
                        search_scope=search_scope,
                        min_size_kb=min_size,
                        max_size_kb=max_size,
                        start_date=start_date_str, 
                        end_date=end_date_str, 
                        file_type_filter=file_type_filter_list,
                        case_sensitive=case_sensitive
                    )
        except TypeError:
            # 如果后端不支持某些参数，使用最基本的参数调用
            search_result = document_search.search_index(
                query_str=query_str, 
                index_dir_path=index_dir_path, 
                search_mode=search_mode,
                page_size=page_size,
                page_number=page_number,
                return_total=(page_number == 1)
            )
        
        # 处理搜索结果格式（新增：处理分页格式）
        if isinstance(search_result, dict) and 'results' in search_result:
            # 新的分页格式：{'results': [...], 'pagination': {...}}
            results_list = search_result['results']  # 临时变量：结果列表
            pagination_info = search_result.get('pagination', {})
            print(f"使用分页格式：获得 {len(results_list)} 条结果，分页信息：{pagination_info}")
            # 保持完整的分页格式对象
            results = search_result  # 保持完整的分页格式
            is_paginated_format = True
        else:
            # 旧格式：直接返回列表
            results = search_result if isinstance(search_result, list) else []
            print(f"使用传统格式：获得 {len(results)} 条结果")
            is_paginated_format = False
        
        # 如果搜索目录不为None但后端不支持，则手动过滤结果
        if search_dirs_list and (results_list if is_paginated_format else results):
            try:
                print(f"DEBUG: 后端不支持目录过滤，手动过滤 {len(results)} 个结果")
                # 创建过滤后的结果列表
                filtered_results = []
                
                # 规范化所选目录路径
                # 确保路径格式一致，以便正确匹配
                normalized_search_dirs = [os.path.normpath(d).lower() for d in search_dirs_list]
                print(f"DEBUG: 规范化的过滤目录: {normalized_search_dirs}")
                
                # 遍历结果进行过滤
                for result in (results_list if is_paginated_format else results):
                    file_path = result.get('file_path', '')
                    if not file_path:
                        continue
                    
                    # 检查文件所在的目录是否在所选目录列表中
                    is_in_selected_dir = False
                    
                    # 处理存档文件内部项目
                    if '::' in file_path:
                        archive_path = file_path.split('::', 1)[0]
                        file_path_normalized = os.path.normpath(archive_path).lower()
                    else:
                        file_path_normalized = os.path.normpath(file_path).lower()
                    
                    # 检查文件是否在选定的目录列表中或其子目录中
                    for search_dir in normalized_search_dirs:
                        # 检查文件是否在搜索目录中或其子目录中
                        if file_path_normalized.startswith(search_dir + os.sep) or file_path_normalized == search_dir:
                            is_in_selected_dir = True
                            print(f"DEBUG: 文件 {file_path} 匹配目录 {search_dir}")
                            break
                            
                    if not is_in_selected_dir:
                        print(f"DEBUG: 过滤掉文件 {file_path}（不在当前源目录中）")
                    
                    # 如果文件在所选目录中，添加到过滤结果
                    if is_in_selected_dir:
                        filtered_results.append(result)
                
                print(f"--- Filtered {len(results_list if is_paginated_format else results)} results to {len(filtered_results)} results based on selected directories ---")
                if is_paginated_format:
                    # 更新分页格式中的结果列表
                    results['results'] = filtered_results
                    # 更新分页信息中的总数
                    if 'pagination' in results:
                        results['pagination']['total_count'] = len(filtered_results)
                        # 重新计算总页数
                        page_size = results['pagination'].get('page_size', 50)
                        results['pagination']['total_pages'] = max(1, (len(filtered_results) + page_size - 1) // page_size)
                else:
                    results = filtered_results
            except Exception as e:
                print(f"Error filtering results by directory: {e}")
                # 如果过滤出错，保留原始结果
                import traceback
                traceback.print_exc()
        
        # 确保返回完整的分页格式（保持分页信息）
        if is_paginated_format:
            # 分页格式：返回完整的分页对象
            return results
        else:
            # 传统格式：返回列表
            return results if isinstance(results, list) else []

    def clear_search_cache(self):
        """Clears the LRU search cache."""
        cache_info = self._perform_search_with_cache.cache_info()
        print(f"--- Clearing search cache ({cache_info.hits} hits, {cache_info.misses} misses, {cache_info.currsize}/{cache_info.maxsize} size) ---")
        self._perform_search_with_cache.cache_clear()
        print("--- Search cache cleared. ---")

    # --- ADDED: Worker method for checking updates --- 
    @Slot(str, str) # current_version, update_url
    def run_update_check(self, current_version_str, update_url):
        """Performs the update check in the background."""
        try:
            print(f"Checking for updates at {update_url}...")
            
            # 创建一个完全定制的连接会话
            session = requests.Session()
            
            # 配置重试策略，加大重试次数和间隔
            retry_strategy = requests.packages.urllib3.util.retry.Retry(
                total=5,                          # 增加到5次重试
                backoff_factor=1,                 # 重试间隔更长
                status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的HTTP状态码
                allowed_methods=["GET"],          # 只对GET请求重试
                raise_on_status=False,            # 不立即因状态码而失败
                connect=5,                        # 连接问题最多重试5次
                read=3,                           # 读取问题最多重试3次
                redirect=5                        # 重定向最多重试5次
            )
            
            # 配置适配器，包括连接和读取超时
            adapter = requests.adapters.HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=3,               # 保持连接池大小
                pool_maxsize=10,                  # 最大连接数
                pool_block=False                  # 不阻塞连接池
            )
            
            # 应用适配器到HTTP和HTTPS请求
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # 更详细的用户代理和请求头
            headers = {
                "User-Agent": f"WenzhiSou/UpdateChecker/{current_version_str} (Windows NT; PySide6)",
                "Accept": "application/json",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Connection": "close"  # 使用短连接，避免保持连接
            }
            
            # 在请求URL中添加随机参数，避免缓存
            import random, time
            cache_buster = f"&_cb={int(time.time())}_{random.randint(1000, 9999)}"
            if "?" in update_url:
                request_url = f"{update_url}{cache_buster}"
            else:
                request_url = f"{update_url}?_cb={int(time.time())}_{random.randint(1000, 9999)}"
            
            print(f"实际请求URL: {request_url}")
            
            # 执行GET请求，使用更长的超时时间
            response = session.get(
                request_url, 
                timeout=(10, 30),            # 连接超时10秒，读取超时30秒
                headers=headers,
                verify=True                  # 验证SSL证书
            )
            
            # 处理状态码
            if response.status_code != 200:
                print(f"请求返回非200状态码: {response.status_code}")
                error_msg = f"服务器返回状态码 {response.status_code}，请稍后再试"
                self.updateCheckFailedSignal.emit(error_msg)
                return
                
            # 尝试解析JSON
            try:
                latest_info = response.json()
            except json.JSONDecodeError:
                print(f"JSON解析失败，返回内容: {response.text[:200]}...")
                error_msg = "无法解析更新信息文件。文件格式可能不正确。"
                self.updateCheckFailedSignal.emit(error_msg)
                return
                
            latest_version_str = latest_info.get("version")
            
            if not latest_version_str:
                raise ValueError("Version information missing in update file.")
            
            print(f"Current version: {current_version_str}, Latest version from server: {latest_version_str}")
            
            # Compare versions
            current_v = version.parse(current_version_str)
            latest_v = version.parse(latest_version_str)
            
            if latest_v > current_v:
                print("Update available.")
                self.updateAvailableSignal.emit(latest_info) # Send all info back
            else:
                print("Already up to date.")
                self.upToDateSignal.emit()
                
        except requests.exceptions.SSLError as ssl_err:
            error_msg = f"SSL证书验证失败: {ssl_err}"
            print(f"Error: {error_msg}")
            self.updateCheckFailedSignal.emit(error_msg)
            
        except requests.exceptions.ConnectionError as ce:
            # 连接错误需要更详细的诊断
            error_detail = str(ce)
            print(f"Connection error details: {error_detail}")
            if "Connection aborted" in error_detail and "ConnectionResetError" in error_detail:
                error_msg = "检查更新时网络连接被重置，可能是网络问题、防火墙限制或服务器拒绝连接"
                
                # 尝试Ping目标网站
                try:
                    from urllib.parse import urlparse
                    import socket
                    parsed_url = urlparse(update_url)
                    hostname = parsed_url.netloc
                    print(f"尝试解析域名: {hostname}")
                    ip = socket.gethostbyname(hostname)
                    print(f"域名 {hostname} 解析到IP: {ip}")
                    error_msg += f"\n\n已确认域名 {hostname} 可以解析到 {ip}。问题可能是由于网络连接限制或服务器配置问题。"
                except Exception as e:
                    error_msg += f"\n\n域名解析失败: {e}。可能是网络连接问题或DNS服务不可用。"
            else:
                error_msg = f"检查更新时连接错误: {ce}"
            self.updateCheckFailedSignal.emit(error_msg)
            
        except requests.exceptions.Timeout:
            error_msg = "检查更新请求超时，请稍后再试"
            print(f"Error: {error_msg}")
            self.updateCheckFailedSignal.emit(error_msg)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"检查更新时网络错误: {e}"
            print(f"Error: {error_msg}")
            self.updateCheckFailedSignal.emit(error_msg)
            
        except json.JSONDecodeError as je:
            error_msg = f"无法解析更新信息文件。文件格式可能不正确。详细错误: {je}"
            print(f"Error: {error_msg}")
            self.updateCheckFailedSignal.emit(error_msg)
            
        except ValueError as e:
            error_msg = f"更新信息文件内容错误: {e}"
            print(f"Error: {error_msg}")
            self.updateCheckFailedSignal.emit(error_msg)
            
        except Exception as e:
            error_msg = f"检查更新时发生未知错误: {e}"
            print(f"Error: {error_msg}")
            # 添加更多调试信息
            import traceback
            print(f"Update check exception traceback:\n{traceback.format_exc()}")
            self.updateCheckFailedSignal.emit(error_msg)
    # --------------------------------------------------

# --- Settings Dialog Class --- (NEW)
class SettingsDialog(QDialog):
    # MODIFIED: Accept an optional category argument
    def __init__(self, parent=None, category_to_show='all'):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(450) # Increase width slightly
        self.category_to_show = category_to_show # Store the category
        
        # --- ADDED: 获取许可证管理器 ---
        from license_manager import get_license_manager, Features
        self.license_manager = get_license_manager()
        # ------------------------------
        
        # --- 初始化设置对象 ---
        self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        # -----------------
        
        # --- 初始化主题文件列表 ---
        self.theme_files = ["现代蓝", "现代紫", "现代红", "现代橙", "默认"]
        # -----------------
        
        # --- 初始化文件类型选择 ---
        self.selected_file_types = []
        print("DEBUG: 初始化 self.selected_file_types =", self.selected_file_types)
        # -----------------

        # --- Main Layout ---
        layout = QVBoxLayout(self)

        # --- Create Category Containers ---
        self.index_settings_widget = QWidget()
        self.search_settings_widget = QWidget()
        self.interface_settings_widget = QWidget()

        # --- Populate Index Settings Container ---
        index_layout = QVBoxLayout(self.index_settings_widget)
        index_layout.setContentsMargins(5,5,5,5)

        # 创建标签页控件来组织设置
        tab_widget = QTabWidget()
        index_layout.addWidget(tab_widget)

        # === 基本设置标签页 ===
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        basic_layout.setSpacing(15)

        # 基本设置分组
        basic_group = QGroupBox("📁 基本设置")
        basic_group_layout = QVBoxLayout(basic_group)

        # --- Source Directories Management ---
        source_dirs_label = QLabel("要索引的文件夹:")
        source_dirs_label.setStyleSheet("font-weight: bold; color: #333;")

        self.source_dirs_list = QListWidget()
        self.source_dirs_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.source_dirs_list.setToolTip("指定一个或多个需要建立索引的根文件夹。")
        self.source_dirs_list.setMaximumHeight(120)  # 限制高度

        source_dirs_button_layout = QHBoxLayout()
        self.add_source_dir_button = QPushButton("➕ 添加目录")
        self.remove_source_dir_button = QPushButton("➖ 移除选中")
        self.add_source_dir_button.setMaximumWidth(100)
        self.remove_source_dir_button.setMaximumWidth(100)
        source_dirs_button_layout.addWidget(self.add_source_dir_button)
        source_dirs_button_layout.addWidget(self.remove_source_dir_button)
        source_dirs_button_layout.addStretch()

        basic_group_layout.addWidget(source_dirs_label)
        basic_group_layout.addWidget(self.source_dirs_list)
        basic_group_layout.addLayout(source_dirs_button_layout)

        # OCR设置分组
        ocr_group = QGroupBox("🔍 OCR设置")
        ocr_group_layout = QVBoxLayout(ocr_group)

        ocr_layout = QHBoxLayout()
        self.enable_ocr_checkbox = QCheckBox("启用 OCR 光学字符识别")
        self.pro_feature_ocr_label = QLabel("🔒 专业版专享")
        self.pro_feature_ocr_label.setStyleSheet("color: #FF6600; font-weight: bold; font-size: 11px;")
        ocr_layout.addWidget(self.enable_ocr_checkbox)
        ocr_layout.addWidget(self.pro_feature_ocr_label)
        ocr_layout.addStretch()

        # OCR说明
        ocr_info = QLabel("💡 OCR可以识别PDF中的图像文字，但会显著增加索引时间")
        ocr_info.setStyleSheet("color: #666; font-size: 11px; margin-top: 5px;")
        ocr_info.setWordWrap(True)

        ocr_group_layout.addLayout(ocr_layout)
        ocr_group_layout.addWidget(ocr_info)
        
        # 根据许可状态禁用OCR选项
        pdf_support_available = self.license_manager.is_feature_available(Features.PDF_SUPPORT)
        self.enable_ocr_checkbox.setEnabled(pdf_support_available)
        self.pro_feature_ocr_label.setVisible(not pdf_support_available)
        
        # 添加提示信息
        self.enable_ocr_checkbox.setToolTip("OCR功能需要专业版授权才能使用" if not pdf_support_available else 
                                       "启用OCR可以识别PDF中的图像文字，但会显著增加索引时间")

        basic_layout.addWidget(basic_group)
        basic_layout.addWidget(ocr_group)
        basic_layout.addStretch()
        tab_widget.addTab(basic_tab, "📁 基本设置")

        # === 文件类型标签页 ===
        file_types_tab = QWidget()
        file_types_layout = QVBoxLayout(file_types_tab)
        file_types_layout.setSpacing(10)

        # --- ADDED: File Types to Index Selection ---
        file_types_group = QGroupBox("📄 文件类型与索引模式")
        file_types_group.setToolTip("选择需要创建索引的文件类型，未勾选的类型将被跳过")
        file_types_group_layout = QVBoxLayout(file_types_group)

        # 添加说明信息
        info_widget = QWidget()
        info_widget.setStyleSheet("background-color: #e8f4fd; border: 1px solid #bee5eb; border-radius: 4px; padding: 8px;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(8, 8, 8, 8)

        info_title = QLabel("💡 索引模式说明")
        info_title.setStyleSheet("font-weight: bold; color: #0c5460; margin-bottom: 4px;")
        info_content = QLabel("• 完整索引：提取并索引文件完整内容，支持全文搜索\n• 仅文件名：只索引文件名信息，适合大文件或归档文件")
        info_content.setStyleSheet("color: #0c5460; font-size: 11px; line-height: 1.4;")
        info_content.setWordWrap(True)

        info_layout.addWidget(info_title)
        info_layout.addWidget(info_content)
        file_types_group_layout.addWidget(info_widget)
        
        # 创建全选复选框
        controls_layout = QHBoxLayout()
        self.select_all_types_checkbox = QCheckBox("🔲 全选/全不选")
        self.select_all_types_checkbox.setChecked(True)
        self.select_all_types_checkbox.setStyleSheet("font-weight: bold; color: #333;")
        controls_layout.addWidget(self.select_all_types_checkbox)
        controls_layout.addStretch()
        file_types_group_layout.addLayout(controls_layout)

        # 创建滚动区域用于文件类型列表
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMaximumHeight(300)

        scroll_widget = QWidget()
        scroll_area.setWidget(scroll_widget)
        
        # 定义支持的文件类型
        supported_types = {
            # 文档类型
            'txt': {'display': '📝 文本文件 (.txt)', 'pro_feature': None},
            'docx': {'display': '📄 Word文档 (.docx)', 'pro_feature': None},
            'xlsx': {'display': '📊 Excel表格 (.xlsx)', 'pro_feature': None},
            'pptx': {'display': '📺 PowerPoint演示文稿 (.pptx)', 'pro_feature': None},
            'pdf': {'display': '📋 PDF文档 (.pdf)', 'pro_feature': Features.PDF_SUPPORT},
            'html': {'display': '🌐 HTML网页 (.html, .htm)', 'pro_feature': None},
            'rtf': {'display': '📄 RTF富文本 (.rtf)', 'pro_feature': None},
            'md': {'display': '📝 Markdown文档 (.md)', 'pro_feature': Features.MARKDOWN_SUPPORT},
            'eml': {'display': '📧 电子邮件 (.eml)', 'pro_feature': Features.EMAIL_SUPPORT},
            'msg': {'display': '📧 Outlook邮件 (.msg)', 'pro_feature': Features.EMAIL_SUPPORT},
            'zip': {'display': '🗜️ ZIP压缩包 (.zip)', 'pro_feature': None},
            'rar': {'display': '🗜️ RAR压缩包 (.rar)', 'pro_feature': None},

            # 多媒体文件类型（仅文件名索引）
            'mp4': {'display': '🎬 视频文件 (.mp4, .mkv, .avi等)', 'pro_feature': None, 'filename_only': True},
            'mp3': {'display': '🎵 音频文件 (.mp3, .wav, .flac等)', 'pro_feature': None, 'filename_only': True},
            'jpg': {'display': '🖼️ 图片文件 (.jpg, .png, .gif等)', 'pro_feature': None, 'filename_only': True},
        }
        
        # 将文件类型分为基础版和专业版两组
        free_types = []
        pro_types = []
        for type_key, type_info in supported_types.items():
            if type_info['pro_feature'] is None:
                free_types.append((type_key, type_info))
            else:
                pro_types.append((type_key, type_info))
        
        # 创建复选框网格布局
        grid_layout = QGridLayout(scroll_widget)
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setSpacing(8)
        
        # 文件类型复选框和模式选择字典
        self.file_type_checkboxes = {}
        self.file_type_modes = {}
        
        # 添加基础版文件类型
        row = 0
        for i, (type_key, type_info) in enumerate(free_types):
            type_layout = QHBoxLayout()
            type_layout.setSpacing(8)

            # 复选框
            checkbox = QCheckBox(type_info['display'])
            checkbox.setChecked(True)
            self.file_type_checkboxes[type_key] = checkbox

            # 索引模式选择下拉框
            mode_combo = QComboBox()
            mode_combo.addItem("完整索引", "full")
            mode_combo.addItem("仅文件名", "filename_only")

            # 检查是否为仅文件名类型（多媒体文件）
            if type_info.get('filename_only', False):
                mode_combo.setCurrentIndex(1)  # 设置为"仅文件名"
                mode_combo.setEnabled(False)   # 禁用选择
                mode_combo.setToolTip("多媒体文件只支持文件名索引")
            else:
                mode_combo.setCurrentIndex(0)  # 默认为"完整索引"

            mode_combo.setMinimumWidth(85)
            mode_combo.setMaximumWidth(85)
            mode_combo.setStyleSheet("QComboBox { font-size: 11px; }")
            self.file_type_modes[type_key] = mode_combo

            type_layout.addWidget(checkbox)
            type_layout.addStretch()
            type_layout.addWidget(mode_combo)

            type_widget = QWidget()
            type_widget.setLayout(type_layout)
            grid_layout.addWidget(type_widget, row, 0)

            checkbox.stateChanged.connect(self._update_select_all_checkbox_state)
                row += 1
        
        # 添加专业版文件类型
        for type_key, type_info in pro_types:
            pro_feature = type_info['pro_feature']
            feature_available = self.license_manager.is_feature_available(pro_feature)
            
            type_layout = QHBoxLayout()
            type_layout.setSpacing(8)

            # 复选框
            checkbox = QCheckBox(type_info['display'])
            checkbox.setChecked(feature_available)
            
            if not feature_available:
                checkbox.setEnabled(False)
                checkbox.setToolTip(f"此文件类型需要专业版授权才能使用")
                checkbox.setStyleSheet("color: #999;")

            # 索引模式选择下拉框
            mode_combo = QComboBox()
            mode_combo.addItem("完整索引", "full")
            mode_combo.addItem("仅文件名", "filename_only")

            # 检查是否为仅文件名类型（多媒体文件）
            if type_info.get('filename_only', False):
                mode_combo.setCurrentIndex(1)  # 设置为"仅文件名"
                mode_combo.setEnabled(False)   # 禁用选择
                mode_combo.setToolTip("多媒体文件只支持文件名索引")
            else:
                mode_combo.setCurrentIndex(0)  # 默认为"完整索引"
                if not feature_available:
                    mode_combo.setEnabled(False)
                    mode_combo.setToolTip(f"此文件类型需要专业版授权才能使用")

            mode_combo.setMinimumWidth(85)
            mode_combo.setMaximumWidth(85)
            mode_combo.setStyleSheet("QComboBox { font-size: 11px; }")

            self.file_type_modes[type_key] = mode_combo

            type_layout.addWidget(checkbox)
            type_layout.addStretch()
            type_layout.addWidget(mode_combo)

            # 添加专业版标记
            if not feature_available:
                pro_label = QLabel("🔒")
                pro_label.setStyleSheet("color: #FF6600; font-size: 12px;")
                pro_label.setToolTip("专业版功能")
                type_layout.addWidget(pro_label)

            row += 1
            type_widget.setLayout(type_layout)
            grid_layout.addWidget(type_widget, row, 0)

            if feature_available:
                checkbox.stateChanged.connect(self._update_select_all_checkbox_state)
            
            self.file_type_checkboxes[type_key] = checkbox
        
        file_types_group_layout.addWidget(scroll_area)
        file_types_layout.addWidget(file_types_group)
        
        # 连接全选复选框信号
        self.select_all_types_checkbox.stateChanged.connect(self._toggle_all_file_types)
        tab_widget.addTab(file_types_tab, "📄 文件类型")

        # === 高级设置标签页 ===
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        advanced_layout.setSpacing(15)

        # 性能设置分组
        performance_group = QGroupBox("⚡ 性能设置")
        performance_layout = QVBoxLayout(performance_group)

        # --- ADDED: Extraction Timeout Setting ---
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("⏱️ 单个文件提取超时 (秒):")
        timeout_label.setStyleSheet("font-weight: bold; color: #333;")
        self.extraction_timeout_spinbox = QSpinBox()
        self.extraction_timeout_spinbox.setMinimum(0)
        self.extraction_timeout_spinbox.setMaximum(600)
        self.extraction_timeout_spinbox.setValue(120)
        self.extraction_timeout_spinbox.setToolTip("设置提取单个文件内容（尤其是 OCR）允许的最长时间。\n0 表示不设置超时限制。")
        self.extraction_timeout_spinbox.setMaximumWidth(100)
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.extraction_timeout_spinbox)
        timeout_layout.addStretch()
        performance_layout.addLayout(timeout_layout)

        # --- ADDED: TXT Content Limit Setting ---
        txt_limit_layout = QHBoxLayout()
        txt_limit_label = QLabel("📝 .txt 文件内容索引上限 (KB):")
        txt_limit_label.setStyleSheet("font-weight: bold; color: #333;")
        self.txt_content_limit_spinbox = QSpinBox()
        self.txt_content_limit_spinbox.setMinimum(1)
        self.txt_content_limit_spinbox.setMaximum(10240)
        self.txt_content_limit_spinbox.setValue(1024)
        self.txt_content_limit_spinbox.setToolTip("设置每个 .txt 文件可以索引的内容大小上限。\n大文件会被截断以节省内存和空间。")
        self.txt_content_limit_spinbox.setMaximumWidth(100)
        txt_limit_layout.addWidget(txt_limit_label)
        txt_limit_layout.addWidget(self.txt_content_limit_spinbox)
        txt_limit_layout.addStretch()
        performance_layout.addLayout(txt_limit_layout)

        advanced_layout.addWidget(performance_group)

        # 索引存储位置设置
        storage_group = QGroupBox("💾 存储设置")
        storage_layout = QVBoxLayout(storage_group)

        index_dir_layout = QHBoxLayout()
        index_dir_label = QLabel("📁 索引文件存储位置:")
        index_dir_label.setStyleSheet("font-weight: bold; color: #333;")
        self.index_dir_entry = QLineEdit()
        self.index_dir_entry.setToolTip("指定用于存储索引文件的文件夹。")
        self.browse_index_button = QPushButton("📂 浏览...")
        self.browse_index_button.setMaximumWidth(80)
        index_dir_layout.addWidget(index_dir_label)
        index_dir_layout.addWidget(self.index_dir_entry, 1)
        index_dir_layout.addWidget(self.browse_index_button)
        storage_layout.addLayout(index_dir_layout)

        advanced_layout.addWidget(storage_group)
        advanced_layout.addStretch()
        tab_widget.addTab(advanced_tab, "⚙️ 高级设置")

        # 连接按钮信号
        self.add_source_dir_button.clicked.connect(self._browse_add_source_directory)
        self.remove_source_dir_button.clicked.connect(self._remove_selected_source_directory)
        self.browse_index_button.clicked.connect(self._browse_index_directory)

        # --- Populate Search Settings Container ---
        search_layout = QVBoxLayout(self.search_settings_widget)
        search_layout.setContentsMargins(0,0,0,0)
        search_groupbox = QGroupBox("搜索设置") # Use GroupBox
        search_layout.addWidget(search_groupbox)
        search_group_layout = QVBoxLayout(search_groupbox)

        # search_settings_label = QLabel("<b>搜索设置</b>") # Removed, groupbox has title
        # search_group_layout.addWidget(search_settings_label)
        self.case_sensitive_checkbox = QCheckBox("区分大小写")
        search_group_layout.addWidget(self.case_sensitive_checkbox)
        
        # --- ADDED: 文件大小筛选控件 ---
        size_filter_group = QGroupBox("文件大小筛选 (KB)")
        size_filter_layout = QHBoxLayout(size_filter_group)
        
        min_size_label = QLabel("最小:")
        self.min_size_entry = QLineEdit()
        self.min_size_entry.setPlaceholderText("可选")
        self.min_size_entry.setMaximumWidth(120)
        self.min_size_entry.setValidator(QIntValidator(0, 999999999))
        
        max_size_label = QLabel("最大:")
        self.max_size_entry = QLineEdit()
        self.max_size_entry.setPlaceholderText("可选")
        self.max_size_entry.setMaximumWidth(120)
        self.max_size_entry.setValidator(QIntValidator(0, 999999999))
        
        size_filter_layout.addWidget(min_size_label)
        size_filter_layout.addWidget(self.min_size_entry)
        size_filter_layout.addWidget(max_size_label)
        size_filter_layout.addWidget(self.max_size_entry)
        size_filter_layout.addStretch()
        
        search_group_layout.addWidget(size_filter_group)
        # -----------------------------
        
        # --- ADDED: 修改日期筛选控件 ---
        date_filter_group = QGroupBox("修改日期筛选")
        date_filter_layout = QVBoxLayout(date_filter_group)
        
        date_row_layout = QHBoxLayout()
        start_date_label = QLabel("从:")
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setDate(QDate(1900, 1, 1))
        self.start_date_edit.setMaximumDate(QDate.currentDate())
        
        end_date_label = QLabel("到:")
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setDate(QDate.currentDate())
        
        date_row_layout.addWidget(start_date_label)
        date_row_layout.addWidget(self.start_date_edit)
        date_row_layout.addWidget(end_date_label)
        date_row_layout.addWidget(self.end_date_edit)
        date_row_layout.addStretch()
        
        # 添加清除日期按钮
        clear_dates_layout = QHBoxLayout()
        self.clear_dates_button = QPushButton("清除日期筛选")
        self.clear_dates_button.clicked.connect(self._clear_dates)
        clear_dates_layout.addStretch()
        clear_dates_layout.addWidget(self.clear_dates_button)
        
        date_filter_layout.addLayout(date_row_layout)
        date_filter_layout.addLayout(clear_dates_layout)
        
        search_group_layout.addWidget(date_filter_group)
        # -----------------------------
        
        # Add more search settings here later if needed
        # search_group_layout.addStretch(1) # Remove stretch

        # --- Populate Interface Settings Container ---
        interface_layout = QVBoxLayout(self.interface_settings_widget)
        interface_layout.setContentsMargins(0,0,0,0)
        interface_groupbox = QGroupBox("界面设置") # Use GroupBox
        interface_layout.addWidget(interface_groupbox)
        interface_group_layout = QVBoxLayout(interface_groupbox)

        # interface_settings_label = QLabel("<b>界面设置</b>") # Removed
        # interface_group_layout.addWidget(interface_settings_label)
        # Theme Selector
        theme_layout = QHBoxLayout()
        theme_label = QLabel("主题:")
        self.theme_combo = QComboBox()
        
        # 基础主题（免费版可用）
        self.theme_combo.addItem("现代蓝")
        
        # 检查是否可以使用高级主题（专业版功能）
        advanced_themes_available = self.license_manager.is_feature_available(Features.ADVANCED_THEMES)
        
        # 专业版主题列表
        pro_themes = ["现代紫", "现代红", "现代橙"]
        
        for theme in pro_themes:
            self.theme_combo.addItem(theme)
            # 找到刚添加的项目的索引
            idx = self.theme_combo.count() - 1
            # 如果没有专业版许可证，则禁用该项
            if not advanced_themes_available:
                # 使用ItemDelegate可以更好地控制项目的样式，但这里使用简单的方法
                self.theme_combo.setItemData(idx, QColor(Qt.gray), Qt.ForegroundRole)
                # 添加"专业版"标记
                self.theme_combo.setItemText(idx, f"{theme} (专业版)")
        
        # 添加额外的系统主题
        # 删除浅色和深色主题
        
        # 在ComboBox旁边添加专业版标记（当没有专业版许可证时显示）
        self.pro_feature_theme_label = QLabel("部分主题需要专业版")
        self.pro_feature_theme_label.setStyleSheet("color: #FF6600; font-weight: bold;")
        self.pro_feature_theme_label.setVisible(not advanced_themes_available)
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo, 1)
        theme_layout.addWidget(self.pro_feature_theme_label)
        interface_group_layout.addLayout(theme_layout)
        
        # 如果选择了禁用的主题项，自动切换到"现代蓝"
        def on_theme_changed(index):
            if not advanced_themes_available and index > 0 and index <= len(pro_themes):
                self.theme_combo.setCurrentIndex(0)  # 切换回"现代蓝"
                QMessageBox.information(
                    self, 
                    "主题限制", 
                    "高级主题（现代紫、现代红、现代橙）仅在专业版中可用。\n"
                    "已自动切换到现代蓝主题。\n"
                    "升级到专业版以解锁所有主题。"
                )
        
        self.theme_combo.currentIndexChanged.connect(on_theme_changed)

        # Result Font Size Selector
        font_size_layout = QHBoxLayout()
        font_size_label = QLabel("结果字体大小:")
        self.result_font_size_spinbox = QSpinBox()
        self.result_font_size_spinbox.setMinimum(8)
        self.result_font_size_spinbox.setMaximum(18)
        self.result_font_size_spinbox.setSuffix(" pt")
        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.result_font_size_spinbox, 1)
        interface_group_layout.addLayout(font_size_layout)

        # --- ADDED: Default Sort Settings ---
        sort_group = QGroupBox("默认排序方式")
        sort_group_layout = QVBoxLayout(sort_group)
        
        # 排序字段选择
        sort_field_layout = QHBoxLayout()
        sort_field_label = QLabel("排序字段:")
        self.default_sort_combo = QComboBox()
        self.default_sort_combo.addItems(["修改时间", "文件名", "文件大小", "文件类型", "所在文件夹"])
        
        sort_field_layout.addWidget(sort_field_label)
        sort_field_layout.addWidget(self.default_sort_combo, 1)
        sort_group_layout.addLayout(sort_field_layout)
        
        # 排序顺序选择
        sort_order_layout = QHBoxLayout()
        sort_order_label = QLabel("排序顺序:")
        self.default_sort_asc_radio = QRadioButton("升序")
        self.default_sort_desc_radio = QRadioButton("降序")
        self.default_sort_desc_radio.setChecked(True)  # 默认降序
        
        sort_order_layout.addWidget(sort_order_label)
        sort_order_layout.addWidget(self.default_sort_asc_radio)
        sort_order_layout.addWidget(self.default_sort_desc_radio)
        sort_order_layout.addStretch()
        sort_group_layout.addLayout(sort_order_layout)
        
        # 隐藏排序设置组（仅保留控件引用以便在_load_settings和_apply_settings中使用）
        sort_group.setVisible(False)
        interface_group_layout.addWidget(sort_group)
        # ----------------------------------

        # --- Add Containers to Main Layout ---
        layout.addWidget(self.index_settings_widget)
        layout.addWidget(self.search_settings_widget)
        layout.addWidget(self.interface_settings_widget)
        layout.addStretch(1) # Add stretch here to push groups up

        # --- Set Visibility Based on Category ---
        self.index_settings_widget.setVisible(category_to_show == 'all' or category_to_show == 'index')
        self.search_settings_widget.setVisible(category_to_show == 'all' or category_to_show == 'search')
        self.interface_settings_widget.setVisible(category_to_show == 'all' or category_to_show == 'interface')

        # --- Dialog Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply) # Add Apply button
        button_box.accepted.connect(self.accept) # OK closes and saves
        button_box.rejected.connect(self.reject) # Cancel closes without saving
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings) # Apply saves without closing
        layout.addWidget(button_box)

        # --- Connections ---\
        self.browse_index_button.clicked.connect(self._browse_index_directory)
        self.add_source_dir_button.clicked.connect(self._browse_add_source_directory)
        # 注意：remove_source_dir_button 的连接已在创建按钮时完成，避免重复连接

        # --- Load Initial Settings (Load all, visibility handles display) ---\
        self._load_settings()

    def _browse_index_directory(self):
        current_dir = self.index_dir_entry.text()
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择索引存储位置",
            current_dir or str(Path.home()) # Default to home if empty
        )
        if directory:
            self.index_dir_entry.setText(directory)

    # --- ADDED: Method to add source directory ---
    def _browse_add_source_directory(self):
        # --- ADDED: 检查源目录数量限制 ---
        current_dirs_count = self.source_dirs_list.count()
        # 只有在免费版下才限制源目录数量
        if not self.license_manager.is_feature_available(Features.UNLIMITED_DIRS):
            max_dirs = 5  # 免费版最多允许 5 个源目录
            if current_dirs_count >= max_dirs:
                QMessageBox.warning(
                    self, 
                    "达到免费版限制", 
                    f"免费版最多支持 {max_dirs} 个源目录。\n\n"
                    f"请升级到专业版以添加无限制的源目录。"
                )
                return
        # -----------------------------
        
        # Determine a sensible starting directory
        last_added_dir = ""
        if self.source_dirs_list.count() > 0:
            last_added_dir = self.source_dirs_list.item(self.source_dirs_list.count() - 1).text()
        start_dir = last_added_dir or str(Path.home())

        directory = QFileDialog.getExistingDirectory(
            self,
            "选择要索引的文件夹",
            start_dir
        )
        if directory:
            # Check if already exists (case-insensitive on Windows, case-sensitive elsewhere)
            items = [self.source_dirs_list.item(i).text() for i in range(self.source_dirs_list.count())]
            is_windows = sys.platform == "win32"
            normalized_dir = os.path.normpath(directory)

            already_exists = False
            for item in items:
                normalized_item = os.path.normpath(item)
                if is_windows:
                    if normalized_item.lower() == normalized_dir.lower():
                        already_exists = True
                        break
                else:
                    if normalized_item == normalized_dir:
                         already_exists = True
                         break

            if not already_exists:
                 # Use normalized path for consistency
                 self.source_dirs_list.addItem(normalized_dir)
            else:
                 QMessageBox.information(self, "提示", f"文件夹 '{directory}' 已经在列表中了。")

    # --- ADDED: Method to remove selected source directories ---
    def _remove_selected_source_directory(self):
        selected_items = self.source_dirs_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先在列表中选中要移除的文件夹。")
            return

        confirm = QMessageBox.question(self, "确认移除",
                                       f"确定要从索引列表中移除选中的 {len(selected_items)} 个文件夹吗？\\n"
                                       f"(注意：这不会删除实际文件夹，仅将其从索引范围移除。\\n"
                                       f"下次索引更新时，这些文件夹的内容将被删除。)",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if confirm == QMessageBox.Yes:
            # 收集要移除的项目文本，避免在移除过程中索引变化
            items_to_remove = [(item, self.source_dirs_list.row(item)) for item in selected_items]

            # 按行号从大到小排序，确保移除时不会影响索引
            items_to_remove.sort(key=lambda x: x[1], reverse=True)

            for item, row in items_to_remove:
                self.source_dirs_list.takeItem(row)
                print(f"DEBUG: 已移除源目录: {item.text()}")

            print(f"DEBUG: 成功移除 {len(selected_items)} 个源目录")

    def _load_settings(self):
        """Load all settings from QSettings"""
        # Source Directories
        source_dirs = self.settings.value("indexing/sourceDirectories", [], type=list)
        self.source_dirs_list.clear()
        for directory in source_dirs:
            self.source_dirs_list.addItem(directory)

        # OCR Setting
        ocr_enabled = self.settings.value("indexing/enableOcr", True, type=bool)
        self.enable_ocr_checkbox.setChecked(ocr_enabled)
        
        # --- ADDED: Load File Type Settings ---
        # 获取已保存的文件类型设置，如果没有则默认全选
        selected_file_types = self.settings.value("indexing/selectedFileTypes", [], type=list)
        print("DEBUG: 从设置加载文件类型 =", selected_file_types)
        
        # 只有在首次运行（返回None）或格式不正确时才设置为默认全选
        # 当设置中存储的是空列表时，保持为空列表
        if selected_file_types is None or not isinstance(selected_file_types, list):
            selected_file_types = list(self.file_type_checkboxes.keys())
            print("DEBUG: 设置为默认全选 =", selected_file_types)
        
        # 保存选中的文件类型到成员变量
        self.selected_file_types = selected_file_types
        print("DEBUG: 设置 self.selected_file_types =", self.selected_file_types)

        # --- ADDED: Load File Type Modes Settings ---
        # 获取已保存的文件类型模式设置，如果没有则默认都为完整索引
        saved_file_type_modes = self.settings.value("indexing/fileTypeModes", {})
        print("DEBUG: 从设置加载文件类型模式 =", saved_file_type_modes)

        # 为所有文件类型设置模式（多媒体文件强制为仅文件名，其他使用保存的设置）
        supported_types = {
            'txt': {'display': '📝 文本文件 (.txt)', 'pro_feature': None},
            'docx': {'display': '📄 Word文档 (.docx)', 'pro_feature': None},
            'xlsx': {'display': '📊 Excel表格 (.xlsx)', 'pro_feature': None},
            'pptx': {'display': '📺 PowerPoint演示文稿 (.pptx)', 'pro_feature': None},
            'pdf': {'display': '📋 PDF文档 (.pdf)', 'pro_feature': Features.PDF_SUPPORT},
            'html': {'display': '🌐 HTML网页 (.html, .htm)', 'pro_feature': None},
            'rtf': {'display': '📄 RTF富文本 (.rtf)', 'pro_feature': None},
            'md': {'display': '📝 Markdown文档 (.md)', 'pro_feature': Features.MARKDOWN_SUPPORT},
            'eml': {'display': '📧 电子邮件 (.eml)', 'pro_feature': Features.EMAIL_SUPPORT},
            'msg': {'display': '📧 Outlook邮件 (.msg)', 'pro_feature': Features.EMAIL_SUPPORT},
            'zip': {'display': '🗜️ ZIP压缩包 (.zip)', 'pro_feature': None},
            'rar': {'display': '🗜️ RAR压缩包 (.rar)', 'pro_feature': None},
            'mp4': {'display': '🎬 视频文件 (.mp4, .mkv, .avi等)', 'pro_feature': None, 'filename_only': True},
            'mp3': {'display': '🎵 音频文件 (.mp3, .wav, .flac等)', 'pro_feature': None, 'filename_only': True},
            'jpg': {'display': '🖼️ 图片文件 (.jpg, .png, .gif等)', 'pro_feature': None, 'filename_only': True},
        }

        for type_key, mode_combo in self.file_type_modes.items():
            # 检查是否为多媒体文件类型
            type_info = supported_types.get(type_key, {})
            is_multimedia = type_info.get('filename_only', False)

            if is_multimedia:
                # 多媒体文件强制设置为"仅文件名"
                mode_combo.setCurrentIndex(1)  # 仅文件名
                mode_combo.setEnabled(False)   # 禁用选择
                print(f"DEBUG: 设置多媒体文件类型 {type_key} 强制为 filename_only")
            else:
                # 非多媒体文件使用保存的设置
                saved_mode = saved_file_type_modes.get(type_key, "full")  # 默认完整索引
                if saved_mode == "filename_only":
                    mode_combo.setCurrentIndex(1)  # 仅文件名
                else:
                    mode_combo.setCurrentIndex(0)  # 完整索引
                print(f"DEBUG: 设置文件类型 {type_key} 的模式为 {saved_mode}")
        # ----------------------------------------------
        
        # 暂时阻断复选框信号
        for checkbox in self.file_type_checkboxes.values():
            checkbox.blockSignals(True)
        
        # 设置复选框状态
        enabled_checkboxes_count = 0
        checked_enabled_count = 0
        for checkbox, type_value in self.file_type_checkboxes.items():
            if checkbox.isEnabled():  # 只处理可用的复选框
                enabled_checkboxes_count += 1
                is_checked = type_key in selected_file_types
                checkbox.setChecked(is_checked)
                if is_checked:
                    checked_enabled_count += 1
                print(f"DEBUG: 设置复选框 {type_key} = {is_checked} (可用: {checkbox.isEnabled()})")
        
        # 恢复复选框信号
        for checkbox in self.file_type_checkboxes.values():
            checkbox.blockSignals(False)
        
        # 检查是否全选了，并更新全选复选框状态
        all_enabled_checked = checked_enabled_count == enabled_checkboxes_count
        print(f"DEBUG: 所有可用均被选中: {all_enabled_checked} ({checked_enabled_count}/{enabled_checkboxes_count})")
        
        # 阻断全选复选框信号
        self.select_all_types_checkbox.blockSignals(True)
        self.select_all_types_checkbox.setChecked(all_enabled_checked)
        self.select_all_types_checkbox.blockSignals(False)
        # ---------------------------------
        
        # Index Directory
        default_index_path = str(Path.home() / "Documents" / "DocumentSearchIndex")
        index_dir = self.settings.value("indexing/indexDirectory", default_index_path)
        self.index_dir_entry.setText(index_dir or default_index_path)
        
        # --- ADDED: Extraction Timeout ---
        extraction_timeout = self.settings.value("indexing/extractionTimeout", 120, type=int)
        self.extraction_timeout_spinbox.setValue(extraction_timeout)
        # ------------------------------
        
        # --- ADDED: TXT Content Limit ---
        txt_content_limit = self.settings.value("indexing/txtContentLimitKb", 0, type=int)
        self.txt_content_limit_spinbox.setValue(txt_content_limit)
        # ------------------------------
        
        # Search Settings
        case_sensitive = self.settings.value("search/caseSensitive", False, type=bool)
        self.case_sensitive_checkbox.setChecked(case_sensitive)
        
        # --- ADDED: Size filter settings ---
        min_size = self.settings.value("search/minSizeKb", "", type=str)
        max_size = self.settings.value("search/maxSizeKb", "", type=str)
        self.min_size_entry.setText(min_size)
        self.max_size_entry.setText(max_size)
        # --------------------------------
        
        # --- ADDED: Date filter settings ---
        start_date_str = self.settings.value("search/startDate", "", type=str)
        end_date_str = self.settings.value("search/endDate", "", type=str)
        
        if start_date_str:
            start_date = QDate.fromString(start_date_str, "yyyy-MM-dd")
            if start_date.isValid():
                self.start_date_edit.setDate(start_date)
        else:
            # 默认设置为远过去的日期
            self.start_date_edit.setDate(QDate(1900, 1, 1))
            
        if end_date_str:
            end_date = QDate.fromString(end_date_str, "yyyy-MM-dd")
            if end_date.isValid():
                self.end_date_edit.setDate(end_date)
        else:
            # 默认设置为当前日期
            self.end_date_edit.setDate(QDate.currentDate())
        # ---------------------------------
        
        # Populate Theme ComboBox
        theme_name = self.settings.value("interface/theme", "默认", type=str)
        # 设置默认主题（如果没有设置或设置无效）
        if not theme_name in self.theme_files:
            theme_name = "默认"
        
        # 设置主题下拉框的当前选项
        theme_index = self.theme_combo.findText(theme_name)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
            
        # --- ADDED: Font Size Settings ---
        font_size = self.settings.value("interface/resultFontSize", 10, type=int)
        self.result_font_size_spinbox.setValue(font_size)
        # --------------------------------
        
        # --- ADDED: Default Sort Settings ---
        sort_field = self.settings.value("interface/defaultSortField", "修改时间", type=str)
        sort_order = self.settings.value("interface/defaultSortOrder", "降序", type=str)
        
        sort_field_index = self.default_sort_combo.findText(sort_field)
        if sort_field_index >= 0:
            self.default_sort_combo.setCurrentIndex(sort_field_index)
            
        if sort_order == "升序":
            self.default_sort_asc_radio.setChecked(True)
        else:
            self.default_sort_desc_radio.setChecked(True)
        # -----------------------------------

        # 阻断全选复选框信号
        self.select_all_types_checkbox.blockSignals(True)
        self.select_all_types_checkbox.setChecked(all_enabled_checked)
        self.select_all_types_checkbox.blockSignals(False)
        
        # 确保选中状态与当前复选框状态一致
        current_selected = self._save_current_file_types()
        if set(current_selected) != set(self.selected_file_types):
            print(f"DEBUG: 更新 self.selected_file_types 以匹配当前复选框状态")
            self.selected_file_types = current_selected
        # ---------------------------------

    def _apply_settings(self):
        """Apply all settings from the dialog to QSettings"""
        # Source Directories
        source_dirs = []
        for i in range(self.source_dirs_list.count()):
            source_dirs.append(self.source_dirs_list.item(i).text())
        self.settings.setValue("indexing/sourceDirectories", source_dirs)
        
        # OCR Setting
        ocr_enabled = self.enable_ocr_checkbox.isChecked()
        self.settings.setValue("indexing/enableOcr", ocr_enabled)
        
        # --- ADDED: Save File Types Settings ---
        selected_file_types = self._save_current_file_types()
        print(f"DEBUG: _apply_settings 保存文件类型 = {selected_file_types}")
        self.settings.setValue("indexing/selectedFileTypes", selected_file_types)

        # --- ADDED: Save File Type Modes Settings ---
        file_type_modes = self._save_current_file_type_modes()
        print(f"DEBUG: _apply_settings 保存文件类型模式 = {file_type_modes}")
        self.settings.setValue("indexing/fileTypeModes", file_type_modes)
        # ------------------------------------------
        
        # Index Directory
        index_dir = self.index_dir_entry.text().strip()
        self.settings.setValue("indexing/indexDirectory", index_dir)
        
        # --- ADDED: Extraction Timeout ---
        extraction_timeout = self.extraction_timeout_spinbox.value()
        self.settings.setValue("indexing/extractionTimeout", extraction_timeout)
        # -----------------------------
        
        # --- ADDED: TXT Content Limit ---
        txt_content_limit = self.txt_content_limit_spinbox.value()
        self.settings.setValue("indexing/txtContentLimitKb", txt_content_limit)
        # -----------------------------
        
        # Search Settings
        case_sensitive = self.case_sensitive_checkbox.isChecked()
        self.settings.setValue("search/caseSensitive", case_sensitive)
        
        # --- ADDED: Size filter settings ---
        min_size = self.min_size_entry.text().strip()
        max_size = self.max_size_entry.text().strip()
        self.settings.setValue("search/minSizeKb", min_size)
        self.settings.setValue("search/maxSizeKb", max_size)
        # --------------------------------
        
        # --- ADDED: Date filter settings ---
        # 只有当日期不是默认值时才保存
        if self.start_date_edit.date() != QDate(1900, 1, 1):
            start_date_str = self.start_date_edit.date().toString("yyyy-MM-dd")
            self.settings.setValue("search/startDate", start_date_str)
        else:
            self.settings.setValue("search/startDate", "")
            
        if self.end_date_edit.date() != QDate.currentDate():
            end_date_str = self.end_date_edit.date().toString("yyyy-MM-dd")
            self.settings.setValue("search/endDate", end_date_str)
        else:
            self.settings.setValue("search/endDate", "")
        # ---------------------------------
            
        # Interface Settings - Theme
        theme_name = self.theme_combo.currentText()
        self.settings.setValue("interface/theme", theme_name)
        
        # 应用所选主题
        if self.parent():
            self.parent().apply_theme(theme_name)
            
        # --- ADDED: Font Size Settings ---
        font_size = self.result_font_size_spinbox.value()
        self.settings.setValue("interface/resultFontSize", font_size)
        
        # 应用字体大小
        if self.parent():
            self.parent()._apply_result_font_size()
        # --------------------------------
        
        # --- ADDED: Default Sort Settings ---
        sort_field = self.default_sort_combo.currentText()
        sort_order = "升序" if self.default_sort_asc_radio.isChecked() else "降序"
        
        self.settings.setValue("interface/defaultSortField", sort_field)
        self.settings.setValue("interface/defaultSortOrder", sort_order)
        
        # 应用默认排序
        if self.parent():
            self.parent()._load_and_apply_default_sort()
        # -----------------------------------

    # Override accept() to apply settings before closing
    def accept(self):
        self._apply_settings() # Apply settings first
        super().accept() # Then close the dialog

    # Override reject() to make sure no changes are inadvertently kept (though load reloads)
    def reject(self):
        print("Settings changes rejected.")
        super().reject()

    def _clear_dates(self):
        """清除日期筛选，恢复为默认值"""
        self.start_date_edit.setDate(QDate(1900, 1, 1))
        self.end_date_edit.setDate(QDate.currentDate())

    def _toggle_all_file_types(self, state):
        """处理全选复选框状态变更"""
        # 获取当前状态 - 注意：这里要使用传入的state参数，而不是直接获取复选框状态
        # Qt.Checked = 2, Qt.Unchecked = 0, Qt.PartiallyChecked = 1
        # 直接使用数值2表示选中状态
        is_checked = (state == 2)  # 明确使用数值2表示选中状态
        
        print(f"DEBUG: 全选复选框状态变更: 设置所有复选框为 {is_checked} (状态值: {state})")
        
        # 防止设置复选框状态时触发信号循环
        self.select_all_types_checkbox.blockSignals(True)
        
        enabled_count = 0
        checked_count = 0
        # 遍历所有文件类型复选框
        for checkbox, type_value in self.file_type_checkboxes.items():
            # 只处理启用的复选框（即可用的文件类型）
            if checkbox.isEnabled():
                enabled_count += 1
                checkbox.blockSignals(True)  # 阻止复选框状态改变触发信号
                checkbox.setChecked(is_checked)  # 使用传入的状态
                checkbox.blockSignals(False)  # 恢复信号连接
                if is_checked:
                    checked_count += 1
                print(f"DEBUG: 设置复选框 {type_key} = {is_checked}")
        
        print(f"DEBUG: 总共处理了 {enabled_count} 个可用复选框，设置了 {checked_count} 个为选中状态")
        
        # 直接更新选中的文件类型列表，不通过_save_current_file_types方法
        if is_checked:
            # 如果是全选，直接创建所有可用类型的列表
            selected_types = []
            for checkbox, type_value in self.file_type_checkboxes.items():
                if checkbox.isEnabled():
                    selected_types.append(type_key)
            self.selected_file_types = selected_types
        else:
            # 如果是取消选中，则为空列表
            self.selected_file_types = []
            
        print(f"DEBUG: 直接更新 self.selected_file_types = {self.selected_file_types}")
        
        # 恢复信号连接
        self.select_all_types_checkbox.blockSignals(False)

    def _save_current_file_types(self):
        """收集当前勾选的文件类型并返回列表"""
        selected_types = []
        for checkbox, type_value in self.file_type_checkboxes.items():
            if checkbox.isChecked():
                selected_types.append(type_key)
                print(f"DEBUG: 复选框 {type_key} 被选中")
        
        print(f"DEBUG: _save_current_file_types 返回 {len(selected_types)} 个选中类型")
        return selected_types

    def _save_current_file_type_modes(self):
        """收集当前文件类型的索引模式并返回字典"""
        file_type_modes = {}
        for type_key, mode_combo in self.file_type_modes.items():
            selected_mode = mode_combo.currentData()  # 获取当前选中项的data值
            file_type_modes[type_key] = selected_mode
            print(f"DEBUG: 文件类型 {type_key} 的索引模式 = {selected_mode}")

        print(f"DEBUG: _save_current_file_type_modes 返回字典 = {file_type_modes}")
        return file_type_modes

    def _update_button_states(self):
        """更新应用按钮状态"""
        # 应用按钮始终可用，不再检查是否有文件类型被选中
        self.apply_button.setEnabled(True)
    
    def _apply_selection(self):
        """应用当前选择的文件类型"""
        # 保存当前勾选的文件类型
        self.selected_file_types = self._save_current_file_types()
        print(f"DEBUG: _apply_selection 更新 self.selected_file_types = {self.selected_file_types}")
        
        # 判断是否没有选择任何文件类型
        if len(self.selected_file_types) == 0:
            # 如果没有选择任何文件类型，恢复为默认全部可用文件类型
            enabled_types = []
            for checkbox, type_value in self.file_type_checkboxes.items():
                if checkbox.isEnabled():
                    enabled_types.append(type_key)
            
            self.selected_file_types = enabled_types
            print(f"DEBUG: 未选择任何文件类型，自动恢复为全选可用类型: {len(self.selected_file_types)} 个")
            
            # 更新UI以反映变化，但由于对话框即将关闭，这一步可能看不到效果
            try:
                # 阻断全选复选框信号
                self.select_all_types_checkbox.blockSignals(True)
                
                # 更新复选框状态，逐个设置为选中
                for checkbox, type_value in self.file_type_checkboxes.items():
                    if checkbox.isEnabled():
                        checkbox.blockSignals(True)
                        checkbox.setChecked(True)
                        checkbox.blockSignals(False)
                
                # 更新全选复选框状态
                self.select_all_types_checkbox.setCheckState(Qt.Checked)
                self.select_all_types_checkbox.blockSignals(False)
            except Exception as e:
                print(f"DEBUG: 更新UI反映全选状态时出错: {e}")
        
        # 保存选中的文件类型
        self.settings.setValue("indexing/selectedFileTypes", self.selected_file_types)
        print(f"DEBUG: _apply_selection 保存到设置中 'indexing/selectedFileTypes' = {self.selected_file_types}")
        
        # 发出信号通知选择已更改
        self.fileTypesSelectionChanged.emit(self.selected_file_types)
        
        # 显示确认消息
        source_dirs = self.settings.value("indexing/sourceDirectories", [], type=list)
        enabled_count = 0
        for checkbox in self.file_type_checkboxes.values():
            if checkbox.isEnabled():
                enabled_count += 1
        
        if len(self.selected_file_types) == 0:
            msg = "警告：未选择任何文件类型，已自动恢复为全选"
            print(f"DEBUG: {msg}")
        elif len(self.selected_file_types) == enabled_count:
            msg = "已应用搜索范围：将搜索所有可用文件类型"
            print(f"DEBUG: {msg}")
        else:
            msg = f"已应用搜索范围：将只搜索所选的 {len(self.selected_file_types)} 个文件类型"
            print(f"DEBUG: {msg}")
        
        if self.parent():
            self.parent().statusBar().showMessage(msg, 3000)
        
        self.accept()

    def _update_select_all_checkbox_state(self):
        """当文件类型复选框状态改变时更新全选复选框状态"""
        # 暂时阻断信号，防止循环触发
        self.select_all_types_checkbox.blockSignals(True)
        
        # 检查是否所有可用的复选框都被选中
        enabled_count = 0
        checked_count = 0
        for checkbox in self.file_type_checkboxes.values():
            if checkbox.isEnabled():
                enabled_count += 1
                if checkbox.isChecked():
                    checked_count += 1
        
        all_checked = enabled_count > 0 and checked_count == enabled_count
        print(f"DEBUG: 更新全选复选框状态: {all_checked} ({checked_count}/{enabled_count})")
        
        # 设置全选复选框状态
        self.select_all_types_checkbox.setChecked(all_checked)
        
        # 恢复信号连接
        self.select_all_types_checkbox.blockSignals(False)
        
        # 保存当前选中状态到内存变量（不直接保存到设置中）
        self.selected_file_types = self._save_current_file_types()

# --- Main GUI Window ---
# --- UI设计规范常量 ---
UI_CONSTANTS = {
    # 字体设置
    'FONT_SIZE_NORMAL': '12px',      # 标准字体大小
    'FONT_SIZE_SMALL': '11px',       # 小字体大小
    'FONT_SIZE_LARGE': '14px',       # 大字体大小
    'FONT_SIZE_ICON': '14px',        # 图标字体大小
    
    # 控件尺寸
    'BUTTON_HEIGHT': 28,             # 标准按钮高度
    'INPUT_HEIGHT': 28,              # 输入框高度
    'COMBO_HEIGHT': 28,              # 下拉框高度
    'ICON_SIZE': 16,                 # 标准图标尺寸
    
    # 间距设置
    'SPACING_SMALL': 6,              # 小间距
    'SPACING_NORMAL': 8,             # 标准间距
    'SPACING_LARGE': 12,             # 大间距
    'MARGIN_SMALL': 4,               # 小边距
    'MARGIN_NORMAL': 6,              # 标准边距
    
    # 圆角设置
    'BORDER_RADIUS_SMALL': 4,        # 小圆角
    'BORDER_RADIUS_NORMAL': 6,       # 标准圆角
    
    # 配色方案 - 现代渐变色系
    'COLORS': {
        # 主要操作按钮 - 蓝绿渐变系
        'PRIMARY': '#00BCD4',           # 青色主色
        'PRIMARY_HOVER': '#00ACC1',     # 青色悬停
        'PRIMARY_PRESSED': '#0097A7',   # 青色按下
        
        # 成功操作按钮 - 绿色系
        'SUCCESS': '#4CAF50',           # 绿色主色  
        'SUCCESS_HOVER': '#45A049',     # 绿色悬停
        'SUCCESS_PRESSED': '#3D8B40',   # 绿色按下
        
        # 警告操作按钮 - 橙色系
        'WARNING': '#FF9800',           # 橙色主色
        'WARNING_HOVER': '#F57C00',     # 橙色悬停  
        'WARNING_PRESSED': '#E65100',   # 橙色按下
        
        # 危险操作按钮 - 红色系
        'DANGER': '#F44336',            # 红色主色
        'DANGER_HOVER': '#E53935',      # 红色悬停
        'DANGER_PRESSED': '#C62828',    # 红色按下
        
        # 信息操作按钮 - 蓝色系
        'INFO': '#2196F3',              # 蓝色主色
        'INFO_HOVER': '#1E88E5',        # 蓝色悬停
        'INFO_PRESSED': '#1565C0',      # 蓝色按下
        
        # 次要操作按钮 - 紫色系
        'SECONDARY': '#9C27B0',         # 紫色主色
        'SECONDARY_HOVER': '#8E24AA',   # 紫色悬停
        'SECONDARY_PRESSED': '#7B1FA2', # 紫色按下
    },
    
    # 图标定义
    'ICONS': {
        'search': '🔍',
        'clear': '✖️',
        'help': '❓',
        'settings': '⚙️',
        'index': '📚',
        'cancel': '⏹️',
        'files': '📄',
        'list': '📄',
        'time': '⏰',
        'type': '📁',
        'folder': '🗂️',
        'range': '📍',
        'mode': '🎯',
        'view': '👁️'
    }
}

def create_button_style(color_type='PRIMARY'):
    """创建统一的按钮样式
    
    Args:
        color_type: 颜色类型，可选值：PRIMARY, SUCCESS, WARNING, DANGER, INFO, SECONDARY
    """
    colors = UI_CONSTANTS['COLORS']
    return f"""
        QPushButton {{
            font-weight: bold;
            background-color: {colors[color_type]};
            color: white;
            border: none;
            border-radius: {UI_CONSTANTS['BORDER_RADIUS_SMALL']}px;
            padding: {UI_CONSTANTS['MARGIN_SMALL']}px {UI_CONSTANTS['MARGIN_NORMAL']}px;
            font-size: {UI_CONSTANTS['FONT_SIZE_NORMAL']};
        }}
        QPushButton:hover {{
            background-color: {colors[f'{color_type}_HOVER']};
        }}
        QPushButton:pressed {{
            background-color: {colors[f'{color_type}_PRESSED']};
        }}
    """

class MainWindow(QMainWindow):  # Changed base class to QMainWindow
    # Signal to trigger indexing in the worker thread
    # --- MODIFIED: Add file_types_to_index parameter ---
    startIndexingSignal = Signal(list, str, bool, int, int, object) # source_dirs, index_dir, enable_ocr, timeout, txt_limit_kb, file_types_to_index
    # ---------------------------------------------------------
    # Signal to trigger search in the worker thread (add types for size, date, file type, and case sensitivity)
    startSearchSignal = Signal(str, str, object, object, object, object, object, str, bool, str, object, int, int) # Added page_number and page_size parameters
    # --- ADDED: Signal for update check --- 
    startUpdateCheckSignal = Signal(str, str) # current_version, update_url
    # ----------------------------------------

    def __init__(self):
        super().__init__()
        self.setWindowTitle("文智搜 (PySide6)")
        self.setMinimumSize(600, 450) # ADDED: Set a minimum window size
        
        # --- 设置窗口图标 ---
        try:
            icon_path = get_resource_path("app_icon.ico")
            self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"设置窗口图标时发生错误: {e}")
        # -------------------

        # --- Initialize Config (using QSettings) --- 
        self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        
        # --- 初始化许可证管理器（放在所有UI元素创建之前) ---
        self.license_manager = get_license_manager()
        
        self.MAX_HISTORY_ITEMS = 10 # Max number of search history items
        self.worker_thread = None # Initialize worker_thread to None
        self.worker = None
        self.search_results = [] # Store current search results (Displayed/Filtered)
        # --- ADD MISSING INITIALIZATIONS --- 
        self.original_search_results = [] # Stores results directly from backend before filtering/sorting
        self.is_busy = False # Flag to prevent concurrent operations
        self.collapse_states = {} # Stores {key: is_collapsed (bool)} for result display
        self.blocking_filter_update = False # Flag to temporarily block filter updates
        # ----------------------------------
        self.current_sort_key = 'score' # Default sort key
        self.current_sort_descending = True # Default sort order
        self.last_search_scope = 'fulltext' # ADDED: Store last search scope, default to fulltext
        self.skipped_files_dialog = None # ADDED: Initialize skipped files dialog instance
        
        # --- 添加文件夹树与搜索结果的过滤变量 ---
        self.filtered_by_folder = False  # 是否按文件夹进行了过滤
        self.current_filter_folder = None  # 当前过滤的文件夹路径
        # ---------------------------------------
        
        # --- 添加索引目录搜索变量 ---
        self.search_directories = []  # 存储用户选择的搜索目录
        self.index_directories_dialog = None  # 索引目录对话框
        # ---------------------------
        
<<<<<<< HEAD
        # --- 添加防抖搜索功能变量 ---
        self.search_debounce_timer = QTimer()
        self.search_debounce_timer.setSingleShot(True)
        self.debounce_delay = 300  # 300毫秒防抖延迟
        self.min_search_length = 2  # 最小搜索长度
        self.instant_search_enabled = False  # 即时搜索默认禁用
        self.last_search_text = ""  # 上次搜索文本
        # ---------------------------
        
        # --- 添加分组功能变量 ---
        self.grouping_enabled = False  # 分组功能默认禁用
        self.current_grouping_mode = 'none'  # 当前分组模式
        self.group_data = {}  # 分组数据
        self.group_collapse_states = {}  # 分组折叠状态
        # -------------------------
        
        # --- 添加查看方式功能变量 ---
        self.current_view_mode = 0  # 默认为列表视图
        # -------------------------
        

        
        # --- 即时搜索和防抖功能初始化 ---
        self.instant_search_enabled = True  # 默认启用即时搜索
        self.min_search_length = 2  # 最小搜索长度
        self.debounce_delay = 500   # 防抖延迟（毫秒）
        self.last_search_text = ""  # 上次搜索文本
        self._setting_text_from_history = False  # 标志：是否正在从历史记录设置文本
        self._history_selection_in_progress = False  # 标志：历史记录选择进行中
        
        # 创建防抖计时器
        self.search_debounce_timer = QTimer()
        self.search_debounce_timer.setSingleShot(True)
        self.search_debounce_timer.timeout.connect(self._perform_debounced_search)
        # --------------------------------------------

        # --- 主题管理系统初始化 ---
        self.current_theme = "现代蓝"  # 保持兼容性
        self.theme_manager = ThemeManager("现代蓝")  # 创建统一主题管理器
        # ---------------------------
=======
        # --- 添加分页相关属性 ---
        self.current_page = 1
        self.page_size = 50
        self.total_pages = 0
        self.total_count = 0
        self.current_search_params = {}
        self.pagination_enabled = True  # 是否启用分页功能
        # -------------------------
>>>>>>> 205d800b1db2b33deca56ba17897fa8699e7318f

        # --- Central Widget and Main Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # --- 移动操作按钮到搜索框上方 ---
        # --- Action Buttons (移至搜索框上方) ---
        action_layout = self._create_action_buttons()
        main_layout.addLayout(action_layout)
        
        # 添加水平分隔线增强视觉分隔
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # --- Search Bar ---
        search_bar_layout = self._create_search_bar()
        main_layout.addLayout(search_bar_layout)

        # --- Filters ---
        # 移除文件大小筛选条件
        # 移除修改日期筛选条件
        view_mode_layout = self._create_view_mode_bar() # 整合排序和分组功能
        main_layout.addLayout(view_mode_layout)
        type_filter_layout = self._create_type_filter_bar() # Assume helper exists
        main_layout.addLayout(type_filter_layout)
        
        # --- 不再需要在此处添加操作按钮 ---
        # --- Action Buttons ---
        # action_layout = self._create_action_buttons() # Assume helper exists
        # main_layout.addLayout(action_layout)

        # --- 创建水平分隔器，添加文件夹树视图和搜索结果 ---
        self.main_splitter = QSplitter(Qt.Horizontal)
        # 设置分隔器手柄样式
        self.main_splitter.setHandleWidth(5)
        self.main_splitter.setChildrenCollapsible(False)
        
        # 创建左侧容器（文件夹树及其标题）
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # 创建右侧容器（搜索结果及其标题）
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # 添加左侧标题和文件夹树
        left_title = QLabel("文件夹结构")
        left_title.setAlignment(Qt.AlignCenter)
        left_title.setStyleSheet("background-color: #F0F0F0; padding: 5px;")
        self.folder_tree = FolderTreeWidget(title_visible=False)  # 不在内部显示标题，由外部控制
        
        left_layout.addWidget(left_title)
        left_layout.addWidget(self.folder_tree)
        
        # 添加右侧标题和搜索结果
        right_title = QLabel("搜索结果")
        right_title.setAlignment(Qt.AlignCenter)
        right_title.setStyleSheet("background-color: #F0F0F0; padding: 5px;")
        
        # 添加搜索警告标签（结果截断提示）
        self.search_warning_label = QLabel()
        self.search_warning_label.setVisible(False)  # 默认隐藏
        self.search_warning_label.setWordWrap(True)  # 允许文字换行
        self.search_warning_label.setStyleSheet("""
            QLabel {
                background-color: #FFF3CD;
                color: #856404;
                border: 1px solid #FFEAA7;
                border-radius: 4px;
                padding: 8px;
                margin: 4px;
                font-weight: bold;
            }
        """)
        
        # === 创建搜索结果显示区域 - 支持传统和虚拟滚动 ===
        self.results_text = QTextBrowser() 
        self.results_text.setOpenExternalLinks(False)  # 禁止外部链接自动打开
        self.results_text.setOpenLinks(False)          # 禁止所有链接自动打开，使用信号处理
        self.results_text.setStyleSheet("border: 1px solid #D0D0D0;")

        # 启用右键菜单并设置选择模式
        self.results_text.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_text.customContextMenuRequested.connect(self._show_results_context_menu)
        self.results_text.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard | Qt.LinksAccessibleByMouse)
        
        # 创建虚拟滚动组件
        self.virtual_results_model = VirtualResultsModel(self)
        self.virtual_results_view = VirtualResultsView(self)
        self.virtual_results_view.setModel(self.virtual_results_model)
        self.virtual_results_view.setStyleSheet("border: 1px solid #D0D0D0;")
        
        # 创建结果显示容器，使用QStackedWidget进行切换
        self.results_stack = QStackedWidget()
        self.results_stack.addWidget(self.results_text)         # 索引0: 传统文本浏览器
        self.results_stack.addWidget(self.virtual_results_view) # 索引1: 虚拟滚动视图
        self.results_stack.setCurrentIndex(0)  # 默认使用传统模式
        
        # 虚拟滚动切换阈值
        self.virtual_scroll_threshold = 50  # 超过50个结果时使用虚拟滚动
        
        # --- 创建分页控件 ---
        self.pagination_frame = QFrame()
        self.pagination_frame.setStyleSheet("background-color: #F8F8F8; border-top: 1px solid #D0D0D0;")
        pagination_layout = QHBoxLayout(self.pagination_frame)
        pagination_layout.setContentsMargins(10, 5, 10, 5)
        
        # 上一页按钮
        self.prev_button = QPushButton("上一页")
        self.prev_button.setEnabled(False)
        self.prev_button.clicked.connect(self._go_to_prev_page)
        
        # 页码信息标签
        self.page_info_label = QLabel("第 1 页，共 1 页")
        self.page_info_label.setAlignment(Qt.AlignCenter)
        
        # 下一页按钮
        self.next_button = QPushButton("下一页")
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self._go_to_next_page)
        
        # 每页条数选择
        page_size_label = QLabel("每页显示:")
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["25", "50", "100", "200"])
        self.page_size_combo.setCurrentText("50")
        self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        
        # 跳转到页
        goto_label = QLabel("跳转到:")
        self.goto_page_edit = QLineEdit()
        self.goto_page_edit.setPlaceholderText("页码")
        self.goto_page_edit.setMaximumWidth(60)
        self.goto_page_edit.returnPressed.connect(self._goto_page)
        
        # 布局分页控件
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_info_label)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(page_size_label)
        pagination_layout.addWidget(self.page_size_combo)
        pagination_layout.addWidget(goto_label)
        pagination_layout.addWidget(self.goto_page_edit)
        
        # 默认隐藏分页控件
        self.pagination_frame.setVisible(False)
        # -------------------------
        
        right_layout.addWidget(right_title)
<<<<<<< HEAD
        right_layout.addWidget(self.search_warning_label)  # 添加警告标签
        right_layout.addWidget(self.results_stack)
=======
        right_layout.addWidget(self.results_text)
        right_layout.addWidget(self.pagination_frame)
>>>>>>> 205d800b1db2b33deca56ba17897fa8699e7318f
        
        # 将两个容器添加到分隔器
        self.main_splitter.addWidget(left_container)
        self.main_splitter.addWidget(right_container)
        
        # 设置初始分隔比例 (文件夹树:搜索结果 = 1:3)
        self.main_splitter.setSizes([200, 600])
        
        # 将分隔器添加到主布局
        main_layout.addWidget(self.main_splitter, 1)
        # ----------------------------------------------

        # --- Status Bar ---
        self._setup_status_bar() # Call helper

        # --- Create Menubar --- 
        self._create_menubar()

        # --- 更新菜单和功能可用性（menubar创建后执行） ---
        self._update_pro_menu()
        self._update_feature_availability()
        
        # --- Setup Worker Thread --- 
        self._setup_worker_thread()

        # --- Setup Connections (AFTER UI Elements Created) ---
        self._setup_connections() # Setup AFTER all UI elements are created

        # --- Restore Window Geometry --- 
        # 直接在这里实现窗口几何恢复，而不是调用方法
        geometry = self.settings.value("windowGeometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # --- 检查文件夹树功能是否可用 ---
        folder_tree_available = self.license_manager.is_feature_available(Features.FOLDER_TREE)
        if hasattr(self, 'main_splitter') and hasattr(self, 'folder_tree'):
            # 获取主分隔器中的左侧窗口小部件（应该是包含文件夹树的容器）
            left_container = self.main_splitter.widget(0)
            
            if left_container:
                left_container.setVisible(folder_tree_available)
                
                # 调整分隔器大小
                if folder_tree_available:
                    # 如果显示文件夹树，设置分隔器位置为1/4处
                    self.main_splitter.setSizes([200, 600])
                else:
                    # 如果不显示文件夹树，将宽度设置为0，让右侧搜索结果占满宽度
                    self.main_splitter.setSizes([0, self.main_splitter.width()])
        # ---------------------------------------
        
        # --- Apply Initial Settings (AFTER UI Elements Created) ---
        self.apply_theme(self.settings.value("ui/theme", "系统默认"))
        
        # 确保下拉箭头图标正确显示
        theme_name = self.settings.value("ui/theme", "系统默认")
        self._update_theme_icons(theme_name)
            
        self._load_and_apply_default_sort()
        self._apply_result_font_size()
        self._load_search_history() # NOW safe to call

        # --- ADDED: Setup Shortcuts ---
        self._setup_shortcuts()
        # ----------------------------
        
        # --- REMOVED: Outdated mode buttons state update ---
        # self._update_mode_buttons_state_slot()  # 已删除
        # ------------------------------------------------
        
        # --- 保存和恢复分隔器位置 ---
        splitter_state = self.settings.value("ui/splitterState")
        if splitter_state:
            self.main_splitter.restoreState(splitter_state)
            
        # --- 检查首次启动 ---
        # 使用QTimer确保界面完全加载后再显示引导对话框
        QTimer.singleShot(500, self._check_first_launch)

    def _create_search_bar(self):
        """创建搜索栏 - 使用统一设计规范"""
        # 创建统一样式的容器
        container = QFrame()
        container.setObjectName("search_container")
        container.setStyleSheet(f"""
            QFrame#search_container {{
                background-color: #f0f8f0;
                border: 2px solid #4CAF50;
                border-radius: {UI_CONSTANTS['BORDER_RADIUS_NORMAL']}px;
                padding: {UI_CONSTANTS['MARGIN_NORMAL']}px;
            }}
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(UI_CONSTANTS['SPACING_SMALL'])
        main_layout.setContentsMargins(UI_CONSTANTS['MARGIN_SMALL'], UI_CONSTANTS['MARGIN_SMALL'], 
                                     UI_CONSTANTS['MARGIN_SMALL'], UI_CONSTANTS['MARGIN_SMALL'])
        
        # 第一行：搜索输入 - 统一布局
        input_layout = QHBoxLayout()
        input_layout.setSpacing(UI_CONSTANTS['SPACING_NORMAL'])
        
        search_label = QLabel(UI_CONSTANTS['ICONS']['search'])
        search_label.setFixedSize(UI_CONSTANTS['ICON_SIZE'] + 4, UI_CONSTANTS['INPUT_HEIGHT'])
        search_label.setAlignment(Qt.AlignCenter)
        search_label.setStyleSheet(f"font-size: {UI_CONSTANTS['FONT_SIZE_ICON']};")
        input_layout.addWidget(search_label)
        
        # 搜索输入框 - 统一高度
        self.search_combo = QComboBox()
        self.search_combo.setEditable(True)
        self.search_line_edit = self.search_combo.lineEdit()
        self.search_line_edit.setPlaceholderText("输入搜索词或选择历史记录...")
        self.search_line_edit.setMinimumWidth(200)
        self.search_combo.setFixedHeight(UI_CONSTANTS['INPUT_HEIGHT'])
        input_layout.addWidget(self.search_combo, 2)

        # 搜索按钮 - 使用SUCCESS配色（绿色系）
        self.search_button = QPushButton("搜索")
        self.search_button.setObjectName("search_button")
        self.search_button.setFixedHeight(UI_CONSTANTS['BUTTON_HEIGHT'])
        self.search_button.setMinimumWidth(60)
        self.search_button.setStyleSheet(create_button_style('SUCCESS'))
        input_layout.addWidget(self.search_button)
        
        # 清空按钮 - 使用DANGER配色（红色系）
        self.clear_search_button = QPushButton(UI_CONSTANTS['ICONS']['clear'])
        self.clear_search_button.setFixedHeight(UI_CONSTANTS['BUTTON_HEIGHT'])
        self.clear_search_button.setFixedWidth(UI_CONSTANTS['BUTTON_HEIGHT'])  # 正方形按钮
        self.clear_search_button.setToolTip("清空搜索")
        self.clear_search_button.setStyleSheet(create_button_style('DANGER'))
        input_layout.addWidget(self.clear_search_button)

        # 通配符帮助按钮 - 使用INFO配色（蓝色系）
        wildcard_help_button = QPushButton(UI_CONSTANTS['ICONS']['help'])
        wildcard_help_button.setToolTip("通配符搜索帮助")
        wildcard_help_button.setFixedSize(UI_CONSTANTS['BUTTON_HEIGHT'], UI_CONSTANTS['BUTTON_HEIGHT'])
        # 为圆形按钮特别设置样式
        wildcard_help_button.setStyleSheet(f"""
            QPushButton {{
                font-weight: bold;
                background-color: {UI_CONSTANTS['COLORS']['INFO']};
                color: white;
                border: none;
                border-radius: {UI_CONSTANTS['BUTTON_HEIGHT'] // 2}px;
                font-size: {UI_CONSTANTS['FONT_SIZE_NORMAL']};
            }}
            QPushButton:hover {{
                background-color: {UI_CONSTANTS['COLORS']['INFO_HOVER']};
            }}
            QPushButton:pressed {{
                background-color: {UI_CONSTANTS['COLORS']['INFO_PRESSED']};
            }}
        """)
        wildcard_help_button.clicked.connect(self.show_wildcard_help_dialog)
        input_layout.addWidget(wildcard_help_button)

        main_layout.addLayout(input_layout)
        
        # 第二行：搜索选项 - 统一布局
        options_layout = QHBoxLayout()
        options_layout.setSpacing(UI_CONSTANTS['SPACING_LARGE'])
        
        # 范围选择 - 统一样式
        scope_label = QLabel(f"{UI_CONSTANTS['ICONS']['range']} 范围:")
        scope_label.setStyleSheet(f"font-weight: bold; color: #333; font-size: {UI_CONSTANTS['FONT_SIZE_NORMAL']};")
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["全文", "文件名"])
        self.scope_combo.setFixedHeight(UI_CONSTANTS['COMBO_HEIGHT'])
        self.scope_combo.setMinimumWidth(80)
        options_layout.addWidget(scope_label)
        options_layout.addWidget(self.scope_combo)
        
        # 模式选择 - 统一样式
        mode_label = QLabel(f"{UI_CONSTANTS['ICONS']['mode']} 模式:")
        mode_label.setStyleSheet(f"font-weight: bold; color: #333; font-size: {UI_CONSTANTS['FONT_SIZE_NORMAL']};")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["精确", "模糊"])
        self.mode_combo.setFixedHeight(UI_CONSTANTS['COMBO_HEIGHT'])
        self.mode_combo.setMinimumWidth(80)
        options_layout.addWidget(mode_label)
        options_layout.addWidget(self.mode_combo)
        
        # 添加弹性空间
        options_layout.addStretch(1)
        
        main_layout.addLayout(options_layout)
        
        # 设置容器的布局
        container.setLayout(main_layout)
        
        # 返回紧凑布局
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)  # 移除外边距
        container_layout.addWidget(container)
        return container_layout

    # (Add other _create_* helper methods if they were inline before)
    def _create_view_mode_bar(self):
        """创建查看方式栏 - 使用统一设计规范"""
        # 创建统一的水平布局
        main_layout = QHBoxLayout()
        main_layout.setSpacing(UI_CONSTANTS['SPACING_LARGE'])
        main_layout.setContentsMargins(UI_CONSTANTS['MARGIN_NORMAL'], UI_CONSTANTS['MARGIN_NORMAL'], 
                                     UI_CONSTANTS['MARGIN_NORMAL'], UI_CONSTANTS['MARGIN_NORMAL'])
        
        # 添加统一的背景和边框样式
        container = QFrame()
        container.setObjectName("view_container")
        container.setStyleSheet(f"""
            QFrame#view_container {{
                background-color: #f8f9fa;
                border: 1px solid #C0C0C0;
                border-radius: {UI_CONSTANTS['BORDER_RADIUS_NORMAL']}px;
                padding: {UI_CONSTANTS['MARGIN_SMALL']}px;
            }}
        """)
        
        # === 视图方式选择器 ===
        view_label = QLabel(f"{UI_CONSTANTS['ICONS']['view']} 视图:")
        view_label.setStyleSheet(f"font-weight: bold; color: #333; font-size: {UI_CONSTANTS['FONT_SIZE_NORMAL']};")
        
        self.view_mode_combo = QComboBox()
        # 定义视图方式 - 使用统一图标
        view_modes = [
            f"{UI_CONSTANTS['ICONS']['list']} 列表视图",        # 默认：不分组
            f"{UI_CONSTANTS['ICONS']['time']} 时间视图",        # 按修改日期分组
            f"{UI_CONSTANTS['ICONS']['type']} 类型视图",        # 按文件类型分组  
            f"{UI_CONSTANTS['ICONS']['folder']} 文件夹视图",      # 按文件夹分组
        ]
        
        self.view_mode_combo.addItems(view_modes)
        self.view_mode_combo.setCurrentIndex(0)  # 默认选择列表视图
        self.view_mode_combo.setFixedHeight(UI_CONSTANTS['COMBO_HEIGHT'])
        self.view_mode_combo.setMinimumWidth(140)
        
        main_layout.addWidget(view_label)
        main_layout.addWidget(self.view_mode_combo)
        
        # 添加垂直分隔线
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setFixedWidth(1)
        separator1.setMaximumHeight(20)
        separator1.setStyleSheet("QFrame { color: #C0C0C0; }")
        main_layout.addWidget(separator1)
        

        
        # 清除结果按钮 - 使用WARNING配色（橙色系）
        self.clear_results_button = QPushButton("🗑️ 清除结果")
        self.clear_results_button.setToolTip("清除当前搜索结果")
        self.clear_results_button.setFixedHeight(UI_CONSTANTS['COMBO_HEIGHT'])
        self.clear_results_button.setMinimumWidth(100)
        self.clear_results_button.setStyleSheet(create_button_style('WARNING'))
        main_layout.addWidget(self.clear_results_button)
        
        # 添加弹性空间
        main_layout.addStretch(1)
        
        # 设置容器的布局
        container.setLayout(main_layout)
        
        # 返回紧凑布局
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(container)
        return container_layout

    def _create_type_filter_bar(self):
        """创建文件类型过滤栏 - 紧凑美观版本"""
        self.file_type_checkboxes = {}
        self.pro_file_types = {}  # 用于存储专业版文件类型的映射
        
        # 创建容器
        container = QFrame()
        container.setObjectName("filter_container")
        container.setStyleSheet("""
            QFrame#filter_container {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        
        # 使用水平布局，紧凑排列
        main_layout = QHBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # 添加图标标题
        icon_label = QLabel("📁")
        icon_label.setStyleSheet("font-size: 14px; padding: 0px;")
        main_layout.addWidget(icon_label)

        # 创建文件类型定义（紧凑版本）
        file_type_configs = [
            # 文档类型
            ('pdf', {'display': 'PDF', 'pro_feature': Features.PDF_SUPPORT, 'color': '#dc3545'}),
            ('docx', {'display': 'Word', 'pro_feature': None, 'color': '#2b5797'}),
            ('txt', {'display': 'TXT', 'pro_feature': None, 'color': '#6c757d'}),
            ('xlsx', {'display': 'Excel', 'pro_feature': None, 'color': '#107c41'}),
            ('pptx', {'display': 'PPT', 'pro_feature': None, 'color': '#d83b01'}),
            ('html', {'display': 'HTML', 'pro_feature': None, 'color': '#e34c26'}),
            ('md', {'display': 'MD', 'pro_feature': Features.MARKDOWN_SUPPORT, 'color': '#333'}),
            # 分隔符
            ('separator1', {'type': 'separator'}),
            # 多媒体类型
            ('mp4', {'display': '🎬视频', 'pro_feature': None, 'color': '#6f42c1', 'multimedia': ['mp4', 'mkv', 'avi', 'wmv', 'mov', 'flv', 'webm', 'm4v']}),
            ('mp3', {'display': '🎵音频', 'pro_feature': None, 'color': '#fd7e14', 'multimedia': ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a']}),
            ('jpg', {'display': '🖼️图片', 'pro_feature': None, 'color': '#20c997', 'multimedia': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg']}),
            # 分隔符
            ('separator2', {'type': 'separator'}),
            # 邮件类型
            ('eml', {'display': '📧EML', 'pro_feature': Features.EMAIL_SUPPORT, 'color': '#0d6efd'}),
            ('msg', {'display': '📧MSG', 'pro_feature': Features.EMAIL_SUPPORT, 'color': '#0d6efd'}),
        ]

        # 处理函数
        def add_checkbox_to_layout(type_key, type_config):
            if type_config.get('type') == 'separator':
                # 添加分隔线
                separator = QFrame()
                separator.setFrameShape(QFrame.VLine)
                separator.setFrameShadow(QFrame.Sunken)
                separator.setFixedWidth(1)
                separator.setFixedHeight(20)
                separator.setStyleSheet("color: #dee2e6;")
                main_layout.addWidget(separator)
                return

            display_name = type_config['display']
            pro_feature = type_config.get('pro_feature')
            color = type_config.get('color', '#495057')
            
            checkbox = QCheckBox(display_name)
            
            # 检查此文件类型是否需要专业版
            is_pro_feature = pro_feature is not None
            feature_available = not is_pro_feature or self.license_manager.is_feature_available(pro_feature)
            
            # 存储复选框和其对应的类型
            if 'multimedia' in type_config:
                self.file_type_checkboxes[checkbox] = type_config['multimedia']
            else:
            self.file_type_checkboxes[checkbox] = type_key
            
            # 设置样式
            if is_pro_feature and not feature_available:
                checkbox.setEnabled(False)
                checkbox.setText(f"{display_name}⭐")
                checkbox.setStyleSheet(f"""
                    QCheckBox {{
                        font-size: 10px;
                        font-weight: 500;
                        color: #adb5bd;
                        padding: 2px 4px;
                        spacing: 3px;
                    }}
                    QCheckBox::indicator {{
                        width: 12px;
                        height: 12px;
                    }}
                """)
                
                self.pro_file_types[checkbox] = {
                    'feature': pro_feature,
                    'display_name': display_name.replace('⭐', '')
                }
                checkbox.clicked.connect(self._show_pro_feature_dialog)
            else:
                checkbox.setEnabled(True)
                checkbox.setStyleSheet(f"""
                    QCheckBox {{
                        font-size: 10px;
                        font-weight: 500;
                        color: {color};
                        padding: 2px 4px;
                        spacing: 3px;
                    }}
                    QCheckBox::indicator {{
                        width: 12px;
                        height: 12px;
                        border: 1px solid {color};
                        border-radius: 2px;
                        background-color: white;
                    }}
                    QCheckBox::indicator:checked {{
                        background-color: {color};
                        border: 1px solid {color};
                    }}
                    QCheckBox::indicator:checked:hover {{
                        background-color: {color};
                    }}
                    QCheckBox:hover {{
                        background-color: rgba(0,0,0,0.05);
                        border-radius: 3px;
                    }}
                """)
            
            # 连接复选框状态改变信号
            checkbox.stateChanged.connect(self._filter_results_by_type_slot)
            main_layout.addWidget(checkbox)

        # 添加所有文件类型
        for type_key, type_config in file_type_configs:
            add_checkbox_to_layout(type_key, type_config)
        
        main_layout.addStretch(1)
        
        # 设置容器的布局
        container.setLayout(main_layout)
        
        # 返回布局
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(container)
        return container_layout
        
    def _show_pro_feature_dialog(self):
        """显示专业版功能提示对话框"""
        # 找出是哪个复选框被点击
        sender = self.sender()
        if sender in self.pro_file_types:
            feature_info = self.pro_file_types[sender]
            type_name = feature_info['display_name']
            
            # 重置复选框状态为未选中
            sender.blockSignals(True)
            sender.setChecked(False)
            sender.blockSignals(False)
            
            # 设置过滤更新阻断标志为True，防止触发过滤操作
            self.blocking_filter_update = True
            print("DEBUG: Blocking filter updates while showing pro feature dialog")
            
            # 使用QTimer确保搜索结果能正确显示
            QTimer.singleShot(100, lambda: self._show_pro_feature_dialog_message(type_name))
    
    def _show_pro_feature_dialog_message(self, type_name):
        """显示专业版功能对话框的实际消息"""
        # 显示提示对话框
        QMessageBox.information(
                self, 
                "专业版功能", 
                f"搜索 {type_name} 文件是专业版功能。\n\n"
                f"升级到专业版以解锁此功能和更多高级特性。"
            )
        # 对话框关闭后，重置过滤更新阻断标志
        self.blocking_filter_update = False
        print("DEBUG: Reset filter blocking after pro feature dialog closed")
        
        # 确保搜索结果在对话框关闭后不变
        QTimer.singleShot(100, lambda: self._apply_view_mode_and_display())
        
        # 强制刷新UI，确保专业版功能的复选框状态正确显示
        QTimer.singleShot(200, self._force_ui_refresh)

    def _create_action_buttons(self):
        """创建操作按钮区域 - 使用统一设计规范"""
        # 创建统一样式的容器
        container = QFrame()
        container.setObjectName("action_container")
        container.setStyleSheet(f"""
            QFrame#action_container {{
                background-color: #f5f5f5;
                border: 1px solid #C0C0C0;
                border-radius: {UI_CONSTANTS['BORDER_RADIUS_SMALL']}px;
                padding: {UI_CONSTANTS['MARGIN_NORMAL']}px;
            }}
        """)
        
        # 使用统一的水平布局
        main_layout = QHBoxLayout()
        main_layout.setSpacing(UI_CONSTANTS['SPACING_NORMAL'])
        main_layout.setContentsMargins(UI_CONSTANTS['MARGIN_NORMAL'], UI_CONSTANTS['MARGIN_NORMAL'], 
                                     UI_CONSTANTS['MARGIN_NORMAL'], UI_CONSTANTS['MARGIN_NORMAL'])
        
        # 操作标签 - 统一样式
        action_label = QLabel(f"{UI_CONSTANTS['ICONS']['settings']} 操作:")
        action_label.setStyleSheet(f"font-weight: bold; color: #333; font-size: {UI_CONSTANTS['FONT_SIZE_NORMAL']};")
        main_layout.addWidget(action_label)
        
        # 创建索引按钮 - 使用PRIMARY配色（青蓝色系）
        self.index_button = QPushButton(f"{UI_CONSTANTS['ICONS']['index']} 索引")
        self.index_button.setObjectName("index_button")
        self.index_button.setToolTip("创建或更新文档索引")
        self.index_button.setFixedHeight(UI_CONSTANTS['BUTTON_HEIGHT'])
        self.index_button.setMinimumWidth(80)
        self.index_button.setStyleSheet(create_button_style('PRIMARY'))
        
        # 取消索引按钮 - 使用DANGER配色（红色系）
        self.cancel_index_button = QPushButton(f"{UI_CONSTANTS['ICONS']['cancel']} 取消")
        self.cancel_index_button.setObjectName("cancel_button")
        self.cancel_index_button.setToolTip("取消正在进行的索引操作")
        self.cancel_index_button.setFixedHeight(UI_CONSTANTS['BUTTON_HEIGHT'])
        self.cancel_index_button.setMinimumWidth(80)
        self.cancel_index_button.setVisible(False)
        self.cancel_index_button.setStyleSheet(create_button_style('DANGER'))
        
        main_layout.addWidget(self.index_button)
        main_layout.addWidget(self.cancel_index_button)
        
        # 添加垂直分隔线 - 统一样式
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setFixedWidth(1)
        separator.setFixedHeight(UI_CONSTANTS['BUTTON_HEIGHT'] - 6)
        separator.setStyleSheet("QFrame { color: #C0C0C0; }")
        main_layout.addWidget(separator)
        
        # 查看跳过的文件按钮 - 使用SECONDARY配色（紫色系）
        self.view_skipped_button = QPushButton(f"{UI_CONSTANTS['ICONS']['files']} 跳过文件")
        self.view_skipped_button.setToolTip("查看在创建索引过程中被跳过的文件")
        self.view_skipped_button.setFixedHeight(UI_CONSTANTS['BUTTON_HEIGHT'])
        self.view_skipped_button.setMinimumWidth(100)
        self.view_skipped_button.setStyleSheet(create_button_style('SECONDARY'))
        
        # 为保持兼容性，添加同名变量引用
        self.view_skipped_files_button = self.view_skipped_button
        
        main_layout.addWidget(self.view_skipped_button)
        
        # 添加弹性空间
        main_layout.addStretch(1)
        
        # 设置容器的布局
        container.setLayout(main_layout)
        
        # 返回紧凑布局
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)  # 移除外边距
        container_layout.addWidget(container)
        return container_layout

    def _setup_status_bar(self):
        """Sets up the status bar with progress bar and labels."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Phase Label (e.g., "Scanning", "Extracting")
        self.phase_label = QLabel("阶段: ")
        self.phase_label.setVisible(False) # Initially hidden
        self.status_bar.addPermanentWidget(self.phase_label)

        # --- ADDED: Detail Label ---
        self.detail_label = QLabel("") # Initially empty
        self.detail_label.setMinimumWidth(200) # Give it some space
        self.detail_label.setVisible(False) # Initially hidden
        self.status_bar.addPermanentWidget(self.detail_label)
        # --------------------------

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(15) # Make it less tall
        self.progress_bar.setVisible(False) # Initially hidden
        self.progress_bar.setTextVisible(True) # Show percentage text
        self.status_bar.addPermanentWidget(self.progress_bar, 1) # Give it stretch factor

    def _setup_worker_thread(self):
        """创建并设置工作线程及其工作对象"""
        try:
            # 如果已存在线程，确保它被正确清理
            if hasattr(self, 'worker_thread') and self.worker_thread and self.worker_thread.isRunning():
                print("警告: 工作线程已存在，先清理...")
                self.worker_thread.quit()
                if not self.worker_thread.wait(3000):  # 等待最多3秒
                    print("警告: 线程未能在3秒内退出，将强制终止")
                    self.worker_thread.terminate()
                    self.worker_thread.wait(1000)
                
                if hasattr(self, 'worker') and self.worker:
                    self.worker.deleteLater()
                
                self.worker_thread.deleteLater()
            
            # 创建新的线程和工作对象
            self.worker_thread = QThread()
            self.worker = Worker()
            self.worker.moveToThread(self.worker_thread)
            
            # 连接工作线程信号到主线程槽函数
            self.worker.statusChanged.connect(self.update_status_label_slot)
            self.worker.progressUpdated.connect(self.update_progress_bar_slot)
            self.worker.resultsReady.connect(self._handle_new_search_results_slot)
            
            self.worker.errorOccurred.connect(self.handle_error_slot)
            
            # --- ADDED: Connect update check signals ---
            self.worker.updateAvailableSignal.connect(self.show_update_available_dialog_slot)
            self.worker.upToDateSignal.connect(self.show_up_to_date_dialog_slot)
            self.worker.updateCheckFailedSignal.connect(self.show_update_check_failed_dialog_slot)
            # -----------------------------------------
            
            # 连接主线程信号到工作线程槽函数
            self.startIndexingSignal.connect(self.worker.run_indexing)
            self.startSearchSignal.connect(self.worker.run_search)
            # --- ADDED: Connect update check signal to worker ---
            self.startUpdateCheckSignal.connect(self.worker.run_update_check)
            # ---------------------------------------------------
            
            # 连接线程完成信号
            self.worker_thread.finished.connect(self.thread_finished_slot)
            
            # 启动线程
            self.worker_thread.start()
            print("工作线程已成功创建并启动")
        except Exception as e:
            print(f"创建工作线程时发生错误: {str(e)}")
            # 确保清理任何可能部分创建的资源
            if hasattr(self, 'worker') and self.worker:
                self.worker.deleteLater()
                self.worker = None
            
            if hasattr(self, 'worker_thread') and self.worker_thread:
                self.worker_thread.quit()
                self.worker_thread.wait(1000)
                self.worker_thread.deleteLater()
                self.worker_thread = None
            
            # 显示错误消息
            QMessageBox.critical(self, "错误", f"创建工作线程时发生错误: {str(e)}")
    @Slot()
    def thread_finished_slot(self):
        """处理线程完成事件"""
        print("工作线程已完成")
        # 在这里可以添加任何在线程完成后需要执行的清理操作
        # 注意：worker和thread会在closeEvent中被正确清理
        
    def _setup_connections(self):
        # --- Directory/Index buttons (REMOVED browse_button connection) ---
        # self.browse_button.clicked.connect(self.browse_directory_slot) # REMOVED

        # --- 添加索引按钮的信号连接 ---
        self.index_button.clicked.connect(self.start_indexing_slot)
        # 测试取消按钮连接
        print("🔧 正在连接取消按钮信号...")
        self.cancel_index_button.clicked.connect(self.cancel_indexing_slot)
        print("✅ 取消按钮信号连接完成")
        
        # 添加测试连接
        def test_cancel_button():
            print("🧪 测试取消按钮点击")
            print("🧪 测试取消按钮点击")
            print("🧪 测试取消按钮点击")
        
        # 连接测试函数
        self.cancel_index_button.clicked.connect(test_cancel_button)  # 添加取消按钮连接
        self.view_skipped_button.clicked.connect(self.show_skipped_files_dialog_slot)
        # --------------------------------
        
        # --- Search buttons ---
        self.search_button.clicked.connect(self.start_search_slot)
        self.clear_search_button.clicked.connect(self.clear_search_entry_slot)
        self.clear_results_button.clicked.connect(self.clear_results_slot)
        
        # --- 排序和分组控件连接 ---
        # --- 查看方式控件信号连接 ---
        self.view_mode_combo.currentIndexChanged.connect(self._handle_view_mode_change_slot)
        
        # --- 搜索防抖机制连接 ---
        self.search_line_edit.textChanged.connect(self._on_search_text_changed)
        self.search_debounce_timer.timeout.connect(self._perform_debounced_search)

        # --- 搜索历史下拉框选择处理 ---
        self.search_combo.activated.connect(self._on_history_item_selected)

        # --- 回车键搜索支持 ---
        self.search_line_edit.returnPressed.connect(self.start_search_slot)

        # --- Date fields ---

        # --- Results text browser ---
        self.results_text.anchorClicked.connect(self.handle_link_clicked_slot)
        
        # --- 虚拟滚动视图信号连接 ---
        self.virtual_results_view.linkClicked.connect(self.handle_link_clicked_slot)

        # --- Worker thread signals ---
        if self.worker:
            # Check that worker exists (just in case)
            self.worker.statusChanged.connect(self.update_status_label_slot)
            self.worker.progressUpdated.connect(self.update_progress_bar_slot)
            self.worker.resultsReady.connect(self.display_search_results_slot)
            self.worker.indexingComplete.connect(self.indexing_finished_slot)
            self.worker.errorOccurred.connect(self.handle_error_slot)
            # --- ADDED: Update check connections ---
            self.worker.updateAvailableSignal.connect(self.show_update_available_dialog_slot)
            self.worker.upToDateSignal.connect(self.show_up_to_date_dialog_slot)
            self.worker.updateCheckFailedSignal.connect(self.show_update_check_failed_dialog_slot)
            # --------------------------------------
            # Connect our signals to worker slots
            self.startIndexingSignal.connect(self.worker.run_indexing)
            self.startSearchSignal.connect(self.worker.run_search)
            # --- ADDED: Update check signal ---
            self.startUpdateCheckSignal.connect(self.worker.run_update_check)
            # --------------------------------
        
        # --- File type filter change and sorting ---
        for checkbox, type_value in self.file_type_checkboxes.items():  # 正确遍历字典的键值对
            checkbox.stateChanged.connect(self._filter_results_by_type_slot)
            
        # --- Sort option changes trigger redisplay ---


        
        # --- 新增：范围下拉框变化时更新模式下拉框启用状态 ---
        self.scope_combo.currentIndexChanged.connect(self._update_mode_combo_state_slot)
        # ----------------------------------------------------------
        
        # --- 文件夹树视图信号连接 ---
        self.folder_tree.folderSelected.connect(self._filter_results_by_folder_slot)
        # --------------------------
    
    @Slot(list)
    def _handle_new_search_results_slot(self, backend_results):
        """处理从Worker接收到的新搜索结果，存储并显示"""
        print(f"Received {len(backend_results)} search results from backend")
        
        # --- 添加: 检查是否有错误或警告 ---
        if backend_results and len(backend_results) > 0:
            # 检查是否有错误消息
            first_result = backend_results[0]
            if first_result.get('error', False):
                error_msg = first_result.get('error_message', '搜索过程中出现错误')
                # 检查是否需要许可证
                if first_result.get('license_required', False):
                    # 如果是许可证错误，显示升级提示
                    self._show_pro_feature_dialog_message("通配符搜索")
                    # 恢复用户界面状态
                    self.set_busy_state(False, "search")
                    return
                else:
                    # 其他错误显示普通错误对话框
                    QMessageBox.warning(self, "搜索错误", error_msg)
                    # 恢复用户界面状态
                    self.set_busy_state(False, "search")
                    return
            
            # 检查是否有性能警告
            performance_warnings = []
            warning_results = []
            for result in backend_results:
                if result.get('warning', False) and result.get('performance_warning', False):
                    warning_msg = result.get('warning_message', '')
                    if warning_msg:
                        performance_warnings.append(warning_msg)
                        warning_results.append(result)
            
            # 如果有性能警告，显示给用户
            if performance_warnings:
                # 从结果中移除警告消息项
                backend_results = [r for r in backend_results if not r.get('warning', False)]
                
                # 显示警告消息在状态栏
                warning_msg = "; ".join(performance_warnings)
                self.statusBar().showMessage(f"警告: {warning_msg}", 10000)  # 显示10秒
                
                # 显示一个不阻断用户操作的警告对话框
                from PySide6.QtCore import QTimer
                warning_dialog = QMessageBox(QMessageBox.Warning, "搜索性能警告", 
                                           f"检测到可能的性能问题:\n{warning_msg}\n\n结果仍在加载中，但可能需要较长时间。",
                                           QMessageBox.Ok, self)
                warning_dialog.setWindowFlags(warning_dialog.windowFlags() | Qt.WindowStaysOnTopHint)
                warning_dialog.setModal(False)  # 设置为非模态
                warning_dialog.show()
                QTimer.singleShot(8000, warning_dialog.close)  # 8秒后自动关闭
        # --- 添加结束 ---
        
        # 保存完整的后端结果（包括分页信息）
        self.backend_search_result = backend_results
        
        # 保存完整的后端结果（包括分页信息）用于后续筛选
        # 这样筛选时可以保持分页格式
        self.original_search_results = backend_results
        print(f"🎯 DEBUG: 设置 original_search_results，类型: {type(backend_results)}")
        if isinstance(backend_results, dict):
            print(f"🎯 DEBUG: 字典键: {backend_results.keys()}")
        self.collapse_states = {}  # Reset collapse states on new search
        
        # 重置文件夹过滤状态
        self.filtered_by_folder = False
        self.current_filter_folder = None
        
        # 检查文件夹树功能是否可用
        folder_tree_available = self.license_manager.is_feature_available(Features.FOLDER_TREE)
        if folder_tree_available:
            # 提取结果列表用于文件夹树构建
            if isinstance(backend_results, dict) and 'results' in backend_results:
                results_for_tree = backend_results['results']
            else:
                results_for_tree = backend_results if isinstance(backend_results, list) else []
            
            # 仅当文件夹树功能可用时构建文件夹树
            self.folder_tree.build_folder_tree_from_results(results_for_tree)
        else:
            # 如果功能不可用，确保文件夹树是空的
            self.folder_tree.clear()
        
        # Now apply the current checkbox filters to these new results
        self._filter_results_by_type_slot()
        # Note: set_busy_state(False) is called within display_search_results_slot's finally block
    
    @Slot(str)
    def _filter_results_by_folder_slot(self, folder_path):
        """按文件夹路径过滤搜索结果
        
        Args:
            folder_path: 要过滤的文件夹路径
        """
        # 检查文件夹树功能是否可用
        if not self.license_manager.is_feature_available(Features.FOLDER_TREE):
            # 功能不可用，显示提示消息
            self.statusBar().showMessage("文件夹树视图是专业版功能", 3000)
            return
            
        if not self.original_search_results:
            return  # 没有结果可过滤
            
        if self.filtered_by_folder and self.current_filter_folder == folder_path:
            # 如果已经按此文件夹过滤，则取消过滤
            self.filtered_by_folder = False
            self.current_filter_folder = None
            self.statusBar().showMessage(f"已清除文件夹过滤", 3000)
        else:
            self.filtered_by_folder = True
            self.current_filter_folder = folder_path
            self.statusBar().showMessage(f"正在过滤 '{folder_path}' 中的结果", 3000)
            
        # 重新应用过滤并显示结果
        self._filter_results_by_type_slot()
    
    @Slot()

    @Slot()
    def _update_mode_combo_state_slot(self):
        """根据选择的搜索范围更新搜索模式下拉框的启用状态
        
        当搜索范围是"文件名"时，模糊搜索不可用；当范围是"全文"时，所有搜索模式都可用。
        """
        # 获取当前范围选择的索引（0=全文，1=文件名）
        scope_index = self.scope_combo.currentIndex()
        
        # 获取搜索模式下拉框对象
        mode_combo = self.mode_combo
        
        if scope_index == 1:  # 文件名搜索
            # 如果当前选择是模糊搜索（索引1），则切换到精确搜索（索引0）
            if mode_combo.currentIndex() == 1:
                mode_combo.setCurrentIndex(0)
                
            # 禁用模糊搜索选项
            mode_combo.model().item(1).setEnabled(False)
            # 修改模糊搜索选项的文本颜色为灰色
            mode_combo.setItemData(1, QColor(Qt.gray), Qt.ForegroundRole)
        else:  # 全文搜索
            # 启用所有模式选项
            mode_combo.model().item(1).setEnabled(True)
            # 恢复文本颜色
            mode_combo.setItemData(1, QColor(), Qt.ForegroundRole)
        
        # 打印调试信息
        print(f"搜索范围变更为: {'文件名' if scope_index == 1 else '全文'}, " 
              f"模糊搜索选项{'已禁用' if scope_index == 1 else '已启用'}")
<<<<<<< HEAD
    def _filter_results_by_type_slot(self):
        """Filters the original search results based on checked file types and updates display."""
        print("DEBUG: _filter_results_by_type_slot triggered")  # DEBUG
        
        # 检查是否处于过滤更新阻断状态
        if self.blocking_filter_update:
            print("DEBUG: Filter update is currently blocked")  # DEBUG
            return
        
        # 检查是否有已选的文件类型
        checked_types = []
        for checkbox, type_value in self.file_type_checkboxes.items():
            # 只添加被选中且可用的文件类型（专业版功能在未激活时为灰色不可选）
            if checkbox.isChecked() and checkbox.isEnabled():
                # 处理多媒体类型的列表
                if isinstance(type_value, list):
                    checked_types.extend(type_value)
                else:
                checked_types.append(type_value)
        
        print(f"DEBUG: Checked types for filtering: {checked_types}")  # DEBUG
        
        # 如果没有选择文件类型，使用所有原始结果
        if not checked_types:
            print("DEBUG: No file types checked, using all original results")  # DEBUG
            # 重要修复：必须创建原始结果的副本，而不是直接引用
            filtered_results = self.original_search_results.copy()
        else:
            # 根据所选文件类型过滤原始结果
            print("DEBUG: Filtering original results based on checked types...")  # DEBUG
            filtered_results = []
            for result in self.original_search_results:
                file_path = result.get('file_path', '')
                file_type = None
                
                # 提取文件扩展名，包括多媒体文件
                if file_path:
                    lower_path = file_path.lower()
                    # 扩展文件类型列表，包含多媒体文件
                    all_extensions = [
                        '.pdf', '.docx', '.txt', '.xlsx', '.pptx', '.eml', '.msg', '.html', '.htm', '.rtf', '.md',
                        '.mp4', '.mkv', '.avi', '.wmv', '.mov', '.flv', '.webm', '.m4v',  # 视频
                        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',         # 音频
                        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'  # 图片
                    ]
                    for ext in all_extensions:
                        if lower_path.endswith(ext):
                            file_type = ext[1:]  # 移除前导点
                            # .htm特殊情况，处理为html
                            if file_type == 'htm':
                                file_type = 'html'
                            # .jpeg特殊情况，处理为jpg
                            elif file_type == 'jpeg':
                                file_type = 'jpg'
                            break
                
                # 如果文件类型匹配所选类型，添加结果
                if file_type and file_type in checked_types:
                    filtered_results.append(result)
            
            print(f"DEBUG: Filtered results count after type filtering: {len(filtered_results)}")  # DEBUG
        
        # 应用文件夹过滤
        if self.filtered_by_folder and self.current_filter_folder:
            folder_filtered_results = []
            for result in filtered_results:
                file_path = result.get('file_path', '')
                if not file_path:
                    continue
                    
                # 处理存档文件中的项目
                if '::' in file_path:
                    archive_path = file_path.split('::', 1)[0]
                    folder_path = str(Path(archive_path).parent)
                else:
                    folder_path = str(Path(file_path).parent)
                
                # 标准化路径进行比较
                folder_path = normalize_path_for_display(folder_path)
                normalized_filter_folder = normalize_path_for_display(self.current_filter_folder)
                
                # 检查文件路径是否属于所选文件夹
                # 特殊处理根目录情况
                is_match = False
                if normalized_filter_folder.endswith(':\\'):  # 根目录情况
                    # 对于D:\这样的根目录，直接检查文件路径是否以此开头
                    is_match = folder_path.startswith(normalized_filter_folder) or folder_path == normalized_filter_folder[:-1]
                else:
                    # 非根目录的正常情况
                    is_match = (folder_path == normalized_filter_folder or 
                               folder_path.startswith(normalized_filter_folder + os.path.sep))
                
                if is_match:
                    folder_filtered_results.append(result)
                    
            # 更新过滤后的结果
            filtered_results = folder_filtered_results
        
        # 保存过滤后的结果
        self.search_results = filtered_results
        
        # 检查是否处于过滤更新阻断状态
        if self.blocking_filter_update:
            print("DEBUG: Filter update is currently blocked")  # DEBUG
            return
        
        # 检查是否是轻量级搜索模式
        if hasattr(self, '_quick_search_mode') and self._quick_search_mode:
            print("DEBUG: 轻量级搜索模式：跳过文件类型过滤，直接显示所有结果")
            # 在轻量级搜索模式下，直接使用所有原始结果
            filtered_results = self.original_search_results.copy()
            # 保存过滤后的结果
            self.search_results = filtered_results
            # 直接调用display_search_results_slot
            self.display_search_results_slot(filtered_results)
            return
        
        # 更新状态栏，显示过滤信息
        original_count = len(self.original_search_results) if hasattr(self, 'original_search_results') else 0
        filtered_count = len(filtered_results)
        
        # 清除之前的搜索警告（如果过滤后结果变少）
        if hasattr(self, 'search_warning_label') and filtered_count < 500:
            self.search_warning_label.setVisible(False)
        
        if checked_types:
            # 有选择文件类型时，显示过滤状态
            type_names = ', '.join(checked_types)
            if filtered_count == 0:
                self.statusBar().showMessage(f"未找到 {type_names} 类型的文件 (原始结果: {original_count} 个)", 0)
            else:
                self.statusBar().showMessage(f"已过滤为 {type_names} 类型: {filtered_count} 个结果 (原始: {original_count} 个)", 0)
        else:
            # 没有选择文件类型时，显示所有结果
            if filtered_count == 0:
                self.statusBar().showMessage("未找到结果", 0)
            else:
                self.statusBar().showMessage(f"显示所有类型: {filtered_count} 个结果", 0)
        
        # === 统一显示逻辑修复 ===
        # 调用统一的display_search_results_slot函数，避免重复的虚拟滚动判断逻辑
        print(f"DEBUG: _filter_results_by_type_slot调用display_search_results_slot，结果数量: {filtered_count}")
        self.display_search_results_slot(filtered_results)
=======
>>>>>>> 205d800b1db2b33deca56ba17897fa8699e7318f
    
    @Slot()
    def _sort_and_redisplay_results_slot(self):
        """向后兼容的排序函数 - 重定向到新的查看方式函数"""
        self._apply_view_mode_and_display()

    def _load_search_history(self):
        """Loads search history from QSettings and populates the search combo box."""
        history = self.settings.value("history/searchQueries", [])
        # Ensure loaded data is a list of strings
        if not isinstance(history, list) or not all(isinstance(item, str) for item in history):
            print("Warning: Search history in settings is corrupted. Resetting.")
            history = []
            self.settings.setValue("history/searchQueries", history) # Optionally clear corrupted setting
            
        print(f"DEBUG: Loading search history: {history}") # DEBUG
        # Clear existing items before adding new ones (safer)
        self.search_combo.clear()
        self.search_combo.addItems(history)
        # Set initial text to empty (or last item if desired, but empty is safer)
        self.search_line_edit.setText("")

    # --- Slot Methods --- 
    def clear_search_entry_slot(self):
        """Slot for the Clear Search button click. Clears the search entry."""
        self.search_line_edit.clear()

    def clear_results_slot(self):
        """Slot for the Clear Results button click. Clears the results area and resets status."""
        # 清空传统文本浏览器
        self.results_text.clear()
        
        # 清空虚拟滚动模型
        if hasattr(self, 'virtual_results_model'):
            self.virtual_results_model.set_results([])
            
        # 切换回传统模式
        if hasattr(self, 'results_stack'):
            self.results_stack.setCurrentIndex(0)
            
        # 隐藏搜索警告标签
        if hasattr(self, 'search_warning_label'):
            self.search_warning_label.setVisible(False)
            
        self.statusBar().showMessage("就绪", 0)  # Reset status
        self.progress_bar.setVisible(False)
        # Clear stored data associated with results
        self.collapse_states = {}
        self.original_search_results = []
        self.search_results = []
        # 清空分组状态
        self.group_data = {}
        self.group_collapse_states = {}
        # --- 同时清空文件夹树 ---
        if hasattr(self, 'folder_tree'):
            self.folder_tree.clear()
        # ----------------------------

    # UNIFIED Search Slot (Handles button click, enter press, combo activation)
    @Slot()
    def start_search_slot(self):
        """统一的搜索启动槽，基于搜索框文本和下拉框模式。"""
        query = self.search_line_edit.text().strip()
        print(f"DEBUG: Unified search requested for query: '{query}'") # DEBUG
        if not query:
            # Only show warning if triggered by button/enter, not by selecting empty history item
            # We might need more context here, but for now, always warn if query is empty.
            # QMessageBox.warning(self, "提示", "请输入搜索关键词。") # Avoid warning if selecting blank from history?
            return # Don't proceed with empty query
            
        # --- Update Search History --- 
        self._update_search_history(query)
        # --------------------------- 
            
        # 从下拉框获取搜索模式
        mode_index = self.mode_combo.currentIndex()
        mode = 'phrase' if mode_index == 0 else 'fuzzy'
        print(f"DEBUG: Search mode selected: {mode}")

        # 从下拉框获取搜索范围
        scope_index = self.scope_combo.currentIndex()
        search_scope = 'fulltext' if scope_index == 0 else 'filename'
        print(f"DEBUG: Search scope selected: {search_scope}")

        # --- 清除搜索缓存以确保结果准确性 ---
        if hasattr(self, 'worker') and self.worker:
            self.worker.clear_search_cache()
            print(f"DEBUG: 搜索开始前已清除缓存")

        # --- MODIFIED: Call common search prep with scope ---
        self._start_search_common(mode, query, search_scope)
        # --------------------------------------------------
        
    # --- NEW Method to update history ---
    def _update_search_history(self, query):
        """Updates the search history dropdown and saves it to settings."""
        if not query: # Should not happen due to check above, but safety first
             return 
             
        # 1. Get current history from ComboBox items
        current_history = []
        for i in range(self.search_combo.count()):
            item_text = self.search_combo.itemText(i)
            # Avoid adding empty strings if they somehow got in
            if item_text:
                 current_history.append(item_text)
                 
        # 2. Remove existing entry if found (case-sensitive match)
        if query in current_history:
            current_history.remove(query)
            
        # 3. Insert new query at the beginning
        current_history.insert(0, query)
        
        # 4. Trim the history list
        updated_history = current_history[:self.MAX_HISTORY_ITEMS]
        
        # 5. Update ComboBox items
        self.search_combo.blockSignals(True) # Block signals during update
        self.search_combo.clear()
        self.search_combo.addItems(updated_history)
        self.search_combo.blockSignals(False) # Unblock signals
        
        # 6. IMPORTANT: Restore the currently searched query in the line edit
        # 设置标志以表明这是历史记录选择
        self._setting_text_from_history = True
        self.search_line_edit.setText(query)
        # 延迟稍长一些确保textChanged信号处理完成后再重置标志
        QTimer.singleShot(200, lambda: setattr(self, '_setting_text_from_history', False))
        
        # 7. Save updated history to QSettings
        self.settings.setValue("history/searchQueries", updated_history)
        print(f"DEBUG: Updated search history: {updated_history}") # DEBUG

    # MODIFIED: Accepts mode and query as arguments
    def _start_search_common(self, mode: str, query: str, search_scope: str):
        """Common logic to start search, now takes mode, query, and scope."""
        # 检查是否为历史记录选择，如果是则优先处理
        is_history_selection = getattr(self, '_history_selection_in_progress', False)

        if self.is_busy and not is_history_selection:
            QMessageBox.warning(self, "忙碌中", "请等待当前操作完成。")
            return
        elif self.is_busy and is_history_selection:
            # 历史记录选择时，如果有进行中的操作，则取消它
            print(f"DEBUG: 历史记录选择优先，停止当前操作")
            if hasattr(self, 'worker') and self.worker:
                self.worker.stop_requested = True
            
        # --- 检测精确模式下的逻辑操作符和通配符 ---
        if mode == 'phrase' and query:
            # 检查逻辑操作符
            logical_operators = ['AND', 'OR', 'NOT']
            has_logical_operators = any(f" {op} " in f" {query} " for op in logical_operators)
            
            # 检查通配符
            wildcard_chars = ['*', '?']
            has_wildcards = any(wc in query for wc in wildcard_chars)
            
            # 如果存在逻辑操作符或通配符
            if has_logical_operators or has_wildcards:
                message = ""
                if has_logical_operators and has_wildcards:
                    message = "您的搜索词中包含逻辑操作符（AND、OR、NOT）和通配符（*、?），这些在精确搜索模式下不起作用。"
                elif has_logical_operators:
                    message = "您的搜索词中包含逻辑操作符（AND、OR、NOT），这些在精确搜索模式下不起作用。"
                else:  # has_wildcards
                    message = "您的搜索词中包含通配符（*、?），这些在精确搜索模式下不起作用。"
                    
                switch_to_fuzzy = QMessageBox.question(
                    self, 
                    "检测到特殊搜索字符", 
                    f"{message}\n\n"
                    f"您是否希望切换到模糊搜索模式来使用这些特殊字符？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if switch_to_fuzzy == QMessageBox.Yes:
                    # 切换到模糊模式
                    self.mode_combo.setCurrentIndex(1)  # 假设模糊模式是第二个选项（索引1）
                    mode = 'fuzzy'
                    self.statusBar().showMessage("已切换到模糊搜索模式以支持特殊搜索字符", 3000)
        # ----------------------------------------------------
            
        # --- ADDED: 检查通配符搜索许可证 ---
        # 在 fuzzy 模式下检查是否包含通配符字符 * 或 ?
        if mode == 'fuzzy' and ('*' in query or '?' in query):
            # 检查通配符搜索功能是否可用
            if not self.license_manager.is_feature_available(Features.WILDCARDS):
                QMessageBox.warning(
                    self, 
                    "需要专业版", 
                    "通配符搜索 (使用 * 和 ? 符号) 是专业版功能。\n\n"
                    "请升级到专业版以使用此功能。"
                )
                return
                
            # 确保通配符能被正确处理（不要自动添加额外的通配符）
            print(f"DEBUG: 检测到通配符查询: '{query}'，保持原样传递到后端")
        # ----------------------------------
            
        # --- Get Index Directory from Settings --- 
        settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        default_index_path = str(Path.home() / "Documents" / "DocumentSearchIndex") 
        index_dir = settings.value(SETTINGS_INDEX_DIRECTORY, default_index_path)
        if not index_dir:
            QMessageBox.critical(self, "错误", "未配置索引目录路径！请在设置中指定。")
            return
        # Check if index exists before searching (optional but good practice)
        if not Path(index_dir).exists():
             QMessageBox.warning(self, "索引不存在", f"索引目录 '{index_dir}' 不存在。请先建立索引或在设置中指定正确的路径。")
             return
        # -------------------------------------------
            
        # --- 从设置中读取文件大小筛选条件 ---
        min_size_str = settings.value("search/minSizeKB", "", type=str)
        max_size_str = settings.value("search/maxSizeKB", "", type=str)
        # --------------------------------------
        
        # --- 从设置中读取日期筛选条件 ---
        default_start_date = QDate(1900, 1, 1)
        default_end_date = QDate.currentDate()
        
        start_date_str = settings.value("search/startDate", "")
        start_qdate = QDate.fromString(start_date_str, "yyyy-MM-dd") if start_date_str else default_start_date
        
        end_date_str = settings.value("search/endDate", "")
        end_qdate = QDate.fromString(end_date_str, "yyyy-MM-dd") if end_date_str else default_end_date
        # --------------------------------------
        
        # --- 读取目录筛选条件 ---
        selected_dirs = settings.value("search/selectedDirectories", [], type=list)
        # -------------------------

        # --- Validate Size Inputs --- 
        min_size_kb = None
        max_size_kb = None
        try:
            if min_size_str:
                min_size_kb = int(min_size_str)
                if min_size_kb < 0:
                    QMessageBox.warning(self, "输入错误", "最小文件大小不能为负数。")
                    return
            if max_size_str:
                max_size_kb = int(max_size_str)
                if max_size_kb < 0:
                    QMessageBox.warning(self, "输入错误", "最大文件大小不能为负数。")
                    return
            if min_size_kb is not None and max_size_kb is not None and min_size_kb > max_size_kb:
                QMessageBox.warning(self, "输入错误", "最小文件大小不能大于最大文件大小。")
                return
        except ValueError:
            QMessageBox.warning(self, "输入错误", "文件大小必须是有效的整数 (KB)。")
            return
        # ---------------------------

        # --- Validate Date Inputs --- 
        if start_qdate.isValid() and end_qdate.isValid():
            if start_qdate > end_qdate:
                QMessageBox.warning(self, "日期错误", "开始日期不能晚于结束日期。")
                return
            # Convert QDate to Python date objects (or pass QDate if backend handles it)
            # Let's pass QDate for now, backend will convert
            start_date_obj = start_qdate
            end_date_obj = end_qdate
            # Alternative: Convert here
            # start_date_obj = start_qdate.toPython()
            # end_date_obj = end_qdate.toPython()
        else:
            QMessageBox.warning(self, "日期错误", "选择的日期无效。")
            return
        # ---------------------------

        # Check if at least query or size filter or date filter is provided
        # We might need a better way to check if dates are default/cleared
        # For now, assume if dates are valid, they are intended filters
        if not query and min_size_kb is None and max_size_kb is None:
             # We could also check if dates are the default wide range here
             # if start_date_obj == QDate(2000, 1, 1) and end_date_obj == QDate.currentDate():
             #      QMessageBox.warning(self, "输入错误", "请输入搜索词或设置文件大小/日期过滤器。")
             #      return
             pass  # Allow searching only by date range for now
        
        if not query and min_size_kb is None and max_size_kb is None and start_qdate == QDate(1900, 1, 1) and end_qdate == QDate.currentDate():
            QMessageBox.warning(self, "输入错误", "请输入搜索词或修改搜索设置中的文件大小/日期过滤器以进行搜索。")
            return
            
        # --- MODIFIED: Use scope in status message (optional, but good) ---
        search_type_text = "精确" if mode == 'phrase' else "模糊"
        scope_ui_map = {'fulltext': '全文', 'filename': '文件名'}
        scope_text = scope_ui_map.get(search_scope, search_scope)
        
        # 构建包含筛选条件的状态消息
        status_msg = f"正在进行 {search_type_text} ({scope_text}) 搜索: '{query}'"
        
        # 添加筛选条件到状态消息
        filter_parts = []
        if min_size_kb is not None:
            filter_parts.append(f"最小: {min_size_kb}KB")
        if max_size_kb is not None:
            filter_parts.append(f"最大: {max_size_kb}KB")
        if start_date_str:
            filter_parts.append(f"开始日期: {start_date_str}")
        if end_date_str:
            filter_parts.append(f"结束日期: {end_date_str}")
        
        # 添加目录筛选信息
        if selected_dirs and len(selected_dirs) < len(self.settings.value("indexing/sourceDirectories", [], type=list)):
            filter_parts.append(f"目录: 已选择{len(selected_dirs)}个")
            
        if filter_parts:
            status_msg += f" (筛选条件: {', '.join(filter_parts)})"
        
        # --- 增强搜索进度提示 ---
        self.statusBar().showMessage(status_msg + "...", 0)
        # 清除之前的警告标签
        if hasattr(self, 'search_warning_label'):
            self.search_warning_label.setVisible(False)
        # 设置忙碌状态为搜索操作（不显示进度条和取消按钮）
        self.set_busy_state(True, "search")
        # ------------------------------

        # --- Get File Type Filters --- 
        selected_file_types = []
        for checkbox, type_value in self.file_type_checkboxes.items():
            if checkbox.isChecked():
                selected_file_types.append(type_key)
        
        # --- Get Case Sensitivity Setting --- 
        settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME) # Re-get settings here
        case_sensitive = settings.value("search/caseSensitive", False, type=bool)
        
        # --- MODIFIED: 正确传递目录过滤参数 ---
        # 获取当前配置的源目录，用于过滤历史索引中已删除目录的结果
        source_dirs = self.settings.value("indexing/sourceDirectories", [], type=list)

        # 区分两种目录参数：
        # 1. current_source_dirs_param: 用于过滤已删除目录，总是传递所有当前配置的源目录
        # 2. search_dirs_param: 用于搜索范围限制，仅在用户选择特定目录时传递
        current_source_dirs_param = source_dirs if source_dirs else None
        search_dirs_param = selected_dirs if selected_dirs and len(selected_dirs) < len(source_dirs) else None
        
<<<<<<< HEAD
        # 调试信息
        print(f"DEBUG: 当前配置的源目录: {source_dirs}")
        print(f"DEBUG: 目录过滤参数(current_source_dirs): {current_source_dirs_param}")
        print(f"DEBUG: 搜索范围参数(search_dirs): {search_dirs_param}")

        # 清除搜索缓存以确保目录过滤生效
        if self.worker:
            self.worker.clear_search_cache()
            print("DEBUG: 已清除搜索缓存，确保目录过滤生效")

        # --- MODIFIED: Emit Signal to Worker with scope ---
=======
        # --- ADDED: 保存搜索参数以便分页使用 ---
        self.current_search_params = {
            "query_str": query,
            "search_mode": mode,
            "min_size": min_size_kb,
            "max_size": max_size_kb,
            "start_date": start_date_obj,
            "end_date": end_date_obj,
            "selected_file_types": selected_file_types,
            "index_dir": index_dir,
            "case_sensitive": case_sensitive,
            "search_scope": search_scope,
            "search_dirs_param": search_dirs_param
        }
        
        # 重置分页状态为第一页
        self.current_page = 1
        
        # --- MODIFIED: Emit Signal to Worker with scope and pagination ---
>>>>>>> 205d800b1db2b33deca56ba17897fa8699e7318f
        self.startSearchSignal.emit(query,
                                    mode,
                                    min_size_kb,
                                    max_size_kb,
                                    start_date_obj,
                                    end_date_obj,
                                    selected_file_types,
                                    index_dir, # Pass the index_dir_path
                                    case_sensitive,
                                    search_scope, # Pass search scope
<<<<<<< HEAD
                                    current_source_dirs_param) # Pass current source directories for filtering
=======
                                    search_dirs_param, # Pass selected directories for filtering
                                    self.current_page, # Page number
                                    self.page_size) # Page size
>>>>>>> 205d800b1db2b33deca56ba17897fa8699e7318f
        # -------------------------------------------------

        # --- ADDED: Store the current search scope --- 
        self.last_search_scope = search_scope 
        # ---------------------------------------------
    
    # --- 搜索防抖和分组功能方法 ---
    @Slot(str)
    def _on_search_text_changed(self, text):
        """处理搜索文本变化 - 智能防抖机制：历史记录自动搜索，手动输入需要回车"""
        print(f"DEBUG: _on_search_text_changed 被调用，文本: '{text}'")

        # 重置防抖计时器
        if hasattr(self, 'search_debounce_timer'):
            self.search_debounce_timer.stop()
            print(f"DEBUG: 防抖计时器已停止")
        
        # 如果搜索文本长度不足最小要求，不触发搜索
        if len(text.strip()) < getattr(self, 'min_search_length', 2):
            print(f"DEBUG: 文本长度不足，跳过 (长度: {len(text.strip())})")
            return
            
        # 如果文本与上次相同，不需要重新搜索（但历史记录选择除外）
        is_history_selection = getattr(self, '_setting_text_from_history', False)
        if text.strip() == getattr(self, 'last_search_text', '') and not is_history_selection:
            print(f"DEBUG: 文本与上次相同，跳过搜索")
            return
            
        # 检测是否为历史记录选择（通过程序设置文本）
        is_history_selection = getattr(self, '_setting_text_from_history', False)
        print(f"DEBUG: 历史记录选择标志: {is_history_selection}")

        # 如果启用了即时搜索
        instant_search = getattr(self, 'instant_search_enabled', False)
        print(f"DEBUG: 即时搜索启用状态: {instant_search}")

        if instant_search:
            if is_history_selection:
                # 历史记录选择：立即重置标志，然后启动短延迟自动搜索
                self._setting_text_from_history = False  # 立即重置标志避免重复触发
                print(f"DEBUG: 历史记录选择标志已立即重置")

                # 历史记录选择时立即执行搜索，不使用计时器
                print(f"DEBUG: 历史记录选择，立即执行搜索 (文本: '{text}')")
                # 更新搜索文本记录
                self.last_search_text = text.strip()
                # 立即执行搜索
                self.start_search_slot()
            else:
                # 手动输入：不自动搜索，用户需要按回车或点击搜索按钮
                print(f"DEBUG: 手动输入检测，禁用自动搜索 (文本: '{text}')")
                # 显示提示信息
                if len(text.strip()) >= 2:
                    self.statusBar().showMessage("请按回车键或点击搜索按钮开始搜索", 2000)
        else:
            print(f"DEBUG: 即时搜索未启用，跳过防抖逻辑")

    @Slot(int)
    def _on_history_item_selected(self, index):
        """处理历史记录项目选择"""
        if 0 <= index < self.search_combo.count():
            selected_text = self.search_combo.itemText(index)
            if selected_text:
                print(f"DEBUG: 用户选择历史记录: '{selected_text}' (长度: {len(selected_text)})")

                # 立即阻止所有当前操作
            if hasattr(self, 'search_debounce_timer'):
                    self.search_debounce_timer.stop()

                # 取消当前搜索操作（如果有）
                if hasattr(self, 'worker') and self.worker:
                    self.worker.stop_requested = True

                # 设置标志以表明这是历史记录选择
                self._setting_text_from_history = True
                self._history_selection_in_progress = True  # 额外标志
                print(f"DEBUG: 历史记录选择标志设置为 True")

                # 设置文本（这会触发textChanged信号）
                self.search_line_edit.setText(selected_text)
                print(f"DEBUG: 文本已设置")

                # 确保立即执行搜索，不依赖textChanged
                QTimer.singleShot(50, lambda: self._execute_history_search(selected_text))
            else:
                print(f"DEBUG: 选中的文本为空")
        else:
            print(f"DEBUG: 索引无效: {index}")


    def _execute_history_search(self, search_text):
        """执行历史记录搜索"""
        print(f"DEBUG: _execute_history_search 被调用，文本: '{search_text}'")
        # 重置标志
        self._setting_text_from_history = False
        self._history_selection_in_progress = False

        # 确保搜索框文本正确
        if self.search_line_edit.text().strip() == search_text.strip():
            # 清除搜索缓存以确保新搜索获得准确结果
            if hasattr(self, 'worker') and self.worker:
                self.worker.clear_search_cache()
                print(f"DEBUG: 已清除搜索缓存以确保准确结果")

            # 更新搜索历史记录
            self.last_search_text = search_text.strip()
            print(f"DEBUG: 历史记录搜索 - 立即执行搜索: '{search_text}'")
            # 立即执行搜索
            self.start_search_slot()
        else:
            print(f"DEBUG: 搜索框文本不匹配，跳过历史记录搜索")

    def _reset_history_flag(self):
        """重置历史记录选择标志"""
        self._setting_text_from_history = False
        print(f"DEBUG: 历史记录选择标志已重置为 False")
        
    @Slot()
    def _perform_debounced_search(self):
        """执行防抖搜索"""
        print(f"DEBUG: _perform_debounced_search 被调用")
        current_text = self.search_line_edit.text().strip()
        print(f"DEBUG: 当前文本: '{current_text}'")
        
        # 再次检查长度和变化
        if len(current_text) < getattr(self, 'min_search_length', 2):
            print(f"DEBUG: 防抖搜索-文本长度不足，跳过 (长度: {len(current_text)})")
            return
            
        # 移除重复检查，因为防抖动机制已经在textChanged中检查过了
        # 这里直接执行搜索
            
        # 记录当前搜索文本
        self.last_search_text = current_text
        print(f"DEBUG: 更新 last_search_text 为: '{current_text}'")
        
        # 执行搜索
        print(f"DEBUG: 防抖搜索开始执行: {current_text}")
        self.start_search_slot()
        
    def _toggle_instant_search(self, enabled):
        """切换即时搜索功能"""
        self.instant_search_enabled = enabled
        print(f"即时搜索 {'启用' if enabled else '禁用'}")
        
    @Slot()
    def _handle_view_mode_change_slot(self):
        """处理视图方式改变 - 只控制分组功能"""
        view_mode_index = self.view_mode_combo.currentIndex()
        view_mode_text = self.view_mode_combo.currentText()
        print(f"视图方式改变为: {view_mode_text}")
        
        # 清除分组折叠状态
        self.group_collapse_states = {}
        
        # 根据选择的视图方式设置分组模式
        if view_mode_index == 0:      # 📄 列表视图
            self.current_grouping_mode = 'none'
            self.grouping_enabled = False
        elif view_mode_index == 1:    # ⏰ 时间视图
            self.current_grouping_mode = 'date'
            self.grouping_enabled = True
        elif view_mode_index == 2:    # 📁 类型视图
            self.current_grouping_mode = 'type'
            self.grouping_enabled = True
        elif view_mode_index == 3:    # 🗂️ 文件夹视图
            self.current_grouping_mode = 'folder'
            self.grouping_enabled = True
        
        # 重新应用视图设置并显示结果
        self._apply_view_mode_and_display()
    

        
    def _apply_view_mode_and_display(self):
        """应用查看方式设置并重新显示结果（整合排序和分组）- 支持虚拟滚动"""
        search_results = getattr(self, 'search_results', [])
        if not search_results:
            # 如果没有结果，根据当前显示模式处理
            use_virtual_scroll = hasattr(self, 'results_stack') and self.results_stack.currentIndex() == 1
            
            if use_virtual_scroll:
                # 虚拟滚动模式：设置空结果
                self.virtual_results_model.set_results([])
                print("💡 虚拟滚动模式: 显示 0 个结果")
            else:
                # 传统模式：显示空结果页面
                self.results_text.clear()
                self.results_text.setText("未找到匹配结果。")
            return
            
        # 使用默认相关性排序
        sorted_results = search_results
        
        # === 智能模式选择：基于结果数量和分组需求 ===
        use_virtual_scroll = len(sorted_results) > self.virtual_scroll_threshold
        
        if use_virtual_scroll:
            # 虚拟滚动模式：直接调用display_search_results_slot（支持分组）
            print(f"DEBUG: _apply_view_mode_and_display调用display_search_results_slot（虚拟滚动），结果数量: {len(sorted_results)}")
            self.display_search_results_slot(sorted_results)
        else:
            # 传统模式：根据分组设置选择显示方式
            print(f"DEBUG: _apply_view_mode_and_display处理传统模式，结果数量: {len(sorted_results)}")
            
        if getattr(self, 'grouping_enabled', False) and getattr(self, 'current_grouping_mode', 'none') != 'none':
                # 应用分组显示
                print(f"📋 传统模式: 应用分组显示 ({self.current_grouping_mode})")
            grouped_results = self._group_results(sorted_results, self.current_grouping_mode)
                
                # 根据搜索范围选择合适的分组显示方法
                if hasattr(self, 'last_search_scope') and self.last_search_scope == 'filename':
                    # 文件名搜索：使用传统分组显示方法（现代化按钮样式）
                    self._display_grouped_results_traditional(grouped_results)
                else:
                    # 全文搜索：使用完整分组显示方法
            self._display_grouped_results(grouped_results)
        else:
                # 不分组，调用标准显示
                print("📋 传统模式: 调用标准显示（不分组）")
                self.display_search_results_slot(sorted_results)
            

            
    def _apply_grouping_and_display(self):
        """保持向后兼容的分组应用函数"""
        self._apply_view_mode_and_display()
            
    def _group_results(self, results, group_mode):
        """将搜索结果按指定方式分组"""
        grouped = {}
        
        for result in results:
            group_key = self._get_group_key(result, group_mode)
            
            if group_key not in grouped:
                grouped[group_key] = []
            grouped[group_key].append(result)
        
        return grouped
        
    def _get_group_key(self, result, group_mode):
        """获取结果的分组键"""
        if group_mode == 'type':
            # 按文件类型分组
            file_path = result.get('file_path', result.get('path', ''))
            return self._extract_file_type(file_path)
        elif group_mode == 'date':
            # 按修改日期分组（按天）
            import datetime
            import os
            mtime = result.get('last_modified', result.get('mtime', 0))
            
            # 如果搜索结果没有mtime，尝试从文件系统获取
            if mtime <= 0:
                file_path = result.get('file_path', result.get('path', ''))
                if file_path and os.path.exists(file_path):
                    try:
                        mtime = os.path.getmtime(file_path)
                    except (OSError, FileNotFoundError):
                        mtime = 0
            
            if mtime > 0:
                try:
                    date_obj = datetime.datetime.fromtimestamp(mtime)
                    return date_obj.strftime('%Y-%m-%d')
                except (ValueError, OSError):
                    pass
            return '未知日期'
        elif group_mode == 'folder':
            # 按文件夹分组
            file_path = result.get('file_path', result.get('path', ''))
            return self._extract_folder_path(file_path)
        else:
            return '默认'
            
    def _display_grouped_results(self, grouped_results):
        """显示分组后的搜索结果 - 使用完整的搜索结果显示格式"""
        # 将分组结果展平为包含组信息的结果列表
        flattened_results = []
        
        # 按组名排序
        sorted_groups = sorted(grouped_results.keys())
        
        for group_name in sorted_groups:
            group_results = grouped_results[group_name]
            result_count = len(group_results)
            
            # 检查组的折叠状态
            group_collapse_states = getattr(self, 'group_collapse_states', {})
            is_collapsed = group_collapse_states.get(group_name, False)
            collapse_symbol = "▶" if is_collapsed else "▼"
            
            # 创建组标题项（伪造一个结果项用于显示组标题）
            group_id = f"group_{hash(group_name) & 0xFFFFFF:06X}"
            
            # 存储分组ID到名称的映射
            if not hasattr(self, 'group_id_mapping'):
                self.group_id_mapping = {}
            self.group_id_mapping[group_id] = group_name
            
            # 添加组标题标记
            group_header = {
                '_is_group_header': True,
                '_group_name': group_name,
                '_group_id': group_id,
                '_group_count': result_count,
                '_is_collapsed': is_collapsed,
                '_collapse_symbol': collapse_symbol
            }
            flattened_results.append(group_header)
            
            # 如果组未折叠，添加组内的结果
            if not is_collapsed:
                for result in group_results:
                    # 为每个结果添加分组信息
                    result_with_group = dict(result)
                    result_with_group['_in_group'] = group_name
                    flattened_results.append(result_with_group)
        
        # 使用完整的搜索结果显示函数，但需要临时修改来处理分组
        # 保存原始的last_search_scope设置
        original_scope = getattr(self, 'last_search_scope', 'fulltext')
        self.last_search_scope = 'fulltext'  # 确保使用详细显示模式
        
        # 调用主显示函数
        self._display_grouped_search_results(flattened_results)
        
        # 恢复原始设置
        self.last_search_scope = original_scope
        
    def _display_grouped_search_results(self, flattened_results):
        """显示包含分组信息的完整搜索结果"""
        scrollbar = self.results_text.verticalScrollBar()
        scroll_position = scrollbar.value()
        
        try:
            self.results_text.clear()
            if not flattened_results:
                self.results_text.setText("未找到匹配结果。")
                self.statusBar().showMessage("未找到结果", 5000)
                return

            # 获取主题颜色设置（复制自display_search_results_slot）
            current_theme = self.settings.value("ui/theme", "现代蓝")
            if current_theme == "现代蓝":
                phrase_bg_color = "#E3F2FD"
                fuzzy_bg_color = "#E8F5E9"
                highlight_text_color = "#1565C0"
                link_color = "#2196F3"
                toggle_color = "#3498db"
            elif current_theme == "现代紫":
                phrase_bg_color = "#F3E5F5"
                fuzzy_bg_color = "#EDE7F6"
                highlight_text_color = "#7B1FA2"
                link_color = "#9C27B0"
                toggle_color = "#9b59b6"
            elif current_theme == "现代红":
                phrase_bg_color = "#FFE0E0"
                fuzzy_bg_color = "#FFE8E8"
                highlight_text_color = "#C62828"
                link_color = "#E53935"
                toggle_color = "#F44336"
            elif current_theme == "现代橙":
                phrase_bg_color = "#FFF3E0"
                fuzzy_bg_color = "#FFF8E1"
                highlight_text_color = "#FF6F00"
                link_color = "#FF9800"
                toggle_color = "#F57C00"
            else:
                phrase_bg_color = "#FFECB3"
                fuzzy_bg_color = "#FFF9C4"
                highlight_text_color = "#FF6F00"
                link_color = "#FF9800"
                toggle_color = "#F57C00"
            
            # 定义高亮标签
            phrase_highlight_start = f'<span style="background-color: {phrase_bg_color}; color: {highlight_text_color};">'
            fuzzy_highlight_start = f'<span style="background-color: {fuzzy_bg_color}; color: {highlight_text_color};">'
            highlight_end = '</span>'
            
            link_style = f'style="color: {link_color}; text-decoration:none; font-weight:bold;"'
            toggle_link_style = f'style="color: {toggle_color}; text-decoration:none; font-weight:bold;"'

            html_output = []
            
            # 统计总结果数（排除组标题）
            total_results = sum(1 for r in flattened_results if not r.get('_is_group_header', False))
            html_output.append(f"<h4>搜索结果总计: {total_results} 个文件</h4>")
            
            # 处理每个项目（组标题或搜索结果）
            for i, item in enumerate(flattened_results):
                if item.get('_is_group_header', False):
                    # 显示组标题
                    group_name = item['_group_name']
                    group_id = item['_group_id']
                    group_count = item['_group_count']
                    collapse_symbol = item['_collapse_symbol']
                    
                    html_output.append(f'''
                        <div style="background-color: #f5f5f5; padding: 12px; margin: 15px 0 10px 0; border-left: 4px solid {toggle_color}; border-radius: 3px;">
                            <a href="#{group_id}" {toggle_link_style}>
                                <h3 style="margin: 0; color: {toggle_color};">{collapse_symbol} {group_name} ({group_count} 个文件)</h3>
                            </a>
                        </div>
                    ''')
                else:
                    # 显示常规搜索结果（使用与首次搜索相同的逻辑）
                    # 这里需要重复display_search_results_slot中的主要逻辑
                    file_path = item.get('file_path', '(未知文件)')
                    original_heading = item.get('heading', '(无章节标题)')
                    marked_heading = item.get('marked_heading')
                    marked_paragraph = item.get('marked_paragraph')
                    match_start = item.get('match_start')
                    match_end = item.get('match_end')
                    original_paragraph = item.get('paragraph')
                    
                    escaped_display_path = html.escape(file_path)
                    escaped_start_marker = html.escape("__HIGHLIGHT_START__")
                    escaped_end_marker = html.escape("__HIGHLIGHT_END__")
                    
                    # 处理标题高亮
                    heading_to_display = marked_heading if marked_heading is not None else original_heading
                    if heading_to_display is None:
                        heading_to_display = '(无章节标题)'
                    escaped_heading_display = html.escape(str(heading_to_display))
                    if marked_heading and escaped_start_marker in escaped_heading_display:
                        escaped_heading_display = escaped_heading_display.replace(escaped_start_marker, fuzzy_highlight_start).replace(escaped_end_marker, highlight_end)
                    
                    # 处理段落高亮
                    highlighted_paragraph_display = None
                    if original_paragraph is not None:
                        paragraph_text_for_highlight = marked_paragraph if marked_paragraph is not None else original_paragraph
                        if paragraph_text_for_highlight is None:
                            paragraph_text_for_highlight = str(original_paragraph) if original_paragraph is not None else ''
                        escaped_paragraph = html.escape(str(paragraph_text_for_highlight))
                        highlighted_paragraph_display = escaped_paragraph
                        
                        if match_start is not None and match_end is not None:
                            if 0 <= match_start < match_end <= len(escaped_paragraph):
                                pre = escaped_paragraph[:match_start]
                                mat = escaped_paragraph[match_start:match_end]
                                post = escaped_paragraph[match_end:]
                                highlighted_paragraph_display = f"{pre}{phrase_highlight_start}{mat}{highlight_end}{post}"
                        elif marked_paragraph and escaped_start_marker in escaped_paragraph:
                            highlighted_paragraph_display = escaped_paragraph.replace(escaped_start_marker, fuzzy_highlight_start).replace(escaped_end_marker, highlight_end)
                    
                    # 添加结果项显示
                    html_output.append(f'<div style="margin-left: 20px; border-left: 2px solid #e0e0e0; padding-left: 15px; margin-bottom: 15px;">')
                    
                    # 文件路径和操作链接
                    folder_path_str = ""
                    is_archive_member = "::" in file_path
                    try:
                        if is_archive_member:
                            archive_file_path = file_path.split("::", 1)[0]
                            folder_path_str = str(Path(archive_file_path).parent)
                        else:
                            path_obj = Path(file_path)
                            if path_obj.is_file():
                                folder_path_str = str(path_obj.parent)
                    except Exception as pe:
                        print(f"W: Could not get parent for {file_path}: {pe}")

                    links = [f'<a href="openfile:{html.escape(file_path, quote=True)}" {link_style}>🔍 打开文件</a>']
                    if folder_path_str:
                        links.append(f'<a href="openfolder:{html.escape(folder_path_str, quote=True)}" {link_style}>📁 打开目录</a>')
                    
                    html_output.append(f"<p><strong>{escaped_display_path}</strong></p>")
                    html_output.append(f"<p>{ ' &nbsp; '.join(links) }</p>")
                    
                    # 章节信息
                    if escaped_heading_display and escaped_heading_display != '(无章节标题)':
                        html_output.append(f'<p style="margin-left: 10px;"><b>章节:</b> {escaped_heading_display}</p>')
                    
                    # 段落内容
                    if highlighted_paragraph_display:
                        html_output.append(f'<p style="margin-left: 20px;">{highlighted_paragraph_display}</p>')
                    
                    html_output.append('</div>')
            
            final_html = "".join(html_output)
            self.results_text.setHtml(final_html)
            scrollbar.setValue(scroll_position)
            
            self.statusBar().showMessage(f"找到 {total_results} 个匹配文件", 0)
            
        except Exception as e:
            print(f"Error in _display_grouped_search_results: {e}")
            self.results_text.setText(f"显示结果时出错: {e}")
        
    def _display_grouped_results_traditional(self, grouped_results):
        """传统模式下显示分组后的文件名搜索结果 - 使用现代化按钮样式"""
        scrollbar = self.results_text.verticalScrollBar()
        scroll_position = scrollbar.value()

        try:
            self.results_text.clear()
            if not grouped_results:
                self.results_text.setText("未找到匹配结果。")
                self.statusBar().showMessage("未找到结果", 5000)
                return

            # 获取主题颜色
            current_theme = self.settings.value("ui/theme", "现代蓝")
            theme_colors = self._get_theme_colors_for_display(current_theme)

            html_output = []

            # 统计总结果数
            total_results = sum(len(group_results) for group_results in grouped_results.values())

            # 添加美观的标题
            html_output.append(f'''
            <div style="margin: 15px 5px 20px 5px; padding: 15px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 8px; border-left: 4px solid {theme_colors["primary"]};">
                <h3 style="margin: 0; color: {theme_colors["primary"]}; font-size: 16px; font-weight: bold;">
                    📄 文件名搜索结果 ({total_results} 个文件，按分组显示)
                </h3>
            </div>
            ''')

            # 按组名排序
            sorted_groups = sorted(grouped_results.keys())

            for group_name in sorted_groups:
                group_results = grouped_results[group_name]
                
                # 检查组的折叠状态
                group_collapse_states = getattr(self, 'group_collapse_states', {})
                is_collapsed = group_collapse_states.get(group_name, False)
                collapse_symbol = "▶" if is_collapsed else "▼"
                
                # 创建组标题ID
                group_id = f"group_{hash(group_name) & 0xFFFFFF:06X}"
                
                # 存储分组ID到名称的映射
                if not hasattr(self, 'group_id_mapping'):
                    self.group_id_mapping = {}
                self.group_id_mapping[group_id] = group_name

                # 显示组标题
                html_output.append(f'''
                <div style="background-color: #f5f5f5; padding: 12px; margin: 15px 0 10px 0; border-left: 4px solid {theme_colors["primary"]}; border-radius: 6px;">
                    <a href="#{group_id}" style="color: {theme_colors["primary"]}; text-decoration:none; font-weight:bold;">
                        <h3 style="margin: 0; color: {theme_colors["primary"]};">{collapse_symbol} {group_name} ({len(group_results)} 个文件)</h3>
                    </a>
                </div>
                ''')

                # 如果组未折叠，显示组内的文件
                if not is_collapsed:
                    processed_paths = set()
                    for i, result in enumerate(group_results):
                        file_path = result.get('file_path', '(未知文件)')
                        if file_path in processed_paths:
                            continue
                        processed_paths.add(file_path)

                        # 计算文件信息
                        try:
                            file_name = os.path.basename(file_path)
                            file_size = result.get('file_size', result.get('size', 0))
                            mtime = result.get('last_modified', result.get('mtime', 0))

                            # 格式化文件大小
                            if file_size > 0:
                                if file_size < 1024:
                                    size_str = f"{file_size} B"
                                elif file_size < 1024 * 1024:
                                    size_str = f"{file_size / 1024:.1f} KB"
                                else:
                                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                            else:
                                size_str = '未知大小'

                            # 格式化修改时间
                            if mtime > 0:
                                import datetime
                                mtime_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                            else:
                                mtime_str = '未知时间'

                            # 获取文件类型图标
                            file_ext = Path(file_path).suffix.lower()
                            type_icon = "📄"
                            if file_ext in ['.docx', '.doc']:
                                type_icon = "📝"
                            elif file_ext in ['.xlsx', '.xls']:
                                type_icon = "📊"
                            elif file_ext in ['.pptx', '.ppt']:
                                type_icon = "📋"
                            elif file_ext in ['.pdf']:
                                type_icon = "📕"
                            elif file_ext in ['.txt', '.md']:
                                type_icon = "📄"
                            elif file_ext in ['.jpg', '.png', '.gif', '.bmp']:
                                type_icon = "🖼️"
                            elif file_ext in ['.mp4', '.avi', '.mov']:
                                type_icon = "🎬"
                            elif file_ext in ['.mp3', '.wav', '.flac']:
                                type_icon = "🎵"

                        except Exception as e:
                            file_name = file_path
                            size_str = '未知大小'
                            mtime_str = '未知时间'
                            type_icon = "📄"

                        escaped_file_name = html.escape(file_name)
                        escaped_file_path = html.escape(file_path)

                        # 计算文件夹路径
                        folder_path_str = ""
                        is_archive_member = "::" in file_path
                        try:
                            if is_archive_member:
                                archive_file_path = file_path.split("::", 1)[0]
                                folder_path_str = str(Path(archive_file_path).parent)
                            else:
                                path_obj = Path(file_path)
                                if path_obj.is_file():
                                    folder_path_str = str(path_obj.parent)
                        except Exception as pe:
                            print(f"W: Could not get parent for {file_path}: {pe}")

                        # 构建操作链接 - 使用现代化按钮样式（与不分组显示完全一致）
                        links = [f'<a href="openfile:{html.escape(file_path, quote=True)}" style="color: #fff; text-decoration: none; padding: 6px 12px; background: {theme_colors["success"]}; border-radius: 4px; font-size: 12px; margin-right: 8px;">🔍 打开文件</a>']
                        if folder_path_str:
                            links.append(f'<a href="openfolder:{html.escape(folder_path_str, quote=True)}" style="color: #fff; text-decoration: none; padding: 6px 12px; background: {theme_colors["info"]}; border-radius: 4px; font-size: 12px;">📁 打开目录</a>')

                        # 生成美观的文件项HTML（与不分组显示完全一致）
                        html_output.append(f'''
                        <div style="margin: 6px 15px; padding: 10px; background: #fff; border: 1px solid #e9ecef; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 5px;">
                                <tr>
                                    <td style="vertical-align: middle;">
                                        <span style="font-size: 18px; margin-right: 8px;">{type_icon}</span>
                                        <span style="color: {theme_colors["text_color"]}; font-size: 13px; font-weight: bold;">{escaped_file_name}</span>
                                    </td>
                                    <td style="text-align: right; vertical-align: middle; white-space: nowrap;">
                                        {" ".join(links)}
                                    </td>
                                </tr>
                            </table>

                            <div style="margin-left: 26px;">
                                <p style="margin: 0 0 5px 0; color: #6c757d; font-size: 10px; font-family: monospace; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                    {escaped_file_path}
                                </p>
                                <div style="padding: 5px 8px; background: #f8f9fa; border-radius: 3px;">
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="font-size: 11px; color: #6c757d;">📏 {size_str}</td>
                                            <td style="text-align: right; font-size: 11px; color: #6c757d;">🕒 {mtime_str}</td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                        </div>
                        ''')

            final_html = "".join(html_output)
            self.results_text.setHtml(final_html)
            scrollbar.setValue(scroll_position)

        except Exception as e:
            print(f"Error in _display_grouped_results_traditional: {e}")
            self.results_text.setText(f"显示结果时出错: {e}")

    def _display_ungrouped_results(self, results):
        """显示未分组的搜索结果 - 使用与首次搜索相同的详细显示格式"""
        # 直接使用完整的搜索结果显示函数，确保显示效果一致
        self.display_search_results_slot(results)
        
    def _format_single_result(self, result, result_id):
        """格式化单个搜索结果的HTML"""
        file_path = result.get('file_path', result.get('path', 'Unknown'))
        score = result.get('score', 0)
        mtime = result.get('last_modified', result.get('mtime', 0))
        size = result.get('file_size', result.get('size', 0))
        
        # 格式化修改时间
        if mtime > 0:
            mtime_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        else:
            mtime_str = '未知'
        
        # 格式化文件大小
        if size > 0:
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
        else:
            size_str = '未知'
        
        # 提取文件名和目录
        normalized_path = normalize_path_for_display(file_path)
        file_name = os.path.basename(normalized_path)
        file_dir = os.path.dirname(normalized_path)
        
        return f'''
            <div style="border: 1px solid #ddd; padding: 12px; margin: 8px 0; border-radius: 6px; background-color: #fafafa;">
                <div style="font-weight: bold; color: #1976d2; margin-bottom: 5px;">
                    <a href="openfile:{normalized_path}" style="text-decoration: none; color: inherit;">{file_name}</a>
                </div>
                <div style="color: #666; font-size: 0.9em; margin-bottom: 5px;">
                    📁 <a href="openfolder:{file_dir}" style="text-decoration: none; color: #666;">{file_dir}</a>
                </div>
                <div style="color: #888; font-size: 0.8em;">
                    相关度: {score:.2f} | 修改时间: {mtime_str} | 大小: {size_str}
                </div>
            </div>
        '''
        
    def _extract_file_type(self, file_path):
        """提取文件类型"""
        if not file_path:
            return '未知类型'
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext.startswith('.'):
            ext = ext[1:]
        
        # 文件类型映射
        type_mapping = {
            'pdf': 'PDF文档',
            'doc': 'Word文档', 'docx': 'Word文档',
            'xls': 'Excel文档', 'xlsx': 'Excel文档',
            'ppt': 'PowerPoint文档', 'pptx': 'PowerPoint文档',
            'txt': '文本文件',
            'md': 'Markdown文档',
            'html': 'HTML文档', 'htm': 'HTML文档',
            'rtf': 'RTF文档',
            'eml': '邮件文件',
            'msg': 'Outlook邮件',
        }
        
        return type_mapping.get(ext, f'{ext.upper()}文件' if ext else '无扩展名')
        
    def _extract_folder_path(self, file_path):
        """提取文件夹路径"""
        return PathStandardizer.get_folder_path(file_path)

    def _get_theme_colors_for_display(self, theme_name):
        """获取用于显示的主题颜色配置"""
        if theme_name == "现代蓝":
            return {
                "primary": "#007ACC",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#F59E0B",
                "danger": "#EF4444",
                "text_color": "#333333"
            }
        elif theme_name == "现代紫":
            return {
                "primary": "#8B5CF6",
                "success": "#10B981",
                "info": "#8B5CF6",
                "warning": "#F59E0B",
                "danger": "#EF4444",
                "text_color": "#333333"
            }
        elif theme_name == "现代红":
            return {
                "primary": "#DC2626",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#F59E0B",
                "danger": "#DC2626",
                "text_color": "#333333"
            }
        elif theme_name == "现代橙":
            return {
                "primary": "#EA580C",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#EA580C",
                "danger": "#EF4444",
                "text_color": "#333333"
            }
        elif theme_name == "深色模式":
            return {
                "primary": "#3B82F6",
                "success": "#059669",
                "info": "#3B82F6",
                "warning": "#D97706",
                "danger": "#DC2626",
                "text_color": "#F9FAFB"
            }
        elif theme_name == "护眼绿":
            return {
                "primary": "#059669",
                "success": "#059669",
                "info": "#0891B2",
                "warning": "#D97706",
                "danger": "#DC2626",
                "text_color": "#1E1E1E"
            }
        else:
            return {
                "primary": "#007ACC",
                "success": "#10B981",
                "info": "#3B82F6",
                "warning": "#F59E0B",
                "danger": "#EF4444",
                "text_color": "#333333"
            }

    # --- GUI Update Slots (Connected to worker signals) --- 
    @Slot(str)
    def update_status_label_slot(self, status_text):
        # Use timeout for transient messages, 0 for persistent ones
        # Let's make most status updates persistent for now
        
        # --- Improve status message display --- 
        display_text = status_text
        file_prefixes = ["对比: ", "提取: ", "删除: ", "添加: ", "更新: "]
        prefix_found = False
        for prefix in file_prefixes:
            if status_text.startswith(prefix):
                filename = status_text[len(prefix):]
                max_len = 40 # Max length for filename part
                if len(filename) > max_len:
                    short_filename = "..." + filename[-(max_len-3):] # Show end part
                else:
                    short_filename = filename
                display_text = f"{prefix}{short_filename}"
                prefix_found = True
                break
        # If it's not a file processing message, show it as is (likely a phase message)
        # Also handle warnings/errors which have prefixes like "[警告]"
        self.statusBar().showMessage(display_text, 0) 
        # ---------------------------------------

    @Slot(int, int, str, str)
    @Slot(object, object, object, object)  # 添加通用对象类型支持
    def update_progress_bar_slot(self, current, total, phase, detail):
        # 添加参数类型验证和转换
        try:
            current = int(current) if current is not None else 0
            total = int(total) if total is not None else 0
            phase = str(phase) if phase is not None else "处理中"
            detail = str(detail) if detail is not None else ""
        except (ValueError, TypeError) as e:
            print(f"Progress slot parameter error: {e}, using defaults")
            current, total, phase, detail = 0, 100, "处理中", ""
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            self.progress_bar.setVisible(True)
            # Update the phase label
            self.phase_label.setText(f"阶段: {phase}") 
            self.phase_label.setVisible(True)
            # --- ADDED: Update the detail label ---
            self.detail_label.setText(detail)
            self.detail_label.setVisible(True) # Ensure visible if progress is visible
            # ------------------------------------
        else:
            # Handle indeterminate progress or end state
            # For indeterminate progress (total=0), we might not want to show the bar
            # but still show the phase and detail
            self.progress_bar.setVisible(False) # Hide bar for indeterminate
            # Still show phase and detail if provided
            self.phase_label.setText(f"阶段: {phase}")
            self.phase_label.setVisible(True)
            self.detail_label.setText(detail) # Show detail even for indeterminate phase
            self.detail_label.setVisible(True)

    @Slot(object)
    def display_search_results_slot(self, search_result):
        print(f"\n🎯 DISPLAY_SEARCH_RESULTS_SLOT 被调用")
        print(f"   🔍 search_result type: {type(search_result)}")
        if isinstance(search_result, dict):
            print(f"   🔍 search_result keys: {search_result.keys()}")
            if 'pagination' in search_result:
                print(f"   🔍 pagination info: {search_result['pagination']}")
                print(f"   🔍 results count: {len(search_result.get('results', []))}")
        elif isinstance(search_result, list):
            print(f"   🔍 list length: {len(search_result)}")
        
        """Displays search results, adapting format based on search scope."""
        """Displays search results, adapting format based on search scope."""
        """Displays search results, adapting format based on search scope."""
        """Displays search results, adapting format based on search scope."""
<<<<<<< HEAD
=======
        scrollbar = self.results_text.verticalScrollBar()
        scroll_position = scrollbar.value()
        
        # 处理分页格式的搜索结果
        if isinstance(search_result, dict) and 'results' in search_result:
            # 新的分页格式
            results = search_result['results']
            pagination_info = search_result.get('pagination', {})
            
            # 更新分页控件
            self._update_pagination_controls(pagination_info)
            
            # 显示分页控件
            self.pagination_frame.setVisible(True)
            
        else:
            # 传统格式或空结果
            results = search_result if isinstance(search_result, list) else []
            
            # 隐藏分页控件
            self.pagination_frame.setVisible(False)
        
>>>>>>> 205d800b1db2b33deca56ba17897fa8699e7318f
        try:
            # === 虚拟滚动智能切换逻辑 ===
            use_virtual_scroll = len(results) > self.virtual_scroll_threshold
            print(f"🔧 虚拟滚动判断: len(results)={len(results)}, threshold={self.virtual_scroll_threshold}, use_virtual_scroll={use_virtual_scroll}")
            
            if use_virtual_scroll:
                # 切换到虚拟滚动视图
                self.results_stack.setCurrentIndex(1)
                # 确保虚拟滚动模型有正确的父窗口引用以访问collapse_states
                self.virtual_results_model.parent_window = self
                # 设置虚拟滚动模型数据
                current_theme = self.settings.value("ui/theme", "现代蓝")
                self.virtual_results_model.set_theme(current_theme)
                self.virtual_results_model.set_results(results)
                
                if not results:
                    self.statusBar().showMessage("未找到结果", 5000)
                else:
                    # 检查是否可能被截断（接近限制数值）
                    max_recommended_results = 500
                    if len(results) >= max_recommended_results:
                        self.statusBar().showMessage(f"🔍 结果数量超过 {max_recommended_results} 条，建议使用更明确的搜索词重新尝试", 0)
                        
                        # 在界面顶部添加警告横幅
                        if hasattr(self, 'search_warning_label'):
                            self.search_warning_label.setText(f"⚠️ 结果数量超过 {max_recommended_results} 条，建议使用更明确的搜索词重新尝试以获得更精确的结果。")
                            self.search_warning_label.setVisible(True)
                    elif len(results) >= 50:
                        self.statusBar().showMessage(f"找到 {len(results)} 个结果 (虚拟滚动模式，性能优化)", 0)
                        # 隐藏警告标签
                        if hasattr(self, 'search_warning_label'):
                            self.search_warning_label.setVisible(False)
                    else:
                        self.statusBar().showMessage(f"找到 {len(results)} 个结果 (虚拟滚动模式)", 0)
                        # 隐藏警告标签
                        if hasattr(self, 'search_warning_label'):
                            self.search_warning_label.setVisible(False)
                    
                    print(f"💡 虚拟滚动模式: 显示 {len(results)} 个结果，提升UI性能")
                return
            else:
                # === 传统模式：支持分组功能 ===
                self.results_stack.setCurrentIndex(0)
                scrollbar = self.results_text.verticalScrollBar()
                scroll_position = scrollbar.value()
                
            self.results_text.clear()
            if not results:
                self.results_text.setText("未找到匹配结果。")
                self.statusBar().showMessage("未找到结果", 5000)
                return
            
            # 安全阀：限制显示的结果数量，避免界面卡死
            max_display_results = 100  # 最多显示100条结果
            if len(results) > max_display_results:
                print(f"警告: 结果过多({len(results)}条)，只显示前{max_display_results}条")
                results = results[:max_display_results]
                self.statusBar().showMessage(f"结果过多，只显示前 {max_display_results} 条", 0)

                # 应用分组逻辑（如果启用）
                if (hasattr(self, 'grouping_enabled') and self.grouping_enabled and 
                    hasattr(self, 'current_grouping_mode') and self.current_grouping_mode != 'none'):
                    
                    print(f"📋 传统模式: 应用分组显示 ({self.current_grouping_mode})")
                    # 应用分组并显示
                    grouped_results = self._group_results(results, self.current_grouping_mode)
                    self._display_grouped_results_traditional(grouped_results)
                    self.statusBar().showMessage(f"找到 {len(results)} 个结果 (按{self.current_grouping_mode}分组)", 0)
                    return
                else:
                    print("📋 传统模式: 使用列表显示（不分组）")

            # --- Determine highlight and link colors based on theme --- MODIFIED
            current_theme = self.settings.value("ui/theme", "现代蓝")
            if current_theme == "现代蓝":
                # Modern Blue theme colors
                phrase_bg_color = "#E3F2FD" # 浅蓝色背景
                fuzzy_bg_color = "#E8F5E9"  # 更浅的蓝色背景
                highlight_text_color = "#1565C0" # 蓝色文本
                link_color = "#2196F3" # 蓝色链接
                toggle_color = "#3498db" # 折叠按钮也使用蓝色
            elif current_theme == "现代紫":
                # Modern Purple theme colors
                phrase_bg_color = "#F3E5F5" # 浅紫色背景
                fuzzy_bg_color = "#EDE7F6"  # 更浅的紫色背景
                highlight_text_color = "#7B1FA2" # 紫色文本
                link_color = "#9C27B0" # 紫色链接
                toggle_color = "#9b59b6" # 折叠按钮也使用紫色
            elif current_theme == "现代红":
                # Modern Red theme colors
                phrase_bg_color = "#FFE0E0" # 浅红色背景
                fuzzy_bg_color = "#FFE8E8"  # 更浅的红色背景
                highlight_text_color = "#C62828" # 红色文本
                link_color = "#E53935" # 红色链接
                toggle_color = "#F44336" # 折叠按钮也使用红色
            elif current_theme == "现代橙":
                # Modern Orange theme colors
                phrase_bg_color = "#FFF3E0" # 浅橙色背景
                fuzzy_bg_color = "#FFF8E1"  # 更浅的橙色背景
                highlight_text_color = "#FF6F00" # 橙色文本
                link_color = "#FF9800" # 橙色链接
                toggle_color = "#F57C00" # 橙色折叠按钮
            else:
                # Light/Default theme colors
                phrase_bg_color = "#FFECB3" # 浅黄色背景
                fuzzy_bg_color = "#FFF9C4"  # 更浅的黄色背景
                highlight_text_color = "#FF6F00" # 橙色文本
                link_color = "#FF9800" # 橙色链接
                toggle_color = "#F57C00" # 橙色折叠按钮
            
            # Define span tags with both background and text color
            phrase_highlight_start = f'<span style="background-color: {phrase_bg_color}; color: {highlight_text_color};">'
            fuzzy_highlight_start = f'<span style="background-color: {fuzzy_bg_color}; color: {highlight_text_color};">'
            highlight_end = '</span>'
            
            # Define link styles with matching theme colors
            link_style = f'style="color: {link_color}; text-decoration:none; font-weight:bold;"'
            toggle_link_style = f'style="color: {toggle_color}; text-decoration:none; font-weight:bold;"'
            # -----------------------------------------------------------

            if hasattr(self, 'last_search_scope') and self.last_search_scope == 'filename':
                # --- 优化的文件名搜索结果显示 ---

                # 获取当前主题颜色
                current_theme = self.settings.value("ui/theme", "现代蓝")
                theme_colors = self._get_theme_colors_for_display(current_theme)

                html_output = []

                # 添加美观的标题
                html_output.append(f'''
                <div style="margin: 15px 5px 20px 5px; padding: 15px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 8px; border-left: 4px solid {theme_colors["primary"]};">
                    <h3 style="margin: 0; color: {theme_colors["primary"]}; font-size: 16px; font-weight: bold;">
                        📄 文件名搜索结果 ({len(results)} 个文件)
                    </h3>
                </div>
                ''')

                processed_paths = set()
                for i, result in enumerate(results):
                    file_path = result.get('file_path', '(未知文件)')
                    if file_path in processed_paths:
                        continue
                    processed_paths.add(file_path)

                    # 计算文件信息
                    try:
                        file_name = os.path.basename(file_path)
                        file_size = result.get('file_size', result.get('size', 0))
                        mtime = result.get('last_modified', result.get('mtime', 0))

                        # 格式化文件大小
                        if file_size > 0:
                            if file_size < 1024:
                                size_str = f"{file_size} B"
                            elif file_size < 1024 * 1024:
                                size_str = f"{file_size / 1024:.1f} KB"
                            else:
                                size_str = f"{file_size / (1024 * 1024):.1f} MB"
                        else:
                            size_str = '未知大小'

                        # 格式化修改时间
                        if mtime > 0:
                            import datetime
                            mtime_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                        else:
                            mtime_str = '未知时间'

                        # 获取文件类型图标
                        file_ext = Path(file_path).suffix.lower()
                        type_icon = "📄"
                        if file_ext in ['.docx', '.doc']:
                            type_icon = "📝"
                        elif file_ext in ['.xlsx', '.xls']:
                            type_icon = "📊"
                        elif file_ext in ['.pptx', '.ppt']:
                            type_icon = "📋"
                        elif file_ext in ['.pdf']:
                            type_icon = "📕"
                        elif file_ext in ['.txt', '.md']:
                            type_icon = "📄"
                        elif file_ext in ['.jpg', '.png', '.gif', '.bmp']:
                            type_icon = "🖼️"
                        elif file_ext in ['.mp4', '.avi', '.mov']:
                            type_icon = "🎬"
                        elif file_ext in ['.mp3', '.wav', '.flac']:
                            type_icon = "🎵"

                    except Exception as e:
                        file_name = file_path
                        size_str = '未知大小'
                        mtime_str = '未知时间'
                        type_icon = "📄"

                    escaped_file_name = html.escape(file_name)
                    escaped_file_path = html.escape(file_path)

                    # 计算文件夹路径
                    folder_path_str = ""
                    is_archive_member = "::" in file_path
                    try:
                        if is_archive_member:
                            archive_file_path = file_path.split("::", 1)[0]
                            folder_path_str = str(Path(archive_file_path).parent)
                        else:
                            path_obj = Path(file_path)
                            if path_obj.is_file():
                                folder_path_str = str(path_obj.parent)
                    except Exception as pe:
                        print(f"W: Could not get parent for {file_path}: {pe}")

                    # 构建操作链接 - 使用现代化按钮样式
                    links = [f'<a href="openfile:{html.escape(file_path, quote=True)}" style="color: #fff; text-decoration: none; padding: 6px 12px; background: {theme_colors["success"]}; border-radius: 4px; font-size: 12px; margin-right: 8px;">🔍 打开文件</a>']
                    if folder_path_str:
                        links.append(f'<a href="openfolder:{html.escape(folder_path_str, quote=True)}" style="color: #fff; text-decoration: none; padding: 6px 12px; background: {theme_colors["info"]}; border-radius: 4px; font-size: 12px;">📁 打开目录</a>')

                    # 生成美观的文件项HTML
                    html_output.append(f'''
                    <div style="margin: 6px 5px; padding: 10px; background: #fff; border: 1px solid #e9ecef; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 5px;">
                            <tr>
                                <td style="vertical-align: middle;">
                                    <span style="font-size: 18px; margin-right: 8px;">{type_icon}</span>
                                    <span style="color: {theme_colors["text_color"]}; font-size: 13px; font-weight: bold;">{escaped_file_name}</span>
                                </td>
                                <td style="text-align: right; vertical-align: middle; white-space: nowrap;">
                                    {" ".join(links)}
                                </td>
                            </tr>
                        </table>

                        <div style="margin-left: 26px;">
                            <p style="margin: 0 0 5px 0; color: #6c757d; font-size: 10px; font-family: monospace; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                {escaped_file_path}
                            </p>
                            <div style="padding: 5px 8px; background: #f8f9fa; border-radius: 3px;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="font-size: 11px; color: #6c757d;">📏 {size_str}</td>
                                        <td style="text-align: right; font-size: 11px; color: #6c757d;">🕒 {mtime_str}</td>
                                    </tr>
                                </table>
                            </div>
                        </div>
                    </div>
                    ''')
                
                final_html = "".join(html_output)
                self.results_text.setHtml(final_html)
                scrollbar.setValue(scroll_position)
                self.statusBar().showMessage(f"找到 {len(processed_paths)} 个匹配文件", 0)
            else:
                # --- Render Detailed List for Fulltext Search --- 
                html_output = []
                result_count = 0
                try:  # Inner try for rendering loop
                    # ... (loop through results, generate HTML for each hit) ...
                    # ... (this includes file headers, chapter headers, paragraphs, excel tables) ...
                    last_file_path = None 
                    last_displayed_heading = None
                    file_group_counter = 0 
                    current_file_div_open = False
                    current_chapter_div_open = False

                    for i, result in enumerate(results):
                        # ... (all the complex HTML generation logic for fulltext) ...
                        # (Extract data)
                        file_path = result.get('file_path', '(未知文件)')
                        original_heading = result.get('heading', '(无章节标题)')
                        # ... (extract other needed fields: original_paragraph, marked_heading, etc.)
                        marked_heading = result.get('marked_heading')
                        marked_paragraph = result.get('marked_paragraph')
                        match_start = result.get('match_start')
                        match_end = result.get('match_end')
                        escaped_display_path = html.escape(file_path)
                        escaped_start_marker = html.escape("__HIGHLIGHT_START__")
                        escaped_end_marker = html.escape("__HIGHLIGHT_END__")
                        # (Apply highlighting)
                        heading_to_display = marked_heading if marked_heading is not None else original_heading
                        escaped_heading_display = html.escape(heading_to_display)
                        if marked_heading and escaped_start_marker in escaped_heading_display:
                             escaped_heading_display = escaped_heading_display.replace(escaped_start_marker, fuzzy_highlight_start).replace(escaped_end_marker, highlight_end)
                        highlighted_paragraph_display = None
                        original_paragraph = result.get('paragraph')
                        if original_paragraph is not None:
                            paragraph_text_for_highlight = marked_paragraph if marked_paragraph is not None else original_paragraph
                            escaped_paragraph = html.escape(paragraph_text_for_highlight)
                            highlighted_paragraph_display = escaped_paragraph
                            if match_start is not None and match_end is not None:
                                if 0 <= match_start < match_end <= len(escaped_paragraph):
                                    pre = escaped_paragraph[:match_start]; mat=escaped_paragraph[match_start:match_end]; post=escaped_paragraph[match_end:]
                                    highlighted_paragraph_display = f"{pre}{phrase_highlight_start}{mat}{highlight_end}{post}"
                                else: 
                                    print(f"W: Invalid phrase idx [{match_start}:{match_end}]")
                            elif marked_paragraph and escaped_start_marker in escaped_paragraph:
                                highlighted_paragraph_display = escaped_paragraph.replace(escaped_start_marker, fuzzy_highlight_start).replace(escaped_end_marker, highlight_end)
                        # (Handle breaks)
                        is_new_file = (file_path != last_file_path)
                        is_new_heading = (original_heading != last_displayed_heading)
                        if is_new_file:
                            if current_chapter_div_open: html_output.append("</div>")
                            if current_file_div_open: html_output.append("</div>")
                            current_chapter_div_open = False
                            current_file_div_open = False
                            if i > 0: html_output.append("<hr><br><br>")
                        elif is_new_heading and current_chapter_div_open:
                            html_output.append("</div>")
                            current_chapter_div_open = False
                        # (Output file header)
                        if is_new_file:
                            file_group_counter += 1 
                            file_key = f"f::{file_path}" 
                            is_file_collapsed = self.collapse_states.get(file_key, False)
                            toggle_char = "[+]" if is_file_collapsed else "[-]"
                            toggle_href = f'toggle::{html.escape(file_key, quote=True)}'
                            html_output.append(f'<h3 style="font-size: {UI_FONT_SIZES["file_header"]}; margin: {UI_SPACING["large"]} 0; color: #2c3e50;"><a href="{toggle_href}" {toggle_link_style}>{toggle_char}</a> {file_group_counter}. {escaped_display_path}</h3>')
                            folder_path_str = ""
                            is_archive_member = "::" in file_path
                            try:
                                if is_archive_member:
                                    archive_file_path = file_path.split("::", 1)[0]
                                    folder_path_str = str(Path(archive_file_path).parent)
                                else:
                                    path_obj = Path(file_path)
                                    if path_obj.is_file():
                                        folder_path_str = str(path_obj.parent)
                            except Exception as pe:
                                print(f"W: Could not get parent for {file_path}: {pe}")
                            links = [f'<a href="openfile:{html.escape(file_path, quote=True)}" {link_style}>🔍 打开文件</a>']
                            if folder_path_str:
                                links.append(f'<a href="openfolder:{html.escape(folder_path_str, quote=True)}" {link_style}>📁 打开目录</a>')
                            html_output.append(f"<p>{ ' &nbsp; '.join(links) }</p>")
                            if not is_file_collapsed:
                                html_output.append('<div class="file-details" style="display: block;">')
                                current_file_div_open = True
                            else:
                                current_file_div_open = False 
                            last_displayed_heading = None 
                            last_file_path = file_path
                        # (Output chapter header)
                        if current_file_div_open and (is_new_file or is_new_heading):
                            if result.get('excel_sheet') is None: 
                                # 修复：统一章节键格式，去除索引以确保同一章节的一致性
                                chapter_key = f"c::{file_path}::{original_heading if original_heading else '(无章节)'}"
                                is_chapter_collapsed = self.collapse_states.get(chapter_key, False)
                                toggle_char = "[+]" if is_chapter_collapsed else "[-]"
                                toggle_href = f'toggle::{html.escape(chapter_key, quote=True)}'
                                html_output.append(f'<p style="margin-left: {UI_SPACING["large"]}; font-size: {UI_FONT_SIZES["section_header"]}; font-weight: 600; color: #34495e;"><a href="{toggle_href}" {toggle_link_style}>{toggle_char}</a> <b>📑 章节:</b> {escaped_heading_display}</p>')
                                if not is_chapter_collapsed:
                                    html_output.append('<div class="chapter-details" style="display: block;">')
                                    current_chapter_div_open = True
                                else:
                                    current_chapter_div_open = False
                                last_displayed_heading = original_heading
                            else:
                                current_chapter_div_open = False 
                                last_displayed_heading = None
                        # (Output content: Excel or Paragraph)
                        excel_headers = result.get('excel_headers')
                        excel_values = result.get('excel_values')
                        excel_sheet = result.get('excel_sheet')
                        excel_row_idx = result.get('excel_row_idx')
                        if current_file_div_open and excel_headers is not None and excel_values is not None:
                            # 获取主题颜色
                            theme_colors = self._get_theme_colors_for_display(self.current_theme)

                            # 现代化Excel表格样式
                            html_output.append(f'''
                            <div style="margin: {UI_SPACING['normal']} {UI_SPACING['extra_large']}; padding: {UI_SPACING['large']};
                                        background: linear-gradient(145deg, #ffffff, #f8f9fa);
                                        border: 1px solid #e3e7ea; border-radius: {UI_BORDER_RADIUS['normal']};
                                        box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
                                <div style="margin-bottom: {UI_SPACING['normal']}; padding: {UI_SPACING['small']};
                                            background: {theme_colors["primary"]}15; border-radius: {UI_BORDER_RADIUS['small']};
                                            border-left: 4px solid {theme_colors["primary"]};">
                                    <h4 style="margin: 0; font-size: {UI_FONT_SIZES['section_header']}; color: {theme_colors["text_color"]};">
                                        📊 表格: {html.escape(str(excel_sheet))} | 行: {excel_row_idx}
                                    </h4>
                                </div>
                                <table style="width: 100%; border-collapse: collapse; background: white;
                                             border-radius: {UI_BORDER_RADIUS['small']}; overflow: hidden;
                                             box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                                    <tr style="background: linear-gradient(135deg, {theme_colors['primary']}20, {theme_colors['primary']}15);">
                            ''')
                            for header in excel_headers:
                                html_output.append(f'''
                                        <th style="padding: {UI_SPACING['normal']}; border: none;
                                                  font-size: {UI_FONT_SIZES['table_cell']}; font-weight: 600;
                                                  color: {theme_colors["text_color"]}; text-align: left;">
                                            {html.escape(str(header))}
                                        </th>
                                ''')
                            html_output.append("</tr><tr style='background: white;'>")
                            for value in excel_values:
                                escaped_value = html.escape(str(value))
                                highlighted_value = escaped_value.replace(escaped_start_marker,
                                    f'<mark style="background: linear-gradient(120deg, {theme_colors["highlight_bg"]}60, {theme_colors["highlight_bg"]}); color: {theme_colors["highlight_text"]}; border-radius: 3px; padding: 2px 4px;">'
                                ).replace(escaped_end_marker, '</mark>')
                                html_output.append(f'''
                                        <td style="padding: {UI_SPACING['normal']}; border: none;
                                                  font-size: {UI_FONT_SIZES['table_cell']}; color: {theme_colors["text_color"]};
                                                  border-bottom: 1px solid #f0f0f0;">
                                            {highlighted_value}
                                        </td>
                                ''')
                            html_output.append("</tr></table></div>")
                        elif current_file_div_open and current_chapter_div_open and highlighted_paragraph_display is not None:
                            # 获取主题颜色
                            theme_colors = self._get_theme_colors_for_display(self.current_theme)

                            # 现代化段落样式
                            html_output.append(f'''
                            <div style="margin: {UI_SPACING['normal']} {UI_SPACING['extra_large']}; padding: {UI_SPACING['large']};
                                        background: linear-gradient(145deg, #ffffff, #fafbfc);
                                        border: 1px solid #e8ecef; border-radius: {UI_BORDER_RADIUS['normal']};
                                        border-left: 4px solid {theme_colors["success"]};
                                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                                <div style="margin-bottom: {UI_SPACING['small']};">
                                    <span style="font-size: {UI_FONT_SIZES['small']}; color: {theme_colors["success"]}; font-weight: 600;">
                                        📄 段落内容
                                    </span>
                                </div>
                                <div style="font-size: {UI_FONT_SIZES['normal']}; line-height: 1.6; color: {theme_colors["text_color"]};
                                            word-wrap: break-word; overflow-wrap: break-word;">
                                    {highlighted_paragraph_display}
                                </div>
                            </div>
                            ''')

                        result_count += 1
                    # --- End of loop --- 

                    # --- Close the last opened divs (Corrected Indentation) ---
                    if current_chapter_div_open: html_output.append("</div>")
                    if current_file_div_open: html_output.append("</div>")
                            
                    # --- Final render of parsed HTML (Corrected Indentation) ---
                    if html_output:
                        final_html = "".join(html_output)
                        self.results_text.setHtml(final_html)
                        scrollbar.setValue(scroll_position)
                        
                    # --- Status update (Corrected Indentation) ---
                    if result_count > 0:
<<<<<<< HEAD
                        # 检查是否可能被截断（接近限制数值）
                        max_recommended_results = 500
                        if result_count >= max_recommended_results:
                            self.statusBar().showMessage(f"🔍 结果数量超过 {max_recommended_results} 条，建议使用更明确的搜索词重新尝试", 0)
                            
                            # 在界面顶部添加警告横幅
                            if hasattr(self, 'search_warning_label'):
                                self.search_warning_label.setText(f"⚠️ 结果数量超过 {max_recommended_results} 条，建议使用更明确的搜索词重新尝试以获得更精确的结果。")
                                self.search_warning_label.setVisible(True)
                        else:
                            self.statusBar().showMessage(f"找到 {result_count} 条结果", 0)
                            # 隐藏警告标签
                            if hasattr(self, 'search_warning_label'):
                                self.search_warning_label.setVisible(False)
=======
                        self.statusBar().showMessage(f"显示第1页结果: {result_count} 条 (后端分页已启用)", 0)
>>>>>>> 205d800b1db2b33deca56ba17897fa8699e7318f
                        
                except Exception as render_err: # Inner exception handling
                    # (This block needs correct indentation relative to the inner try)
                    print(f"ERROR during results rendering loop: {render_err}")
                    import traceback
                    traceback.print_exc()
                    self.statusBar().showMessage("显示结果时出错!", 0)
                    try:
                        self.results_text.setText(f"显示结果时发生内部错误:\n{traceback.format_exc()}")
                    except Exception:
                        pass
                # --- End of detailed rendering logic block ---

        # --- Outer Exception Handling (Corrected Indentation) ---
        except Exception as display_err: 
            print("Unexpected error in display_search_results:", display_err)
            import traceback
            tb = traceback.format_exc()
            print(tb)
            try:
                self.statusBar().showMessage("显示结果时发生严重错误!", 0)
                self.results_text.setText(f"显示结果时发生未处理错误:\n{display_err}\n\n{tb}")
            except Exception:
                pass
        # --- Finally block (Corrected Indentation) ---
        finally:
            # 注意：搜索的忙碌状态现在在_handle_new_search_results_slot中重置
            # 这里不再重复重置，避免多次调用
            pass

    @Slot(dict)
    def indexing_finished_slot(self, summary_dict):
        # Process final_status message from summary_dict
        final_message = summary_dict.get('message', '索引完成 (无详细信息)')
        print("--- indexing_finished_slot called ---") # DEBUG
        print(f"Final Message: {final_message}") # DEBUG
        # Update status bar with the final summary message
        self.statusBar().showMessage(final_message, 10000) # Show for 10 seconds
        # Explicitly hide progress and phase label
        print("Hiding progress bar and phase label explicitly...") # DEBUG
        self.progress_bar.setVisible(False)
        self.phase_label.setVisible(False)
        # --- 修复: 也隐藏detail_label ---
        self.detail_label.setVisible(False)
        # -------------------------------
        print("Calling set_busy_state(False)...") # DEBUG
        self.set_busy_state(False, "index")
        print("--- indexing_finished_slot finished ---") # DEBUG
        # Optionally, show a confirmation message box
        # QMessageBox.information(self, "索引完成", final_message)

    @Slot(str)
    def handle_error_slot(self, error_message):
        """Handles errors reported by the worker thread."""
        # Show error message box
        QMessageBox.critical(self, "错误", error_message)
        # Update status bar
        self.statusBar().showMessage(f"操作出错: {error_message[:100]}...", 0)  # Show truncated error persistently
        # Ensure progress bar is hidden on error
        self.progress_bar.setVisible(False)
        # --- 修复: 同时隐藏phase_label和detail_label ---
        self.phase_label.setVisible(False)
        self.detail_label.setVisible(False)
        # -------------------------------------------
        # Reset busy state
        self.set_busy_state(False, "index")

    # --- NEW Slot to handle results directly from worker ---
    @Slot(list)
    def _handle_new_search_results_slot(self, backend_results):
        """Receives results from the backend worker, stores them, and triggers filtering/display."""
        print("Received new results from backend.")  # DEBUG
        # 保存完整的后端结果（包括分页信息）
        self.backend_search_result = backend_results
        
        # 保存完整的后端结果（包括分页信息）用于后续筛选
        # 这样筛选时可以保持分页格式
        self.original_search_results = backend_results
        print(f"🎯 DEBUG: 设置 original_search_results，类型: {type(backend_results)}")
        if isinstance(backend_results, dict):
            print(f"🎯 DEBUG: 字典键: {backend_results.keys()}")
        self.collapse_states = {}  # Reset collapse states on new search
        
        # 重置文件夹过滤状态
        self.filtered_by_folder = False
        self.current_filter_folder = None
        
        # 检查文件夹树功能是否可用
        folder_tree_available = self.license_manager.is_feature_available(Features.FOLDER_TREE)
        if folder_tree_available:
            # 提取结果列表用于文件夹树构建
            if isinstance(backend_results, dict) and 'results' in backend_results:
                results_for_tree = backend_results['results']
            else:
                results_for_tree = backend_results if isinstance(backend_results, list) else []
            
            # 仅当文件夹树功能可用时构建文件夹树
            self.folder_tree.build_folder_tree_from_results(results_for_tree)
        else:
            # 如果功能不可用，确保文件夹树是空的
            self.folder_tree.clear()
        
        # 重置搜索的忙碌状态（关键修复）
        self.set_busy_state(False, "search")
        
        # Now apply the current checkbox filters to these new results
        self._filter_results_by_type_slot()
    
    # --- NEW Slot for Sorting (Called by sort controls) ---
<<<<<<< HEAD
 

    # --- Slot for Live File Type Filtering (Modified) --- 


    # --- Link Handling Slot ---
    def _show_results_context_menu(self, position):
        """显示搜索结果区域的右键菜单"""
        menu = QMenu(self)

        # 获取当前选中的文本
        cursor = self.results_text.textCursor()
        selected_text = cursor.selectedText()

        # 复制选中文本选项
        if selected_text:
            copy_action = menu.addAction("复制选中文本")
            copy_action.triggered.connect(lambda: QApplication.clipboard().setText(selected_text))
        else:
            # 如果没有选中文本，提供复制全部选项
            copy_all_action = menu.addAction("复制全部内容")
            copy_all_action.triggered.connect(lambda: QApplication.clipboard().setText(self.results_text.toPlainText()))

        menu.addSeparator()

        # 全选选项
        select_all_action = menu.addAction("全选")
        select_all_action.triggered.connect(self.results_text.selectAll)

        # 查找选项
        find_action = menu.addAction("查找...")
        find_action.triggered.connect(self._show_find_dialog)

        menu.addSeparator()

        # 刷新搜索结果选项
        refresh_action = menu.addAction("刷新搜索结果")
        refresh_action.triggered.connect(self.start_search_slot)

        # 清空结果选项
        clear_action = menu.addAction("清空结果")
        clear_action.triggered.connect(self.clear_results_slot)

        # 在指定位置显示菜单
        menu.exec(self.results_text.mapToGlobal(position))

    def _show_find_dialog(self):
        """显示查找对话框"""
        text, ok = QInputDialog.getText(self, "查找", "请输入要查找的文本:")
        if ok and text:
            # 在结果中查找文本
            cursor = self.results_text.textCursor()
            cursor.movePosition(cursor.Start)
            self.results_text.setTextCursor(cursor)

            # 查找并高亮显示文本
            found = self.results_text.find(text)
            if not found:
                QMessageBox.information(self, "查找结果", f"未找到 '{text}'")





    @Slot(QUrl)
=======
    @Slot()
    def _sort_and_redisplay_results_slot(self):
        """Sorts the original search results based on current sort controls and triggers redisplay."""
        if not self.original_search_results: # Don't sort if there are no results
            return
            
        # --- Get Sort Parameters --- 
        sort_field = self.sort_combo.currentText()
        is_descending = self.sort_desc_radio.isChecked()
        reverse_sort = is_descending # True for descending, False for ascending

        # --- Define Sort Key Function --- 
        def get_sort_key(item):
            if sort_field == "相关度":
                # Default score is already handled in display, but keep it for explicit sorting
                # Score is negated for descending sort earlier, so here negate again if ascending
                return -item.get('score', 0.0) # Higher score first
            elif sort_field == "文件路径":
                return item.get('file_path', '')
            elif sort_field == "修改日期":
                # Ensure timestamp exists, default to 0 if missing
                return item.get('last_modified', 0.0) 
            elif sort_field == "文件大小":
                # Ensure size exists, default to 0 if missing
                return item.get('file_size', 0)
            else:
                return None # Should not happen

        # --- Sort Original Results --- 
        try:
            # 处理分页格式的排序
            if isinstance(self.original_search_results, dict) and 'results' in self.original_search_results:
                # 分页格式：只排序结果列表，保持分页信息
                results_to_sort = self.original_search_results['results']
                if sort_field == "相关度":
                    sorted_results = sorted(results_to_sort, key=get_sort_key, reverse=not reverse_sort)
                else:
                    sorted_results = sorted(results_to_sort, key=get_sort_key, reverse=reverse_sort)
                
                # 更新分页格式中的结果列表
                self.original_search_results['results'] = sorted_results
            elif isinstance(self.original_search_results, list):
                # 传统格式：直接排序列表
                if sort_field == "相关度":
                    self.original_search_results.sort(key=get_sort_key, reverse=not reverse_sort)
                else:
                    self.original_search_results.sort(key=get_sort_key, reverse=reverse_sort)
        except Exception as sort_err:
            print(f"Error during sorting: {sort_err}")
            QMessageBox.warning(self, "排序错误", f"对结果进行排序时出错: {sort_err}")
            return # Stop if sorting fails

        # --- Trigger Redisplay (which applies file type filter) --- 
        self._filter_results_by_type_slot()

    # --- Slot for Live File Type Filtering (Modified) ---    @Slot()
    def _filter_results_by_type_slot(self):
        """Filters the original search results based on checked file types and updates display."""
        print("DEBUG: _filter_results_by_type_slot triggered")  # DEBUG
        
        # 检查是否处于过滤更新阻断状态
        if self.blocking_filter_update:
            print("DEBUG: Filter update is currently blocked")  # DEBUG
            return
        
        # 检查是否有已选的文件类型
        checked_types = []
        for checkbox, type_value in self.file_type_checkboxes.items():
            # 只添加被选中且可用的文件类型（专业版功能在未激活时为灰色不可选）
            if checkbox.isChecked() and checkbox.isEnabled():
                checked_types.append(type_value)
        
        print(f"DEBUG: Checked types for filtering: {checked_types}")  # DEBUG
        
        # 如果没有选择文件类型，使用所有原始结果
        if not checked_types:
            print("DEBUG: No file types checked, using all original results")  # DEBUG
            # 检查是否有分页格式的原始结果
            if isinstance(self.original_search_results, dict) and 'results' in self.original_search_results:
                filtered_results = self.original_search_results['results'].copy()
            else:
                filtered_results = self.original_search_results.copy() if isinstance(self.original_search_results, list) else []
        else:
            # 根据所选文件类型过滤原始结果
            print("DEBUG: Filtering original results based on checked types...")  # DEBUG
            filtered_results = []
            
            # 确保 original_search_results 是列表格式
            if isinstance(self.original_search_results, dict) and 'results' in self.original_search_results:
                results_to_filter = self.original_search_results['results']
            else:
                results_to_filter = self.original_search_results if isinstance(self.original_search_results, list) else []
            
            for result in results_to_filter:
                file_path = result.get('file_path', '')
                file_type = None
                
                # 提取文件扩展名
                if file_path:
                    lower_path = file_path.lower()
                    for ext in ['.pdf', '.docx', '.txt', '.xlsx', '.pptx', '.eml', '.msg', '.html', '.htm', '.rtf', '.md']:
                        if lower_path.endswith(ext):
                            file_type = ext[1:]  # 移除前导点
                            # .htm特殊情况，处理为html
                            if file_type == 'htm':
                                file_type = 'html'
                            break
                
                # 如果文件类型匹配所选类型，添加结果
                if file_type and file_type in checked_types:
                    filtered_results.append(result)
            
            print(f"DEBUG: Filtered results count after type filtering: {len(filtered_results)}")  # DEBUG
        
        # 应用文件夹过滤
        if self.filtered_by_folder and self.current_filter_folder:
            folder_filtered_results = []
            for result in filtered_results:
                file_path = result.get('file_path', '')
                if not file_path:
                    continue
                    
                # 处理存档文件中的项目
                if '::' in file_path:
                    archive_path = file_path.split('::', 1)[0]
                    folder_path = str(Path(archive_path).parent)
                else:
                    folder_path = str(Path(file_path).parent)
                    
                # 检查文件路径是否属于所选文件夹
                # 特殊处理根目录情况
                is_match = False
                if self.current_filter_folder.endswith(':\\'):  # 根目录情况
                    # 对于D:\这样的根目录，直接检查文件路径是否以此开头
                    is_match = folder_path.startswith(self.current_filter_folder) or folder_path == self.current_filter_folder[:-1]
                else:
                    # 非根目录的正常情况
                    is_match = (folder_path == self.current_filter_folder or 
                               folder_path.startswith(self.current_filter_folder + os.path.sep))
                
                if is_match:
                    folder_filtered_results.append(result)
                    
            # 更新过滤后的结果
            filtered_results = folder_filtered_results
        
        # 保存过滤后的结果
        self.search_results = filtered_results
        
        # 检查原始搜索结果是否是分页格式
        if isinstance(self.original_search_results, dict) and 'pagination' in self.original_search_results:
            # 如果是分页格式，构造相应的过滤后分页结果
            pagination_info = self.original_search_results['pagination'].copy()
            # 更新分页信息以反映过滤后的结果
            pagination_info['total_count'] = len(filtered_results)
            pagination_info['total_pages'] = max(1, (len(filtered_results) + pagination_info.get('page_size', 50) - 1) // pagination_info.get('page_size', 50))
            
            filtered_paginated_result = {
                'results': filtered_results,
                'pagination': pagination_info
            }
            self.display_search_results_slot(filtered_paginated_result)
        else:
            # 如果不是分页格式，直接传递过滤后的列表
            self.display_search_results_slot(filtered_results)
>>>>>>> 205d800b1db2b33deca56ba17897fa8699e7318f
    def handle_link_clicked_slot(self, url):
        """Handles clicks on file, folder, and toggle links in the results text area."""
        scheme = url.scheme()
        raw_url_str = url.toString()
        print(f"--- Link Clicked: Scheme='{scheme}', Raw URL='{raw_url_str}' --- ")  # DEBUG
        
        if scheme == "openfile":
            # 解码URL路径，处理百分比编码
            encoded_path = raw_url_str.split(scheme + ":", 1)[1]
            path_str = QUrl.fromPercentEncoding(encoded_path.encode('utf-8'))
            
            # 移除Windows路径的前导斜杠
            if sys.platform == 'win32' and path_str.startswith('/') and not path_str.startswith('//'): 
                path_str = path_str[1:]
                
            print(f"解码后的文件路径: {path_str}")
            target_path = path_str
            folder_path = None
            
            # 解析路径并选择文件夹
            if "::" in path_str:
                archive_file_path = path_str.split("::", 1)[0]
                target_path = archive_file_path
                folder_path = str(Path(archive_file_path).parent)
            else:
                folder_path = str(Path(path_str).parent)
            
            # 在文件夹树视图中选择对应文件夹
            try:
                if folder_path:
                    self.folder_tree.select_folder(folder_path)
            except Exception as e:
                print(f"选择文件夹时出错: {e}")
            
            # 打开文件
            self._open_path_with_desktop_services(target_path, is_file=True)
            
        elif scheme == "openfolder":
            # 解码URL路径，处理百分比编码
            encoded_path = raw_url_str.split(scheme + ":", 1)[1]
            path_str = QUrl.fromPercentEncoding(encoded_path.encode('utf-8'))
            
            # 移除Windows路径的前导斜杠
            if sys.platform == 'win32' and path_str.startswith('/') and not path_str.startswith('//'):
                path_str = path_str[1:]
                
            print(f"解码后的文件夹路径: {path_str}")
            
            # 在文件夹树视图中选择对应文件夹
            try:
                self.folder_tree.select_folder(path_str)
            except Exception as e:
                print(f"选择文件夹时出错: {e}")
            
            # 打开文件夹
            self._open_path_with_desktop_services(path_str, is_file=False)
            
        elif scheme == "toggle":
            try:
                # Extract the full key after "toggle::"
                encoded_key_part = raw_url_str.split("::", 1)[1]
                # Decode the key (handles potential special chars in path/heading)
                toggle_key = QUrl.fromPercentEncoding(encoded_key_part.encode('utf-8'))
                print(f"  Toggle request for key: '{toggle_key}'")  # DEBUG
                
                # 检查是否是虚拟滚动分组的折叠键
                if toggle_key.startswith("vgroup::"):
                    # 虚拟滚动分组折叠处理
                    if not hasattr(self, 'group_collapse_states'):
                        self.group_collapse_states = {}
                    
                    current_state = self.group_collapse_states.get(toggle_key, False)  # Default to expanded
                    print(f"  Current virtual group collapse state for key '{toggle_key}': {current_state}")
                    new_state = not current_state
                    self.group_collapse_states[toggle_key] = new_state
                    print(f"  New virtual group collapse state for key '{toggle_key}': {self.group_collapse_states[toggle_key]}")
                    
                    # 重新应用分组和显示（虚拟滚动模式）
                    self._apply_view_mode_and_display()
                else:
                    # 传统模式的文件/章节折叠处理
                    current_state = self.collapse_states.get(toggle_key, False)  # Default to expanded
                    print(f"  Current collapse state for key '{toggle_key}': {current_state}")
                    new_state = not current_state
                    self.collapse_states[toggle_key] = new_state
                    print(f"  New collapse state for key '{toggle_key}': {self.collapse_states[toggle_key]}")
                    
                    # 修改：直接渲染当前结果，而不是重新筛选
                    print("  直接渲染当前结果...")
                    # 创建搜索结果的副本，以避免引用问题
                    results_copy = self.search_results.copy()
                    # 直接调用display_search_results_slot更新视图
                    self.display_search_results_slot(results_copy)
                
            except IndexError:
                print("Error: Could not extract key from toggle link:", raw_url_str)
            except Exception as e:
                print(f"Error processing toggle link {raw_url_str}: {e}")
        
        elif scheme == "" and raw_url_str.startswith("#group_"):
            try:
                # 处理锚点格式的分组链接 (#group_XXXXXX)
                group_id = raw_url_str[1:]  # 移除开头的#
                
                # 从ID映射中获取分组名称
                if hasattr(self, 'group_id_mapping') and group_id in self.group_id_mapping:
                    group_name = self.group_id_mapping[group_id]

                else:
                    print(f"  Warning: Unknown group ID: {group_id}")  # DEBUG
                    return
                
                # 切换该分组的折叠状态
                current_state = self.group_collapse_states.get(group_name, False)  # 默认展开
                print(f"  Current collapse state for group '{group_name}': {current_state}")
                new_state = not current_state
                self.group_collapse_states[group_name] = new_state
                print(f"  New collapse state for group '{group_name}': {self.group_collapse_states[group_name]}")
                
                # 重新应用分组显示
                self._apply_grouping_and_display()
                
            except IndexError:
                print("Error: Could not extract group name from toggle_group link:", raw_url_str)
            except Exception as e:
                print(f"Error processing toggle_group link {raw_url_str}: {e}")

    def _save_window_geometry(self):
        """Saves window geometry to QSettings."""
        # print("保存窗口几何状态...")
        self.settings.setValue("windowGeometry", self.saveGeometry())

    def _restore_window_geometry(self):
        """从QSettings恢复窗口几何状态。"""
        geometry = self.settings.value("windowGeometry")
        if geometry:
            self.restoreGeometry(geometry)

    def _load_last_directory(self) -> str:
        """Loads the last used directory from QSettings."""
        return self.settings.value("lastDirectory", "")  # Default to empty string

    def _save_last_directory(self, directory: str):
        """Saves the last used directory to QSettings."""
        self.settings.setValue("lastDirectory", directory)

    def _create_menubar(self):
        """Creates the application menu bar."""
        menu_bar = self.menuBar()
        
        # --- File Menu ---
        file_menu = menu_bar.addMenu("文件(&F)")
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.Quit) # Use standard Quit shortcut for current OS
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # --- Search Menu ---
        search_menu = menu_bar.addMenu("搜索(&S)")
        
        start_search_action = QAction("开始搜索(&S)...", self) # Add & for shortcut Alt+S
        start_search_action.triggered.connect(self.start_search_slot)
        search_menu.addAction(start_search_action)
        
        clear_results_action = QAction("清除结果(&C)", self)
        clear_results_action.triggered.connect(self.clear_results_slot)
        search_menu.addAction(clear_results_action)
        
        search_menu.addSeparator()
        
        search_settings_action = QAction("搜索设置(&P)...", self) # P for Parameters/Preferences
        search_settings_action.triggered.connect(self.show_search_settings_dialog_slot)
        search_menu.addAction(search_settings_action)
        
        # --- Index Menu ---
        index_menu = menu_bar.addMenu("索引(&I)")
        
        create_index_action = QAction("创建索引(&C)...", self)
        create_index_action.triggered.connect(self.start_indexing_slot)
        index_menu.addAction(create_index_action)
        
        view_skipped_action = QAction("查看跳过的文件(&V)...", self)
        view_skipped_action.triggered.connect(self.show_skipped_files_dialog_slot)
        index_menu.addAction(view_skipped_action)
        
        index_menu.addSeparator()
        
        index_settings_action = QAction("索引设置(&S)...", self)
        index_settings_action.triggered.connect(self.show_index_settings_dialog_slot)
        index_menu.addAction(index_settings_action)
        
        # --- Settings Menu ---
        settings_menu = menu_bar.addMenu("设置(&T)")
        
        interface_settings_action = QAction("界面设置(&U)...", self) # U for User interface
        interface_settings_action.triggered.connect(self.show_interface_settings_dialog_slot)
        settings_menu.addAction(interface_settings_action)

        # 添加索引优化设置菜单项
        optimization_settings_action = QAction("索引优化设置(&O)...", self)
        optimization_settings_action.triggered.connect(self.show_optimization_settings_dialog_slot)
        settings_menu.addAction(optimization_settings_action)

        # 添加托盘设置菜单项
        tray_settings_action = QAction("托盘设置(&R)...", self)
        tray_settings_action.triggered.connect(self.show_tray_settings_dialog_slot)
        settings_menu.addAction(tray_settings_action)
        
        # 添加启动设置菜单项
        startup_settings_action = QAction("启动设置(&S)...", self)
        startup_settings_action.triggered.connect(self.show_startup_settings_dialog_slot)
        settings_menu.addAction(startup_settings_action)

        # 添加热键设置菜单项
        hotkey_settings_action = QAction("热键设置(&K)...", self)
        hotkey_settings_action.triggered.connect(self.show_hotkey_settings_dialog_slot)
        settings_menu.addAction(hotkey_settings_action)

        # --- ADDED: 许可证菜单 ---
        settings_menu.addSeparator()  # 添加分隔线
        license_action = QAction("许可证管理(&L)...", self)
        license_action.triggered.connect(self.show_license_dialog_slot)
        settings_menu.addAction(license_action)
        # ------------------------
        
        # --- Help Menu ---
        help_menu = menu_bar.addMenu("帮助(&H)")  # Add & for shortcut Alt+H
        
        # --- ADDED: 使用帮助菜单项 ---
        help_doc_action = QAction("使用帮助(&H)...", self)
        help_doc_action.triggered.connect(self.show_help_documentation_slot)
        help_menu.addAction(help_doc_action)
        
        help_menu.addSeparator()  # 添加分隔线
        # ------------------------------
        
        # --- ADDED: Check for updates menu item --- 
        check_update_action = QAction("检查更新(&U)...", self)
        check_update_action.triggered.connect(self.check_for_updates_slot) # Connect later
        help_menu.addAction(check_update_action)
        # ------------------------------------------
        
        about_action = QAction("关于(&A)...", self)  # Add & for shortcut Alt+A
        about_action.triggered.connect(self.show_about_dialog_slot)
        help_menu.addAction(about_action)

        # --- 创建右侧菜单（仅创建空菜单，不更新内容） ---
        # 创建一个右对齐的菜单
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        menu_bar.setCornerWidget(spacer, Qt.TopLeftCorner)
        
        # 保存为成员变量，以便之后可以更新它
        # 仅创建空菜单，内容将在_init_license_manager中更新
        self.upgrade_menu = menu_bar.addMenu("")
        
        # 设置样式（可以在这里设置，因为不需要license_manager）
        menu_style = "QMenu { color: #007BFF; font-weight: bold; }"
        self.upgrade_menu.setStyleSheet(menu_style)

    # 添加一个新的方法，用于更新Pro菜单的状态
    def _update_pro_menu(self):
        """根据当前许可证状态更新Pro菜单"""
        # 强制重新获取许可证状态，确保获取最新状态
        self.license_manager = get_license_manager()
        is_licensed = self.license_manager.get_license_status() == LicenseStatus.ACTIVE
        menu_text = "专业版" if is_licensed else "升级到专业版(&U)"
        self.upgrade_menu.setTitle(menu_text)
        
        # 清除现有操作
        self.upgrade_menu.clear()
        
        # 设置更醒目的样式，但只针对菜单标题，不影响下拉菜单项
        if is_licensed:
            # 专业版状态 - 使用金色加粗，只应用于菜单标题
            menu_style = """
                QMenuBar > QMenu::title { color: #FFD700; font-weight: bold; background-color: #333333; }
                QMenu::item { color: inherit; font-weight: normal; background-color: transparent; }
            """
        else:
            # 普通版状态 - 使用醒目的红色加粗，只应用于菜单标题
            menu_style = """
                QMenuBar > QMenu::title { color: #FF4500; font-weight: bold; background-color: #333333; }
                QMenu::item { color: inherit; font-weight: normal; background-color: transparent; }
            """
        
        self.upgrade_menu.setStyleSheet(menu_style)
        
        if not is_licensed:
            upgrade_action = QAction("查看专业版详情...", self)
            upgrade_action.triggered.connect(self.show_license_dialog_slot)
            self.upgrade_menu.addAction(upgrade_action)
        else:
            view_license_action = QAction("查看许可证信息...", self)
            view_license_action.triggered.connect(self.show_license_dialog_slot)
            self.upgrade_menu.addAction(view_license_action)
            
    def _force_ui_refresh(self):
        """强制刷新整个UI，确保所有控件正确显示"""
        print("DEBUG: 强制刷新整个UI...")
        
        # 首先获取当前主题
        theme_name = self.settings.value("ui/theme", "系统默认")
        
        # 重新应用主题图标
        if theme_name == "现代蓝" or theme_name == "系统默认":
            arrow_icon_path = get_resource_path("down_arrow_blue.png")
        elif theme_name == "现代紫":
            arrow_icon_path = get_resource_path("down_arrow_purple.png")
        elif theme_name == "现代红":
            arrow_icon_path = get_resource_path("down_arrow_red.png")
        elif theme_name == "现代橙":
            arrow_icon_path = get_resource_path("down_arrow_orange.png")
        else:
            # 默认使用蓝色
            arrow_icon_path = get_resource_path("down_arrow_blue.png")
            
        # 重新应用主题图标到下拉框
        if os.path.exists(arrow_icon_path):
            self._apply_direct_arrow_icons(arrow_icon_path)
            
        # 强制每个控件重绘
        from PySide6.QtWidgets import QHeaderView
        for widget in QApplication.allWidgets():
            try:
                # 特殊处理 QHeaderView，它的 update() 方法需要参数
                if isinstance(widget, QHeaderView):
                    # 对于 QHeaderView，我们可以调用updateSection或直接跳过
                    continue
                else:
                    widget.style().unpolish(widget)
                    widget.style().polish(widget)
                    widget.update()
            except Exception as e:
                print(f"刷新控件时出错: {e}")
            
        # 特别关注下拉框控件
        for widget in [self.search_combo, self.view_mode_combo]:
            if widget:
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
                
        # 特别关注文件类型复选框
        for checkbox in self.file_type_checkboxes.keys():
            checkbox.style().unpolish(checkbox)
            checkbox.style().polish(checkbox)
            checkbox.update()
        
        # 重新应用应用程序样式表
        app = QApplication.instance()
        current_stylesheet = app.styleSheet()
        app.setStyleSheet("")
        app.setStyleSheet(current_stylesheet)
        
        # 处理所有待处理的事件
        QApplication.processEvents()
        
        # 强制重绘整个窗口
        self.repaint()
        
        # 刷新菜单栏
        self.menuBar().update()
        
        # 最后再处理一次所有事件
        QApplication.processEvents()
        
        print("DEBUG: UI刷新完成")
    def set_busy_state(self, is_busy, operation_type="index"):
        """设置应用程序忙碌状态，禁用或启用UI控件
        
        Args:
            is_busy: 是否处于忙碌状态
            operation_type: 操作类型，"index" 或 "search"
        """
        # 添加调试信息
        import traceback
        call_stack = traceback.extract_stack()
        caller_info = call_stack[-2] if len(call_stack) >= 2 else "Unknown"
        print(f"🔧 set_busy_state 调用: is_busy={is_busy}, operation_type='{operation_type}', 调用者: {caller_info.filename}:{caller_info.lineno} in {caller_info.name}")
        
        self.is_busy = is_busy
        
        # 禁用或启用主要操作按钮
        if hasattr(self, 'search_button'):
            self.search_button.setEnabled(not is_busy)
        if hasattr(self, 'index_button'):
            self.index_button.setEnabled(not is_busy)
            # --- ADDED: 控制索引按钮的显示/隐藏 ---
            self.index_button.setVisible(not is_busy)
        if hasattr(self, 'cancel_index_button'):
            # --- MODIFIED: 根据操作类型决定取消按钮的行为 ---
            if is_busy:
                print(f"🔧 条件检查: operation_type='{operation_type}', 比较结果: {operation_type == 'index'}")
                if operation_type == "index":
                    # 索引操作：显示并启用取消按钮
                    print("🔧 显示取消按钮...")
                    self.cancel_index_button.setVisible(True)
                    print(f"🔧 取消按钮可见性: {self.cancel_index_button.isVisible()}")
                    self.cancel_index_button.setEnabled(True)
                    self.cancel_index_button.setText("取消索引")
                else:
                    # 搜索操作：隐藏取消按钮，因为搜索操作通常很快完成
                    print(f"🔧 隐藏取消按钮 (操作类型: '{operation_type}')")
                    self.cancel_index_button.setVisible(False)
                    self.cancel_index_button.setEnabled(False)
            else:
                # 结束忙碌状态：隐藏取消按钮并重置状态
                self.cancel_index_button.setVisible(False)
                self.cancel_index_button.setEnabled(False)
                self.cancel_index_button.setText("取消索引")  # 重置文本
            # ------------------------------------------------
        if hasattr(self, 'clear_search_button'):
            self.clear_search_button.setEnabled(not is_busy)
        if hasattr(self, 'clear_results_button'):
            self.clear_results_button.setEnabled(not is_busy)
        
        # 显示或隐藏进度条 - 根据操作类型决定
        if hasattr(self, 'progress_bar'):
            if operation_type == "search":
                # 搜索操作：隐藏进度条，因为搜索通常很快
                self.progress_bar.setVisible(False)
            else:
                # 索引操作：显示进度条
                self.progress_bar.setVisible(is_busy)
        
        # --- ADDED: 显示或隐藏进度相关的标签 - 根据操作类型决定 ---
        if hasattr(self, 'phase_label'):
            if operation_type == "search":
                self.phase_label.setVisible(False)
            else:
                self.phase_label.setVisible(is_busy)
        if hasattr(self, 'detail_label'):
            if operation_type == "search":
                self.detail_label.setVisible(False)
            else:
                self.detail_label.setVisible(is_busy)


    def _update_feature_availability(self):
        """更新UI基于许可证状态，启用或禁用专业版功能"""
        # 确保许可证管理器实例是最新的
        self.license_manager = get_license_manager()
        
        # 检查各种功能是否可用
        folder_tree_available = self.license_manager.is_feature_available(Features.FOLDER_TREE)
        pdf_support_available = self.license_manager.is_feature_available(Features.PDF_SUPPORT)
        email_support_available = self.license_manager.is_feature_available(Features.EMAIL_SUPPORT)
        markdown_support_available = self.license_manager.is_feature_available(Features.MARKDOWN_SUPPORT)
        wildcards_available = self.license_manager.is_feature_available(Features.WILDCARDS)
        advanced_themes_available = self.license_manager.is_feature_available(Features.ADVANCED_THEMES)
        
        # 更新主菜单中的专业版菜单
        self._update_pro_menu()
        
        # 更新文件夹树的可见性
        if hasattr(self, 'main_splitter') and hasattr(self, 'folder_tree'):
            # 获取主分隔器中的左侧窗口小部件（应该是包含文件夹树的容器）
            left_container = self.main_splitter.widget(0)
            
            if left_container:
                left_container.setVisible(folder_tree_available)
                
                # 调整分隔器大小
                if folder_tree_available:
                    # 如果显示文件夹树，设置分隔器位置为1/4处
                    self.main_splitter.setSizes([200, 600])
        else:
                    # 如果不显示文件夹树，将宽度设置为0，让右侧搜索结果占满宽度
                    self.main_splitter.setSizes([0, self.main_splitter.width()])
        
        # 更新文件类型复选框的状态
        if hasattr(self, 'file_type_checkboxes') and hasattr(self, 'pro_file_types'):
            # 遍历所有的专业版文件类型复选框
            for checkbox, info in self.pro_file_types.items():
                feature = info.get('feature')
                pro_label = info.get('pro_label')
                available = self.license_manager.is_feature_available(feature)
                
                # 更新复选框状态
                checkbox.setEnabled(available)
                checkbox.setStyleSheet("" if available else "color: #888888;")
                if pro_label:
                    # 如果功能可用，隐藏专业版标签
                    pro_label.setVisible(not available)
                
                # 如果功能不可用，确保复选框未被选中
                if not available:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)
        
        # 更新主题设置
        current_theme = self.settings.value("ui/theme", "现代蓝")
        if not advanced_themes_available and current_theme not in ["现代蓝", "系统默认"]:
            # 如果高级主题不可用，但当前主题是高级主题，切换回基本主题
            self.settings.setValue("ui/theme", "现代蓝")
            self.apply_theme("现代蓝")

    @Slot()
    def show_license_dialog_slot(self):
        """显示许可证对话框"""
        # 创建许可证对话框
        from license_dialog import LicenseDialog
        license_dialog = LicenseDialog(self)

        # 连接许可证对话框的状态更新信号
        license_dialog.license_status_updated_signal.connect(self._update_feature_availability)

        # 执行对话框
        license_dialog.exec()
        
        # 对话框关闭后，更新UI以反映许可证状态
        self._update_feature_availability()
        
        # 延迟后强制刷新UI，确保所有控件正确显示
        QTimer.singleShot(300, self._force_ui_refresh)
        
        # 检查高级主题是否可用，并相应地更新主题
        advanced_themes_available = self.license_manager.is_feature_available(Features.ADVANCED_THEMES)
        theme_name = self.settings.value("ui/theme", "系统默认")
        
        # 如果选择了高级主题但功能不可用，或者当前许可证状态需要更改主题
        if not advanced_themes_available and theme_name not in ["系统默认", "现代蓝"]:
            # 更改为默认主题
            self.settings.setValue("ui/theme", "现代蓝")
            self.apply_theme("现代蓝")
            
            # 应用图标到下拉框
            arrow_icon_path = get_resource_path("down_arrow_blue.png")
            if os.path.exists(arrow_icon_path):
                self._apply_direct_arrow_icons(arrow_icon_path)
        
        # 刷新菜单栏和UI以显示正确的许可证状态
        self._update_pro_menu()

    # --- ADDED: Shortcut Setup Method ---
    def _setup_shortcuts(self):
        """Creates and connects QShortcut instances."""
        # Shortcut to focus the search input field (Ctrl+F or Ctrl+L)
        focus_search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        focus_search_shortcut.activated.connect(self.search_line_edit.setFocus)
        # Alternative Ctrl+L (like browsers)
        focus_search_shortcut_l = QShortcut(QKeySequence("Ctrl+L"), self)
        focus_search_shortcut_l.activated.connect(self.search_line_edit.setFocus)

        # Shortcut to trigger search (Ctrl+Return/Enter)
        start_search_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        start_search_shortcut.activated.connect(self.start_search_slot)
        start_search_shortcut_enter = QShortcut(QKeySequence("Ctrl+Enter"), self) # Also map Ctrl+Enter
        start_search_shortcut_enter.activated.connect(self.start_search_slot)

        # Shortcut for Indexing (Ctrl+I)
        index_shortcut = QShortcut(QKeySequence("Ctrl+I"), self)
        index_shortcut.activated.connect(self.start_indexing_slot)

        # Add more shortcuts here if needed, e.g., for clear buttons
        # clear_search_shortcut = QShortcut(QKeySequence("Esc"), self.search_line_edit) # Esc in search box clears it?
        # clear_search_shortcut.activated.connect(self.clear_search_entry_slot)

    @Slot()
    def show_settings_dialog_slot(self):
        """Shows the Settings dialog."""
        dialog = SettingsDialog(self) # Create the dialog
        # No need to check dialog.exec() result here, 
        # saving happens within dialog's accept() method.
        if dialog.exec(): # Use if dialog.exec(): to check if OK was pressed
             # REMOVED applying settings here, as they are handled by specific slots now
             # self.apply_theme(self.settings.value("ui/theme", "系统默认")) 
             # self._apply_result_font_size()
             pass # No immediate action needed for the old combined dialog

    @Slot()
    def show_index_settings_dialog_slot(self):
        """Shows the Settings dialog filtered for Index settings."""
        dialog = SettingsDialog(self, category_to_show='index')
        dialog.exec() # Settings are saved within dialog's accept()

    @Slot()
    def show_search_settings_dialog_slot(self):
        """Shows the Settings dialog filtered for Search settings."""
        dialog = SettingsDialog(self, category_to_show='search')
        dialog.exec() # Settings are saved within dialog's accept()
        # No immediate UI update needed in MainWindow for case sensitivity yet

    @Slot()
    def show_interface_settings_dialog_slot(self):
        """Shows the Settings dialog filtered for Interface settings and applies changes."""
        dialog = SettingsDialog(self, category_to_show='interface')
        if dialog.exec(): # Check if OK was pressed
            print("Interface settings accepted. Applying theme and font size...")
            self.apply_theme(self.settings.value("ui/theme", "系统默认")) # Re-apply theme if it changed
            self._apply_result_font_size() # Re-apply font size if it changed

    @Slot()
    def show_about_dialog_slot(self):
        """Shows the About dialog."""
        # --- UPDATED: Include CURRENT_VERSION in About dialog --- 
        about_text = f"""
        <b>文智搜</b><br><br>
        版本: {CURRENT_VERSION}<br> 
        一个用于本地文档全文搜索的工具。<br><br>
        使用 Whoosh 索引, 支持多种文件类型。
        """
        QMessageBox.about(self, "关于", about_text)
        # ---------------------------------------------------------

    # --- ADDED: 打开使用帮助文档 ---
    @Slot()
    def show_help_documentation_slot(self):
        """打开使用帮助文档页面"""
        help_url = "https://azariasy.github.io/-wen-zhi-sou-website/faq.html"
        QDesktopServices.openUrl(QUrl(help_url))
    # ----------------------------

    # --- Theme Handling ---
    def apply_theme(self, theme_name):
        """应用指定的主题样式
        Args:
            theme_name (str): 主题名称，如"系统默认"、"现代蓝"、"现代紫"
        """
        self.settings.setValue("ui/theme", theme_name)
        
        # --- 检查高级主题是否可用 ---
        advanced_themes_available = self.license_manager.is_feature_available(Features.ADVANCED_THEMES)
        
        # --- 处理非现代蓝的专业版主题许可证检查 ---
        if theme_name != "现代蓝" and not advanced_themes_available:
            if not hasattr(self, '_theme_warning_shown'):
                self._theme_warning_shown = False
                
            if not self._theme_warning_shown:
                self._theme_warning_shown = True
                warning_msg = QMessageBox()
                warning_msg.setIcon(QMessageBox.Icon.Warning)
                warning_msg.setWindowTitle("主题受限")
                warning_msg.setText("高级主题仅在专业版中可用")
                warning_msg.setInformativeText(
                    "高级主题（现代紫、现代红、现代橙）仅在专业版中可用。\n"
                    "请升级到专业版以使用这些主题。"
                )
                warning_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                warning_msg.exec()
                
            theme_name = "现代蓝"
            self.settings.setValue("ui/theme", theme_name)
        
        # --- 更新主题管理器 ---
        self.theme_manager.set_current_theme(theme_name)

        # --- 应用主题 ---
        if theme_name == "现代蓝":
            try:
                # 使用现代蓝色主题
                
                # 加载蓝色样式表，使用资源路径解析器
                style_path = get_resource_path("blue_style.qss")
                print(f"资源路径解析: blue_style.qss -> {style_path}")
                
                with open(style_path, "r", encoding="utf-8") as style_file:
                    style_content = style_file.read()
                    self.setStyleSheet(style_content)
                    print("Applied modern blue theme.")
                    
                # --- 修正图像路径 ---
                self._update_theme_icons(theme_name)
            except Exception as e:
                print(f"Error applying modern blue style: {e}")
                # 如果无法加载现代蓝色主题，使用默认样式
                self.setStyleSheet("")
                
        elif theme_name == "现代紫":
            try:
                # 使用现代紫色主题
                
                # 加载紫色样式表，使用资源路径解析器
                style_path = get_resource_path("purple_style.qss")
                print(f"资源路径解析: purple_style.qss -> {style_path}")
                
                with open(style_path, "r", encoding="utf-8") as style_file:
                    style_content = style_file.read()
                    self.setStyleSheet(style_content)
                    print("Applied modern purple theme.")
                    
                # --- 修正图像路径 ---
                self._update_theme_icons(theme_name)
            except Exception as e:
                print(f"Error applying modern purple style: {e}. Falling back to modern blue theme.")
                self._apply_fallback_blue_theme()
        elif theme_name == "现代红":
            try:
                # 使用现代红色主题
                
                # 加载红色样式表，使用资源路径解析器
                style_path = get_resource_path("red_style.qss")
                print(f"资源路径解析: red_style.qss -> {style_path}")
                
                with open(style_path, "r", encoding="utf-8") as style_file:
                    style_content = style_file.read()
                    self.setStyleSheet(style_content)
                    print("Applied modern red theme.")
                    
                # --- 修正图像路径 ---
                self._update_theme_icons(theme_name)
            except Exception as e:
                print(f"Error applying modern red style: {e}. Falling back to modern blue theme.")
                self._apply_fallback_blue_theme()
        elif theme_name == "现代橙":
            try:
                # 使用现代橙色主题
                
                # 加载橙色样式表，使用资源路径解析器
                style_path = get_resource_path("orange_style.qss")
                print(f"资源路径解析: orange_style.qss -> {style_path}")
                
                with open(style_path, "r", encoding="utf-8") as style_file:
                    style_content = style_file.read()
                    self.setStyleSheet(style_content)
                    print("Applied modern orange theme.")
                    
                # --- 修正图像路径 ---
                self._update_theme_icons(theme_name)
            except Exception as e:
                print(f"Error applying modern orange style: {e}. Falling back to modern blue theme.")
                self._apply_fallback_blue_theme()
        else:
            # 默认使用蓝色主题
            self._apply_fallback_blue_theme()
            
        # === 更新虚拟滚动模型主题 ===
        if hasattr(self, 'virtual_results_model'):
            self.virtual_results_model.set_theme(theme_name)
            print(f"虚拟滚动模型主题已更新为: {theme_name}")
        # ===========================


    def _update_theme_icons(self, theme_name):
        """根据主题更新界面中的图标
        Args:
            theme_name: 主题名称
        """
        # 获取组合框中的箭头图标
        arrow_icon_path = None
        
        if theme_name == "现代蓝" or theme_name == "系统默认":
            arrow_icon_path = get_resource_path("down_arrow_blue.png")
        elif theme_name == "现代紫":
            arrow_icon_path = get_resource_path("down_arrow_purple.png")
        elif theme_name == "现代红":
            arrow_icon_path = get_resource_path("down_arrow_red.png")
        elif theme_name == "现代橙":
            arrow_icon_path = get_resource_path("down_arrow_orange.png")
            
        if arrow_icon_path and os.path.exists(arrow_icon_path):
            # 通过代码设置图标路径，确保在所有环境下正确显示
            self._apply_direct_arrow_icons(arrow_icon_path)
    
    def _apply_direct_arrow_icons(self, arrow_icon_path):
        """直接将箭头图标应用到下拉框
        
        Args:
            arrow_icon_path: 箭头图标路径
        """
        try:
            # 规范化路径，确保在样式表中使用正确的路径分隔符
            icon_path = arrow_icon_path.replace('\\', '/').replace('\\', '/')
            
            # 将图标应用到所有下拉框
            for widget in [self.search_combo, self.scope_combo, self.mode_combo, self.view_mode_combo]:
                if widget:
                    try:
                        # 设置自定义样式表以使用新图标
                        widget.setStyleSheet(f"""
                            QComboBox::down-arrow {{
                                image: url({icon_path});
                                width: 14px;
                                height: 14px;
                            }}
                        """)
                    except Exception as e:
                        print(f"应用箭头图标到下拉框时出错: {e}")
                        
        except Exception as e:
            print(f"应用箭头图标时出错: {e}")
    def _apply_fallback_blue_theme(self):
        """在其他主题不可用时应用默认蓝色主题"""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        try:
            # 使用资源路径解析器加载蓝色样式表
            style_path = get_resource_path("blue_style.qss")
            if os.path.exists(style_path):
                with open(style_path, "r", encoding="utf-8") as f:
                    stylesheet = f.read()
                
                # 检查打包环境下的路径并修改URL引用
                if getattr(sys, 'frozen', False):
                    # 在PyInstaller打包后的环境中
                    print("检测到打包环境，应用相对路径处理...")
                    # 获取资源文件所在的目录
                    base_path = sys._MEIPASS
                    
                    # 修改样式表中的图片URL路径为绝对路径
                    # 这解决了在打包环境中图片路径引用的问题
                    stylesheet = stylesheet.replace('image: url(', f'image: url("{base_path}/")')
                    stylesheet = stylesheet.replace('.png)', '.png")')
                    
                    # 同时保持原有的替换逻辑
                    stylesheet = stylesheet.replace("image: url(checkmark.png)", "image: url(checkmark_blue.png)")
                    stylesheet = stylesheet.replace("image: url(down_arrow.png)", "image: url(down_arrow_blue.png)")
                else:
                    # 在开发环境中
                    stylesheet = stylesheet.replace("image: url(checkmark.png)", "image: url(checkmark_blue.png)")
                    stylesheet = stylesheet.replace("image: url(down_arrow.png)", "image: url(down_arrow_blue.png)")
                
                    app.setStyleSheet(stylesheet)
                print("Applied fallback blue theme.")
                
                # 通过编程方式直接设置下拉箭头和单选按钮图标
                # 这是一种备选方法，如果通过样式表无法正确设置图标
                try:
                    from PySide6.QtGui import QIcon, QPixmap
                    arrow_icon_path = get_resource_path("down_arrow_blue.png")
                    radio_icon_path = get_resource_path("radio_checked_blue.png")
                    check_icon_path = get_resource_path("checkmark_blue.png")
                    
                    if os.path.exists(arrow_icon_path):
                        down_arrow_icon = QIcon(arrow_icon_path)
                        # 将图标应用于应用程序范围的图标设置
                        app.setProperty("down_arrow_icon", down_arrow_icon)
                        print(f"已通过代码设置下拉箭头图标: {arrow_icon_path}")
                except Exception as e:
                    print(f"通过代码设置图标时发生错误: {e}")
                
                # 更新样式设置
                self.settings.setValue("ui/theme", "现代蓝")
            else:
                print(f"Blue style file not found: {style_path}")
                # 如果找不到样式表文件，使用系统默认样式
                app.setStyleSheet("")
        except Exception as e:
            print(f"Error applying fallback blue style: {e}. Using system default.")
            # 如果出现错误，使用系统默认样式
            app.setStyleSheet("")

    # --- Load and Apply Default View Mode Settings --- 
    def _load_and_apply_default_sort(self):
        """Loads default view mode settings and applies them to the UI controls."""
        default_view_mode = self.settings.value("search/defaultViewMode", 0, type=int) # Default: 列表视图
        
        print(f"DEBUG: Loading default view mode setting - Read Mode: {default_view_mode}") # DETAILED DEBUG

        # Apply to View Mode ComboBox
        if hasattr(self, 'view_mode_combo') and default_view_mode < self.view_mode_combo.count():
            self.view_mode_combo.setCurrentIndex(default_view_mode)
            self.current_view_mode = default_view_mode
        else:
            print(f"Warning: Default view mode '{default_view_mode}' is invalid. Using default.")
            if hasattr(self, 'view_mode_combo'):
                self.view_mode_combo.setCurrentIndex(0) # Fallback to first item
            self.current_view_mode = 0
            
    def _save_default_sort(self):
        """Saves the current view mode settings as the new default."""
        if hasattr(self, 'view_mode_combo'):
            current_view_mode = self.view_mode_combo.currentIndex()
            print(f"DEBUG: Saving default view mode setting - Current Mode: {current_view_mode}") # DETAILED DEBUG
            self.settings.setValue("search/defaultViewMode", current_view_mode)
        # self.settings.sync() # Explicit sync usually not needed, but can try if issues persist

    def _apply_result_font_size(self):
        """Applies the font size setting to the results display area."""
        default_font_size = 10
        font_size = self.settings.value("ui/resultFontSize", default_font_size, type=int)
        print(f"DEBUG: Applying result font size: {font_size}pt") # DEBUG
        current_font = self.results_text.font() # Get current font
        current_font.setPointSize(font_size)     # Set the desired point size
        self.results_text.setFont(current_font)  # Apply the modified font

    # --- 添加首次启动检查方法 ---
    def _check_first_launch(self):
        """检查是否是首次启动，如果是则引导用户设置索引"""
        # 检查是否已运行过该软件
        first_launch = self.settings.value("app/firstLaunch", True, type=bool)
        
        # 检查是否已配置源目录
        source_dirs = self.settings.value("indexing/sourceDirectories", [], type=list)
        
        if first_launch or not source_dirs:
            # 显示欢迎信息
            welcome_msg = "欢迎使用文智搜!\n\n" \
                          "为了帮助您开始使用，请先设置需要索引的文件夹。\n" \
                          "点击确定将打开设置页面，您可以在其中添加要搜索的文件夹。\n\n" \
                          "添加文件夹后，请点击\"创建索引\"按钮来开始索引过程。"
            
            QMessageBox.information(self, "首次启动设置", welcome_msg)
            
            # 自动打开索引设置对话框
            self.show_index_settings_dialog_slot()
            
            # 添加主界面提示
            self.statusBar().showMessage("请设置要索引的文件夹，然后点击\"创建索引\"按钮", 10000)
            
            # 记录已不是首次启动
            self.settings.setValue("app/firstLaunch", False)

    # --- ADDED: Slots for handling update check results ---
    @Slot()
    def check_for_updates_slot(self):
        """Initiates the update check process."""
        if self.is_busy:
            QMessageBox.warning(self, "忙碌中", "请等待当前操作完成。")
            return
        
        # Show immediate feedback that check is starting
        self.statusBar().showMessage("正在检查更新...", 0) 
        self.set_busy_state(True, "update") # Prevent other actions during check
        
        # Trigger the worker
        # Pass current version and URL from constants
        self.startUpdateCheckSignal.emit(CURRENT_VERSION, UPDATE_INFO_URL)

    @Slot(dict)
    def show_update_available_dialog_slot(self, update_info):
        """Displays a dialog indicating an update is available."""
        self.set_busy_state(False, "update") # Reset busy state
        self.statusBar().showMessage("发现新版本", 5000) # Update status
        
        latest_version = update_info.get('version', '未知')
        release_date = update_info.get('release_date', '未知')
        notes = update_info.get('notes', '无说明')
        download_url = update_info.get('download_url', '')
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("发现新版本")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setTextFormat(Qt.RichText) # Allow HTML link
        
        text = f"发现新版本: <b>{latest_version}</b> (发布于 {release_date})<br><br>"
        text += f"<b>更新内容:</b><br>{html.escape(notes)}<br><br>"
        if download_url:
            text += f"是否前往下载页面？<br><a href=\"{download_url}\">{download_url}</a>"
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.Yes)
        else:
            text += "请访问官方渠道获取更新。"
            msg_box.setStandardButtons(QMessageBox.Ok)
            
        msg_box.setText(text)
        
        
        result = msg_box.exec()
        
        if download_url and result == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl(download_url))

    @Slot()
    def show_up_to_date_dialog_slot(self):
        """Displays a dialog indicating the application is up to date."""
        self.set_busy_state(False, "update") # Reset busy state
        self.statusBar().showMessage("已是最新版本", 3000)
        QMessageBox.information(self, "检查更新", "您当前使用的是最新版本。")

    @Slot(str)
    def show_update_check_failed_dialog_slot(self, error_message):
        """Displays a dialog indicating the update check failed."""
        self.set_busy_state(False, "update") # Reset busy state
        self.statusBar().showMessage("检查更新失败", 3000)
        
        # 避免重复弹出对话框，检查是否已经存在更新错误对话框
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMessageBox) and widget.windowTitle() == "检查更新失败":
                print("已存在更新错误对话框，不再重复显示")
                return
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("检查更新失败")
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setTextFormat(Qt.RichText)  # 启用富文本
        
        # 主要错误消息
        message = f"无法完成更新检查：\n{error_message}\n\n"
        
        # 添加手动访问更新页面的建议和链接
        website_url = "https://azariasy.github.io/-wen-zhi-sou-website/"
        message += f'您可以尝试手动访问我们的网站查看最新版本：<br><a href="{website_url}">{website_url}</a>'
        
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        # 添加一个直接打开网站的按钮
        open_website_button = msg_box.addButton("访问网站", QMessageBox.ActionRole)
        
        result = msg_box.exec()
        
        # 如果用户点击了"访问网站"按钮
        if msg_box.clickedButton() == open_website_button:
            QDesktopServices.openUrl(QUrl(website_url))
    # ------------------------------------------------------

    # --- Cleanup --- 
    def closeEvent(self, event):
        """Handle window close event to clean up the worker thread and save settings."""
        print("DEBUG: closeEvent started...") # DEBUG
        print("接收到关闭事件，开始清理和保存...")
        
        # --- Save Settings --- 
        self._save_window_geometry() 
        self._save_default_sort() # Save current sort settings as default
        
        # --- 保存分隔器状态 ---
        self.settings.setValue("ui/splitterState", self.main_splitter.saveState())
        # -----------------------
        
        # --- 确保所有设置被写入磁盘 ---
        self.settings.sync()
        
        # --- 确保许可证信息被保存 ---
        if hasattr(self, 'license_manager'):
            # 这将触发LicenseManager的_save_license_info方法
            license_status = self.license_manager.get_license_status()
            print(f"正在保存许可证状态: {license_status}")
        # ---------------------------------

        # --- Stop Worker Thread --- 
        if self.worker_thread and self.worker_thread.isRunning():
            print("  尝试退出线程...")
            # 停止任何正在进行的操作
            if self.worker:
                # 首先尝试断开所有信号连接，防止在清理过程中触发回调
                try:
                    # 断开工作线程的信号连接
                    self.worker.statusChanged.disconnect()
                    self.worker.progressUpdated.disconnect()
                    self.worker.resultsReady.disconnect()
                    self.worker.indexingComplete.disconnect()
                    self.worker.errorOccurred.disconnect()
                    
                    # 断开主线程发送到工作线程的信号
                    self.startIndexingSignal.disconnect()
                    self.startSearchSignal.disconnect()
                    # --- ADDED: Connect update check signal to worker ---
                    self.startUpdateCheckSignal.disconnect()
                    # ---------------------------------------------------
                except Exception as e:
                    print(f"  断开信号时发生错误: {str(e)}")
                    pass  # 忽略任何断开连接错误
                
                # 确保工作线程知道需要停止任何长时间运行的操作
                if hasattr(self.worker, 'stop_requested'):
                    self.worker.stop_requested = True
                
                # 给工作线程一些时间来响应停止请求
                time.sleep(0.2)
            
            # 请求线程退出并等待
            print("  请求线程退出...")
            self.worker_thread.quit()  # 请求事件循环退出
            
            # 等待线程退出，使用更积极的超时策略
            timeout_ms = 5000  # 最多等待5秒
            if not self.worker_thread.wait(timeout_ms):
                print(f"  警告: 线程未能在{timeout_ms/1000}秒内退出，将强制终止。")
                
                # 在终止前，再次检查线程状态
                if self.worker_thread.isRunning():
                    print("  线程仍在运行，执行强制终止...")
                    self.worker_thread.terminate()  # 强制终止线程
                    
                    # 再等待一小段时间确保终止完成
                    if not self.worker_thread.wait(1000): 
                        print("  严重警告: 即使在强制终止后，线程仍未停止!")
                    else:
                        print("  线程已成功强制终止。")
                else:
                    print("  线程现在已停止运行。")
            else:
                print("  线程成功正常退出。")
        else:
            print("  线程未运行或已清理。")

        # 显式设置对象为None，帮助垃圾回收
        if hasattr(self, 'worker') and self.worker:
            self.worker.deleteLater()
            self.worker = None
            
        if hasattr(self, 'worker_thread') and self.worker_thread:
            self.worker_thread.deleteLater()
            self.worker_thread = None

        print("清理完成，接受关闭事件。")
        print("DEBUG: closeEvent finishing...") # DEBUG
        
        # 接受关闭事件
        event.accept()

    @Slot()
    def start_indexing_slot(self):
        """Slot to initiate the indexing process."""
        if self.is_busy:
            QMessageBox.warning(self, "忙碌中", "请等待当前操作完成。")
            return

        # --- MODIFIED: Read source directories from settings ---
        source_dirs = self.settings.value("indexing/sourceDirectories", [])
        if not isinstance(source_dirs, list):
            source_dirs = [] if source_dirs is None else [source_dirs]

        print(f"DEBUG: start_indexing_slot 读取源目录 = {source_dirs}")

        if not source_dirs:
             QMessageBox.warning(self, "未配置源目录", "请先前往 \"设置 -> 索引设置\" 添加需要索引的文件夹。")
             return
        # -----------------------------------------------------

        # --- Get Index Directory from Settings ---
        default_index_path = str(Path.home() / "Documents" / "DocumentSearchIndex")
        index_dir = self.settings.value("indexing/indexDirectory", default_index_path) # Use specific key
        if not index_dir:
            # This check might be redundant if settings dialog enforces it, but good safety check
            QMessageBox.critical(self, "错误", "未配置索引存储位置！请在设置中指定。")
            return
        # ------------------------------------------

        # --- ADDED: Check if index directory exists, create if it doesn't ---
        index_path = Path(index_dir)
        if not index_path.exists():
            try:
                index_path.mkdir(parents=True, exist_ok=True)
                print(f"索引目录不存在，已创建: {index_dir}")
                self.statusBar().showMessage(f"已创建索引目录: {index_dir}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法创建索引目录: {index_dir}\n错误: {e}")
                return
        # -------------------------------------------------------------------

        # --- ADDED: Get OCR Setting --- 
        enable_ocr = self.settings.value("indexing/enableOcr", True)
        if isinstance(enable_ocr, str):
            enable_ocr = enable_ocr.lower() in ('true', '1', 'yes')
        enable_ocr = bool(enable_ocr)
        # ------------------------------

        # --- ADDED: Get Extraction Timeout Setting ---
        extraction_timeout = self.settings.value("indexing/extractionTimeout", 120)
        try:
            extraction_timeout = int(extraction_timeout)
        except (ValueError, TypeError):
            extraction_timeout = 120
        # ---------------------------------------------

        # --- ADDED: Get TXT Content Limit Setting --- 
        txt_content_limit_kb = self.settings.value("indexing/txtContentLimitKb", 1024)
        try:
            txt_content_limit_kb = int(txt_content_limit_kb)
        except (ValueError, TypeError):
            txt_content_limit_kb = 1024
        # -------------------------------------------

        # --- ADDED: 获取文件类型和模式设置 ---
        selected_file_types = self.settings.value("indexing/selectedFileTypes", [])
        if not isinstance(selected_file_types, list):
            selected_file_types = [] if selected_file_types is None else [selected_file_types]

        file_type_modes = self.settings.value("indexing/fileTypeModes", {})
        if not isinstance(file_type_modes, dict):
            file_type_modes = {}

        print(f"DEBUG: start_indexing_slot 读取 'indexing/selectedFileTypes' = {selected_file_types}")
        print(f"DEBUG: start_indexing_slot 读取 'indexing/fileTypeModes' = {file_type_modes}")
        
        # 如果文件类型列表为空，询问用户是否使用所有文件类型
        if not selected_file_types:
            reply = QMessageBox.question(
                self, 
                "未选择文件类型", 
                "您没有选择任何要索引的文件类型。\n\n请问您是否希望索引所有支持的文件类型？\n\n如果选择\"否\"，您可以前往\"设置 -> 索引设置\"选择需要索引的文件类型。",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # 用户确认使用所有文件类型
                selected_file_types = ['txt', 'docx', 'xlsx', 'pptx', 'html', 'rtf', 'zip', 'rar', 'pdf', 'md', 'eml', 'msg']
                # 为所有类型设置默认完整索引模式
                file_type_modes = {ft: "full" for ft in selected_file_types}
                print(f"DEBUG: 用户确认使用所有支持的类型: {selected_file_types}")
            else:
                # 用户取消操作
                print(f"DEBUG: 用户取消了索引操作，因为未选择文件类型")
                return
            
        # 分离完整索引和仅文件名索引的文件类型
        full_index_types = []
        filename_only_types = []

        # 遍历所有文件类型模式设置，不仅仅是选中的文件类型
        all_possible_types = set(selected_file_types)
        all_possible_types.update(file_type_modes.keys())  # 确保包含所有配置的类型

        for file_type in all_possible_types:
            # 首先检查该文件类型是否被用户勾选
            if file_type not in selected_file_types:
                continue  # 未勾选的文件类型直接跳过，无论什么模式

            mode = file_type_modes.get(file_type, "full")  # 默认完整索引
            if mode == "filename_only":
                filename_only_types.append(file_type)
            else:
                full_index_types.append(file_type)

        print(f"DEBUG: 完整索引类型: {full_index_types}")
        print(f"DEBUG: 仅文件名索引类型: {filename_only_types}")

        file_types_str = "所有支持的类型" if len(selected_file_types) == 12 else f"{', '.join(selected_file_types)}"
        # ---------------------------------------

        # Updated print to include all settings
        print(f"开始索引 {len(source_dirs)} 个源目录 -> '{index_dir}'")
        print(f"- OCR: {enable_ocr}")
        print(f"- 单文件提取超时: {extraction_timeout}秒") 
        print(f"- TXT文件大小限制: {txt_content_limit_kb}KB")
        print(f"- 索引文件类型: {file_types_str}")

        self.set_busy_state(True, "index")
        self.results_text.clear()  # Clear previous results/logs
        self.statusBar().showMessage(f"开始准备索引 {len(source_dirs)} 个源目录...", 3000)

        # --- MODIFIED: 传递文件类型过滤参数 --- 
        # 将文件类型数据打包传递
        file_type_config = {
            'full_index_types': full_index_types,
            'filename_only_types': filename_only_types
        }
        self.startIndexingSignal.emit(source_dirs, index_dir, enable_ocr, extraction_timeout, txt_content_limit_kb, file_type_config)
        # -------------------------------------------------------
    
    def _open_selected_folder(self):
        """打开选中文件所在的文件夹"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        # 从第一个单元格获取存储的完整数据
        item_data = self.table.item(row, 0).data(Qt.UserRole)
        file_path = item_data["file_path"]
        
        # 获取文件夹路径
        folder_path = ""
        if "::" in file_path:
            archive_path = file_path.split("::")[0]
            folder_path = str(Path(archive_path).parent)
        else:
            folder_path = str(Path(file_path).parent)
            
        # 使用主窗口的方法打开文件夹
        if self.parent():
            self.parent()._open_path_with_desktop_services(folder_path, is_file=False)
    
    def _clear_log(self):
        """清空跳过文件的日志"""
        reply = QMessageBox.question(self, "确认清空", 
                                   "确定要清空跳过文件的记录吗？此操作不可撤销。",
                                   QMessageBox.Yes | QMessageBox.No, 
                                   QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
            
        # 获取索引目录
        default_index_path = str(Path.home() / "Documents" / "DocumentSearchIndex")
        index_dir = self.settings.value("indexing/indexDirectory", default_index_path)
        
        if not index_dir or not os.path.exists(index_dir):
            QMessageBox.warning(self, "错误", "索引目录不存在或未配置！")
            return
            
        # 构建日志文件路径
        log_file_path = os.path.join(index_dir, "index_skipped_files.tsv")
        
        try:
            # 清空文件，但保留表头 - 确保使用与读取时相同的字段名
            import csv
            with open(log_file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f, delimiter='\t')
                # 使用与_load_skipped_files方法中相同的表头字段
                writer.writerow(["文件路径", "跳过原因", "时间"])
                
            print(f"DEBUG: 已清空跳过文件记录，创建了新的TSV文件，表头: ['文件路径', '跳过原因', '时间']")
                
            # 清空内存中的记录并更新UI
            self.skipped_files = []
            self._apply_filter()
            QMessageBox.information(self, "已清空", "跳过文件记录已清空。")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"清空记录时出错: {e}")
            import traceback
            print(f"清空记录错误: {e}\n{traceback.format_exc()}")
    
    def showEvent(self, event):
        """窗口显示时仅调用父类方法并打印调试信息"""
        print("DEBUG: SkippedFilesDialog showEvent triggered.") # Simple debug message
        super().showEvent(event)
        # 不再在此处加载数据或清空表格，因为__init__和_update_ui会处理

    def closeEvent(self, event):
        """保存窗口大小并确保正确关闭"""
        try:
            self.settings.setValue("skippedFilesDialog/geometry", self.saveGeometry())
        except Exception as e:
            print(f"保存窗口几何信息时出错: {e}")
        
        # 确保关闭事件被接受
        event.accept()
        super().closeEvent(event)

    def _update_button_states(self):
        """根据当前选择状态更新按钮的启用状态"""
        # 无论选择哪种搜索模式，应用按钮始终可用
        self.apply_button.setEnabled(True)

    @Slot()
    def show_skipped_files_dialog_slot(self):
        """显示被跳过文件的对话框"""
        try:
            # 如果对话框已经存在，则只需显示它
            if hasattr(self, 'skipped_files_dialog') and self.skipped_files_dialog:
                self.skipped_files_dialog.show()
                self.skipped_files_dialog.raise_()  # 确保对话框位于前台
                self.skipped_files_dialog.activateWindow()  # 激活窗口
                return
                
            # 直接在此创建一个简单的跳过文件对话框
            class SimpleSkippedFilesDialog(QDialog):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("跳过的文件")
                    self.resize(800, 500)
                    self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
                    
                    # 创建布局
                    layout = QVBoxLayout(self)
                    
                    # 添加说明标签
                    info_label = QLabel("以下文件在索引过程中被跳过：")
                    layout.addWidget(info_label)
                    
                    # 创建表格
                    self.table = QTableWidget()
                    self.table.setColumnCount(3)
                    self.table.setHorizontalHeaderLabels(["文件路径", "跳过原因", "时间"])
                    self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
                    self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
                    self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
                    # 设置表格选择整行
                    self.table.setSelectionBehavior(QTableWidget.SelectRows)
                    # 双击打开文件
                    self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
                    # 右键菜单
                    self.table.setContextMenuPolicy(Qt.CustomContextMenu)
                    self.table.customContextMenuRequested.connect(self._show_context_menu)
                    # 连接表格选择变更信号
                    self.table.itemSelectionChanged.connect(self._update_button_states)
                    layout.addWidget(self.table)
                    
                    # 创建过滤部分
                    filter_layout = QHBoxLayout()
                    filter_label = QLabel("过滤条件:")
                    self.filter_entry = QLineEdit()
                    self.filter_entry.setPlaceholderText("输入关键词过滤")
                    self.filter_entry.textChanged.connect(self._apply_filter)
                    filter_layout.addWidget(filter_label)
                    filter_layout.addWidget(self.filter_entry, 1)
                    layout.addLayout(filter_layout)
                    
                    # 创建按钮
                    button_layout = QHBoxLayout()
                    self.clear_log_button = QPushButton("清空日志")
                    self.clear_log_button.clicked.connect(self._clear_log)
                    self.open_file_button = QPushButton("打开文件")
                    self.open_file_button.clicked.connect(self._open_selected_file)
                    self.open_folder_button = QPushButton("打开所在文件夹")
                    self.open_folder_button.clicked.connect(self._open_selected_folder)
                    close_button = QPushButton("关闭")
                    close_button.clicked.connect(self.accept)
                    button_layout.addWidget(self.clear_log_button)
                    button_layout.addWidget(self.open_file_button)
                    button_layout.addWidget(self.open_folder_button)
                    button_layout.addStretch()
                    button_layout.addWidget(close_button)
                    layout.addLayout(button_layout)
                    
                    # 加载跳过文件数据
                    self._load_skipped_files()
                    
                    # 恢复窗口位置和大小
                    self._restore_geometry()
                    
                    # 更新按钮状态
                    self._update_button_states()
                    
                    # 设置窗口特性，允许最大化
                    self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
                
                def showEvent(self, event):
                    super().showEvent(event)
                    # 恢复窗口状态
                    if self.settings.contains("skippedFilesDialog/state"):
                        self.restoreState(self.settings.value("skippedFilesDialog/state"))
                
                def closeEvent(self, event):
                    # 保存窗口几何信息和状态
                    self._save_geometry()
                    super().closeEvent(event)
                
                def _save_geometry(self):
                    """保存窗口位置和大小"""
                    self.settings.setValue("skippedFilesDialog/geometry", self.saveGeometry())
                    if hasattr(self, "saveState"):
                        self.settings.setValue("skippedFilesDialog/state", self.saveState())
                
                def _restore_geometry(self):
                    """恢复窗口位置和大小"""
                    if self.settings.contains("skippedFilesDialog/geometry"):
                        self.restoreGeometry(self.settings.value("skippedFilesDialog/geometry"))
                
                def _update_button_states(self):
                    """更新按钮状态"""
                    selected_items = self.table.selectedItems()
                    has_selection = len(selected_items) > 0
                    self.open_file_button.setEnabled(has_selection)
                    self.open_folder_button.setEnabled(has_selection)
                
                def _on_cell_double_clicked(self, row, column):
                    """双击单元格时打开文件"""
                    try:
                        import os, sys  # 导入必要的模块
                        
                        file_path = self.table.item(row, 0).text()
                        
                        if not os.path.exists(file_path):
                            QMessageBox.warning(self, "文件不存在", f"找不到文件:\n{file_path}")
                            return
                        
                        # 直接使用QDesktopServices打开文件，避免直接调用self._open_selected_file()
                        url = QUrl.fromLocalFile(str(file_path))
                        result = QDesktopServices.openUrl(url)
                        
                        if not result and sys.platform == 'win32':
                            try:
                                # 使用startfile而不是subprocess.Popen，更安全
                                os.startfile(file_path)
                            except Exception as e:
                                QMessageBox.warning(self, "打开失败", f"无法打开文件:\n{file_path}\n\n错误: {e}")
                    except Exception as e:
                        print(f"双击打开文件时出错: {e}")
                        import traceback
                        traceback.print_exc()
                
                def _show_context_menu(self, pos):
                    """显示右键菜单"""
                    selected_items = self.table.selectedItems()
                    if not selected_items:
                        return
                        
                    menu = QMenu(self)
                    open_file_action = menu.addAction("打开文件")
                    open_folder_action = menu.addAction("打开所在文件夹")
                    
                    # 使用exec代替exec_
                    action = menu.exec(self.table.mapToGlobal(pos))
                    
                    if action == open_file_action:
                        self._open_selected_file()
                    elif action == open_folder_action:
                        self._open_selected_folder()
                
                def _open_selected_file(self):
                    """打开选中的文件"""
                    import os, sys  # 导入必要的模块
                    
                    selected_items = self.table.selectedItems()
                    if not selected_items:
                        return
                        
                    row = selected_items[0].row()
                    file_path = self.table.item(row, 0).text()
                    
                    if not os.path.exists(file_path):
                        QMessageBox.warning(self, "文件不存在", f"找不到文件:\n{file_path}")
                        return
                    
                    # 直接使用QDesktopServices打开文件，避免调用parent方法
                    url = QUrl.fromLocalFile(str(file_path))
                    result = QDesktopServices.openUrl(url)
                    
                    if not result and sys.platform == 'win32':
                        try:
                            # 使用startfile而不是subprocess.Popen，更安全
                            os.startfile(file_path)
                        except Exception as e:
                            QMessageBox.warning(self, "打开失败", f"无法打开文件:\n{file_path}\n\n错误: {e}")
                
                def _open_selected_folder(self):
                    """打开所选文件所在的文件夹"""
                    import os, sys  # 导入必要的模块
                    
                    selected_items = self.table.selectedItems()
                    if not selected_items:
                        return
                        
                    row = selected_items[0].row()
                    file_path = self.table.item(row, 0).text()
                    folder_path = os.path.dirname(file_path)
                    
                    if not os.path.exists(folder_path):
                        QMessageBox.warning(self, "文件夹不存在", f"找不到文件夹:\n{folder_path}")
                        return
                    
                    # 直接使用QDesktopServices打开文件夹，避免调用parent方法
                    url = QUrl.fromLocalFile(str(folder_path))
                    result = QDesktopServices.openUrl(url)
                    
                    if not result and sys.platform == 'win32':
                        try:
                            # 使用startfile而不是subprocess.Popen，更安全
                            os.startfile(folder_path)
                        except Exception as e:
                            QMessageBox.warning(self, "打开失败", f"无法打开文件夹:\n{folder_path}\n\n错误: {e}")
                
                def _load_skipped_files(self):
                    """从TSV文件加载被跳过的文件数据"""
                    self.skipped_files = []
                    
                    # 获取索引目录
                    default_index_path = str(Path.home() / "Documents" / "DocumentSearchIndex")
                    index_dir = self.settings.value("indexing/indexDirectory", default_index_path)
                    
                    if not index_dir or not os.path.exists(index_dir):
                        return
                    
                    # 构建日志文件路径
                    log_file_path = os.path.join(index_dir, "index_skipped_files.tsv")
                    
                    if not os.path.exists(log_file_path):
                        return
                    
                    try:
                        import csv
                        with open(log_file_path, 'r', encoding='utf-8', newline='') as f:
                            reader = csv.reader(f, delimiter='\t')
                            # 跳过表头行
                            headers = next(reader, None)
                            
                            # 针对旧版本可能的不同表头进行兼容处理
                            path_idx, reason_idx, time_idx = 0, 1, 2
                            if headers:
                                for i, header in enumerate(headers):
                                    if "路径" in header:
                                        path_idx = i
                                    elif "原因" in header:
                                        reason_idx = i
                                    elif "时间" in header:
                                        time_idx = i
                            
                            # 读取数据行
                            for row in reader:
                                if len(row) >= 3:
                                    file_path = row[path_idx]
                                    reason = row[reason_idx]
                                    timestamp = row[time_idx]
                                    self.skipped_files.append({
                                        'path': file_path,
                                        'reason': reason,
                                        'time': timestamp
                                    })
                        
                        # 更新UI
                        self._apply_filter()
                    except Exception as e:
                        print(f"读取跳过文件记录时出错: {e}")
                        import traceback
                        traceback.print_exc()
                        if self.parent():
                            QMessageBox.warning(self.parent(), "错误", f"读取跳过文件记录时出错: {e}")

                def _apply_filter(self):
                    """应用过滤器并更新表格"""
                    filter_text = self.filter_entry.text().lower()
                    self.table.setRowCount(0)
                    
                    if not self.skipped_files:
                        return
                    
                    # 过滤并显示结果
                    for item in self.skipped_files:
                        # 如果过滤文本为空或者任何字段包含过滤文本，则显示该项目
                        if not filter_text or \
                           filter_text in item['path'].lower() or \
                           filter_text in item['reason'].lower() or \
                           filter_text in item['time'].lower():
                            
                            row = self.table.rowCount()
                            self.table.insertRow(row)
                            
                            path_item = QTableWidgetItem(item['path'])
                            path_item.setToolTip(item['path'])
                            self.table.setItem(row, 0, path_item)
                            
                            reason_item = QTableWidgetItem(item['reason'])
                            reason_item.setToolTip(item['reason'])
                            self.table.setItem(row, 1, reason_item)
                            
                            time_item = QTableWidgetItem(item['time'])
                            self.table.setItem(row, 2, time_item)
                    
                    # 更新标题以显示过滤结果
                    if filter_text:
                        self.setWindowTitle(f"跳过的文件 (已过滤: {self.table.rowCount()}/{len(self.skipped_files)})")
                    else:
                        self.setWindowTitle(f"跳过的文件 ({len(self.skipped_files)})")
                        
                    # 更新按钮状态
                    self._update_button_states()

                def _clear_log(self):
                    """清空跳过文件的日志"""
                    reply = QMessageBox.question(self, "确认清空", 
                                               "确定要清空跳过文件的记录吗？此操作不可撤销。",
                                               QMessageBox.Yes | QMessageBox.No, 
                                               QMessageBox.No)
                    
                    if reply != QMessageBox.Yes:
                        return
                        
                    # 获取索引目录
                    default_index_path = str(Path.home() / "Documents" / "DocumentSearchIndex")
                    index_dir = self.settings.value("indexing/indexDirectory", default_index_path)
                    
                    if not index_dir or not os.path.exists(index_dir):
                        QMessageBox.warning(self, "错误", "索引目录不存在或未配置！")
                        return
                        
                    # 构建日志文件路径
                    log_file_path = os.path.join(index_dir, "index_skipped_files.tsv")
                    
                    try:
                        # 清空文件，但保留表头 - 确保使用与读取时相同的字段名
                        import csv
                        with open(log_file_path, 'w', encoding='utf-8', newline='') as f:
                            writer = csv.writer(f, delimiter='\t')
                            # 使用与_load_skipped_files方法中相同的表头字段
                            writer.writerow(["文件路径", "跳过原因", "时间"])
                            
                        # 清空内存中的记录并更新UI
                        self.skipped_files = []
                        self._apply_filter()
                        QMessageBox.information(self, "已清空", "跳过文件记录已清空。")
                        
                    except Exception as e:
                        QMessageBox.critical(self, "错误", f"清空记录时出错: {e}")
                        import traceback
                        print(f"清空记录错误: {e}\n{traceback.format_exc()}")
            
            # 创建我们刚刚定义的对话框
            self.skipped_files_dialog = SimpleSkippedFilesDialog(self)
            self.skipped_files_dialog.show()
        except Exception as e:
            print(f"显示跳过文件对话框时出错: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"显示跳过文件对话框时发生错误: {str(e)}")

    def _open_path_with_desktop_services(self, path, is_file=True):
        """使用QDesktopServices打开文件或文件夹。

        Args:
            path: 要打开的文件或文件夹路径
            is_file: 如果为True，则打开文件；如果为False，则打开文件夹
        """
        try:
            if not path:
                return

            # 检查路径是否存在
            path_obj = Path(path)
            if not path_obj.exists():
                QMessageBox.warning(self, "路径不存在", f"找不到{'文件' if is_file else '文件夹'}:\n{path}")
                return

            # 转换为QUrl格式
            url = QUrl.fromLocalFile(str(path_obj))
            
            # 使用QDesktopServices打开文件或文件夹
            result = QDesktopServices.openUrl(url)
            
            if not result:
                if sys.platform == 'win32':
                    # 在Windows上使用备用方法
                    import subprocess
                    try:
                        subprocess.Popen(f'explorer "{path}"', shell=True)
                    except Exception as e:
                        QMessageBox.warning(self, "打开失败", f"无法打开{'文件' if is_file else '文件夹'}:\n{path}\n\n错误: {e}")
                else:
                    QMessageBox.warning(self, "打开失败", f"无法打开{'文件' if is_file else '文件夹'}:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"尝试打开{'文件' if is_file else '文件夹'}时出错:\n{path}\n\n错误: {e}")

    # 在MainWindow类中添加通配符搜索帮助对话框函数
    def show_wildcard_help_dialog(self):
        """
        显示通配符搜索帮助对话框
        """
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea, QTabWidget
        from PySide6.QtCore import Qt
        
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("通配符与高级搜索帮助")
        layout = QVBoxLayout(help_dialog)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # ---------- 通配符选项卡 ----------
        wildcard_tab = QScrollArea()
        wildcard_widget = QLabel()
        wildcard_widget.setTextFormat(Qt.RichText)
        wildcard_widget.setWordWrap(True)
        
        wildcard_text = """
        <h3>通配符搜索指南</h3>
        
        <p><b>支持的通配符：</b></p>
        <ul>
            <li><b>*</b> - 匹配0或多个任意字符</li>
            <li><b>?</b> - 匹配1个任意字符</li>
        </ul>
        
        <p><b>使用示例：</b></p>
        <ul>
            <li><code>文档*方案</code> - 查找以"文档"开头，"方案"结尾的内容</li>
            <li><code>2023?报告</code> - 查找类似"2023年报告"、"2023季报告"等内容</li>
            <li><code>项目*计划*2023</code> - 查找含有"项目"、"计划"和"2023"的内容，顺序固定</li>
        </ul>
        
        <p><b>搜索限制与解决方案：</b></p>
        <ul>
            <li><b>中文分词影响</b>：通配符跨越分词边界时可能失效，例如"构建*发展"，推荐改为 <code>构建 AND 发展</code></li>
            <li><b>位置敏感</b>：开头通配符(<code>*词语</code>)效率较低，结尾通配符(<code>词语*</code>)效果更好</li>
            <li><b>文档格式影响</b>：PDF表格、图片文本可能影响匹配质量</li>
            <li><b>未知文件问题</b>：当文件元数据提取失败时，可能显示为未知文件，可尝试其他关键词</li>
        </ul>
        
        <p><b>最佳实践建议：</b></p>
        <ul>
            <li>优先使用<code>词语*</code>形式而非<code>*词语</code></li>
            <li>复杂查询使用逻辑运算符: <code>构建 AND 发展</code>优于<code>*构建*发展*</code></li>
            <li>当通配符查询失败时，尝试拆分为多个关键词用AND连接</li>
            <li>对于中文特定格式（如"十九届*全会"），系统会尝试多种匹配模式</li>
        </ul>
        
        <p><b>注意事项：</b></p>
        <ul>
            <li>通配符搜索仅在<b>模糊搜索模式</b>下可用</li>
            <li>以*开头的搜索可能较慢</li>
            <li>文件名搜索会自动添加首尾通配符</li>
            <li>不要使用过多通配符，可能影响性能</li>
        </ul>
        """
        wildcard_widget.setText(wildcard_text)
        wildcard_tab.setWidget(wildcard_widget)
        wildcard_tab.setWidgetResizable(True)
        
        # ---------- 逻辑运算符选项卡 ----------
        logic_tab = QScrollArea()
        logic_widget = QLabel()
        logic_widget.setTextFormat(Qt.RichText)
        logic_widget.setWordWrap(True)
        
        logic_text = """
        <h3>逻辑运算符指南</h3>
        
        <p><b>支持的逻辑运算符：</b></p>
        <ul>
            <li><b>AND</b> - 同时包含两个词语（默认运算符）</li>
            <li><b>OR</b> - 包含任一词语</li>
            <li><b>NOT</b> - 不包含某词语</li>
        </ul>
        
        <p><b>使用示例：</b></p>
        <ul>
            <li><code>国民经济 AND 发展</code> - 同时包含"国民经济"和"发展"</li>
            <li><code>规划 OR 计划</code> - 包含"规划"或"计划"</li>
            <li><code>计划 NOT 五年</code> - 包含"计划"但不包含"五年"</li>
            <li><code>国民 AND (经济 OR 健康) NOT 危机</code> - 复合条件搜索</li>
        </ul>
        
        <p><b>注意事项：</b></p>
        <ul>
            <li>逻辑运算符仅在<b>模糊搜索模式</b>下可用</li>
            <li>运算符必须使用大写 (AND、OR、NOT)</li>
            <li>运算符两侧需要有空格</li>
            <li>可以使用括号来分组，如<code>(A OR B) AND C</code></li>
        </ul>
        """
        logic_widget.setText(logic_text)
        logic_tab.setWidget(logic_widget)
        logic_tab.setWidgetResizable(True)
        
        # ---------- 高级搜索选项卡 ----------
        advanced_tab = QScrollArea()
        advanced_widget = QLabel()
        advanced_widget.setTextFormat(Qt.RichText)
        advanced_widget.setWordWrap(True)
        
        advanced_text = """
        <h3>高级搜索技巧</h3>
        
        <p><b>组合使用：</b></p>
        <ul>
            <li><code>计划* AND NOT 临时</code> - 以"计划"开头但不含"临时"的内容</li>
            <li><code>20?? AND (报告 OR 总结)</code> - 包含"20"开头的年份，且含有"报告"或"总结"</li>
        </ul>
        
        <p><b>搜索范围：</b></p>
        <ul>
            <li><b>全文搜索</b> - 搜索文档的全部内容</li>
            <li><b>文件名搜索</b> - 仅搜索文件名（自动添加通配符）</li>
        </ul>
        
        <p><b>高级过滤：</b></p>
        <ul>
            <li>使用右侧面板可按文件类型过滤</li>
            <li>使用左侧文件夹树可按文件位置过滤</li>
            <li>从设置菜单可设置更多过滤条件（如文件大小、日期）</li>
        </ul>
        """
        advanced_widget.setText(advanced_text)
        advanced_tab.setWidget(advanced_widget)
        advanced_tab.setWidgetResizable(True)
        
        # 添加选项卡到选项卡容器
        tab_widget.addTab(wildcard_tab, "通配符")
        tab_widget.addTab(logic_tab, "逻辑运算符") 
        tab_widget.addTab(advanced_tab, "高级搜索")
        
        # 添加确认按钮
        ok_button = QPushButton("了解了")
        ok_button.clicked.connect(help_dialog.accept)
        
        # 添加到主布局
        layout.addWidget(tab_widget)
        layout.addWidget(ok_button, 0, Qt.AlignCenter)
        
        # 设置对话框大小
        help_dialog.resize(500, 450)
        help_dialog.exec_()

    @Slot()
    def show_tray_settings_dialog_slot(self):
        """显示托盘设置对话框"""
        try:
            from tray_settings import TraySettingsDialog
            dialog = TraySettingsDialog(self)
            # 连接设置更新信号
            dialog.settings_updated_signal.connect(self._on_tray_settings_updated)
            dialog.exec()
        except ImportError:
            QMessageBox.information(self, "托盘设置", "托盘设置功能暂不可用。")
    
    def _on_tray_settings_updated(self):
        """托盘设置更新后的处理"""
        # 重新读取托盘设置并更新相关组件
        print("托盘设置已更新，刷新相关组件...")
        # 可以在这里添加更新托盘行为的代码
        self.statusBar().showMessage("托盘设置已更新", 3000)

    @Slot()
    def show_startup_settings_dialog_slot(self):
        """显示启动设置对话框"""
        from startup_settings import StartupSettingsDialog
        dialog = StartupSettingsDialog(self)
        dialog.exec()

    @Slot()
    def show_hotkey_settings_dialog_slot(self):
        """显示热键设置对话框"""
        try:
            from hotkey_settings import HotkeySettingsDialog
            dialog = HotkeySettingsDialog(self)
            # 连接设置更新信号
            dialog.hotkey_updated_signal.connect(self._on_hotkey_settings_updated)
            dialog.exec()
        except ImportError:
            QMessageBox.information(self, "热键设置", "热键设置功能暂不可用。")
    
    def _on_hotkey_settings_updated(self):
        """热键设置更新后的处理"""
        print("热键设置已更新，正在重新加载...")
        
        # 如果有热键管理器，重新加载热键设置
        if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
            self.hotkey_manager.reload_hotkeys()
            
        # 更新托盘菜单中的热键显示
        try:
            from dynamic_tray_menu import update_tray_menu_hotkeys
            # 这里需要获取托盘图标的引用
            # 由于MainWindow可能没有直接的托盘图标引用，我们稍后在TrayMainWindow中处理
            pass
        except ImportError:
            pass
            
        self.statusBar().showMessage("热键设置已更新，重启应用程序后生效", 5000)

    @Slot()
    def show_optimization_settings_dialog_slot(self):
        """显示索引优化设置对话框"""
        try:
            from gui_optimization_settings import OptimizationSettingsDialog
            dialog = OptimizationSettingsDialog(self)
            dialog.exec()
        except ImportError as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "索引优化设置", f"索引优化设置功能暂不可用:\n{str(e)}")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", f"打开索引优化设置时出现错误:\n{str(e)}")

    # --- ADDED: 取消索引的槽函数 ---
    @Slot()
    def cancel_indexing_slot(self):
        """取消正在进行的索引操作 - 完全借鉴closeEvent的线程中断机制"""
        print("🚨🚨🚨 CANCEL BUTTON CLICKED! 🚨🚨🚨")
        print("🚨🚨🚨 CANCEL BUTTON CLICKED! 🚨🚨🚨")
        print("🚨🚨🚨 CANCEL BUTTON CLICKED! 🚨🚨🚨")
        
        # 强制刷新控制台输出
        import sys
        import time
        sys.stdout.flush()
        sys.stderr.flush()
        
        print(f"is_busy: {self.is_busy}")
        print(f"has worker: {hasattr(self, 'worker')}")
        print(f"worker is not None: {self.worker is not None if hasattr(self, 'worker') else False}")
        print(f"worker_thread running: {self.worker_thread.isRunning() if hasattr(self, 'worker_thread') and self.worker_thread else False}")
        
        if not self.is_busy:
            print("⚠️ 当前没有正在进行的操作")
            return
        
        # 立即更新UI状态，让用户知道取消请求已收到
        self.statusBar().showMessage("🚨 正在强制取消索引操作，请稍候...", 0)
        if hasattr(self, 'cancel_index_button'):
            self.cancel_index_button.setEnabled(False)
            self.cancel_index_button.setText("🚨 正在强制取消...")
        
        # 强制刷新UI
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        print("🚨 开始借鉴closeEvent的完整线程中断机制...")
        
        # === 完全借鉴closeEvent的机制 ===
        if self.worker_thread and self.worker_thread.isRunning():
            print("✅ 发现工作线程正在运行，开始强制中断流程...")
            
            # 1. 首先设置停止标志
            if self.worker:
                print("✅ 设置停止标志...")
                if hasattr(self.worker, 'stop_requested'):
                    self.worker.stop_requested = True
                    print(f"🚨 已设置取消标志: stop_requested = {self.worker.stop_requested}")
                
                # 2. 给工作线程一些时间来响应停止请求（借鉴closeEvent）
                print("⏳ 给工作线程时间响应停止请求...")
                time.sleep(0.2)
                QApplication.processEvents()
            
            # 3. 检查线程是否仍在运行
            if self.worker_thread.isRunning():
                print("⚠️ 线程仍在运行，开始强制中断...")
                
                # 4. 请求线程退出（借鉴closeEvent）
                print("🔧 请求线程退出...")
                self.worker_thread.quit()  # 请求事件循环退出
                
                # 5. 等待线程退出，使用较短的超时（因为是用户主动取消）
                timeout_ms = 2000  # 等待2秒
                print(f"⏳ 等待线程退出（最多{timeout_ms/1000}秒）...")
                
                if not self.worker_thread.wait(timeout_ms):
                    print(f"⚠️ 线程未能在{timeout_ms/1000}秒内退出，执行强制终止...")
                    
                    # 6. 强制终止线程（借鉴closeEvent）
                    if self.worker_thread.isRunning():
                        print("🔨 执行强制终止...")
                        self.worker_thread.terminate()  # 强制终止线程
                        
                        # 再等待一小段时间确保终止完成
                        if not self.worker_thread.wait(1000): 
                            print("❌ 严重警告: 即使在强制终止后，线程仍未停止!")
                        else:
                            print("✅ 线程已成功强制终止")
                    else:
                        print("✅ 线程现在已停止运行")
                else:
                    print("✅ 线程成功正常退出")
                
                # 7. 重新创建工作线程（因为被终止的线程不能重用）
                print("🔧 重新创建工作线程...")
                self._setup_worker_thread()
                print("✅ 工作线程已重新创建")
            else:
                print("✅ 线程已停止运行")
        else:
            print("⚠️ 工作线程未运行或已停止")
        
        # 8. 重置UI状态
        print("🔧 重置UI状态...")
        self.set_busy_state(False, "index")
        
        # 9. 清除所有进度相关显示
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
        if hasattr(self, 'phase_label'):
            self.phase_label.setVisible(False)
            self.phase_label.setText("")  # 清除文本
        if hasattr(self, 'detail_label'):
            self.detail_label.setVisible(False)
            self.detail_label.setText("")  # 清除文本
            
        self.statusBar().showMessage("索引操作已被用户强制取消", 5000)
        
        # 9. 显示取消确认
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, 
            "操作已取消", 
            "索引操作已被成功取消。\n\n已处理的文件将保留在索引中。"
        )
        
        print("✅ 取消操作完成")
        
        # 强制刷新控制台输出
        sys.stdout.flush()
        sys.stderr.flush()
    # ----------------------------------------

    # --- 分页控制方法 ---
    def _update_pagination_controls(self, pagination_info=None):
        """更新分页控件显示"""
        if pagination_info:
            self.current_page = pagination_info.get('current_page', 1)
            self.total_pages = pagination_info.get('total_pages', 1)
            self.total_count = pagination_info.get('total_count', 0)
            
            self.page_info_label.setText(f"第 {self.current_page} 页，共 {self.total_pages} 页 (总计 {self.total_count} 条)")
            
            self.prev_button.setEnabled(pagination_info.get('has_prev', False))
            self.next_button.setEnabled(pagination_info.get('has_next', False))
        else:
            self.page_info_label.setText(f"第 {self.current_page} 页，共 {self.total_pages} 页")
            self.prev_button.setEnabled(self.current_page > 1)
            self.next_button.setEnabled(self.current_page < self.total_pages)
        
        self.goto_page_edit.clear()

    @Slot()
    def _go_to_prev_page(self):
        """跳转到上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self._perform_paginated_search()
    
    @Slot()
    def _go_to_next_page(self):
        """跳转到下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._perform_paginated_search()
    
    @Slot(str)
    def _on_page_size_changed(self, new_size):
        """每页显示条数改变时的处理"""
        try:
            self.page_size = int(new_size)
            self.current_page = 1
            self._perform_paginated_search()
        except ValueError:
            print(f"无效的页面大小: {new_size}")
    
    @Slot()
    def _goto_page(self):
        """跳转到指定页面"""
        try:
            page_text = self.goto_page_edit.text().strip()
            if not page_text:
                return
            
            new_page = int(page_text)
            if 1 <= new_page <= self.total_pages:
                self.current_page = new_page
                self._perform_paginated_search()
                self.goto_page_edit.clear()
            else:
                QMessageBox.warning(self, "输入错误", f"页码必须在 1 到 {self.total_pages} 之间。")
                self.goto_page_edit.clear()
        except ValueError:
            QMessageBox.warning(self, "输入错误", "页码必须是有效的整数。")
            self.goto_page_edit.clear()

    def _perform_paginated_search(self):
        """执行分页搜索"""
        if not self.current_search_params:
            return
        
        params = self.current_search_params.copy()
        params["page_size"] = self.page_size
        params["page_number"] = self.current_page
        params["return_total"] = self.current_page == 1
        
        self.startSearchSignal.emit(
            params["query_str"],
            params["search_mode"],
            params["min_size"],
            params["max_size"],
            params["start_date"],
            params["end_date"],
            params["selected_file_types"],
            params["index_dir"],
            params["case_sensitive"],
            params["search_scope"],
            params["search_dirs_param"],
            self.current_page,
            self.page_size
        )
    # --- 分页控制方法结束 ---

# --- 文件夹树视图组件 ---
class FolderTreeWidget(QWidget):
    """提供文件夹树视图，显示搜索结果的源文件夹结构"""
    
    # 定义信号，当用户点击文件夹时触发
    folderSelected = Signal(str)  # 发送所选文件夹路径
    
    def __init__(self, parent=None, title_visible=True):
        super().__init__(parent)
        self.setMinimumWidth(200)  # 设置最小宽度
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加标题标签（可选）
        if title_visible:
            title_label = QLabel("文件夹结构")
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
        
        # 创建树视图
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)  # 隐藏表头
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)  # 禁止编辑
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)  # 允许自定义右键菜单
        self.tree_view.setStyleSheet("border: 1px solid #D0D0D0;")
        
        # 创建模型
        self.tree_model = QStandardItemModel()
        self.tree_view.setModel(self.tree_model)
        
        # 添加到布局
        layout.addWidget(self.tree_view)
        
        # 设置连接
        self.tree_view.clicked.connect(self._on_tree_item_clicked)
        
        # 初始化变量
        self.folder_paths = set()  # 存储已添加的文件夹路径
        self.path_items = {}  # 存储路径到项目的映射
        
    def _on_tree_item_clicked(self, index):
        """当用户点击树中的项目时处理"""
        item = self.tree_model.itemFromIndex(index)
        if item and item.data():
            folder_path = item.data()
            print(f"选择了文件夹: {folder_path}")
            self.folderSelected.emit(folder_path)
    
    def clear(self):
        """清除树视图中的所有项目"""
        self.tree_model.clear()
        self.folder_paths = set()
        self.path_items = {}
    
    def build_folder_tree_from_results(self, results):
        """从搜索结果中构建文件夹树
        
        Args:
            results: 搜索结果列表
        """
        self.clear()
        
        # 收集所有唯一的文件夹路径
        for result in results:
            file_path = result.get('file_path', '')
            if not file_path:
                continue
                
            # 处理存档文件中的项目
            if '::' in file_path:
                # 对于存档内的文件，只显示存档文件所在的文件夹
                archive_path = file_path.split('::', 1)[0]
                folder_path = str(Path(archive_path).parent)
            else:
                folder_path = str(Path(file_path).parent)
            
            # 标准化路径
            folder_path = normalize_path_for_display(folder_path)
            self._add_folder_path(folder_path)
        
        # 展开所有顶层节点
        self.tree_view.expandToDepth(0)
        
    def _add_folder_path(self, folder_path):
        """添加文件夹路径到树中，确保创建完整的路径层次结构
        
        Args:
            folder_path: 要添加的文件夹路径
        """
        if folder_path in self.folder_paths:
            return
            
        self.folder_paths.add(folder_path)
        
        # 创建路径的各个部分
        path = Path(folder_path)
        parts = list(path.parts)
        
        # 找出根目录（盘符或最顶层目录）
        root_part = parts[0]
        
        # 从根目录开始构建路径
        current_path = root_part
        
        # 查找或创建根目录项目
        root_item = None
        for i in range(self.tree_model.rowCount()):
            item = self.tree_model.item(i)
            if item.text() == root_part:
                root_item = item
                break
                
        # 如果根目录不存在，创建它
        if root_item is None:
            root_item = QStandardItem(root_part)
            root_item.setData(root_part)
            self.tree_model.appendRow(root_item)
            self.path_items[root_part] = root_item
            
        # 构建路径的其余部分
        parent_item = root_item
        for i in range(1, len(parts)):
            current_path = os.path.join(current_path, parts[i])
            
            # 检查此部分是否已存在
            child_exists = False
            for j in range(parent_item.rowCount()):
                child = parent_item.child(j)
                if child.text() == parts[i]:
                    parent_item = child
                    child_exists = True
                    break
                    
            # 如果不存在，创建它
            if not child_exists:
                new_item = QStandardItem(parts[i])
                new_item.setData(current_path)
                parent_item.appendRow(new_item)
                parent_item = new_item
                self.path_items[current_path] = new_item
    
    def select_folder(self, folder_path):
        """选择指定的文件夹在树中
        
        Args:
            folder_path: 要选择的文件夹路径
        """
        if folder_path in self.path_items:
            item = self.path_items[folder_path]
            index = self.tree_model.indexFromItem(item)
            self.tree_view.setCurrentIndex(index)
            self.tree_view.scrollTo(index)

# --- 索引目录对话框类 --- 
class IndexDirectoriesDialog(QDialog):
    """显示索引目录列表并允许在搜索时选择特定目录"""
    
    # 当用户更改索引目录选择时发出信号
    directoriesSelectionChanged = Signal(list)  # 发送选中的目录列表
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("索引目录")
        self.setMinimumSize(500, 400)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        self.selected_directories = []
        
        # 创建UI
        self._create_ui()
        
        # 在创建UI后应用主题样式（确保应用与主窗口相同的主题样式）
        if self.parent() and hasattr(self.parent(), 'license_manager'):
            # 获取主题名称
            theme_name = self.settings.value("ui/theme", "系统默认")
            
            # 根据主题应用对应的复选框样式
            if theme_name == "现代蓝" or theme_name == "系统默认":
                checkbox_style = """
                    QCheckBox::indicator:checked {
                        image: url(checkmark_blue.png);
                    }
                """
            elif theme_name == "现代绿":
                checkbox_style = """
                    QCheckBox::indicator:checked {
                        image: url(checkmark_green.png);
                    }
                """
            elif theme_name == "现代紫":
                checkbox_style = """
                    QCheckBox::indicator:checked {
                        image: url(checkmark_purple.png);
                    }
                """
        else:
                checkbox_style = """
                    QCheckBox::indicator:checked {
                        image: url(checkmark_blue.png);
                    }
                """
                
            # 应用样式到对话框中的所有复选框
        self.setStyleSheet(checkbox_style)
            
        # 加载窗口几何信息
        geometry = self.settings.value("indexDirectoriesDialog/geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        # 加载目录
        self._load_directories()

    def _create_ui(self):
        layout = QVBoxLayout(self)
        
        # 添加说明标签
        info_label = QLabel("以下是当前已添加到索引的文件夹。请勾选您希望搜索的文件夹：")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 创建复选框选项 "全选"
        self.select_all_checkbox = QCheckBox("全选")
        self.select_all_checkbox.setChecked(True)  # 默认选中
        layout.addWidget(self.select_all_checkbox)
        
        # 创建列表控件用于显示和选择目录
        self.dir_list = QListWidget()
        self.dir_list.setAlternatingRowColors(True)
        # 确保列表允许复选框选择
        self.dir_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.dir_list)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        self.close_button = QPushButton("关闭")
        self.apply_button = QPushButton("应用选择")
        
        button_layout.addStretch(1)
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        
        # 连接信号 - 无需断开，因为这是新创建的控件
        self.close_button.clicked.connect(self.reject)
        self.apply_button.clicked.connect(self._apply_selection)
        self.select_all_checkbox.stateChanged.connect(self._toggle_all_directories)
        self.dir_list.itemChanged.connect(self._on_item_changed)
        
        # 确保应用按钮一直可用
        self.apply_button.setEnabled(True)
    
    def _load_directories(self):
        """加载索引目录并设置选择状态"""
        # 清空列表
        self.dir_list.clear()
        
        # 获取所有索引目录
        source_dirs = self.settings.value("indexing/sourceDirectories", [], type=list)
        print(f"加载文件夹，共找到 {len(source_dirs)} 个索引目录")
        
        # 获取先前选择的目录
        self.selected_directories = self.settings.value("search/selectedDirectories", [], type=list)
        
        # 如果不存在已选择的目录，则默认选择所有目录
        if not self.selected_directories:
            self.selected_directories = source_dirs.copy()
            is_all_selected = True
        else:
            is_all_selected = (len(self.selected_directories) == len(source_dirs) and 
                              all(d in self.selected_directories for d in source_dirs))
        
        # 阻止信号以防止递归触发
        self.dir_list.blockSignals(True)
        self.select_all_checkbox.blockSignals(True)
        
        # 设置全选复选框状态
        self.select_all_checkbox.setChecked(is_all_selected)
        
        # 添加所有目录到列表并设置勾选状态
        for directory in source_dirs:
            item = QListWidgetItem(directory)
            # 明确设置为可勾选
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            
            # 设置复选框状态 - 如果全选被选中，则所有项目都应该被选中
            if is_all_selected:
                check_state = Qt.Checked
            else:
                check_state = Qt.Checked if directory in self.selected_directories else Qt.Unchecked
                
            # 直接设置复选框状态
            item.setCheckState(check_state)
            self.dir_list.addItem(item)
            
            print(f"添加目录: {directory}, 选中状态: {check_state}")
            
        # 验证选中的项目数量
        selected_count = sum(1 for i in range(self.dir_list.count()) 
                           if self.dir_list.item(i).checkState() == Qt.Checked)
        print(f"目录加载完成，选中的目录数量: {selected_count}/{len(source_dirs)}")
        
        # 恢复信号
        self.dir_list.blockSignals(False)
        self.select_all_checkbox.blockSignals(False)
        
        # 更新按钮状态确保可用
        self.apply_button.setEnabled(True)
    
    def _toggle_all_directories(self, state):
        """处理全选复选框状态变更"""
        print(f"切换全选状态: {'选中' if state == Qt.Checked else '未选中'}")
        
        # 准备设置所有目录的选中状态
        count = self.dir_list.count()
        print(f"准备设置 {count} 个目录的选中状态")
        
        # 阻塞项目变更信号，防止循环触发
        self.dir_list.blockSignals(True)
        
        # 设置状态为Qt.Checked或Qt.Unchecked
        check_state = Qt.Checked if state == Qt.Checked else Qt.Unchecked
        
        # 遍历所有项目并设置其状态
        for i in range(count):
            item = self.dir_list.item(i)
            if item.checkState() != check_state:
                item.setCheckState(check_state)
                print(f"目录 {i}: {item.text()}, 状态更改为 {'选中' if check_state == Qt.Checked else '未选中'}")
            
        # 解除信号阻塞
        self.dir_list.blockSignals(False)
        
        # 保存当前选择状态
        self._save_current_selection()
        
        print(f"全选操作完成，当前选中的目录数量: {len(self.selected_directories)}/{count}")
    
    def _save_current_selection(self):
        """保存当前列表中勾选的目录"""
        self.selected_directories = []
        
        for i in range(self.dir_list.count()):
            item = self.dir_list.item(i)
            if item.checkState() == Qt.Checked:
                self.selected_directories.append(item.text())
    
    def _update_button_states(self):
        """更新应用按钮状态"""
        # 应用按钮始终可用，不再检查是否有目录被选中
        self.apply_button.setEnabled(True)
    
    def _apply_selection(self):
        """应用当前选择的目录"""
        # 保存当前勾选的目录
        self._save_current_selection()
        
        # 保存选中的目录
        self.settings.setValue("search/selectedDirectories", self.selected_directories)
        
        # 发出信号通知选择已更改
        self.directoriesSelectionChanged.emit(self.selected_directories)
        
        # 显示确认消息
        source_dirs = self.settings.value("indexing/sourceDirectories", [], type=list)
        if len(self.selected_directories) == 0 or len(self.selected_directories) == len(source_dirs):
            msg = "已应用搜索范围：将搜索所有索引目录"
        else:
            msg = f"已应用搜索范围：将只搜索所选的 {len(self.selected_directories)} 个目录"
            
        if self.parent():
            self.parent().statusBar().showMessage(msg, 3000)
        
        self.accept()
    
    def closeEvent(self, event):
        """保存窗口大小"""
        self.settings.setValue("indexDirectoriesDialog/geometry", self.saveGeometry())
        event.accept()
        super().closeEvent(event)
    
    def _on_item_changed(self, item):
        """当列表项的复选框状态更改时处理"""
        print(f"项目状态变更: {item.text()}, 状态: {item.checkState()}")
        
        # 检查是否所有项都被选中，来更新全选复选框状态
        all_checked = True
        any_checked = False
        
        for i in range(self.dir_list.count()):
            current_state = self.dir_list.item(i).checkState()
            if current_state == Qt.Checked:
                any_checked = True
            else:
                all_checked = False
                
        # 保存当前选择状态
        self._save_current_selection()
                
        # 阻塞信号以防止循环触发
        self.select_all_checkbox.blockSignals(True)
        self.select_all_checkbox.setChecked(all_checked)
        self.select_all_checkbox.blockSignals(False)
        
        # 确保应用按钮始终可用
        self.apply_button.setEnabled(True)
        
        print(f"全选复选框更新为: {'选中' if all_checked else '未选中'}, 有选择项: {'是' if any_checked else '否'}")

    @Slot()
    def show_tray_settings_dialog_slot(self):
        """显示托盘设置对话框"""
        try:
            from tray_settings import TraySettingsDialog
            dialog = TraySettingsDialog(self)
            dialog.exec()
        except ImportError:
            QMessageBox.information(self, "托盘设置", "托盘设置功能暂不可用。")
    
    @Slot()
    def show_startup_settings_dialog_slot(self):
        """显示启动设置对话框"""
        from startup_settings import StartupSettingsDialog
        dialog = StartupSettingsDialog(self)
        dialog.exec()

    @Slot()
    def show_hotkey_settings_dialog_slot(self):
        """显示热键设置对话框"""
        try:
            from hotkey_settings import HotkeySettingsDialog
            dialog = HotkeySettingsDialog(self)
            dialog.exec()
        except ImportError:
            QMessageBox.information(self, "热键设置", "热键设置功能暂不可用。")

# --- Main Execution --- 
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()

    import sys
    import os
    import datetime
    import logging # Import logging module
    
    # --- Redirect stderr AND Configure Root Logger to a log file --- 
    log_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'DocumentSearchIndexLogs') # Log directory
    os.makedirs(log_dir, exist_ok=True) # Create directory if it doesn't exist
    log_file_path = os.path.join(log_dir, f"gui_stderr_{datetime.datetime.now():%Y%m%d_%H%M%S}.log")
    error_log_file = None # Initialize
    
    try:
        # Open the log file
        error_log_file = open(log_file_path, 'a', encoding='utf-8', buffering=1)
        
        # *** Configure the root logger ***
        logging.basicConfig(level=logging.DEBUG, # Capture DEBUG level messages from libraries
                            stream=error_log_file, # Send logs to our file stream
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Redirect stderr to the same file (belt and suspenders)
        sys.stderr = error_log_file
        # Optionally redirect stdout (can be noisy)
        # sys.stdout = error_log_file 
        
        print(f"--- GUI Started: stderr and root logger redirected to {log_file_path} ---", file=sys.stderr) # Log start
        logging.info(f"--- GUI Started: stderr and root logger redirected to {log_file_path} ---") # Also log via logging
        
    except Exception as e:
        # Fallback if redirection/logging config fails
        print(f"Error configuring logging or redirecting stderr to {log_file_path}: {e}", file=sys.__stderr__) 
        # Close the file if it was opened before the exception
        if error_log_file:
            try:
                error_log_file.close()
            except Exception:
                pass # Ignore errors during cleanup
    # --- End of logging/stderr redirection --- 
    
    # Make app aware of HiDPI scaling (using non-deprecated approach)
    # Note: In Qt 6, high DPI scaling is enabled by default, so these attributes are deprecated
    # QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)  # Deprecated in Qt 6
    # QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)     # Deprecated in Qt 6

    app = QApplication(sys.argv)  # Create the application instance

    # Setup QSettings before creating MainWindow if it reads settings in __init__
    QApplication.setOrganizationName(ORGANIZATION_NAME)
    QApplication.setApplicationName(APPLICATION_NAME)

    window = MainWindow()  # Create the main window
    window.show()  # Show the window
    
    # 确保应用程序退出前正确清理工作线程
    exit_code = app.exec()
    
    # 执行额外的清理工作
    if hasattr(window, 'worker_thread') and window.worker_thread:
        print("应用程序退出，正在等待工作线程结束...")
        if window.worker_thread.isRunning():
            # 如果工作线程还在运行，请求它退出
            if hasattr(window.worker, 'stop_requested'):
                window.worker.stop_requested = True
                
            window.worker_thread.quit()
            # 给线程一些时间来退出
            if not window.worker_thread.wait(3000):  # 等待3秒
                print("工作线程未能及时退出，强制终止...")
                window.worker_thread.terminate()
                window.worker_thread.wait(1000)  # 再给1秒确保终止完成
    
    # 显式删除窗口实例以触发closeEvent
    del window
    
    # 最后退出应用程序
    sys.exit(exit_code)

