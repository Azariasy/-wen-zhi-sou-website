"""
启动修复后的托盘功能文智搜

此脚本启动修复后的带有系统托盘支持的文智搜应用程序。
修复了以下问题：
1. 托盘设置菜单在原有设置菜单下正确显示
2. 最近搜索菜单显示真实的搜索历史
3. 修复了对象访问和线程安全问题
4. 添加全局热键支持，可通过双击Ctrl快速调出搜索窗口
5. 添加轻量级搜索窗口，提供快速搜索体验

用法：
1. 普通启动：python start_tray_fixed.py
2. 最小化启动：python start_tray_fixed.py --minimized
3. 搜索启动：python start_tray_fixed.py --search "搜索关键词"
"""

import sys
import os
import argparse
import multiprocessing
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings

# 导入托盘应用程序模块
from main_window_tray import TrayMainWindow
from tray_app import TrayIcon, get_resource_path
from search_gui_pyside import ORGANIZATION_NAME, APPLICATION_NAME
from hotkey_manager import HotkeyManager

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="文智搜 - 带托盘功能")
    parser.add_argument("--minimized", action="store_true", 
                        help="以最小化模式启动，仅显示托盘图标")
    parser.add_argument("--search", type=str, 
                        help="启动时立即执行搜索查询")
    parser.add_argument("--quick-search", action="store_true",
                        help="启动时显示轻量级搜索窗口")
    return parser.parse_args()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 多进程支持
    multiprocessing.freeze_support()
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭最后一个窗口时不退出
    
    # 设置应用信息
    app.setApplicationName(APPLICATION_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)
    
    # 创建托盘图标（先创建托盘图标）
    tray_icon = TrayIcon()
    tray_icon.show()
    
    # 创建主窗口
    window = TrayMainWindow()
    
    # 设置主窗口的托盘图标引用
    window.set_tray_icon(tray_icon)
    
    # 创建热键管理器
    hotkey_manager = HotkeyManager(window)
    
    # 注册"显示主窗口"热键
    hotkey_manager.register_hotkey(
        "show_search",
        "ctrl+ctrl",  # 双击Ctrl
        callback=lambda: (
            window.showNormal(),
            window.activateWindow(),
            window.search_line_edit.setFocus()
        ),
        enabled=True
    )
    
    # 注册"显示轻量级搜索"热键
    # 从设置中读取快速搜索热键配置
    # 首先从设置加载热键配置
    hotkey_manager.load_hotkeys_from_settings()
    
    # 获取热键信息
    hotkey_info = hotkey_manager.get_hotkey_info()
    quick_search_config = hotkey_info.get("quick_search", {})
    quick_search_key = quick_search_config.get('key', 'ctrl+alt+q')  # 默认使用 ctrl+alt+q
    quick_search_enabled = quick_search_config.get('enabled', True)
    
    hotkey_manager.register_hotkey(
        "quick_search",
        quick_search_key,
        callback=lambda: window.show_quick_search_dialog(),
        enabled=quick_search_enabled
    )
    
    # 设置托盘图标的热键管理器引用
    tray_icon.set_hotkey_manager(hotkey_manager)
    
    # 设置热键管理器的托盘图标引用
    hotkey_manager.set_tray_icon(tray_icon)
    
    # 确保热键设置正确
    for name, config in hotkey_manager.hotkeys.items():
        if name == "quick_search":
            print(f"检查轻量级搜索热键: {config['key']} (启用: {config['enabled']})")
    
    # 启动热键监听
    print("正在启动热键监听...")
    hotkey_manager.start_listener()
    print(f"热键监听中... (已注册 {len(hotkey_manager.hotkeys)} 个热键)")
    
    # 连接信号
    tray_icon.show_main_window_signal.connect(lambda: (window.showNormal(), window.activateWindow()))
    tray_icon.hide_main_window_signal.connect(window.hide)
    tray_icon.quit_app_signal.connect(lambda: (window.force_close(), app.quit()))
    
    # 添加最近搜索信号连接，点击后显示主窗口并执行搜索
    tray_icon.quick_search_signal.connect(lambda text: (
        window.showNormal(),
        window.activateWindow(),
        window.search_line_edit.setText(text),
        window.start_search_slot()
    ))
    
    # 添加轻量级搜索菜单项的信号连接
    tray_icon.light_search_signal.connect(window.show_quick_search_dialog)
    
    # 如果提供了搜索参数，执行搜索
    if args.search:
        # 设置搜索框文本并执行搜索
        window.search_line_edit.setText(args.search)
        window.start_search_slot()
    
    # 如果指定了显示轻量级搜索窗口
    if args.quick_search:
        initial_query = args.search if args.search else None
        window.show_quick_search_dialog(initial_query)
    
    # 根据参数显示或隐藏窗口
    if args.minimized and not args.quick_search:
        print("以最小化模式启动，仅显示托盘图标")
        window.hide()
    elif not args.quick_search:
        window.show()
    
    # 添加应用退出时的清理函数
    app.aboutToQuit.connect(lambda: hotkey_manager.stop_listener())
    
    # 保存热键管理器的引用到窗口对象，防止被垃圾回收
    window.hotkey_manager = hotkey_manager
    
    # 运行应用程序
    exit_code = app.exec()
    
    # 应用程序退出时的清理工作
    print("应用程序正在退出...")
    
    # 返回退出代码
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 