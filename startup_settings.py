"""
启动设置对话框模块
"""

import os
import sys
import winreg
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, 
                              QGroupBox, QPushButton, QMessageBox, QLabel,
                              QRadioButton, QButtonGroup)
from PySide6.QtCore import QSettings, Qt


class StartupSettingsDialog(QDialog):
    """启动设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("启动设置")
        self.setMinimumWidth(400)
        self.setMinimumHeight(250)
        
        # 初始化设置对象
        self.settings = QSettings("YourOrganizationName", "DocumentSearchToolPySide")
        
        # 获取应用程序路径
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            self.app_path = sys.executable
        else:
            # 如果是直接运行Python脚本
            self.app_path = os.path.abspath(sys.argv[0])
            
        self._create_ui()
        self._load_settings()
        
    def _create_ui(self):
        """创建用户界面"""
        layout = QVBoxLayout(self)
        
        # 开机启动设置组
        startup_group = QGroupBox("开机启动设置")
        startup_layout = QVBoxLayout(startup_group)
        
        self.auto_start_checkbox = QCheckBox("开机自动启动文智搜")
        self.auto_start_checkbox.setToolTip("选中后，系统开机时会自动启动文智搜应用程序")
        startup_layout.addWidget(self.auto_start_checkbox)
        
        # 启动方式设置组
        startup_mode_group = QGroupBox("启动方式")
        startup_mode_layout = QVBoxLayout(startup_mode_group)
        
        self.startup_mode_group = QButtonGroup(self)
        
        self.normal_startup_radio = QRadioButton("正常启动（显示主窗口）")
        self.normal_startup_radio.setToolTip("启动时显示主窗口")
        self.minimized_startup_radio = QRadioButton("最小化启动（隐藏到系统托盘）")
        self.minimized_startup_radio.setToolTip("启动时自动最小化到系统托盘，不显示主窗口")
        
        self.startup_mode_group.addButton(self.normal_startup_radio, 0)
        self.startup_mode_group.addButton(self.minimized_startup_radio, 1)
        
        startup_mode_layout.addWidget(self.normal_startup_radio)
        startup_mode_layout.addWidget(self.minimized_startup_radio)
        
        # 托盘行为设置组
        tray_group = QGroupBox("系统托盘行为")
        tray_layout = QVBoxLayout(tray_group)
        
        self.close_to_tray_checkbox = QCheckBox("关闭窗口时最小化到托盘")
        self.close_to_tray_checkbox.setToolTip("点击关闭按钮时，程序不退出而是最小化到系统托盘")
        tray_layout.addWidget(self.close_to_tray_checkbox)
        
        self.minimize_to_tray_checkbox = QCheckBox("最小化时隐藏到托盘")
        self.minimize_to_tray_checkbox.setToolTip("最小化窗口时自动隐藏到系统托盘")
        tray_layout.addWidget(self.minimize_to_tray_checkbox)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        # 添加所有组件到主布局
        layout.addWidget(startup_group)
        layout.addWidget(startup_mode_group)
        layout.addWidget(tray_group)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        # 连接信号
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.auto_start_checkbox.toggled.connect(self._on_auto_start_toggled)
        
        # 初始状态
        self._on_auto_start_toggled(False)
        
    def _on_auto_start_toggled(self, checked):
        """当开机启动复选框状态改变时"""
        # 启动方式选项只有在开机启动时才有意义
        self.normal_startup_radio.setEnabled(checked)
        self.minimized_startup_radio.setEnabled(checked)
        
    def _load_settings(self):
        """加载当前设置"""
        # 检查是否已设置开机启动
        auto_start = self._is_auto_start_enabled()
        self.auto_start_checkbox.setChecked(auto_start)
        
        # 加载启动方式设置
        startup_minimized = self.settings.value("startup/minimized", False, type=bool)
        if startup_minimized:
            self.minimized_startup_radio.setChecked(True)
        else:
            self.normal_startup_radio.setChecked(True)
            
        # 加载托盘行为设置
        close_to_tray = self.settings.value("tray/close_to_tray", True, type=bool)
        self.close_to_tray_checkbox.setChecked(close_to_tray)
        
        minimize_to_tray = self.settings.value("tray/minimize_to_tray", False, type=bool)
        self.minimize_to_tray_checkbox.setChecked(minimize_to_tray)
        
    def _is_auto_start_enabled(self):
        """检查是否已启用开机启动"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run",
                               0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(key, "DocumentSearchTool")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False
            
    def _set_auto_start(self, enable):
        """设置或取消开机启动"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Run",
                               0, winreg.KEY_SET_VALUE)
            
            if enable:
                # 根据启动方式设置命令行参数
                if self.minimized_startup_radio.isChecked():
                    startup_command = f'"{self.app_path}" --minimized'
                else:
                    startup_command = f'"{self.app_path}"'
                    
                winreg.SetValueEx(key, "DocumentSearchTool", 0, winreg.REG_SZ, startup_command)
                print(f"已设置开机启动: {startup_command}")
            else:
                try:
                    winreg.DeleteValue(key, "DocumentSearchTool")
                    print("已取消开机启动")
                except FileNotFoundError:
                    pass  # 值不存在，无需删除
                    
            winreg.CloseKey(key)
            return True
            
        except Exception as e:
            print(f"设置开机启动失败: {e}")
            QMessageBox.warning(self, "错误", f"设置开机启动失败:\n{str(e)}")
            return False
            
    def accept(self):
        """确定按钮点击处理"""
        # 设置开机启动
        auto_start = self.auto_start_checkbox.isChecked()
        if not self._set_auto_start(auto_start):
            return  # 如果设置失败，不关闭对话框
            
        # 保存启动方式设置
        startup_minimized = self.minimized_startup_radio.isChecked()
        self.settings.setValue("startup/minimized", startup_minimized)
        
        # 保存托盘行为设置
        self.settings.setValue("tray/close_to_tray", self.close_to_tray_checkbox.isChecked())
        self.settings.setValue("tray/minimize_to_tray", self.minimize_to_tray_checkbox.isChecked())
        
        # 同步设置
        self.settings.sync()
        
        QMessageBox.information(self, "设置成功", "启动设置已保存成功！")
        super().accept()
        
    def reject(self):
        """取消按钮点击处理"""
        super().reject() 