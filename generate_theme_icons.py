#!/usr/bin/env python
"""
为文智搜生成所有主题图标
"""
import simple_icons
import sys
import os

def main():
    print("生成所有主题图标...")
    # 运行图标生成
    simple_icons.main()
    print("图标生成完成!")
    
    # 检查图标是否都已创建
    expected_icons = [
        "down_arrow.png",
        "checkmark.png",
        "checkmark_blue.png",
        "checkmark_green.png",
        "checkmark_purple.png",
        "radio_checked_blue.png",
        "radio_checked_green.png",
        "radio_checked_purple.png"
    ]
    
    all_exist = True
    for icon in expected_icons:
        icon_path = os.path.join(os.getcwd(), icon)
        if os.path.exists(icon_path):
            print(f"✓ 图标存在: {icon}")
        else:
            print(f"✗ 图标缺失: {icon}")
            all_exist = False
    
    if all_exist:
        print("所有图标已成功生成!")
        return 0
    else:
        print("部分图标生成失败，请检查错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 