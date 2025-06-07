#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复SettingsDialog中的最后一个checkbox.blockSignals错误
"""

import os
import re

def fix_final_settings_error():
    """修复SettingsDialog中的checkbox.blockSignals错误"""
    
    file_path = "search_gui_pyside.py"
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复第一个错误：暂时阻断复选框信号
    old_code1 = '''        # 暂时阻断复选框信号
        for checkbox in self.file_type_checkboxes.values():
            checkbox.blockSignals(True)'''
    
    new_code1 = '''        # 暂时阻断复选框信号
        for checkbox_or_key, value in self.file_type_checkboxes.items():
            # 兼容两种字典结构: {checkbox: type_key} 或 {type_key: checkbox}
            if hasattr(checkbox_or_key, 'blockSignals'):
                # checkbox_or_key 是复选框对象
                checkbox_or_key.blockSignals(True)
            elif isinstance(checkbox_or_key, str) and hasattr(value, 'blockSignals'):
                # checkbox_or_key 是字符串，value 是复选框对象
                value.blockSignals(True)'''
    
    # 修复第二个错误：恢复复选框信号
    old_code2 = '''        # 恢复复选框信号
        for checkbox in self.file_type_checkboxes.values():
            checkbox.blockSignals(False)'''
    
    new_code2 = '''        # 恢复复选框信号
        for checkbox_or_key, value in self.file_type_checkboxes.items():
            # 兼容两种字典结构: {checkbox: type_key} 或 {type_key: checkbox}
            if hasattr(checkbox_or_key, 'blockSignals'):
                # checkbox_or_key 是复选框对象
                checkbox_or_key.blockSignals(False)
            elif isinstance(checkbox_or_key, str) and hasattr(value, 'blockSignals'):
                # checkbox_or_key 是字符串，value 是复选框对象
                value.blockSignals(False)'''
    
    modified = False
    
    if old_code1 in content:
        content = content.replace(old_code1, new_code1)
        modified = True
        print("✅ 成功修复暂时阻断复选框信号的代码")
    
    if old_code2 in content:
        content = content.replace(old_code2, new_code2)
        modified = True
        print("✅ 成功修复恢复复选框信号的代码")
    
    if modified:
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 成功修复SettingsDialog中的blockSignals错误")
        print("📋 修复内容:")
        print("   - 修复了暂时阻断复选框信号的循环")
        print("   - 修复了恢复复选框信号的循环")
        print("   - 添加了兼容两种字典结构的处理逻辑")
        return True
    else:
        print("❌ 未找到需要修复的代码段")
        print("💡 可能代码已经被修改或位置发生变化")
        return False

if __name__ == "__main__":
    print("🔧 开始修复SettingsDialog错误...")
    fix_final_settings_error()
    print("🎯 修复完成！") 