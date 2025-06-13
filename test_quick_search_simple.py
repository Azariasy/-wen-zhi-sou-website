#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的快捷搜索测试程序
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_window_tray import TrayMainWindow
from quick_search_controller import QuickSearchController

def test_quick_search():
    """测试快捷搜索功能"""
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = TrayMainWindow()
    
    # 创建快捷搜索控制器
    controller = QuickSearchController(main_window)
    
    # 显示快捷搜索窗口
    controller.show_quick_search()
    
    # 模拟搜索
    if controller.dialog:
        print("快捷搜索窗口已创建")
        
        # 模拟输入搜索词
        controller.dialog.search_line_edit.setText("手册")
        
        # 手动触发搜索
        controller._handle_search_request("手册")
        
        # 等待一下让搜索完成
        QTimer.singleShot(2000, lambda: print("搜索应该已完成"))
        QTimer.singleShot(3000, app.quit)
        
        app.exec()
    else:
        print("快捷搜索窗口创建失败")

if __name__ == "__main__":
    test_quick_search() 