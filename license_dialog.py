"""
许可证激活对话框 - 用于输入和验证许可证密钥
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont

from license_manager import get_license_manager, LicenseStatus, Features

class LicenseDialog(QDialog):
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
        """创建对话框UI元素"""
        layout = QVBoxLayout(self)
        
        # 创建许可证信息组
        info_group = QGroupBox("许可证状态")
        info_layout = QFormLayout(info_group)
        
        # 状态标签
        self.status_label = QLabel("未激活")
        status_font = self.status_label.font()
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        info_layout.addRow("当前状态:", self.status_label)
        
        # 许可证密钥
        self.key_label = QLabel("")
        info_layout.addRow("许可证密钥:", self.key_label)
        
        # 激活日期
        self.activation_date_label = QLabel("")
        info_layout.addRow("激活日期:", self.activation_date_label)
        
        # 过期日期
        self.expiration_date_label = QLabel("")
        info_layout.addRow("过期日期:", self.expiration_date_label)
        
        # 剩余天数
        self.days_left_label = QLabel("")
        info_layout.addRow("剩余天数:", self.days_left_label)
        
        # 用户名
        self.user_name_label = QLabel("")
        info_layout.addRow("用户名:", self.user_name_label)
        
        # 用户邮箱
        self.user_email_label = QLabel("")
        info_layout.addRow("用户邮箱:", self.user_email_label)
        
        layout.addWidget(info_group)
        
        # 创建功能列表组
        features_group = QGroupBox("功能可用性")
        features_layout = QFormLayout(features_group)
        
        # PDF支持
        self.pdf_support_label = QLabel("")
        features_layout.addRow("PDF支持 (文本+OCR):", self.pdf_support_label)
        
        # Markdown支持
        self.md_support_label = QLabel("")
        features_layout.addRow("Markdown支持:", self.md_support_label)
        
        # 邮件支持
        self.email_support_label = QLabel("")
        features_layout.addRow("邮件支持 (EML/MSG):", self.email_support_label)
        
        # 压缩包支持
        self.archive_support_label = QLabel("")
        features_layout.addRow("压缩包支持 (ZIP/RAR):", self.archive_support_label)
        
        # 通配符搜索
        self.wildcards_label = QLabel("")
        features_layout.addRow("通配符搜索:", self.wildcards_label)
        
        # 无限制目录
        self.unlimited_dirs_label = QLabel("")
        features_layout.addRow("无限制源目录:", self.unlimited_dirs_label)
        
        # 高级主题
        self.advanced_themes_label = QLabel("")
        features_layout.addRow("高级主题:", self.advanced_themes_label)
        
        layout.addWidget(features_group)
        
        # 创建激活表单组
        activation_group = QGroupBox("激活许可证")
        activation_layout = QFormLayout(activation_group)
        
        # 许可证密钥输入
        self.key_entry = QLineEdit()
        self.key_entry.setPlaceholderText("格式：XXXX-XXXX-XXXX-XXXX")
        activation_layout.addRow("许可证密钥:", self.key_entry)
        
        # 用户名输入（可选）
        self.user_name_entry = QLineEdit()
        self.user_name_entry.setPlaceholderText("可选")
        activation_layout.addRow("用户名:", self.user_name_entry)
        
        # 用户邮箱输入（可选）
        self.user_email_entry = QLineEdit()
        self.user_email_entry.setPlaceholderText("可选")
        activation_layout.addRow("用户邮箱:", self.user_email_entry)
        
        layout.addWidget(activation_group)
        
        # 按钮行
        button_layout = QHBoxLayout()
        
        self.activate_button = QPushButton("激活许可证")
        self.activate_button.clicked.connect(self._activate_license)
        
        self.deactivate_button = QPushButton("停用许可证")
        self.deactivate_button.clicked.connect(self._deactivate_license)
        
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.activate_button)
        button_layout.addWidget(self.deactivate_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def _update_license_info_display(self):
        """更新许可证信息显示"""
        license_info = self.license_manager.get_license_info()
        status = license_info["status"]
        
        # 更新状态标签
        if status == LicenseStatus.ACTIVE:
            self.status_label.setText("已激活 (专业版)")
            self.status_label.setStyleSheet("color: green")
        elif status == LicenseStatus.EXPIRED:
            self.status_label.setText("已过期 (专业版)")
            self.status_label.setStyleSheet("color: orange")
        else:
            self.status_label.setText("未激活 (免费版)")
            self.status_label.setStyleSheet("color: gray")
        
        # 更新其他信息
        self.key_label.setText(license_info["key"] or "无")
        self.activation_date_label.setText(license_info.get("activation_date_display", "无"))
        
        if status == LicenseStatus.ACTIVE:
            self.expiration_date_label.setText(license_info.get("expiration_date_display", "无"))
            self.days_left_label.setText(f"{license_info.get('days_left', 0)} 天")
        else:
            self.expiration_date_label.setText("无" if status == LicenseStatus.INACTIVE else license_info.get("expiration_date_display", "无"))
            self.days_left_label.setText("0 天" if status == LicenseStatus.EXPIRED else "无")
        
        self.user_name_label.setText(license_info["user_name"] or "无")
        self.user_email_label.setText(license_info["user_email"] or "无")
        
        # 更新功能可用性
        self._update_feature_availability()
        
        # 更新按钮状态
        self.deactivate_button.setEnabled(status == LicenseStatus.ACTIVE)
    
    def _update_feature_availability(self):
        """更新功能可用性显示"""
        def _set_availability_label(label, feature_name):
            is_available = self.license_manager.is_feature_available(feature_name)
            label.setText("可用" if is_available else "不可用")
            label.setStyleSheet("color: green" if is_available else "color: red")
        
        _set_availability_label(self.pdf_support_label, Features.PDF_SUPPORT)
        _set_availability_label(self.md_support_label, Features.MARKDOWN_SUPPORT)
        _set_availability_label(self.email_support_label, Features.EMAIL_SUPPORT)
        _set_availability_label(self.archive_support_label, Features.ARCHIVE_SUPPORT)
        _set_availability_label(self.wildcards_label, Features.WILDCARDS)
        _set_availability_label(self.unlimited_dirs_label, Features.UNLIMITED_DIRS)
        _set_availability_label(self.advanced_themes_label, Features.ADVANCED_THEMES)
    
    def _activate_license(self):
        """激活许可证"""
        license_key = self.key_entry.text().strip()
        user_name = self.user_name_entry.text().strip()
        user_email = self.user_email_entry.text().strip()
        
        if not license_key:
            QMessageBox.warning(self, "输入错误", "请输入许可证密钥。")
            return
        
        success, message = self.license_manager.activate_license(
            license_key, user_name, user_email
        )
        
        if success:
            QMessageBox.information(self, "激活成功", message)
            self._update_license_info_display()
            # 清空输入字段
            self.key_entry.clear()
            self.user_name_entry.clear()
            self.user_email_entry.clear()
        else:
            QMessageBox.warning(self, "激活失败", message)
    
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
            else:
                QMessageBox.warning(self, "停用失败", message)

# 测试代码（独立运行时使用）
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = LicenseDialog()
    dialog.exec() 