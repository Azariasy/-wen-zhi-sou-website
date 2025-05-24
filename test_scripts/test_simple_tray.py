"""
测试简单托盘功能的脚本
"""

import sys
import os
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QTimer

# 导入我们的托盘应用
from simple_tray_app import TrayMainWindow, SimpleTrayIcon

def main():
    """运行基本测试"""
    print("开始测试简单托盘功能...")
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # 创建主窗口和托盘图标
    print("创建主窗口和托盘图标...")
    window = TrayMainWindow()
    tray_icon = SimpleTrayIcon()
    
    # 显示托盘
    print("显示托盘图标...")
    tray_icon.show()
    
    # 连接信号
    print("连接信号...")
    tray_icon.show_window_signal.connect(lambda: print("触发显示窗口信号") or window.showNormal())
    tray_icon.hide_window_signal.connect(lambda: print("触发隐藏窗口信号") or window.hide())
    tray_icon.quit_app_signal.connect(lambda: print("触发退出应用信号") or app.quit())
    
    # 测试流程
    def test_sequence():
        print("\n===== 测试1: 显示/隐藏窗口 =====")
        # 测试显示窗口
        QTimer.singleShot(1000, lambda: (print("显示窗口..."), tray_icon.show_window_signal.emit()))
        
        # 测试隐藏窗口
        QTimer.singleShot(2000, lambda: (print("隐藏窗口..."), tray_icon.hide_window_signal.emit()))
        
        # 测试关闭窗口到托盘
        QTimer.singleShot(3000, lambda: (print("显示窗口..."), window.showNormal()))
        QTimer.singleShot(4000, lambda: (print("关闭窗口（应最小化到托盘）..."), window.close()))
        
        # 测试退出应用
        QTimer.singleShot(5000, lambda: (print("显示窗口..."), window.showNormal()))
        QTimer.singleShot(6000, lambda: (print("测试完成，退出应用..."), tray_icon.quit_app_signal.emit()))
    
    # 启动测试序列
    QTimer.singleShot(500, test_sequence)
    
    # 运行事件循环
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 