"""
应用程序重新打包脚本
用于解决图标文件路径问题，在PyInstaller打包过程中确保所有资源文件被正确包含
"""

import os
import sys
import subprocess
import shutil

def rebuild_application():
    """重新打包应用程序，确保包含所有必要的资源文件"""
    print("开始重新打包应用程序...\n")
    
    # 确保.spec文件存在
    spec_file = "文智搜.spec"
    if not os.path.exists(spec_file):
        print(f"错误: {spec_file} 文件未找到")
        return False
    
    # 确保所有要打包的资源文件存在
    required_resources = [
        "blue_style.qss",
        "green_style.qss",
        "purple_style.qss",
        "checkmark.png",
        "checkmark_blue.png",
        "checkmark_green.png",
        "checkmark_purple.png",
        "down_arrow.png",
        "down_arrow_blue.png",
        "down_arrow_green.png",
        "down_arrow_purple.png",
        "radio_checked_blue.png",
        "radio_checked_green.png",
        "radio_checked_purple.png"
    ]
    
    missing_files = []
    for file in required_resources:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("错误: 以下资源文件缺失:")
        for file in missing_files:
            print(f"  - {file}")
        print("\n请确保所有资源文件存在后再尝试打包")
        return False
    
    # 备份原来的.spec文件
    backup_spec = f"{spec_file}.bak"
    try:
        print(f"备份 {spec_file} 到 {backup_spec}")
        shutil.copy2(spec_file, backup_spec)
    except Exception as e:
        print(f"备份 {spec_file} 时出错: {e}")
        return False
    
    # 运行PyInstaller
    print("\n开始PyInstaller打包流程...")
    try:
        cmd = f"pyinstaller --clean {spec_file}"
        print(f"执行命令: {cmd}")
        subprocess.run(cmd, shell=True, check=True)
        print("\n打包完成!")
        
        # 检查打包结果
        dist_dir = os.path.join("dist", "文智搜")
        if os.path.exists(dist_dir):
            print(f"\n打包成功! 输出目录: {dist_dir}")
            exe_file = os.path.join(dist_dir, "文智搜.exe")
            if os.path.exists(exe_file):
                print(f"可执行文件: {exe_file}")
            else:
                print("警告: 没有找到可执行文件")
        else:
            print("\n警告: 打包可能未成功完成，没有找到输出目录")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n打包过程中出错: {e}")
        return False
    except Exception as e:
        print(f"\n发生意外错误: {e}")
        return False

if __name__ == "__main__":
    success = rebuild_application()
    
    if success:
        print("\n操作完成。请测试打包后的应用是否能正确显示图标。")
    else:
        print("\n打包失败。请修复错误后重试。")
    
    input("\n按Enter键退出...") 