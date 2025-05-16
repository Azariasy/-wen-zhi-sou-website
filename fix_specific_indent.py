#!/usr/bin/env python
# -*- coding: utf-8 -*-

def main():
    # 读取文件内容
    file_path = "search_gui_pyside.py"
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    
    # 查找并修复第3412行附近的缩进问题
    target_line_num = 3412
    for i in range(target_line_num - 10, target_line_num + 10):
        if i < len(lines) and i >= 0:
            # 查找包含 "self._apply_fallback_blue_theme()" 且缩进过多的行
            if "self._apply_fallback_blue_theme()" in lines[i]:
                # 检查前一行是否有 "Error applying modern"
                if i > 0 and "Error applying modern" in lines[i-1]:
                    # 获取前一行的缩进
                    prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                    # 用相同的缩进替换当前行
                    lines[i] = ' ' * prev_indent + lines[i].lstrip()
                    print(f"修复了第{i+1}行的缩进问题")
    
    # 再检查第1527行附近的缩进问题
    target_line_num = 1527
    for i in range(target_line_num - 10, target_line_num + 10):
        if i < len(lines) and i >= 0:
            # 查找包含 "QMessageBox.information" 的行
            if "QMessageBox.information" in lines[i]:
                # 检查前面几行是否有方法定义
                for j in range(max(0, i-10), i):
                    if "def _show_pro_feature_dialog_message" in lines[j]:
                        # 获取方法定义行的缩进
                        method_indent = len(lines[j]) - len(lines[j].lstrip())
                        # 正确的缩进应该是方法缩进 + 4
                        correct_indent = method_indent + 4
                        # 设置正确的缩进
                        lines[i] = ' ' * correct_indent + lines[i].lstrip()
                        print(f"修复了第{i+1}行的缩进问题")
                        break
    
    # 写回文件
    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(lines)
    
    print("缩进修复完成！")

if __name__ == "__main__":
    main() 