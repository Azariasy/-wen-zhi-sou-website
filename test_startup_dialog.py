"""
测试启动设置对话框功能
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QSettings

from startup_settings import StartupSettingsDialog

def test_startup_dialog():
    """测试启动设置对话框"""
    app = QApplication(sys.argv)
    
    # 设置应用元数据
    QApplication.setOrganizationName("YourOrganizationName")
    QApplication.setApplicationName("DocumentSearchToolPySide")
    
    # 创建对话框
    dialog = StartupSettingsDialog()
    
    print(f"启动设置对话框创建成功")
    print(f"对话框标题: {dialog.windowTitle()}")
    print(f"对话框大小: {dialog.size().width()} x {dialog.size().height()}")
    
    # 检查各种选项的状态
    print(f"开机启动复选框: {'选中' if dialog.auto_start_checkbox.isChecked() else '未选中'}")
    print(f"正常启动选项: {'选中' if dialog.normal_startup_radio.isChecked() else '未选中'} - {dialog.normal_startup_radio.text()}")
    print(f"最小化启动选项: {'选中' if dialog.minimized_startup_radio.isChecked() else '未选中'} - {dialog.minimized_startup_radio.text()}")
    print(f"关闭到托盘选项: {'选中' if dialog.close_to_tray_checkbox.isChecked() else '未选中'} - {dialog.close_to_tray_checkbox.text()}")
    print(f"最小化到托盘选项: {'选中' if dialog.minimize_to_tray_checkbox.isChecked() else '未选中'} - {dialog.minimize_to_tray_checkbox.text()}")
    
    # 显示对话框
    dialog.show()
    
    # 设置定时器自动关闭对话框
    QTimer.singleShot(3000, dialog.close)
    
    # 运行应用
    app.exec()

if __name__ == "__main__":
    test_startup_dialog() 