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
    FOLDER_TREE = "folder_tree"           # 搜索结果文件夹树视图
    
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
            Features.ADVANCED_THEMES,
            Features.FOLDER_TREE
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
            "user_email": "",
            "max_devices": 1,              # 默认最大设备数
            "current_device_id": "",       # 当前设备ID
            "activated_devices": []        # 已激活设备列表
        }
        
        # 记录设置文件路径（调试信息）
        path = self.settings.fileName()
        logger.debug(f"正在从设置文件加载许可证信息: {path}")
        print(f"DEBUG: 正在从设置文件加载许可证: {path}")
        
        # 从设置加载
        encoded_info = self.settings.value("license/info", "")
        if not encoded_info:
            logger.warning("设置中不存在许可证信息，使用默认值")
            print("DEBUG: 未找到许可证信息，使用默认值（未激活状态）")
            return default_info
        
        # 从加密存储中解码
        try:
            decoded_json = self._decrypt_license_data(encoded_info)
            license_info = json.loads(decoded_json)
            
            # 确保所有必要的字段都存在
            for key in default_info:
                if key not in license_info:
                    license_info[key] = default_info[key]
            
            # 检查许可证状态和有效期
            if license_info["status"] == LicenseStatus.ACTIVE:
                # 检查是否过期
                if license_info["expiration_date"]:
                    try:
                        # 尝试将过期日期解析为datetime对象
                        expiration_date = datetime.fromisoformat(license_info["expiration_date"])
                        now = datetime.now()
                        
                        # 如果过期，更新状态为过期
                        if now > expiration_date:
                            license_info["status"] = LicenseStatus.EXPIRED
                            logger.info("许可证已过期")
                            print(f"DEBUG: 许可证已过期。过期日期: {expiration_date.strftime('%Y-%m-%d')}")
                        else:
                            # 计算剩余天数
                            days_left = (expiration_date - now).days
                            license_info["days_left"] = days_left
                            logger.info(f"许可证有效，剩余 {days_left} 天")
                            print(f"DEBUG: 许可证有效。还剩余: {days_left} 天")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"解析过期日期时出错: {e}")
                        print(f"DEBUG: 解析过期日期时出错: {e}")
                        # 如果无法解析日期，假设许可证仍然有效
                        license_info["days_left"] = "未知"
                else:
                    # 如果没有过期日期，表示永久许可证
                    license_info["days_left"] = "永久"
                    logger.info("永久许可证")
                    print("DEBUG: 许可证是永久有效的")
            
            return license_info
            
        except Exception as e:
            logger.error(f"解码许可证信息时出错: {e}")
            print(f"DEBUG: 解码许可证信息出错: {e}")
            # 出错时返回默认许可证信息
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
            
            # 保存前记录状态和密钥信息（用于调试）
            key_info = self._license_info.get('key', '')
            key_truncated = key_info[:8] + '...' if key_info else 'None'
            logger.info(f"正在保存许可证信息，当前状态: {self._license_info['status']}, 密钥: {key_truncated}")
            
            # 保存到设置
            self.settings.setValue("license/info", encoded)
            
            # 确保立即写入磁盘
            sync_result = self.settings.sync()
            logger.info(f"许可证信息已保存并同步到磁盘，sync()返回: {sync_result}")
            
            # 验证保存是否成功
            saved_value = self.settings.value("license/info", "")
            if saved_value == encoded:
                logger.info("许可证信息验证成功，已正确保存到设置中")
            else:
                logger.warning("许可证信息验证失败，保存的值与原始值不匹配")
                
            # 打印当前保存的内容用于调试
            status = self._license_info['status']
            logger.debug(f"保存的许可证状态: {status}")
            if status == LicenseStatus.ACTIVE:
                exp_date = self._license_info.get('expiration_date', '未设置')
                logger.debug(f"保存的许可证有效期: {exp_date}")
                
            # 打印设置文件路径（仅用于调试）
            path = self.settings.fileName()
            logger.debug(f"设置文件路径: {path}")
            print(f"DEBUG: 许可证信息已保存到: {path}")
            
            return True
            
        except Exception as e:
            logger.error(f"保存许可证信息时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            print(f"ERROR: 保存许可证信息失败: {e}")
            return False
    
    def _decrypt_license_data(self, encoded_info):
        """
        解密存储的许可证信息
        
        Args:
            encoded_info: 编码后的许可证信息
            
        Returns:
            str: 解码后的JSON字符串
        """
        try:
            # 解码base64
            decoded_bytes = base64.b64decode(encoded_info)
            # 解码为字符串
            obfuscated = decoded_bytes.decode('utf-8')
            # 反向混淆：还原字符替换并倒序回来
            serialized = obfuscated.replace('*', '"').replace('#', ':')[::-1]
            
            return serialized
        except Exception as e:
            logger.error(f"解码许可证数据时出错: {e}")
            raise
    
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
        
        # 验证是否为演示密钥
        demo_prefix = "DEMO-"
        is_demo = license_key.startswith(demo_prefix)
        if is_demo:
            logger.info(f"检测到演示版密钥: {license_key}")
            license_key = license_key[len(demo_prefix):]  # 去掉演示前缀
        
        # 获取当前日期作为激活日期
        activation_date = datetime.now()
        
        # 所有许可证都设为永久有效
        expiration_date = None
        
        # 更新许可证信息
        self._license_info.update({
            "status": LicenseStatus.ACTIVE,
            "key": license_key,
            "activation_date": activation_date.isoformat(),
            "expiration_date": "",
            "user_name": user_name,
            "user_email": user_email
        })
        
        # 保存更新后的许可证信息
        self._save_license_info()
        
        # 调试信息：记录激活成功
        logger.info(f"许可证已成功激活。密钥: {license_key}, 状态: {self._license_info['status']}, 永久有效")
        print(f"DEBUG: 许可证成功激活。状态: {self._license_info['status']}, 永久有效")
        
        # 返回成功消息，根据是否为演示版显示不同的信息
        if is_demo:
            return True, f"演示版许可证已成功激活，永久有效"
        else:
            return True, f"许可证已成功激活，永久有效"
    
    def update_and_save_license_details(self, details_dict):
        """
        用从API成功激活后获得的详细信息更新并保存许可证状态。

        Args:
            details_dict (dict): 包含许可证详细信息的字典，
                                 例如: {"key": "...", "user_email": "...", 
                                        "product_id": "...", "activation_date": "YYYY-MM-DD",
                                        "status": LicenseStatus.ACTIVE, ...}
        Returns:
            bool: 如果更新和保存成功则返回True，否则返回False。
        """
        logger.info(f"正在使用API返回的详细信息更新许可证: {details_dict}")
        try:
            # 更新内部许可证信息
            self._license_info["status"] = details_dict.get("status", LicenseStatus.INACTIVE)
            self._license_info["key"] = details_dict.get("key", "").upper() # 确保密钥大写
            
            # 处理激活日期
            activation_date_str = details_dict.get("activation_date", "")
            if activation_date_str:
                 # 尝试将多种可能的日期时间格式转换为 YYYY-MM-DD
                try:
                    if 'T' in activation_date_str: # ISO format like "2023-10-26T10:00:00Z" or "2023-10-26T10:00:00.123Z"
                        activation_dt_obj = datetime.fromisoformat(activation_date_str.replace('Z', '+00:00'))
                    elif ' ' in activation_date_str: # Format like "YYYY-MM-DD HH:MM:SS"
                        activation_dt_obj = datetime.strptime(activation_date_str.split(' ')[0], "%Y-%m-%d")
                    else: # Assume "YYYY-MM-DD"
                        activation_dt_obj = datetime.strptime(activation_date_str, "%Y-%m-%d")
                    self._license_info["activation_date"] = activation_dt_obj.isoformat() # Store as full ISO
                except ValueError as ve:
                    logger.warning(f"提供的激活日期格式无法解析 '{activation_date_str}': {ve}. 将尝试使用当前日期。")
                    self._license_info["activation_date"] = datetime.now().isoformat()
            else:
                self._license_info["activation_date"] = datetime.now().isoformat() # Fallback to current date

            # 根据product_id等信息确定过期日期
            product_id = details_dict.get("product_id", "")
            self._license_info["product_id"] = product_id # Store product_id
            
            # 获取许可证密钥
            license_key = details_dict.get("key", "")
            
            # 检查是否是永久许可证
            # 1. 根据product_id判断
            # 2. 如果许可证密钥以WZS-WZSP开头，视为永久版本
            is_perpetual = False
            
            if product_id and "PERPETUAL" in product_id.upper():
                is_perpetual = True
                logger.info(f"基于product_id识别为永久版: {product_id}")
            elif license_key and license_key.upper().startswith("WZS-WZSP"):
                is_perpetual = True
                logger.info(f"基于密钥前缀识别为永久版: {license_key[:8]}...")
            
            if is_perpetual:
                self._license_info["expiration_date"] = "" # 永久版无过期
                logger.info("许可证配置为永久有效，无过期日期。")
                print("DEBUG: 永久许可证成功激活，无过期日期限制。")
            else:
                # 所有许可证都设置为永久有效
                self._license_info["expiration_date"] = "" # 永久版无过期
                logger.info("所有许可证均为永久有效，无过期日期。")
                print("DEBUG: 许可证成功激活，永久有效，无过期日期限制。")

            self._license_info["user_name"] = details_dict.get("user_name", "") 
            self._license_info["user_email"] = details_dict.get("user_email", "")
            
            # 添加多设备支持
            self._license_info["max_devices"] = details_dict.get("max_devices", 1)
            
            # 更新当前设备ID
            from generate_device_id import get_device_id
            current_device_id = details_dict.get("device_id", "")
            if not current_device_id:
                try:
                    current_device_id = get_device_id()
                except Exception as e:
                    logger.error(f"获取设备ID时出错: {e}")
                    current_device_id = ""
            self._license_info["current_device_id"] = current_device_id
            
            # 更新已激活设备列表
            activated_devices = details_dict.get("activated_devices", [])
            if activated_devices:
                self._license_info["activated_devices"] = activated_devices
            elif current_device_id and current_device_id not in self._license_info["activated_devices"]:
                self._license_info["activated_devices"].append(current_device_id)
            
            self._save_license_info()
            logger.info("已成功使用API返回的详细信息更新并保存许可证。")
            return True
        except Exception as e:
            logger.error(f"使用API详细信息更新许可证时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def deactivate_license(self):
        """
        停用当前许可证
        
        Returns:
            tuple: (成功状态, 消息)
        """
        if self._license_info["status"] == LicenseStatus.INACTIVE:
            return False, "没有激活的许可证可供停用"
        
        # 尝试通知服务器停用此设备
        if self._license_info["key"] and self._license_info["current_device_id"]:
            try:
                from license_activation import deactivate_device
                # 调用API注销当前设备
                result = deactivate_device(
                    self._license_info["key"], 
                    self._license_info["current_device_id"]
                )
                
                if result.get("success"):
                    logger.info(f"成功通知服务器停用设备: {self._license_info['current_device_id']}")
                else:
                    logger.warning(f"无法通知服务器停用设备: {result.get('message')}")
            except Exception as e:
                logger.error(f"尝试停用设备时出错: {e}")
        
        # 重置许可证信息
        self._license_info = {
            "status": LicenseStatus.INACTIVE,
            "key": "",
            "activation_date": "",
            "expiration_date": "",
            "user_name": "",
            "user_email": "",
            "max_devices": 1,
            "current_device_id": "",
            "activated_devices": []
        }
        
        # 保存更新后的许可证信息
        self._save_license_info()
        
        return True, "许可证已成功停用"
    
    def get_device_list(self):
        """
        获取当前许可证的设备列表
        
        Returns:
            dict: 包含设备信息的字典，如{"max_devices": 3, "current_devices": 2, "device_list": [{"id": "...", "name": "当前设备"}]}
        """
        if self._license_info["status"] != LicenseStatus.ACTIVE:
            return {"max_devices": 0, "current_devices": 0, "device_list": []}
        
        # 尝试从服务器获取最新设备列表
        try:
            from license_activation import get_device_list
            current_device_id = self._license_info["current_device_id"]
            if not current_device_id:
                from generate_device_id import get_device_id
                current_device_id = get_device_id()
                self._license_info["current_device_id"] = current_device_id
                self._save_license_info()
            
            result = get_device_list(self._license_info["key"], current_device_id)
            
            if result.get("success"):
                # 更新本地存储的信息
                self._license_info["max_devices"] = result.get("license", {}).get("maxDevices", self._license_info["max_devices"])
                self._license_info["activated_devices"] = [device["id"] for device in result.get("devices", [])]
                self._save_license_info()
                return {
                    "max_devices": self._license_info["max_devices"],
                    "current_devices": len(self._license_info["activated_devices"]),
                    "device_list": result.get("devices", [])
                }
            else:
                logger.warning(f"获取设备列表失败: {result.get('message')}")
        except Exception as e:
            logger.error(f"获取设备列表时出错: {e}")
        
        # 如果无法从服务器获取，则返回本地存储的信息
        return {
            "max_devices": self._license_info["max_devices"],
            "current_devices": len(self._license_info["activated_devices"]),
            "device_list": [
                {"id": self._license_info["current_device_id"], "name": "当前设备", "isCurrentDevice": True}
            ]
        }
    
    def deactivate_specific_device(self, device_id):
        """
        停用特定设备
        
        Args:
            device_id: 要停用的设备ID
            
        Returns:
            tuple: (成功状态, 消息)
        """
        if self._license_info["status"] != LicenseStatus.ACTIVE:
            return False, "没有激活的许可证"
        
        if device_id == self._license_info["current_device_id"]:
            return False, "无法停用当前设备，请使用注销功能"
        
        try:
            from license_activation import deactivate_specific_device
            result = deactivate_specific_device(
                self._license_info["key"],
                self._license_info["current_device_id"],
                device_id
            )
            
            if result.get("success"):
                # 更新本地存储的信息
                if device_id in self._license_info["activated_devices"]:
                    self._license_info["activated_devices"].remove(device_id)
                    self._save_license_info()
                
                return True, f"设备已成功停用。当前已激活 {result.get('currentDevices', len(self._license_info['activated_devices']))} 个设备，最多可激活 {result.get('maxDevices', self._license_info['max_devices'])} 个设备"
            else:
                return False, result.get("message", "停用设备失败")
        except Exception as e:
            logger.error(f"尝试停用设备时出错: {e}")
            return False, f"停用设备时发生错误: {str(e)}"
    
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
                
        # 检查是否为永久版（无过期日期）
        if not info["expiration_date"]:
            info["expiration_date_display"] = "永久有效"
            info["days_left"] = "∞" # 无限符号表示永久
            info["is_perpetual"] = True
        elif info["expiration_date"]:
            try:
                expiration_date = datetime.fromisoformat(info["expiration_date"])
                info["expiration_date_display"] = expiration_date.strftime("%Y-%m-%d")
                # 计算剩余天数
                days_left = (expiration_date - datetime.now()).days
                info["days_left"] = max(0, days_left)
                info["is_perpetual"] = False
            except ValueError:
                info["expiration_date_display"] = "未知"
                info["days_left"] = 0
                info["is_perpetual"] = False
        
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
        if not key: #  or len(key) != 19:  # 总长度应为19 (XXXX-XXXX-XXXX-XXXX) # 长度可变
            return False
            
        # 检查格式: WZS-PRODUCTID-XXXX-XXXX-XXXX-XXXX
        # 例如: WZS-PROPERPETUAL-A1B2-C3D4-E5F6-G7H8
        import re
        # 正则表达式解释：
        # ^WZS-  : 以 "WZS-" 开头
        # [A-Z0-9]+- : 产品ID部分 (大写字母和数字，后跟一个连字符)
        # ([A-Z0-9]{4}-){3} : 三组 "XXXX-"
        # [A-Z0-9]{4}$ : 最后一组 "XXXX"
        # 允许产品ID包含连字符，例如 WZS-PRO-MONTHLY-XXXX...
        # pattern = r'^WZS-[A-Z0-9]+-([A-Z0-9]{4}-){3}[A-Z0-9]{4}$' 
        pattern = r'^WZS-([A-Z0-9]+(?:-[A-Z0-9]+)*)-([A-Z0-9]{4}-){3}[A-Z0-9]{4}$'

        if not re.match(pattern, key.upper()): # 统一转大写进行匹配
            logger.warning(f"许可证密钥格式 '{key}' 不匹配预期模式: {pattern}")
            return False
            
        # 不再需要旧的简单校验逻辑，因为服务器会进行最终验证
        # segments = key.split('-')
        # for segment in segments:
        #     if len(segment) != 4:  # 再次检查每段长度，以防万一
        #         return False
        #         
        #     # 简单校验：第一个和最后一个字符的ASCII值之和应为偶数
        #     first_char_val = ord(segment[0])
        #     last_char_val = ord(segment[3])
        #     if (first_char_val + last_char_val) % 2 != 0:
        #         return False
                
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
_license_manager_lock = None

try:
    import threading
    _license_manager_lock = threading.Lock()
except ImportError:
    # 如果不可用，我们将没有锁机制，这在单线程环境中是可接受的
    pass

def get_license_manager():
    """
    获取LicenseManager的单例实例。
    确保整个应用程序使用同一个LicenseManager实例。
    
    Returns:
        LicenseManager: LicenseManager的单例实例
    """
    # 使用全局变量来保存实例
    global _license_manager_instance
    global _license_manager_lock
    
    # 简单的同步机制，如果可用
    if _license_manager_lock:
        _license_manager_lock.acquire()
        have_lock = True
    else:
        have_lock = False
        
    try:
        # 如果实例不存在，创建一个新实例
        if not '_license_manager_instance' in globals() or _license_manager_instance is None:
            try:
                _license_manager_instance = LicenseManager()
                logger.info("创建了新的LicenseManager实例")
                print("DEBUG: 已创建新的LicenseManager实例")
                
                # 加载并打印当前许可状态（用于调试）
                status = _license_manager_instance.get_license_status()
                license_info = _license_manager_instance.get_license_info()
                
                print(f"DEBUG: 许可状态: {status}")
                if status == LicenseStatus.ACTIVE:
                    exp_date = license_info.get('expiration_date', '未设置')
                    days_left = license_info.get('days_left', 'N/A')
                    print(f"DEBUG: 许可证有效期至: {exp_date} (剩余: {days_left}天)")
                
                # 确保设置同步到磁盘
                _license_manager_instance.settings.sync()
                print("DEBUG: 已同步许可证设置到磁盘")
                
            except Exception as e:
                logger.error(f"创建LicenseManager实例时出错: {e}")
                print(f"ERROR: 创建LicenseManager实例时出错: {e}")
                # 如果发生错误，最好也记录堆栈跟踪
                import traceback
                logger.error(traceback.format_exc())
                print(traceback.format_exc())
                
                # 出错时也要确保返回一个可用的实例
                _license_manager_instance = LicenseManager()
        else:
            logger.debug("使用已存在的LicenseManager实例")
    finally:
        # 释放锁，如果我们获取了它
        if have_lock and _license_manager_lock:
            _license_manager_lock.release()
    
    return _license_manager_instance

# 在模块加载时预先创建实例
try:
    _license_manager_instance = LicenseManager()
    logger.debug("在模块加载时预先创建了LicenseManager实例")
except Exception as e:
    logger.error(f"在模块加载时预创建LicenseManager实例失败: {e}")
    _license_manager_instance = None  # 重置为None，让get_license_manager尝试创建 