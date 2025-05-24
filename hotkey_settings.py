"""
热键设置对话框模块
"""

import os
import sys
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, 
                              QGroupBox, QPushButton, QMessageBox, QLabel,
                              QKeySequenceEdit, QTableWidget, QTableWidgetItem,
                              QHeaderView, QComboBox, QWidget)
from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QKeySequence


class HotkeySettingsDialog(QDialog):
    """热键设置对话框"""
    
    # 热键设置更新信号
    hotkey_updated_signal = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("热键设置")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # 初始化设置对象
        self.settings = QSettings("YourOrganizationName", "DocumentSearchToolPySide")
        
        # 预定义的热键动作
        self.hotkey_actions = {
            "show_main_window": "显示主窗口",
            "show_quick_search": "显示快速搜索",
            "hide_window": "隐藏窗口",
            "start_search": "开始搜索",
            "clear_search": "清空搜索框",
            "toggle_window": "切换窗口显示/隐藏"
        }
        
        self._create_ui()
        self._load_settings()
        
    def _create_ui(self):
        """创建用户界面"""
        layout = QVBoxLayout(self)
        
        # 热键启用设置
        enable_group = QGroupBox("热键功能")
        enable_layout = QVBoxLayout(enable_group)
        
        self.enable_hotkeys_checkbox = QCheckBox("启用全局热键")
        self.enable_hotkeys_checkbox.setToolTip("启用后可以在任何应用程序中使用设定的热键")
        enable_layout.addWidget(self.enable_hotkeys_checkbox)
        
        self.enable_on_startup_checkbox = QCheckBox("开机时自动启用热键")
        self.enable_on_startup_checkbox.setToolTip("程序启动时自动注册并启用热键")
        enable_layout.addWidget(self.enable_on_startup_checkbox)
        
        # 热键配置表格
        config_group = QGroupBox("热键配置")
        config_layout = QVBoxLayout(config_group)
        
        # 创建表格
        self.hotkey_table = QTableWidget()
        self.hotkey_table.setColumnCount(3)
        self.hotkey_table.setHorizontalHeaderLabels(["功能", "热键", "启用"])
        
        # 设置表格列宽
        header = self.hotkey_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # 设置表格行为
        self.hotkey_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.hotkey_table.setAlternatingRowColors(True)
        
        config_layout.addWidget(self.hotkey_table)
        
        # 填充表格
        self._populate_hotkey_table()
        
        # 热键提示信息
        info_group = QGroupBox("使用说明")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(
            "• 点击热键列可以修改快捷键组合\n"
            "• 建议使用 Ctrl+Alt 或 Ctrl+Shift 组合避免冲突\n"
            "• 热键在所有应用程序中都有效\n"
            "• 修改后立即生效，无需重启应用程序"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #666666; font-size: 9pt;")
        info_layout.addWidget(info_text)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reset_button = QPushButton("重置为默认")
        self.test_button = QPushButton("测试热键")
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.test_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        # 添加所有组件到主布局
        layout.addWidget(enable_group)
        layout.addWidget(config_group)
        layout.addWidget(info_group)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        # 连接信号
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.reset_button.clicked.connect(self._reset_to_defaults)
        self.test_button.clicked.connect(self._test_hotkeys)
        self.enable_hotkeys_checkbox.toggled.connect(self._on_enable_hotkeys_toggled)
        
    def _populate_hotkey_table(self):
        """填充热键配置表格"""
        self.hotkey_table.setRowCount(len(self.hotkey_actions))
        
        row = 0
        for action_id, action_name in self.hotkey_actions.items():
            # 功能名称
            name_item = QTableWidgetItem(action_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.hotkey_table.setItem(row, 0, name_item)
            
            # 热键输入
            hotkey_edit = QKeySequenceEdit()
            hotkey_edit.setToolTip("点击此处输入新的热键组合")
            self.hotkey_table.setCellWidget(row, 1, hotkey_edit)
            
            # 启用复选框
            enable_checkbox = QCheckBox()
            enable_checkbox.setChecked(True)
            # 创建一个容器widget来居中复选框
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(enable_checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.hotkey_table.setCellWidget(row, 2, checkbox_widget)
            
            # 存储action_id到widget的映射
            hotkey_edit.setProperty("action_id", action_id)
            enable_checkbox.setProperty("action_id", action_id)
            
            row += 1
    
    def _on_enable_hotkeys_toggled(self, checked):
        """当启用热键复选框状态改变时"""
        # 启用/禁用表格
        self.hotkey_table.setEnabled(checked)
        self.test_button.setEnabled(checked)
        
    def _load_settings(self):
        """加载当前设置"""
        # 加载热键启用设置
        enable_hotkeys = self.settings.value("hotkeys/enabled", True, type=bool)
        self.enable_hotkeys_checkbox.setChecked(enable_hotkeys)
        
        enable_on_startup = self.settings.value("hotkeys/enable_on_startup", True, type=bool)
        self.enable_on_startup_checkbox.setChecked(enable_on_startup)
        
        # 加载各个热键配置
        for row in range(self.hotkey_table.rowCount()):
            hotkey_edit = self.hotkey_table.cellWidget(row, 1)
            checkbox_widget = self.hotkey_table.cellWidget(row, 2)
            enable_checkbox = checkbox_widget.findChild(QCheckBox)
            
            action_id = hotkey_edit.property("action_id")
            
            # 加载热键序列
            hotkey_seq = self.settings.value(f"hotkeys/{action_id}", "", type=str)
            if hotkey_seq:
                hotkey_edit.setKeySequence(QKeySequence(hotkey_seq))
            else:
                # 设置默认热键
                default_hotkey = self._get_default_hotkey(action_id)
                if default_hotkey:
                    hotkey_edit.setKeySequence(QKeySequence(default_hotkey))
            
            # 加载启用状态
            enabled = self.settings.value(f"hotkeys/{action_id}_enabled", True, type=bool)
            enable_checkbox.setChecked(enabled)
        
        # 更新控件状态
        self._on_enable_hotkeys_toggled(enable_hotkeys)
        
    def _get_default_hotkey(self, action_id):
        """获取默认热键"""
        defaults = {
            "show_main_window": "Ctrl+Alt+S",
            "show_quick_search": "Ctrl+Alt+Q",
            "hide_window": "Ctrl+Alt+H",
            "start_search": "Ctrl+Alt+F",
            "clear_search": "Ctrl+Alt+C",
            "toggle_window": "Ctrl+Alt+T"
        }
        return defaults.get(action_id, "")
        
    def _reset_to_defaults(self):
        """重置为默认热键"""
        reply = QMessageBox.question(self, "重置热键", 
                                   "确定要重置所有热键为默认值吗？",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            for row in range(self.hotkey_table.rowCount()):
                hotkey_edit = self.hotkey_table.cellWidget(row, 1)
                checkbox_widget = self.hotkey_table.cellWidget(row, 2)
                enable_checkbox = checkbox_widget.findChild(QCheckBox)
                
                action_id = hotkey_edit.property("action_id")
                default_hotkey = self._get_default_hotkey(action_id)
                
                if default_hotkey:
                    hotkey_edit.setKeySequence(QKeySequence(default_hotkey))
                    
                enable_checkbox.setChecked(True)
            
            # 重置启用设置
            self.enable_hotkeys_checkbox.setChecked(True)
            self.enable_on_startup_checkbox.setChecked(True)
            
    def _test_hotkeys(self):
        """测试热键设置"""
        # 收集当前设置的热键
        active_hotkeys = []
        for row in range(self.hotkey_table.rowCount()):
            hotkey_edit = self.hotkey_table.cellWidget(row, 1)
            checkbox_widget = self.hotkey_table.cellWidget(row, 2)
            enable_checkbox = checkbox_widget.findChild(QCheckBox)
            
            if enable_checkbox.isChecked():
                action_id = hotkey_edit.property("action_id")
                hotkey_seq = hotkey_edit.keySequence().toString()
                action_name = self.hotkey_actions[action_id]
                
                if hotkey_seq:
                    active_hotkeys.append(f"• {action_name}: {hotkey_seq}")
        
        if active_hotkeys:
            message = "当前启用的热键:\n\n" + "\n".join(active_hotkeys)
            message += "\n\n注意: 热键修改后立即生效，无需重启应用程序。"
        else:
            message = "没有启用任何热键。"
            
        QMessageBox.information(self, "热键测试", message)
        
    def accept(self):
        """确定按钮点击处理"""
        # 检查热键冲突
        if not self._check_hotkey_conflicts():
            return
            
        # 保存所有设置
        self._save_settings()
        
        # 发出设置更新信号
        self.hotkey_updated_signal.emit()
        
        QMessageBox.information(self, "设置成功", 
                              "热键设置已保存成功！\n\n注意: 热键修改立即生效，无需重启应用程序。")
        super().accept()
        
    def _check_hotkey_conflicts(self):
        """检查热键冲突"""
        hotkey_map = {}
        conflicts = []
        
        for row in range(self.hotkey_table.rowCount()):
            hotkey_edit = self.hotkey_table.cellWidget(row, 1)
            checkbox_widget = self.hotkey_table.cellWidget(row, 2)
            enable_checkbox = checkbox_widget.findChild(QCheckBox)
            
            if enable_checkbox.isChecked():
                action_id = hotkey_edit.property("action_id")
                hotkey_seq = hotkey_edit.keySequence().toString()
                action_name = self.hotkey_actions[action_id]
                
                if hotkey_seq:
                    if hotkey_seq in hotkey_map:
                        conflicts.append(f"热键 '{hotkey_seq}' 被以下功能重复使用:\n  • {hotkey_map[hotkey_seq]}\n  • {action_name}")
                    else:
                        hotkey_map[hotkey_seq] = action_name
        
        if conflicts:
            message = "检测到热键冲突:\n\n" + "\n\n".join(conflicts)
            message += "\n\n请修改冲突的热键后再保存。"
            QMessageBox.warning(self, "热键冲突", message)
            return False
            
        return True
        
    def _save_settings(self):
        """保存设置到QSettings"""
        # 保存热键启用设置
        self.settings.setValue("hotkeys/enabled", self.enable_hotkeys_checkbox.isChecked())
        self.settings.setValue("hotkeys/enable_on_startup", self.enable_on_startup_checkbox.isChecked())
        
        # 保存各个热键配置
        for row in range(self.hotkey_table.rowCount()):
            hotkey_edit = self.hotkey_table.cellWidget(row, 1)
            checkbox_widget = self.hotkey_table.cellWidget(row, 2)
            enable_checkbox = checkbox_widget.findChild(QCheckBox)
            
            action_id = hotkey_edit.property("action_id")
            hotkey_seq = hotkey_edit.keySequence().toString()
            enabled = enable_checkbox.isChecked()
            
            self.settings.setValue(f"hotkeys/{action_id}", hotkey_seq)
            self.settings.setValue(f"hotkeys/{action_id}_enabled", enabled)
        
        # 同步设置
        self.settings.sync()
        
    def reject(self):
        """取消按钮点击处理"""
        super().reject()


# 测试代码
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = HotkeySettingsDialog()
    dialog.exec()
    
    # 打印结果
    print("\n热键配置:")
    for name, config in dialog.settings.allKeys():
        if name.startswith("hotkeys/"):
            print(f"  {name}: {dialog.settings.value(name)}")
        
    sys.exit(0) 