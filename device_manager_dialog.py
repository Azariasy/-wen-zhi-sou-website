"""
设备管理对话框 - 用于查看和管理已激活的设备
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QPushButton, QMessageBox, QTableWidgetItem, QHeaderView,
    QGroupBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont, QColor
import datetime

from license_manager import get_license_manager

class DeviceManagerDialog(QDialog):
    """设备管理对话框，显示已激活的设备列表并允许管理"""
    
    # 设备列表刷新信号
    device_list_updated_signal = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设备管理")
        self.setMinimumWidth(550)
        self.setMinimumHeight(350)
        
        # 获取许可证管理实例
        self.license_manager = get_license_manager()
        
        # 创建UI组件
        self._create_ui()
        
        # 加载设备列表
        self._load_device_list()
    
    def _create_ui(self):
        """创建用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 许可证信息区域
        license_group = QGroupBox("许可证信息")
        license_layout = QVBoxLayout(license_group)
        
        # 许可证信息标签
        self.license_info_label = QLabel()
        self.license_info_label.setTextFormat(Qt.RichText)
        self.license_info_label.setWordWrap(True)
        license_layout.addWidget(self.license_info_label)
        
        # 添加到主布局
        main_layout.addWidget(license_group)
        
        # 设备列表区域
        devices_group = QGroupBox("已激活设备")
        devices_layout = QVBoxLayout(devices_group)
        
        # 设备表格
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(4)  # ID, 名称, 激活日期, 操作
        self.devices_table.setHorizontalHeaderLabels(["设备ID", "名称", "激活日期", "操作"])
        self.devices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.devices_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.devices_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.devices_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.devices_table.verticalHeader().setVisible(False)
        self.devices_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.devices_table.setEditTriggers(QTableWidget.NoEditTriggers)
        devices_layout.addWidget(self.devices_table)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        
        # 刷新按钮
        self.refresh_button = QPushButton("刷新列表")
        self.refresh_button.clicked.connect(self._load_device_list)
        buttons_layout.addWidget(self.refresh_button)
        
        # 添加一个弹性空间
        buttons_layout.addStretch()
        
        # 关闭按钮
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_button)
        
        devices_layout.addLayout(buttons_layout)
        
        # 添加到主布局
        main_layout.addWidget(devices_group)
    
    def _load_device_list(self):
        """加载设备列表"""
        # 获取设备信息
        device_info = self.license_manager.get_device_list()
        
        if not device_info:
            QMessageBox.warning(self, "错误", "无法获取设备列表信息")
            return
        
        # 获取许可证详细信息，用于补充可能缺失的数据
        license_info = self.license_manager.get_license_info()
        activation_date_display = license_info.get("activation_date_display", "")
        if not activation_date_display:
            activation_date_display = datetime.datetime.now().strftime("%Y-%m-%d")
            
        # 更新许可证信息标签
        max_devices = device_info.get("max_devices", 0)
        current_devices = device_info.get("current_devices", 0)
        license_info_html = f"""
        <b>许可证状态：</b>专业版（已激活）<br>
        <b>最多可激活设备数：</b>{max_devices}<br>
        <b>已激活设备数：</b>{current_devices}
        """
        self.license_info_label.setText(license_info_html)
        
        # 清空表格
        self.devices_table.setRowCount(0)
        
        # 填充设备数据
        device_list = device_info.get("device_list", [])
        
        # 如果设备列表为空但已激活设备数大于0，尝试从license_info中获取设备信息
        if not device_list and current_devices > 0:
            activated_devices = license_info.get("activated_devices", [])
            current_device_id = license_info.get("current_device_id", "")
            
            # 为每个设备ID创建一个设备信息项
            for device_id in activated_devices:
                # 检查是否为当前设备
                is_current = device_id == current_device_id
                device_list.append({
                    "id": device_id,
                    "name": "当前设备" if is_current else f"设备 {len(device_list) + 1}",
                    "activationDate": activation_date_display,
                    "isCurrentDevice": is_current
                })
        
        # 确保每个设备项都有激活日期
        for device in device_list:
            if not device.get("activationDate"):
                device["activationDate"] = activation_date_display
                
        self.devices_table.setRowCount(len(device_list))
        
        for row, device in enumerate(device_list):
            # 设备ID
            id_item = QTableWidgetItem(device.get("id", "")[:12] + "...")
            id_item.setData(Qt.UserRole, device.get("id"))
            self.devices_table.setItem(row, 0, id_item)
            
            # 设备名称
            name_item = QTableWidgetItem(device.get("name", f"设备 {row + 1}"))
            # 如果是当前设备，加粗显示
            if device.get("isCurrentDevice", False):
                font = name_item.font()
                font.setBold(True)
                name_item.setFont(font)
                name_item.setForeground(QColor(0, 128, 0))  # 绿色
            self.devices_table.setItem(row, 1, name_item)
            
            # 激活日期
            date_item = QTableWidgetItem(device.get("activationDate", "未知"))
            self.devices_table.setItem(row, 2, date_item)
            
            # 操作按钮
            if not device.get("isCurrentDevice", False):
                deactivate_button = QPushButton("解除绑定")
                deactivate_button.setProperty("device_id", device.get("id"))
                deactivate_button.clicked.connect(lambda checked=False, did=device.get("id"): self._deactivate_device(did))
                self.devices_table.setCellWidget(row, 3, deactivate_button)
            else:
                # 当前设备不能解除绑定
                current_label = QLabel("当前设备")
                current_label.setAlignment(Qt.AlignCenter)
                font = current_label.font()
                font.setItalic(True)
                current_label.setFont(font)
                self.devices_table.setCellWidget(row, 3, current_label)
        
        # 调整表格大小
        self.devices_table.resizeColumnsToContents()
        self.devices_table.resizeRowsToContents()
    
    def _deactivate_device(self, device_id):
        """解除设备绑定"""
        # 二次确认
        reply = QMessageBox.question(
            self,
            "确认解除绑定",
            f"确定要解除此设备的绑定吗？\n\n设备ID: {device_id[:12]}...\n\n解除绑定后，此设备将无法使用当前许可证，但可以在需要时重新激活。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 调用许可管理器解除设备绑定
            success, message = self.license_manager.deactivate_specific_device(device_id)
            
            if success:
                QMessageBox.information(self, "操作成功", message)
                # 重新加载设备列表
                self._load_device_list()
                # 发送设备列表更新信号
                self.device_list_updated_signal.emit()
            else:
                QMessageBox.warning(self, "操作失败", message)
    
    def showEvent(self, event):
        """当对话框显示时加载设备列表"""
        super().showEvent(event)
        self._load_device_list() 