#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证修复效果
"""

import subprocess
import sys
import time

def run_test():
    print("=== 文智搜修复效果验证测试 ===\n")
    
    print("🚀 启动应用...")
    try:
        # 运行应用
        process = subprocess.Popen([sys.executable, "search_gui_pyside.py"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.STDOUT, 
                                 universal_newlines=True,
                                 bufsize=1)
        
        print("✅ 应用已启动")
        print("\n📋 测试步骤:")
        print("1. 搜索'十四五'关键词")
        print("2. 测试文件类型筛选:")
        print("   - 点击docx、xlsx、pptx等复选框")
        print("   - 确认结果正确过滤")
        print("3. 测试折叠展开:")
        print("   - 点击[+]/[-]按钮")
        print("   - 确认内容正确展开/折叠")
        print("4. 检查文件名显示:")
        print("   - 确认每个结果都显示文件名")
        print("\n⚠️ 注意: 如果控制台没有大量Qt委托错误，说明修复成功！")
        
        # 等待一段时间让用户测试
        print("\n⏳ 应用运行中，按Ctrl+C停止测试...")
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 用户中断测试")
            process.terminate()
            
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    run_test()
