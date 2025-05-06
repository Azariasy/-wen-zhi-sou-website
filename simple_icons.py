#!/usr/bin/env python3
"""生成主题图标的简单脚本"""

import os
import sys
from PIL import Image, ImageDraw

def create_down_arrow(filename, size=(20, 20), color=(128, 128, 128), bg_color=None, alpha=180):
    """创建下拉箭头图标"""
    # 创建透明背景
    img = Image.new('RGBA', size, color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 计算箭头坐标
    width, height = size
    margin = width // 4
    
    # 画一个向下的三角形
    points = [
        (margin, margin),  # 左上角
        (width - margin, margin),  # 右上角
        (width // 2, height - margin)  # 底部中间
    ]
    
    # 使用指定颜色和透明度
    arrow_color = color + (alpha,)
    draw.polygon(points, fill=arrow_color)
    
    # 保存图标
    img.save(filename, 'PNG')
    print(f"成功保存图标: {os.path.abspath(filename)}")

def create_checkmark(filename, size=(20, 20), color=(128, 128, 128)):
    """创建勾选标记图标"""
    # 创建透明背景
    img = Image.new('RGBA', size, color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 计算勾选标记的坐标
    width, height = size
    
    # 勾选标记的点（比例自定义）
    scale = min(width, height)
    points = [
        (0.2 * scale, 0.5 * scale),  # 左侧点
        (0.45 * scale, 0.75 * scale),  # 底部点
        (0.8 * scale, 0.2 * scale)   # 右上角点
    ]
    
    # 将坐标映射到图像尺寸
    points = [(int(x), int(y)) for x, y in points]
    
    # 绘制勾选标记，使用较粗的线条
    line_width = max(2, int(scale / 10))
    draw.line(points, fill=color, width=line_width)
    
    # 保存图标
    img.save(filename, 'PNG')
    print(f"成功保存图标: {os.path.abspath(filename)}")

def create_radio_indicator(filename, size=(16, 16), color=(128, 128, 128)):
    """创建单选按钮指示器"""
    # 创建透明背景
    img = Image.new('RGBA', size, color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 计算圆的参数
    width, height = size
    center = (width // 2, height // 2)
    radius = min(width, height) // 3
    
    # 绘制实心圆
    draw.ellipse(
        (center[0] - radius, center[1] - radius, 
         center[0] + radius, center[1] + radius), 
        fill=color
    )
    
    # 保存图标
    img.save(filename, 'PNG')
    print(f"成功保存图标: {os.path.abspath(filename)}")

def create_all_theme_icons():
    """创建所有主题所需的图标"""
    # 标准白色勾选标记（用于深色背景）
    create_checkmark("checkmark.png", color=(255, 255, 255))
    
    # 蓝色主题
    blue_color = (52, 152, 219)  # #3498db
    create_down_arrow("down_arrow_blue.png", color=blue_color)
    create_checkmark("checkmark_blue.png", color=blue_color)
    create_radio_indicator("radio_checked_blue.png", color=blue_color)
    
    # 绿色主题
    green_color = (46, 204, 113)  # #2ecc71
    create_down_arrow("down_arrow_green.png", color=green_color)
    create_checkmark("checkmark_green.png", color=green_color)
    create_radio_indicator("radio_checked_green.png", color=green_color)
    
    # 紫色主题
    purple_color = (155, 89, 182)  # #9b59b6
    create_down_arrow("down_arrow_purple.png", color=purple_color)
    create_checkmark("checkmark_purple.png", color=purple_color)
    create_radio_indicator("radio_checked_purple.png", color=purple_color)
    
    # 金色主题
    gold_color = (230, 195, 74)  # #e6c34a
    create_down_arrow("down_arrow_gold.png", color=gold_color)
    create_checkmark("checkmark_gold.png", color=gold_color)
    create_radio_indicator("radio_checked_gold.png", color=gold_color)
    
    # 薄荷色主题
    mint_color = (102, 205, 170)  # #66cdaa
    create_down_arrow("down_arrow_mint.png", color=mint_color)
    create_checkmark("checkmark_mint.png", color=mint_color)
    create_radio_indicator("radio_checked_mint.png", color=mint_color)
    
    # 默认下拉箭头（灰色）
    create_down_arrow("down_arrow.png", color=(128, 128, 128))

if __name__ == "__main__":
    create_all_theme_icons()
    print("所有主题图标创建完成") 