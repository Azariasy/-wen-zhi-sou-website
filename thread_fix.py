"""
临时脚本，用于修复search_gui_pyside.py中的线程变量名冲突
将所有的self.thread替换为self.worker_thread
"""

import re
import sys
import os
from pathlib import Path

def fix_thread_variable():
    # 文件路径
    file_path = "search_gui_pyside.py"
    
    # 如果文件不存在，报错并退出
    if not os.path.exists(file_path):
        print(f"错误: 文件 {file_path} 不存在")
        return False
    
    # 备份原文件
    backup_path = file_path + ".bak"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 创建备份
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"已创建备份文件: {backup_path}")
        
        # 使用正则表达式替换self.thread为self.worker_thread
        # 注意避免将thread.xxx中的thread误认为是self.thread
        pattern = r'self\.thread\b'
        replacement = 'self.worker_thread'
        modified_content = re.sub(pattern, replacement, content)
        
        # 检查是否有改动
        if content == modified_content:
            print("警告: 未找到匹配的模式进行替换")
            return False
        
        # 写入修改后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f"已成功修改文件: {file_path}")
        
        # 检查是否在__init__中已经有worker_thread的定义
        init_pattern = r'def __init__\([^)]*\):\s*.*?self\.worker_thread\s*='
        init_match = re.search(init_pattern, modified_content, re.DOTALL)
        
        if not init_match:
            print("警告: 未在__init__中找到worker_thread的定义，请手动检查")
        
        return True
        
    except Exception as e:
        print(f"错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_thread_variable()
    if success:
        print("线程变量名修复完成")
    else:
        print("线程变量名修复失败") 