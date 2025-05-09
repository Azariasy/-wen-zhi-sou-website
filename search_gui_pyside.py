import sys
# Import necessary classes from PySide6
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextBrowser, QProgressBar,
    QFileDialog, QMessageBox, QDateEdit, QCheckBox, QComboBox, QRadioButton, QDialog, QDialogButtonBox, QSpinBox,
    QButtonGroup, QListWidget, QListWidgetItem, QAbstractItemView, QGroupBox, QMenuBar, QToolBar, # ADDED QListWidget, QListWidgetItem, QAbstractItemView, QGroupBox, QMenuBar, QToolBar
    QStatusBar, # Ensure QProgressBar is imported if not already
    QTableWidget, QHeaderView, QTableWidgetItem,
    QTreeView, QSplitter, # 添加文件夹树视图所需的组件
)
from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot, QUrl, QSettings, QDate, QTimer, QSize, QDir, QModelIndex # Added QSize, QDir and QModelIndex 
from PySide6.QtGui import QDesktopServices, QAction, QIntValidator, QShortcut, QKeySequence, QIcon, QColor, QStandardItemModel, QStandardItem # Added QStandardItemModel and QStandardItem
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
    # --- ADDED: Signals for update check --- 
    updateAvailableSignal = Signal(dict) # Sends dict with version info
    upToDateSignal = Signal()
    updateCheckFailedSignal = Signal(str) # Sends error message
    # ---------------------------------------
    
    def __init__(self):
        super().__init__()
        # 添加一个标志位，用于指示是否请求停止操作
        self.stop_requested = False
        
    def _check_stop_requested(self):
        """检查是否请求了停止操作，如果是则抛出异常"""
        if self.stop_requested:
            raise InterruptedError("操作被用户中断")

    @Slot(list, str, bool, int, int) # Added int for txt_content_limit_kb
    def run_indexing(self, source_directories, index_dir_path, enable_ocr, extraction_timeout, txt_content_limit_kb):
        """Runs the indexing process in the background for multiple source directories."""
        try:
            # 重置停止标志位
            self.stop_requested = False
            
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
            generator = document_search.create_or_update_index(
                source_directories,
                index_dir_path,
                enable_ocr,
                extraction_timeout=extraction_timeout, # Pass timeout here
                txt_content_limit_kb=txt_content_limit_kb # Pass txt limit here
            )

            for update in generator:
                # 检查是否请求了停止
                self._check_stop_requested()
                
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
            self.indexingComplete.emit(summary_dict)
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
            # 重置停止标志位
            self.stop_requested = False
            
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
                search_scope # Pass scope here
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

    # --- ADDED: Worker method for checking updates --- 
    @Slot(str, str) # current_version, update_url
    def run_update_check(self, current_version_str, update_url):
        """Performs the update check in the background."""
        try:
            print(f"Checking for updates at {update_url}...")
            response = requests.get(update_url, timeout=10) # 10 second timeout
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            latest_info = response.json()
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
                
        except requests.exceptions.RequestException as e:
            error_msg = f"检查更新时网络错误: {e}"
            print(f"Error: {error_msg}")
            self.updateCheckFailedSignal.emit(error_msg)
        except json.JSONDecodeError:
            error_msg = "无法解析更新信息文件。文件格式可能不正确。"
            print(f"Error: {error_msg}")
            self.updateCheckFailedSignal.emit(error_msg)
        except ValueError as e:
            error_msg = f"更新信息文件内容错误: {e}"
            print(f"Error: {error_msg}")
            self.updateCheckFailedSignal.emit(error_msg)
        except Exception as e:
            error_msg = f"检查更新时发生未知错误: {e}"
            print(f"Error: {error_msg}")
            # traceback.print_exc() # Optional: more detailed logging
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

        index_group_layout.addWidget(source_dirs_label)
        index_group_layout.addWidget(self.source_dirs_list)
        index_group_layout.addLayout(source_dirs_button_layout)
        index_group_layout.addSpacing(15) # Add some space before next setting

        # --- OCR Setting ---
        # --- MODIFIED: 添加OCR设置区域和专业版标记 ---
        ocr_layout = QHBoxLayout()
        self.enable_ocr_checkbox = QCheckBox("索引时启用 OCR (适用于 PDF, 可能显著增加时长)")
        self.pro_feature_ocr_label = QLabel("专业版专享")
        self.pro_feature_ocr_label.setStyleSheet("color: #FF6600; font-weight: bold;")
        ocr_layout.addWidget(self.enable_ocr_checkbox)
        ocr_layout.addWidget(self.pro_feature_ocr_label)
        ocr_layout.addStretch()
        index_group_layout.addLayout(ocr_layout)
        
        # 根据许可状态禁用OCR选项
        pdf_support_available = self.license_manager.is_feature_available(Features.PDF_SUPPORT)
        self.enable_ocr_checkbox.setEnabled(pdf_support_available)
        self.pro_feature_ocr_label.setVisible(not pdf_support_available)
        
        # 添加提示信息
        self.enable_ocr_checkbox.setToolTip("OCR功能需要专业版授权才能使用" if not pdf_support_available else 
                                       "启用OCR可以识别PDF中的图像文字，但会显著增加索引时间")
        # ----------------------------------------
        
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
        
        # 检查高级主题是否可用
        advanced_themes_available = self.license_manager.is_feature_available(Features.ADVANCED_THEMES)
        
        # 添加专业版主题，根据许可证状态禁用或启用
        pro_themes = ["现代绿", "现代紫"]
        
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
                    "高级主题（现代绿、现代紫）仅在专业版中可用。\n"
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
            for item in selected_items:
                # QListWidget.takeItem requires the row index
                row = self.source_dirs_list.row(item)
                self.source_dirs_list.takeItem(row)

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
        
        # --- ADDED: Load Size Filter Settings ---
        min_size = settings.value("search/minSizeKB", "", type=str)
        self.min_size_entry.setText(min_size)
        
        max_size = settings.value("search/maxSizeKB", "", type=str)
        self.max_size_entry.setText(max_size)
        # ------------------------------------
        
        # --- ADDED: Load Date Filter Settings ---
        # 设置默认日期范围
        default_start_date = QDate(1900, 1, 1)
        default_end_date = QDate.currentDate()
        
        # 从设置中读取日期
        start_date_str = settings.value("search/startDate", "")
        if start_date_str:
            self.start_date_edit.setDate(QDate.fromString(start_date_str, "yyyy-MM-dd"))
        else:
            self.start_date_edit.setDate(default_start_date)
            
        end_date_str = settings.value("search/endDate", "")
        if end_date_str:
            self.end_date_edit.setDate(QDate.fromString(end_date_str, "yyyy-MM-dd"))
        else:
            self.end_date_edit.setDate(default_end_date)
        # ------------------------------------

        # --- Load UI Settings ---
        theme = settings.value("ui/theme", "现代蓝") # Default to 'Modern Blue'
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
        
        # --- ADDED: Save Size Filter Settings ---
        settings.setValue("search/minSizeKB", self.min_size_entry.text())
        settings.setValue("search/maxSizeKB", self.max_size_entry.text())
        # ------------------------------------
        
        # --- ADDED: Save Date Filter Settings ---
        # 保存日期设置
        if self.start_date_edit.date() != QDate(1900, 1, 1):  # 如果不是默认日期，才保存
            settings.setValue("search/startDate", self.start_date_edit.date().toString("yyyy-MM-dd"))
        else:
            settings.setValue("search/startDate", "")
            
        if self.end_date_edit.date() != QDate.currentDate():  # 如果不是默认日期，才保存
            settings.setValue("search/endDate", self.end_date_edit.date().toString("yyyy-MM-dd"))
        else:
            settings.setValue("search/endDate", "")
        # ------------------------------------
        
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
        print(f"Min Size (KB): {self.min_size_entry.text()}")
        print(f"Max Size (KB): {self.max_size_entry.text()}")
        print(f"Start Date: {self.start_date_edit.date().toString('yyyy-MM-dd')}")
        print(f"End Date: {self.end_date_edit.date().toString('yyyy-MM-dd')}")
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

    def _clear_dates(self):
        """清除日期筛选，恢复为默认值"""
        self.start_date_edit.setDate(QDate(1900, 1, 1))
        self.end_date_edit.setDate(QDate.currentDate())

# --- Main GUI Window ---
class MainWindow(QMainWindow):  # Changed base class to QMainWindow
    # Signal to trigger indexing in the worker thread
    # --- MODIFIED: Add int parameter for txt_content_limit_kb ---
    startIndexingSignal = Signal(list, str, bool, int, int) # source_dirs, index_dir, enable_ocr, timeout, txt_limit_kb
    # ---------------------------------------------------------
    # Signal to trigger search in the worker thread (add types for size, date, file type, and case sensitivity)
    startSearchSignal = Signal(str, str, object, object, object, object, object, str, bool, str) # Added str for search_scope
    # --- ADDED: Signal for update check --- 
    startUpdateCheckSignal = Signal(str, str) # current_version, update_url
    # ----------------------------------------

    def __init__(self):
        super().__init__()
        self.setWindowTitle("文智搜 (PySide6)")
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
        self.skipped_files_dialog = None # ADDED: Initialize skipped files dialog instance
        
        # --- 添加文件夹树与搜索结果的过滤变量 ---
        self.filtered_by_folder = False  # 是否按文件夹进行了过滤
        self.current_filter_folder = None  # 当前过滤的文件夹路径
        # ---------------------------------------

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
        # 移除文件大小筛选条件
        # 移除修改日期筛选条件
        sort_layout = self._create_sort_bar() # Assume helper exists
        main_layout.addLayout(sort_layout)
        type_filter_layout = self._create_type_filter_bar() # Assume helper exists
        main_layout.addLayout(type_filter_layout)

        # --- Action Buttons ---
        action_layout = self._create_action_buttons() # Assume helper exists
        main_layout.addLayout(action_layout)
        
        # --- 创建水平分隔器，添加文件夹树视图和搜索结果 ---
        self.main_splitter = QSplitter(Qt.Horizontal)
        # 设置分隔器手柄样式
        self.main_splitter.setHandleWidth(5)
        self.main_splitter.setChildrenCollapsible(False)
        
        # 创建文件夹树视图
        self.folder_tree = FolderTreeWidget()
        self.main_splitter.addWidget(self.folder_tree)
        
        # 创建搜索结果显示区
        self.results_text = QTextBrowser() 
        self.results_text.setOpenLinks(False)
        self.main_splitter.addWidget(self.results_text)
        
        # 设置初始分隔比例 (文件夹树:搜索结果 = 1:3)
        self.main_splitter.setSizes([200, 600])
        
        # 将分隔器添加到主布局
        main_layout.addWidget(self.main_splitter, 1)
        # ----------------------------------------------
        
        # --- Status Bar ---
        self._setup_status_bar() # Call helper

        # --- Create Menubar --- 
        self._create_menubar()
        
        # --- Setup Worker Thread --- 
        self._setup_worker_thread()

        # --- Setup Connections (AFTER UI Elements Created) ---
        self._setup_connections() # Setup AFTER all UI elements are created

        # --- Restore Window Geometry --- 
        # 直接在这里实现窗口几何恢复，而不是调用方法
        geometry = self.settings.value("windowGeometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # --- ADDED: Initialize license manager AFTER UI elements but BEFORE applying settings ---
        self._init_license_manager()
        # ---------------------------------------
        
        # --- Apply Initial Settings (AFTER UI Elements Created) ---
        self.apply_theme(self.settings.value("ui/theme", "系统默认"))
        self._load_and_apply_default_sort()
        self._apply_result_font_size()
        self._load_search_history() # NOW safe to call

        # --- ADDED: Setup Shortcuts ---
        self._setup_shortcuts()
        # ----------------------------
        
        # --- ADDED: Set initial state for mode buttons ---
        self._update_mode_buttons_state_slot()
        # ------------------------------------------------
        
        # --- 保存和恢复分隔器位置 ---
        splitter_state = self.settings.value("ui/splitterState")
        if splitter_state:
            self.main_splitter.restoreState(splitter_state)

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
        self.search_button.setObjectName("search_button")
        layout.addWidget(self.search_button)
        # Clear Button
        self.clear_search_button = QPushButton("清空输入")
        layout.addWidget(self.clear_search_button)
        return layout

    # (Add other _create_* helper methods if they were inline before)
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
        # 添加清除结果按钮
        self.clear_results_button = QPushButton("清除结果")
        self.clear_results_button.setToolTip("清除当前搜索结果")
        sort_layout.addWidget(self.clear_results_button)
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
        """创建操作按钮区域"""
        action_layout = QHBoxLayout()
        
        # 创建索引按钮
        self.index_button = QPushButton("创建索引")
        self.index_button.setObjectName("index_button")
        self.index_button.setToolTip("创建或更新文档索引")
        
        # 查看跳过的文件按钮
        self.view_skipped_button = QPushButton("查看跳过文件")
        self.view_skipped_button.setToolTip("查看在创建索引过程中被跳过的文件")
        
        # 为保持兼容性，添加同名变量引用
        self.view_skipped_files_button = self.view_skipped_button
        
        # 将按钮添加到布局
        action_layout.addWidget(self.index_button)
        action_layout.addWidget(self.view_skipped_button)
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
            self.worker.indexingComplete.connect(self.indexing_finished_slot)
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
        self.view_skipped_button.clicked.connect(self.show_skipped_files_dialog_slot)
        # --------------------------------

        # --- Search buttons ---
        self.search_button.clicked.connect(self.start_search_slot)
        self.clear_search_button.clicked.connect(self.clear_search_entry_slot)
        self.clear_results_button.clicked.connect(self.clear_results_slot)

        # --- Date fields ---

        # --- Results text browser ---
        self.results_text.anchorClicked.connect(self.handle_link_clicked_slot)

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
        for checkbox in self.file_type_checkboxes:  # Assume these checkboxes setup earlier
            checkbox.stateChanged.connect(self._filter_results_by_type_slot)
            
        # --- Sort option changes trigger redisplay ---
        self.sort_combo.currentIndexChanged.connect(self._sort_and_redisplay_results_slot)
        # Direction also changes the sorting
        self.sort_desc_radio.toggled.connect(self._sort_and_redisplay_results_slot)
        
        # --- ADDED: Scope radio buttons toggle affects mode buttons ---
        self.scope_button_group.buttonToggled.connect(self._update_mode_buttons_state_slot)
        # ----------------------------------------------------------
        
        # --- 文件夹树视图信号连接 ---
        self.folder_tree.folderSelected.connect(self._filter_results_by_folder_slot)
        # --------------------------
    
    @Slot(list)
    def _handle_new_search_results_slot(self, backend_results):
        """处理从Worker接收到的新搜索结果，存储并显示"""
        print(f"Received {len(backend_results)} search results from backend")
        
        # Store original results
        self.original_search_results = backend_results
        
        # Apply any type filters
        self._filter_results_by_type_slot()
        
        # 根据搜索结果构建文件夹树
        self.folder_tree.build_folder_tree_from_results(backend_results)
    
    @Slot(str)
    def _filter_results_by_folder_slot(self, folder_path):
        """按文件夹路径过滤搜索结果
        
        Args:
            folder_path: 要过滤的文件夹路径
        """
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
    def _filter_results_by_type_slot(self):
        """基于所选文件类型复选框过滤搜索结果"""
        # First, check if any filters are applied
        selected_types = []
        for checkbox, type_value in self.file_type_checkboxes.items():
            if checkbox.isChecked():
                selected_types.append(type_value)
        
        # If no filters selected, use all original results
        if not selected_types:
            filtered_results = self.original_search_results
        else:
            # Filter results based on selected file types
            filtered_results = []
            for result in self.original_search_results:
                file_path = result.get('file_path', '')
                file_type = None
                
                # Extract file extension
                if file_path:
                    lower_path = file_path.lower()
                    for ext in ['.pdf', '.docx', '.txt', '.xlsx', '.pptx', '.eml', '.msg', '.html', '.htm', '.rtf', '.md']:
                        if lower_path.endswith(ext):
                            file_type = ext[1:]  # Remove leading dot
                            # Special case for .htm -> html
                            if file_type == 'htm':
                                file_type = 'html'
                            break
                
                # Add result if it matches selected types
                if file_type and file_type in selected_types:
                    filtered_results.append(result)
        
        # --- 添加文件夹过滤 ---
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
        # -----------------------
        
        # Store filtered results
        self.search_results = filtered_results
        
        # Sort and display
        self._sort_and_redisplay_results_slot()
        
    @Slot()
    def _sort_and_redisplay_results_slot(self):
        """Sort results based on current sort settings and redisplay."""
        # 获取排序键
        combo_text = self.sort_combo.currentText()
        if combo_text == "相关度":
            sort_key = 'score'
        elif combo_text == "文件路径":
            sort_key = 'path'
        elif combo_text == "修改日期":
            sort_key = 'date'
        elif combo_text == "文件大小":
            sort_key = 'size'
        else:
            sort_key = 'score'  # 默认为相关度
        
        # 获取排序方向
        is_descending = self.sort_desc_radio.isChecked()
        
        # 如果排序配置已更改，更新并保存设置
        if sort_key != self.current_sort_key or is_descending != self.current_sort_descending:
            self.current_sort_key = sort_key
            self.current_sort_descending = is_descending
            self._save_default_sort()
        
        # 对结果进行排序
        results_to_sort = list(self.search_results)  # 创建副本进行排序
        
        def get_sort_key(item):
            if sort_key == 'score':
                # 相关度得分，可能是None
                return item.get('score', 0) or 0
            elif sort_key == 'path':
                # 按文件路径排序
                return item.get('file_path', '').lower()
            elif sort_key == 'date':
                # 按修改日期排序，格式为ISO字符串
                date_str = item.get('file_date', '')
                if not date_str:
                    # 如果没有日期，归为最早或最晚
                    return '1900-01-01' if is_descending else '9999-12-31'
                return date_str
            elif sort_key == 'size':
                # 按文件大小排序
                return item.get('file_size_kb', 0) or 0
            else:
                # 默认按相关度排序
                return item.get('score', 0) or 0
        
        # 执行排序
        results_to_sort.sort(
            key=get_sort_key,
            reverse=is_descending
        )
        
        # 更新并显示排序后的结果
        self.search_results = results_to_sort
        self.display_search_results_slot(self.search_results)
        
        # 更新状态消息（反映过滤状态）
        result_count = len(self.search_results)
        total_count = len(self.original_search_results)
        
        if self.filtered_by_folder and self.current_filter_folder:
            self.statusBar().showMessage(f"显示 '{self.current_filter_folder}' 中的 {result_count} 条结果 (总共 {total_count} 条)", 0)
        elif result_count != total_count:
            # 其他过滤条件（如文件类型）
            self.statusBar().showMessage(f"显示 {result_count} / {total_count} 条经过过滤的结果", 0)
        else:
            self.statusBar().showMessage(f"显示 {result_count} 条结果", 0)

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
            
        if filter_parts:
            status_msg += f" (筛选条件: {', '.join(filter_parts)})"
        
        self.statusBar().showMessage(status_msg + "...", 0)
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
            current_theme = self.settings.value("ui/theme", "现代蓝")
            if current_theme == "现代蓝":
                # Modern Blue theme colors
                phrase_bg_color = "#E3F2FD" # 浅蓝色背景
                fuzzy_bg_color = "#E1F5FE"  # 更浅的蓝色背景
                highlight_text_color = "#2980b9" # 蓝色文本
                link_color = "#3498db" # 蓝色链接
                toggle_color = "#3498db" # 折叠按钮也使用蓝色
            elif current_theme == "现代绿":
                # Modern Green theme colors
                phrase_bg_color = "#E8F5E9" # 浅绿色背景
                fuzzy_bg_color = "#F1F8E9"  # 更浅的绿色背景
                highlight_text_color = "#27ae60" # 绿色文本
                link_color = "#2ecc71" # 绿色链接
                toggle_color = "#2ecc71" # 折叠按钮也使用绿色
            elif current_theme == "现代紫":
                # Modern Purple theme colors
                phrase_bg_color = "#F3E5F5" # 浅紫色背景
                fuzzy_bg_color = "#EDE7F6"  # 更浅的紫色背景
                highlight_text_color = "#8e44ad" # 紫色文本
                link_color = "#9b59b6" # 紫色链接
                toggle_color = "#9b59b6" # 折叠按钮也使用紫色
            else:
                # Light/Default theme colors
                phrase_bg_color = "#F5F5F5" # 浅灰色背景
                fuzzy_bg_color = "#EEEEEE"  # 更浅的灰色背景
                highlight_text_color = "#333333" # 深灰色文本
                link_color = "#0366d6" # GitHub风格的蓝色链接
                toggle_color = "#0366d6" # 折叠按钮也使用相同的蓝色
            
            # Define span tags with both background and text color
            phrase_highlight_start = f'<span style="background-color: {phrase_bg_color}; color: {highlight_text_color};">'
            fuzzy_highlight_start = f'<span style="background-color: {fuzzy_bg_color}; color: {highlight_text_color};">'
            highlight_end = '</span>'
            
            # Define link styles with matching theme colors
            link_style = f'style="color: {link_color}; text-decoration:none; font-weight:bold;"'
            toggle_link_style = f'style="color: {toggle_color}; text-decoration:none; font-weight:bold;"'
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
        
        # 重置文件夹过滤状态
        self.filtered_by_folder = False
        self.current_filter_folder = None
        
        # 根据搜索结果构建文件夹树
        self.folder_tree.build_folder_tree_from_results(backend_results)
        
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
        print("DEBUG: _filter_results_by_type_slot triggered")  # DEBUG
        # REMOVED BUSY CHECK - Checkboxes are disabled by set_busy_state anyway
        # if self.is_busy:
        #     # print("  Busy, skipping filter")  # DEBUG
        #     return # Don\'t filter if an operation is in progress
        
        # REMOVED check for empty last_search_results, now rely on original_search_results
        # if not self.last_search_results:

        checked_types = [ftype for cb, ftype in self.file_type_checkboxes.items() if cb.isChecked()]
        print(f"DEBUG: Checked types for filtering: {checked_types}")  # DEBUG
        
        # 应用文件类型过滤
        if not checked_types:
            # If no types are checked, show all original results
            print("DEBUG: No file types checked, using all original results")  # DEBUG
            filtered_results = self.original_search_results.copy()
        else:
            # Filter the ORIGINAL stored results based on checked types
            print("DEBUG: Filtering original results based on checked types...")  # DEBUG
            filtered_results = [item for item in self.original_search_results 
                                if item.get('file_type', '').lstrip('.').lower() in checked_types]
            print(f"DEBUG: Filtered results count after type filtering: {len(filtered_results)}")  # DEBUG
        
        # 应用文件夹过滤
        if self.filtered_by_folder and self.current_filter_folder:
            print(f"DEBUG: Applying folder filter for '{self.current_filter_folder}'")  # DEBUG
            folder_filtered_results = []
            for result in filtered_results:
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
            
            print(f"DEBUG: Filtered results count after folder filtering: {len(folder_filtered_results)}")  # DEBUG
            filtered_results = folder_filtered_results
        
        # 保存过滤后的结果并显示
        self.search_results = filtered_results
        
        # 更新状态栏消息
        total_count = len(self.original_search_results)
        filtered_count = len(filtered_results)
        
        if self.filtered_by_folder and self.current_filter_folder:
            folder_name = os.path.basename(self.current_filter_folder) or self.current_filter_folder
            self.statusBar().showMessage(f"显示文件夹 '{folder_name}' 中的 {filtered_count}/{total_count} 条结果", 0)
        elif filtered_count != total_count:
            self.statusBar().showMessage(f"显示 {filtered_count}/{total_count} 条经过过滤的结果", 0)
        
        # 使用过滤后的结果更新显示
        self.display_search_results_slot(filtered_results)

    # --- Link Handling Slot ---
    @Slot(QUrl)
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

        # --- ADDED: 许可证菜单 ---
        settings_menu.addSeparator()  # 添加分隔线
        license_action = QAction("许可证管理(&L)...", self)
        license_action.triggered.connect(self.show_license_dialog_slot)
        settings_menu.addAction(license_action)
        # ------------------------

        # --- Help Menu ---
        help_menu = menu_bar.addMenu("帮助(&H)")  # Add & for shortcut Alt+H
        
        # --- 添加升级到专业版菜单项 ---
        upgrade_action = QAction("升级到专业版(&U)...", self)
        upgrade_action.triggered.connect(self.show_license_dialog_slot)
        help_menu.addAction(upgrade_action)
        
        help_menu.addSeparator()  # 添加分隔线
        # ---------------------------------
        
        # --- ADDED: Check for updates menu item --- 
        check_update_action = QAction("检查更新(&U)...", self)
        check_update_action.triggered.connect(self.check_for_updates_slot) # Connect later
        help_menu.addAction(check_update_action)
        # ------------------------------------------
        
        about_action = QAction("关于(&A)...", self)  # Add & for shortcut Alt+A
        about_action.triggered.connect(self.show_about_dialog_slot)
        help_menu.addAction(about_action)

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

    # --- Theme Handling ---
    def apply_theme(self, theme_name):
        """应用程序主题设置"""
        app = QApplication.instance()
        
        # 检查非蓝色主题是否可用（是否有专业版许可证）
        advanced_themes_available = self.license_manager.is_feature_available(Features.ADVANCED_THEMES)
        
        # 如果选择了非蓝色主题但没有专业版许可证，就强制使用蓝色主题
        if theme_name != "现代蓝" and not advanced_themes_available:
            if not hasattr(self, '_theme_warning_shown'):
                self._theme_warning_shown = False
                
            if not self._theme_warning_shown:
                self._theme_warning_shown = True
                QMessageBox.information(
                    self, 
                    "主题限制", 
                    "高级主题（现代绿、现代紫）仅在专业版中可用。\n"
                    "已自动切换到现代蓝主题。\n"
                    "升级到专业版以解锁所有主题。"
                )
            
            # 强制使用现代蓝主题并保存设置
            theme_name = "现代蓝"
            self.settings.setValue("ui/theme", theme_name)
        
        if theme_name == "现代蓝":
            # 使用现代蓝色主题
            try:
                # 加载蓝色样式表，使用资源路径解析器
                style_path = get_resource_path("blue_style.qss")
                if os.path.exists(style_path):
                    with open(style_path, "r", encoding="utf-8") as f:
                        stylesheet = f.read()
                    
                    # 检查打包环境下的路径并修改URL引用
                    import sys
                    if getattr(sys, 'frozen', False):
                        # 在PyInstaller打包后的环境中
                        print("检测到打包环境，应用相对路径处理...")
                        # 获取资源文件所在的目录
                        base_path = sys._MEIPASS
                        
                        # 修改样式表中的图片URL路径为绝对路径
                        # 这解决了在打包环境中图片路径引用的问题
                        stylesheet = stylesheet.replace('image: url(', f'image: url("{base_path}/')
                        stylesheet = stylesheet.replace('.png)', '.png")')
                        
                        # 同时保持原有的替换逻辑
                        stylesheet = stylesheet.replace("image: url(checkmark.png)", "image: url(checkmark_blue.png)")
                        stylesheet = stylesheet.replace("image: url(down_arrow.png)", "image: url(down_arrow_blue.png)")
                    else:
                        # 在开发环境中
                        stylesheet = stylesheet.replace("image: url(checkmark.png)", "image: url(checkmark_blue.png)")
                        stylesheet = stylesheet.replace("image: url(down_arrow.png)", "image: url(down_arrow_blue.png)")
                    
                    # 确保进度条使用正确的蓝色主题颜色
                    progress_color = "#3498db"
                    import re
                    stylesheet = re.sub(
                        r'QProgressBar::chunk\s*\{\s*background-color:\s*#[0-9a-fA-F]+',
                        f'QProgressBar::chunk {{ background-color: {progress_color}',
                        stylesheet
                    )
                    
                    # 应用样式表
                    app.setStyleSheet(stylesheet)
                    print("Applied modern blue theme.")
                    
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
                else:
                    print(f"Blue style file not found: {style_path}")
                    # 回退到系统默认
                    app.setStyleSheet("")
            except Exception as e:
                print(f"Error applying modern blue style: {e}. Falling back to system default.")
                app.setStyleSheet("")
                
        elif theme_name == "现代绿":
            # 使用现代绿色主题
            try:
                # 加载绿色样式表，使用资源路径解析器
                style_path = get_resource_path("green_style.qss")
                if os.path.exists(style_path):
                    with open(style_path, "r", encoding="utf-8") as f:
                        stylesheet = f.read()
                    
                    # 检查打包环境下的路径并修改URL引用
                    import sys
                    if getattr(sys, 'frozen', False):
                        # 在PyInstaller打包后的环境中
                        print("检测到打包环境，应用相对路径处理...")
                        # 获取资源文件所在的目录
                        base_path = sys._MEIPASS
                        
                        # 修改样式表中的图片URL路径为绝对路径
                        # 这解决了在打包环境中图片路径引用的问题
                        stylesheet = stylesheet.replace('image: url(', f'image: url("{base_path}/')
                        stylesheet = stylesheet.replace('.png)', '.png")')
                        
                        # 同时保持原有的替换逻辑
                        stylesheet = stylesheet.replace("image: url(checkmark.png)", "image: url(checkmark_green.png)")
                        stylesheet = stylesheet.replace("image: url(down_arrow.png)", "image: url(down_arrow_green.png)")
                    else:
                        # 在开发环境中
                        stylesheet = stylesheet.replace("image: url(checkmark.png)", "image: url(checkmark_green.png)")
                        stylesheet = stylesheet.replace("image: url(down_arrow.png)", "image: url(down_arrow_green.png)")
                    
                    # 确保进度条使用正确的绿色主题颜色
                    progress_color = "#2ecc71"
                    import re
                    stylesheet = re.sub(
                        r'QProgressBar::chunk\s*\{\s*background-color:\s*#[0-9a-fA-F]+',
                        f'QProgressBar::chunk {{ background-color: {progress_color}',
                        stylesheet
                    )
                    
                    app.setStyleSheet(stylesheet)
                    print("Applied modern green theme.")
                    
                    # 通过编程方式直接设置下拉箭头和单选按钮图标
                    try:
                        from PySide6.QtGui import QIcon, QPixmap
                        arrow_icon_path = get_resource_path("down_arrow_green.png")
                        radio_icon_path = get_resource_path("radio_checked_green.png")
                        check_icon_path = get_resource_path("checkmark_green.png")
                        
                        if os.path.exists(arrow_icon_path):
                            down_arrow_icon = QIcon(arrow_icon_path)
                            # 将图标应用于应用程序范围的图标设置
                            app.setProperty("down_arrow_icon", down_arrow_icon)
                            print(f"已通过代码设置下拉箭头图标: {arrow_icon_path}")
                    except Exception as e:
                        print(f"通过代码设置图标时发生错误: {e}")
                else:
                    print(f"Green style file not found: {style_path}")
                    # 回退到现代蓝
                    self._apply_fallback_blue_theme()
            except Exception as e:
                print(f"Error applying modern green style: {e}. Falling back to modern blue theme.")
                self._apply_fallback_blue_theme()
                
        elif theme_name == "现代紫":
            # 使用现代紫色主题
            try:
                # 加载紫色样式表，使用资源路径解析器
                style_path = get_resource_path("purple_style.qss")
                if os.path.exists(style_path):
                    with open(style_path, "r", encoding="utf-8") as f:
                        stylesheet = f.read()
                    
                    # 检查打包环境下的路径并修改URL引用
                    import sys
                    if getattr(sys, 'frozen', False):
                        # 在PyInstaller打包后的环境中
                        print("检测到打包环境，应用相对路径处理...")
                        # 获取资源文件所在的目录
                        base_path = sys._MEIPASS
                        
                        # 修改样式表中的图片URL路径为绝对路径
                        # 这解决了在打包环境中图片路径引用的问题
                        stylesheet = stylesheet.replace('image: url(', f'image: url("{base_path}/')
                        stylesheet = stylesheet.replace('.png)', '.png")')
                        
                        # 同时保持原有的替换逻辑
                        stylesheet = stylesheet.replace("image: url(checkmark.png)", "image: url(checkmark_purple.png)")
                        stylesheet = stylesheet.replace("image: url(down_arrow.png)", "image: url(down_arrow_purple.png)")
                    else:
                        # 在开发环境中
                        stylesheet = stylesheet.replace("image: url(checkmark.png)", "image: url(checkmark_purple.png)")
                        stylesheet = stylesheet.replace("image: url(down_arrow.png)", "image: url(down_arrow_purple.png)")
                    
                    # 确保进度条使用正确的紫色主题颜色
                    progress_color = "#9b59b6"
                    import re
                    stylesheet = re.sub(
                        r'QProgressBar::chunk\s*\{\s*background-color:\s*#[0-9a-fA-F]+',
                        f'QProgressBar::chunk {{ background-color: {progress_color}',
                        stylesheet
                    )
                    
                    app.setStyleSheet(stylesheet)
                    print("Applied modern purple theme.")
                    
                    # 通过编程方式直接设置下拉箭头和单选按钮图标
                    try:
                        from PySide6.QtGui import QIcon, QPixmap
                        arrow_icon_path = get_resource_path("down_arrow_purple.png")
                        radio_icon_path = get_resource_path("radio_checked_purple.png")
                        check_icon_path = get_resource_path("checkmark_purple.png")
                        
                        if os.path.exists(arrow_icon_path):
                            down_arrow_icon = QIcon(arrow_icon_path)
                            # 将图标应用于应用程序范围的图标设置
                            app.setProperty("down_arrow_icon", down_arrow_icon)
                            print(f"已通过代码设置下拉箭头图标: {arrow_icon_path}")
                    except Exception as e:
                        print(f"通过代码设置图标时发生错误: {e}")
                else:
                    print(f"Purple style file not found: {style_path}")
                    # 回退到现代蓝
                    self._apply_fallback_blue_theme()
            except Exception as e:
                print(f"Error applying modern purple style: {e}. Falling back to modern blue theme.")
                self._apply_fallback_blue_theme()
        else:
            # 对于任何未知主题，使用现代蓝
            self._apply_fallback_blue_theme()

    def _apply_fallback_blue_theme(self):
        """在其他主题不可用时应用默认蓝色主题"""
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
                    stylesheet = stylesheet.replace('image: url(', f'image: url("{base_path}/')
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

    # --- ADDED: Slots for handling update check results ---
    @Slot()
    def check_for_updates_slot(self):
        """Initiates the update check process."""
        if self.is_busy:
            QMessageBox.warning(self, "忙碌中", "请等待当前操作完成。")
            return
        
        # Show immediate feedback that check is starting
        self.statusBar().showMessage("正在检查更新...", 0) 
        self.set_busy_state(True) # Prevent other actions during check
        
        # Trigger the worker
        # Pass current version and URL from constants
        self.startUpdateCheckSignal.emit(CURRENT_VERSION, UPDATE_INFO_URL)

    @Slot(dict)
    def show_update_available_dialog_slot(self, update_info):
        """Displays a dialog indicating an update is available."""
        self.set_busy_state(False) # Reset busy state
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
        self.set_busy_state(False) # Reset busy state
        self.statusBar().showMessage("已是最新版本", 3000)
        QMessageBox.information(self, "检查更新", "您当前使用的是最新版本。")

    @Slot(str)
    def show_update_check_failed_dialog_slot(self, error_message):
        """Displays a dialog indicating the update check failed."""
        self.set_busy_state(False) # Reset busy state
        self.statusBar().showMessage("检查更新失败", 3000)
        QMessageBox.warning(self, "检查更新失败", f"无法完成更新检查：\n{error_message}")
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
        """显示或创建并显示跳过索引文件的对话框 (复用实例)"""
        # 检查实例是否存在，如果不存在则创建
        if self.skipped_files_dialog is None:
            print("DEBUG: Creating new SkippedFilesDialog instance.")
            self.skipped_files_dialog = SkippedFilesDialog(self)
            # 当对话框关闭时（例如通过点击关闭按钮），将其引用设为None，以便下次重新创建
            # 注意：这里使用 finished 信号可能不完全可靠，因为对话框可能只是隐藏而不是销毁
            # 一个更稳妥的方式可能是在 closeEvent 中发出信号，或者在这里每次都重新加载数据
            # self.skipped_files_dialog.finished.connect(lambda: setattr(self, 'skipped_files_dialog', None))
        
        # 每次显示前都重新加载数据
        print("DEBUG: Reloading data for SkippedFilesDialog before showing.")
        self.skipped_files_dialog._load_skipped_files()
        
        # 显示对话框并将其置于顶层
        self.skipped_files_dialog.show()
        self.skipped_files_dialog.raise_() # 提升到顶层
        self.skipped_files_dialog.activateWindow() # 激活窗口

    # 添加显示许可证对话框的槽函数
    @Slot()
    def show_license_dialog_slot(self):
        """显示许可证管理对话框"""
        dialog = LicenseDialog(self)
        dialog.exec()
        # 许可证状态可能已更改，需要更新 UI
        self._update_feature_availability()

    # 添加初始化许可证管理器和更新功能可用性的方法
    def _init_license_manager(self):
        """初始化许可证管理器"""
        self.license_manager = get_license_manager()
        self._update_feature_availability()

    def _update_feature_availability(self):
        """根据许可证状态更新功能可用性"""
        license_status = self.license_manager.get_license_status()
        
        # 1. 更新文件类型复选框
        # PDF 支持检查
        pdf_available = self.license_manager.is_feature_available(Features.PDF_SUPPORT)
        for checkbox, file_type in self.file_type_checkboxes.items():
            if file_type == 'pdf':
                checkbox.setEnabled(pdf_available)
                if not pdf_available and checkbox.isChecked():
                    checkbox.setChecked(False)
        
        # Markdown 支持检查
        md_available = self.license_manager.is_feature_available(Features.MARKDOWN_SUPPORT)
        for checkbox, file_type in self.file_type_checkboxes.items():
            if file_type == 'md':
                checkbox.setEnabled(md_available)
                if not md_available and checkbox.isChecked():
                    checkbox.setChecked(False)
        
        # 邮件支持检查（EML 和 MSG）
        email_available = self.license_manager.is_feature_available(Features.EMAIL_SUPPORT)
        for checkbox, file_type in self.file_type_checkboxes.items():
            if file_type in ['eml', 'msg']:
                checkbox.setEnabled(email_available)
                if not email_available and checkbox.isChecked():
                    checkbox.setChecked(False)
        
        # 2. 通配符搜索支持检查
        # 我们需要确保通配符搜索逻辑实现时考虑许可证状态
        
        # 3. 无限制源目录检查
        # 这将在 SettingsDialog 类中处理
        
        # 4. 高级主题功能检查
        # 检查当前主题是否是专业版主题，如果是但无权限使用，则切换回蓝色主题
        advanced_themes_available = self.license_manager.is_feature_available(Features.ADVANCED_THEMES)
        current_theme = self.settings.value("ui/theme", "现代蓝")
        advanced_themes = ["现代绿", "现代紫"]
        
        if not advanced_themes_available and current_theme in advanced_themes:
            print(f"专业版主题 {current_theme} 不可用，切换回现代蓝主题")
            self.settings.setValue("ui/theme", "现代蓝")
            self.apply_theme("现代蓝")
        
        # 5. 显示许可证状态在状态栏
        if license_status == LicenseStatus.ACTIVE:
            status_msg = "专业版已激活"
            license_info = self.license_manager.get_license_info()
            if license_info.get("days_left") is not None:
                status_msg += f" (剩余 {license_info['days_left']} 天)"
            self.statusBar().showMessage(status_msg, 3000)
        elif license_status == LicenseStatus.EXPIRED:
            self.statusBar().showMessage("专业版许可证已过期，部分功能不可用", 5000)
        else:
            # 免费版无需特别提示
            pass

    def _restore_window_geometry(self):
        """从QSettings恢复窗口几何状态。"""
        geometry = self.settings.value("windowGeometry")
        if geometry:
            self.restoreGeometry(geometry)

    def set_busy_state(self, is_busy):
        """设置UI的忙碌状态，禁用或启用相关控件
        
        Args:
            is_busy (bool): True表示正在执行操作，禁用控件；False表示空闲，启用控件
        """
        self.is_busy = is_busy
        
        # 禁用或启用搜索相关控件
        self.search_button.setEnabled(not is_busy)
        self.clear_search_button.setEnabled(not is_busy)
        self.clear_results_button.setEnabled(not is_busy)
        self.search_combo.setEnabled(not is_busy)
        
        # 禁用或启用索引相关控件
        self.index_button.setEnabled(not is_busy)
        self.view_skipped_button.setEnabled(not is_busy)
        
        # 禁用或启用过滤器控件
        for checkbox in self.file_type_checkboxes:
            checkbox.setEnabled(not is_busy)
        
        # 如果状态为空闲，隐藏进度条和阶段标签
        if not is_busy:
            self.progress_bar.setVisible(False)
            self.phase_label.setVisible(False)
            self.detail_label.setVisible(False)
        
        # 更新光标
        if is_busy:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()

    def _open_path_with_desktop_services(self, path, is_file=True):
        """使用系统默认程序打开文件或文件夹
        
        Args:
            path (str): 文件或文件夹的路径
            is_file (bool): 是否是文件，如果为False则表示是文件夹
        """
        try:
            # 确保路径是绝对路径
            abs_path = os.path.abspath(path)
            print(f"尝试打开{'文件' if is_file else '文件夹'}: {abs_path}")
            
            # 处理URL编码
            # 在Windows系统上，需要特别处理路径中的特殊字符
            url = QUrl.fromLocalFile(abs_path)
            
            # 使用系统默认程序打开
            result = QDesktopServices.openUrl(url)
            
            if not result:
                print(f"打开{'文件' if is_file else '文件夹'}失败: {abs_path}")
                QMessageBox.warning(
                    self, 
                    "打开失败", 
                    f"无法打开{'文件' if is_file else '文件夹'}: {abs_path}\n\n可能是路径不存在或没有关联的应用程序。"
                )
        except Exception as e:
            print(f"打开{'文件' if is_file else '文件夹'}时出错: {e}")
            QMessageBox.warning(
                self, 
                "打开错误", 
                f"打开{'文件' if is_file else '文件夹'}时发生错误: {abs_path}\n\n错误: {e}"
            )

# --- Skipped Files Dialog Class --- (NEW)
class SkippedFilesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("跳过索引的文件列表")
        self.setMinimumSize(800, 500)
        # --- 设置窗口标志，包括关闭按钮 ---
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
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
            
        # 在初始化时加载一次数据
        self._load_skipped_files()
            
    def _create_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建过滤控件
        filter_layout = QHBoxLayout()
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItem("所有文件", "all")
        self.filter_type_combo.addItem("PDF超时文件", "pdf_timeout")
        self.filter_type_combo.addItem("内容过大文件", "content_limit")
        self.filter_type_combo.addItem("加密ZIP文件", "password_zip")
        self.filter_type_combo.addItem("加密RAR文件", "password_rar")
        self.filter_type_combo.addItem("损坏的ZIP文件", "corrupted_zip")
        self.filter_type_combo.addItem("损坏的RAR文件", "corrupted_rar")
        self.filter_type_combo.addItem("许可证限制文件", "license_limit")
        
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
        self.close_button.clicked.connect(self.reject)
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
            print("警告: 索引目录不存在或未配置！请先配置并创建索引。")
            self.skipped_files = []
            self._apply_filter()
            return
            
        # 构建日志文件路径
        log_file_path = os.path.join(index_dir, "index_skipped_files.tsv")
        
        if not os.path.exists(log_file_path):
            print("提示: 未找到跳过文件的记录，可能没有文件被跳过。")
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
                        elif "许可证限制" in reason:
                            reason_type = "license_limit"
                        
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
            
        except Exception as e:
            print(f"加载跳过文件错误: {e}")
            import traceback
            print(traceback.format_exc())
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
        has_selection = len(self.table.selectedItems()) > 0
        self.open_file_button.setEnabled(has_selection)
        self.open_folder_button.setEnabled(has_selection)

# --- 文件夹树视图组件 ---
class FolderTreeWidget(QWidget):
    """提供文件夹树视图，显示搜索结果的源文件夹结构"""
    
    # 定义信号，当用户点击文件夹时触发
    folderSelected = Signal(str)  # 发送所选文件夹路径
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(200)  # 设置最小宽度
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加标题标签
        title_label = QLabel("文件夹结构")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建树视图
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)  # 隐藏表头
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)  # 禁止编辑
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)  # 允许自定义右键菜单
        
        # 创建模型
        self.tree_model = QStandardItemModel()
        self.tree_view.setModel(self.tree_model)
        
        # 添加到布局
        layout.addWidget(self.tree_view)
        
        # 设置连接
        self.tree_view.clicked.connect(self._on_tree_item_clicked)
        
        # 初始化变量
        self.root_item = QStandardItem("搜索结果")
        self.tree_model.appendRow(self.root_item)
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
        self.root_item = QStandardItem("搜索结果")
        self.tree_model.appendRow(self.root_item)
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
                
            self._add_folder_path(folder_path)
        
        # 展开根节点
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
        parent_item = self.root_item
        
        # 检查根目录是否已存在
        root_exists = False
        for i in range(self.root_item.rowCount()):
            child = self.root_item.child(i)
            if child.text() == root_part:
                parent_item = child
                root_exists = True
                break
                
        # 如果根目录不存在，创建它
        if not root_exists:
            root_item = QStandardItem(root_part)
            root_item.setData(root_part)
            self.root_item.appendRow(root_item)
            parent_item = root_item
            self.path_items[root_part] = root_item
            
        # 构建路径的其余部分
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