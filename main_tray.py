import sys
import os
import datetime
import logging
import multiprocessing
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QSettings

# 导入托盘功能模块
from tray_app import TrayIcon, parse_arguments

# 导入支持托盘的主窗口类和相关常量
from main_window_tray import TrayMainWindow
from search_gui_pyside import ORGANIZATION_NAME, APPLICATION_NAME

# 导入热键管理器
from hotkey_manager import HotkeyManager

def main():
    """程序入口函数"""
    # 多进程支持
    multiprocessing.freeze_support()
    
    # --- 配置日志 ---
    log_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'DocumentSearchIndexLogs')
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, f"gui_stderr_{datetime.datetime.now():%Y%m%d_%H%M%S}.log")
    error_log_file = None
    
    try:
        error_log_file = open(log_file_path, 'a', encoding='utf-8', buffering=1)
        logging.basicConfig(level=logging.DEBUG,
                           stream=error_log_file,
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        sys.stderr = error_log_file
        print(f"--- GUI Started: stderr and root logger redirected to {log_file_path} ---", file=sys.stderr)
        logging.info(f"--- 程序启动: 日志重定向到 {log_file_path} ---")
    except Exception as e:
        print(f"Error configuring logging: {e}", file=sys.__stderr__)
        if error_log_file:
            try:
                error_log_file.close()
            except Exception:
                pass
    
    # --- 解析命令行参数 ---
    args = parse_arguments()
    
    # --- 读取启动设置 ---
    settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
    
    # 检测是否为首次启动
    is_first_run = not settings.value("app/has_run_before", False, type=bool)
    
    # 启动逻辑优化：区分开机自启动和手动启动
    if args.minimized:
        # 命令行指定了--minimized参数（通常是开机自启动）
        print("检测到开机自启动或命令行最小化启动，将隐藏主窗口")
        should_minimize = True
        # 如果是首次启动但通过开机自启动，仍然设置标记
        if is_first_run:
            settings.setValue("app/has_run_before", True)
    elif is_first_run:
        # 首次手动启动
        print("检测到首次手动启动，将显示主窗口")
        settings.setValue("app/has_run_before", True)
        should_minimize = False  # 首次手动启动总是显示主窗口
    else:
        # 非首次手动启动，根据设置决定
        startup_minimized = settings.value("startup/minimized", False, type=bool)
        should_minimize = startup_minimized
        if should_minimize:
            print("非首次启动且设置为启动时最小化，将隐藏主窗口")
        else:
            print("非首次启动且未设置启动时最小化，将显示主窗口")
    
    # --- 配置高DPI支持 ---
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # --- 创建应用实例 ---
    app = QApplication(sys.argv)
    
    # --- 设置应用元数据 ---
    QApplication.setOrganizationName(ORGANIZATION_NAME)
    QApplication.setApplicationName(APPLICATION_NAME)
    
    # --- 创建支持托盘的主窗口 ---
    window = TrayMainWindow()
    
    # --- 创建热键管理器并初始化 ---
    hotkey_manager = HotkeyManager(window)
    window.hotkey_manager = hotkey_manager  # 给窗口设置热键管理器引用
    
    # 从设置中加载热键配置
    hotkey_manager.load_hotkeys_from_settings()
    
    # --- 创建系统托盘图标 ---
    tray_icon = TrayIcon(window)
    tray_icon.show()
    
    # --- 设置主窗口的托盘图标引用 ---
    window.set_tray_icon(tray_icon)
    
    # --- 设置热键管理器的托盘图标引用 ---
    hotkey_manager.set_tray_icon(tray_icon)
    
    # --- 连接热键信号到相应的处理函数 ---
    def handle_hotkey_triggered(hotkey_name):
        """处理热键触发事件"""
        print(f"热键触发: {hotkey_name}")
        if hotkey_name == "show_search":
            # 显示主搜索窗口
            window.showNormal()
            window.activateWindow()
        elif hotkey_name == "quick_search":
            # 显示轻量级搜索窗口
            window.show_quick_search_dialog()
    
    hotkey_manager.hotkey_activated_signal.connect(handle_hotkey_triggered)
    
    # --- 启动热键监听 ---
    hotkey_manager.start_listener()
    
    # --- 连接托盘信号 ---
    tray_icon.show_main_window_signal.connect(lambda: (window.showNormal(), window.activateWindow()))
    tray_icon.hide_main_window_signal.connect(window.hide)
    tray_icon.quit_app_signal.connect(lambda: (hotkey_manager.stop_listener(), window.force_close(), app.quit()))
    
    # --- 根据启动参数决定是否显示主窗口 ---
    if should_minimize:
        print("以最小化模式启动，仅显示托盘图标")
        window.hide()
    else:
        window.show()
    
    # --- 运行应用 ---
    exit_code = app.exec()
    
    # --- 应用退出时的清理工作 ---
    # 停止热键监听
    hotkey_manager.stop_listener()
    
    # 显式删除窗口实例以触发closeEvent
    window.force_quit = True  # 确保窗口真正关闭而不是最小化到托盘
    del window
    
    # 最后退出应用程序
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 