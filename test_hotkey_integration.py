"""
测试热键集成功能
验证热键设置保存、加载和实际功能是否正常工作
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, QTimer, QObject

from hotkey_manager import HotkeyManager
from dynamic_tray_menu import get_hotkey_display_text, get_quick_search_hotkey_text

def test_hotkey_integration():
    """测试热键集成功能"""
    app = QApplication(sys.argv)
    
    # 设置应用元数据
    QApplication.setOrganizationName("YourOrganizationName")
    QApplication.setApplicationName("DocumentSearchToolPySide")
    
    print("=== 热键集成测试 ===\n")
    
    # 1. 测试从设置读取热键
    print("1. 测试从设置读取热键:")
    settings = QSettings()
    
    # 预设一些测试热键
    test_hotkeys = {
        "show_quick_search": "Ctrl+Shift+Space",
        "show_main_window": "Ctrl+Alt+S",
        "hide_window": "Ctrl+Alt+H"
    }
    
    for action, hotkey in test_hotkeys.items():
        settings.setValue(f"hotkeys/{action}", hotkey)
        settings.setValue(f"hotkeys/{action}_enabled", True)
    
    settings.setValue("hotkeys/enabled", True)
    settings.sync()
    
    # 测试读取
    for action in test_hotkeys:
        retrieved_hotkey = get_hotkey_display_text(action)
        print(f"  {action}: {retrieved_hotkey}")
    
    print(f"\n  快速搜索菜单文本: {get_quick_search_hotkey_text()}")
    
    # 2. 测试热键管理器加载设置
    print("\n2. 测试热键管理器加载设置:")
    
    class MockWindow(QObject):
        def __init__(self):
            super().__init__()
    
    window = MockWindow()
    hotkey_manager = HotkeyManager(window)
    
    # 加载设置
    try:
        hotkey_manager.load_hotkeys_from_settings()
        print("  ✓ 热键设置加载成功")
        
        # 显示加载的热键
        hotkeys = hotkey_manager.get_hotkey_info()
        for name, config in hotkeys.items():
            print(f"    {name}: {config}")
            
    except Exception as e:
        print(f"  ✗ 热键设置加载失败: {e}")
    
    # 3. 测试热键重新加载
    print("\n3. 测试热键重新加载:")
    try:
        # 修改一个热键设置
        settings.setValue("hotkeys/show_quick_search", "Ctrl+Alt+F1")
        settings.sync()
        
        # 重新加载
        hotkey_manager.reload_hotkeys()
        print("  ✓ 热键重新加载成功")
        
        # 检查是否更新
        updated_hotkey = get_hotkey_display_text("show_quick_search")
        print(f"  更新后的快速搜索热键: {updated_hotkey}")
        
    except Exception as e:
        print(f"  ✗ 热键重新加载失败: {e}")
    
    print("\n=== 测试完成 ===")
    
    # 清理测试数据
    for action in test_hotkeys:
        settings.remove(f"hotkeys/{action}")
        settings.remove(f"hotkeys/{action}_enabled")
    settings.remove("hotkeys/enabled")
    settings.sync()
    
    # 退出
    QTimer.singleShot(1000, app.quit)
    app.exec()

if __name__ == "__main__":
    test_hotkey_integration() 