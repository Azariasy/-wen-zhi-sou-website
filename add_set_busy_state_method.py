import re

# 要插入的方法代码
method_code = '''
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
'''

# 读取文件内容
with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找合适的插入位置 - 在_force_ui_refresh方法后
target_method = 'def _force_ui_refresh(self):'

start_pos = content.find(target_method)
if start_pos != -1:
    # 找到方法的结束
    end_marker = "        print(\"DEBUG: UI刷新完成\")"
    end_pos = content.find(end_marker, start_pos)
    
    if end_pos != -1:
        # 找到方法结束后的下一行位置
        next_line_pos = content.find('\n', end_pos + len(end_marker))
        
        if next_line_pos != -1:
            # 在方法结束后插入新方法
            new_content = content[:next_line_pos] + method_code + content[next_line_pos:]
            
            # 写回文件
            with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("set_busy_state方法已成功添加!")
        else:
            print("无法找到_force_ui_refresh方法后的下一行")
    else:
        print("无法找到_force_ui_refresh方法的结束标记")
else:
    print("无法找到_force_ui_refresh方法") 