import re

# 要插入的方法代码
method_code = '''
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
'''

# 读取文件内容
with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找合适的插入位置 - 选择在_filter_results_by_folder_slot方法后插入
target_method = 'def _filter_results_by_folder_slot(self, folder_path):'
# 首先找到方法的起始位置
start_pos = content.find(target_method)
if start_pos != -1:
    # 找到方法的结束位置
    # 简单方法：往后搜索遇到的第一个同级方法定义
    next_method_pos = content.find('    def ', start_pos + len(target_method))
    if next_method_pos != -1:
        # 在方法后插入新方法
        new_content = content[:next_method_pos] + method_code + content[next_method_pos:]
        
        # 写回文件
        with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("_update_mode_combo_state_slot方法已成功添加!")
    else:
        print("无法找到_filter_results_by_folder_slot方法后的下一个方法")
else:
    print("无法找到_filter_results_by_folder_slot方法的位置") 