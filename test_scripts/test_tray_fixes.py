"""
测试托盘菜单修复的专用脚本
"""

import sys
import os
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, QSettings

# 导入托盘功能模块
from tray_app import TrayIcon, parse_arguments
from main_window_tray import TrayMainWindow

def modify_search_history():
    """修改搜索历史，确保有数据可供测试"""
    print("设置测试用搜索历史...")
    
    # 获取设置对象
    settings = QSettings("WenZhiSou", "DocumentSearch")
    
    # 设置搜索历史
    test_history = ["测试关键词1", "测试关键词2", "Python", "PySide6", "托盘功能测试"]
    
    # 尝试使用不同的键存储，以确保至少有一个会被找到
    settings.setValue("search/history", test_history)
    settings.setValue("unified_search/history", test_history)
    settings.setValue("search_history", test_history)
    settings.sync()
    
    print(f"已设置测试搜索历史: {test_history}")

def test_tray_fixes():
    """测试托盘修复"""
    print("开始测试托盘功能修复...")
    
    # 修改搜索历史
    modify_search_history()
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # 创建主窗口
    print("创建支持托盘的主窗口...")
    window = TrayMainWindow()
    
    # 创建托盘图标
    print("创建托盘图标...")
    tray_icon = TrayIcon(window)
    tray_icon.show()
    
    # 设置主窗口的托盘图标引用
    window.set_tray_icon(tray_icon)
    
    # 连接信号
    tray_icon.show_main_window_signal.connect(lambda: window.showNormal())
    tray_icon.hide_main_window_signal.connect(lambda: window.hide())
    tray_icon.quit_app_signal.connect(lambda: (window.force_close(), app.quit()))
    tray_icon.quick_search_signal.connect(lambda text: print(f"快速搜索: {text}"))
    
    # 显示窗口
    window.show()
    
    # 测试流程
    def test_sequence():
        """测试序列"""
        print("\n===== 测试修复项 =====")
        
        # 测试1: 打开主菜单，查看设置菜单
        QTimer.singleShot(2000, lambda: print("\n1. 请查看主窗口菜单栏是否有'设置'项，并检查其中是否包含'托盘设置'选项"))
        
        # 测试2: 右键托盘图标，查看最近搜索
        QTimer.singleShot(4000, lambda: print("\n2. 请右键点击托盘图标，查看'最近搜索'菜单是否有内容"))
        
        # 测试3: 显示确认对话框
        QTimer.singleShot(10000, lambda: (
            print("\n3. 测试完成，请确认两个问题是否已修复"), 
            QMessageBox.information(window, "测试结果", 
                                   "请确认以下问题是否已解决：\n\n"
                                   "1. 主窗口菜单中是否有'托盘设置'选项\n"
                                   "2. 托盘右键菜单中'最近搜索'是否显示内容\n\n"
                                   "测试完成后，点击托盘菜单的'退出'退出应用。")
        ))
    
    # 启动测试序列
    QTimer.singleShot(1000, test_sequence)
    
    # 运行应用程序
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_tray_fixes()) 