"""
测试托盘设置对话框功能
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QSettings

from tray_settings import TraySettingsDialog

def test_tray_dialog():
    """测试托盘设置对话框"""
    app = QApplication(sys.argv)
    
    # 设置应用元数据
    QApplication.setOrganizationName("YourOrganizationName")
    QApplication.setApplicationName("DocumentSearchToolPySide")
    
    # 创建对话框
    dialog = TraySettingsDialog()
    
    print(f"托盘设置对话框创建成功")
    print(f"对话框标题: {dialog.windowTitle()}")
    print(f"对话框大小: {dialog.size().width()} x {dialog.size().height()}")
    
    # 检查各种选项的状态
    print(f"显示系统托盘图标: {'选中' if dialog.show_tray_icon_checkbox.isChecked() else '未选中'}")
    print(f"启用托盘通知: {'选中' if dialog.tray_notifications_checkbox.isChecked() else '未选中'}")
    print(f"关闭窗口时最小化到托盘: {'选中' if dialog.close_to_tray_checkbox.isChecked() else '未选中'}")
    print(f"最小化时隐藏到托盘: {'选中' if dialog.minimize_to_tray_checkbox.isChecked() else '未选中'}")
    print(f"启动时最小化到托盘: {'选中' if dialog.start_minimized_checkbox.isChecked() else '未选中'}")
    print(f"显示快速搜索菜单: {'选中' if dialog.show_quick_search_checkbox.isChecked() else '未选中'}")
    print(f"显示最近文件菜单: {'选中' if dialog.show_recent_files_checkbox.isChecked() else '未选中'}")
    print(f"最近文件显示数量: {dialog.recent_files_count_spinbox.value()}")
    print(f"启用托盘动画效果: {'选中' if dialog.tray_animations_checkbox.isChecked() else '未选中'}")
    print(f"启用气泡通知: {'选中' if dialog.balloon_notifications_checkbox.isChecked() else '未选中'}")
    
    # 显示对话框
    dialog.show()
    
    # 设置定时器自动关闭对话框
    QTimer.singleShot(5000, dialog.close)
    
    # 运行应用
    app.exec()

if __name__ == "__main__":
    test_tray_dialog() 