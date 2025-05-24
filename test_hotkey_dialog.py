"""
测试热键设置对话框功能
"""

import sys
from PySide6.QtWidgets import QApplication, QCheckBox
from PySide6.QtCore import QTimer, QSettings

from hotkey_settings import HotkeySettingsDialog

def test_hotkey_dialog():
    """测试热键设置对话框"""
    app = QApplication(sys.argv)
    
    # 设置应用元数据
    QApplication.setOrganizationName("YourOrganizationName")
    QApplication.setApplicationName("DocumentSearchToolPySide")
    
    # 创建对话框
    dialog = HotkeySettingsDialog()
    
    print(f"热键设置对话框创建成功")
    print(f"对话框标题: {dialog.windowTitle()}")
    print(f"对话框大小: {dialog.size().width()} x {dialog.size().height()}")
    
    # 检查各种选项的状态
    print(f"启用全局热键: {'选中' if dialog.enable_hotkeys_checkbox.isChecked() else '未选中'}")
    print(f"开机时自动启用热键: {'选中' if dialog.enable_on_startup_checkbox.isChecked() else '未选中'}")
    
    # 检查热键表格
    print(f"热键配置表格行数: {dialog.hotkey_table.rowCount()}")
    print("当前热键配置:")
    
    for row in range(dialog.hotkey_table.rowCount()):
        # 获取功能名称
        function_item = dialog.hotkey_table.item(row, 0)
        function_name = function_item.text() if function_item else "未知功能"
        
        # 获取热键编辑器
        hotkey_edit = dialog.hotkey_table.cellWidget(row, 1)
        hotkey_sequence = hotkey_edit.keySequence().toString() if hotkey_edit else "无"
        
        # 获取启用复选框
        checkbox_widget = dialog.hotkey_table.cellWidget(row, 2)
        if checkbox_widget:
            enable_checkbox = checkbox_widget.findChild(QCheckBox)
            enabled = enable_checkbox.isChecked() if enable_checkbox else False
        else:
            enabled = False
            
        print(f"  {function_name}: {hotkey_sequence} ({'启用' if enabled else '禁用'})")
    
    # 显示对话框
    dialog.show()
    
    # 设置定时器自动关闭对话框
    QTimer.singleShot(6000, dialog.close)
    
    # 运行应用
    app.exec()

if __name__ == "__main__":
    test_hotkey_dialog() 