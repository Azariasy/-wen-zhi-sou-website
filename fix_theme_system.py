#!/usr/bin/env python3
"""
修改主题系统的脚本，删除浅色、深色、金色和薄荷色主题，只保留现代蓝、现代绿、现代紫三种主题。
"""

import re
import os

def fix_settings_dialog_themes():
    """修改SettingsDialog中的主题下拉框选项"""
    file_path = "search_gui_pyside.py"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 查找并修改主题下拉框初始化部分
    pattern = r'(self\.theme_combo = QComboBox\(\).*?)(self\.theme_combo\.addItem\("浅色"\).*?self\.theme_combo\.addItem\("深色"\))'
    replacement = r'\1# 删除浅色和深色主题'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # 删除金色和薄荷色主题的添加代码，但保留现代绿和现代紫
    pro_themes_pattern = r'(advanced_themes = \[.*?\])'
    pro_themes_replacement = r'advanced_themes = ["现代绿", "现代紫"]'
    content = re.sub(pro_themes_pattern, pro_themes_replacement, content)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("成功修改SettingsDialog中的主题下拉框选项")

def fix_apply_theme_method():
    """修改apply_theme方法，删除浅色、深色、金色和薄荷色主题处理部分"""
    file_path = "search_gui_pyside.py"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 查找apply_theme方法的开始和结束位置
    apply_theme_pattern = r'def apply_theme\(self, theme_name\):.*?def _apply_fallback_blue_theme'
    match = re.search(apply_theme_pattern, content, re.DOTALL)
    
    if match:
        apply_theme_content = match.group(0)
        
        # 删除浅色和深色主题的处理部分
        light_dark_pattern = r'(elif theme_name == "浅色":.*?elif theme_name == "深色":.*?)(elif theme_name == "现代蓝":|elif theme_name == "现代绿":|elif theme_name == "现代紫":)'
        apply_theme_content = re.sub(light_dark_pattern, r'\2', apply_theme_content, flags=re.DOTALL)
        
        # 删除金色和薄荷色主题的处理部分
        gold_mint_pattern = r'(elif theme_name == "金色":.*?)(elif theme_name == "现代蓝":|elif theme_name == "现代绿":|elif theme_name == "现代紫":)'
        apply_theme_content = re.sub(gold_mint_pattern, r'\2', apply_theme_content, flags=re.DOTALL)
        
        mint_pattern = r'(elif theme_name == "薄荷色":.*?)(else:)'
        apply_theme_content = re.sub(mint_pattern, r'\2', apply_theme_content, flags=re.DOTALL)
        
        # 更新检查主题是否可用的条件判断，使用更简单的逻辑
        warning_pattern = r'if theme_name != "现代蓝" and theme_name != "浅色" and theme_name != "深色" and theme_name != "系统默认" and not advanced_themes_available:'
        warning_replacement = r'if theme_name != "现代蓝" and not advanced_themes_available:'
        apply_theme_content = re.sub(warning_pattern, warning_replacement, apply_theme_content)
        
        # 修改警告消息
        message_pattern = r'"高级主题（现代绿、现代紫、金色和薄荷色）仅在专业版中可用'
        message_replacement = r'"高级主题（现代绿、现代紫）仅在专业版中可用'
        apply_theme_content = re.sub(message_pattern, message_replacement, apply_theme_content)
        
        # 替换回整个文件
        updated_content = content.replace(match.group(0), apply_theme_content)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        
        print("成功修改apply_theme方法")
    else:
        print("未找到apply_theme方法")

def create_replacement_theme_method():
    """创建一个新的apply_theme方法，替换原来的方法"""
    file_path = "apply_theme_replacement.py"
    
    content = """
def apply_theme(self, theme_name):
    \"\"\"应用程序主题设置\"\"\"
    app = QApplication.instance()
    
    # 检查非蓝色主题是否可用（是否有专业版许可证）
    advanced_themes_available = self.license_manager.is_feature_available(Features.ADVANCED_THEMES)
    
    # 如果选择了非蓝色主题但没有专业版许可证，就强制使用蓝色主题
    if theme_name != "现代蓝" and not advanced_themes_available:
        if not hasattr(self, '_theme_warning_shown'):
            self._theme_warning_shown = False
            
        if not self._theme_warning_shown:
            self._theme_warning_shown = True
            QMessageBox.information(
                self, 
                "主题限制", 
                "高级主题（现代绿、现代紫）仅在专业版中可用。\\n"
                "已自动切换到现代蓝主题。\\n"
                "升级到专业版以解锁所有主题。"
            )
        
        # 强制使用现代蓝主题并保存设置
        theme_name = "现代蓝"
        self.settings.setValue("ui/theme", theme_name)
    
    if theme_name == "现代蓝":
        # 使用现代蓝色主题
        try:
            # 加载蓝色样式表
            style_path = os.path.join(os.path.dirname(__file__), "blue_style.qss")
            if os.path.exists(style_path):
                with open(style_path, "r", encoding="utf-8") as f:
                    stylesheet = f.read()
                # 确保QSS使用正确的checkmark图标
                stylesheet = stylesheet.replace("image: url(checkmark.png)", "image: url(checkmark_blue.png)")
                app.setStyleSheet(stylesheet)
                print("Applied modern blue theme.")
            else:
                print(f"Blue style file not found: {style_path}")
                # 回退到系统默认
                app.setStyleSheet("")
        except Exception as e:
            print(f"Error applying modern blue style: {e}. Falling back to system default.")
            app.setStyleSheet("")
            
    elif theme_name == "现代绿":
        # 使用现代绿色主题
        try:
            # 加载绿色样式表
            style_path = os.path.join(os.path.dirname(__file__), "green_style.qss")
            if os.path.exists(style_path):
                with open(style_path, "r", encoding="utf-8") as f:
                    stylesheet = f.read()
                # 确保QSS使用正确的checkmark图标
                stylesheet = stylesheet.replace("image: url(checkmark.png)", "image: url(checkmark_green.png)")
                app.setStyleSheet(stylesheet)
                print("Applied modern green theme.")
            else:
                print(f"Green style file not found: {style_path}")
                # 回退到现代蓝
                self._apply_fallback_blue_theme()
        except Exception as e:
            print(f"Error applying modern green style: {e}. Falling back to modern blue theme.")
            self._apply_fallback_blue_theme()
            
    elif theme_name == "现代紫":
        # 使用现代紫色主题
        try:
            # 加载紫色样式表
            style_path = os.path.join(os.path.dirname(__file__), "purple_style.qss")
            if os.path.exists(style_path):
                with open(style_path, "r", encoding="utf-8") as f:
                    stylesheet = f.read()
                # 确保QSS使用正确的checkmark图标
                stylesheet = stylesheet.replace("image: url(checkmark.png)", "image: url(checkmark_purple.png)")
                app.setStyleSheet(stylesheet)
                print("Applied modern purple theme.")
            else:
                print(f"Purple style file not found: {style_path}")
                # 回退到现代蓝
                self._apply_fallback_blue_theme()
        except Exception as e:
            print(f"Error applying modern purple style: {e}. Falling back to modern blue theme.")
            self._apply_fallback_blue_theme()
    else:
        # 对于任何未知主题，使用现代蓝
        self._apply_fallback_blue_theme()
"""
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("已创建替换用的apply_theme方法，保存在", file_path)
    print("请手动替换search_gui_pyside.py中的apply_theme方法")

def delete_theme_files():
    """删除不再使用的主题文件"""
    theme_files_to_delete = [
        "gold_style.qss",
        "mint_style.qss"
    ]
    
    for file_name in theme_files_to_delete:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"已删除: {file_name}")
        else:
            print(f"文件不存在: {file_name}")

def modify_test_style():
    """修改测试样式脚本，删除不需要的主题选项"""
    file_path = "test_style.py"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 更新主题下拉框选项
        pattern = r'self\.theme_combo\.addItems\(\["现代蓝", "现代绿", "现代紫", "金色", "薄荷色", "浅色", "深色"\]\)'
        replacement = r'self.theme_combo.addItems(["现代蓝", "现代绿", "现代紫"])'
        content = re.sub(pattern, replacement, content)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print("成功修改测试样式脚本")
    else:
        print("测试样式脚本不存在")

def create_simplified_icon_script():
    """创建一个简化版的图标创建脚本，只生成现代蓝、现代绿、现代紫三种主题的图标"""
    file_path = "create_theme_icons.py"
    
    content = """#!/usr/bin/env python3
\"\"\"
创建主题图标的脚本，只为现代蓝、现代绿、现代紫三种主题生成图标
\"\"\"

from PIL import Image, ImageDraw
import os

def create_down_arrow(filename, size=(10, 10), color="#333333"):
    \"\"\"创建下拉箭头图标\"\"\"
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
    \"\"\"创建勾选图标\"\"\"
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
    \"\"\"创建单选按钮指示器图标\"\"\"
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
    \"\"\"为所有主题创建图标\"\"\"
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
"""
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("已创建简化版图标创建脚本，保存在", file_path)

if __name__ == "__main__":
    print("开始修改主题系统...")
    
    # 生成替换用的apply_theme方法
    create_replacement_theme_method()
    
    # 创建简化版图标创建脚本
    create_simplified_icon_script()
    
    # 尝试修改现有文件
    try:
        fix_settings_dialog_themes()
    except Exception as e:
        print(f"修改SettingsDialog时出错: {e}")
    
    try:
        fix_apply_theme_method()
    except Exception as e:
        print(f"修改apply_theme方法时出错: {e}")
    
    try:
        modify_test_style()
    except Exception as e:
        print(f"修改测试样式脚本时出错: {e}")
    
    try:
        delete_theme_files()
    except Exception as e:
        print(f"删除主题文件时出错: {e}")
    
    print("\n修改完成。如果自动修改失败，请使用生成的替换文件手动修改。")
    print("1. apply_theme_replacement.py - 包含新的apply_theme方法")
    print("2. create_theme_icons.py - 简化版图标创建脚本")
    
    input("按回车键退出...") 