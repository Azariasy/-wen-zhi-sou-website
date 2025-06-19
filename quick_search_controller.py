"""
文智搜轻量级搜索控制器

此模块提供轻量级搜索窗口与主窗口的搜索功能之间的连接和控制逻辑。
包括搜索请求的处理、结果的展示以及与主窗口的交互。
"""

import os
import sys
import subprocess
from PySide6.QtCore import QObject, Signal, Slot, QTimer
from PySide6.QtWidgets import QApplication

from quick_search_dialog import QuickSearchDialog

class QuickSearchController(QObject):
    """轻量级搜索控制器
    
    负责管理轻量级搜索窗口与主窗口的交互，处理搜索请求，显示结果等
    """
    
    # 定义信号
    show_main_window_signal = Signal(str)  # 显示主窗口信号，带有搜索文本参数
    
    def __init__(self, main_window):
        """初始化快速搜索控制器
        
        Args:
            main_window: 主窗口实例
        """
        super().__init__()
        self.main_window = main_window
        self.dialog = None
        self.current_theme = "现代蓝"  # 默认主题
        
        # 快速搜索配置
        self.max_results = 50  # 限制结果数量，提升性能
        self.preview_length = 100  # 预览文本长度
        
        # 搜索结果缓存
        self.search_results_cache = {}
        
        # 智能预测缓存
        self.prediction_cache = {}
        self.search_history = []  # 搜索历史记录
        
        # 防重复调用机制
        self._current_search_query = None  # 当前正在处理的搜索词
        self._search_in_progress = False   # 搜索进行中标志
        
        # 预热缓存 - 同步主窗口的热门搜索
        self._sync_with_main_window_cache()
        
        if hasattr(main_window, 'settings'):
            self.current_theme = main_window.settings.value("ui/theme", "现代蓝")
            # 加载搜索历史
            self._load_search_history()
    
    def _sync_with_main_window_cache(self):
        """同步主窗口的搜索历史和缓存，预热快速搜索
        
        这个方法会：
        1. 获取主窗口的搜索历史
        2. 对于最近的搜索词，尝试从主窗口缓存中获取结果
        3. 预加载到快速搜索缓存中，提升响应速度
        """
        try:
            if not self.main_window or not hasattr(self.main_window, 'settings'):
                return
            
            # 获取主窗口的搜索历史
            search_history = self.main_window.settings.value("search_history", [])
            if not search_history or not isinstance(search_history, list):
                return
            
            print(f"🔄 同步主窗口搜索历史，共 {len(search_history)} 个搜索词")
            
            # 预热最近的5个搜索词
            recent_searches = search_history[:5]
            preloaded_count = 0
            
            for query in recent_searches:
                if not query or not query.strip():
                    continue
                    
                query = query.strip()
                
                # 如果快速搜索缓存中已有，跳过
                if query in self.search_results_cache:
                    continue
                
                # 尝试从主窗口缓存中获取
                if self._try_get_from_main_window_cache_silent(query):
                    preloaded_count += 1
                    print(f"  ✅ 预加载搜索词: '{query}'")
            
            if preloaded_count > 0:
                print(f"🚀 快速搜索缓存预热完成，预加载了 {preloaded_count} 个搜索词")
            
        except Exception as e:
            print(f"同步主窗口缓存时出错: {str(e)}")
    
    def _try_get_from_main_window_cache_silent(self, query):
        """静默尝试从主窗口缓存获取结果（用于预热缓存）
        
        Args:
            query: 搜索关键词
            
        Returns:
            bool: 是否成功获取并缓存结果
        """
        try:
            # 检查主窗口是否有worker和缓存方法
            if not hasattr(self.main_window, 'worker') or not self.main_window.worker:
                return False
            
            worker = self.main_window.worker
            if not hasattr(worker, '_perform_search_with_cache'):
                return False
            
            # 构造缓存键参数
            search_mode = "phrase"
            search_scope = "filename"
            case_sensitive = False
            min_size = None
            max_size = None
            start_date_str = None
            end_date_str = None
            file_type_filter_tuple = None
            
            # 获取索引目录和源目录
            index_dir_path = self.main_window.settings.value("index_directory", "")
            if not index_dir_path:
                return False
            
            source_dirs = self.main_window.settings.value("source_directories", [])
            if isinstance(source_dirs, str):
                source_dirs = [source_dirs]
            search_dirs_tuple = tuple(source_dirs) if source_dirs else None
            
            # 检查缓存状态
            cache_info = worker._perform_search_with_cache.cache_info()
            
            # 尝试获取缓存结果
            cached_results = worker._perform_search_with_cache(
                query, search_mode, min_size, max_size, start_date_str, end_date_str,
                file_type_filter_tuple, index_dir_path, case_sensitive, search_scope, search_dirs_tuple
            )
            
            # 检查是否是缓存命中
            new_cache_info = worker._perform_search_with_cache.cache_info()
            if new_cache_info.hits > cache_info.hits:
                # 缓存命中，格式化并存储到快速搜索缓存
                formatted_results = self._format_search_results(cached_results)
                self.search_results_cache[query] = formatted_results
                return True
            
            return False
            
        except Exception:
            # 静默失败，不打印错误信息
            return False
    
    def update_theme(self, theme_name):
        """更新主题
        
        Args:
            theme_name: 新主题名称
        """
        self.current_theme = theme_name
        
        # 如果对话框已经创建，更新其主题
        if self.dialog and hasattr(self.dialog, 'update_theme'):
            self.dialog.update_theme(theme_name)
    
    def show_quick_search(self, initial_query=None):
        """显示快速搜索对话框
        
        Args:
            initial_query: 初始搜索关键词，可选
        """
        try:
            # 如果对话框不存在，创建新的
            if not self.dialog:
                from quick_search_dialog import QuickSearchDialog
                self.dialog = QuickSearchDialog()
                
                # 设置当前主题
                if hasattr(self.dialog, 'update_theme'):
                    self.dialog.update_theme(self.current_theme)
                
                # 连接信号
                self._connect_dialog_signals()
            
            # 设置初始查询
            if initial_query and hasattr(self.dialog, 'search_line_edit'):
                self.dialog.search_line_edit.setText(initial_query)
                # 触发搜索
                if hasattr(self.dialog, '_perform_search'):
                    self.dialog._perform_search()
            
            # 显示对话框
            self.dialog.show()
            self.dialog.raise_()
            self.dialog.activateWindow()
            
            # 聚焦到搜索框
            if hasattr(self.dialog, 'search_line_edit'):
                self.dialog.search_line_edit.setFocus()
                
        except Exception as e:
            print(f"显示快速搜索对话框时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _connect_dialog_signals(self):
        """连接对话框信号"""
        if not self.dialog:
            return
            
        try:
            # 连接搜索信号
            if hasattr(self.dialog, 'search_executed'):
                self.dialog.search_executed.connect(self._handle_search_request)
            
            # 连接文件操作信号
            if hasattr(self.dialog, 'open_file_signal'):
                self.dialog.open_file_signal.connect(self._handle_open_file)
            
            if hasattr(self.dialog, 'open_folder_signal'):
                self.dialog.open_folder_signal.connect(self._handle_open_folder)
            
            # 连接主窗口打开信号
            if hasattr(self.dialog, 'open_main_window'):
                self.dialog.open_main_window.connect(self._open_in_main_window)
                
        except Exception as e:
            print(f"连接对话框信号时出错: {str(e)}")
    
    def _get_source_directories(self):
        """获取搜索源目录"""
        try:
            # 尝试从主窗口获取源目录配置
            if hasattr(self.main_window, 'settings') and self.main_window.settings:
                # 获取源目录设置
                source_dirs = []
                size = self.main_window.settings.beginReadArray("source_directories")
                for i in range(size):
                    self.main_window.settings.setArrayIndex(i)
                    directory = self.main_window.settings.value("directory", "")
                    if directory and os.path.exists(directory):
                        source_dirs.append(directory)
                self.main_window.settings.endArray()
                
                if source_dirs:
                    print(f"📁 从设置获取源目录: {len(source_dirs)} 个")
                    return source_dirs
            
            # 如果没有配置，使用默认目录
            default_dirs = [
                "D:/OneDrive/person/文件搜索工具/测试文件夹",
                "D:/OneDrive/person/文件搜索工具/新建文件夹",
                "D:/OneDrive/工作/中移（成都）信息通信科技有限公司/内控及风险管理/内控矩阵相关/2025年上半年修订情况"
            ]
            
            # 过滤存在的目录
            existing_dirs = [d for d in default_dirs if os.path.exists(d)]
            if existing_dirs:
                print(f"📁 使用默认源目录: {len(existing_dirs)} 个")
                return existing_dirs
            
            print("❌ 未找到可用的源目录")
            return []
            
        except Exception as e:
            print(f"❌ 获取源目录失败: {str(e)}")
            return []
    
    def _handle_search_request(self, query):
        """处理搜索请求（全面修复版本）"""
        if not query or not query.strip():
            # 清空结果
            if self.dialog and hasattr(self.dialog, 'set_search_results'):
                self.dialog.set_search_results([])
            return
        
        query = query.strip()
        
        # 防重复调用检查 - 增强版本
        if self._search_in_progress:
            if self._current_search_query == query:
                print(f"快捷搜索：跳过重复请求 '{query}'（搜索进行中）")
                return
            else:
                print(f"快捷搜索：取消当前搜索 '{self._current_search_query}'，开始新搜索 '{query}'")
                # 强制重置状态
                self._search_in_progress = False
                self._current_search_query = None
        
        # 设置搜索状态
        self._search_in_progress = True
        self._current_search_query = query
        
        print(f"轻量级搜索：开始处理搜索请求 '{query}'")
        
        try:
            # 🚀 使用新的快速文件名搜索，不依赖主窗口的全文搜索
            print("🚀 启动快速文件名搜索（独立于全文搜索）")
            
            # 先清空当前结果，避免显示旧结果
            if self.dialog and hasattr(self.dialog, 'set_search_results'):
                self.dialog.set_search_results([])
            
            # 获取源目录
            source_dirs = self._get_source_directories()
            if not source_dirs:
                print("❌ 未配置搜索目录，回退到主窗口搜索")
                # 回退到原有逻辑
                main_window_results = self._try_get_from_main_window_cache(query)
                if main_window_results is not None:
                    print(f"✅ 获取主窗口结果：'{query}' ({len(main_window_results)} 个)")
                    if self.dialog and hasattr(self.dialog, 'set_search_results'):
                        self.dialog.set_search_results(main_window_results)
                else:
                    print(f"⚠️ 主窗口无结果：'{query}'")
                    if self.dialog and hasattr(self.dialog, 'set_search_results'):
                        self.dialog.set_search_results([])
                return
            
            # 导入快速文件名搜索模块
            try:
                from quick_filename_search import QuickFilenameSearcher
                
                # 执行快速文件名搜索
                searcher = QuickFilenameSearcher(source_dirs)
                results = searcher.search_filenames(query, max_results=self.max_results)
                
                print(f"✅ 快速文件名搜索完成：'{query}' ({len(results)} 个)")
                
                # 转换结果格式以兼容现有的显示逻辑
                formatted_results = []
                for result in results:
                    formatted_result = {
                        'file_path': result['file_path'],
                        'filename': result['filename'],
                        'directory': result['directory'],
                        'file_size': result['file_size'],
                        'modified_time': result['modified_time'],
                        'file_type': result['file_type'],
                        'content_preview': f"文件名匹配: {result['filename']}",
                        'match_score': result['match_score']
                    }
                    formatted_results.append(formatted_result)
                
                # 确保搜索状态仍然匹配（防止被其他搜索覆盖）
                if self._current_search_query != query:
                    print(f"⚠️ 搜索已被新请求覆盖，跳过结果显示：'{query}' -> '{self._current_search_query}'")
                    return
                
                # 立即更新UI
                if self.dialog and hasattr(self.dialog, 'set_search_results'):
                    self.dialog.set_search_results(formatted_results)
                    
            except ImportError:
                print("❌ 无法导入快速文件名搜索模块，回退到主窗口搜索")
                # 回退到原有逻辑
                main_window_results = self._try_get_from_main_window_cache(query)
                if main_window_results is not None:
                    print(f"✅ 获取主窗口结果：'{query}' ({len(main_window_results)} 个)")
                    if self.dialog and hasattr(self.dialog, 'set_search_results'):
                        self.dialog.set_search_results(main_window_results)
                else:
                    print(f"⚠️ 主窗口无结果：'{query}'")
                    if self.dialog and hasattr(self.dialog, 'set_search_results'):
                        self.dialog.set_search_results([])
            
        except Exception as e:
            print(f"❌ 搜索请求处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            if self.dialog and hasattr(self.dialog, 'set_search_results'):
                self.dialog.set_search_results([])
        finally:
            # 重置搜索状态（只有当前查询匹配时才重置）
            if self._current_search_query == query:
                self._search_in_progress = False
                self._current_search_query = None
                print(f"🔄 搜索状态已重置：'{query}'")
    
    def _execute_search_async(self, query):
        """异步执行搜索（动态等待优化版本）"""
        try:
            # 执行搜索并等待完成
            results = self._execute_new_search(query)
            
            # 缓存结果
            if results:
                self.search_results_cache[query] = results
                print(f"快捷搜索：缓存结果 '{query}' ({len(results)} 个)")
            
            # 显示结果
            if self.dialog and hasattr(self.dialog, 'set_search_results'):
                self.dialog.set_search_results(results)
                
        except Exception as e:
            print(f"异步搜索执行失败: {str(e)}")
            if self.dialog and hasattr(self.dialog, 'set_search_results'):
                self.dialog.set_search_results([])
        finally:
            # 确保重置搜索状态
            self._search_in_progress = False
            self._current_search_query = None
            print(f"快捷搜索：搜索状态已重置")
    
    def _execute_progressive_search(self, query):
        """渐进式搜索：先快速返回部分结果，再补充完整结果"""
        print(f"🚀 开始渐进式搜索：'{query}'")
        
        # 第一阶段：快速搜索（限制结果数量，提升速度）
        print("📊 第一阶段：快速预览搜索...")
        try:
            # 快速搜索：只获取前15个结果
            quick_results = self.main_window._perform_search(
                query=query,
                max_results=15,  # 大幅减少结果数量
                quick_search=True,
                search_scope="filename"
            )
            
            if quick_results:
                print(f"⚡ 快速搜索完成：{len(quick_results)} 个结果")
                # 立即显示快速结果
                if self.dialog and hasattr(self.dialog, 'set_search_results'):
                    # 添加"正在加载更多..."提示
                    enhanced_results = quick_results.copy()
                    enhanced_results.append({
                        'file_path': '正在搜索更多结果...',
                        'content_preview': '⏳ 正在后台搜索完整结果，请稍候...',
                        'is_loading_indicator': True
                    })
                    self.dialog.set_search_results(enhanced_results)
                
                # 第二阶段：完整搜索（异步进行）
                QTimer.singleShot(100, lambda: self._execute_complete_search(query))
            else:
                # 如果快速搜索没有结果，直接进行完整搜索
                self._execute_complete_search(query)
                
        except Exception as e:
            print(f"快速搜索失败，回退到完整搜索: {str(e)}")
            self._execute_complete_search(query)
    
    def _execute_complete_search(self, query):
        """执行完整搜索"""
        print("📚 第二阶段：完整搜索...")
        try:
            # 完整搜索：获取所有结果
            complete_results = self.main_window._perform_search(
                query=query,
                max_results=self.max_results,  # 使用原始限制
                quick_search=True,
                search_scope="filename"
            )
            
            print(f"✅ 完整搜索完成：{len(complete_results)} 个结果")
            
            # 缓存完整结果
            if complete_results:
                self.search_results_cache[query] = complete_results
                # 限制缓存大小
                if len(self.search_results_cache) > 50:
                    oldest_key = next(iter(self.search_results_cache))
                    del self.search_results_cache[oldest_key]
            
            # 更新UI显示完整结果
            if self.dialog and hasattr(self.dialog, 'set_search_results'):
                self.dialog.set_search_results(complete_results)
                
        except Exception as e:
            print(f"完整搜索执行失败: {str(e)}")
            if self.dialog and hasattr(self.dialog, 'set_search_results'):
                self.dialog.set_search_results([])
    
    def _try_get_from_main_window_cache(self, query):
        """尝试从主窗口获取搜索结果（修复版本）"""
        if not self.main_window or not hasattr(self.main_window, '_perform_search'):
            return None
        
        try:
            print(f"快捷搜索：为'{query}'清除主窗口缓存，确保结果正确")
            
            # 执行搜索，获取新鲜的结果
            results = self.main_window._perform_search(
                query=query,
                max_results=self.max_results,
                quick_search=True,
                search_scope="filename"
            )
            
            # 确保结果是列表格式
            if results is None:
                results = []
            elif not isinstance(results, list):
                print(f"⚠️ 主窗口返回的结果不是列表格式: {type(results)}")
                results = []
            
            print(f"✅ 获取主窗口结果：'{query}' ({len(results)} 个)")
            return results
                
        except Exception as e:
            print(f"❌ 主窗口搜索失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _execute_new_search(self, query):
        """执行新的搜索操作（简化版本）
        
        Args:
            query: 搜索关键词
            
        Returns:
            list: 格式化后的搜索结果
        """
        try:
            # 确保主窗口有搜索方法
            if not hasattr(self.main_window, '_perform_search') or \
               not callable(getattr(self.main_window, '_perform_search')):
                print("主窗口没有提供 _perform_search 方法")
                return []
            
            print(f"🔍 执行新搜索：'{query}'")
            
            # 直接调用主窗口搜索，使用动态等待机制
            raw_results = self.main_window._perform_search(
                query=query,
                max_results=self.max_results,
                quick_search=True,
                search_scope="filename"
            )
            
            print(f"获取到原始搜索结果，数量: {len(raw_results) if raw_results else 0}")
            
            # 格式化结果
            formatted_results = self._format_search_results(raw_results)
            
            print(f"格式化后的搜索结果，数量: {len(formatted_results)}")
            
            return formatted_results
            
        except Exception as e:
            print(f"执行新搜索时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _execute_search_via_main_window(self, query):
        """通过主窗口执行搜索 - 专注于文件名搜索
        
        Args:
            query: 搜索关键词
            
        Returns:
            list: 搜索结果原始数据
        """
        try:
            print(f"快捷搜索：开始执行文件名搜索 '{query}'")
            
            # 专注于文件名搜索 - 这是快捷搜索的主要用途
            print("  执行文件名搜索...")
            filename_results = self.main_window._perform_search(
                query=query, 
                max_results=self.max_results,
                quick_search=True,
                search_scope="filename"
            )
            print(f"  文件名搜索结果: {len(filename_results)} 个")
            
            # 快速搜索只返回文件名搜索结果，不补充全文搜索
            # 这确保了快速搜索的纯粹性 - 只搜索文件名
            return filename_results
                
        except Exception as e:
            print(f"通过主窗口执行搜索失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _format_search_results(self, raw_results):
        """格式化搜索结果为快速搜索对话框需要的格式
        
        Args:
            raw_results: 原始搜索结果数据
            
        Returns:
            list: 格式化后的搜索结果
        """
        formatted_results = []
        
        if not raw_results:
            print("没有原始搜索结果可以格式化")
            return formatted_results
            
        try:
            import os
            print("开始格式化搜索结果...")
            print(f"原始结果类型: {type(raw_results)}")
            if raw_results and len(raw_results) > 0:
                # 打印第一个结果的结构，帮助调试
                first_result = raw_results[0]
                print(f"第一个结果的结构: {first_result.keys() if hasattr(first_result, 'keys') else type(first_result)}")
            
            # 根据原始结果的格式，转换为快速搜索需要的格式
            for result in raw_results[:self.max_results]:
                try:
                    # 处理不同的结果格式
                    if hasattr(result, 'get'):  # 字典类型
                        file_path = result.get('file_path', result.get('path', ''))
                        content = result.get('content_preview', result.get('content', result.get('preview', '')))
                    elif hasattr(result, '__getitem__'):  # 列表或元组类型
                        if len(result) >= 2:
                            file_path = result[0] if result[0] else ''
                            content = result[1] if len(result) > 1 and result[1] else ''
                        else:
                            file_path = str(result[0]) if result else ''
                            content = ''
                    else:
                        # 如果是字符串，假设是文件路径
                        file_path = str(result)
                        content = ''
                    
                    # 确保文件路径有效
                    if not file_path:
                        continue
                        
                    # 获取文件名
                    file_name = os.path.basename(file_path) if file_path else '未知文件'
                    
                    # 截断过长的预览内容
                    if content and len(content) > self.preview_length:
                        content = content[:self.preview_length] + "..."
                    
                    # 创建格式化结果，使用快捷搜索对话框期望的格式
                    formatted_result = {
                        'file_path': file_path,  # 使用 file_path 键名
                        'content_preview': content or f"文件: {file_name}"  # 使用 content_preview 键名
                    }
                    
                    formatted_results.append(formatted_result)
                    print(f"格式化结果: {file_name} -> {file_path}")
                    
                except Exception as e:
                    print(f"处理单个结果时出错: {str(e)}, 结果: {result}")
                    continue
                
        except Exception as e:
            print(f"格式化搜索结果失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return formatted_results
    
    def _show_search_results(self, results):
        """在快速搜索对话框中显示格式化的搜索结果
        
        Args:
            results: 格式化后的搜索结果
        """
        if self.dialog:
            self.dialog.set_search_results(results)
    
    def _handle_open_file(self, file_path):
        """处理打开文件请求"""
        try:
            if self.main_window and hasattr(self.main_window, 'open_file'):
                self.main_window.open_file(file_path)
        except Exception as e:
            print(f"打开文件时出错: {str(e)}")
    
    def _handle_open_folder(self, file_path):
        """处理打开文件夹请求"""
        try:
            import os
            folder_path = os.path.dirname(file_path)
            if self.main_window and hasattr(self.main_window, 'open_file'):
                self.main_window.open_file(folder_path)
        except Exception as e:
            print(f"打开文件夹时出错: {str(e)}")
    
    def _open_in_main_window(self, query):
        """在主窗口中打开搜索
        
        Args:
            query: 搜索关键词
        """
        # 发出信号
        self.show_main_window_signal.emit(query)
        
        # 如果有直接访问主窗口的权限，也可以直接调用
        if self.main_window:
            # 显示主窗口
            self.main_window.showNormal()
            self.main_window.activateWindow()
            
            # 设置搜索内容
            if hasattr(self.main_window, 'search_line_edit'):
                self.main_window.search_line_edit.setText(query)
            
            # 设置搜索范围为文件名搜索（与快捷搜索保持一致）
            # 注意：这里需要根据实际的主窗口界面来确定正确的索引
            if hasattr(self.main_window, 'scope_combo'):
                # 查看当前的搜索范围选项
                scope_count = self.main_window.scope_combo.count()
                print(f"主窗口搜索范围选项数量: {scope_count}")
                
                # 打印所有选项以便调试
                for i in range(scope_count):
                    option_text = self.main_window.scope_combo.itemText(i)
                    print(f"  索引 {i}: {option_text}")
                
                # 寻找文件名搜索选项（通常包含"文件名"关键词）
                filename_index = -1
                for i in range(scope_count):
                    option_text = self.main_window.scope_combo.itemText(i).lower()
                    if "文件名" in option_text or "filename" in option_text:
                        filename_index = i
                        break
                
                if filename_index >= 0:
                    self.main_window.scope_combo.setCurrentIndex(filename_index)
                    print(f"设置主窗口搜索范围为文件名搜索 (索引: {filename_index})")
                else:
                    # 如果找不到明确的文件名搜索选项，默认使用索引1
                    if scope_count > 1:
                        self.main_window.scope_combo.setCurrentIndex(1)
                        print(f"未找到文件名搜索选项，使用默认索引1")
                    else:
                        print(f"搜索范围选项不足，保持当前设置")
            else:
                print("未找到主窗口的scope_combo控件")
            
            # 执行搜索
            if hasattr(self.main_window, 'start_search_slot'):
                self.main_window.start_search_slot()
                print(f"已在主窗口中执行搜索: {query}")
            else:
                print("未找到主窗口的start_search_slot方法")

    def _load_search_history(self):
        """加载搜索历史记录"""
        try:
            if hasattr(self.main_window, 'settings'):
                history = self.main_window.settings.value("search_history", [])
                if isinstance(history, list):
                    self.search_history = history[:20]  # 保留最近20个搜索
                    print(f"加载搜索历史: {len(self.search_history)} 个记录")
        except Exception as e:
            print(f"加载搜索历史失败: {str(e)}")
            self.search_history = []
    
    def _predict_search_intent(self, partial_query):
        """基于部分输入预测搜索意图"""
        if len(partial_query) < 2:
            return []
        
        # 从搜索历史中找到匹配的项目
        predictions = []
        for history_item in self.search_history:
            if partial_query.lower() in history_item.lower():
                predictions.append(history_item)
        
        # 限制预测数量
        return predictions[:5]
    
    def _preload_predicted_searches(self, partial_query):
        """预加载预测的搜索结果"""
        predictions = self._predict_search_intent(partial_query)
        
        for predicted_query in predictions:
            if predicted_query not in self.search_results_cache:
                # 异步预加载
                QTimer.singleShot(50, lambda q=predicted_query: self._preload_search_async(q))
    
    def _preload_search_async(self, query):
        """异步预加载搜索结果"""
        try:
            if query not in self.search_results_cache:
                print(f"🔮 预加载搜索: '{query}'")
                results = self.main_window._perform_search(
                    query=query,
                    max_results=15,
                    quick_search=True,
                    search_scope="filename"
                )
                if results:
                    self.search_results_cache[query] = results
                    print(f"✅ 预加载完成: '{query}' -> {len(results)} 个结果")
        except Exception as e:
            print(f"预加载搜索失败: {str(e)}")


# 简单测试代码
if __name__ == "__main__":
    # 这只是一个演示，通常不会直接运行此文件
    
    class MockMainWindow:
        """模拟主窗口类，用于测试"""
        
        def __init__(self):
            self.search_line_edit = type('obj', (object,), {'setText': lambda s: None})
        
        def showNormal(self):
            print("显示主窗口")
        
        def activateWindow(self):
            print("激活主窗口")
        
        def start_search_slot(self):
            print("在主窗口中执行搜索")
        
        def _perform_search(self, query, max_results=20, quick_search=False, search_scope="filename"):
            """模拟搜索方法"""
            print(f"执行搜索: {query}，最大结果数: {max_results}，快速搜索: {quick_search}，搜索范围: {search_scope}")
            
            # 返回一些模拟结果
            return [
                {
                    'file_path': f'D:/文档/测试文档{i}.txt',
                    'content_preview': f'这是包含"{query}"关键词的示例内容...' * 3
                }
                for i in range(1, 6)
            ]
        
        def open_file(self, path):
            """模拟打开文件方法"""
            print(f"打开文件: {path}")
    
    app = QApplication([])
    
    # 创建模拟主窗口
    mock_window = MockMainWindow()
    
    # 创建控制器
    controller = QuickSearchController(mock_window)
    
    # 显示快速搜索窗口
    controller.show_quick_search("测试关键词")
    
    sys.exit(app.exec()) 