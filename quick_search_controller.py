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
    
    def __init__(self, main_window=None):
        super().__init__(None)
        
        # 持有主窗口的引用（可能是None，延迟设置）
        self.main_window = main_window
        
        # 创建搜索对话框，但不显示
        self.search_dialog = None
        
        # 搜索结果缓存
        self.search_results_cache = {}
        
        # 最大结果数
        self.max_results = 20
        
        # 结果格式化设置
        self.preview_length = 100  # 预览内容的最大长度
    
    def set_main_window(self, main_window):
        """设置主窗口
        
        Args:
            main_window: 主窗口实例
        """
        self.main_window = main_window
    
    def show_quick_search(self, initial_query=None):
        """显示快速搜索对话框
        
        Args:
            initial_query: 初始搜索关键词，可选
        """
        if not self.search_dialog:
            # 懒加载搜索对话框
            self.search_dialog = QuickSearchDialog()
            
            # 连接信号
            self.search_dialog.search_executed.connect(self._handle_search_request)
            self.search_dialog.item_activated.connect(self._handle_item_activation)
            self.search_dialog.open_main_window.connect(self._open_in_main_window)
            self.search_dialog.open_file_signal.connect(self._handle_item_activation)
            self.search_dialog.open_folder_signal.connect(self._handle_folder_open)
        
        # 如果有初始查询，设置到搜索框
        if initial_query:
            self.search_dialog.search_line_edit.setText(initial_query)
            # 使用QTimer延迟执行搜索，使对话框完全显示后再搜索
            QTimer.singleShot(100, self.search_dialog._on_search)
        
        # 显示对话框
        self.search_dialog.show()
        self.search_dialog.activateWindow()
        self.search_dialog.search_line_edit.setFocus()
    
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
        """通过主窗口执行搜索
        
        Args:
            query: 搜索关键词
            
        Returns:
            list: 搜索结果原始数据
        """
        # 这里需要根据主窗口的实际搜索接口来调整
        # 轻量级窗口默认使用文件名搜索，更适合快速浏览
        try:
            # 调用主窗口的搜索方法
            # 注意: 轻量级窗口专门使用文件名搜索模式
            raw_results = self.main_window._perform_search(
                query=query, 
                max_results=self.max_results,
                quick_search=True,  # 标记为快速搜索
                search_scope="filename"  # 轻量级窗口使用文件名搜索
            )
            return raw_results
        except Exception as e:
            print(f"通过主窗口执行搜索失败: {str(e)}")
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
            print("开始格式化搜索结果...")
            print(f"原始结果类型: {type(raw_results)}")
            if raw_results and len(raw_results) > 0:
                # 打印第一个结果的结构，帮助调试
                first_result = raw_results[0]
                print(f"第一个结果的结构: {first_result.keys() if hasattr(first_result, 'keys') else type(first_result)}")
            
            # 根据原始结果的格式，转换为快速搜索需要的格式
            for result in raw_results[:self.max_results]:
                if hasattr(result, 'get'):  # 确认是否是字典类型对象
                    # 尝试从不同的键名获取文件路径
                    file_path = result.get('file_path', result.get('path', ''))
                    file_name = os.path.basename(file_path) if file_path else '未知文件'
                    
                    # 尝试从不同的键名获取内容预览
                    content = result.get('content_preview', result.get('content', result.get('preview', '')))
                    
                    # 截断过长的预览内容
                    if len(content) > self.preview_length:
                        content = content[:self.preview_length] + "..."
                    
                    formatted_result = {
                        'title': file_name,
                        'path': file_path,
                        'preview': content,
                        'icon': None  # 可以通过文件类型获取对应图标
                    }
                    
                    formatted_results.append(formatted_result)
                    print(f"格式化结果: {file_name}")
                else:
                    print(f"跳过不兼容的结果类型: {type(result)}")
                
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
        if self.search_dialog:
            self.search_dialog.set_search_results(results)
    
    def _handle_item_activation(self, path):
        """处理结果项激活（打开文件）
        
        Args:
            path: 要打开的文件路径
        """
        if not path:
            return
        
        try:
            # 如果主窗口有打开文件的方法，调用它
            if self.main_window and hasattr(self.main_window, 'open_file'):
                self.main_window.open_file(path)
            else:
                # 否则使用系统默认程序打开
                os.startfile(path)
        except Exception as e:
            print(f"打开文件失败: {str(e)}")
    
    def _handle_folder_open(self, folder_path):
        """处理打开文件夹请求
        
        Args:
            folder_path: 要打开的文件夹路径
        """
        if not folder_path:
            return
        
        try:
            # 使用系统文件管理器打开文件夹
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['open', folder_path] if sys.platform == 'darwin' else ['xdg-open', folder_path])
            print(f"已打开文件夹: {folder_path}")
        except Exception as e:
            print(f"打开文件夹失败: {str(e)}")
    
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
            
            # 设置搜索范围为文件名搜索（与轻量级搜索保持一致）
            if hasattr(self.main_window, 'scope_combo'):
                # 设置为文件名搜索 (索引1)
                self.main_window.scope_combo.setCurrentIndex(1)
                print(f"设置主窗口搜索范围为文件名搜索")
            else:
                print("未找到主窗口的scope_combo控件")
            
            # 执行搜索
            if hasattr(self.main_window, 'start_search_slot'):
                self.main_window.start_search_slot()


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