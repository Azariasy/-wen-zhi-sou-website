"""
测试托盘菜单热键显示动态更新功能

此脚本测试托盘图标菜单中的热键显示是否能根据设置动态更新。
"""

import sys
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget, QLineEdit
from PySide6.QtCore import Qt

from tray_app import TrayIcon
from hotkey_manager import HotkeyManager

class TestHotkeyDisplay(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("测试托盘热键显示动态更新")
        self.setGeometry(100, 100, 500, 300)
        
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 说明标签
        info_label = QLabel(
            "此窗口用于测试托盘菜单中的热键显示是否能动态更新。\n"
            "1. 首先会创建托盘图标和热键管理器\n"
            "2. 右键点击托盘图标查看轻量级搜索的热键显示\n"
            "3. 然后可以修改热键设置，观察托盘菜单是否动态更新"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)
        
        # 当前热键显示
        self.hotkey_display = QLabel("当前轻量级搜索热键: 未设置")
        layout.addWidget(self.hotkey_display)
        
        # 新热键输入
        self.new_hotkey_input = QLineEdit()
        self.new_hotkey_input.setPlaceholderText("输入新的热键组合，如: ctrl+shift+f")
        layout.addWidget(self.new_hotkey_input)
        
        # 测试按钮
        self.init_btn = QPushButton("初始化托盘和热键管理器")
        self.init_btn.clicked.connect(self.initialize_components)
        layout.addWidget(self.init_btn)
        
        self.update_hotkey_btn = QPushButton("更新轻量级搜索热键")
        self.update_hotkey_btn.clicked.connect(self.update_hotkey)
        layout.addWidget(self.update_hotkey_btn)
        
        self.toggle_enable_btn = QPushButton("切换热键启用状态")
        self.toggle_enable_btn.clicked.connect(self.toggle_hotkey_enabled)
        layout.addWidget(self.toggle_enable_btn)
        
        # 组件
        self.tray_icon = None
        self.hotkey_manager = None
    
    def initialize_components(self):
        """初始化托盘图标和热键管理器"""
        try:
            # 创建托盘图标
            self.tray_icon = TrayIcon()
            self.tray_icon.show()
            
            # 创建热键管理器
            self.hotkey_manager = HotkeyManager()
            
            # 注册默认热键
            self.hotkey_manager.register_hotkey(
                "quick_search",
                "alt+space",
                enabled=True
            )
            
            # 设置双向引用
            self.tray_icon.set_hotkey_manager(self.hotkey_manager)
            self.hotkey_manager.set_tray_icon(self.tray_icon)
            
            # 更新显示
            self.update_display()
            
            self.status_label.setText("托盘图标和热键管理器已初始化")
            
        except Exception as e:
            self.status_label.setText(f"初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_hotkey(self):
        """更新热键设置"""
        if not self.hotkey_manager:
            self.status_label.setText("请先初始化组件")
            return
        
        new_hotkey = self.new_hotkey_input.text().strip()
        if not new_hotkey:
            self.status_label.setText("请输入新的热键组合")
            return
        
        try:
            # 更新热键设置
            success = self.hotkey_manager.set_hotkey("quick_search", new_hotkey, True)
            
            if success:
                self.update_display()
                self.status_label.setText(f"热键已更新为: {new_hotkey}")
            else:
                self.status_label.setText("更新热键失败")
                
        except Exception as e:
            self.status_label.setText(f"更新热键失败: {str(e)}")
    
    def toggle_hotkey_enabled(self):
        """切换热键启用状态"""
        if not self.hotkey_manager:
            self.status_label.setText("请先初始化组件")
            return
        
        try:
            # 获取当前状态
            hotkey_info = self.hotkey_manager.get_hotkey_info()
            current_enabled = hotkey_info.get('quick_search', {}).get('enabled', False)
            
            # 切换状态
            new_enabled = not current_enabled
            success = self.hotkey_manager.set_hotkey("quick_search", enabled=new_enabled)
            
            if success:
                self.update_display()
                status = "启用" if new_enabled else "禁用"
                self.status_label.setText(f"热键已{status}")
            else:
                self.status_label.setText("切换状态失败")
                
        except Exception as e:
            self.status_label.setText(f"切换状态失败: {str(e)}")
    
    def update_display(self):
        """更新显示"""
        if self.hotkey_manager:
            hotkey_info = self.hotkey_manager.get_hotkey_info()
            quick_search_config = hotkey_info.get('quick_search', {})
            
            hotkey_text = quick_search_config.get('key', '未设置')
            enabled_text = "启用" if quick_search_config.get('enabled', False) else "禁用"
            
            self.hotkey_display.setText(f"当前轻量级搜索热键: {hotkey_text} ({enabled_text})")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.tray_icon:
            self.tray_icon.hide()
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    window = TestHotkeyDisplay()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 