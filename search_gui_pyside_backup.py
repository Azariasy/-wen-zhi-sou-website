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
import re
import subprocess
import shutil
import math
import codecs
import webbrowser
import requests.adapters  # 添加requests的适配器和重试策略导入
import requests.packages.urllib3.util.retry

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

    @Slot(str, str, object, object, object, object, object, str, bool, str, object)
    def run_search(self, query_str, search_mode, min_size, max_size, start_date, end_date, file_type_filter, index_dir_path, case_sensitive, search_scope, search_dirs):
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
                search_dirs_tuple # Pass the tuple version instead of the list
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
    def _perform_search_with_cache(self, query_str, search_mode, min_size, max_size, start_date_str, end_date_str, file_type_filter_tuple, index_dir_path, case_sensitive, search_scope, search_dirs_tuple):
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
        # 注意：只有当后端实际支持search_dirs参数时才传递
        try:
            import inspect
            backend_params = inspect.signature(document_search.search_index).parameters
            if 'search_dirs' in backend_params:
                # 后端支持search_dirs参数
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
                    search_dirs=search_dirs_list
                )
            else:
                # 后端不支持search_dirs参数
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
            results = document_search.search_index(
                query_str=query_str, 
                index_dir_path=index_dir_path, 
                search_mode=search_mode
            )
        
        # 如果搜索目录不为None但后端不支持，则手动过滤结果
        if search_dirs_list and results:
            try:
                # 创建过滤后的结果列表
                filtered_results = []
                
                # 规范化所选目录路径
                # 确保路径格式一致，以便正确匹配
                normalized_search_dirs = [os.path.normpath(d) for d in search_dirs_list]
                
                # 遍历结果进行过滤
                for result in results:
                    file_path = result.get('file_path', '')
                    if not file_path:
                        continue
                    
                    # 检查文件所在的目录是否在所选目录列表中
                    is_in_selected_dir = False
                    
                    # 处理存档文件内部项目
                    if '::' in file_path:
                        archive_path = file_path.split('::', 1)[0]
                        parent_dir = os.path.dirname(os.path.normpath(archive_path))
                    else:
                        parent_dir = os.path.dirname(os.path.normpath(file_path))
                    
                    # 检查文件的父目录是否在选定的目录列表中或其子目录中
                    for search_dir in normalized_search_dirs:
                        # 检查文件是否在搜索目录中
                        if parent_dir == search_dir:
                            is_in_selected_dir = True
                            break
                            
                        # 检查文件是否在搜索目录的子目录中
                        if os.path.commonpath([parent_dir, search_dir]) == search_dir and parent_dir.startswith(search_dir):
                            is_in_selected_dir = True
                            break
                    
                    # 如果文件在所选目录中，添加到过滤结果
                    if is_in_selected_dir:
                        filtered_results.append(result)
                
                print(f"--- Filtered {len(results)} results to {len(filtered_results)} results based on selected directories ---")
                results = filtered_results
            except Exception as e:
                print(f"Error filtering results by directory: {e}")
                # 如果过滤出错，保留原始结果
                import traceback
                traceback.print_exc()
        
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
        # 保存当前选中的主题
        selected_theme = self.theme_combo.currentText()
        settings.setValue("ui/theme", selected_theme)
        
        # 保存结果字体大小
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
        print(f"Theme: {selected_theme}")
        print(f"Result Font Size: {self.result_font_size_spinbox.value()}")
        print("-----------------------")

        # 立即应用界面设置
        parent_window = self.parent()
        if parent_window:
            # 如果是界面设置或全局设置，立即应用主题和字体大小
            if hasattr(self, 'interface_settings_widget') and \
               self.interface_settings_widget.isVisible():
                print("立即应用主题设置...")
                parent_window.apply_theme(selected_theme)
                parent_window._apply_result_font_size()
                
        # 显示确认消息
        if parent_window and hasattr(parent_window, 'statusBar'):
            parent_window.statusBar().showMessage("设置已应用", 3000) # Show for 3 seconds

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
    startSearchSignal = Signal(str, str, object, object, object, object, object, str, bool, str, object) # Added object for search_dirs
    # --- ADDED: Signal for update check --- 
    startUpdateCheckSignal = Signal(str, str) # current_version, update_url
    # ----------------------------------------

    def __init__(self):
        super().__init__()
        self.setWindowTitle("文智搜 (PySide6)")
        self.setMinimumSize(600, 450) # ADDED: Set a minimum window size

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
        sort_layout = self._create_sort_bar() # Assume helper exists
        main_layout.addLayout(sort_layout)
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
        self.results_text = QTextBrowser() 
        self.results_text.setOpenLinks(False)
        self.results_text.setStyleSheet("border: 1px solid #D0D0D0;")
        
        right_layout.addWidget(right_title)
        right_layout.addWidget(self.results_text)
        
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

        # --- 创建搜索选项 (范围和模式) 使用下拉框 ---
        # 所有搜索选项统一在一个水平布局中
        options_h_layout = QHBoxLayout()
        
        # 范围选择下拉框
        scope_label = QLabel("范围:")
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["全文", "文件名"])
        options_h_layout.addWidget(scope_label)
        options_h_layout.addWidget(self.scope_combo)
        
        # 添加一个小间隔
        options_h_layout.addSpacing(10)
        
        # 模式选择下拉框
        mode_label = QLabel("模式:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["精确", "模糊"])
        options_h_layout.addWidget(mode_label)
        options_h_layout.addWidget(self.mode_combo)
        
        options_h_layout.addStretch(1)
        
        # 将水平布局添加到主布局
        layout.addLayout(options_h_layout)

        # Search Button
        self.search_button = QPushButton("搜索")
        self.search_button.setObjectName("search_button")
        layout.addWidget(self.search_button)
        # Clear Button
        self.clear_search_button = QPushButton("清空输入")
        layout.addWidget(self.clear_search_button)

        # 添加通配符帮助按钮
        wildcard_help_button = QPushButton("?", self)
        wildcard_help_button.setToolTip("通配符搜索帮助")
        wildcard_help_button.setFixedSize(24, 24)  # 确保按钮足够小
        wildcard_help_button.setStyleSheet("QPushButton { font-weight: bold; }")
        wildcard_help_button.clicked.connect(self.show_wildcard_help_dialog)
        
        # 添加到搜索布局中，放在合适位置
        layout.insertWidget(layout.count()-1, wildcard_help_button)

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
        self.pro_file_types = {}  # 用于存储专业版文件类型的映射
        
        type_filter_layout = QHBoxLayout()
        type_filter_label = QLabel("文件类型:")
        type_filter_layout.addWidget(type_filter_label)
        
        # 定义支持的文件类型，包括专业版标记
        supported_types = {
            'pdf': {'display': 'PDF', 'pro_feature': Features.PDF_SUPPORT},
            'docx': {'display': 'Word', 'pro_feature': None},  # 基础版支持
            'txt': {'display': 'Text', 'pro_feature': None},   # 基础版支持
            'xlsx': {'display': 'Excel', 'pro_feature': None}, # 基础版支持
            'pptx': {'display': 'PPT', 'pro_feature': None},   # 基础版支持
            'eml': {'display': 'EML', 'pro_feature': Features.EMAIL_SUPPORT},
            'msg': {'display': 'MSG', 'pro_feature': Features.EMAIL_SUPPORT},
            'html': {'display': 'HTML', 'pro_feature': None},  # 基础版支持
            'rtf': {'display': 'RTF', 'pro_feature': None},    # 基础版支持
            'md': {'display': 'Markdown', 'pro_feature': Features.MARKDOWN_SUPPORT},
        }
        
        # 先添加基础版支持的文件类型
        free_types = []
        pro_types = []
        
        # 将文件类型分为基础版和专业版两组
        for type_key, type_info in supported_types.items():
            if type_info['pro_feature'] is None:
                free_types.append((type_key, type_info))
            else:
                pro_types.append((type_key, type_info))
        
        # 处理函数 - 为了避免代码重复
        def add_checkbox_to_layout(type_key, type_info):
            display_name = type_info['display']
            pro_feature = type_info['pro_feature']
            
            checkbox = QCheckBox(display_name)
            
            # 检查此文件类型是否需要专业版
            is_pro_feature = pro_feature is not None
            feature_available = not is_pro_feature or self.license_manager.is_feature_available(pro_feature)
            
            # 存储复选框和其对应的类型
            self.file_type_checkboxes[checkbox] = type_key
            
            # 如果是专业版功能且未激活，则灰显并存储对应关系
            if is_pro_feature and not feature_available:
                checkbox.setEnabled(False)
                checkbox.setStyleSheet("color: #888888;")  # 灰色文本
                
                # 添加专业版标识
                pro_label = QLabel("专业版")
                pro_label.setStyleSheet("color: #FF6600; font-size: 8pt; font-weight: bold;")
                self.pro_file_types[checkbox] = {
                    'feature': pro_feature,
                    'pro_label': pro_label,
                    'display_name': display_name
                }
                
                # 创建带有专业版标签的布局
                checkbox_layout = QHBoxLayout()
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                checkbox_layout.setSpacing(2)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.addWidget(pro_label)
                type_filter_layout.addLayout(checkbox_layout)
                
                # 为灰显的复选框添加点击事件提示专业版
                checkbox.clicked.connect(self._show_pro_feature_dialog)
            else:
                # 如果是已激活的专业版功能或基础版功能，正常显示
                checkbox.setEnabled(True)
                
                # 如果是专业版功能但已激活，不显示专业版标签
                if is_pro_feature and feature_available:
                    # 专业版功能已激活时，不显示"专业版"标签，直接添加复选框
                    type_filter_layout.addWidget(checkbox)
                else:
                    # 基础版功能
                    type_filter_layout.addWidget(checkbox)
            
            # 连接复选框状态改变信号
            checkbox.stateChanged.connect(self._filter_results_by_type_slot)
        
        # 先添加基础版文件类型
        for type_key, type_info in free_types:
            add_checkbox_to_layout(type_key, type_info)
            
        # 添加专业版分隔符
        if pro_types:
            # 添加垂直分隔线
            separator = QFrame()
            separator.setFrameShape(QFrame.VLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setFixedWidth(1)
            type_filter_layout.addWidget(separator)
            
            # 检查是否所有专业版功能都已激活
            all_pro_features_available = True
            for _, type_info in pro_types:
                feature = type_info['pro_feature']
                if feature is not None and not self.license_manager.is_feature_available(feature):
                    all_pro_features_available = False
                    break
            
            # 只有当有专业版功能未激活时，才显示"专业版"标签
            if not all_pro_features_available:
                pro_section_label = QLabel("专业版:")
                pro_section_label.setStyleSheet("color: #FF6600; font-weight: bold;")
                type_filter_layout.addWidget(pro_section_label)
        
        # 再添加专业版文件类型
        for type_key, type_info in pro_types:
            add_checkbox_to_layout(type_key, type_info)
        
        type_filter_layout.addStretch(1)
        return type_filter_layout
        
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
        QTimer.singleShot(100, lambda: self._sort_and_redisplay_results_slot())
        
        # 强制刷新UI，确保专业版功能的复选框状态正确显示
        QTimer.singleShot(200, self._force_ui_refresh)

    def _create_action_buttons(self):
        """创建操作按钮区域"""
        action_layout = QHBoxLayout()
        
        # 添加说明标签
        index_label = QLabel("索引操作:")
        action_layout.addWidget(index_label)
        
        # 创建索引按钮
        self.index_button = QPushButton("创建索引")
        self.index_button.setObjectName("index_button")
        self.index_button.setToolTip("创建或更新文档索引")
        self.index_button.setMinimumWidth(100)  # 设置最小宽度确保按钮足够宽
        
        # 查看跳过的文件按钮
        self.view_skipped_button = QPushButton("查看跳过文件")
        self.view_skipped_button.setToolTip("查看在创建索引过程中被跳过的文件")
        self.view_skipped_button.setMinimumWidth(120)  # 设置最小宽度确保按钮足够宽
        self.view_skipped_button.setObjectName("index_button")  # 使用相同的objectName来应用相同样式
        
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
                    self.set_busy_state(False)
                    return
                else:
                    # 其他错误显示普通错误对话框
                    QMessageBox.warning(self, "搜索错误", error_msg)
                    # 恢复用户界面状态
                    self.set_busy_state(False)
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
        
        self.original_search_results = backend_results
        self.collapse_states = {}  # Reset collapse states on new search
        
        # 重置文件夹过滤状态
        self.filtered_by_folder = False
        self.current_filter_folder = None
        
        # 检查文件夹树功能是否可用
        folder_tree_available = self.license_manager.is_feature_available(Features.FOLDER_TREE)
        if folder_tree_available:
            # 仅当文件夹树功能可用时构建文件夹树
            self.folder_tree.build_folder_tree_from_results(backend_results)
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
            # 重要修复：必须创建原始结果的副本，而不是直接引用
            filtered_results = self.original_search_results.copy()
        else:
            # 根据所选文件类型过滤原始结果
            print("DEBUG: Filtering original results based on checked types...")  # DEBUG
            filtered_results = []
            for result in self.original_search_results:
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
        
        # 修复：直接调用display_search_results_slot，而不是_sort_and_redisplay_results_slot
        # 避免递归调用
        self.display_search_results_slot(filtered_results)
    
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
        
        try:
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
        except Exception as e:
            print(f"Error during sorting: {e}")
            # 出错时继续使用未排序的结果
        
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
        
        # --- MODIFIED: 将选中的目录传递给后端搜索函数 ---
        # 只有在有选中的目录且不是全部目录时才传递目录参数
        source_dirs = self.settings.value("indexing/sourceDirectories", [], type=list)
        search_dirs_param = selected_dirs if selected_dirs and len(selected_dirs) < len(source_dirs) else None
        
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
                                    search_scope, # Pass search scope
                                    search_dirs_param) # Pass selected directories for filtering
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
        
        # 检查文件夹树功能是否可用
        folder_tree_available = self.license_manager.is_feature_available(Features.FOLDER_TREE)
        if folder_tree_available:
            # 仅当文件夹树功能可用时构建文件夹树
            self.folder_tree.build_folder_tree_from_results(backend_results)
        else:
            # 如果功能不可用，确保文件夹树是空的
            self.folder_tree.clear()
        
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
            # 重要修复：必须创建原始结果的副本，而不是直接引用
            filtered_results = self.original_search_results.copy()
        else:
            # 根据所选文件类型过滤原始结果
            print("DEBUG: Filtering original results based on checked types...")  # DEBUG
            filtered_results = []
            for result in self.original_search_results:
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
        
        # 修复：直接调用display_search_results_slot，而不是_sort_and_redisplay_results_slot
        # 避免递归调用
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
        for widget in [self.search_combo, self.sort_combo]:
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
    def set_busy_state(self, is_busy):
        """设置应用程序忙碌状态，禁用或启用UI控件
        
        Args:
            is_busy: 是否处于忙碌状态
        """
        self.is_busy = is_busy
        
        # 禁用或启用主要操作按钮
        if hasattr(self, 'search_button'):
            self.search_button.setEnabled(not is_busy)
        if hasattr(self, 'index_button'):
            self.index_button.setEnabled(not is_busy)
        if hasattr(self, 'clear_search_button'):
            self.clear_search_button.setEnabled(not is_busy)
        if hasattr(self, 'clear_results_button'):
            self.clear_results_button.setEnabled(not is_busy)
        
        # 显示或隐藏进度条
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(is_busy)


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
            for widget in [self.search_combo, self.scope_combo, self.mode_combo, self.sort_combo]:
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
        # directory = self.dir_entry.text() # REMOVED
        source_dirs = self.settings.value("indexing/sourceDirectories", [], type=list)
        if not source_dirs:
             QMessageBox.warning(self, "未配置源目录", "请先前往 \"设置 -> 索引设置\" 添加需要索引的文件夹。")
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
                return
                
            # 动态导入对话框类
            try:
                from skipped_files_dialog import SkippedFilesDialog
                # 创建跳过文件对话框实例
                self.skipped_files_dialog = SkippedFilesDialog(self)
                self.skipped_files_dialog.show()
            except ImportError as e:
                print(f"无法导入SkippedFilesDialog类: {e}")
                QMessageBox.critical(self, "错误", "无法打开跳过文件对话框，缺少必要的组件。")
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
        
        print(f"全选复选框更新为: {'选中' if all_checked else '未选中'}, 有选择项: {'是' if any_checked else '否'}")# --- Main Execution --- 
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

