from PIL import Image, ImageDraw, ImageFont
import os

# 创建512x512的透明背景图像
size = 512
img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# 绘制圆角矩形背景
bg_color = (52, 152, 219)  # 蓝色背景
draw.rectangle([(0, 0), (size, size)], fill=bg_color)

# 添加一个搜索图标元素
icon_margin = size // 4
icon_size = size - (icon_margin * 2)
# 绘制放大镜
circle_size = icon_size // 2
circle_pos = (icon_margin + circle_size // 2, icon_margin + circle_size // 2)
draw.ellipse([(circle_pos[0] - circle_size // 2, circle_pos[1] - circle_size // 2),
              (circle_pos[0] + circle_size // 2, circle_pos[1] + circle_size // 2)],
             outline=(255, 255, 255), width=size // 25, fill=None)

# 绘制放大镜手柄
handle_width = size // 25
handle_start = (circle_pos[0] + circle_size // 2 * 0.7, circle_pos[1] + circle_size // 2 * 0.7)
handle_end = (size - icon_margin, size - icon_margin)
draw.line([handle_start, handle_end], fill=(255, 255, 255), width=handle_width)

# 添加文字 "文智搜"
try:
    # 尝试加载中文字体，如果没有可用的中文字体，将使用默认字体
    font_size = size // 6
    font_path = None
    
    # 尝试常见的中文字体路径
    possible_fonts = [
        "C:/Windows/Fonts/simhei.ttf",  # Windows 黑体
        "C:/Windows/Fonts/msyh.ttf",    # Windows 微软雅黑
        "C:/Windows/Fonts/simsun.ttc",  # Windows 宋体
        "/System/Library/Fonts/PingFang.ttc",  # macOS
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"  # Linux
    ]
    
    for path in possible_fonts:
        if os.path.exists(path):
            font_path = path
            break
    
    if font_path:
        font = ImageFont.truetype(font_path, font_size)
        text = "文智搜"
        # 计算文本大小以居中放置
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_position = ((size - text_width) // 2, size - icon_margin - text_height)
        draw.text(text_position, text, font=font, fill=(255, 255, 255))
except Exception as e:
    print(f"无法添加文字: {e}")

# 保存图像为PNG，优化文件大小
output_path = "app_icon.png"
img.save(output_path, "PNG", optimize=True)

# 检查文件大小
file_size = os.path.getsize(output_path) / 1024  # KB
print(f"图标已生成: {output_path}")
print(f"文件大小: {file_size:.2f} KB")

# 如果文件大小超过200KB，尝试进一步优化
if file_size > 200:
    # 尝试使用不同的压缩级别
    for quality in [90, 80, 70, 60]:
        img.save(output_path, "PNG", optimize=True, quality=quality)
        new_size = os.path.getsize(output_path) / 1024
        print(f"优化后大小 (quality={quality}): {new_size:.2f} KB")
        if new_size <= 200:
            break

print(f"最终图标路径: {output_path}")
print(f"最终文件大小: {os.path.getsize(output_path) / 1024:.2f} KB") 