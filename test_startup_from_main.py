"""从主窗口测试启动设置功能"""

import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, QSettings

def test_startup_from_main():
    """从主窗口测试启动设置功能"""
    app = QApplication(sys.argv)
    QApplication.setOrganizationName("YourOrganizationName")
    QApplication.setApplicationName("DocumentSearchToolPySide")
    
    try:
        # 导入主窗口
        from search_gui_pyside import MainWindow
        
        # 创建主窗口
        window = MainWindow()
        print("✅ 主窗口创建成功")
        
        # 显示主窗口
        window.show()
        print("✅ 主窗口显示成功")
        
        # 测试启动设置对话框方法是否存在
        if hasattr(window, 'show_startup_settings_dialog_slot'):
            print("✅ 找到启动设置对话框方法")
            
            # 延迟调用启动设置对话框
            def open_startup_dialog():
                try:
                    print("正在打开启动设置对话框...")
                    window.show_startup_settings_dialog_slot()
                    print("✅ 启动设置对话框调用成功")
                except Exception as e:
                    print(f"❌ 启动设置对话框调用失败: {e}")
            
            QTimer.singleShot(2000, open_startup_dialog)
        else:
            print("❌ 未找到启动设置对话框方法")
        
        # 设置自动关闭
        QTimer.singleShot(8000, window.close)
        QTimer.singleShot(8500, app.quit)
        
        return app.exec()
        
    except ImportError as e:
        print(f"❌ 导入主窗口失败: {e}")
        QMessageBox.critical(None, "错误", f"主窗口不可用:\n{str(e)}")
        return 1
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        QMessageBox.critical(None, "错误", f"测试失败:\n{str(e)}")
        return 1

if __name__ == "__main__":
    result = test_startup_from_main()
    sys.exit(result) 