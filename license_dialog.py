"""
许可证激活对话框 - 用于输入和验证许可证密钥
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFormLayout, QGroupBox, QApplication
)
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QFont

from license_manager import get_license_manager, LicenseStatus, Features
from license_activation import activate_license
from device_manager_dialog import DeviceManagerDialog
import datetime

class LicenseDialog(QDialog):
    license_status_updated_signal = Signal()
    """许可证激活对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("许可证管理")
        self.setMinimumWidth(500)
        self.license_manager = get_license_manager()
        
        # 创建UI元素
        self._create_ui()
        
        # 更新界面显示
        self._update_license_info_display()
    
    def _create_ui(self):
        """创建用户界面组件"""
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 当前许可证状态区域
        status_group = QGroupBox("当前许可证状态")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel()
        self.status_label.setTextFormat(Qt.RichText)
        self.status_label.setWordWrap(True)
        font = self.status_label.font()
        font.setPointSize(font.pointSize() + 1)
        self.status_label.setFont(font)
        
        status_layout.addWidget(self.status_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 停用许可证按钮
        self.deactivate_button = QPushButton("停用许可证")
        self.deactivate_button.clicked.connect(self._deactivate_license)
        button_layout.addWidget(self.deactivate_button)
        
        # 设备管理按钮
        self.manage_devices_button = QPushButton("管理设备")
        self.manage_devices_button.clicked.connect(self._open_device_manager)
        button_layout.addWidget(self.manage_devices_button)
        
        status_layout.addLayout(button_layout)
        layout.addWidget(status_group)
        
        # 激活区域
        activation_group = QGroupBox("激活许可证")
        activation_layout = QVBoxLayout(activation_group)
        
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        # 许可证密钥输入框
        self.key_entry = QLineEdit()
        self.key_entry.setPlaceholderText("输入激活码 (例如: WZS-XXXX-XXXX-XXXX)")
        form_layout.addRow("激活码:", self.key_entry)
        
        activation_layout.addLayout(form_layout)
        
        # 激活按钮
        activate_button_layout = QHBoxLayout()
        activate_button_layout.addStretch()
        
        self.activate_button = QPushButton("激活")
        self.activate_button.setMinimumWidth(120)
        self.activate_button.clicked.connect(self._activate_license)
        activate_button_layout.addWidget(self.activate_button)
        
        activation_layout.addLayout(activate_button_layout)
        layout.addWidget(activation_group)
        
        # 购买信息区域
        purchase_group = QGroupBox("获取许可证")
        purchase_layout = QVBoxLayout(purchase_group)
        
        purchase_info = QLabel(
            "如果您还没有激活码，可以通过官方渠道购买：<br>"
            "<a href='https://azariasy.github.io/-wen-zhi-sou-website/index.html'>https://azariasy.github.io/-wen-zhi-sou-website/index.html</a>"
        )
        purchase_info.setOpenExternalLinks(True)
        purchase_info.setTextFormat(Qt.RichText)
        purchase_layout.addWidget(purchase_info)
        
        # 添加专业版功能列表
        features_group = QGroupBox("专业版功能")
        features_layout = QVBoxLayout(features_group)
        
        features_list = QLabel(
            "<ul>"
            "<li><b>📋 PDF文档支持</b> - PDF文本提取和OCR识别</li>"
            "<li><b>📝 Markdown文件支持</b> - 完整的MD文档索引和搜索</li>"
            "<li><b>📧 邮件文件支持</b> - EML和MSG邮件文件解析</li>"
            "<li><b>🎬 多媒体文件索引</b> - 视频、音频、图片文件名搜索</li>"
            "<li><b>🔍 高级搜索功能</b> - 通配符搜索 (*, ?) 和精确匹配</li>"
            "<li><b>🗂️ 文件夹树导航</b> - 可视化结果分组和导航</li>"
            "<li><b>🎨 多种界面主题</b> - 现代蓝、现代紫、现代红、现代橙</li>"
            "<li><b>📁 无限源目录</b> - 不限制索引目录数量</li>"
            "<li><b>⚡ 优先技术支持</b> - 专业版用户专属客服</li>"
            "<li><b>💻 多设备激活</b> - 1台/3台/6台设备选择</li>"
            "</ul>"
            "<p style='color: #666; font-size: 12px; margin-top: 15px;'>"
            "<b>基础版包含：</b>TXT、Word、Excel、PPT、HTML、RTF、ZIP、RAR文件支持<br>"
            "<b>专业版独有：</b>PDF、Markdown、邮件文件、多媒体文件名索引等高级功能"
            "</p>"
        )
        features_list.setTextFormat(Qt.RichText)
        features_layout.addWidget(features_list)
        
        layout.addWidget(purchase_group)
        layout.addWidget(features_group)
        
        # 关闭按钮
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        self.close_button = QPushButton("关闭")
        self.close_button.setMinimumWidth(100)
        self.close_button.clicked.connect(self.accept)
        close_layout.addWidget(self.close_button)
        
        layout.addLayout(close_layout)
    
    def _update_license_info_display(self):
        """更新许可证信息显示"""
        license_status = self.license_manager.get_license_status()
        license_info = self.license_manager.get_license_info()
        
        if license_status == LicenseStatus.ACTIVE:
            # 已激活
            key = license_info.get("key", "")
            truncated_key = key[:8] + "..." if key else ""
            
            email = license_info.get("user_email", "")
            
            expiration_date = "永久有效"
            days_left = ""
            
            if license_info.get("expiration_date"):
                try:
                    expiry_date = datetime.datetime.fromisoformat(license_info.get("expiration_date"))
                    expiration_date = expiry_date.strftime("%Y-%m-%d")
                    days_left = license_info.get("days_left", "")
                    days_left = f"（剩余 {days_left} 天）" if days_left else ""
                except (ValueError, TypeError):
                    pass
            
            # 获取设备信息
            max_devices = license_info.get("max_devices", 1)
            current_devices_count = len(license_info.get("activated_devices", []))
            
            status_html = f"""
            <font color='green'><b>已激活专业版</b></font><br>
            <b>激活码:</b> {truncated_key}<br>
            <b>用户:</b> {email}<br>
            <b>有效期至:</b> {expiration_date} {days_left}<br>
            <b>设备数:</b> {current_devices_count}/{max_devices}
            """
            
            self.deactivate_button.setEnabled(True)
            self.manage_devices_button.setEnabled(True)
            self.activate_button.setEnabled(False)
            self.key_entry.setEnabled(False)
            
            self.status_label.setText(status_html)
        elif license_status == LicenseStatus.EXPIRED:
            # 已过期
            key = license_info.get("key", "")
            truncated_key = key[:8] + "..." if key else ""
            
            expiration_date = "未知"
            if license_info.get("expiration_date"):
                try:
                    expiry_date = datetime.datetime.fromisoformat(license_info.get("expiration_date"))
                    expiration_date = expiry_date.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    pass
            
            status_html = f"""
            <font color='red'><b>许可证已过期</b></font><br>
            <b>激活码:</b> {truncated_key}<br>
            <b>过期日期:</b> {expiration_date}<br>
            请重新激活或购买新的许可证
            """
            
            self.deactivate_button.setEnabled(True)
            self.manage_devices_button.setEnabled(False)
            self.activate_button.setEnabled(True)
            self.key_entry.setEnabled(True)
        else:
            # 未激活或其他状态
            status_html = """
            <font color='blue'><b>免费版</b></font><br>
            您正在使用免费版。<br>
            激活专业版以使用所有功能。
            """
            
            self.deactivate_button.setEnabled(False)
            self.manage_devices_button.setEnabled(False)
            self.activate_button.setEnabled(True)
            self.key_entry.setEnabled(True)
        
        self.status_label.setText(status_html)
    
    def _activate_license(self):
        """激活许可证"""
        license_key_input = self.key_entry.text().strip()
        
        if not license_key_input:
            QMessageBox.warning(self, "输入错误", "请输入激活码")
            return
        
        # 确认是否继续
        reply = QMessageBox.question(
            self,
            "确认激活",
            "正在连接激活服务器进行验证，请确保网络连接正常。\n\n是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply != QMessageBox.Yes:
            return 

        # 调用在线激活API
        api_result = activate_license(license_key_input)

        if api_result and api_result.get("success"):
            # 从API响应中获取日期信息
            activation_date_to_store = api_result.get("purchaseDate", "") 
            purchase_date_from_api = api_result.get("purchaseDate", "")
            
            if not activation_date_to_store:
                # 如果API没有返回日期，则使用当前日期
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                activation_date_to_store = today
                purchase_date_from_api = today
            
            # 获取用户邮箱，确保正确处理
            user_email = api_result.get("user_email") or api_result.get("userEmail") or ""
            print(f"从API获取用户邮箱: {user_email}, 原始数据: {api_result}")
            
            # 构建许可证详细信息并保存
            license_details = {
                "key": license_key_input,
                "user_email": user_email,
                "product_id": api_result.get("product_id") or api_result.get("productId") or "",
                "activation_date": activation_date_to_store, 
                "purchase_date": purchase_date_from_api, 
                "status": LicenseStatus.ACTIVE,
                "max_devices": api_result.get("max_devices", 1),
                "activated_devices": api_result.get("activated_devices", []),
                "device_id": api_result.get("device_id", "")
            }
            self.license_manager.update_and_save_license_details(license_details)
            # -----
            QMessageBox.information(self, "激活成功", api_result.get("message", "许可证已成功激活！"))
            self._update_license_info_display() 
            self.license_status_updated_signal.emit() 
            self.key_entry.clear()

        elif api_result: 
            QMessageBox.warning(self, "激活失败", 
                                api_result.get("message", "激活失败，请检查您的激活码或网络连接。"))
        else: 
            QMessageBox.critical(self, "激活错误", "激活服务未返回有效结果或发生未知错误。")
        
        # 尝试激活父窗口并设置焦点
        self.activateWindow()
        self.raise_()
        self.key_entry.setFocus()
    
    def _deactivate_license(self):
        """停用许可证"""
        reply = QMessageBox.question(
            self,
            "确认停用",
            "您确定要停用当前许可证吗？\n这将会禁用所有专业版功能。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.license_manager.deactivate_license()
            
            if success:
                QMessageBox.information(self, "停用成功", message)
                self._update_license_info_display()
                self.license_status_updated_signal.emit()
            else:
                QMessageBox.warning(self, "停用失败", message)
    
    def _open_device_manager(self):
        """打开设备管理对话框"""
        # 检查许可证状态
        if self.license_manager.get_license_status() != LicenseStatus.ACTIVE:
            QMessageBox.warning(self, "无效操作", "只有在许可证激活状态下才能管理设备")
            return
        
        # 创建并显示设备管理对话框
        device_dialog = DeviceManagerDialog(self)
        device_dialog.device_list_updated_signal.connect(self._update_license_info_display)
        device_dialog.exec()

# 测试代码（独立运行时使用）
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = LicenseDialog()
    dialog.exec() 