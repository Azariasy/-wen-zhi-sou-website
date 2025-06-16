#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主题管理工具模块

统一管理所有主题配色、样式生成等功能
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ThemeColors:
    """主题颜色配置数据类"""
    primary: str           # 主色调
    secondary: str         # 次要色调  
    background: str        # 背景色
    surface: str          # 表面色
    text_primary: str     # 主要文本色
    text_secondary: str   # 次要文本色
    border: str           # 边框色
    hover: str            # 悬停色
    accent: str           # 强调色
    
    # 语义化颜色
    success: str          # 成功色
    warning: str          # 警告色
    error: str            # 错误色
    info: str             # 信息色
    
    # 渐变色
    gradient_start: str   # 渐变开始色
    gradient_end: str     # 渐变结束色


class ThemeManager:
    """主题管理器"""
    
    # 定义所有可用主题
    THEMES = {
        "现代蓝": ThemeColors(
            primary="#007ACC",
            secondary="#005A9E", 
            background="#F8FAFE",
            surface="#FFFFFF",
            text_primary="#1E1E1E",
            text_secondary="#6B7280",
            border="#E1E5E9",
            hover="#E3F2FD",
            accent="#FF6B35",
            success="#10B981",
            warning="#F59E0B", 
            error="#EF4444",
            info="#3B82F6",
            gradient_start="#007ACC",
            gradient_end="#00A8E8"
        ),
        
        "现代紫": ThemeColors(
            primary="#8B5CF6",
            secondary="#7C3AED",
            background="#FDFBFF", 
            surface="#FFFFFF",
            text_primary="#1E1E1E",
            text_secondary="#6B7280",
            border="#E9E3FF",
            hover="#F3F0FF",
            accent="#06B6D4",
            success="#10B981",
            warning="#F59E0B",
            error="#EF4444", 
            info="#8B5CF6",
            gradient_start="#8B5CF6",
            gradient_end="#A855F7"
        ),
        
        "现代红": ThemeColors(
            primary="#DC2626",
            secondary="#B91C1C",
            background="#FFFBFA",
            surface="#FFFFFF", 
            text_primary="#1E1E1E",
            text_secondary="#6B7280",
            border="#FEE2E2",
            hover="#FEF2F2",
            accent="#059669",
            success="#10B981",
            warning="#F59E0B",
            error="#DC2626",
            info="#3B82F6",
            gradient_start="#DC2626", 
            gradient_end="#F87171"
        ),
        
        "现代橙": ThemeColors(
            primary="#EA580C",
            secondary="#C2410C",
            background="#FFFBF5",
            surface="#FFFFFF",
            text_primary="#1E1E1E", 
            text_secondary="#6B7280",
            border="#FED7AA",
            hover="#FFF7ED",
            accent="#0D9488",
            success="#10B981",
            warning="#EA580C",
            error="#EF4444",
            info="#3B82F6",
            gradient_start="#EA580C",
            gradient_end="#FB923C"
        ),
        

    }
    
    def __init__(self, default_theme: str = "现代蓝"):
        """初始化主题管理器"""
        self.current_theme = default_theme
        
    def get_theme_colors(self, theme_name: str = None) -> ThemeColors:
        """获取指定主题的颜色配置"""
        theme_name = theme_name or self.current_theme
        if theme_name not in self.THEMES:
            theme_name = "现代蓝"  # 默认主题
        return self.THEMES[theme_name]
    
    def get_available_themes(self) -> list:
        """获取所有可用主题列表"""
        return list(self.THEMES.keys())
    
    def set_current_theme(self, theme_name: str):
        """设置当前主题"""
        if theme_name in self.THEMES:
            self.current_theme = theme_name
    
    def generate_button_style(self, 
                            button_type: str = "primary",
                            theme_name: str = None) -> str:
        """生成按钮样式字符串"""
        colors = self.get_theme_colors(theme_name)
        
        style_map = {
            "primary": {
                "bg": colors.primary,
                "hover": colors.secondary,
                "text": "#FFFFFF"
            },
            "secondary": {
                "bg": colors.surface,
                "hover": colors.hover,
                "text": colors.text_primary
            },
            "success": {
                "bg": colors.success,
                "hover": "#059669",
                "text": "#FFFFFF"
            },
            "warning": {
                "bg": colors.warning,
                "hover": "#D97706", 
                "text": "#FFFFFF"
            },
            "error": {
                "bg": colors.error,
                "hover": "#DC2626",
                "text": "#FFFFFF"
            }
        }
        
        style = style_map.get(button_type, style_map["primary"])
        
        return f"""
            QPushButton {{
                background-color: {style['bg']};
                color: {style['text']};
                border: 1px solid {colors.border};
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {style['hover']};
                border-color: {style['hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors.secondary};
            }}
            QPushButton:disabled {{
                background-color: {colors.border};
                color: {colors.text_secondary};
            }}
        """
    
    def generate_input_style(self, theme_name: str = None) -> str:
        """生成输入框样式"""
        colors = self.get_theme_colors(theme_name)
        
        return f"""
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {colors.surface};
                border: 1px solid {colors.border};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                color: {colors.text_primary};
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border-color: {colors.primary};
                outline: none;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {colors.text_secondary};
            }}
        """
    
    def generate_container_style(self, theme_name: str = None) -> str:
        """生成容器样式"""
        colors = self.get_theme_colors(theme_name)
        
        return f"""
            QWidget {{
                background-color: {colors.background};
                color: {colors.text_primary};
            }}
            QFrame {{
                border: 1px solid {colors.border};
                border-radius: 8px;
                background-color: {colors.surface};
            }}
            QScrollArea {{
                border: none;
                background-color: {colors.background};
            }}
        """
    
    def generate_full_application_style(self, theme_name: str = None) -> str:
        """生成完整应用程序样式"""
        colors = self.get_theme_colors(theme_name)
        
        return f"""
            /* 全局样式 */
            QMainWindow {{
                background-color: {colors.background};
                color: {colors.text_primary};
            }}
            
            /* 按钮样式 */
            {self.generate_button_style("primary", theme_name)}
            
            /* 输入框样式 */
            {self.generate_input_style(theme_name)}
            
            /* 容器样式 */
            {self.generate_container_style(theme_name)}
            
            /* 状态栏样式 */
            QStatusBar {{
                background-color: {colors.surface};
                border-top: 1px solid {colors.border};
                color: {colors.text_secondary};
            }}
            
            /* 进度条样式 */
            QProgressBar {{
                border: 1px solid {colors.border};
                border-radius: 4px;
                background-color: {colors.surface};
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: linear-gradient(to right, {colors.gradient_start}, {colors.gradient_end});
                border-radius: 3px;
            }}
            
            /* 滚动条样式 */
            QScrollBar:vertical {{
                background-color: {colors.background};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors.border};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors.text_secondary};
            }}
        """


def test_theme_manager():
    """测试主题管理器"""
    print("=== 主题管理器测试 ===")
    
    tm = ThemeManager()
    
    # 测试1: 获取主题列表
    themes = tm.get_available_themes()
    print(f"✅ 可用主题: {', '.join(themes)}")
    
    # 测试2: 获取主题颜色
    colors = tm.get_theme_colors("现代蓝")
    print(f"✅ 现代蓝主题主色调: {colors.primary}")
    
    # 测试3: 生成按钮样式
    style = tm.generate_button_style("primary", "现代蓝")
    print(f"✅ 按钮样式生成: {len(style)} 字符")
    
    # 测试4: 生成完整应用样式
    full_style = tm.generate_full_application_style("深色模式")
    print(f"✅ 完整样式生成: {len(full_style)} 字符")
    
    print("=== 主题管理器测试完成 ===")


if __name__ == "__main__":
    test_theme_manager() 