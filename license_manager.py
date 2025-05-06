"""
许可证管理器 - 处理免费版和专业版的功能控制

此模块负责:
1. 验证许可证密钥
2. 存储授权状态
3. 检查特定功能是否可用（基于授权状态）
"""

import os
import json
import base64
import hashlib
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from PySide6.QtCore import QSettings

# 配置记录器
logger = logging.getLogger(__name__)

# 应用程序标识符（与主应用程序保持一致）
ORGANIZATION_NAME = "YourOrganizationName"  # 需要与主应用程序一致
APPLICATION_NAME = "DocumentSearchToolPySide"  # 需要与主应用程序一致

# 功能标识符
class Features:
    """功能标识符枚举"""
    # 专业版功能
    PDF_SUPPORT = "pdf_support"          # PDF文件支持（文本和OCR）
    MARKDOWN_SUPPORT = "md_support"       # Markdown文件支持
    EMAIL_SUPPORT = "email_support"       # 邮件文件支持（.eml和.msg）
    ARCHIVE_SUPPORT = "archive_support"   # 压缩包内容支持（zip和rar）
    WILDCARDS = "wildcards"               # 通配符搜索支持
    UNLIMITED_DIRS = "unlimited_dirs"     # 无限制源目录
    ADVANCED_THEMES = "advanced_themes"   # 高级主题支持
    
    # 工具方法
    @staticmethod
    def get_all_pro_features():
        """获取所有专业版功能的列表"""
        return [
            Features.PDF_SUPPORT,
            Features.MARKDOWN_SUPPORT,
            Features.EMAIL_SUPPORT,
            Features.ARCHIVE_SUPPORT,
            Features.WILDCARDS,
            Features.UNLIMITED_DIRS,
            Features.ADVANCED_THEMES
        ]

class LicenseStatus:
    """许可证状态枚举"""
    INACTIVE = "inactive"    # 未激活（免费版）
    ACTIVE = "active"        # 已激活（专业版）
    EXPIRED = "expired"      # 已过期（曾经是专业版）

class LicenseManager:
    """许可证管理器类，负责验证、存储和检查许可状态"""
    
    def __init__(self):
        """初始化许可证管理器"""
        self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        self._license_info = self._load_license_info()
        
    def _load_license_info(self):
        """从设置加载许可证信息"""
        # 默认许可证信息
        default_info = {
            "status": LicenseStatus.INACTIVE,
            "key": "",
            "activation_date": "",
            "expiration_date": "",
            "user_name": "",
            "user_email": ""
        }
        
        # 从设置加载
        encoded_info = self.settings.value("license/info", "")
        if not encoded_info:
            return default_info
            
        try:
            # 解码和解析保存的许可证信息
            decoded_base64 = base64.b64decode(encoded_info).decode('utf-8')
            # 解混淆：恢复替换的字符并反转字符串
            deobfuscated = decoded_base64.replace('*', '"').replace('#', ':')[::-1]
            license_info = json.loads(deobfuscated)
            
            # 验证加载的信息中包含所有必需的字段
            for key in default_info:
                if key not in license_info:
                    logger.warning(f"加载的许可证信息缺少字段: {key}")
                    license_info[key] = default_info[key]
            
            # 验证数据完整性
            if "_checksum" in license_info:
                stored_checksum = license_info.pop("_checksum")
                calculated_checksum = self._generate_checksum(license_info)
                if stored_checksum != calculated_checksum:
                    logger.warning("许可证信息校验和不匹配，可能已被篡改")
                    return default_info
            
            # 移除额外的内部字段
            if "_last_saved" in license_info:
                license_info.pop("_last_saved")
            
            # 检查许可证是否已过期
            if license_info["status"] == LicenseStatus.ACTIVE and license_info["expiration_date"]:
                try:
                    expiration_date = datetime.fromisoformat(license_info["expiration_date"])
                    if expiration_date < datetime.now():
                        logger.info("许可证已过期")
                        license_info["status"] = LicenseStatus.EXPIRED
                except ValueError:
                    logger.error(f"无效的过期日期格式: {license_info['expiration_date']}")
            
            return license_info
        except Exception as e:
            logger.error(f"加载许可证信息时出错: {e}")
            return default_info
    
    def _save_license_info(self):
        """保存许可证信息到设置"""
        try:
            # 添加校验信息
            info_to_save = self._license_info.copy()
            
            # 添加一个校验和，用于验证数据完整性
            checksum = self._generate_checksum(info_to_save)
            info_to_save["_checksum"] = checksum
            
            # 添加一个时间戳，用于追踪最后保存时间
            info_to_save["_last_saved"] = datetime.now().isoformat()
            
            # 编码许可证信息（使用base64和简单混淆）
            serialized = json.dumps(info_to_save)
            # 简单的混淆：将JSON字符串倒序并替换某些字符
            obfuscated = serialized[::-1].replace('"', '*').replace(':', '#')
            encoded = base64.b64encode(obfuscated.encode('utf-8')).decode('utf-8')
            
            # 保存到设置
            self.settings.setValue("license/info", encoded)
            logger.info("许可证信息已保存")
        except Exception as e:
            logger.error(f"保存许可证信息时出错: {e}")
    
    def activate_license(self, license_key, user_name="", user_email=""):
        """
        激活许可证
        
        Args:
            license_key: 许可证密钥
            user_name: 用户名（可选）
            user_email: 用户电子邮件（可选）
            
        Returns:
            tuple: (成功状态, 消息)
        """
        # 清理输入的许可证密钥（去除空格并转为大写）
        license_key = license_key.strip().upper()
        
        # 检查许可证密钥格式
        if not self._validate_key_format(license_key):
            return False, "无效的许可证密钥格式，请确保格式为：XXXX-XXXX-XXXX-XXXX"
        
        # 模拟简单的密钥检查
        # 在实际产品中，这里应该有更真实和安全的验证逻辑
        # 例如，检查密钥是否已被使用、是否在有效密钥列表中等
        
        # 检查是否为演示密钥（仅用于测试，限制某些功能或有效期）
        is_demo = license_key.startswith("DEMO")
        
        # 设置激活日期为当前日期
        activation_date = datetime.now()
        
        # 根据是否为演示密钥设置不同的过期日期
        if is_demo:
            # 演示密钥有效期为30天
            expiration_date = activation_date + timedelta(days=30)
        else:
            # 正常密钥有效期为一年
            expiration_date = activation_date + timedelta(days=365)
        
        # 更新许可证信息
        self._license_info.update({
            "status": LicenseStatus.ACTIVE,
            "key": license_key,
            "activation_date": activation_date.isoformat(),
            "expiration_date": expiration_date.isoformat(),
            "user_name": user_name,
            "user_email": user_email
        })
        
        # 保存更新后的许可证信息
        self._save_license_info()
        
        # 返回成功消息，根据是否为演示版显示不同的信息
        if is_demo:
            return True, f"演示版许可证已成功激活，有效期为30天，到期日期: {expiration_date.strftime('%Y-%m-%d')}"
        else:
            return True, f"许可证已成功激活，有效期至 {expiration_date.strftime('%Y-%m-%d')}"
    
    def deactivate_license(self):
        """
        停用当前许可证
        
        Returns:
            tuple: (成功状态, 消息)
        """
        if self._license_info["status"] == LicenseStatus.INACTIVE:
            return False, "没有激活的许可证可供停用"
        
        # 重置许可证信息
        self._license_info = {
            "status": LicenseStatus.INACTIVE,
            "key": "",
            "activation_date": "",
            "expiration_date": "",
            "user_name": "",
            "user_email": ""
        }
        
        # 保存更新后的许可证信息
        self._save_license_info()
        
        return True, "许可证已成功停用"
    
    def get_license_status(self):
        """
        获取当前许可证状态
        
        Returns:
            str: 当前许可证状态（LicenseStatus中的一个值）
        """
        return self._license_info["status"]
    
    def get_license_info(self):
        """
        获取许可证详细信息
        
        Returns:
            dict: 包含许可证详细信息的字典
        """
        info = self._license_info.copy()
        # 添加格式化的日期/用户友好显示
        if info["activation_date"]:
            try:
                activation_date = datetime.fromisoformat(info["activation_date"])
                info["activation_date_display"] = activation_date.strftime("%Y-%m-%d")
            except ValueError:
                info["activation_date_display"] = "未知"
                
        if info["expiration_date"]:
            try:
                expiration_date = datetime.fromisoformat(info["expiration_date"])
                info["expiration_date_display"] = expiration_date.strftime("%Y-%m-%d")
                # 计算剩余天数
                days_left = (expiration_date - datetime.now()).days
                info["days_left"] = max(0, days_left)
            except ValueError:
                info["expiration_date_display"] = "未知"
                info["days_left"] = 0
        
        return info
    
    def is_feature_available(self, feature_name):
        """
        检查特定功能是否可用
        
        Args:
            feature_name: 要检查的功能名称（从Features类获取）
            
        Returns:
            bool: 如果功能可用返回True，否则返回False
        """
        # 如果许可证处于活动状态，所有功能都可用
        if self._license_info["status"] == LicenseStatus.ACTIVE:
            return True
            
        # 对于免费版和过期版，需要检查该功能是否是专业版功能
        if feature_name in Features.get_all_pro_features():
            return False  # 专业版功能在免费版或过期版中不可用
            
        return True  # 非专业版功能始终可用
    
    def _validate_key_format(self, key):
        """
        验证许可证密钥格式
        
        Args:
            key: 要验证的许可证密钥
            
        Returns:
            bool: 如果格式正确返回True，否则返回False
        """
        # 如果密钥为空或格式不对，返回False
        if not key or len(key) != 19:  # 总长度应为19 (XXXX-XXXX-XXXX-XXXX)
            return False
            
        # 检查格式: XXXX-XXXX-XXXX-XXXX (四组字母数字，每组4个字符，中间用连字符分隔)
        import re
        if not re.match(r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$', key):
            return False
            
        # 简单的校验算法，确保密钥结构合理
        # 这里我们检查每个分段的第一个字符和最后一个字符的ASCII值之和是否为偶数
        # 这只是个简单的示例，实际产品中应该有更强的验证逻辑
        segments = key.split('-')
        for segment in segments:
            if len(segment) != 4:  # 再次检查每段长度，以防万一
                return False
                
            # 简单校验：第一个和最后一个字符的ASCII值之和应为偶数
            first_char_val = ord(segment[0])
            last_char_val = ord(segment[3])
            if (first_char_val + last_char_val) % 2 != 0:
                return False
                
        return True

    def _generate_checksum(self, data):
        """生成数据的校验和"""
        # 创建一个排序的键值对列表，确保校验和的一致性
        sorted_items = sorted([(str(k), str(v)) for k, v in data.items() if not k.startswith("_")])
        
        # 将键值对连接成一个字符串
        concat_str = "".join([f"{k}:{v}" for k, v in sorted_items])
        
        # 使用SHA-256生成校验和
        return hashlib.sha256(concat_str.encode('utf-8')).hexdigest()[:16]  # 使用前16个字符作为校验和

# 单例实例
_license_manager_instance = None

def get_license_manager():
    """
    获取LicenseManager的单例实例
    
    Returns:
        LicenseManager: 许可证管理器实例
    """
    global _license_manager_instance
    if _license_manager_instance is None:
        _license_manager_instance = LicenseManager()
    return _license_manager_instance 