"""
详细调试轻量级搜索对话框

用于追踪所有信号触发和事件处理
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from quick_search_dialog import QuickSearchDialog

class DebugQuickSearchDialog(QuickSearchDialog):
    """带调试功能的轻量级搜索对话框"""
    
    def __init__(self, parent=None):
        print("[调试] 创建轻量级搜索对话框")
        super().__init__(parent)
    
    def _connect_signals(self):
        """连接信号和槽 - 调试版本"""
        print("[调试] 连接信号...")
        
        # 关闭按钮
        self.close_button.clicked.connect(self.close)
        print("[调试] 已连接关闭按钮信号")
        
        # 搜索框回车
        self.search_line_edit.returnPressed.connect(self._on_search)
        print("[调试] 已连接搜索框回车信号")
        
        # 结果列表双击
        self.results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        print("[调试] 已连接结果列表双击信号")
        
        # 结果列表回车
        self.results_list.itemActivated.connect(self._on_item_activated)
        print("[调试] 已连接结果列表激活信号")
        
        # 在主窗口打开按钮
        self.main_window_button.clicked.connect(self._on_main_window_button)
        print("[调试] 已连接主窗口打开按钮信号")
    
    def _on_search(self):
        """处理搜索请求 - 调试版本"""
        print("[调试] _on_search 被调用")
        search_text = self.search_line_edit.text().strip()
        print(f"[调试] 搜索文本: '{search_text}'")
        
        if not search_text:
            print("[调试] 搜索文本为空，返回")
            return
        
        # 清空结果列表
        self.results_list.clear()
        print("[调试] 已清空结果列表")
        
        # 更新状态
        self.status_label.setText("正在搜索...")
        print("[调试] 已更新状态标签")
        
        # 打印调试信息
        print(f"轻量级搜索对话框: 触发搜索请求 '{search_text}'")
        
        # 发出搜索信号
        print("[调试] 准备发出搜索信号")
        self.search_executed.emit(search_text)
        print("[调试] 搜索信号已发出")
    
    def _on_main_window_button(self):
        """处理在主窗口中打开按钮 - 调试版本"""
        print("[调试] _on_main_window_button 被调用！！！")
        
        # 打印调用栈
        import traceback
        print("[调试] 调用栈:")
        traceback.print_stack()
        
        search_text = self.search_line_edit.text().strip()
        print(f"[调试] 主窗口按钮 - 搜索文本: '{search_text}'")
        
        if search_text:
            print(f"轻量级搜索对话框: 在主窗口中打开搜索 '{search_text}'")
            self.open_main_window.emit(search_text)
            self.close()
        else:
            print("轻量级搜索对话框: 尝试在主窗口中打开，但搜索文本为空")
    
    def keyPressEvent(self, event):
        """处理键盘事件 - 调试版本"""
        key = event.key()
        print(f"[调试] 键盘事件: {key} (Qt.Key_Return={Qt.Key_Return}, Qt.Key_Enter={Qt.Key_Enter})")
        
        # Escape键关闭窗口
        if key == Qt.Key_Escape:
            print("[调试] 按下Escape键，关闭窗口")
            self.close()
        # 检查是否是回车键
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            print("[调试] 按下回车键")
            # 检查当前焦点
            if self.search_line_edit.hasFocus():
                print("[调试] 搜索框有焦点，应该触发搜索")
            elif self.results_list.hasFocus():
                print("[调试] 结果列表有焦点，应该激活选中项")
            else:
                print("[调试] 其他控件有焦点")
        # 上下键在搜索框和结果列表之间导航
        elif key == Qt.Key_Down and self.search_line_edit.hasFocus():
            print("[调试] 从搜索框向下导航到结果列表")
            # 从搜索框移动到结果列表
            if self.results_list.count() > 0:
                self.results_list.setCurrentRow(0)
                self.results_list.setFocus()
        elif key == Qt.Key_Up and self.results_list.hasFocus() and self.results_list.currentRow() == 0:
            print("[调试] 从结果列表向上导航到搜索框")
            # 从结果列表的第一项移回搜索框
            self.search_line_edit.setFocus()
        else:
            print("[调试] 调用父类键盘事件处理")
            super().keyPressEvent(event)
    
    def set_search_results(self, results):
        """设置搜索结果 - 调试版本"""
        print(f"[调试] set_search_results 被调用，结果数量: {len(results) if results else 0}")
        
        # 清空结果列表
        self.results_list.clear()
        print("[调试] 已清空结果列表")
        
        if not results:
            self.status_label.setText("未找到结果")
            print("[调试] 无搜索结果")
            return
        
        # 添加结果
        for i, result in enumerate(results):
            title = result.get('title', '未知标题')
            path = result.get('path', '')
            preview = result.get('preview', '')
            icon_path = result.get('icon', None)
            
            print(f"[调试] 添加结果 {i+1}: {title}")
            
            from quick_search_dialog import SearchResultItem
            item = SearchResultItem(title, path, icon_path, preview)
            self.results_list.addItem(item)
        
        # 更新状态
        self.status_label.setText(f"找到 {len(results)} 个结果")
        print(f"[调试] 状态更新: 找到 {len(results)} 个结果")
        
        # 选中第一项
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)
            print("[调试] 已选中第一项")


def main():
    app = QApplication(sys.argv)
    
    # 创建调试版本的搜索对话框
    dialog = DebugQuickSearchDialog()
    
    # 连接信号进行监控
    dialog.search_executed.connect(
        lambda text: print(f"[信号] 搜索执行: '{text}'")
    )
    
    dialog.item_activated.connect(
        lambda path: print(f"[信号] 项目激活: '{path}'")
    )
    
    dialog.open_main_window.connect(
        lambda text: print(f"[信号] 主窗口打开请求: '{text}' *** 这不应该自动发生！***")
    )
    
    print("测试说明：")
    print("1. 在搜索框中输入内容并按回车")
    print("2. 观察调试信息，确定何时触发主窗口打开信号")
    print("3. 按ESC关闭窗口")
    print()
    
    # 设置一些测试结果，模拟搜索完成
    def set_test_results(text):
        print(f"[处理器] 处理搜索请求: '{text}'")
        results = [
            {
                'title': f'测试文件_{text}_1.txt',
                'path': f'D:/test_{text}_1.txt',
                'preview': f'这是测试文件1的预览内容，包含关键词"{text}"...'
            },
            {
                'title': f'测试文件_{text}_2.txt',
                'path': f'D:/test_{text}_2.txt',
                'preview': f'这是测试文件2的预览内容，包含关键词"{text}"...'
            }
        ]
        print(f"[处理器] 设置搜索结果，数量: {len(results)}")
        dialog.set_search_results(results)
        print(f"[处理器] 搜索结果设置完成")
    
    # 连接搜索信号到设置结果的函数
    dialog.search_executed.connect(set_test_results)
    
    dialog.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 