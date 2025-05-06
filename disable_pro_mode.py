#!/usr/bin/env python3
"""
恢复免费版模式的脚本
用于在测试专业版功能后恢复免费版状态
"""

from license_manager import get_license_manager, LicenseStatus

def disable_pro_mode():
    """恢复免费版模式"""
    license_manager = get_license_manager()
    
    # 打印当前许可证状态
    current_status = license_manager.get_license_status()
    print(f"当前许可证状态: {current_status}")
    
    if current_status == LicenseStatus.INACTIVE:
        print("已经是免费版模式，无需恢复。")
        return
    
    # 直接重置许可证信息
    print("正在恢复免费版模式...")
    
    # 使用内置的deactivate_license方法
    success, message = license_manager.deactivate_license()
    
    if success:
        print(f"成功: {message}")
        print("许可证状态已恢复为免费版，所有专业版功能已禁用。")
    else:
        print(f"失败: {message}")

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
        (Features.ADVANCED_THEMES, "高级主题支持")
    ]
    
    for feature_id, feature_name in features:
        available = license_manager.is_feature_available(feature_id)
        status = "可用 ✓" if available else "不可用 ✗"
        print(f"{feature_name}: {status}")
    
    print("-" * 40)

if __name__ == "__main__":
    disable_pro_mode()
    check_features()
    input("按回车键关闭窗口...") 