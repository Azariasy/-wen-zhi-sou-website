"""
简化版的文智搜托盘应用程序

这个脚本提供了基本的托盘支持功能:
1. 系统托盘图标显示
2. 托盘菜单（显示/隐藏窗口、退出）
3. 最小化到托盘
4. 启动时最小化到托盘 (--minimized 参数)
"""

import sys
import os
import argparse
from pathlib import Path

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMainWindow
from PySide6.QtGui import QIcon, QAction, QCloseEvent
from PySide6.QtCore import Qt, Signal, QSettings, QThread

# 导入原始的主窗口类
from search_gui_pyside import MainWindow, ORGANIZATION_NAME, APPLICATION_NAME

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，适用于开发环境和打包后的环境"""
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # 如果不是通过PyInstaller打包，则使用当前文件夹
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class SimpleTrayIcon(QSystemTrayIcon):
    """简化版系统托盘图标类"""
    
    # 定义信号
    show_window_signal = Signal()    # 显示窗口信号
    hide_window_signal = Signal()    # 隐藏窗口信号
    quit_app_signal = Signal()       # 退出应用信号
    
    def __init__(self, parent=None):
        """初始化托盘图标"""
        # 加载图标
        icon_path = get_resource_path("app_icon.ico")
        if not os.path.exists(icon_path):
            # 尝试使用PNG作为备选
            icon_path = get_resource_path("app_icon.png")
        
        icon = QIcon(icon_path)
        super().__init__(icon, parent)
        
        # 设置工具提示
        self.setToolTip("文智搜")
        
        # 创建托盘菜单
        self.setup_menu()
        
        # 连接信号
        self.activated.connect(self._on_activated)
    
    def setup_menu(self):
        """设置托盘菜单"""
        menu = QMenu()
        
        # 添加显示/隐藏窗口菜单项
        self.show_action = menu.addAction("显示主窗口")
        self.show_action.triggered.connect(self.show_window_signal.emit)
        
        self.hide_action = menu.addAction("隐藏主窗口")
        self.hide_action.triggered.connect(self.hide_window_signal.emit)
        
        # 添加分隔线
        menu.addSeparator()
        
        # 添加退出菜单项
        exit_action = menu.addAction("退出")
        exit_action.triggered.connect(self.quit_app_signal.emit)
        
        # 设置菜单
        self.setContextMenu(menu)
    
    def _on_activated(self, reason):
        """处理托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # 单击托盘图标，显示主窗口
            self.show_window_signal.emit()

class TrayMainWindow(MainWindow):
    """支持托盘功能的主窗口"""
    
    def __init__(self):
        super().__init__()
        # 添加托盘功能支持的标志
        self.minimize_to_tray = True
    
    def closeEvent(self, event: QCloseEvent):
        """重写关闭事件，最小化到托盘而不是关闭"""
        if self.minimize_to_tray:
            event.ignore()  # 忽略关闭事件
            self.hide()     # 隐藏窗口
        else:
            # 确保优雅关闭所有线程
            self._shutdown_threads()
            event.accept()  # 接受关闭事件
    
    def _shutdown_threads(self):
        """确保所有线程安全停止"""
        try:
            print("正在关闭所有线程...")
            
            # 检查是否有搜索线程在运行
            if hasattr(self, 'search_thread') and self.search_thread.isRunning():
                print("正在停止搜索线程...")
                self.search_thread.terminate()
                self.search_thread.wait(1000)
                
            # 检查是否有索引线程在运行
            if hasattr(self, 'indexing_thread') and self.indexing_thread.isRunning():
                print("正在停止索引线程...")
                self.indexing_thread.terminate()
                self.indexing_thread.wait(1000)
            
            # 检查是否有工作线程在运行
            if hasattr(self, 'worker_thread') and self.worker_thread.isRunning():
                print("正在停止工作线程...")
                self.worker_thread.terminate()
                self.worker_thread.wait(1000)
                
            # 检查所有QThread子类（查找所有线程）
            all_threads = []
            for attr_name in dir(self):
                attr = getattr(self, attr_name)
                if isinstance(attr, QThread) and attr.isRunning():
                    print(f"正在停止额外线程: {attr_name}")
                    attr.terminate()
                    attr.wait(1000)
                    all_threads.append(attr)
                    
            print(f"已关闭 {len(all_threads)} 个额外线程")
        except Exception as e:
            print(f"关闭线程时出错: {e}")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="文智搜 - 托盘模式")
    parser.add_argument("--minimized", action="store_true", 
                        help="以最小化模式启动")
    return parser.parse_args()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭最后一个窗口时不退出
    
    # 设置应用信息
    app.setApplicationName(APPLICATION_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)
    
    # 创建主窗口
    window = TrayMainWindow()
    
    # 创建托盘图标
    tray_icon = SimpleTrayIcon()
    tray_icon.show()
    
    # 连接信号
    tray_icon.show_window_signal.connect(lambda: (window.showNormal(), window.activateWindow()))
    tray_icon.hide_window_signal.connect(window.hide)
    tray_icon.quit_app_signal.connect(lambda: (setattr(window, 'minimize_to_tray', False), window.close(), app.quit()))
    
    # 根据参数显示或隐藏窗口
    if args.minimized:
        print("以最小化模式启动，窗口隐藏")
        window.hide()
    else:
        window.show()
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 