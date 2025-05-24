"""测试启动设置功能"""

import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, QSettings

def test_startup_settings():
    """测试启动设置对话框"""
    app = QApplication(sys.argv)
    QApplication.setOrganizationName("YourOrganizationName")
    QApplication.setApplicationName("DocumentSearchToolPySide")
    
    try:
        # 导入启动设置对话框
        from startup_settings import StartupSettingsDialog
        
        # 创建对话框
        dialog = StartupSettingsDialog()
        print("✅ 启动设置对话框创建成功")
        print(f"对话框标题: {dialog.windowTitle()}")
        print(f"对话框大小: {dialog.minimumWidth()} x {dialog.minimumHeight()}")
        
        # 检查对话框内的主要组件
        settings = QSettings("YourOrganizationName", "DocumentSearchToolPySide")
        
        # 显示当前设置值
        auto_start = settings.value("startup/auto_start", False, type=bool)
        startup_mode = settings.value("startup/startup_mode", "normal", type=str)
        close_to_tray = settings.value("tray/close_to_tray", True, type=bool)
        minimize_to_tray = settings.value("tray/minimize_to_tray", False, type=bool)
        
        print(f"\n当前启动设置:")
        print(f"- 开机自启动: {auto_start}")
        print(f"- 启动模式: {startup_mode}")
        print(f"- 关闭到托盘: {close_to_tray}")
        print(f"- 最小化到托盘: {minimize_to_tray}")
        
        # 显示对话框
        dialog.show()
        print("\n✅ 启动设置对话框显示成功")
        print("请在对话框中测试各种设置选项...")
        
        # 设置自动关闭
        QTimer.singleShot(8000, dialog.close)
        QTimer.singleShot(8500, app.quit)
        
        return app.exec()
        
    except ImportError as e:
        print(f"❌ 导入启动设置模块失败: {e}")
        QMessageBox.critical(None, "错误", f"启动设置功能不可用:\n{str(e)}")
        return 1
    except Exception as e:
        print(f"❌ 启动设置测试失败: {e}")
        QMessageBox.critical(None, "错误", f"启动设置测试失败:\n{str(e)}")
        return 1

if __name__ == "__main__":
    result = test_startup_settings()
    sys.exit(result) 