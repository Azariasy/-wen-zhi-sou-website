#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复所有剩余的for checkbox in self.file_type_checkboxes.values()错误
"""

import os
import re

def fix_all_remaining_errors():
    """修复所有剩余的checkbox.values()循环错误"""
    
    file_path = "search_gui_pyside.py"
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 修复第1633行：计算enabled_count
    old_code1 = '''        enabled_count = 0
        for checkbox in self.file_type_checkboxes.values():
            if checkbox.isEnabled():
                enabled_count += 1'''
    
    new_code1 = '''        enabled_count = 0
        for checkbox_or_key, value in self.file_type_checkboxes.items():
            # 兼容两种字典结构: {checkbox: type_key} 或 {type_key: checkbox}
            if hasattr(checkbox_or_key, 'isEnabled'):
                # checkbox_or_key 是复选框对象
                checkbox = checkbox_or_key
            elif isinstance(checkbox_or_key, str) and hasattr(value, 'isEnabled'):
                # checkbox_or_key 是字符串，value 是复选框对象
                checkbox = value
            else:
                continue
                
            if checkbox.isEnabled():
                enabled_count += 1'''
    
    # 2. 修复第1660行：_update_select_all_checkbox_state中的循环
    old_code2 = '''        enabled_count = 0
        checked_count = 0
        for checkbox in self.file_type_checkboxes.values():
            if checkbox.isEnabled():
                enabled_count += 1
                if checkbox.isChecked():
                    checked_count += 1'''
    
    new_code2 = '''        enabled_count = 0
        checked_count = 0
        for checkbox_or_key, value in self.file_type_checkboxes.items():
            # 兼容两种字典结构: {checkbox: type_key} 或 {type_key: checkbox}
            if hasattr(checkbox_or_key, 'isEnabled'):
                # checkbox_or_key 是复选框对象
                checkbox = checkbox_or_key
            elif isinstance(checkbox_or_key, str) and hasattr(value, 'isEnabled'):
                # checkbox_or_key 是字符串，value 是复选框对象
                checkbox = value
            else:
                continue
                
            if checkbox.isEnabled():
                enabled_count += 1
                if checkbox.isChecked():
                    checked_count += 1'''
    
    modified = False
    
    if old_code1 in content:
        content = content.replace(old_code1, new_code1)
        modified = True
        print("✅ 成功修复第1633行的enabled_count计算")
    
    if old_code2 in content:
        content = content.replace(old_code2, new_code2)
        modified = True
        print("✅ 成功修复第1660行的_update_select_all_checkbox_state循环")
    
    # 再次查找并替换所有剩余的values()模式
    # 使用正则表达式替换所有类似模式
    pattern = r'for\s+checkbox\s+in\s+self\.file_type_checkboxes\.values\(\):'
    replacement = '''for checkbox_or_key, value in self.file_type_checkboxes.items():
            # 兼容两种字典结构: {checkbox: type_key} 或 {type_key: checkbox}
            if hasattr(checkbox_or_key, 'isEnabled') or hasattr(checkbox_or_key, 'isChecked') or hasattr(checkbox_or_key, 'blockSignals'):
                # checkbox_or_key 是复选框对象
                checkbox = checkbox_or_key
            elif isinstance(checkbox_or_key, str):
                # checkbox_or_key 是字符串，value 是复选框对象
                checkbox = value
            else:
                continue
                '''
    
    # 查找所有匹配并进行替换
    matches = re.finditer(pattern, content)
    match_count = 0
    for match in matches:
        match_count += 1
    
    if match_count > 0:
        content = re.sub(pattern, replacement, content)
        modified = True
        print(f"✅ 使用正则表达式修复了 {match_count} 个剩余的values()循环")
    
    if modified:
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 成功修复所有剩余的checkbox.values()错误")
        print("📋 修复内容:")
        print("   - 修复了所有for checkbox in self.file_type_checkboxes.values()模式")
        print("   - 添加了兼容两种字典结构的处理逻辑")
        return True
    else:
        print("❌ 未找到需要修复的代码段")
        print("💡 可能代码已经被修改或位置发生变化")
        return False

if __name__ == "__main__":
    print("🔧 开始修复所有剩余的checkbox.values()错误...")
    fix_all_remaining_errors()
    print("🎯 修复完成！") 