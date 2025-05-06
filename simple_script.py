#!/usr/bin/env python
"""
修复search_gui_pyside.py文件中的语法错误
"""
import os
import re

def fix_syntax_errors():
    # 读取文件
    with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 修复第一个错误：行933-945的缩进问题
    try_found = False
    worker_line = -1
    
    # 寻找worker创建行和try语句
    for i, line in enumerate(lines):
        if "try:" in line and i < 1000:
            try_found = True
        if "self.worker = Worker()" in line and try_found:
            worker_line = i
            break
    
    # 修复worker行的缩进
    if worker_line > 0:
        print(f"修复worker行 {worker_line+1}: {lines[worker_line]}")
        # 确保worker行有正确的缩进
        lines[worker_line] = "            self.worker = Worker()\n"
    
    # 修复第二个错误：SkippedFilesDialog.closeEvent方法的缩进
    for i, line in enumerate(lines):
        if "self.settings.setValue(\"skippedFilesDialog/geometry\"" in line:
            print(f"修复closeEvent行 {i+1}: {lines[i]}")
            # 修复缩进
            lines[i] = "            self.settings.setValue(\"skippedFilesDialog/geometry\", self.saveGeometry())\n"
    
    # 写回文件
    with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("文件修复完成")

if __name__ == "__main__":
    fix_syntax_errors() 