"""
托盘功能测试脚本

这个脚本用于测试文智搜的托盘功能，支持以下测试:
1. 系统托盘图标显示
2. 托盘菜单功能
3. 最小化到托盘
4. 启动时最小化到托盘 (--minimized 参数)
5. 托盘设置对话框

使用方法:
python test_tray.py          # 正常启动
python test_tray.py --minimized  # 以最小化模式启动
"""

import sys
from main_tray import main

if __name__ == "__main__":
    print("启动托盘功能测试...")
    print(f"命令行参数: {sys.argv}")
    
    # 如果参数中包含--test-tray-only，只测试托盘功能不加载主窗口（未实现）
    if "--test-tray-only" in sys.argv:
        print("仅测试托盘功能，不加载主窗口")
        # 移除这个标志，避免传递给主程序
        sys.argv.remove("--test-tray-only")
    
    main() 