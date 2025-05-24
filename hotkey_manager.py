"""
文智搜热键管理器

提供全局热键监听和处理功能。
"""

import keyboard
import sys
import time
from threading import Thread
from PySide6.QtCore import QObject, Signal, QSettings


class HotkeyManager(QObject):
    """全局热键管理类"""
    
    # 定义热键触发信号
    hotkey_activated_signal = Signal(str)  # 参数为热键名称
    
    def __init__(self, parent=None):
        """初始化热键管理器"""
        super().__init__(parent)
        
        # 热键配置字典，格式: {"hotkey_name": {"key": "ctrl+alt+q", "enabled": True}}
        self.hotkeys = {}
        
        # 监听线程
        self.listener_thread = None
        self.is_listening = False
        self.stop_requested = False
        
        # 托盘图标引用（用于更新热键显示）
        self.tray_icon = None
        
        # 不再使用旧的热键加载系统，将在main_tray.py中调用load_hotkeys_from_settings()
    
    def register_hotkey(self, name, key_combination, callback=None, enabled=True):
        """注册一个新的热键
        
        Args:
            name: 热键名称
            key_combination: 热键组合，如 "ctrl+空格"
            callback: 热键触发时的回调函数
            enabled: 是否启用该热键
        """
        # 确保热键组合使用英文space
        key_combination = key_combination.replace("空格", "space")
        
        if name not in self.hotkeys:
            self.hotkeys[name] = {
                "key": key_combination,
                "enabled": enabled,
                "description": name
            }
        else:
            # 更新现有热键
            self.hotkeys[name]["key"] = key_combination
            self.hotkeys[name]["enabled"] = enabled
        
        # 如果提供了回调函数，连接到信号
        if callback:
            self.hotkey_activated_signal.connect(
                lambda hotkey_name: callback() if hotkey_name == name else None
            )
    
    def start_listener(self):
        """启动热键监听线程"""
        if self.listener_thread and self.listener_thread.is_alive():
            print("热键监听线程已在运行")
            return
        
        self.stop_requested = False
        self.is_listening = True
        
        # 创建新的监听线程
        self.listener_thread = Thread(
            target=self._listener_thread_func,
            daemon=True  # 设为守护线程，应用退出时自动结束
        )
        self.listener_thread.start()
        print("热键监听线程已启动")
    
    def stop_listener(self):
        """停止热键监听线程"""
        if not self.listener_thread or not self.listener_thread.is_alive():
            return
        
        self.stop_requested = True
        self.is_listening = False
        
        # 等待线程结束
        self.listener_thread.join(timeout=1.0)
        print("热键监听线程已停止")
    
    def _listener_thread_func(self):
        """热键监听线程函数"""
        print("正在启动热键监听...")
        
        # 取消所有已注册的热键
        keyboard.unhook_all()
        
        # 注册活跃的热键
        active_hotkeys = {}
        for name, config in self.hotkeys.items():
            if config["enabled"]:
                try:
                    key = config["key"]
                    keyboard.add_hotkey(
                        key, 
                        lambda n=name: self._hotkey_triggered(n),
                        suppress=False  # 不阻止热键传递给其他应用
                    )
                    active_hotkeys[name] = key
                    print(f"已注册热键: {name} -> {key}")
                except Exception as e:
                    print(f"注册热键 {name} ({config['key']}) 失败: {e}")
        
        # 监听事件，直到请求停止
        print(f"热键监听中... (已注册 {len(active_hotkeys)} 个热键)")
        try:
            while not self.stop_requested:
                time.sleep(0.1)
        finally:
            # 清理
            keyboard.unhook_all()
            print("已解除所有热键绑定")
    
    def _hotkey_triggered(self, hotkey_name):
        """热键触发处理函数"""
        print(f"热键触发: {hotkey_name}")
        # 发射信号，通知UI线程
        self.hotkey_activated_signal.emit(hotkey_name)
    
    def set_tray_icon(self, tray_icon):
        """设置托盘图标引用，用于更新热键显示
        
        Args:
            tray_icon: 托盘图标实例
        """
        self.tray_icon = tray_icon
    
    def set_hotkey(self, name, key_combination=None, enabled=None):
        """修改热键设置
        
        Args:
            name: 热键名称
            key_combination: 新的热键组合，不变则为None
            enabled: 是否启用，不变则为None
        
        Returns:
            bool: 是否成功设置
        """
        # 如果热键不存在，创建新的
        if name not in self.hotkeys:
            self.hotkeys[name] = {"key": "", "enabled": True, "description": name}
        
        if key_combination is not None:
            self.hotkeys[name]["key"] = key_combination
            
        if enabled is not None:
            self.hotkeys[name]["enabled"] = enabled
            
        print(f"设置热键: {name} = {self.hotkeys[name]['key']} (启用: {self.hotkeys[name]['enabled']})")
        return True
    
    def get_hotkey_info(self):
        """获取所有热键信息
        
        Returns:
            dict: 热键配置信息
        """
        return self.hotkeys.copy()

    def load_hotkeys_from_settings(self):
        """从QSettings加载热键配置"""
        settings = QSettings("YourOrganizationName", "DocumentSearchToolPySide")
        
        # 检查是否启用热键
        hotkeys_enabled = settings.value("hotkeys/enabled", True, type=bool)
        if not hotkeys_enabled:
            print("热键功能被禁用")
            return
            
        # 预定义的热键动作映射
        action_mapping = {
            "show_main_window": "show_search",
            "show_quick_search": "quick_search", 
            "hide_window": "hide_window",
            "start_search": "start_search",
            "clear_search": "clear_search", 
            "toggle_window": "toggle_window"
        }
        
        # 默认热键
        default_hotkeys = {
            "show_main_window": "ctrl+alt+s",
            "show_quick_search": "ctrl+alt+q", 
            "hide_window": "ctrl+alt+h",
            "start_search": "ctrl+alt+f",
            "clear_search": "ctrl+alt+c",
            "toggle_window": "ctrl+alt+t"
        }
        
        # 清除现有热键配置
        self.hotkeys.clear()
        
        # 加载每个热键
        for setting_key, hotkey_name in action_mapping.items():
            # 检查是否启用该热键
            enabled = settings.value(f"hotkeys/{setting_key}_enabled", True, type=bool)
            if not enabled:
                continue
                
            # 获取热键序列
            hotkey_seq = settings.value(f"hotkeys/{setting_key}", "", type=str)
            if not hotkey_seq:
                hotkey_seq = default_hotkeys.get(setting_key, "")
                
            if hotkey_seq:
                # 转换热键格式 (Ctrl+Alt+Q -> ctrl+alt+q)
                hotkey_seq = hotkey_seq.lower().replace("+", "+")
                
                # 设置热键
                self.set_hotkey(hotkey_name, hotkey_seq, enabled=True)
                print(f"加载热键设置: {hotkey_name} = {hotkey_seq}")
                
    def reload_hotkeys(self):
        """重新加载热键设置"""
        print("重新加载热键设置...")
        
        # 停止当前监听
        was_listening = self.is_listening
        if was_listening:
            self.stop_listener()
            
        # 加载新的热键设置
        self.load_hotkeys_from_settings()
        
        # 如果之前在监听，重新开始监听
        if was_listening:
            self.start_listener()
            print("热键设置已重新加载并应用")


# 简单测试代码
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("热键管理器测试")
            self.setGeometry(100, 100, 400, 300)
            
            # 中央部件
            central = QWidget()
            self.setCentralWidget(central)
            layout = QVBoxLayout(central)
            
            # 状态标签
            self.status_label = QLabel("准备就绪")
            layout.addWidget(self.status_label)
            
            # 启动按钮
            self.start_btn = QPushButton("启动热键监听")
            self.start_btn.clicked.connect(self.start_listening)
            layout.addWidget(self.start_btn)
            
            # 停止按钮
            self.stop_btn = QPushButton("停止热键监听")
            self.stop_btn.clicked.connect(self.stop_listening)
            layout.addWidget(self.stop_btn)
            
            # 创建热键管理器
            self.hotkey_manager = HotkeyManager()
            
            # 连接信号
            self.hotkey_manager.hotkey_activated_signal.connect(self.on_hotkey)
            
            # 注册测试热键
            self.hotkey_manager.register_hotkey(
                "test1", 
                "ctrl+shift+t", 
                callback=lambda: self.status_label.setText("热键触发：ctrl+shift+t"), 
                enabled=True
            )
            
            # 注册双击ctrl
            self.hotkey_manager.register_hotkey(
                "show_search", 
                "ctrl+ctrl",
                callback=lambda: self.status_label.setText("热键触发：双击Ctrl"), 
                enabled=True
            )
    
    def start_listening(self):
        self.hotkey_manager.start_listener()
        self.status_label.setText("热键监听已启动")
    
    def stop_listening(self):
        self.hotkey_manager.stop_listener()
        self.status_label.setText("热键监听已停止")
    
    def on_hotkey(self, name):
        self.status_label.setText(f"热键触发：{name}")
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec()) 