#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复启动文智搜.bat的线程错误问题
"""

import os
import re

def fix_tray_startup_error():
    """修复启动批处理文件引用错误问题"""
    
    # 创建一个新的修复版本的启动文件
    new_startup_file = "启动文智搜_修复版.bat"
    old_startup_file = "启动文智搜.bat"
    
    # 读取原始批处理文件
    with open(old_startup_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改批处理文件，使其使用文智搜.py而不是search_gui_pyside.py
    # 找到MAIN_SCRIPT定义行并修改
    new_content = re.sub(
        r'set "MAIN_SCRIPT=%SCRIPT_DIR%search_gui_pyside\.py"',
        'set "MAIN_SCRIPT=%SCRIPT_DIR%文智搜.py"',
        content
    )
    
    # 更新批处理文件的标题
    new_content = re.sub(
        r'echo 文智搜 - 智能文档搜索工具 \(完整版\)',
        'echo 文智搜 - 智能文档搜索工具 (修复版)',
        new_content
    )
    
    # 写入新的批处理文件
    with open(new_startup_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ 成功创建修复版启动脚本: {new_startup_file}")
    print("📋 修复内容:")
    print("   - 将启动脚本改为使用文智搜.py（带有托盘功能的版本）")
    print("   - 文智搜.py中已经包含了thread_finished_slot方法")
    print(f"   - 原始批处理文件 {old_startup_file} 未修改")
    print("   - 请使用新的启动文件来启动应用程序")
    
    return True

if __name__ == "__main__":
    print("🔧 开始修复启动文智搜.bat错误...")
    fix_tray_startup_error()
    print("🎯 修复完成！请使用'启动文智搜_修复版.bat'来启动程序。") 