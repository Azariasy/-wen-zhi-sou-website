"""
测试设置菜单功能
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings

# 导入主窗口类
from search_gui_pyside import MainWindow

def test_settings_menu():
    """测试设置菜单的各项功能"""
    app = QApplication(sys.argv)
    
    # 设置应用元数据
    QApplication.setOrganizationName("YourOrganizationName")
    QApplication.setApplicationName("DocumentSearchToolPySide")
    
    # 创建主窗口
    window = MainWindow()
    
    # 显示窗口
    window.show()
    
    print("设置菜单测试窗口已打开")
    print("可以通过以下菜单测试各种设置功能:")
    print("- 设置 -> 索引设置")
    print("- 设置 -> 搜索设置") 
    print("- 设置 -> 界面设置")
    print("- 设置 -> 托盘设置")
    print("- 设置 -> 启动设置")
    print("- 设置 -> 热键设置")
    print("- 设置 -> 许可证管理")
    
    # 运行应用
    app.exec()

if __name__ == "__main__":
    test_settings_menu() 