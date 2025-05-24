"""
测试文智搜集成轻量级搜索功能

此脚本用于测试文智搜应用程序集成轻量级搜索功能的效果。
包括测试:
1. 通过热键(Alt+Space)调用轻量级搜索窗口
2. 通过托盘菜单调用轻量级搜索窗口
3. 轻量级搜索结果的显示与交互
"""

import os
import sys
import time

def main():
    """主测试函数"""
    print("=== 文智搜轻量级搜索功能测试 ===")
    print()
    
    # 测试不同的启动方式
    test_startup_modes()
    
    print("测试完成!")

def test_startup_modes():
    """测试不同的启动方式"""
    
    print("请选择测试模式:")
    print("1. 测试普通启动 + 热键调出轻量级搜索")
    print("2. 测试使用轻量级搜索直接启动")
    print("3. 测试使用轻量级搜索 + 预设搜索关键词启动")
    print()
    
    try:
        choice = int(input("请输入选项(1-3): "))
        
        if choice == 1:
            print("\n启动普通模式，请在应用启动后按Alt+Space调出轻量级搜索窗口...")
            os.system("python start_tray_fixed.py")
        elif choice == 2:
            print("\n启动轻量级搜索模式...")
            os.system("python start_tray_fixed.py --quick-search")
        elif choice == 3:
            search_term = input("请输入搜索关键词: ")
            print(f"\n启动轻量级搜索模式，预设搜索关键词：{search_term}...")
            os.system(f'python start_tray_fixed.py --quick-search --search "{search_term}"')
        else:
            print("无效的选项，请重新运行并输入1-3之间的数字。")
    except ValueError:
        print("无效的输入，请输入数字。")
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")

if __name__ == "__main__":
    main() 