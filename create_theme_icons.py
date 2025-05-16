#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建红色和橙色主题图标
基于现有的蓝色主题图标，生成对应的红色和橙色版本
"""

from PIL import Image
import os

# 定义颜色
RED_COLOR = (231, 76, 60)     # #e74c3c
ORANGE_COLOR = (243, 156, 18) # #f39c12

def create_colored_icons(base_color, color_name):
    """创建特定颜色的图标"""
    icon_types = ["checkmark", "down_arrow", "radio_checked"]
    
    for icon_type in icon_types:
        # 基于蓝色图标创建
        source_file = f"{icon_type}_blue.png"
        target_file = f"{icon_type}_{color_name}.png"
        
        if os.path.exists(source_file):
            # 打开原始图标
            img = Image.open(source_file)
            # 创建一个新的透明图像，保持原始尺寸
            new_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
            
            # 获取图标中有颜色的像素（非透明部分）
            pixels = img.load()
            new_pixels = new_img.load()
            
            # 替换所有非透明像素为新颜色
            for y in range(img.height):
                for x in range(img.width):
                    # 如果像素不是完全透明的（alpha > 0）
                    if pixels[x, y][3] > 0:
                        # 设置新颜色，保持原来的透明度
                        new_pixels[x, y] = (base_color[0], base_color[1], base_color[2], pixels[x, y][3])
                    else:
                        new_pixels[x, y] = pixels[x, y]
            
            # 保存新图标
            new_img.save(target_file)
            print(f"已创建: {target_file}")
        else:
            print(f"错误: 找不到源文件 {source_file}")

def main():
    # 创建红色图标
    create_colored_icons(RED_COLOR, "red")
    
    # 创建橙色图标
    create_colored_icons(ORANGE_COLOR, "orange")
    
    print("图标创建完成！")

if __name__ == "__main__":
    main()
