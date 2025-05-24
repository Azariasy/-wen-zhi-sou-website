"""
动态托盘菜单模块
提供根据设置动态更新托盘菜单热键显示的功能
"""

from PySide6.QtCore import QSettings

def get_hotkey_display_text(action_id):
    """获取指定动作的热键显示文本
    
    Args:
        action_id: 热键动作ID
        
    Returns:
        str: 热键显示文本，如 "Ctrl+Alt+Q"
    """
    settings = QSettings("YourOrganizationName", "DocumentSearchToolPySide")
    
    # 默认热键映射
    default_hotkeys = {
        "show_main_window": "Ctrl+Alt+S",
        "show_quick_search": "Ctrl+Alt+Q", 
        "hide_window": "Ctrl+Alt+H",
        "start_search": "Ctrl+Alt+F",
        "clear_search": "Ctrl+Alt+C",
        "toggle_window": "Ctrl+Alt+T"
    }
    
    # 从设置中读取热键，如果没有则使用默认值
    hotkey = settings.value(f"hotkeys/{action_id}", default_hotkeys.get(action_id, ""), type=str)
    
    # 检查是否启用
    enabled = settings.value(f"hotkeys/{action_id}_enabled", True, type=bool)
    hotkeys_enabled = settings.value("hotkeys/enabled", True, type=bool)
    
    if not enabled or not hotkeys_enabled or not hotkey:
        return ""
        
    return hotkey

def get_quick_search_hotkey_text():
    """获取快速搜索的热键显示文本
    
    Returns:
        str: 完整的菜单文本，如 "快速搜索 (Ctrl+Alt+Q)"
    """
    hotkey = get_hotkey_display_text("show_quick_search")
    if hotkey:
        return f"快速搜索 ({hotkey})"
    else:
        return "快速搜索"

def get_main_window_hotkey_text():
    """获取显示主窗口的热键显示文本
    
    Returns:
        str: 完整的菜单文本，如 "显示主窗口 (Ctrl+Alt+S)"
    """
    hotkey = get_hotkey_display_text("show_main_window")
    if hotkey:
        return f"显示主窗口 ({hotkey})"
    else:
        return "显示主窗口"

def update_tray_menu_hotkeys(tray_icon):
    """更新托盘菜单中的热键显示
    
    Args:
        tray_icon: 托盘图标对象
    """
    if not hasattr(tray_icon, 'contextMenu'):
        return
        
    menu = tray_icon.contextMenu()
    if not menu:
        return
        
    # 更新菜单项文本
    for action in menu.actions():
        if action.objectName() == "quick_search_action":
            action.setText(get_quick_search_hotkey_text())
        elif action.objectName() == "show_main_window_action":
            action.setText(get_main_window_hotkey_text()) 