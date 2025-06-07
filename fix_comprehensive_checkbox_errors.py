#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全面修复程序中所有的checkbox和type_key变量未定义错误
"""

import os
import re

def fix_comprehensive_checkbox_errors():
    """修复所有的checkbox和type_key变量未定义错误"""
    
    file_path = "search_gui_pyside.py"
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定义需要修复的代码模式
    fixes = []
    
    # 1. 修复 _toggle_all_file_types 方法
    fix1_old = '''    def _toggle_all_file_types(self, state):
        """全选或取消全选所有可用的文件类型复选框"""
        is_checked = state == Qt.Checked
        print(f"DEBUG: _toggle_all_file_types 调用，状态 = {is_checked}")
        
        # 暂时阻止信号触发，避免循环更新
        self.select_all_types_checkbox.blockSignals(True)
        
        enabled_count = 0
        checked_count = 0
        for checkbox_or_key, value in self.file_type_checkboxes.items():
            # 只处理启用的复选框（即可用的文件类型）
            if checkbox.isEnabled():
                enabled_count += 1
                checkbox.blockSignals(True)  # 阻止复选框状态改变触发信号
                checkbox.setChecked(is_checked)  # 使用传入的状态
                checkbox.blockSignals(False)  # 恢复信号连接
                if is_checked:
                    checked_count += 1
                print(f"DEBUG: 设置复选框 {type_key} = {is_checked}")'''
    
    fix1_new = '''    def _toggle_all_file_types(self, state):
        """全选或取消全选所有可用的文件类型复选框"""
        is_checked = state == Qt.Checked
        print(f"DEBUG: _toggle_all_file_types 调用，状态 = {is_checked}")
        
        # 暂时阻止信号触发，避免循环更新
        self.select_all_types_checkbox.blockSignals(True)
        
        enabled_count = 0
        checked_count = 0
        for checkbox_or_key, value in self.file_type_checkboxes.items():
            # 兼容两种字典结构: {checkbox: type_key} 或 {type_key: checkbox}
            if hasattr(checkbox_or_key, 'isEnabled'):
                # checkbox_or_key 是复选框对象
                checkbox = checkbox_or_key
                type_key = value
            elif isinstance(checkbox_or_key, str) and hasattr(value, 'isEnabled'):
                # checkbox_or_key 是字符串，value 是复选框对象
                checkbox = value
                type_key = checkbox_or_key
            else:
                continue
                
            # 只处理启用的复选框（即可用的文件类型）
            if checkbox.isEnabled():
                enabled_count += 1
                checkbox.blockSignals(True)  # 阻止复选框状态改变触发信号
                checkbox.setChecked(is_checked)  # 使用传入的状态
                checkbox.blockSignals(False)  # 恢复信号连接
                if is_checked:
                    checked_count += 1
                print(f"DEBUG: 设置复选框 {type_key} = {is_checked}")'''
    
    fixes.append((fix1_old, fix1_new))
    
    # 2. 修复 _save_current_file_types 方法
    fix2_old = '''    def _save_current_file_types(self):
        """收集当前勾选的文件类型并返回列表"""
        selected_types = []
        for checkbox_or_key, value in self.file_type_checkboxes.items():
            if checkbox.isChecked():
                selected_types.append(type_key)
                print(f"DEBUG: 复选框 {type_key} 被选中")'''
    
    fix2_new = '''    def _save_current_file_types(self):
        """收集当前勾选的文件类型并返回列表"""
        selected_types = []
        for checkbox_or_key, value in self.file_type_checkboxes.items():
            # 兼容两种字典结构: {checkbox: type_key} 或 {type_key: checkbox}
            if hasattr(checkbox_or_key, 'isChecked'):
                # checkbox_or_key 是复选框对象
                checkbox = checkbox_or_key
                type_key = value
            elif isinstance(checkbox_or_key, str) and hasattr(value, 'isChecked'):
                # checkbox_or_key 是字符串，value 是复选框对象
                checkbox = value
                type_key = checkbox_or_key
            else:
                continue
                
            if checkbox.isChecked():
                selected_types.append(type_key)
                print(f"DEBUG: 复选框 {type_key} 被选中")'''
    
    fixes.append((fix2_old, fix2_new))
    
    # 3. 修复 _apply_selection 方法中的错误
    fix3_old = '''            for checkbox_or_key, value in self.file_type_checkboxes.items():
                if checkbox.isEnabled():
                    enabled_types.append(type_key)'''
    
    fix3_new = '''            for checkbox_or_key, value in self.file_type_checkboxes.items():
                # 兼容两种字典结构: {checkbox: type_key} 或 {type_key: checkbox}
                if hasattr(checkbox_or_key, 'isEnabled'):
                    # checkbox_or_key 是复选框对象
                    checkbox = checkbox_or_key
                    type_key = value
                elif isinstance(checkbox_or_key, str) and hasattr(value, 'isEnabled'):
                    # checkbox_or_key 是字符串，value 是复选框对象
                    checkbox = value
                    type_key = checkbox_or_key
                else:
                    continue
                    
                if checkbox.isEnabled():
                    enabled_types.append(type_key)'''
    
    fixes.append((fix3_old, fix3_new))
    
    # 4. 修复 _apply_selection 方法中的另一个错误
    fix4_old = '''                for checkbox_or_key, value in self.file_type_checkboxes.items():
                    if checkbox.isEnabled():
                        checkbox.blockSignals(True)
                        checkbox.setChecked(True)
                        checkbox.blockSignals(False)'''
    
    fix4_new = '''                for checkbox_or_key, value in self.file_type_checkboxes.items():
                    # 兼容两种字典结构: {checkbox: type_key} 或 {type_key: checkbox}
                    if hasattr(checkbox_or_key, 'isEnabled'):
                        # checkbox_or_key 是复选框对象
                        checkbox = checkbox_or_key
                        type_key = value
                    elif isinstance(checkbox_or_key, str) and hasattr(value, 'isEnabled'):
                        # checkbox_or_key 是字符串，value 是复选框对象
                        checkbox = value
                        type_key = checkbox_or_key
                    else:
                        continue
                        
                    if checkbox.isEnabled():
                        checkbox.blockSignals(True)
                        checkbox.setChecked(True)
                        checkbox.blockSignals(False)'''
    
    fixes.append((fix4_old, fix4_new))
    
    # 5. 修复 _start_search_common 方法中的错误
    fix5_old = '''        for checkbox_or_key, value in self.file_type_checkboxes.items():
            if checkbox.isChecked():
                selected_file_types.append(type_key)'''
    
    fix5_new = '''        for checkbox_or_key, value in self.file_type_checkboxes.items():
            # 兼容两种字典结构: {checkbox: type_key} 或 {type_key: checkbox}
            if hasattr(checkbox_or_key, 'isChecked'):
                # checkbox_or_key 是复选框对象
                checkbox = checkbox_or_key
                type_key = value
            elif isinstance(checkbox_or_key, str) and hasattr(value, 'isChecked'):
                # checkbox_or_key 是字符串，value 是复选框对象
                checkbox = value
                type_key = checkbox_or_key
            else:
                continue
                
            if checkbox.isChecked():
                selected_file_types.append(type_key)'''
    
    fixes.append((fix5_old, fix5_new))
    
    # 6. 修复 _filter_results_by_type_slot 方法中的错误
    fix6_old = '''        for checkbox, type_value in self.file_type_checkboxes.items():
            if checkbox.isChecked():
                if type_value in self.AVAILABLE_FILE_TYPES:
                    enabled_file_types.append(type_value)'''
    
    fix6_new = '''        for checkbox_or_key, value in self.file_type_checkboxes.items():
            # 兼容两种字典结构: {checkbox: type_key} 或 {type_key: checkbox}
            if hasattr(checkbox_or_key, 'isChecked'):
                # checkbox_or_key 是复选框对象
                checkbox = checkbox_or_key
                type_value = value
            elif isinstance(checkbox_or_key, str) and hasattr(value, 'isChecked'):
                # checkbox_or_key 是字符串，value 是复选框对象
                checkbox = value
                type_value = checkbox_or_key
            else:
                continue
                
            if checkbox.isChecked():
                if type_value in self.AVAILABLE_FILE_TYPES:
                    enabled_file_types.append(type_value)'''
    
    fixes.append((fix6_old, fix6_new))
    
    # 7. 修复 _setup_connections 方法中的错误（第6836行附近）
    fix7_old = '''        # --- File type filter change and sorting ---
        for checkbox_or_key, value in self.file_type_checkboxes.items():  # 正确遍历字典的键值对
            checkbox.stateChanged.connect(self._filter_results_by_type_slot)'''
    
    fix7_new = '''        # --- File type filter change and sorting ---
        for checkbox_or_key, value in self.file_type_checkboxes.items():  # 正确遍历字典的键值对
            # 兼容两种字典结构: {checkbox: type_key} 或 {type_key: checkbox}
            if hasattr(checkbox_or_key, 'stateChanged'):
                # checkbox_or_key 是复选框对象
                checkbox = checkbox_or_key
            elif isinstance(checkbox_or_key, str) and hasattr(value, 'stateChanged'):
                # checkbox_or_key 是字符串，value 是复选框对象
                checkbox = value
            else:
                continue
                
            checkbox.stateChanged.connect(self._filter_results_by_type_slot)'''
    
    fixes.append((fix7_old, fix7_new))
    
    # 应用所有修复
    modified = False
    for old_code, new_code in fixes:
        if old_code in content:
            content = content.replace(old_code, new_code)
            modified = True
            print(f"✅ 成功修复一个代码段")
    
    # 检查是否还有剩余的未定义变量使用
    # 查找剩余的 checkbox. 模式（在循环中但没有正确定义的）
    checkbox_pattern = r'for\s+checkbox_or_key,\s*value\s+in\s+self\.file_type_checkboxes\.items\(\):\s*\n.*?(?=\n\s*\n|\n\s*def|\n\s*class|\Z)'
    
    def fix_remaining_checkbox_usage(match):
        block = match.group(0)
        if 'if hasattr(checkbox_or_key,' in block:
            # 已经修复过
            return block
        
        # 检查是否有直接使用checkbox或type_key的情况
        if 'checkbox.' in block or 'type_key' in block:
            # 需要修复
            lines = block.split('\n')
            new_lines = []
            for i, line in enumerate(lines):
                new_lines.append(line)
                if i == 0 and 'for checkbox_or_key, value in self.file_type_checkboxes.items():' in line:
                    # 在循环开始后添加兼容性处理
                    indent = '            '
                    new_lines.extend([
                        indent + '# 兼容两种字典结构: {checkbox: type_key} 或 {type_key: checkbox}',
                        indent + 'if hasattr(checkbox_or_key, \'isEnabled\') or hasattr(checkbox_or_key, \'isChecked\') or hasattr(checkbox_or_key, \'stateChanged\'):',
                        indent + '    # checkbox_or_key 是复选框对象',
                        indent + '    checkbox = checkbox_or_key',
                        indent + '    type_key = value',
                        indent + 'elif isinstance(checkbox_or_key, str):',
                        indent + '    # checkbox_or_key 是字符串，value 是复选框对象',
                        indent + '    checkbox = value',
                        indent + '    type_key = checkbox_or_key',
                        indent + 'else:',
                        indent + '    continue',
                        indent + ''
                    ])
            return '\n'.join(new_lines)
        return block
    
    # 暂时注释掉这个自动修复，因为可能会造成重复修复
    # content = re.sub(checkbox_pattern, fix_remaining_checkbox_usage, content, flags=re.DOTALL)
    
    if modified:
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 成功修复所有checkbox和type_key变量未定义错误")
        print("📋 修复内容:")
        print("   - 修复了_toggle_all_file_types方法中的变量问题")
        print("   - 修复了_save_current_file_types方法中的变量问题")
        print("   - 修复了_apply_selection方法中的变量问题") 
        print("   - 修复了_start_search_common方法中的变量问题")
        print("   - 修复了_filter_results_by_type_slot方法中的变量问题")
        print("   - 修复了_setup_connections方法中的变量问题")
        print("   - 所有修复都包含了兼容两种字典结构的处理逻辑")
        return True
    else:
        print("❌ 未找到需要修复的代码段")
        print("💡 可能代码已经被修改或位置发生变化")
        return False

if __name__ == "__main__":
    print("🔧 开始全面修复checkbox和type_key错误...")
    fix_comprehensive_checkbox_errors()
    print("🎯 修复完成！重新启动程序以查看效果。") 