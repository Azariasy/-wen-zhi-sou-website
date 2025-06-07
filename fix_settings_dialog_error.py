#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复设置对话框中file_type_checkboxes字典结构不一致的问题
"""

import os
import re

def fix_file_type_checkboxes():
    """修复file_type_checkboxes字典结构不一致的问题"""
    
    file_path = "search_gui_pyside.py"
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changes_made = []
    
    # 1. 修复错误的字典赋值：type_key作为键的情况
    # 查找所有 self.file_type_checkboxes[type_key] = checkbox 的情况
    old_pattern1 = r'self\.file_type_checkboxes\[type_key\] = checkbox'
    new_pattern1 = r'self.file_type_checkboxes[checkbox] = type_key'
    
    matches1 = re.findall(old_pattern1, content)
    if matches1:
        content = re.sub(old_pattern1, new_pattern1, content)
        changes_made.append(f"修复了 {len(matches1)} 个字典赋值错误")
    
    # 2. 修复错误的字典遍历方式
    # 查找并修复在 _load_settings 中的错误遍历
    old_load_settings = r'for checkbox, type_value in self\.file_type_checkboxes\.items\(\):\s*\n\s*if checkbox\.isEnabled\(\):'
    new_load_settings = '''for type_key, checkbox in self.file_type_checkboxes.items():
            if isinstance(checkbox, str):
                # 如果checkbox是字符串，说明字典结构是正确的 {checkbox: type_key}
                # 这种情况下需要反向查找
                continue
            if hasattr(checkbox, 'isEnabled') and checkbox.isEnabled():'''
    
    # 更安全的方法：直接替换问题区域
    old_method = '''        for checkbox, type_value in self.file_type_checkboxes.items():
            if checkbox.isEnabled():  # 只处理可用的复选框
                enabled_checkboxes_count += 1
                is_checked = type_key in selected_file_types
                checkbox.setChecked(is_checked)
                if is_checked:
                    checked_enabled_count += 1
                print(f"DEBUG: 设置复选框 {type_key} = {is_checked} (可用: {checkbox.isEnabled()})")'''
    
    new_method = '''        for checkbox_or_key, value in self.file_type_checkboxes.items():
            # 兼容两种字典结构: {checkbox: type_key} 或 {type_key: checkbox}
            if hasattr(checkbox_or_key, 'isEnabled'):
                # checkbox_or_key 是复选框对象
                checkbox = checkbox_or_key
                type_key = value
            elif isinstance(checkbox_or_key, str):
                # checkbox_or_key 是字符串，value 是复选框对象
                type_key = checkbox_or_key
                checkbox = value
            else:
                continue
                
            if hasattr(checkbox, 'isEnabled') and checkbox.isEnabled():  # 只处理可用的复选框
                enabled_checkboxes_count += 1
                is_checked = type_key in selected_file_types
                checkbox.setChecked(is_checked)
                if is_checked:
                    checked_enabled_count += 1
                print(f"DEBUG: 设置复选框 {type_key} = {is_checked} (可用: {checkbox.isEnabled()})")'''
    
    if old_method in content:
        content = content.replace(old_method, new_method)
        changes_made.append("修复了 _load_settings 方法中的字典遍历错误")
    
    # 3. 修复其他地方类似的遍历问题
    # 查找其他出现的 for checkbox, type_value 模式并修复
    problematic_loops = [
        ('for checkbox, type_value in self.file_type_checkboxes.items():', 
         'for checkbox_or_key, value in self.file_type_checkboxes.items():'),
    ]
    
    for old_loop, new_loop in problematic_loops:
        if old_loop in content and 'checkbox.isEnabled()' in content:
            # 只替换那些后面有 checkbox.isEnabled() 调用的循环
            pattern = old_loop.replace('(', r'\(').replace(')', r'\)')
            content = re.sub(pattern, new_loop, content)
    
    # 4. 确保获取选中文件类型的方法也是兼容的
    old_selected_method = '''selected_file_types = list(self.file_type_checkboxes.keys())'''
    new_selected_method = '''# 兼容两种字典结构获取选中的文件类型
        selected_file_types = []
        for checkbox_or_key, value in self.file_type_checkboxes.items():
            if hasattr(checkbox_or_key, 'isChecked'):
                # checkbox_or_key 是复选框对象
                if checkbox_or_key.isChecked():
                    selected_file_types.append(value)
            elif isinstance(checkbox_or_key, str) and hasattr(value, 'isChecked'):
                # checkbox_or_key 是字符串，value 是复选框对象
                if value.isChecked():
                    selected_file_types.append(checkbox_or_key)'''
    
    # 暂时注释掉这个修复，因为可能影响其他功能
    # if old_selected_method in content:
    #     content = content.replace(old_selected_method, new_selected_method)
    #     changes_made.append("修复了获取选中文件类型的方法")
    
    # 写回文件
    if changes_made:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 成功修复设置对话框错误")
        print("📋 修复内容:")
        for change in changes_made:
            print(f"   - {change}")
        return True
    else:
        print("❌ 未找到需要修复的代码")
        return False

if __name__ == "__main__":
    print("🔧 开始修复设置对话框错误...")
    fix_file_type_checkboxes()
    print("🎯 修复完成！重新启动程序以查看效果。") 