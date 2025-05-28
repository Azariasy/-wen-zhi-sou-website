"""
托盘设置对话框模块

本模块提供托盘相关设置的配置界面。
"""

import os
import sys
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, 
                              QGroupBox, QPushButton, QMessageBox, QLabel,
                              QRadioButton, QButtonGroup, QSpinBox)
from PySide6.QtCore import QSettings, Qt, Signal

# 导入主程序的常量
from search_gui_pyside import ORGANIZATION_NAME, APPLICATION_NAME


class TraySettingsDialog(QDialog):
    """托盘设置对话框"""
    
    # 设置更新信号
    settings_updated_signal = Signal()
    
    def __init__(self, parent=None):
        """初始化对话框"""
        super().__init__(parent)
        
        # 设置窗口属性
        self.setWindowTitle("托盘设置")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        # 创建设置对象 - 使用与主程序相同的设置路径
        self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        
        # 创建UI
        self._create_ui()
        
        # 加载设置
        self._load_settings()
    
    def _create_ui(self):
        """创建用户界面"""
        # 主布局
        layout = QVBoxLayout(self)
        
        # 托盘显示设置组
        display_group = QGroupBox("托盘图标显示")
        display_layout = QVBoxLayout(display_group)
        
        self.show_tray_icon_checkbox = QCheckBox("显示系统托盘图标")
        self.show_tray_icon_checkbox.setToolTip("在系统托盘中显示应用程序图标")
        display_layout.addWidget(self.show_tray_icon_checkbox)
        
        self.tray_notifications_checkbox = QCheckBox("启用托盘通知")
        self.tray_notifications_checkbox.setToolTip("在托盘中显示操作通知消息")
        display_layout.addWidget(self.tray_notifications_checkbox)
        
        # 窗口行为设置组
        behavior_group = QGroupBox("窗口行为")
        behavior_layout = QVBoxLayout(behavior_group)
        
        self.close_to_tray_checkbox = QCheckBox("关闭窗口时最小化到托盘")
        self.close_to_tray_checkbox.setToolTip("点击关闭按钮时，程序不退出而是最小化到系统托盘")
        behavior_layout.addWidget(self.close_to_tray_checkbox)
        
        self.minimize_to_tray_checkbox = QCheckBox("最小化时隐藏到托盘")
        self.minimize_to_tray_checkbox.setToolTip("最小化窗口时自动隐藏到系统托盘")
        behavior_layout.addWidget(self.minimize_to_tray_checkbox)
        
        self.start_minimized_checkbox = QCheckBox("启动时最小化到托盘")
        self.start_minimized_checkbox.setToolTip("程序启动时自动最小化到托盘，不显示主窗口")
        behavior_layout.addWidget(self.start_minimized_checkbox)
        
        # 托盘菜单设置组
        menu_group = QGroupBox("托盘菜单选项")
        menu_layout = QVBoxLayout(menu_group)
        
        self.show_quick_search_checkbox = QCheckBox("显示快速搜索菜单")
        self.show_quick_search_checkbox.setToolTip("在托盘右键菜单中显示快速搜索选项")
        menu_layout.addWidget(self.show_quick_search_checkbox)
        
        self.show_recent_files_checkbox = QCheckBox("显示最近文件菜单")
        self.show_recent_files_checkbox.setToolTip("在托盘右键菜单中显示最近打开的文件")
        menu_layout.addWidget(self.show_recent_files_checkbox)
        
        # 最近文件数量设置
        recent_files_layout = QHBoxLayout()
        recent_files_label = QLabel("最近文件显示数量:")
        self.recent_files_count_spinbox = QSpinBox()
        self.recent_files_count_spinbox.setMinimum(1)
        self.recent_files_count_spinbox.setMaximum(20)
        self.recent_files_count_spinbox.setValue(5)
        self.recent_files_count_spinbox.setToolTip("设置托盘菜单中显示的最近文件数量")
        
        recent_files_layout.addWidget(recent_files_label)
        recent_files_layout.addWidget(self.recent_files_count_spinbox)
        recent_files_layout.addStretch()
        
        menu_layout.addLayout(recent_files_layout)
        
        # 动画和效果设置组
        effects_group = QGroupBox("动画和效果")
        effects_layout = QVBoxLayout(effects_group)
        
        self.tray_animations_checkbox = QCheckBox("启用托盘动画效果")
        self.tray_animations_checkbox.setToolTip("在托盘图标上启用动画效果（如闪烁通知）")
        effects_layout.addWidget(self.tray_animations_checkbox)
        
        self.balloon_notifications_checkbox = QCheckBox("启用气泡通知")
        self.balloon_notifications_checkbox.setToolTip("使用系统气泡通知显示重要消息")
        effects_layout.addWidget(self.balloon_notifications_checkbox)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.restore_defaults_button = QPushButton("恢复默认")
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        
        button_layout.addWidget(self.restore_defaults_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        # 添加所有组件到主布局
        layout.addWidget(display_group)
        layout.addWidget(behavior_group)
        layout.addWidget(menu_group)
        layout.addWidget(effects_group)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        # 连接信号
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.restore_defaults_button.clicked.connect(self._restore_defaults)
        
        # 连接复选框信号以动态启用/禁用相关控件
        self.show_recent_files_checkbox.toggled.connect(self._on_recent_files_toggled)
    
    def _on_recent_files_toggled(self, checked):
        """当最近文件复选框状态改变时"""
        self.recent_files_count_spinbox.setEnabled(checked)
    
    def _load_settings(self):
        """从设置加载配置"""
        # 托盘显示设置
        show_tray_icon = self.settings.value("tray/show_icon", True, type=bool)
        self.show_tray_icon_checkbox.setChecked(show_tray_icon)
        
        tray_notifications = self.settings.value("tray/notifications", True, type=bool)
        self.tray_notifications_checkbox.setChecked(tray_notifications)
        
        # 窗口行为设置
        close_to_tray = self.settings.value("tray/close_to_tray", True, type=bool)
        self.close_to_tray_checkbox.setChecked(close_to_tray)
        
        minimize_to_tray = self.settings.value("tray/minimize_to_tray", False, type=bool)
        self.minimize_to_tray_checkbox.setChecked(minimize_to_tray)
        
        start_minimized = self.settings.value("startup/minimized", False, type=bool)
        self.start_minimized_checkbox.setChecked(start_minimized)
        
        # 托盘菜单设置
        show_quick_search = self.settings.value("tray/show_quick_search", True, type=bool)
        self.show_quick_search_checkbox.setChecked(show_quick_search)
        
        show_recent_files = self.settings.value("tray/show_recent_files", True, type=bool)
        self.show_recent_files_checkbox.setChecked(show_recent_files)
        
        recent_files_count = self.settings.value("tray/recent_files_count", 5, type=int)
        self.recent_files_count_spinbox.setValue(recent_files_count)
        
        # 动画和效果设置
        tray_animations = self.settings.value("tray/animations", True, type=bool)
        self.tray_animations_checkbox.setChecked(tray_animations)
        
        balloon_notifications = self.settings.value("tray/balloon_notifications", True, type=bool)
        self.balloon_notifications_checkbox.setChecked(balloon_notifications)
        
        # 更新控件状态
        self._on_recent_files_toggled(show_recent_files)
    
    def _restore_defaults(self):
        """恢复默认设置"""
        reply = QMessageBox.question(self, "恢复默认设置", 
                                   "确定要恢复所有托盘设置为默认值吗？",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 设置默认值
            self.show_tray_icon_checkbox.setChecked(True)
            self.tray_notifications_checkbox.setChecked(True)
            self.close_to_tray_checkbox.setChecked(True)
            self.minimize_to_tray_checkbox.setChecked(False)
            self.start_minimized_checkbox.setChecked(False)
            self.show_quick_search_checkbox.setChecked(True)
            self.show_recent_files_checkbox.setChecked(True)
            self.recent_files_count_spinbox.setValue(5)
            self.tray_animations_checkbox.setChecked(True)
            self.balloon_notifications_checkbox.setChecked(True)
    
    def accept(self):
        """确定按钮点击处理"""
        # 保存所有设置
        self._save_settings()
        
        # 发出设置更新信号
        self.settings_updated_signal.emit()
        
        QMessageBox.information(self, "设置成功", "托盘设置已保存成功！")
        super().accept()
    
    def _save_settings(self):
        """保存设置并关闭对话框"""
        # 保存托盘显示设置
        self.settings.setValue("tray/show_icon", self.show_tray_icon_checkbox.isChecked())
        self.settings.setValue("tray/notifications", self.tray_notifications_checkbox.isChecked())
        
        # 保存窗口行为设置
        self.settings.setValue("tray/close_to_tray", self.close_to_tray_checkbox.isChecked())
        self.settings.setValue("tray/minimize_to_tray", self.minimize_to_tray_checkbox.isChecked())
        self.settings.setValue("startup/minimized", self.start_minimized_checkbox.isChecked())
        
        # 保存托盘菜单设置
        self.settings.setValue("tray/show_quick_search", self.show_quick_search_checkbox.isChecked())
        self.settings.setValue("tray/show_recent_files", self.show_recent_files_checkbox.isChecked())
        self.settings.setValue("tray/recent_files_count", self.recent_files_count_spinbox.value())
        
        # 保存动画和效果设置
        self.settings.setValue("tray/animations", self.tray_animations_checkbox.isChecked())
        self.settings.setValue("tray/balloon_notifications", self.balloon_notifications_checkbox.isChecked())
        
        # 同步设置
        self.settings.sync()
    
    def reject(self):
        """取消按钮点击处理"""
        super().reject() 