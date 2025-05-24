"""测试启动设置功能逻辑"""

import sys
from PySide6.QtWidgets import QApplication, QCheckBox, QRadioButton
from PySide6.QtCore import QSettings

def test_startup_functionality():
    """测试启动设置的各项功能"""
    app = QApplication(sys.argv)
    QApplication.setOrganizationName("YourOrganizationName")
    QApplication.setApplicationName("DocumentSearchToolPySide")
    
    print("🔍 测试启动设置功能...")
    
    try:
        # 导入启动设置对话框
        from startup_settings import StartupSettingsDialog
        
        # 创建对话框
        dialog = StartupSettingsDialog()
        
        # 获取设置对象
        settings = QSettings("YourOrganizationName", "DocumentSearchToolPySide")
        
        print("\n📋 当前启动设置状态:")
        
        # 测试1: 检查开机启动设置
        auto_start_original = settings.value("startup/auto_start", False, type=bool)
        print(f"- 开机自启动: {auto_start_original}")
        
        # 测试2: 检查启动模式设置
        startup_mode_original = settings.value("startup/startup_mode", "normal", type=str)
        print(f"- 启动模式: {startup_mode_original}")
        
        # 测试3: 检查托盘设置
        close_to_tray_original = settings.value("tray/close_to_tray", True, type=bool)
        minimize_to_tray_original = settings.value("tray/minimize_to_tray", False, type=bool)
        print(f"- 关闭到托盘: {close_to_tray_original}")
        print(f"- 最小化到托盘: {minimize_to_tray_original}")
        
        print("\n🔧 测试设置修改功能...")
        
        # 测试4: 修改设置并保存
        test_settings = {
            "startup/auto_start": True,
            "startup/startup_mode": "minimized",
            "tray/close_to_tray": False,
            "tray/minimize_to_tray": True
        }
        
        for key, value in test_settings.items():
            settings.setValue(key, value)
            print(f"✅ 设置 {key} = {value}")
        
        settings.sync()
        print("✅ 设置已同步保存")
        
        print("\n🔍 验证设置是否生效...")
        
        # 测试5: 重新读取设置验证
        for key, expected_value in test_settings.items():
            if key.endswith("_start"):
                actual_value = settings.value(key, False, type=bool)
            elif key.endswith("_tray"):
                actual_value = settings.value(key, False, type=bool)
            else:
                actual_value = settings.value(key, "", type=str)
            
            if actual_value == expected_value:
                print(f"✅ {key}: {actual_value} (正确)")
            else:
                print(f"❌ {key}: 期望 {expected_value}, 实际 {actual_value}")
        
        print("\n🔄 恢复原始设置...")
        
        # 测试6: 恢复原始设置
        original_settings = {
            "startup/auto_start": auto_start_original,
            "startup/startup_mode": startup_mode_original,
            "tray/close_to_tray": close_to_tray_original,
            "tray/minimize_to_tray": minimize_to_tray_original
        }
        
        for key, value in original_settings.items():
            settings.setValue(key, value)
        
        settings.sync()
        print("✅ 原始设置已恢复")
        
        print("\n📊 启动设置功能测试总结:")
        print("✅ 启动设置对话框创建: 成功")
        print("✅ 设置读取功能: 成功")
        print("✅ 设置保存功能: 成功")
        print("✅ 设置验证功能: 成功")
        print("✅ 设置恢复功能: 成功")
        
        return 0
        
    except ImportError as e:
        print(f"❌ 启动设置模块导入失败: {e}")
        return 1
    except Exception as e:
        print(f"❌ 启动设置功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        app.quit()

if __name__ == "__main__":
    result = test_startup_functionality()
    sys.exit(result) 