"""
测试文智搜托盘功能的完整脚本
"""

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer

# 导入托盘功能模块
from tray_app import TrayIcon, parse_arguments
from main_window_tray import TrayMainWindow

def run_test():
    """运行托盘功能测试"""
    print("开始测试文智搜托盘功能...")
    
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
    print("连接托盘信号...")
    tray_icon.show_main_window_signal.connect(lambda: (print("显示主窗口"), window.showNormal(), window.activateWindow()))
    tray_icon.hide_main_window_signal.connect(lambda: (print("隐藏主窗口"), window.hide()))
    tray_icon.quit_app_signal.connect(lambda: (print("退出应用程序"), window.force_close(), app.quit()))
    tray_icon.quick_search_signal.connect(lambda text: print(f"快速搜索: {text}"))
    
    # 显示窗口
    window.show()
    
    # 测试流程
    def test_sequence():
        """测试序列"""
        print("\n===== 测试1: 托盘基本功能 =====")
        
        # 测试1: 最小化到托盘
        QTimer.singleShot(2000, lambda: (print("\n1. 测试最小化窗口到托盘..."), window.showMinimized()))
        
        # 测试2: 显示窗口
        QTimer.singleShot(4000, lambda: (print("\n2. 测试显示窗口..."), tray_icon.show_main_window_signal.emit()))
        
        # 测试3: 隐藏窗口
        QTimer.singleShot(6000, lambda: (print("\n3. 测试隐藏窗口..."), tray_icon.hide_main_window_signal.emit()))
        
        # 测试4: 再次显示窗口
        QTimer.singleShot(8000, lambda: (print("\n4. 测试再次显示窗口..."), tray_icon.show_main_window_signal.emit()))
        
        # 测试5: 关闭窗口（应最小化到托盘）
        QTimer.singleShot(10000, lambda: (print("\n5. 测试关闭窗口（应最小化到托盘）..."), window.close()))
        
        # 测试6: 显示窗口
        QTimer.singleShot(12000, lambda: (print("\n6. 测试显示窗口..."), tray_icon.show_main_window_signal.emit()))
        
        # 测试7: 显示托盘设置对话框
        QTimer.singleShot(14000, lambda: (print("\n7. 测试显示托盘设置对话框..."), window.show_tray_settings_dialog()))
        
        # 测试8: 完成测试
        QTimer.singleShot(20000, lambda: (
            print("\n8. 测试完成，显示结果..."), 
            QMessageBox.information(window, "测试完成", "托盘功能测试完成！\n\n现在可以手动测试托盘功能。"),
            print("\n测试结束。可以继续手动测试，或者点击托盘菜单中的'退出'来退出应用程序。")
        ))
    
    # 启动测试序列
    QTimer.singleShot(1000, test_sequence)
    
    # 运行应用程序
    return app.exec()

if __name__ == "__main__":
    sys.exit(run_test()) 