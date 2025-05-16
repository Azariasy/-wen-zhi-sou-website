from PIL import Image, ImageDraw, ImageFont
import os

# 创建一个256x256的图像，橙色背景
width, height = 256, 256
background_color = (255, 140, 0)  # 橙色
icon = Image.new('RGBA', (width, height), (0, 0, 0, 0))

# 创建圆形背景
draw = ImageDraw.Draw(icon)
draw.ellipse((0, 0, width, height), fill=background_color)

# 尝试加载一个中文字体
try:
    # 尝试几个常见的中文字体
    font_paths = [
        'C:/Windows/Fonts/simhei.ttf',  # Windows黑体
        'C:/Windows/Fonts/simsun.ttc',  # Windows宋体
        'C:/Windows/Fonts/msyh.ttc'     # Windows微软雅黑
    ]
    
    font = None
    for path in font_paths:
        if os.path.exists(path):
            font = ImageFont.truetype(path, size=100)
            break
    
    if font is None:  # 如果找不到中文字体，使用默认字体
        font = ImageFont.load_default()
        text = "WZS"  # 如果无法显示中文，使用拼音首字母
    else:
        text = "文智"
    
    # 添加文本 - 使用textbbox而不是textsize (在新版PIL中推荐)
    try:
        # 新版PIL
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except AttributeError:
        # 旧版PIL兼容
        text_width, text_height = draw.textsize(text, font=font)
        
    position = ((width - text_width) // 2, (height - text_height) // 2 - 10)
    
    # 添加文本
    draw.text(position, text, fill=(255, 255, 255), font=font)
    
except Exception as e:
    # 如果出错，创建一个简单的文本
    print(f"尝试加载中文字体失败: {e}")
    try:
        default_font = ImageFont.truetype("arial", 80)
    except:
        default_font = ImageFont.load_default()
        
    draw.text((80, 100), "WZS", fill=(255, 255, 255), font=default_font)

# 保存为ICO文件
icon.save('app_icon.ico', format='ICO', sizes=[(256, 256)])
print("图标已保存为 app_icon.ico") 