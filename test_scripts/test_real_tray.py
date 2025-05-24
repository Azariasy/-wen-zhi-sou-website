"""
测试托盘功能修复的脚本 - 使用真实搜索历史，简化测试流程
"""

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, QSettings

# 导入托盘功能模块
from tray_app import TrayIcon, parse_arguments
from main_window_tray import TrayMainWindow

def display_settings_info():
    """显示设置信息，不修改现有设置"""
    settings = QSettings("WenZhiSou", "DocumentSearch")
    
    # 读取搜索历史
    print("\n当前搜索历史信息:")
    history_value = settings.value("history/searchQueries", [])
    if history_value:
        print(f"  history/searchQueries: {history_value[:5] if isinstance(history_value, list) else history_value}")
    
    # 检查其他可能的键
    backup_keys = ["unified_search/history", "search/history", "search_history", "recent_searches"]
    for key in backup_keys:
        value = settings.value(key, None)
        if value:
            if isinstance(value, list):
                print(f"  {key}: {value[:5]}...")
            else:
                print(f"  {key}: {value}")

def test_real_tray_fixes():
    """使用真实设置测试托盘修复 - 简化版本"""
    print("开始测试托盘功能修复 (使用真实设置)...")
    
    # 显示当前设置
    display_settings_info()
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # 创建托盘图标（先创建托盘图标，后创建窗口）
    print("\n创建托盘图标...")
    tray_icon = TrayIcon()
    tray_icon.show()
    
    # 创建主窗口
    print("创建支持托盘的主窗口...")
    window = TrayMainWindow()
    
    # 设置主窗口的托盘图标引用
    window.set_tray_icon(tray_icon)
    
    # 连接信号
    tray_icon.show_main_window_signal.connect(lambda: window.showNormal())
    tray_icon.hide_main_window_signal.connect(lambda: window.hide())
    tray_icon.quit_app_signal.connect(lambda: (window.force_close(), app.quit()))
    tray_icon.quick_search_signal.connect(lambda text: print(f"快速搜索: '{text}'"))
    
    # 显示窗口
    window.show()
    
    # 显示确认对话框
    QTimer.singleShot(2000, lambda: (
        QMessageBox.information(window, "测试说明", 
                              "请依次测试以下功能:\n\n"
                              "1. 检查主窗口菜单栏中是否有'托盘设置'项\n"
                              "2. 右键单击托盘图标，查看'最近搜索'菜单中是否显示搜索历史\n\n"
                              "测试完成后，点击托盘菜单的'退出'退出应用。")
    ))
    
    # 运行应用程序
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_real_tray_fixes()) 