#!/usr/bin/env python
"""
创建样式表中使用的简单图标
"""
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QColor, QPixmap, QPen, QBrush, QPainterPath
from PySide6.QtWidgets import QApplication
import os
import sys

def save_pixmap(pixmap, filename):
    """将pixmap保存为png文件"""
    try:
        # 获取当前脚本目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(current_dir, filename)
        
        # 确保目录存在
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))
        
        # 保存图标
        success = pixmap.save(filepath)
        if success:
            print(f"成功保存图标: {filepath}")
        else:
            print(f"保存图标失败: {filepath}")
    except Exception as e:
        print(f"保存图标时出错: {e}")

def create_down_arrow():
    """创建下拉箭头图标"""
    print("正在创建下拉箭头图标...")
    
    size = 16
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 绘制箭头
    painter.setPen(QPen(QColor("#3498db"), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(QBrush(QColor("#3498db")))
    
    # 画箭头路径
    path = QPainterPath()
    path.moveTo(3, 6)
    path.lineTo(size/2, size-5)
    path.lineTo(size-3, 6)
    path.closeSubpath()
    
    painter.drawPath(path)
    painter.end()
    
    save_pixmap(pixmap, "down_arrow.png")

def create_checkmark():
    """创建勾选标记图标"""
    print("正在创建勾选标记图标...")
    
    size = 16
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 绘制勾选标记
    painter.setPen(QPen(QColor("white"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    
    # 画勾选标记路径
    path = QPainterPath()
    path.moveTo(3, 8)
    path.lineTo(7, 12)
    path.lineTo(13, 4)
    
    painter.drawPath(path)
    painter.end()
    
    save_pixmap(pixmap, "checkmark.png")

if __name__ == "__main__":
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    print("创建QApplication...")
    
    app = QApplication([])  # 需要QApplication来创建pixmap
    
    print("开始创建图标...")
    create_down_arrow()
    create_checkmark()
    print("图标创建完成") 