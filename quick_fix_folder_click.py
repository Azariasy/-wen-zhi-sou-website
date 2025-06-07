#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速修复文件夹树点击事件的脚本
解决路径大小写不一致的问题
"""

import os
import re

def fix_folder_click_method():
    """修复_on_tree_item_clicked方法"""
    
    file_path = "search_gui_pyside.py"
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并替换_on_tree_item_clicked方法
    old_method = '''    def _on_tree_item_clicked(self, index):
        """当用户点击树中的项目时处理"""
        item = self.tree_model.itemFromIndex(index)
        if item and item.data():
            folder_path = item.data()
            print(f"选择了文件夹: {folder_path}")
            self.folderSelected.emit(folder_path)'''
    
    new_method = '''    def _on_tree_item_clicked(self, index):
        """当用户点击树中的项目时处理"""
        item = self.tree_model.itemFromIndex(index)
        if item and item.data():
            folder_path = item.data()
            # 标准化路径以确保一致性
            normalized_folder_path = normalize_path_for_display(folder_path)
            print(f"选择了文件夹: {normalized_folder_path}")
            self.folderSelected.emit(normalized_folder_path)'''
    
    # 执行替换
    if old_method in content:
        content = content.replace(old_method, new_method)
        print("已修复 _on_tree_item_clicked 方法")
    else:
        print("未找到需要修复的 _on_tree_item_clicked 方法")
        return False
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

if __name__ == "__main__":
    print("开始修复文件夹树点击事件...")
    success = fix_folder_click_method()
    if success:
        print("修复完成！")
    else:
        print("修复失败！") 