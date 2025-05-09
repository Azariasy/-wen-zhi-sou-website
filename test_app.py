#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试启动文智搜应用程序并捕获所有异常
"""

import sys
import traceback

def main():
    """主函数，尝试导入并启动应用程序"""
    try:
        print("开始导入模块...")
        # 导入必要的模块
        from PySide6.QtWidgets import QApplication
        print("成功导入 PySide6.QtWidgets")
        
        # 导入应用程序模块
        import search_gui_pyside
        print("成功导入 search_gui_pyside 模块")
        
        # 创建应用程序实例
        print("创建应用程序实例...")
        app = QApplication(sys.argv)
        print("应用程序实例创建成功")
        
        # 设置组织和应用名称（对QSettings很重要）
        QApplication.setOrganizationName(search_gui_pyside.ORGANIZATION_NAME)
        QApplication.setApplicationName(search_gui_pyside.APPLICATION_NAME)
        print("已设置组织和应用名称")
        
        # 创建主窗口
        print("创建主窗口...")
        window = search_gui_pyside.MainWindow()
        print("主窗口创建成功")
        
        # 显示窗口
        print("显示窗口...")
        window.show()
        print("窗口显示成功")
        
        # 启动应用程序事件循环
        print("启动事件循环...")
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"发生错误: {e}")
        print("详细错误信息:")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 