import subprocess
import hashlib
import platform
import os
import sys
import uuid
import time

print("文智搜设备ID生成工具启动...")
print(f"Python版本: {sys.version}")
print(f"系统平台: {platform.platform()}")

def get_simple_windows_id():
    """使用简单可靠的方法获取Windows设备ID"""
    print("使用简化方法获取Windows设备ID...")
    identifiers = []
    
    # 1. 使用systeminfo命令获取基本信息
    try:
        print("运行systeminfo命令获取系统信息...")
        result = subprocess.check_output("systeminfo", shell=True, text=True, stderr=subprocess.PIPE)
        lines = result.strip().split('\n')
        
        # 提取主机名
        hostname_lines = [line for line in lines if "主机名" in line or "Host Name" in line]
        if hostname_lines:
            hostname = hostname_lines[0].split(':', 1)[1].strip()
            if hostname:
                identifiers.append(f"HOST-{hostname}")
                print(f"获取到主机名: {hostname}")
        
        # 提取BIOS信息
        bios_lines = [line for line in lines if "BIOS" in line]
        if bios_lines:
            bios_info = bios_lines[0].split(':', 1)[1].strip()
            if bios_info:
                identifiers.append(f"BIOS-{bios_info}")
                print(f"获取到BIOS信息: {bios_info}")
    except Exception as e:
        print(f"获取系统信息失败: {e}")
    
    # 2. 使用环境变量获取计算机名和用户名
    try:
        computername = os.environ.get('COMPUTERNAME')
        if computername:
            identifiers.append(f"PC-{computername}")
            print(f"从环境变量获取计算机名: {computername}")
    except Exception as e:
        print(f"获取环境变量COMPUTERNAME失败: {e}")
    
    try:
        username = os.environ.get('USERNAME')
        if username:
            identifiers.append(f"USER-{username}")
            print(f"从环境变量获取用户名: {username}")
    except Exception as e:
        print(f"获取环境变量USERNAME失败: {e}")
    
    # 3. 获取盘符信息
    try:
        print("获取系统盘信息...")
        result_vol = subprocess.check_output("dir C:\\ /a", shell=True, text=True, stderr=subprocess.PIPE)
        for line in result_vol.strip().split('\n'):
            if "Volume Serial Number is" in line or "卷序列号是" in line:
                parts = line.split("is" if "is" in line else "是")
                if len(parts) > 1:
                    vol_serial = parts[1].strip()
                    identifiers.append(f"VOL-{vol_serial}")
                    print(f"获取到系统盘序列号: {vol_serial}")
                    break
    except Exception as e:
        print(f"获取系统盘信息失败: {e}")
    
    # 如果没有收集到任何标识符，使用备选方案
    if not identifiers:
        print("未能获取到任何系统标识符，将使用备选方案...")
        return get_fallback_device_id()
    
    # 合并并哈希所有标识符
    combined_id_string = "-".join(sorted(set(identifiers)))
    hashed_id = hashlib.sha256(combined_id_string.encode('utf-8')).hexdigest()
    
    print(f"合并的标识符字符串: {combined_id_string}")
    print(f"生成的设备ID (SHA256): {hashed_id}")
    return hashed_id

def get_fallback_device_id():
    """当无法获取到硬件信息时的备选方法"""
    print("使用备选方法生成设备ID...")
    
    # 首先检查是否存在持久化存储的ID
    device_id_path = os.path.join(os.path.expanduser("~"), ".wenzhisou_device_id")
    if os.path.exists(device_id_path):
        try:
            with open(device_id_path, "r") as f:
                stored_id = f.read().strip()
                if stored_id:
                    print(f"使用已存储的设备ID: {stored_id}")
                    return stored_id
        except Exception as e:
            print(f"读取已存储ID时出错: {e}")
    
    # 随机生成一个UUID作为设备ID
    random_id = str(uuid.uuid4())
    try:
        # 将ID持久化存储以便下次使用
        with open(device_id_path, "w") as f:
            f.write(random_id)
        print(f"生成并存储了新的随机设备ID: {random_id}")
    except Exception as e:
        print(f"存储随机设备ID时出错: {e}")
    
    return random_id

def get_device_id():
    """获取设备ID的主函数"""
    print(f"检测操作系统...")
    if platform.system().lower() == "windows":
        print(f"检测到Windows系统")
        return get_simple_windows_id()
    else:
        print(f"检测到非Windows系统: {platform.system()}")
        return get_fallback_device_id()

if __name__ == '__main__':
    try:
        print("="*50)
        print("文智搜设备ID生成工具")
        print("="*50)
        
        print("\n开始收集设备信息...")
        device_id = get_device_id()
        
        print("\n" + "="*50)
        print(f"最终设备ID: {device_id}")
        print("此ID将用于软件激活")
        print("="*50)
        
        # 保存设备ID到文件
        try:
            with open("device_id.txt", "w") as f:
                f.write(device_id)
            print(f"\n设备ID已保存至当前目录下的 device_id.txt 文件")
        except Exception as e:
            print(f"\n保存设备ID到文件时出错: {e}")
        
        print("\n按Enter键退出...")
        input()
    except Exception as e:
        print(f"\n程序运行时发生错误: {e}")
        print("\n按Enter键退出...")
        input() 