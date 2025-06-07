#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复剩余的checkbox和type_value变量未定义错误
"""

import os
import re

def fix_remaining_checkbox_errors():
    """修复剩余的checkbox变量未定义错误"""
    
    file_path = "search_gui_pyside.py"
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复_filter_results_by_type_slot方法中剩余的错误
    old_code = '''        checked_types = []
        for checkbox_or_key, value in self.file_type_checkboxes.items():
            # 只添加被选中且可用的文件类型（专业版功能在未激活时为灰色不可选）
            if checkbox.isChecked() and checkbox.isEnabled():
                checked_types.append(type_value)'''
    
    new_code = '''        checked_types = []
        for checkbox_or_key, value in self.file_type_checkboxes.items():
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
                
            # 只添加被选中且可用的文件类型（专业版功能在未激活时为灰色不可选）
            if checkbox.isChecked() and checkbox.isEnabled():
                checked_types.append(type_value)'''
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 成功修复剩余的checkbox和type_value变量未定义错误")
        print("📋 修复内容:")
        print("   - 修复了_filter_results_by_type_slot方法中的剩余变量问题")
        print("   - 添加了兼容两种字典结构的处理逻辑")
        return True
    else:
        print("❌ 未找到需要修复的代码段")
        print("💡 可能代码已经被修改或位置发生变化")
        return False

if __name__ == "__main__":
    print("🔧 开始修复剩余的checkbox错误...")
    fix_remaining_checkbox_errors()
    print("🎯 修复完成！") 