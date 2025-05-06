#!/usr/bin/env python3
"""
创建主题图标的脚本，只为现代蓝、现代绿、现代紫三种主题生成图标
"""

from PIL import Image, ImageDraw
import os

def create_down_arrow(filename, size=(10, 10), color="#333333"):
    """创建下拉箭头图标"""
    img = Image.new('RGBA', size, color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 计算三角形的坐标
    width, height = size
    margin = int(width * 0.2)
    
    # 三角形坐标：左上，右上，底部中点
    points = [
        (margin, margin),
        (width - margin, margin),
        (width // 2, height - margin)
    ]
    
    # 绘制填充三角形
    draw.polygon(points, fill=color)
    
    # 保存图像
    img.save(filename, 'PNG')
    print(f"成功保存图标: {os.path.abspath(filename)}")

def create_checkmark(filename, size=(14, 14), color="#333333"):
    """创建勾选图标"""
    img = Image.new('RGBA', size, color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 计算勾号的坐标
    width, height = size
    margin = int(width * 0.2)
    
    # 勾号的点：左下，中下，右上
    check_width = width - 2 * margin
    check_height = height - 2 * margin
    
    # 计算勾号的三个关键点
    p1 = (margin, height / 2)
    p2 = (width * 0.4, height - margin)
    p3 = (width - margin, margin)
    
    # 绘制折线
    draw.line([p1, p2, p3], fill=color, width=2)
    
    # 保存图像
    img.save(filename, 'PNG')
    print(f"成功保存图标: {os.path.abspath(filename)}")

def create_radio_indicator(filename, size=(10, 10), color="#333333"):
    """创建单选按钮指示器图标"""
    img = Image.new('RGBA', size, color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 计算圆形的坐标
    width, height = size
    margin = int(width * 0.2)
    
    # 绘制填充圆形
    draw.ellipse(
        [(margin, margin), (width - margin, height - margin)],
        fill=color
    )
    
    # 保存图像
    img.save(filename, 'PNG')
    print(f"成功保存图标: {os.path.abspath(filename)}")

def create_all_theme_icons():
    """为所有主题创建图标"""
    print("生成图标...")
    
    # 创建默认灰色下拉箭头
    create_down_arrow("down_arrow.png", color="#333333")
    
    # 创建白色勾选图标（用于深色背景）
    create_checkmark("checkmark.png", color="#ffffff")
    
    # 为每个主题创建对应颜色的图标
    themes = [
        ("blue", "#3498db"),    # 现代蓝
        ("green", "#2ecc71"),   # 现代绿
        ("purple", "#9b59b6"),  # 现代紫
    ]
    
    for theme_name, color in themes:
        # 为每个主题创建下拉箭头
        create_down_arrow(f"down_arrow_{theme_name}.png", color=color)
        
        # 为每个主题创建勾选标记
        create_checkmark(f"checkmark_{theme_name}.png", color=color)
        
        # 为每个主题创建单选按钮指示器
        create_radio_indicator(f"radio_checked_{theme_name}.png", color=color)
    
    print("图标创建完成")

if __name__ == "__main__":
    create_all_theme_icons()
