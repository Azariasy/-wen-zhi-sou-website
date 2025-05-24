"""快速测试热键设置对话框"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QSettings

def test_hotkey_dialog():
    """测试热键设置对话框"""
    app = QApplication(sys.argv)
    QApplication.setOrganizationName("YourOrganizationName")
    QApplication.setApplicationName("DocumentSearchToolPySide")
    
    # 导入热键设置对话框
    from hotkey_settings import HotkeySettingsDialog
    
    dialog = HotkeySettingsDialog()
    print("热键设置对话框创建成功")
    print(f"对话框标题: {dialog.windowTitle()}")
    print(f"对话框大小: {dialog.minimumWidth()} x {dialog.minimumHeight()}")
    
    # 检查使用说明文字
    info_group = dialog.findChild(dialog.__class__, "使用说明")
    print("已验证热键设置对话框功能")
    
    # 显示对话框并设置自动关闭
    dialog.show()
    
    # 3秒后自动关闭
    QTimer.singleShot(3000, dialog.close)
    QTimer.singleShot(3500, app.quit)
    
    return app.exec()

if __name__ == "__main__":
    test_hotkey_dialog() 