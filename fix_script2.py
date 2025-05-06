#!/usr/bin/env python
"""
修复search_gui_pyside.py文件中对apply_theme()方法的调用
"""
import re

def fix_file():
    # 打开文件
    with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复对apply_theme()的调用，添加默认主题参数
    content = content.replace('self.apply_theme()', 'self.apply_theme(self.settings.value("ui/theme", "系统默认"))')
    
    # 保存修改后的内容
    with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("修复apply_theme调用完成！")

if __name__ == "__main__":
    fix_file() 