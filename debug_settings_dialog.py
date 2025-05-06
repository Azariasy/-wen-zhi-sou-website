#!/usr/bin/env python3
"""
调试设置对话框的脚本
用于测试设置对话框是否正常工作
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings

# 导入必要的组件
from search_gui_pyside import SettingsDialog, ORGANIZATION_NAME, APPLICATION_NAME

def main():
    """主函数，创建并显示设置对话框"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息，确保QSettings工作正常
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationName(APPLICATION_NAME)
    
    # 创建设置对话框
    print("正在创建设置对话框实例...")
    
    # 分别测试三种类别的设置对话框
    dialog_types = [
        ("interface", "界面设置"),
        ("search", "搜索设置"),
        ("index", "索引设置"),
        ("all", "所有设置")
    ]
    
    # 只测试界面设置对话框
    category, name = dialog_types[0]
    
    print(f"正在创建 {name} 对话框...")
    dialog = SettingsDialog(None, category_to_show=category)
    
    # 显示对话框
    print(f"正在显示 {name} 对话框...")
    result = dialog.exec()
    
    print(f"{name} 对话框结果: {'接受' if result else '取消'}")
    
    return app.exec()

if __name__ == "__main__":
    main() 