"""测试启动设置UI组件功能"""

import sys
from PySide6.QtWidgets import QApplication, QCheckBox, QRadioButton, QGroupBox
from PySide6.QtCore import QSettings, QTimer

def test_startup_ui_components():
    """测试启动设置对话框的UI组件"""
    app = QApplication(sys.argv)
    QApplication.setOrganizationName("YourOrganizationName")
    QApplication.setApplicationName("DocumentSearchToolPySide")
    
    print("🔍 测试启动设置UI组件...")
    
    try:
        # 导入启动设置对话框
        from startup_settings import StartupSettingsDialog
        
        # 创建对话框
        dialog = StartupSettingsDialog()
        print("✅ 启动设置对话框创建成功")
        
        # 测试UI组件
        print("\n📋 检查UI组件:")
        
        # 查找开机启动复选框
        auto_start_checkbox = dialog.findChild(QCheckBox, "auto_start_checkbox")
        if auto_start_checkbox:
            print(f"✅ 开机启动复选框: 找到 (选中: {auto_start_checkbox.isChecked()})")
        else:
            print("❌ 开机启动复选框: 未找到")
        
        # 查找启动模式组
        startup_group = dialog.findChild(QGroupBox)
        if startup_group:
            print(f"✅ 启动模式组: 找到 ('{startup_group.title()}')")
            
            # 查找启动模式单选按钮
            radio_buttons = startup_group.findChildren(QRadioButton)
            if radio_buttons:
                print(f"✅ 找到 {len(radio_buttons)} 个启动模式选项:")
                for i, radio in enumerate(radio_buttons):
                    checked_status = "选中" if radio.isChecked() else "未选中"
                    print(f"  - {radio.text()}: {checked_status}")
            else:
                print("❌ 启动模式单选按钮: 未找到")
        else:
            print("❌ 启动模式组: 未找到")
        
        # 查找托盘相关复选框
        all_checkboxes = dialog.findChildren(QCheckBox)
        tray_checkboxes = [cb for cb in all_checkboxes if "托盘" in cb.text()]
        
        if tray_checkboxes:
            print(f"✅ 找到 {len(tray_checkboxes)} 个托盘选项:")
            for checkbox in tray_checkboxes:
                checked_status = "选中" if checkbox.isChecked() else "未选中"
                print(f"  - {checkbox.text()}: {checked_status}")
        else:
            print("❌ 托盘复选框: 未找到")
        
        print(f"\n📏 对话框尺寸: {dialog.width()} x {dialog.height()}")
        print(f"📏 最小尺寸: {dialog.minimumWidth()} x {dialog.minimumHeight()}")
        
        # 显示对话框
        dialog.show()
        print("\n✅ 对话框显示成功")
        
        # 简短显示后关闭
        QTimer.singleShot(3000, dialog.close)
        QTimer.singleShot(3500, app.quit)
        
        print("📊 UI组件测试总结:")
        print("✅ 对话框创建: 成功")
        print("✅ UI组件检查: 完成")
        print("✅ 对话框显示: 成功")
        
        return app.exec()
        
    except ImportError as e:
        print(f"❌ 启动设置模块导入失败: {e}")
        return 1
    except Exception as e:
        print(f"❌ UI组件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    result = test_startup_ui_components()
    sys.exit(result) 