#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复程序启动时的NameError: name 'checkbox' is not defined错误
"""

import os
import re

def fix_startup_error():
    """修复启动时的checkbox变量未定义错误"""
    
    file_path = "search_gui_pyside.py"
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复第6836行的问题
    old_code = '''        # --- File type filter change and sorting ---
        for checkbox_or_key, value in self.file_type_checkboxes.items():  # 正确遍历字典的键值对
            checkbox.stateChanged.connect(self._filter_results_by_type_slot)'''
    
    new_code = '''        # --- File type filter change and sorting ---
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
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 成功修复启动错误")
        print("📋 修复内容:")
        print("   - 修复了第6836行的checkbox变量未定义错误")
        print("   - 添加了兼容两种字典结构的处理逻辑")
        return True
    else:
        print("❌ 未找到需要修复的代码段")
        print("💡 可能代码已经被修改或位置发生变化")
        return False

if __name__ == "__main__":
    print("🔧 开始修复启动错误...")
    fix_startup_error()
    print("🎯 修复完成！重新启动程序以查看效果。") 