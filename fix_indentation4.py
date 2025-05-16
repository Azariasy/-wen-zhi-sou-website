#!/usr/bin/env python
# -*- coding: utf-8 -*-

def main():
    # 读取文件内容
    file_path = "search_gui_pyside.py"
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    # 修复第1463-1465行附近的缩进错误
    import re
    
    # 修复 _show_pro_feature_dialog_message 方法中的缩进错误
    pattern1 = r'(\s+def _show_pro_feature_dialog_message\(self, type_name\):.*?\n)(\s+)QMessageBox\.information'
    replacement1 = r'\1\2QMessageBox.information'
    content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
    
    # 修复多个地方的 except 缩进问题
    # 1. 修复第3412行附近的 except 后面的代码缩进过多问题
    pattern2 = r'(except Exception as e:.*?\n)(\s+)(self\._apply_fallback_blue_theme\(\))'
    replacement2 = r'\1\2\3'
    content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)
    
    # 检查文件中每一行的缩进，查找明显不正确的缩进
    lines = content.split('\n')
    corrected_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 如果当前行是 except 语句，检查下一行的缩进是否正确
        if re.match(r'\s+except\s+', line):
            # 获取当前行的缩进级别
            current_indent = len(line) - len(line.lstrip())
            
            # 如果有下一行，检查其缩进
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.strip():  # 如果下一行不是空行
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    # 如果下一行缩进明显过多（比如多了8个空格以上），修正它
                    if next_indent > current_indent + 8:
                        # 保持与 except 行相同的缩进加4个空格
                        correct_indent = ' ' * (current_indent + 4)
                        lines[i + 1] = correct_indent + next_line.lstrip()
        
        corrected_lines.append(lines[i])
        i += 1
    
    # 组合为新内容
    corrected_content = '\n'.join(corrected_lines)
    
    # 写回文件
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(corrected_content)
    
    print("所有缩进错误已修复！")

if __name__ == "__main__":
    main() 