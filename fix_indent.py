#!/usr/bin/env python
# Fix indentation in search_gui_pyside.py

def fix_file():
    with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 检查第1465行的缩进问题
    if len(lines) >= 1465 and lines[1464].strip() == '# 基础版功能' and not lines[1464].startswith('                    '):
        # 修复第1464行和第1465行的缩进
        lines[1464] = '                    # 基础版功能\n'
        lines[1465] = '                    type_filter_layout.addWidget(checkbox)\n'
        print("修复了第1464-1465行的缩进")
    
    # 检查第1513行的缩进问题
    if len(lines) >= 1513 and '# 显示提示对话框' in lines[1512] and not lines[1512].startswith('        '):
        # 修复第1513行的缩进
        lines[1512] = '        # 显示提示对话框\n'
        print("修复了第1513行的缩进")
    
    # Write back the fixed content
    with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("文件修复完成，请检查是否还有其他缩进错误")

if __name__ == "__main__":
    fix_file()
