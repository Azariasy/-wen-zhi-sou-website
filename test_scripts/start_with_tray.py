"""
启动带托盘功能的文智搜

此脚本启动带有系统托盘支持的文智搜应用程序。
用户可以通过以下方式启动：
1. 普通启动：python start_with_tray.py
2. 最小化启动：python start_with_tray.py --minimized
"""

import sys
import os
import multiprocessing
from pathlib import Path

# 导入托盘应用程序模块
from main_tray import main

if __name__ == "__main__":
    # 多进程支持
    multiprocessing.freeze_support()
    
    # 启动应用程序
    main() 