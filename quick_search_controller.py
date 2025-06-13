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
        self.max_results = 50  # 增加轻量级搜索结果数量，与主窗口保持一致
        
        # 当前主题
        self.current_theme = "现代蓝"
        if hasattr(main_window, 'settings'):
            self.current_theme = main_window.settings.value("ui/theme", "现代蓝")
        
        # 搜索结果缓存
        self.search_results_cache = {}
        
        # 结果格式化设置
        self.preview_length = 100  # 预览内容的最大长度
    
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
            # 如果对话框不存在或已关闭，创建新的
            if not self.dialog or not self.dialog.isVisible():
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
    
    def _handle_search_request(self, query):
        """处理搜索请求
        
        Args:
            query: 搜索关键词
        """
        if not query or not self.main_window:
            print("无法执行搜索：查询为空或主窗口未设置")
            return
        
        print(f"轻量级搜索：处理搜索请求 '{query}'")
        
        # 检查是否有缓存结果
        if query in self.search_results_cache:
            print(f"使用缓存的搜索结果：'{query}'")
            self._show_search_results(self.search_results_cache[query])
            return
        
        # 获取主窗口的搜索引擎
        try:
            # 确保主窗口有搜索方法
            if not hasattr(self.main_window, '_perform_search') or \
               not callable(getattr(self.main_window, '_perform_search')):
                print("主窗口没有提供 _perform_search 方法")
                self._show_search_results([])
                return
            
            print(f"调用主窗口的搜索方法：'{query}'")
            
            # 使用主窗口的搜索方法，获取结果
            raw_results = self._execute_search_via_main_window(query)
            
            print(f"获取到原始搜索结果，数量: {len(raw_results) if raw_results else 0}")
            
            # 格式化结果
            formatted_results = self._format_search_results(raw_results)
            
            print(f"格式化后的搜索结果，数量: {len(formatted_results)}")
            
            # 缓存结果
            self.search_results_cache[query] = formatted_results
            
            # 显示结果
            self._show_search_results(formatted_results)
            
        except Exception as e:
            print(f"执行搜索时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            self._show_search_results([])
    
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
            
            # 如果文件名搜索结果很少（<5个），才补充一些全文搜索结果
            if len(filename_results) < 5:
                print("  文件名搜索结果较少，补充部分全文搜索结果...")
                fulltext_results = self.main_window._perform_search(
                    query=query, 
                    max_results=min(15, self.max_results - len(filename_results)),
                    quick_search=True,
                    search_scope="fulltext"
                )
                print(f"  全文搜索补充结果: {len(fulltext_results)} 个")
                
                # 合并结果，文件名搜索结果优先
                combined_results = filename_results.copy()
                existing_paths = {result.get('file_path', '') for result in filename_results}
                
                for result in fulltext_results:
                    file_path = result.get('file_path', '')
                    if file_path and file_path not in existing_paths:
                        combined_results.append(result)
                        existing_paths.add(file_path)
                
                print(f"  合并后结果: {len(combined_results)} 个（文件名优先）")
                return combined_results
            else:
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