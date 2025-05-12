#!/usr/bin/env python3
"""
临时启用专业版模式的脚本
仅用于开发和测试阶段，查看专业版功能效果
"""

from license_manager import get_license_manager, LicenseStatus

def enable_pro_mode():
    """临时启用专业版模式"""
    license_manager = get_license_manager()
    
    # 打印当前许可证状态
    current_status = license_manager.get_license_status()
    print(f"当前许可证状态: {current_status}")
    
    # 直接访问内部变量以修改许可证状态（仅用于开发阶段）
    # 警告：这是一个不安全的操作，仅用于开发阶段查看专业版效果
    print("正在临时设置许可证状态为专业版...")
    
    license_manager._license_info["status"] = LicenseStatus.ACTIVE
    license_manager._license_info["key"] = "DEV-MODE-TEMP-TEST"  # 开发模式临时密钥
    
    # 设置1年有效期，从今天开始
    from datetime import datetime, timedelta
    activation_date = datetime.now()
    expiration_date = activation_date + timedelta(days=365)
    
    license_manager._license_info["activation_date"] = activation_date.isoformat()
    license_manager._license_info["expiration_date"] = expiration_date.isoformat()
    
    # 保存更改
    license_manager._save_license_info()
    
    # 打印新状态
    new_status = license_manager.get_license_status()
    print(f"许可证状态已更改为: {new_status}")
    print(f"现在所有高级功能已临时启用，有效期至: {expiration_date.strftime('%Y-%m-%d')}")
    print("注意: 此更改是真实的并会保存到设置中，要恢复免费模式请运行 disable_pro_mode.py")

def check_features():
    """检查所有高级功能的可用状态"""
    from license_manager import Features
    
    license_manager = get_license_manager()
    
    print("\n检查高级功能可用状态:")
    print("-" * 40)
    
    features = [
        (Features.PDF_SUPPORT, "PDF文件支持"),
        (Features.MARKDOWN_SUPPORT, "Markdown文件支持"),
        (Features.EMAIL_SUPPORT, "邮件文件支持"),
        (Features.ARCHIVE_SUPPORT, "压缩包内容支持"),
        (Features.WILDCARDS, "通配符搜索"),
        (Features.UNLIMITED_DIRS, "无限制源目录"),
        (Features.ADVANCED_THEMES, "高级主题支持"),
        (Features.FOLDER_TREE, "文件夹树视图")
    ]
    
    for feature_id, feature_name in features:
        available = license_manager.is_feature_available(feature_id)
        status = "可用 ✓" if available else "不可用 ✗"
        print(f"{feature_name}: {status}")
    
    print("-" * 40)

if __name__ == "__main__":
    enable_pro_mode()
    check_features()
    input("按回车键关闭窗口...") 