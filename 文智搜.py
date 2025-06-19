"""
文智搜 - 智能文档搜索工具启动器

这是文智搜的主启动文件，用于启动带有托盘功能的搜索应用程序。
"""

import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def main():
    """主函数 - 启动文智搜托盘版应用程序"""
    try:
        # 首先检查单实例
        from single_instance import check_single_instance
        instance_manager = check_single_instance()
        
        if instance_manager is None:
            # 检测到重复实例，程序应该退出
            print("检测到程序已在运行，退出...")
            return 0
        
        print("单实例检查通过，启动托盘版程序...")
        
        # 导入并运行托盘版本的主程序
        from main_tray import main as tray_main
        
        # 清理单实例管理器（在托盘程序退出后）
        try:
            exit_code = tray_main()
        finally:
            if instance_manager:
                instance_manager.cleanup()
        
        return exit_code
        
    except Exception as e:
        print(f"启动文智搜托盘版时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 