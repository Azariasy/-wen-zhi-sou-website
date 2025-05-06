import sys
import os
import re
import time
import json
import traceback  # 用于详细异常日志记录
import functools  # 用于lru_cache装饰器
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import (
    Qt, Signal, Slot, QObject, QThread, QDate, 
    QSize, QUrl, QSettings, QTimer, QRect
)
from PySide6.QtGui import (
    QIcon, QColor, QPixmap, QCursor, QAction, 
    QKeySequence, QIntValidator, QTextDocument
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, 
    QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QSplitter, QMessageBox, 
    QStatusBar, QProgressBar, QCheckBox, QTabWidget,
    QListWidget, QListWidgetItem, QTextBrowser, QButtonGroup,
    QGroupBox, QSpinBox, QRadioButton, QDateEdit, QMenu, 
    QSizePolicy, QStyle, QScrollArea, QToolBar, QToolButton
)

# --- 导入许可证管理模块 ---
from license_manager import LicenseManager, LicenseActivationDialog, LicenseStatusDialog

# --- QDarkStyle Support (Optional) --- 
try:
    import qdarkstyle
    _qdarkstyle_available = True
except ImportError:
    _qdarkstyle_available = False

# 用于导入搜索引擎后端
# import file_search_backend as search_backend
import search_backend as search_backend  # 使用重构后的模块名

# --- Global Constants ---
ORGANIZATION_NAME = "DocumentSearchTool"
APPLICATION_NAME = "FileSearchIndex"

# 下面的旧许可证常量不再需要，从license_manager模块导入
# --- License Constants ---
# LICENSE_STATUS_KEY = "license/status"  # Key for storing license status in QSettings
# LICENSE_KEY_KEY = "license/key"  # Key for storing license key in QSettings
# LICENSE_EXPIRE_KEY = "license/expire_date"  # Key for storing license expiration date in QSettings
# LICENSE_PURCHASE_KEY = "license/purchase_date"  # Key for storing license purchase date in QSettings

# --- Other Settings Keys ---
SETTING_THEME = "ui/theme"
SETTING_LAST_DIR = "search/lastDirectory"
SETTING_INDEX_DIR = "indexing/indexLocation"
SETTING_SOURCE_DIRS = "indexing/sourceDirectories"
SETTING_RESULTS_FONT_SIZE = "ui/resultsFontSize"
SETTING_DEFAULT_SORT_BY = "search/defaultSortBy"
SETTING_DEFAULT_SORT_DESCENDING = "search/defaultSortDescending"
SETTING_SEARCH_HISTORY = "search/history"

# --- 删除旧的LicenseManager类 ---
# 注意：通过在此位置删除旧类，保持文件其余部分的行号不变

# --- ADDED: Import for license hashing and validation ---
import base64
import hashlib
import time
from datetime import datetime, timedelta
# -----------------------------------------------

# --- Constants ---
ORGANIZATION_NAME = "YourOrganizationName"  # Replace with your actual org name or identifier
APPLICATION_NAME = "DocumentSearchToolPySide"
CONFIG_FILE = 'search_config.ini'  # Keep for reference, but QSettings handles location
DEFAULT_DOC_DIR = ""

# --- License Constants ---
LICENSE_STATUS_KEY = "license/status"  # Key for storing license status in QSettings
LICENSE_KEY_KEY = "license/key"  # Key for storing license key in QSettings
LICENSE_EXPIRE_KEY = "license/expire_date"  # Key for storing license expiration date in QSettings
LICENSE_PURCHASE_KEY = "license/purchase_date"  # Key for storing license purchase date in QSettings

# --- Settings Keys --- (Define keys for QSettings)
SETTINGS_LAST_SEARCH_DIR = "history/lastSearchDirectory"
SETTINGS_WINDOW_GEOMETRY = "window/geometry"
SETTINGS_INDEX_DIRECTORY = "indexing/indexDirectory" # New key for index path
SETTINGS_SOURCE_DIRECTORIES = "indexing/sourceDirectories"
SETTINGS_ENABLE_OCR = "indexing/enableOcr"
SETTINGS_EXTRACTION_TIMEOUT = "indexing/extractionTimeout"
SETTINGS_TXT_CONTENT_LIMIT = "indexing/txtContentLimitKb"
SETTINGS_CASE_SENSITIVE = "search/caseSensitive"

# --- License Manager Class --- 
# 注意：此类已移至 license_manager.py 模块
# class LicenseManager:
#     """
#     管理许可证状态和功能解锁的类
#     """
#     
#     # Pro功能列表 - 列出所有专业版功能的标识符
#     PRO_FEATURES = [
#         "pdf_support",        # PDF文件支持（包括纯文本和OCR）
#         "markdown_support",   # Markdown文件支持
#         "email_support",      # EML/MSG邮件支持
#         "archive_support",    # ZIP/RAR压缩包支持
#         "wildcard_search",    # 通配符搜索
#         "unlimited_folders",  # 无限制文件夹索引
#     ]
#     
#     # 功能描述（用于UI显示）
#     FEATURE_DESCRIPTIONS = {
#         "pdf_support": "PDF文件支持（包括纯文本和OCR）",
#         "markdown_support": "Markdown文件支持",
#         "email_support": "EML/MSG邮件支持",
#         "archive_support": "ZIP/RAR压缩包支持",
#         "wildcard_search": "通配符搜索",
#         "unlimited_folders": "无限制文件夹索引",
#     }
#     
#     # 免费版最大文件夹数
#     FREE_MAX_FOLDERS = 5
#     
#     def __init__(self):
#         """初始化许可证管理器"""
#         self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
#         self._load_license_data()
#     
#     def _load_license_data(self):
#         """从设置加载许可证数据"""
#         self.license_key = self.settings.value(LICENSE_KEY_KEY, "")
#         self.is_activated = self.settings.value(LICENSE_STATUS_KEY, False, type=bool)
#         self.expire_date = self.settings.value(LICENSE_EXPIRE_KEY, "")  # 日期格式: YYYY-MM-DD
#         self.purchase_date = self.settings.value(LICENSE_PURCHASE_KEY, "")  # 日期格式: YYYY-MM-DD
#     
#     def activate_license(self, license_key):
#         """
#         验证并激活许可证密钥
#         
#         Args:
#             license_key: 用户输入的许可证密钥
#             
#         Returns:
#             tuple: (bool, str) - (是否成功, 信息/错误消息)
#         """
#         # 初期简单验证 - 仅检查格式和固定前缀
#         # 真实实现应该连接到服务器或使用更复杂的算法
#         if not license_key or len(license_key) < 16:
#             return False, "无效的许可证密钥：密钥格式不正确"
#         
#         # 验证密钥格式 (简单版本)
#         if not re.match(r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$', license_key):
#             return False, "无效的许可证密钥：格式不正确，应为XXXX-XXXX-XXXX-XXXX格式"
#         
#         # 简单的内置验证（在实际环境中应该改为在线验证或更安全的离线验证）
#         # 这里只是演示 - 具有"DEMO"前缀的密钥被视为有效
#         if not license_key.startswith("DEMO"):
#             return False, "无效的许可证密钥：不是有效的密钥"
#         
#         # 设置激活状态
#         now = datetime.now()
#         purchase_date = now.strftime("%Y-%m-%d")
#         expire_date = (now + timedelta(days=365)).strftime("%Y-%m-%d")  # 一年后到期
#         
#         # 保存许可证信息
#         self.license_key = license_key
#         self.is_activated = True
#         self.purchase_date = purchase_date
#         self.expire_date = expire_date
#         
#         # 存储到设置
#         self.settings.setValue(LICENSE_KEY_KEY, license_key)
#         self.settings.setValue(LICENSE_STATUS_KEY, True)
#         self.settings.setValue(LICENSE_PURCHASE_KEY, purchase_date)
#         self.settings.setValue(LICENSE_EXPIRE_KEY, expire_date)
#         
#         return True, f"许可证激活成功！有效期至 {expire_date}"
#     
#     def deactivate_license(self):
#         """
#         停用当前许可证
#         
#         Returns:
#             bool: 是否成功停用
#         """
#         # 清除许可证信息
#         self.license_key = ""
#         self.is_activated = False
#         self.purchase_date = ""
#         self.expire_date = ""
#         
#         # 更新设置
#         self.settings.setValue(LICENSE_KEY_KEY, "")
#         self.settings.setValue(LICENSE_STATUS_KEY, False)
#         self.settings.setValue(LICENSE_PURCHASE_KEY, "")
#         self.settings.setValue(LICENSE_EXPIRE_KEY, "")
#         
#         return True
#     
#     def is_pro_feature(self, feature_name):
#         """
#         检查功能是否为专业版功能
#         
#         Args:
#             feature_name: 功能标识符
#             
#         Returns:
#             bool: 是否为专业版功能
#         """
#         return feature_name in self.PRO_FEATURES
#     
#     def is_feature_enabled(self, feature_name):
#         """
#         检查指定功能是否启用
#         
#         Args:
#             feature_name: 功能标识符
#             
#         Returns:
#             bool: 功能是否可用
#         """
#         # 如果不是专业版功能，则免费版也可用
#         if not self.is_pro_feature(feature_name):
#             return True
#             
#         # 如果是专业版功能，则需要检查许可证状态
#         return self.is_activated and self.is_license_valid()
#     
#     def is_license_valid(self):
#         """
#         检查许可证是否仍在有效期内
#         
#         Returns:
#             bool: 许可证是否有效
#         """
#         if not self.is_activated or not self.expire_date:
#             return False
#             
#         try:
#             # 解析过期日期
#             expire_date = datetime.strptime(self.expire_date, "%Y-%m-%d")
#             now = datetime.now()
#             
#             # 检查是否过期
#             return now <= expire_date
#         except ValueError:
#             # 日期解析错误
#             return False
#     
#     def get_license_status_text(self):
#         """
#         获取许可证状态的友好文本描述
#         
#         Returns:
#             str: 许可证状态描述
#         """
#         if not self.is_activated:
#             return "免费版 (未激活专业版)"
#             
#         if self.is_license_valid():
#             return f"专业版 (有效期至 {self.expire_date})"
#         else:
#             return f"专业版 (已过期，购买于 {self.purchase_date})"
#     
#     def get_folder_limit(self):
#         """
#         获取当前许可证状态下的文件夹数量限制
#         
#         Returns:
#             int: 允许的最大文件夹数，-1 表示无限制
#         """
#         if self.is_feature_enabled("unlimited_folders"):
#             return -1  # 无限制
#         return self.FREE_MAX_FOLDERS
#     
#     def is_in_update_period(self):
#         """
#         检查是否在更新期内（通常是购买后一年内可以免费获取更新）
#         
#         Returns:
#             bool: 是否在更新期内
#         """
#         if not self.is_activated or not self.purchase_date:
#             return False
#             
#         try:
#             # 解析购买日期
#             purchase_date = datetime.strptime(self.purchase_date, "%Y-%m-%d")
#             now = datetime.now()
#             
#             # 更新期为一年
#             update_end_date = purchase_date + timedelta(days=365)
#             
#             return now <= update_end_date
#         except ValueError:
#             # 日期解析错误
#             return False

# --- Worker Class for Background Tasks ---
class Worker(QObject):
    # Signals to communicate with the main thread
    statusChanged = Signal(str)       # For general status updates
    # --- MODIFIED: Added detail parameter to progressUpdated signal ---
    progressUpdated = Signal(int, int, str, str) # current, total, phase, detail
    # -----------------------------------------------------------------
    resultsReady = Signal(list)       # Search results list[dict]
    indexingComplete = Signal(dict)   # Summary dict from backend
    errorOccurred = Signal(str)       # Error message

    @Slot(list, str, bool, int, int) # Added int for txt_content_limit_kb
    def run_indexing(self, source_directories, index_dir_path, enable_ocr, extraction_timeout, txt_content_limit_kb):
        """Runs the indexing process in the background for multiple source directories."""
        try:
            # --- Clear search cache before indexing ---
            self.clear_search_cache()
            # -----------------------------------------

            # --- Status message for multiple directories ---
            ocr_status_text = "启用OCR" if enable_ocr else "禁用OCR"
            dir_count = len(source_directories)
            dir_text = f"{dir_count} 个源目录" if dir_count != 1 else f"源目录 '{source_directories[0]}'"
            self.statusChanged.emit(f"开始索引 ({ocr_status_text}): {dir_text} -> {index_dir_path}")
            # ------------------------------------------------------

            # --- REMOVED Simulation Block ---
            # # Temporarily simulate processing instead of calling the old backend function
            # self.statusChanged.emit(f"[模拟] 准备处理 {dir_count} 个目录...")
            # import time # Need time for sleep
            # for i, directory_path_str in enumerate(source_directories):
            #     self.statusChanged.emit(f"[模拟] 处理目录 {i+1}/{dir_count}: {directory_path_str}")
            #     time.sleep(0.5) # Simulate work
            #     self.progressUpdated.emit(i + 1, dir_count, "模拟处理目录")
            # summary = {
            #     'message': f'模拟索引完成: 处理了 {dir_count} 个目录。',
            #     'added': dir_count * 5, # Fake data
            #     'updated': dir_count * 2,
            #     'deleted': dir_count * 1,
            #     'errors': 0
            # }
            # self.indexingComplete.emit(summary)
            # --------------------------------

            # --- RESTORED Actual Backend Call and Generator Processing ---
            generator = document_search.create_or_update_index(
                source_directories,
                index_dir_path,
                enable_ocr,
                extraction_timeout=extraction_timeout, # Pass timeout here
                txt_content_limit_kb=txt_content_limit_kb # Pass txt limit here
            )

            for update in generator:
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
                    self.progressUpdated.emit(current, total, phase, detail)
                    # --------------------------------------------------
                elif msg_type == 'warning':
                    self.statusChanged.emit(f"[警告] {message}")  # Warnings can also be status messages
                elif msg_type == 'error':
                    self.errorOccurred.emit(f"索引错误: {message}")
                elif msg_type == 'complete': # Check for 'complete' type
                    summary_dict = update.get('summary', {}) # Get the summary dict
                    # --- ADDED: Include ocr_enabled status in the final message if available ---
                    # final_ocr_enabled = summary_dict.get('ocr_enabled', enable_ocr) # Get from summary or fallback
                    # ocr_status_final = "启用OCR" if final_ocr_enabled else "禁用OCR"
                    # summary_message = summary_dict.get('message', '索引处理完成。') + f" ({ocr_status_final})"
                    # summary_dict['message'] = summary_message # Update message in dict before emitting
                    # -----------------------------------------------------------------------
                    self.indexingComplete.emit(summary_dict) # Emit the summary dict
            # -------------------------------------------------------------

        except Exception as e:
            # Catch any unexpected errors during the backend call itself
            tb = traceback.format_exc()
            print(f"WORKER EXCEPTION in run_indexing: {e}\
{tb}", file=sys.stderr)
            self.errorOccurred.emit(f"启动或执行索引时发生意外错误: {e}")

    @Slot(str, str, object, object, object, object, object, str, bool, str)
    def run_search(self, query_str, search_mode, min_size, max_size, start_date, end_date, file_type_filter, index_dir_path, case_sensitive, search_scope):
        """Runs the search process in the background with optional filters, using cache."""
        try:
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
                search_scope # Pass scope here
            )
            # -------------------------------------------
            
            self.resultsReady.emit(results)

        except Exception as e:
            error_info = traceback.format_exc()
            self.errorOccurred.emit(f"搜索过程中发生意外错误: {e}\n{error_info}")

    # --- NEW: Cached Search Function ---
    @functools.lru_cache(maxsize=128) # Cache up to 128 recent search results
    def _perform_search_with_cache(self, query_str, search_mode, min_size, max_size, start_date_str, end_date_str, file_type_filter_tuple, index_dir_path, case_sensitive, search_scope):
        """Internal method that performs the actual search and caches results.
           Args must be hashable, hence file_type_filter_tuple.
        """
        print(f"--- Cache MISS: Performing backend search for: '{query_str}' (Scope: {search_scope}) ---") # Debug with scope
        # Convert tuple back to list for backend function if needed (check backend signature)
        file_type_filter_list = list(file_type_filter_tuple) if file_type_filter_tuple else None
        
        # Call the actual backend search function, passing scope
        results = document_search.search_index(
            query_str=query_str, 
            index_dir_path=index_dir_path, 
            search_mode=search_mode,
            search_scope=search_scope, # Pass scope to backend
            min_size_kb=min_size,
            max_size_kb=max_size,
            start_date=start_date_str, 
            end_date=end_date_str, 
            file_type_filter=file_type_filter_list, # Pass list or None
            case_sensitive=case_sensitive
            # sort_by is handled later in the GUI
        )
        return results

    # --- NEW: Cache Clearing Method --- (Step 5)
    def clear_search_cache(self):
        """Clears the LRU search cache."""
        cache_info = self._perform_search_with_cache.cache_info()
        print(f"--- Clearing search cache ({cache_info.hits} hits, {cache_info.misses} misses, {cache_info.currsize}/{cache_info.maxsize} size) ---")
        self._perform_search_with_cache.cache_clear()
        print("--- Search cache cleared. ---")

# --- Settings Dialog Class --- (NEW)
class SettingsDialog(QDialog):
    # MODIFIED: Accept an optional category argument and license_manager
    def __init__(self, parent=None, category_to_show='all', license_manager=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(450) # Increase width slightly
        self.category_to_show = category_to_show # Store the category
        
        # 使用提供的license_manager或创建新的
        self.license_manager = license_manager or LicenseManager()

        # --- Main Layout ---
        layout = QVBoxLayout(self)

        # --- Create Category Containers ---
        self.index_settings_widget = QWidget()
        self.search_settings_widget = QWidget()
        self.interface_settings_widget = QWidget()

        # --- Populate Index Settings Container ---
        index_layout = QVBoxLayout(self.index_settings_widget)
        index_layout.setContentsMargins(0,0,0,0) # Remove margins if needed
        # Use QGroupBox for better visual grouping
        index_groupbox = QGroupBox("索引设置")
        index_layout.addWidget(index_groupbox)
        index_group_layout = QVBoxLayout(index_groupbox) # Layout for the groupbox

        # --- Source Directories Management ---
        source_dirs_label = QLabel("要索引的文件夹:")
        self.source_dirs_list = QListWidget()
        self.source_dirs_list.setSelectionMode(QAbstractItemView.ExtendedSelection) # Allow multiple selections
        self.source_dirs_list.setToolTip("指定一个或多个需要建立索引的根文件夹。")

        source_dirs_button_layout = QHBoxLayout()
        self.add_source_dir_button = QPushButton("添加目录")
        self.remove_source_dir_button = QPushButton("移除选中")
        source_dirs_button_layout.addWidget(self.add_source_dir_button)
        source_dirs_button_layout.addWidget(self.remove_source_dir_button)
        source_dirs_button_layout.addStretch() # Push buttons to the left
        
        # --- 添加许可证状态显示 ---
        self.source_dir_limit_label = QLabel()
        self.update_source_dir_limit_display()
        source_dirs_button_layout.addWidget(self.source_dir_limit_label)

        index_group_layout.addWidget(source_dirs_label)
        index_group_layout.addWidget(self.source_dirs_list)
        index_group_layout.addLayout(source_dirs_button_layout)
        index_group_layout.addSpacing(15) # Add some space before next setting

        # --- OCR Setting ---
        self.enable_ocr_checkbox = QCheckBox("索引时启用 OCR (适用于 PDF, 可能显著增加时长)") # Clarified PDF applicability
        index_group_layout.addWidget(self.enable_ocr_checkbox)
        index_group_layout.addSpacing(15) # Add some space

        # --- ADDED: Extraction Timeout Setting ---
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("单个文件提取超时 (秒):")
        self.extraction_timeout_spinbox = QSpinBox()
        self.extraction_timeout_spinbox.setMinimum(0) # 0 means no timeout
        self.extraction_timeout_spinbox.setMaximum(600) # Max 10 minutes, adjust as needed
        self.extraction_timeout_spinbox.setValue(120) # Default 2 minutes
        self.extraction_timeout_spinbox.setToolTip("设置提取单个文件内容（尤其是 OCR）允许的最长时间。\n0 表示不设置超时限制。")
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.extraction_timeout_spinbox)
        timeout_layout.addStretch()
        index_group_layout.addLayout(timeout_layout)
        index_group_layout.addSpacing(15)
        # ----------------------------------------

        # --- ADDED: TXT Content Limit Setting ---
        txt_limit_layout = QHBoxLayout()
        txt_limit_label = QLabel(".txt 文件内容索引上限 (KB):")
        self.txt_content_limit_spinbox = QSpinBox()
        self.txt_content_limit_spinbox.setMinimum(0)       # 0 means no limit
        self.txt_content_limit_spinbox.setMaximum(102400)  # Max 100 MB, adjust as needed
        self.txt_content_limit_spinbox.setValue(0)         # Default 0 (no limit)
        self.txt_content_limit_spinbox.setToolTip("限制索引 .txt 文件内容的最大大小（单位 KB）。\\n设置为 0 表示不限制。")
        txt_limit_layout.addWidget(txt_limit_label)
        txt_limit_layout.addWidget(self.txt_content_limit_spinbox)
        txt_limit_layout.addStretch()
        index_group_layout.addLayout(txt_limit_layout)
        index_group_layout.addSpacing(15)
        # -----------------------------------------

        # --- Index Storage Location ---
        index_dir_layout = QHBoxLayout()
        index_dir_label = QLabel("索引文件存储位置:")
        self.index_dir_entry = QLineEdit()
        self.index_dir_entry.setToolTip("指定用于存储索引文件的文件夹。")
        self.browse_index_button = QPushButton("浏览...")
        index_dir_layout.addWidget(index_dir_label)
        index_dir_layout.addWidget(self.index_dir_entry, 1)
        index_dir_layout.addWidget(self.browse_index_button)
        index_group_layout.addLayout(index_dir_layout)

        # Remove the stretch added earlier as group box provides structure
        # index_layout.addStretch(1)

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
        self.theme_combo.addItems(["系统默认", "浅色", "深色"])
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo, 1)
        interface_group_layout.addLayout(theme_layout)
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
        # interface_group_layout.addStretch(1) # Remove stretch

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
        self.remove_source_dir_button.clicked.connect(self._remove_selected_source_directory)

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

    def update_source_dir_limit_display(self):
        """更新源目录数量限制的显示"""
        folder_limit = self.license_manager.get_folder_limit()
        current_count = self.source_dirs_list.count() if hasattr(self, 'source_dirs_list') else 0
        
        if folder_limit < 0:
            # 无限制
            self.source_dir_limit_label.setText("无限制目录")
            self.source_dir_limit_label.setStyleSheet("color: green;")
        else:
            # 有限制
            self.source_dir_limit_label.setText(f"{current_count}/{folder_limit} 目录")
            
            # 设置颜色
            if current_count >= folder_limit:
                self.source_dir_limit_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                self.source_dir_limit_label.setStyleSheet("color: #333;")
        
        # 如果已经到达限制，禁用添加按钮
        if hasattr(self, 'add_source_dir_button'):
            self.add_source_dir_button.setEnabled(folder_limit < 0 or current_count < folder_limit)

    # --- ADDED: Method to add source directory ---
    def _browse_add_source_directory(self):
        # 检查是否已达到文件夹数量限制
        folder_limit = self.license_manager.get_folder_limit()
        current_count = self.source_dirs_list.count()
        
        if folder_limit >= 0 and current_count >= folder_limit:
            # 显示专业版提示
            reply = QMessageBox.information(
                self, 
                "已达到免费版限制",
                f"免费版最多支持 {folder_limit} 个源目录。\n\n"
                "升级到专业版可以获得无限源目录支持。\n"
                "是否要查看专业版详情？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes and self.parent():
                # 如果用户点击了"是"，显示激活对话框
                try:
                    # 尝试调用主窗口的方法显示激活对话框
                    self.parent().show_license_activation_dialog_slot()
                    # 更新显示
                    self.update_source_dir_limit_display()
                except Exception as e:
                    print(f"Error showing license dialog: {e}")
            
            return
        
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
                 # 更新目录限制显示
                 self.update_source_dir_limit_display()
            else:
                 QMessageBox.information(self, "提示", f"文件夹 '{directory}' 已经在列表中了。")

    # --- ADDED: Method to remove selected source directories ---
    def _remove_selected_source_directory(self):
        """Slot to remove selected source directories."""
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
            for item in selected_items:
                # QListWidget.takeItem requires the row index
                row = self.source_dirs_list.row(item)
                self.source_dirs_list.takeItem(row)
            
            # 更新目录限制显示
            self.update_source_dir_limit_display()

    def _load_settings(self):
        settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)

        # --- Load Index Settings ---
        # Use specific key, provide default path if setting doesn't exist
        default_index_path = str(Path.home() / "Documents" / "DocumentSearchIndex")
        index_dir = settings.value("indexing/indexDirectory", default_index_path) # Use specific key
        self.index_dir_entry.setText(index_dir)

        enable_ocr = settings.value("indexing/enableOcr", True, type=bool)
        self.enable_ocr_checkbox.setChecked(enable_ocr)

        # --- ADDED: Load Source Directories ---
        source_dirs = settings.value("indexing/sourceDirectories", [], type=list) # Default to empty list
        self.source_dirs_list.clear()
        if source_dirs: # Only add if the list is not empty
            self.source_dirs_list.addItems(source_dirs)
        # -----------------------------------

        # --- ADDED: Load Extraction Timeout ---
        default_timeout = 120
        timeout = settings.value("indexing/extractionTimeout", default_timeout, type=int)
        self.extraction_timeout_spinbox.setValue(timeout)
        # -----------------------------------

        # --- ADDED: Load TXT Content Limit ---
        txt_limit_kb = settings.value("indexing/txtContentLimitKb", 0, type=int)
        self.txt_content_limit_spinbox.setValue(txt_limit_kb)
        # ------------------------------------

        # --- Load Search Settings ---
        case_sensitive = settings.value("search/caseSensitive", False, type=bool)
        self.case_sensitive_checkbox.setChecked(case_sensitive)

        # --- Load UI Settings ---
        theme = settings.value("ui/theme", "系统默认") # Default to 'System Default'
        self.theme_combo.setCurrentText(theme)

        # Load Result Font Size Setting
        # default_font_size = 10 # Sensible default
        default_font_size = QApplication.font().pointSize() # Use app default font size
        font_size = settings.value("ui/resultFontSize", default_font_size, type=int)
        self.result_font_size_spinbox.setValue(font_size)


    # --- MODIFIED: Renamed to _apply_settings for clarity with Apply button ---
    def _apply_settings(self):
        settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)

        # --- Save Index Settings ---
        settings.setValue("indexing/indexDirectory", self.index_dir_entry.text()) # Use specific key
        settings.setValue("indexing/enableOcr", self.enable_ocr_checkbox.isChecked())

        # --- ADDED: Save Source Directories ---
        source_dirs = [self.source_dirs_list.item(i).text() for i in range(self.source_dirs_list.count())]
        settings.setValue("indexing/sourceDirectories", source_dirs)
        # -----------------------------------

        # --- ADDED: Save Extraction Timeout ---
        settings.setValue("indexing/extractionTimeout", self.extraction_timeout_spinbox.value())
        # -----------------------------------

        # --- ADDED: Save TXT Content Limit ---
        settings.setValue("indexing/txtContentLimitKb", self.txt_content_limit_spinbox.value())
        # ------------------------------------

        # --- Save Search Settings ---
        settings.setValue("search/caseSensitive", self.case_sensitive_checkbox.isChecked())
        # --- Save UI Settings ---
        settings.setValue("ui/theme", self.theme_combo.currentText())
        # Save Result Font Size Setting
        settings.setValue("ui/resultFontSize", self.result_font_size_spinbox.value())

        print("--- Settings Applied ---") # Indicate settings were applied
        print(f"Source Directories: {source_dirs}") # Debug
        print(f"Index Directory: {self.index_dir_entry.text()}")
        print(f"Enable OCR: {self.enable_ocr_checkbox.isChecked()}")
        print(f"Extraction Timeout: {self.extraction_timeout_spinbox.value()}") # Debug print
        print(f"Case Sensitive: {self.case_sensitive_checkbox.isChecked()}")
        print(f"Theme: {self.theme_combo.currentText()}")
        print(f"Result Font Size: {self.result_font_size_spinbox.value()}")
        print("-----------------------")

        # Optionally emit a signal if main window needs immediate update (e.g., theme)
        # self.settingsApplied.emit() # Need to define this signal if used

        # Show confirmation
        # Use status bar on main window instead of message box
        # QMessageBox.information(self, "设置已应用", "设置已保存。部分设置可能需要重启应用程序才能完全生效。")
        if self.parent() and hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage("设置已应用", 3000) # Show for 3 seconds

    # Override accept() to apply settings before closing
    def accept(self):
        self._apply_settings() # Apply settings first
        super().accept() # Then close the dialog

    # Override reject() to make sure no changes are inadvertently kept (though load reloads)
    def reject(self):
        print("Settings changes rejected.")
        super().reject()

# --- Main GUI Window ---
class MainWindow(QMainWindow):  # Changed base class to QMainWindow
    # Signal to trigger indexing in the worker thread
    # --- MODIFIED: Add int parameter for txt_content_limit_kb ---
    startIndexingSignal = Signal(list, str, bool, int, int) # source_dirs, index_dir, enable_ocr, timeout, txt_limit_kb
    # ---------------------------------------------------------
    # Signal to trigger search in the worker thread (add types for size, date, file type, and case sensitivity)
    startSearchSignal = Signal(str, str, object, object, object, object, object, str, bool, str) # Added str for search_scope

    def __init__(self):
        super().__init__()
        self.setWindowTitle("文档搜索工具 (PySide6)")
        self.setMinimumSize(600, 450) # ADDED: Set a minimum window size

        # --- Initialize Config (using QSettings) --- 
        self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        self.MAX_HISTORY_ITEMS = 10 # Max number of search history items
        self.worker_thread = None # Initialize worker_thread to None
        self.worker = None
        self.search_results = [] # Store current search results (Displayed/Filtered)
        # --- ADD MISSING INITIALIZATIONS --- 
        self.original_search_results = [] # Stores results directly from backend before filtering/sorting
        self.is_busy = False # Flag to prevent concurrent operations
        self.collapse_states = {} # Stores {key: is_collapsed (bool)} for result display
        # ----------------------------------
        self.current_sort_key = 'score' # Default sort key
        self.current_sort_descending = True # Default sort order
        self.last_search_scope = 'fulltext' # ADDED: Store last search scope, default to fulltext
        
        # --- 初始化许可证管理器 ---
        self.license_manager = LicenseManager()

        # --- Central Widget and Main Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # --- Load settings required for UI creation FIRST ---
        # REMOVED: last_directory = self._load_last_directory() # Load last directory BEFORE creating the bar

        # --- Create UI Elements (Order Matters!) ---
        # --- REMOVED: Directory Selection Bar ---
        # dir_layout = self._create_directory_bar(last_directory) # Now last_directory is defined
        # main_layout.addLayout(dir_layout)
        # ----------------------------------------

        # --- Search Bar ---
        search_bar_layout = self._create_search_bar()
        main_layout.addLayout(search_bar_layout)

        # --- Filters ---
        size_filter_layout = self._create_size_filter_bar() # Assume helper exists
        main_layout.addLayout(size_filter_layout)
        date_filter_layout = self._create_date_filter_bar() # Assume helper exists
        main_layout.addLayout(date_filter_layout)
        sort_layout = self._create_sort_bar() # Assume helper exists
        main_layout.addLayout(sort_layout)
        type_filter_layout = self._create_type_filter_bar() # Assume helper exists
        main_layout.addLayout(type_filter_layout)

        # --- Action Buttons ---
        action_layout = self._create_action_buttons() # Assume helper exists
        main_layout.addLayout(action_layout)
        
        # --- Results Display ---
        self.results_text = QTextBrowser() 
        self.results_text.setOpenLinks(False)
        main_layout.addWidget(self.results_text, 1)

        # --- Status Bar ---
        self._setup_status_bar() # Call helper

        # --- Create Menubar --- 
        self._create_menubar()
        
        # --- Setup Worker Thread --- 
        self._setup_worker_thread()

        # --- Setup Connections (AFTER UI Elements Created) ---
        self._setup_connections() # Setup AFTER all UI elements are created

        # --- Restore Window Geometry --- 
        self._restore_window_geometry()
        
        # --- Apply Initial Settings (AFTER UI Elements Created) ---
        self.apply_theme()
        self._load_and_apply_default_sort()
        self._apply_result_font_size()
        self._load_search_history() # NOW safe to call

        # --- ADDED: Setup Shortcuts ---
        self._setup_shortcuts()
        # ----------------------------
        
        # --- ADDED: Set initial state for mode buttons ---
        self._update_mode_buttons_state_slot()
        # ------------------------------------------------
        
        # --- 显示许可证状态 ---
        self.update_license_status_in_ui()
        # ------------------------

    def _create_search_bar(self):
        layout = QHBoxLayout()
        # Search Label
        search_label = QLabel("搜索词:")
        layout.addWidget(search_label)
        # Search ComboBox
        self.search_combo = QComboBox()
        self.search_combo.setEditable(True)
        self.search_line_edit = self.search_combo.lineEdit()
        self.search_line_edit.setPlaceholderText("输入搜索词或选择历史记录...")
        self.search_line_edit.setMinimumWidth(150) # ADDED: Minimum width for search input
        layout.addWidget(self.search_combo, 1)

        # --- Create Option Groups (Scope and Mode) ---
        # Scope Group
        scope_label = QLabel("范围:")
        self.scope_fulltext_radio = QRadioButton("全文")
        self.scope_filename_radio = QRadioButton("文件名")
        self.scope_fulltext_radio.setChecked(True)
        scope_group_layout = QHBoxLayout()
        scope_group_layout.addWidget(scope_label)
        scope_group_layout.addWidget(self.scope_fulltext_radio)
        scope_group_layout.addWidget(self.scope_filename_radio)
        scope_group_layout.addStretch(1)
        # -- ADDED: Button group for Scope --
        self.scope_button_group = QButtonGroup(self) # Parent to self
        self.scope_button_group.addButton(self.scope_fulltext_radio)
        self.scope_button_group.addButton(self.scope_filename_radio)
        # ---------------------------------

        # Mode Group
        mode_label = QLabel("模式:")
        self.phrase_search_radio = QRadioButton("精确")
        self.fuzzy_search_radio = QRadioButton("模糊")
        self.phrase_search_radio.setChecked(True)
        mode_group_layout = QHBoxLayout()
        mode_group_layout.addWidget(mode_label)
        mode_group_layout.addWidget(self.phrase_search_radio)
        mode_group_layout.addWidget(self.fuzzy_search_radio)
        mode_group_layout.addStretch(1)
        # -- ADDED: Button group for Mode --
        self.mode_button_group = QButtonGroup(self) # Parent to self
        self.mode_button_group.addButton(self.phrase_search_radio)
        self.mode_button_group.addButton(self.fuzzy_search_radio)
        # --------------------------------

        # --- Vertically Stack Option Groups ---
        options_v_layout = QVBoxLayout()
        options_v_layout.addLayout(scope_group_layout)
        options_v_layout.addLayout(mode_group_layout)
        layout.addLayout(options_v_layout)

        # Search Button
        self.search_button = QPushButton("搜索")
        layout.addWidget(self.search_button)
        # Clear Button
        self.clear_search_button = QPushButton("清空输入")
        layout.addWidget(self.clear_search_button)
        return layout

    # (Add other _create_* helper methods if they were inline before)
    def _create_size_filter_bar(self):
        size_filter_layout = QHBoxLayout()
        size_filter_label = QLabel("文件大小 (KB):")
        min_size_label = QLabel("最小:")
        self.min_size_entry = QLineEdit()
        self.min_size_entry.setPlaceholderText("可选")
        self.min_size_entry.setMaximumWidth(80)
        self.min_size_entry.setMinimumWidth(60) # ADDED: Minimum width for size entry
        self.min_size_entry.setValidator(QIntValidator(0, 999999999))
        max_size_label = QLabel("最大:")
        self.max_size_entry = QLineEdit()
        self.max_size_entry.setPlaceholderText("可选")
        self.max_size_entry.setMaximumWidth(80)
        self.max_size_entry.setMinimumWidth(60) # ADDED: Minimum width for size entry
        self.max_size_entry.setValidator(QIntValidator(0, 999999999))
        size_filter_layout.addWidget(size_filter_label)
        size_filter_layout.addWidget(min_size_label)
        size_filter_layout.addWidget(self.min_size_entry)
        size_filter_layout.addWidget(max_size_label)
        size_filter_layout.addWidget(self.max_size_entry)
        size_filter_layout.addStretch(1)
        return size_filter_layout

    def _create_date_filter_bar(self):
        date_filter_layout = QHBoxLayout()
        date_filter_label = QLabel("修改日期:")
        start_date_label = QLabel("从:")
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.default_start_date = QDate(1900, 1, 1)
        self.start_date_edit.setDate(self.default_start_date)
        self.start_date_edit.setMaximumDate(QDate.currentDate())
        self.start_date_edit.setMinimumWidth(100)
        end_date_label = QLabel("到:")
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.default_end_date = QDate.currentDate()
        self.end_date_edit.setDate(self.default_end_date)
        self.end_date_edit.setMinimumWidth(100)
        self.clear_dates_button = QPushButton("清除日期")
        date_filter_layout.addWidget(date_filter_label)
        date_filter_layout.addWidget(start_date_label)
        date_filter_layout.addWidget(self.start_date_edit)
        date_filter_layout.addWidget(end_date_label)
        date_filter_layout.addWidget(self.end_date_edit)
        date_filter_layout.addWidget(self.clear_dates_button)
        date_filter_layout.addStretch(1)
        return date_filter_layout

    def _create_sort_bar(self):
        sort_layout = QHBoxLayout()
        sort_label = QLabel("排序方式:")
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["相关度", "文件路径", "修改日期", "文件大小"])
        self.sort_desc_radio = QRadioButton("降序")
        self.sort_asc_radio = QRadioButton("升序")
        self.sort_desc_radio.setChecked(True)
        sort_layout.addWidget(sort_label)
        sort_layout.addWidget(self.sort_combo)
        sort_layout.addWidget(self.sort_desc_radio)
        sort_layout.addWidget(self.sort_asc_radio)
        sort_layout.addStretch(1)
        return sort_layout

    def _create_type_filter_bar(self):
        self.file_type_checkboxes = {}
        type_filter_layout = QHBoxLayout()
        type_filter_label = QLabel("文件类型:")
        type_filter_layout.addWidget(type_filter_label)
        supported_types = {
            'pdf': 'PDF', 'docx': 'Word', 'txt': 'Text', 'xlsx': 'Excel', 
            'pptx': 'PPT', 'eml': 'EML', 'msg': 'MSG', 'html': 'HTML', 
            'rtf': 'RTF', 'md': 'Markdown',
        }
        for type_key, display_name in supported_types.items():
            checkbox = QCheckBox(display_name)
            type_filter_layout.addWidget(checkbox)
            self.file_type_checkboxes[checkbox] = type_key
        type_filter_layout.addStretch(1)
        return type_filter_layout

    def _create_action_buttons(self):
        action_layout = QHBoxLayout()
        self.index_button = QPushButton("建立/更新索引")
        self.clear_results_button = QPushButton("清空结果")
        self.view_skipped_files_button = QPushButton("查看跳过文件")
        action_layout.addWidget(self.index_button)
        action_layout.addWidget(self.clear_results_button)
        action_layout.addWidget(self.view_skipped_files_button)
        action_layout.addStretch(1)
        return action_layout

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
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        # Connect worker signals
        self.worker.statusChanged.connect(self.update_status_label_slot)
        self.worker.progressUpdated.connect(self.update_progress_bar_slot)
        self.worker.resultsReady.connect(self._handle_new_search_results_slot)
        self.worker.indexingComplete.connect(self.indexing_finished_slot)
        self.worker.errorOccurred.connect(self.handle_error_slot)
        # Connect trigger signals
        self.startIndexingSignal.connect(self.worker.run_indexing)
        self.startSearchSignal.connect(self.worker.run_search)
        # Connect thread finished
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        
    def _setup_connections(self):
        # --- Directory/Index buttons (REMOVED browse_button connection) ---
        # self.browse_button.clicked.connect(self.browse_directory_slot) # REMOVED
        self.index_button.clicked.connect(self.start_indexing_slot)
        # --- Search buttons/actions ---
        self.search_button.clicked.connect(self.start_search_slot)
        self.clear_search_button.clicked.connect(self.clear_search_entry_slot)
        self.search_line_edit.returnPressed.connect(self.start_search_slot)
        self.search_combo.activated.connect(self.start_search_slot)
        # Clear buttons
        self.clear_results_button.clicked.connect(self.clear_results_slot)
        self.clear_dates_button.clicked.connect(self.clear_dates_slot)
        # Result area links
        self.results_text.anchorClicked.connect(self.handle_link_clicked_slot)
        # File type checkboxes
        for checkbox in self.file_type_checkboxes.keys():
            checkbox.stateChanged.connect(self._filter_results_by_type_slot)
        # Sort controls
        self.sort_combo.currentIndexChanged.connect(self._sort_and_redisplay_results_slot)
        self.sort_desc_radio.toggled.connect(self._sort_and_redisplay_results_slot)
        # --- ADDED: Connect scope buttons to update mode button state --- 
        self.scope_fulltext_radio.toggled.connect(self._update_mode_buttons_state_slot)
        self.scope_filename_radio.toggled.connect(self._update_mode_buttons_state_slot)
        # -------------------------------------------------------------
        # --- ADDED: Connect the view skipped files button ---
        self.view_skipped_files_button.clicked.connect(self.show_skipped_files_dialog_slot)
        # --------------------------------------------------

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
        self.results_text.clear()
        self.statusBar().showMessage("就绪", 0)  # Reset status
        self.progress_bar.setVisible(False)
        # Clear stored data associated with results
        self.collapse_states = {}
        self.original_search_results = []

    def clear_dates_slot(self):
        """Slot to clear the date edits to default values."""
        # Reset dates to indicate 'no date filter'
        self.start_date_edit.setDate(self.default_start_date)
        self.end_date_edit.setDate(self.default_end_date)

    # UNIFIED Search Slot (Handles button click, enter press, combo activation)
    @Slot()
    def start_search_slot(self):
        """Unified slot to initiate search based on combo box text and radio button mode."""
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
            
        # Determine search mode from radio buttons
        mode = 'phrase' if self.phrase_search_radio.isChecked() else 'fuzzy'
        print(f"DEBUG: Search mode selected: {mode}")

        # --- ADDED: Determine search scope from radio buttons ---
        search_scope = 'filename' if self.scope_filename_radio.isChecked() else 'fulltext'
        print(f"DEBUG: Search scope selected: {search_scope}")
        # ------------------------------------------------------

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
        self.search_line_edit.setText(query)
        
        # 7. Save updated history to QSettings
        self.settings.setValue("history/searchQueries", updated_history)
        print(f"DEBUG: Updated search history: {updated_history}") # DEBUG

    # MODIFIED: Accepts mode and query as arguments
    def _start_search_common(self, mode: str, query: str, search_scope: str):
        """Common logic to start search, now takes mode, query, and scope."""
        if self.is_busy:
            QMessageBox.warning(self, "忙碌中", "请等待当前操作完成。")
            return
            
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
            
        min_size_str = self.min_size_entry.text().strip()
        max_size_str = self.max_size_entry.text().strip()
        # Get dates from QDateEdit
        start_qdate = self.start_date_edit.date()
        end_qdate = self.end_date_edit.date()

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
        
        if not query and min_size_kb is None and max_size_kb is None and start_date_obj == QDate(2000, 1, 1) and end_date_obj == QDate.currentDate():
            QMessageBox.warning(self, "输入错误", "请输入搜索词或修改文件大小/日期过滤器以进行搜索。")
            return
            
        # --- MODIFIED: Use scope in status message (optional, but good) ---
        search_type_text = "精确" if mode == 'phrase' else "模糊"
        scope_ui_map = {'fulltext': '全文', 'filename': '文件名'}
        scope_text = scope_ui_map.get(search_scope, search_scope)
        self.statusBar().showMessage(f"正在进行 {search_type_text} ({scope_text}) 搜索: '{query}'...")
        # --------------------------------------------------------------
        self.progress_bar.setVisible(False)  # Hide progress during search

        # --- Get File Type Filters --- 
        selected_file_types = []
        for checkbox, file_type in self.file_type_checkboxes.items():
            if checkbox.isChecked():
                selected_file_types.append(file_type)
        
        # --- Get Case Sensitivity Setting --- 
        settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME) # Re-get settings here
        case_sensitive = settings.value("search/caseSensitive", False, type=bool)
        
        # --- MODIFIED: Emit Signal to Worker with scope ---
        self.startSearchSignal.emit(query,
                                    mode,
                                    min_size_kb,
                                    max_size_kb,
                                    start_date_obj,
                                    end_date_obj,
                                    selected_file_types,
                                    index_dir, # Pass the index_dir_path
                                    case_sensitive,
                                    search_scope) # Pass search scope
        # -------------------------------------------------

        # --- ADDED: Store the current search scope --- 
        self.last_search_scope = search_scope 
        # ---------------------------------------------

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
    def update_progress_bar_slot(self, current, total, phase, detail):
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

    @Slot(list)
    def display_search_results_slot(self, results):
        """Displays search results, adapting format based on search scope."""
        scrollbar = self.results_text.verticalScrollBar()
        scroll_position = scrollbar.value()
        try:
            self.results_text.clear()
            if not results:
                self.results_text.setText("未找到匹配结果。")
                self.statusBar().showMessage("未找到结果", 5000)
                return

            # --- Determine highlight and link colors based on theme --- MODIFIED
            current_theme = self.settings.value("ui/theme", "系统默认")
            if current_theme == "深色":
                # Dark theme colors
                phrase_bg_color = "#F5F5DC" # Beige
                fuzzy_bg_color = "#AFEEEE"  # PaleTurquoise
                highlight_text_color = "black" # Force black text on light highlight
                link_color = "#CCCCCC" # Light gray for links
            else:
                # Light/Default theme colors
                phrase_bg_color = "yellow"
                fuzzy_bg_color = "lightgreen"
                highlight_text_color = "inherit" # Use default text color
                link_color = "blue" # Standard link color
            
            # Define span tags with both background and text color
            phrase_highlight_start = f'<span style="background-color: {phrase_bg_color}; color: {highlight_text_color};">'
            fuzzy_highlight_start = f'<span style="background-color: {fuzzy_bg_color}; color: {highlight_text_color};">'
            highlight_end = '</span>'
            # Define link style
            link_style = f'style="color: {link_color}; text-decoration:none;"' # Combine color and decoration
            toggle_link_style = f'style="color: {link_color}; text-decoration:none;"' # Use same style for toggle
            # -----------------------------------------------------------

            if hasattr(self, 'last_search_scope') and self.last_search_scope == 'filename':
                # --- Render Simplified List --- 
                html_output = []
                html_output.append("<h4>文件名搜索结果:</h4>")
                html_output.append("<ul>")
                processed_paths = set()
                for i, result in enumerate(results):
                    # ... (extract file_path, determine folder_path_str) ...
                    file_path = result.get('file_path', '(未知文件)')
                    if file_path in processed_paths:
                        continue
                    processed_paths.add(file_path)
                    escaped_display_path = html.escape(file_path)
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

                    # --- MODIFIED: Use link_style for actions ---
                    links = [f'<a href="openfile:{html.escape(file_path, quote=True)}" {link_style}>[打开文件]</a>']
                    if folder_path_str:
                        links.append(f'<a href="openfolder:{html.escape(folder_path_str, quote=True)}" {link_style}>[打开目录]</a>')
                    # -------------------------------------------
                    html_output.append(f'<li>{escaped_display_path} &nbsp;&nbsp; { " &nbsp; ".join(links) }</li>')
                html_output.append("</ul>")
                
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
                            html_output.append(f'<h3><a href="{toggle_href}" {toggle_link_style}>{toggle_char}</a> {file_group_counter}. {escaped_display_path}</h3>')
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
                            links = [f'<a href="openfile:{html.escape(file_path, quote=True)}" {link_style}>[打开文件]</a>']
                            if folder_path_str:
                                links.append(f'<a href="openfolder:{html.escape(folder_path_str, quote=True)}" {link_style}>[打开目录]</a>')
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
                                chapter_key = f"c::{file_path}::{i}::{original_heading}"
                                is_chapter_collapsed = self.collapse_states.get(chapter_key, False)
                                toggle_char = "[+]" if is_chapter_collapsed else "[-]"
                                toggle_href = f'toggle::{html.escape(chapter_key, quote=True)}'
                                html_output.append(f'<p style="margin-left: 10px;"><a href="{toggle_href}" {toggle_link_style}>{toggle_char}</a> <b>章节:</b> {escaped_heading_display}</p>')
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
                            html_output.append(f'<p style="margin-left: 20px;"><b>表:</b> {html.escape(excel_sheet)} - <b>行:</b> {excel_row_idx}</p>')
                            html_output.append('<table border="1" style="margin-left: 30px; border-collapse: collapse; font-size: 9pt;">')
                            html_output.append("<tr>")
                            for header in excel_headers:
                                html_output.append(f"<th>{html.escape(header)}</th>")
                            html_output.append("</tr>")
                            html_output.append("<tr>")
                            for value in excel_values:
                                escaped_value = html.escape(str(value))
                                highlighted_value = escaped_value.replace(escaped_start_marker, fuzzy_highlight_start).replace(escaped_end_marker, highlight_end)
                                html_output.append(f"<td>{highlighted_value}</td>")
                            html_output.append("</tr>")
                            html_output.append("</table><br>")
                        elif current_file_div_open and current_chapter_div_open and highlighted_paragraph_display is not None:
                            paragraph_style = ' style="margin-left: 30px;"' 
                            html_output.append(f'<p{paragraph_style}><b>段落:</b> {highlighted_paragraph_display}</p>')

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
                        self.statusBar().showMessage(f"找到 {result_count} 条结果", 0)
                        
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
            self.set_busy_state(False)

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
        print("Calling set_busy_state(False)...") # DEBUG
        self.set_busy_state(False)
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
        # Reset busy state
        self.set_busy_state(False)

    # --- NEW Slot to handle results directly from worker ---
    @Slot(list)
    def _handle_new_search_results_slot(self, backend_results):
        """Receives results from the backend worker, stores them, and triggers filtering/display."""
        print("Received new results from backend.")  # DEBUG
        self.original_search_results = backend_results
        self.collapse_states = {}  # Reset collapse states on new search
        # Now apply the current checkbox filters to these new results
        self._filter_results_by_type_slot()
        # Note: set_busy_state(False) is called within display_search_results_slot's finally block

    # --- NEW Slot for Sorting (Called by sort controls) ---
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
            # For score, already handled negation in key function, so always sort ascending based on key
            if sort_field == "相关度":
                 self.original_search_results.sort(key=get_sort_key, reverse=not reverse_sort) # Negate reverse for score
            else:
                 self.original_search_results.sort(key=get_sort_key, reverse=reverse_sort)
        except Exception as sort_err:
            print(f"Error during sorting: {sort_err}")
            QMessageBox.warning(self, "排序错误", f"对结果进行排序时出错: {sort_err}")
            return # Stop if sorting fails

        # --- Trigger Redisplay (which applies file type filter) --- 
        self._filter_results_by_type_slot() 

    # --- Slot for Live File Type Filtering (Modified) --- 
    @Slot()
    def _filter_results_by_type_slot(self):
        """Filters the original search results based on checked file types and updates display."""
        # print("_filter_results_by_type_slot triggered")  # DEBUG
        # REMOVED BUSY CHECK - Checkboxes are disabled by set_busy_state anyway
        # if self.is_busy:
        #     # print("  Busy, skipping filter")  # DEBUG
        #     return # Don\'t filter if an operation is in progress
        
        # REMOVED check for empty last_search_results, now rely on original_search_results
        # if not self.last_search_results:

        checked_types = [ftype for cb, ftype in self.file_type_checkboxes.items() if cb.isChecked()]
        # print(f"  Checked types: {checked_types}")  # DEBUG
        
        if not checked_types:
            # If no types are checked, show all original results
            # print("  No types checked, displaying all original results")  # DEBUG
            self.display_search_results_slot(self.original_search_results)
        else:
            # Filter the ORIGINAL stored results based on checked types
            # print("  Filtering original results...")  # DEBUG
            filtered_results = [item for item in self.original_search_results 
                                if item.get('file_type') in checked_types]
            # print(f"  Filtered count: {len(filtered_results)}")  # DEBUG
            self.display_search_results_slot(filtered_results)

    # --- Link Handling Slot ---
    @Slot(QUrl)
    def handle_link_clicked_slot(self, url):
        """Handles clicks on file, folder, and toggle links in the results text area."""
        scheme = url.scheme()
        raw_url_str = url.toString()
        print(f"--- Link Clicked: Scheme='{scheme}', Raw URL='{raw_url_str}' --- ")  # DEBUG
        
        if scheme == "openfile":
            path_str = url.toLocalFile() if url.isLocalFile() else url.path()
            if sys.platform == 'win32' and path_str.startswith('/') and not path_str.startswith('//'): path_str = path_str[1:]
            target_path = path_str
            if "::" in path_str:
                archive_file_path = path_str.split("::", 1)[0]
                target_path = archive_file_path
            self._open_path_with_desktop_services(target_path, is_file=True)
        elif scheme == "openfolder":
            path_str = url.toLocalFile() if url.isLocalFile() else url.path()
            if sys.platform == 'win32' and path_str.startswith('/') and not path_str.startswith('//'): path_str = path_str[1:]
            self._open_path_with_desktop_services(path_str, is_file=False)
        elif scheme == "toggle":
            try:
                # Extract the full key after "toggle::"
                encoded_key_part = raw_url_str.split("::", 1)[1]
                # Decode the key (handles potential special chars in path/heading)
                toggle_key = QUrl.fromPercentEncoding(encoded_key_part.encode('utf-8'))
                print(f"  Toggle request for key: '{toggle_key}'")  # DEBUG
                
                # Toggle the state for this specific key
                current_state = self.collapse_states.get(toggle_key, False)  # Default to expanded
                print(f"  Current collapse state for key '{toggle_key}': {current_state}")
                new_state = not current_state
                self.collapse_states[toggle_key] = new_state
                print(f"  New collapse state for key '{toggle_key}': {self.collapse_states[toggle_key]}")
                
                # Re-render the results view - Uses the ORIGINAL results filtered by the checkboxes
                print("  Triggering re-render via _filter_results_by_type_slot...")  # DEBUG
                self._filter_results_by_type_slot()  # Re-apply filters based on original data
            except IndexError:
                print("Error: Could not extract key from toggle link:", raw_url_str)
            except Exception as e:
                print(f"Error processing toggle link {raw_url_str}: {e}")

    # --- Utility Methods ---
    def set_busy_state(self, busy):
        """Enable/disable controls based on busy state."""
        print(f"--- set_busy_state called with busy={busy} ---") # DEBUG
        self.is_busy = busy
        # Disable buttons while busy
        # self.browse_button.setEnabled(not busy) # REMOVED this line
        self.index_button.setEnabled(not busy)
        self.search_button.setEnabled(not busy) # Need to disable search button too
        # --- MODIFIED: Let _update_mode_buttons_state_slot handle mode buttons ---
        # self.phrase_search_radio.setEnabled(not busy)
        # self.fuzzy_search_radio.setEnabled(not busy)
        # --------------------------------------------------------------------
        self.clear_search_button.setEnabled(not busy)
        self.clear_results_button.setEnabled(not busy)
        self.clear_dates_button.setEnabled(not busy)  # Also disable date clear button

        # Disable entries? Optional but recommended
        # self.dir_entry.setEnabled(not busy) # REMOVED
        self.search_line_edit.setEnabled(not busy)
        self.search_combo.setEnabled(not busy) # Also disable the combo box itself
        self.min_size_entry.setEnabled(not busy)
        self.max_size_entry.setEnabled(not busy)
        self.start_date_edit.setEnabled(not busy)
        self.end_date_edit.setEnabled(not busy)

        # Disable file type checkboxes
        for checkbox in self.file_type_checkboxes.keys():
            checkbox.setEnabled(not busy)

        # Disable sort controls
        self.sort_combo.setEnabled(not busy)
        self.sort_desc_radio.setEnabled(not busy)
        self.sort_asc_radio.setEnabled(not busy)
        
        # --- ADDED: Disable Scope Radio buttons too --- 
        self.scope_fulltext_radio.setEnabled(not busy)
        self.scope_filename_radio.setEnabled(not busy)
        # --------------------------------------------

        if not busy:
             self.progress_bar.setVisible(False)  # Hide progress bar when not busy
             self.phase_label.setVisible(False) # Hide phase label when not busy
             self.detail_label.setVisible(False) # <<< ADDED: Hide detail label when not busy
             # Optionally reset progress bar value
             # self.progress_bar.setValue(0)
             # Optionally clear labels
             # self.phase_label.clear()
             # self.detail_label.clear()
        else:
             # Make sure they are visible when busy state starts
             self.phase_label.setVisible(True)
             self.detail_label.setVisible(True) # <<< ADDED: Show detail label when busy
             self.progress_bar.setVisible(True)

        # Update mode buttons state based on current scope (even when busy, relies on scope buttons only)
        self._update_mode_buttons_state_slot() # Call this AFTER potentially disabling scope buttons

        print(f"Progress bar visible: {self.progress_bar.isVisible()}, Phase label visible: {self.phase_label.isVisible()}, Detail label visible: {self.detail_label.isVisible()}") # Updated DEBUG
        print(f"--- set_busy_state finished for busy={busy} ---") # DEBUG

    def _open_path_with_desktop_services(self, path_str: str, is_file: bool):
        """Uses QDesktopServices to open a file or folder path."""
        path_obj = Path(path_str)
        log_prefix = "文件" if is_file else "文件夹"
        
        print(f"Attempting to open {log_prefix}: {path_obj}")
        
        exists = path_obj.is_file() if is_file else path_obj.is_dir()
        
        if not exists:
            # Show error message box later using QMessageBox
            #print(f"错误: {log_prefix}不存在: {path_obj}", file=sys.stderr)
            # Use self.handle_error_slot or a dedicated message box
            QMessageBox.warning(self, "打开错误", f"{log_prefix}不存在:\n{path_obj}")
            self.statusBar().showMessage(f"错误: {log_prefix}不存在", 3000)  # Show error temporarily
            return

        # Construct a QUrl suitable for local files/directories
        qurl = QUrl.fromLocalFile(str(path_obj.resolve()))
        
        if not QDesktopServices.openUrl(qurl):
            # Show error message box later
            #print(f"错误: 无法使用系统默认方式打开 {log_prefix}: {path_obj}", file=sys.stderr)
            QMessageBox.critical(self, "打开错误", f"无法打开 {log_prefix}:\n{path_obj}")
            self.statusBar().showMessage(f"错误: 无法打开 {log_prefix}", 3000)  # Show error temporarily

    # --- Config Handling Methods (Using QSettings) ---
    def _restore_window_geometry(self):
        """Restores window geometry from QSettings."""
        geometry_bytes = self.settings.value("windowGeometry")
        if geometry_bytes:
            print("恢复窗口几何状态...")
            try:
                 self.restoreGeometry(geometry_bytes)
            except Exception as e:
                 print(f"警告: 无法恢复窗口几何状态: {e}")
                 self.resize(800, 600)  # Fallback size
        else:
            # print("未找到窗口几何状态，使用默认大小。")
            self.resize(800, 600)  # Apply default size only if no geometry saved

    def _save_window_geometry(self):
        """Saves window geometry to QSettings."""
        # print("保存窗口几何状态...")
        self.settings.setValue("windowGeometry", self.saveGeometry())

    def _load_last_directory(self) -> str:
        """Loads the last used directory from QSettings."""
        return self.settings.value("lastDirectory", "")  # Default to empty string

    def _save_last_directory(self, directory: str):
        """Saves the last used directory to QSettings."""
        self.settings.setValue("lastDirectory", directory)

    def _create_menubar(self):
        """Creates the main menubar."""
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("文件(&F)")
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close) # Connect to window's close method
        exit_action.setShortcut(QKeySequence("Ctrl+Q")) # Standard shortcut for quit
        file_menu.addAction(exit_action)

        # --- Settings Menu (NEW Top Level) ---
        settings_menu = menu_bar.addMenu("设置(&S)")
        
        index_settings_action = QAction("索引设置(&I)...", self)
        index_settings_action.triggered.connect(self.show_index_settings_dialog_slot)
        settings_menu.addAction(index_settings_action)
        
        search_settings_action = QAction("搜索设置(&E)...", self) # E for sEarch
        search_settings_action.triggered.connect(self.show_search_settings_dialog_slot)
        settings_menu.addAction(search_settings_action)
        
        interface_settings_action = QAction("界面设置(&U)...", self) # U for User interface
        interface_settings_action.triggered.connect(self.show_interface_settings_dialog_slot)
        settings_menu.addAction(interface_settings_action)

        # --- 添加许可证菜单 ---
        license_menu = menu_bar.addMenu("许可证(&L)")
        
        activate_license_action = QAction("激活许可证(&A)...", self)
        activate_license_action.triggered.connect(self.show_license_activation_dialog_slot)
        license_menu.addAction(activate_license_action)
        
        license_status_action = QAction("查看许可证状态(&S)", self)
        license_status_action.triggered.connect(self.show_license_status_slot)
        license_menu.addAction(license_status_action)
        # ----------------------

        # --- Help Menu ---
        help_menu = menu_bar.addMenu("帮助(&H)")  # Add & for shortcut Alt+H
        
        about_action = QAction("关于(&A)...", self)  # Add & for shortcut Alt+A
        about_action.triggered.connect(self.show_about_dialog_slot)
        help_menu.addAction(about_action)
        
        # Add more menus or actions here if needed
    
    # 添加在状态栏显示许可证状态的方法
    def update_license_status_in_ui(self):
        """更新UI中的许可证状态显示"""
        license_status_text = self.license_manager.get_license_status_text()
        
        # 在状态栏显示许可证状态（临时显示）
        self.statusBar().showMessage(f"许可证状态: {license_status_text}", 5000)
        
        # TODO: 如果需要，可以在程序界面其他地方添加永久性的许可证状态显示
    
    # 添加许可证激活对话框显示方法
    @Slot()
    def show_license_activation_dialog_slot(self):
        """显示许可证激活对话框"""
        # 使用从license_manager模块导入的LicenseActivationDialog类
        dialog = LicenseActivationDialog(self, self.license_manager)
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            # 对话框成功完成（激活或停用），可能需要更新UI
            self.update_license_status_in_ui()
            
            # 重新验证所有文件类型复选框
            self._update_file_type_checkboxes_from_license()
    
    @Slot()
    def show_license_status_slot(self):
        """显示当前许可证状态信息"""
        # 使用从license_manager模块导入的LicenseStatusDialog类
        dialog = LicenseStatusDialog(self, self.license_manager)
        dialog.exec()

    # 更新文件类型复选框状态的方法
    def _update_file_type_checkboxes_from_license(self):
        """根据许可证状态更新文件类型复选框的启用状态"""
        # 如果尚未初始化复选框，返回
        if not hasattr(self, 'file_type_checkboxes'):
            return
            
        # 禁用对应于专业版功能的文件类型复选框
        pro_file_extensions = {
            "pdf": "pdf_support",
            "md": "markdown_support",
            "eml": "email_support",
            "msg": "email_support",
            # zip和rar的处理可能是在后端的提取过程中，这里只涉及UI
        }
        
        for checkbox, ext in self.file_type_checkboxes.items():
            if ext in pro_file_extensions:
                feature = pro_file_extensions[ext]
                is_enabled = self.license_manager.is_feature_enabled(feature)
                checkbox.setEnabled(is_enabled)
                
                # 如果禁用此复选框并且它被勾选了，取消勾选
                if not is_enabled and checkbox.isChecked():
                    checkbox.setChecked(False)
                    
                # 设置工具提示解释
                if not is_enabled:
                    checkbox.setToolTip(f"此文件类型需要专业版授权")
                else:
                    checkbox.setToolTip("")

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
        dialog = SettingsDialog(self, license_manager=self.license_manager) # 传递license_manager
        # No need to check dialog.exec() result here, 
        # saving happens within dialog's accept() method.
        if dialog.exec(): # Use if dialog.exec(): to check if OK was pressed
             # REMOVED applying settings here, as they are handled by specific slots now
             # self.apply_theme() 
             # self._apply_result_font_size()
             pass # No immediate action needed for the old combined dialog

    @Slot()
    def show_index_settings_dialog_slot(self):
        """Shows the Settings dialog filtered for Index settings."""
        dialog = SettingsDialog(self, category_to_show='index', license_manager=self.license_manager) # 传递license_manager
        dialog.exec() # Settings are saved within dialog's accept()

    @Slot()
    def show_search_settings_dialog_slot(self):
        """Shows the Settings dialog filtered for Search settings."""
        dialog = SettingsDialog(self, category_to_show='search', license_manager=self.license_manager) # 传递license_manager
        dialog.exec() # Settings are saved within dialog's accept()
        # No immediate UI update needed in MainWindow for case sensitivity yet

    @Slot()
    def show_interface_settings_dialog_slot(self):
        """Shows the Settings dialog filtered for Interface settings and applies changes."""
        dialog = SettingsDialog(self, category_to_show='interface', license_manager=self.license_manager) # 传递license_manager
        if dialog.exec(): # Check if OK was pressed
            print("Interface settings accepted. Applying theme and font size...")
            self.apply_theme() # Re-apply theme if it changed
            self._apply_result_font_size() # Re-apply font size if it changed

    @Slot()
    def show_about_dialog_slot(self):
        """Shows the About dialog."""
        about_text = """
        <b>文档搜索工具</b><br><br>
        版本: 1.2 (PySide6 - 重写)<br>
        一个用于本地文档全文搜索的工具。<br><br>
        使用 Whoosh 索引, 支持多种文件类型。
        """
        QMessageBox.about(self, "关于", about_text)

    # --- Theme Handling ---
    def apply_theme(self):
        theme_name = self.settings.value("ui/theme", "系统默认")
        print(f"Applying theme: {theme_name}") # Debug
        app = QApplication.instance() # Get the application instance
        
        # Reset to default platform style first
        app.setStyleSheet("") 
        
        if theme_name == "浅色":
            # Example light theme (customize as needed)
            # You might want to use qdarkstyle or create a more detailed QSS file
            app.setStyleSheet("""QWidget { background-color: #f0f0f0; color: #000; } ... """) # Keep existing light theme QSS
        elif theme_name == "深色":
            # --- MODIFIED: Use QDarkStyle if available, otherwise fallback ---
            if _qdarkstyle_available:
                try:
                    # Ensure compatibility with PySide6
                    stylesheet = qdarkstyle.load_stylesheet(qt_api='pyside6') 
                    app.setStyleSheet(stylesheet)
                    print("Applied QDarkStyle theme.")
                except Exception as e:
                    print(f"Error applying QDarkStyle: {e}. Falling back to basic dark theme.")
                    # Fallback to basic dark theme if qdarkstyle fails
                    app.setStyleSheet("""QWidget { background-color: #2e2e2e; color: #e0e0e0; } ... """) # Keep existing basic dark QSS
            else:
                print("QDarkStyle not found, using basic dark theme.")
                # Fallback to basic dark theme
                app.setStyleSheet("""QWidget { background-color: #2e2e2e; color: #e0e0e0; } ... """) # Keep existing basic dark QSS
            # -------------------------------------------------------------------
        # else: theme_name == "系统默认" - already handled by resetting the stylesheet

    # --- Load and Apply Default Sort Settings --- 
    def _load_and_apply_default_sort(self):
        """Loads default sort settings and applies them to the UI controls."""
        default_sort_by = self.settings.value("search/defaultSortBy", "相关度") # Default: Relevance
        default_sort_desc = self.settings.value("search/defaultSortDescending", True, type=bool) # Default: Descending
        
        print(f"DEBUG: Loading default sort settings - Read By: '{default_sort_by}', Read Descending: {default_sort_desc}") # DETAILED DEBUG

        # Apply to ComboBox
        index = self.sort_combo.findText(default_sort_by)
        if index != -1:
            self.sort_combo.setCurrentIndex(index)
        else:
            print(f"Warning: Default sort field '{default_sort_by}' not found in ComboBox. Using default.")
            self.sort_combo.setCurrentIndex(0) # Fallback to first item (Relevance)
            
        # Apply to RadioButtons
        if default_sort_desc:
            self.sort_desc_radio.setChecked(True)
        else:
            self.sort_asc_radio.setChecked(True)
            
    def _save_default_sort(self):
        """Saves the current sort settings as the new default."""
        current_sort_by = self.sort_combo.currentText()
        current_sort_desc = self.sort_desc_radio.isChecked()
        
        print(f"DEBUG: Saving default sort settings - Current By: '{current_sort_by}', Current Descending: {current_sort_desc}") # DETAILED DEBUG
        self.settings.setValue("search/defaultSortBy", current_sort_by)
        self.settings.setValue("search/defaultSortDescending", current_sort_desc)
        # self.settings.sync() # Explicit sync usually not needed, but can try if issues persist

    def _apply_result_font_size(self):
        """Applies the font size setting to the results display area."""
        default_font_size = 10
        font_size = self.settings.value("ui/resultFontSize", default_font_size, type=int)
        print(f"DEBUG: Applying result font size: {font_size}pt") # DEBUG
        current_font = self.results_text.font() # Get current font
        current_font.setPointSize(font_size)     # Set the desired point size
        self.results_text.setFont(current_font)  # Apply the modified font

    # --- Cleanup --- 
    def closeEvent(self, event):
        """Handle window close event to clean up the worker thread and save settings."""
        print("DEBUG: closeEvent started...") # DEBUG
        print("接收到关闭事件，开始清理和保存...")
        
        # --- Save Settings --- 
        self._save_window_geometry() 
        # REMOVED: self._save_last_directory(self.dir_entry.text()) # Save current directory
        self._save_default_sort() # Save current sort settings as default
        # ---------------------

        # --- Stop Worker Thread --- 
        if self.thread and self.thread.isRunning():
            # print("  尝试退出线程...")
            self.thread.quit()  # Ask the event loop to exit
            if not self.thread.wait(5000):  # Wait up to 5 seconds
                print("  警告: 线程未能在5秒内退出，将强制终止。")
                self.thread.terminate()  # Force terminate if quit fails
                self.thread.wait()  # Wait for termination
            # else:
                 # print("  线程成功退出。")
        # else:
             # print("  线程未运行或已清理。")

        # print("清理完成，接受关闭事件。")
        print("DEBUG: closeEvent finishing...") # DEBUG
        event.accept()  # Accept the close event

    @Slot()
    def start_indexing_slot(self):
        """Slot to initiate the indexing process."""
        if self.is_busy:
            QMessageBox.warning(self, "忙碌中", "请等待当前操作完成。")
            return

        # --- MODIFIED: Read source directories from settings ---
        # directory = self.dir_entry.text() # REMOVED
        source_dirs = self.settings.value("indexing/sourceDirectories", [], type=list)
        if not source_dirs:
             QMessageBox.warning(self, "未配置源目录", "请先前往 '文件 -> 设置 -> 索引设置' 添加需要索引的文件夹。")
             return
        # -----------------------------------------------------

        # --- Get Index Directory from Settings ---
        # settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME) # Already have self.settings
        default_index_path = str(Path.home() / "Documents" / "DocumentSearchIndex")
        index_dir = self.settings.value("indexing/indexDirectory", default_index_path) # Use specific key
        if not index_dir:
            # This check might be redundant if settings dialog enforces it, but good safety check
            QMessageBox.critical(self, "错误", "未配置索引存储位置！请在设置中指定。")
            return
        # ------------------------------------------

        # --- ADDED: Get OCR Setting --- 
        enable_ocr = self.settings.value("indexing/enableOcr", True, type=bool)
        print(f"Starting indexing for {len(source_dirs)} source(s) -> '{index_dir}'. Enable OCR: {enable_ocr}")
        # ------------------------------

        # --- ADDED: Get Extraction Timeout Setting ---
        extraction_timeout = self.settings.value("indexing/extractionTimeout", 120, type=int)
        # ---------------------------------------------

        # --- ADDED: Get TXT Content Limit Setting --- 
        txt_content_limit_kb = self.settings.value("indexing/txtContentLimitKb", 0, type=int) # Default 0
        # -------------------------------------------

        # Updated print to include the new limit
        print(f"Starting indexing for {len(source_dirs)} source(s) -> '{index_dir}'. OCR: {enable_ocr}, Timeout: {extraction_timeout}s, TXT Limit: {txt_content_limit_kb}KB")

        self.set_busy_state(True)
        self.results_text.clear()  # Clear previous results/logs
        self.statusBar().showMessage(f"开始准备索引 {len(source_dirs)} 个源目录...", 3000)

        # --- MODIFIED: Emit signal with txt_content_limit_kb --- 
        self.startIndexingSignal.emit(source_dirs, index_dir, enable_ocr, extraction_timeout, txt_content_limit_kb)
        # -------------------------------------------------------

    # --- ADDED: Slot to enable/disable mode buttons based on scope ---
    @Slot()
    def _update_mode_buttons_state_slot(self):
        """Enables or disables the phrase/fuzzy radio buttons based on the selected scope."""
        # --- DEBUG --- 
        print("DEBUG: _update_mode_buttons_state_slot called.")
        # --- END DEBUG ---
        
        # Check which scope radio button is currently checked
        # We only need to check one, as toggled signal fires for both states
        filename_scope_selected = self.scope_filename_radio.isChecked()
        
        # --- DEBUG --- 
        enable_state = not filename_scope_selected
        print(f"DEBUG: scope_filename_radio checked: {filename_scope_selected}")
        print(f"DEBUG: Setting mode buttons enabled state to: {enable_state}")
        # --- END DEBUG ---
        
        # Enable mode buttons only if filename scope is NOT selected (i.e., fulltext is selected)
        # self.phrase_search_radio.setEnabled(not filename_scope_selected)
        # self.fuzzy_search_radio.setEnabled(not filename_scope_selected)
        self.phrase_search_radio.setEnabled(enable_state)
        self.fuzzy_search_radio.setEnabled(enable_state)
        
        # Optional: Visually indicate disabled state more clearly if needed (e.g., change text color)
        # style = "color: gray;" if filename_scope_selected else ""
        # self.phrase_search_radio.setStyleSheet(style)
        # self.fuzzy_search_radio.setStyleSheet(style)
    # ----------------------------------------------------------------

    @Slot()
    def show_skipped_files_dialog_slot(self):
        """显示跳过索引文件的对话框"""
        dialog = SkippedFilesDialog(self)
        dialog.exec()

# --- Skipped Files Dialog Class --- (NEW)
class SkippedFilesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("跳过索引的文件列表")
        self.setMinimumSize(800, 500)
        # --- ADDED: Enable Maximize Button ---
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        # -------------------------------------
        
        # 数据相关属性
        self.skipped_files = []  # 存储所有跳过文件的记录
        self.filtered_files = []  # 存储过滤后的文件记录
        self.current_page = 0
        self.page_size = 50  # 每页显示的记录数
        self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        
        # 创建UI
        self._create_ui()
        
        # 记住窗口大小
        geometry = self.settings.value("skippedFilesDialog/geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
    def _create_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建过滤控件
        filter_layout = QHBoxLayout()
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItem("所有类型", "all")
        self.filter_type_combo.addItem("PDF超时", "pdf_timeout")
        self.filter_type_combo.addItem("内容超限", "content_limit")
        self.filter_type_combo.addItem("加密ZIP", "password_zip")
        self.filter_type_combo.addItem("加密RAR", "password_rar")
        self.filter_type_combo.addItem("损坏的ZIP", "corrupted_zip")
        self.filter_type_combo.addItem("损坏的RAR", "corrupted_rar")
        
        filter_label = QLabel("按类型过滤:")
        self.refresh_button = QPushButton("刷新")
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_type_combo)
        filter_layout.addWidget(self.refresh_button)
        filter_layout.addStretch(1)
        
        # 使用表格替代列表
        self.table = QTableWidget()
        
        # 配置表格
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        # 设置列数和表头 - 确保表头与数据处理匹配
        self.table.setColumnCount(4)
        # 第一列显示"文件名"，但实际是从文件路径中提取的
        self.column_headers = ["文件名", "文件路径", "跳过原因", "时间"]
        self.table.setHorizontalHeaderLabels(self.column_headers)
        
        # 设置列宽调整模式
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # 文件名
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)         # 文件路径
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents) # 跳过原因
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) # 时间
        
        # 分页控件
        paging_layout = QHBoxLayout()
        self.prev_button = QPushButton("上一页")
        self.next_button = QPushButton("下一页")
        self.page_info_label = QLabel("0/0")
        self.page_info_label.setAlignment(Qt.AlignCenter)
        
        paging_layout.addWidget(self.prev_button)
        paging_layout.addWidget(self.page_info_label)
        paging_layout.addWidget(self.next_button)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        self.open_file_button = QPushButton("打开文件")
        self.open_folder_button = QPushButton("打开文件夹")
        self.clear_log_button = QPushButton("清空记录")
        self.close_button = QPushButton("关闭")
        
        button_layout.addWidget(self.open_file_button)
        button_layout.addWidget(self.open_folder_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.clear_log_button)
        button_layout.addWidget(self.close_button)
        
        # 添加所有布局
        layout.addLayout(filter_layout)
        layout.addWidget(self.table)
        layout.addLayout(paging_layout)
        layout.addLayout(button_layout)
        
        # 连接信号
        self.filter_type_combo.currentIndexChanged.connect(self._apply_filter)
        self.refresh_button.clicked.connect(self._load_skipped_files)
        self.prev_button.clicked.connect(self._go_to_prev_page)
        self.next_button.clicked.connect(self._go_to_next_page)
        self.open_file_button.clicked.connect(self._open_selected_file)
        self.open_folder_button.clicked.connect(self._open_selected_folder)
        self.clear_log_button.clicked.connect(self._clear_log)
        self.close_button.clicked.connect(self.accept)
        self.table.itemSelectionChanged.connect(self._update_button_states)
        
        # 初始化按钮状态
        self.open_file_button.setEnabled(False)
        self.open_folder_button.setEnabled(False)
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
    def _load_skipped_files(self):
        """加载跳过文件的记录"""
        # 获取索引目录
        default_index_path = str(Path.home() / "Documents" / "DocumentSearchIndex")
        index_dir = self.settings.value("indexing/indexDirectory", default_index_path)
        
        if not index_dir or not os.path.exists(index_dir):
            QMessageBox.warning(self, "错误", "索引目录不存在或未配置！请先配置并创建索引。")
            self.skipped_files = []
            self._apply_filter()
            return
            
        # 构建日志文件路径
        log_file_path = os.path.join(index_dir, "index_skipped_files.tsv")
        
        if not os.path.exists(log_file_path):
            QMessageBox.information(self, "提示", "未找到跳过文件的记录，可能没有文件被跳过。")
            self.skipped_files = []
            self._apply_filter()
            return
            
        try:
            # 读取TSV文件
            self.skipped_files = []
            expected_headers = ["文件路径", "跳过原因", "时间"] # 定义预期的表头
            
            with open(log_file_path, 'r', encoding='utf-8') as f:
                import csv
                reader = csv.reader(f, delimiter='\t')
                
                # 尝试读取文件头进行验证，但不强制要求与预期完全一致
                try:
                    header_row = next(reader)
                    print(f"DEBUG: TSV文件头: {header_row}")
                    if header_row != expected_headers:
                         print(f"警告: TSV文件头不符合预期: {header_row} vs {expected_headers}")
                except StopIteration:
                    print("警告: TSV文件为空或只有表头。")
                    self._apply_filter() # 确保UI更新为空状态
                    return # 文件为空，无需继续

                # 读取数据行
                for idx, row in enumerate(reader):
                    # 增加检查，如果当前行内容与表头相同，则跳过
                    if row == expected_headers:
                        print(f"DEBUG: 跳过第 {idx+2} 行，内容疑似表头: {row}")
                        continue
                        
                    if len(row) >= 3:
                        file_path, reason, timestamp = row[0], row[1], row[2]
                        
                        # 提取原因类型
                        reason_type = "unknown"
                        if "PDF处理超时" in reason:
                            reason_type = "pdf_timeout"
                        elif "内容大小超过限制" in reason:
                            reason_type = "content_limit"
                        elif "需要密码的ZIP" in reason:
                            reason_type = "password_zip"
                        elif "需要密码的RAR" in reason:
                            reason_type = "password_rar"
                        elif "损坏的ZIP" in reason:
                            reason_type = "corrupted_zip"
                        elif "损坏的RAR" in reason:
                            reason_type = "corrupted_rar"
                        
                        self.skipped_files.append({
                            "file_path": file_path,
                            "reason": reason,
                            "reason_type": reason_type,
                            "timestamp": timestamp
                        })
                    else:
                        print(f"警告: 跳过格式不正确的行 {idx+2}: {row}")
            
            # 按时间戳倒序排序（最新的在前面）
            self.skipped_files.sort(key=lambda x: x["timestamp"], reverse=True)
            print(f"DEBUG: 加载了 {len(self.skipped_files)} 条有效跳过文件记录")
            
            # 应用过滤器并更新UI
            self._apply_filter()
            
            # 如果成功加载了记录，显示提示
            if self.skipped_files:
                # 移除加载成功的消息框，避免过多弹窗
                # QMessageBox.information(self, "已加载", f"已加载 {len(self.skipped_files)} 条跳过文件记录。")
                pass
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取跳过文件记录时出错: {e}")
            import traceback
            print(f"加载跳过文件错误: {e}\n{traceback.format_exc()}")
            self.skipped_files = []
            self._apply_filter()
    
    def _apply_filter(self):
        """应用过滤并更新UI"""
        filter_type = self.filter_type_combo.currentData()
        
        # 过滤记录
        if filter_type == "all":
            self.filtered_files = self.skipped_files.copy()
        else:
            self.filtered_files = [
                f for f in self.skipped_files 
                if f["reason_type"] == filter_type
            ]
            
        # 重置分页
        self.current_page = 0
        self._update_ui()
    
    def _update_ui(self):
        """更新UI显示"""
        # 清空表格内容，保留表头 - 只移除所有行，不清除表头
        self.table.setRowCount(0)
        
        # 计算总页数
        total_items = len(self.filtered_files)
        print(f"DEBUG: 更新UI，过滤后文件总数: {total_items}")
        total_pages = max(1, (total_items + self.page_size - 1) // self.page_size)
        
        # 更新页码信息
        if total_items == 0:
            self.page_info_label.setText("0/0")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            return  # 没有记录，直接返回
        else:
            self.current_page = min(self.current_page, total_pages - 1)
            self.page_info_label.setText(f"{self.current_page + 1}/{total_pages}")
            self.prev_button.setEnabled(self.current_page > 0)
            self.next_button.setEnabled(self.current_page < total_pages - 1)
        
        # 获取当前页的数据
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, total_items)
        current_page_data = self.filtered_files[start_idx:end_idx]
        print(f"DEBUG: 当前页显示 {start_idx} 到 {end_idx} 的记录，共 {len(current_page_data)} 条")
        
        # 添加到表格 - 确保表格列数与表头一致
        for row_idx, item_data in enumerate(current_page_data):
            file_path = item_data["file_path"]
            # 从文件路径中提取文件名
            file_name = Path(file_path).name
            reason = item_data["reason"]
            timestamp = item_data["timestamp"]
            
            # 插入新行
            self.table.insertRow(row_idx)
            
            # 设置各列的数据
            try:
                # 第一列是文件名（从路径提取）
                self.table.setItem(row_idx, 0, QTableWidgetItem(file_name))
                # 第二列是完整路径
                self.table.setItem(row_idx, 1, QTableWidgetItem(file_path))
                # 第三列是跳过原因
                self.table.setItem(row_idx, 2, QTableWidgetItem(reason))
                # 第四列是时间戳
                self.table.setItem(row_idx, 3, QTableWidgetItem(timestamp))
                
                # 存储完整数据到第一个单元格
                self.table.item(row_idx, 0).setData(Qt.UserRole, item_data)
            except Exception as e:
                print(f"设置表格单元格时出错: {e}")
        
        # 确保表头可见且正确
        if self.table.rowCount() > 0:
            print(f"DEBUG: 表格行数: {self.table.rowCount()}, 表头: {self.column_headers}")
        
        # 更新按钮状态
        has_selection = len(self.table.selectedItems()) > 0
        self.open_file_button.setEnabled(has_selection)
        self.open_folder_button.setEnabled(has_selection)
    
    def _go_to_prev_page(self):
        """转到上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_ui()
    
    def _go_to_next_page(self):
        """转到下一页"""
        total_pages = (len(self.filtered_files) + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._update_ui()
    
    def _open_selected_file(self):
        """打开选中的文件"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        # 从第一个单元格获取存储的完整数据
        item_data = self.table.item(row, 0).data(Qt.UserRole)
        file_path = item_data["file_path"]
        
        # 处理压缩包内文件
        if "::" in file_path:
            archive_path = file_path.split("::")[0]
            file_path = archive_path  # 打开压缩包而不是里面的文件
            
        # 使用主窗口的方法打开文件
        if self.parent():
            self.parent()._open_path_with_desktop_services(file_path, is_file=True)
    
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
        """窗口显示时加载数据"""
        super().showEvent(event)
        
        print("DEBUG: SkippedFilesDialog showEvent - 清空表格并准备加载数据")
        # 确保表格完全清空，但保留表头
        # 首先重置行数为0，这会清除所有数据行但保留表头
        self.table.setRowCount(0)
        
        # 加载数据
        self._load_skipped_files()

    def closeEvent(self, event):
        """保存窗口大小"""
        self.settings.setValue("skippedFilesDialog/geometry", self.saveGeometry())
        super().closeEvent(event)

    def _update_button_states(self):
        """根据当前选择状态更新按钮的启用状态"""
        has_selection = len(self.table.selectedItems()) > 0
        self.open_file_button.setEnabled(has_selection)
        self.open_folder_button.setEnabled(has_selection)

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
    
    # Make app aware of HiDPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)  # Create the application instance

    # Setup QSettings before creating MainWindow if it reads settings in __init__
    QApplication.setOrganizationName(ORGANIZATION_NAME)
    QApplication.setApplicationName(APPLICATION_NAME)

    window = MainWindow()  # Create the main window
    window.show()  # Show the window
    sys.exit(app.exec())  # Start the application event loop

# --- Replaced: original LicenseActivationDialog has been moved to license_manager.py ---
# class LicenseActivationDialog(QDialog):
    """用于激活许可证的对话框"""
    
    def __init__(self, parent=None, license_manager=None):
        super().__init__(parent)
        self.license_manager = license_manager
        self.setWindowTitle("许可证激活")
        self.setMinimumWidth(400)
        
        self._create_ui()
        
    def _create_ui(self):
        layout = QVBoxLayout(self)
        
        # 标题和说明
        title_label = QLabel("<h3>激活专业版</h3>")
        layout.addWidget(title_label)
        
        description_label = QLabel("请输入您的许可证密钥来激活专业版功能:")
        layout.addWidget(description_label)
        
        # 许可证密钥输入
        key_layout = QHBoxLayout()
        key_label = QLabel("许可证密钥:")
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("输入许可证密钥...")
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_edit)
        layout.addLayout(key_layout)
        
        # 专业版功能列表
        features_group = QGroupBox("专业版功能")
        features_layout = QVBoxLayout(features_group)
        
        for feature_id, description in self.license_manager.FEATURE_DESCRIPTIONS.items():
            feature_label = QLabel(f"✓ {description}")
            features_layout.addWidget(feature_label)
        
        layout.addWidget(features_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.activate_button = QPushButton("激活")
        self.activate_button.clicked.connect(self._activate_license)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.activate_button)
        
        layout.addLayout(button_layout)
    
    def _activate_license(self):
        license_key = self.key_edit.text().strip()
        
        if not license_key:
            QMessageBox.warning(self, "输入错误", "请输入许可证密钥")
            return
        
        success, message = self.license_manager.activate_license(license_key)
        
        if success:
            QMessageBox.information(self, "激活成功", f"专业版已成功激活\n{message}")
            self.accept()
        else:
            QMessageBox.critical(self, "激活失败", f"无法激活许可证\n{message}")

# --- Replaced: original LicenseStatusDialog has been moved to license_manager.py ---
# class LicenseStatusDialog(QDialog):
    """显示许可证状态的对话框"""
    
    def __init__(self, parent=None, license_manager=None):
        super().__init__(parent)
        self.license_manager = license_manager
        self.setWindowTitle("许可证状态")
        self.setMinimumWidth(400)
        
        self._create_ui()
        
    def _create_ui(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("<h3>许可证状态</h3>")
        layout.addWidget(title_label)
        
        # 状态信息
        status_group = QGroupBox("当前状态")
        status_layout = QVBoxLayout(status_group)
        
        # 许可证状态
        self.status_label = QLabel()
        status_layout.addWidget(self.status_label)
        
        # 许可证类型
        self.type_label = QLabel()
        status_layout.addWidget(self.type_label)
        
        # 许可证有效期
        self.validity_label = QLabel()
        status_layout.addWidget(self.validity_label)
        
        # 更新期限
        self.update_label = QLabel()
        status_layout.addWidget(self.update_label)
        
        layout.addWidget(status_group)
        
        # 功能列表
        features_group = QGroupBox("专业版功能")
        features_layout = QVBoxLayout(features_group)
        
        self.feature_labels = {}
        for feature_id, description in self.license_manager.FEATURE_DESCRIPTIONS.items():
            enabled = self.license_manager.is_feature_enabled(feature_id)
            status_icon = "✓" if enabled else "✗"
            self.feature_labels[feature_id] = QLabel(f"{status_icon} {description}")
            features_layout.addWidget(self.feature_labels[feature_id])
        
        layout.addWidget(features_group)
        
        # 激活/停用按钮
        button_layout = QHBoxLayout()
        
        # 创建激活按钮
        self.activate_button = QPushButton("激活许可证")
        self.activate_button.clicked.connect(self._show_activation_dialog)
        
        # 创建停用按钮
        self.deactivate_button = QPushButton("停用许可证")
        self.deactivate_button.clicked.connect(self._deactivate_license)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.activate_button)
        button_layout.addWidget(self.deactivate_button)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # 更新对话框内容
        self._update_ui()
    
    def _update_ui(self):
        # 更新许可证状态信息
        is_valid = self.license_manager.is_license_valid()
        
        # 设置许可证状态文本
        self.status_label.setText(f"当前状态: {self.license_manager.get_license_status_text()}")
        
        # 许可证类型
        license_type = "专业版" if is_valid else "免费版"
        self.type_label.setText(f"版本类型: {license_type}")
        
        # 许可证有效期
        if is_valid and hasattr(self.license_manager, 'license_data') and 'expiry_date' in self.license_manager.license_data:
            expiry_date = self.license_manager.license_data['expiry_date']
            self.validity_label.setText(f"有效期至: {expiry_date}")
        else:
            self.validity_label.setText("有效期至: 不适用")
        
        # 更新期限
        if is_valid and self.license_manager.is_in_update_period():
            update_text = "在更新支持期内"
        elif is_valid:
            update_text = "更新支持已过期，但许可证仍然有效"
        else:
            update_text = "不适用"
        self.update_label.setText(f"更新支持: {update_text}")
        
        # 更新功能状态
        for feature_id, label in self.feature_labels.items():
            enabled = self.license_manager.is_feature_enabled(feature_id)
            status_icon = "✓" if enabled else "✗"
            label.setText(f"{status_icon} {self.license_manager.FEATURE_DESCRIPTIONS[feature_id]}")
        
        # 更新按钮状态
        self.deactivate_button.setEnabled(is_valid)
    
    def _show_activation_dialog(self):
        dialog = LicenseActivationDialog(self, self.license_manager)
        if dialog.exec():
            self._update_ui()
            # 通知主窗口许可证状态已更新
            if hasattr(self.parent(), 'update_license_status_in_ui'):
                self.parent().update_license_status_in_ui()
    
    def _deactivate_license(self):
        reply = QMessageBox.question(
            self, 
            "确认停用", 
            "确定要停用当前许可证吗？您将失去专业版功能的访问权限。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.license_manager.deactivate_license()
            if success:
                QMessageBox.information(self, "停用成功", "许可证已成功停用")
                self._update_ui()
                # 通知主窗口许可证状态已更新
                if hasattr(self.parent(), 'update_license_status_in_ui'):
                    self.parent().update_license_status_in_ui()
            else:
                QMessageBox.critical(self, "停用失败", f"无法停用许可证\n{message}")

# --- Main Execution ---