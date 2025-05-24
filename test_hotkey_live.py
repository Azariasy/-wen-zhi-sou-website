"""
实时测试热键功能
验证热键是否能正确触发
"""

import sys
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from PySide6.QtCore import QSettings, QTimer

from hotkey_manager import HotkeyManager

class HotkeyTestWindow(QMainWindow):
    """热键测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("热键功能测试")
        self.setGeometry(100, 100, 400, 300)
        
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 状态标签
        self.status_label = QLabel("准备测试热键...")
        layout.addWidget(self.status_label)
        
        # 热键信息标签
        self.hotkey_info_label = QLabel("")
        layout.addWidget(self.hotkey_info_label)
        
        # 启动按钮
        self.start_btn = QPushButton("启动热键监听")
        self.start_btn.clicked.connect(self.start_hotkey_listening)
        layout.addWidget(self.start_btn)
        
        # 停止按钮
        self.stop_btn = QPushButton("停止热键监听")
        self.stop_btn.clicked.connect(self.stop_hotkey_listening)
        layout.addWidget(self.stop_btn)
        
        # 创建热键管理器
        self.hotkey_manager = HotkeyManager(self)
        self.hotkey_manager.hotkey_activated_signal.connect(self.on_hotkey_triggered)
        
        # 加载热键设置
        self.load_hotkey_settings()
        
    def load_hotkey_settings(self):
        """加载热键设置"""
        try:
            self.hotkey_manager.load_hotkeys_from_settings()
            
            # 显示当前热键配置
            hotkeys = self.hotkey_manager.get_hotkey_info()
            info_text = "当前热键配置:\n"
            for name, config in hotkeys.items():
                enabled_text = "启用" if config.get('enabled', False) else "禁用"
                info_text += f"  {name}: {config.get('key', '未设置')} ({enabled_text})\n"
            
            self.hotkey_info_label.setText(info_text)
            self.status_label.setText("热键设置已加载")
            
        except Exception as e:
            self.status_label.setText(f"加载热键设置失败: {e}")
            
    def start_hotkey_listening(self):
        """启动热键监听"""
        try:
            self.hotkey_manager.start_listener()
            self.status_label.setText("热键监听已启动，请尝试按下配置的热键")
        except Exception as e:
            self.status_label.setText(f"启动热键监听失败: {e}")
            
    def stop_hotkey_listening(self):
        """停止热键监听"""
        try:
            self.hotkey_manager.stop_listener()
            self.status_label.setText("热键监听已停止")
        except Exception as e:
            self.status_label.setText(f"停止热键监听失败: {e}")
            
    def on_hotkey_triggered(self, hotkey_name):
        """热键触发处理"""
        current_time = time.strftime("%H:%M:%S")
        self.status_label.setText(f"[{current_time}] 热键触发: {hotkey_name}")
        print(f"热键触发: {hotkey_name}")
        
        # 根据不同的热键执行不同的操作
        if hotkey_name == "quick_search":
            self.status_label.setText(f"[{current_time}] 快速搜索热键触发！")
        elif hotkey_name == "show_search":
            self.status_label.setText(f"[{current_time}] 显示主窗口热键触发！")
        elif hotkey_name == "hide_window":
            self.status_label.setText(f"[{current_time}] 隐藏窗口热键触发！")

def main():
    app = QApplication(sys.argv)
    
    # 设置应用元数据
    QApplication.setOrganizationName("YourOrganizationName")
    QApplication.setApplicationName("DocumentSearchToolPySide")
    
    window = HotkeyTestWindow()
    window.show()
    
    # 自动启动热键监听
    QTimer.singleShot(1000, window.start_hotkey_listening)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 