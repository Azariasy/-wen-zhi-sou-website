#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接应用文件夹树修复的脚本

这个脚本会：
1. 在search_gui_pyside.py文件开头添加路径标准化函数
2. 修复FolderTreeWidget类的相关方法
3. 修复文件夹过滤逻辑
"""

import os
import re
from pathlib import Path

def add_normalize_function():
    """在search_gui_pyside.py中添加路径标准化函数"""
    
    normalize_function = '''
# --- 路径标准化函数 ---
def normalize_path_for_display(path_str):
    """
    用于显示的路径标准化函数
    
    与document_search.py中的normalize_path_for_index保持一致
    但专门用于前端显示，解决文件夹树路径大小写不一致问题
    """
    if not path_str:
        return ""
        
    try:
        # 对于压缩包内的文件特殊处理
        if "::" in path_str:
            archive_path, internal_path = path_str.split("::", 1)
            # 分别标准化压缩包路径和内部路径
            norm_archive = normalize_path_for_display(archive_path)
            # 内部路径只需要统一分隔符
            norm_internal = internal_path.replace('\\\\', '/')
            return f"{norm_archive}::{norm_internal}"
            
        # 普通文件路径处理
        try:
            # 尝试使用Path对象处理
            path_obj = Path(path_str)
            if path_obj.exists():
                # 如果路径存在，使用resolve()获取绝对路径
                norm_path = str(path_obj.resolve())
            else:
                # 如果路径不存在，则只进行基本处理
                norm_path = str(path_obj)
        except:
            # 路径无法通过Path对象处理，直接进行字符串处理
            norm_path = path_str
        
        # Windows路径标准化
        if os.name == 'nt':  # Windows系统
            # 统一使用反斜杠
            norm_path = norm_path.replace('/', '\\\\')
            # 驱动器字母统一大写（与Windows系统一致）
            if len(norm_path) >= 2 and norm_path[1] == ':':
                norm_path = norm_path[0].upper() + norm_path[1:]
        else:
            # Unix系统统一使用正斜杠
            norm_path = norm_path.replace('\\\\', '/')
            
        return norm_path
    except Exception as e:
        print(f"路径标准化错误 ({path_str}): {e}")
        return path_str

'''
    
    # 读取文件内容
    with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找插入位置（在导入后、第一个函数定义前）
    insert_pattern = r'(# --- 添加资源文件路径解析器 ---)'
    
    if re.search(insert_pattern, content):
        # 在"添加资源文件路径解析器"注释前插入
        modified_content = re.sub(
            insert_pattern,
            normalize_function + r'\1',
            content
        )
        
        # 写回文件
        with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print("✅ 成功添加路径标准化函数")
        return True
    else:
        print("❌ 未找到合适的插入位置")
        return False

def fix_folder_tree_methods():
    """修复FolderTreeWidget类的方法"""
    
    # 读取文件内容
    with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复build_folder_tree_from_results方法
    old_build_method = r'''    def build_folder_tree_from_results\(self, results\):
        """从搜索结果中构建文件夹树
        
        Args:
            results: 搜索结果列表
        """
        self\.clear\(\)
        
        # 收集所有唯一的文件夹路径
        for result in results:
            file_path = result\.get\('file_path', ''\)
            if not file_path:
                continue
                
            # 处理存档文件中的项目
            if '::' in file_path:
                # 对于存档内的文件，只显示存档文件所在的文件夹
                archive_path = file_path\.split\('::', 1\)\[0\]
                folder_path = str\(Path\(archive_path\)\.parent\)
            else:
                folder_path = str\(Path\(file_path\)\.parent\)
                
            self\._add_folder_path\(folder_path\)
        
        # 展开所有顶层节点
        self\.tree_view\.expandToDepth\(0\)'''
    
    new_build_method = '''    def build_folder_tree_from_results(self, results):
        """从搜索结果中构建文件夹树（修复版）
        
        Args:
            results: 搜索结果列表
        """
        self.clear()
        
        # 收集所有唯一的文件夹路径（使用标准化路径）
        folder_paths_set = set()
        
        for result in results:
            file_path = result.get('file_path', '')
            if not file_path:
                continue
                
            # 处理存档文件中的项目
            if '::' in file_path:
                # 对于存档内的文件，只显示存档文件所在的文件夹
                archive_path = file_path.split('::', 1)[0]
                folder_path = str(Path(archive_path).parent)
            else:
                folder_path = str(Path(file_path).parent)
                
            # 标准化文件夹路径
            normalized_folder_path = normalize_path_for_display(folder_path)
            folder_paths_set.add(normalized_folder_path)
        
        # 添加所有唯一的文件夹路径
        for folder_path in sorted(folder_paths_set):
            self._add_folder_path(folder_path)
        
        # 展开所有顶层节点
        self.tree_view.expandToDepth(0)'''
    
    # 应用修复
    if re.search(old_build_method, content, re.DOTALL):
        content = re.sub(old_build_method, new_build_method, content, flags=re.DOTALL)
        print("✅ 修复了build_folder_tree_from_results方法")
    else:
        print("⚠️  未找到build_folder_tree_from_results方法，可能已经被修改")
    
    # 修复_add_folder_path方法
    old_add_method = r'''    def _add_folder_path\(self, folder_path\):
        """添加文件夹路径到树中，确保创建完整的路径层次结构
        
        Args:
            folder_path: 要添加的文件夹路径
        """
        if folder_path in self\.folder_paths:
            return
            
        self\.folder_paths\.add\(folder_path\)
        
        # 创建路径的各个部分
        path = Path\(folder_path\)
        parts = list\(path\.parts\)
        
        # 找出根目录（盘符或最顶层目录）
        root_part = parts\[0\]
        
        # 从根目录开始构建路径
        current_path = root_part
        
        # 查找或创建根目录项目
        root_item = None
        for i in range\(self\.tree_model\.rowCount\(\)\):
            item = self\.tree_model\.item\(i\)
            if item\.text\(\) == root_part:
                root_item = item
                break
                
        # 如果根目录不存在，创建它
        if root_item is None:
            root_item = QStandardItem\(root_part\)
            root_item\.setData\(root_part\)
            self\.tree_model\.appendRow\(root_item\)
            self\.path_items\[root_part\] = root_item
            
        # 构建路径的其余部分
        parent_item = root_item
        for i in range\(1, len\(parts\)\):
            current_path = os\.path\.join\(current_path, parts\[i\]\)
            
            # 检查此部分是否已存在
            child_exists = False
            for j in range\(parent_item\.rowCount\(\)\):
                child = parent_item\.child\(j\)
                if child\.text\(\) == parts\[i\]:
                    parent_item = child
                    child_exists = True
                    break
                    
            # 如果不存在，创建它
            if not child_exists:
                new_item = QStandardItem\(parts\[i\]\)
                new_item\.setData\(current_path\)
                parent_item\.appendRow\(new_item\)
                parent_item = new_item
                self\.path_items\[current_path\] = new_item'''
    
    new_add_method = '''    def _add_folder_path(self, folder_path):
        """添加文件夹路径到树中，确保创建完整的路径层次结构（修复版）
        
        Args:
            folder_path: 要添加的文件夹路径
        """
        # 标准化路径以避免大小写不一致
        normalized_folder_path = normalize_path_for_display(folder_path)
        
        if normalized_folder_path in self.folder_paths:
            return
            
        self.folder_paths.add(normalized_folder_path)
        
        # 创建路径的各个部分
        path = Path(normalized_folder_path)
        parts = list(path.parts)
        
        # 找出根目录（盘符或最顶层目录）
        root_part = parts[0]
        
        # 从根目录开始构建路径
        current_path = root_part
        
        # 查找或创建根目录项目（使用标准化路径比较）
        root_item = None
        for i in range(self.tree_model.rowCount()):
            item = self.tree_model.item(i)
            existing_root = normalize_path_for_display(item.text())
            if existing_root == normalize_path_for_display(root_part):
                root_item = item
                break
                
        # 如果根目录不存在，创建它
        if root_item is None:
            root_item = QStandardItem(root_part)
            root_item.setData(current_path)
            self.tree_model.appendRow(root_item)
            self.path_items[current_path] = root_item
            
        # 构建路径的其余部分
        parent_item = root_item
        for i in range(1, len(parts)):
            current_path = os.path.join(current_path, parts[i])
            normalized_current_path = normalize_path_for_display(current_path)
            
            # 检查此部分是否已存在（使用标准化路径比较）
            child_exists = False
            for j in range(parent_item.rowCount()):
                child = parent_item.child(j)
                if child and normalize_path_for_display(child.data()) == normalized_current_path:
                    parent_item = child
                    child_exists = True
                    break
                    
            # 如果不存在，创建它
            if not child_exists:
                new_item = QStandardItem(parts[i])
                new_item.setData(normalized_current_path)
                parent_item.appendRow(new_item)
                parent_item = new_item
                self.path_items[normalized_current_path] = new_item'''
    
    # 应用修复
    if re.search(old_add_method, content, re.DOTALL):
        content = re.sub(old_add_method, new_add_method, content, flags=re.DOTALL)
        print("✅ 修复了_add_folder_path方法")
    else:
        print("⚠️  未找到_add_folder_path方法，可能已经被修改")
    
    # 写回文件
    with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def fix_folder_filter_logic():
    """修复文件夹过滤逻辑"""
    
    # 读取文件内容
    with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并修复文件夹过滤逻辑
    old_filter_logic = r'''                # 检查文件路径是否属于所选文件夹
                # 特殊处理根目录情况
                is_match = False
                if self\.current_filter_folder\.endswith\(':\\\\\'\):  # 根目录情况
                    # 对于D:\\这样的根目录，直接检查文件路径是否以此开头
                    is_match = folder_path\.startswith\(self\.current_filter_folder\) or folder_path == self\.current_filter_folder\[:-1\]
                else:
                    # 非根目录的正常情况
                    is_match = \(folder_path == self\.current_filter_folder or 
                               folder_path\.startswith\(self\.current_filter_folder \+ os\.path\.sep\)\)'''
    
    new_filter_logic = '''                # 标准化文件路径的文件夹部分
                normalized_folder_path = normalize_path_for_display(folder_path)
                normalized_filter_folder = normalize_path_for_display(self.current_filter_folder)
                
                # 检查文件路径是否属于所选文件夹
                is_match = False
                if normalized_filter_folder.endswith(':\\\\') or normalized_filter_folder.endswith(':/'):  # 根目录情况
                    # 对于根目录，检查是否以此开头
                    is_match = (normalized_folder_path.startswith(normalized_filter_folder.rstrip('\\\\/:')) or 
                               normalized_folder_path == normalized_filter_folder.rstrip('\\\\/:'))
                else:
                    # 非根目录的正常情况
                    is_match = (normalized_folder_path == normalized_filter_folder or 
                               normalized_folder_path.startswith(normalized_filter_folder + os.path.sep))'''
    
    # 应用修复
    if re.search(old_filter_logic, content, re.DOTALL):
        content = re.sub(old_filter_logic, new_filter_logic, content, flags=re.DOTALL)
        print("✅ 修复了文件夹过滤逻辑")
    else:
        print("⚠️  未找到文件夹过滤逻辑，可能已经被修改")
    
    # 写回文件
    with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    """主函数"""
    print("开始应用文件夹树修复...")
    
    # 备份原文件
    import shutil
    shutil.copy2('search_gui_pyside.py', 'search_gui_pyside.py.backup')
    print("✅ 已备份原文件到 search_gui_pyside.py.backup")
    
    try:
        # 1. 添加路径标准化函数
        if add_normalize_function():
            print("✅ 步骤1完成：添加路径标准化函数")
        
        # 2. 修复文件夹树方法
        if fix_folder_tree_methods():
            print("✅ 步骤2完成：修复文件夹树方法")
        
        # 3. 修复文件夹过滤逻辑
        if fix_folder_filter_logic():
            print("✅ 步骤3完成：修复文件夹过滤逻辑")
        
        print("\n🎉 所有修复已完成！")
        print("\n修复内容总结:")
        print("1. 添加了统一的路径标准化函数")
        print("2. 修复了文件夹树构建逻辑，避免大小写重复")
        print("3. 修复了文件夹过滤逻辑，确保统计准确")
        
        print("\n现在可以重新运行程序测试修复效果。")
        
    except Exception as e:
        print(f"❌ 修复过程中出错: {e}")
        # 恢复备份
        shutil.copy2('search_gui_pyside.py.backup', 'search_gui_pyside.py')
        print("🔄 已恢复原文件")

if __name__ == "__main__":
    main() 