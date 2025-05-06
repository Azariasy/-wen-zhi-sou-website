#!/usr/bin/env python3
"""
测试主题样式和图标生成的测试脚本

此脚本创建一个带有主题切换功能的简单GUI界面，用于测试不同主题的样式和图标。
"""

import os
import sys
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QLabel, QComboBox, QLineEdit,
    QCheckBox, QRadioButton, QButtonGroup, QScrollArea,
    QGroupBox, QProgressBar, QTextEdit, QListWidget,
    QSlider
)
from PySide6.QtCore import Qt, QSettings, QStandardPaths, Signal, Slot

# 组织和应用名称，用于保存设置
ORGANIZATION_NAME = "开源搜索工具"
APPLICATION_NAME = "DocumentSearchToolPySide"

def create_icons():
    """创建测试所需的图标"""
    print("生成图标...")
    
    # 运行图标生成脚本
    try:
        # 使用简化版的图标创建脚本
        from create_theme_icons import create_all_theme_icons
        create_all_theme_icons()
    except Exception as e:
        print(f"图标创建失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("图标创建完成")

class MainWindow(QMainWindow):
    """测试主题的主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("主题测试工具")
        self.setMinimumSize(800, 600)
        
        # 应用设置
        self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        
        # 加载上次使用的主题
        initial_theme = self.settings.value("ui/theme", "现代蓝")
        
        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 主题选择器
        theme_layout = QHBoxLayout()
        theme_label = QLabel("主题:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["现代蓝", "现代绿", "现代紫"])
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        main_layout.addLayout(theme_layout)
        
        # 设置初始主题
        index = self.theme_combo.findText(initial_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        self.apply_theme(initial_theme)
        
        # 创建测试控件
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 按钮组
        button_group = QGroupBox("按钮")
        button_layout = QVBoxLayout(button_group)
        button_layout.addWidget(QPushButton("标准按钮"))
        disabled_button = QPushButton("禁用按钮")
        disabled_button.setEnabled(False)
        button_layout.addWidget(disabled_button)
        scroll_layout.addWidget(button_group)
        
        # 输入组
        input_group = QGroupBox("输入控件")
        input_layout = QVBoxLayout(input_group)
        input_layout.addWidget(QLabel("文本输入:"))
        input_layout.addWidget(QLineEdit("示例文本"))
        input_layout.addWidget(QLabel("下拉框:"))
        combo = QComboBox()
        combo.addItems(["选项 1", "选项 2", "选项 3"])
        input_layout.addWidget(combo)
        input_layout.addWidget(QLabel("文本区域:"))
        input_layout.addWidget(QTextEdit("这是一个多行文本编辑区域。\n可以输入多行文本。"))
        scroll_layout.addWidget(input_group)
        
        # 选择组
        selection_group = QGroupBox("选择控件")
        selection_layout = QVBoxLayout(selection_group)
        selection_layout.addWidget(QCheckBox("复选框选项 1"))
        checked_checkbox = QCheckBox("复选框选项 2 (已选)")
        checked_checkbox.setChecked(True)
        selection_layout.addWidget(checked_checkbox)
        
        radio_layout = QVBoxLayout()
        radio_group = QButtonGroup(self)
        radio1 = QRadioButton("单选按钮 1")
        radio2 = QRadioButton("单选按钮 2 (已选)")
        radio2.setChecked(True)
        radio3 = QRadioButton("单选按钮 3")
        radio_group.addButton(radio1)
        radio_group.addButton(radio2)
        radio_group.addButton(radio3)
        radio_layout.addWidget(radio1)
        radio_layout.addWidget(radio2)
        radio_layout.addWidget(radio3)
        selection_layout.addLayout(radio_layout)
        scroll_layout.addWidget(selection_group)
        
        # 列表组
        list_group = QGroupBox("列表控件")
        list_layout = QVBoxLayout(list_group)
        list_widget = QListWidget()
        list_widget.addItems([f"列表项 {i}" for i in range(1, 11)])
        list_layout.addWidget(list_widget)
        scroll_layout.addWidget(list_group)
        
        # 滑块和进度条组
        slider_group = QGroupBox("滑块和进度条")
        slider_layout = QVBoxLayout(slider_group)
        slider_layout.addWidget(QLabel("滑块:"))
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(50)
        slider_layout.addWidget(slider)
        slider_layout.addWidget(QLabel("进度条:"))
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(75)
        slider_layout.addWidget(progress)
        scroll_layout.addWidget(slider_group)
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
    
    @Slot(str)
    def on_theme_changed(self, theme_name):
        """当主题选择更改时调用"""
        self.apply_theme(theme_name)
        self.settings.setValue("ui/theme", theme_name)
    
    def apply_theme(self, theme_name):
        """应用选定的主题"""
        app = QApplication.instance()
        
        if theme_name == "现代蓝":
            self._apply_theme_from_file("blue_style.qss", "checkmark_blue.png")
            
        elif theme_name == "现代绿":
            self._apply_theme_from_file("green_style.qss", "checkmark_green.png")
            
        elif theme_name == "现代紫":
            self._apply_theme_from_file("purple_style.qss", "checkmark_purple.png")
            
        else:
            # 对于任何未知主题，使用现代蓝
            self._apply_theme_from_file("blue_style.qss", "checkmark_blue.png")
    
    def _apply_theme_from_file(self, style_filename, checkmark_filename):
        """从QSS文件应用主题"""
        app = QApplication.instance()
        
        try:
            # 尝试加载样式表
            style_path = os.path.join(os.path.dirname(__file__), style_filename)
            if os.path.exists(style_path):
                with open(style_path, "r", encoding="utf-8") as f:
                    stylesheet = f.read()
                # 确保QSS使用正确的checkmark图标
                if "image: url(checkmark.png)" in stylesheet:
                    stylesheet = stylesheet.replace("image: url(checkmark.png)", f"image: url({checkmark_filename})")
                
                # 根据主题设置正确的进度条颜色
                progress_color = "#3498db"  # 默认蓝色
                if "green_style" in style_filename:
                    progress_color = "#2ecc71"  # 绿色
                elif "purple_style" in style_filename:
                    progress_color = "#9b59b6"  # 紫色
                
                # 确保QProgressBar::chunk使用正确的主题颜色
                if "QProgressBar::chunk" in stylesheet:
                    import re
                    # 使用正则表达式替换背景色
                    stylesheet = re.sub(
                        r'QProgressBar::chunk\s*\{\s*background-color:\s*#[0-9a-fA-F]+',
                        f'QProgressBar::chunk {{ background-color: {progress_color}',
                        stylesheet
                    )
                
                app.setStyleSheet(stylesheet)
                print(f"Applied theme from {style_filename}")
            else:
                print(f"Style file not found: {style_path}")
                app.setStyleSheet("")
        except Exception as e:
            print(f"Error applying theme: {e}")
            app.setStyleSheet("")

def main():
    """主程序入口"""
    print("Python版本:", sys.version)
    print("当前工作目录:", os.getcwd())
    
    # 创建图标
    create_icons()
    
    # 启动应用
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 