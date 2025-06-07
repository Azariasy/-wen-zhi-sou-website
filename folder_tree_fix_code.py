#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件夹树问题修复代码

使用说明：
1. 将 normalize_path_for_display 函数添加到 search_gui_pyside.py 的顶部
2. 替换 FolderTreeWidget 类中的相关方法
3. 更新文件夹过滤逻辑
"""

import os
from pathlib import Path


用于显示的路径标准化函数

与document_search.py中的normalize_path_for_index保持一致
但专门用于前端显示

def normalize_path_for_display(path_str):
    """用于显示的路径标准化函数"""
    if not path_str:
        return ""
        
    try:
        # 对于压缩包内的文件特殊处理
        if "::" in path_str:
            archive_path, internal_path = path_str.split("::", 1)
            # 分别标准化压缩包路径和内部路径
            norm_archive = normalize_path_for_display(archive_path)
            # 内部路径只需要统一分隔符
            norm_internal = internal_path.replace('\\', '/')
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
            norm_path = norm_path.replace('/', '\\')
            # 驱动器字母统一大写（与Windows系统一致）
            if len(norm_path) >= 2 and norm_path[1] == ':':
                norm_path = norm_path[0].upper() + norm_path[1:]
        else:
            # Unix系统统一使用正斜杠
            norm_path = norm_path.replace('\\', '/')
            
        return norm_path
    except Exception as e:
        print(f"路径标准化错误 ({path_str}): {e}")
        return path_str


# 修复FolderTreeWidget的_add_folder_path方法
def _add_folder_path_fixed(self, folder_path):
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
            self.path_items[normalized_current_path] = new_item

# 修复build_folder_tree_from_results方法
def build_folder_tree_from_results_fixed(self, results):
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
    self.tree_view.expandToDepth(0)



# 修复_filter_results_by_type_slot方法中的文件夹过滤逻辑
def _filter_results_by_folder_fixed(self, filtered_results):
    """修复的文件夹过滤逻辑
    
    Args:
        filtered_results: 已经按文件类型过滤的结果
        
    Returns:
        按文件夹过滤后的结果
    """
    if not self.filtered_by_folder or not self.current_filter_folder:
        return filtered_results
        
    # 标准化当前过滤文件夹路径
    normalized_filter_folder = normalize_path_for_display(self.current_filter_folder)
    
    folder_filtered_results = []
    for result in filtered_results:
        file_path = result.get('file_path', '')
        if not file_path:
            continue
            
        # 处理存档文件中的项目
        if '::' in file_path:
            archive_path = file_path.split('::', 1)[0]
            folder_path = str(Path(archive_path).parent)
        else:
            folder_path = str(Path(file_path).parent)
            
        # 标准化文件路径的文件夹部分
        normalized_folder_path = normalize_path_for_display(folder_path)
        
        # 检查文件路径是否属于所选文件夹
        is_match = False
        if normalized_filter_folder.endswith(':\\') or normalized_filter_folder.endswith(':/'):  # 根目录情况
            # 对于根目录，检查是否以此开头
            is_match = (normalized_folder_path.startswith(normalized_filter_folder.rstrip('\\/:')) or 
                       normalized_folder_path == normalized_filter_folder.rstrip('\\/:'))
        else:
            # 非根目录的正常情况
            is_match = (normalized_folder_path == normalized_filter_folder or 
                       normalized_folder_path.startswith(normalized_filter_folder + os.path.sep))
        
        if is_match:
            folder_filtered_results.append(result)
            
    return folder_filtered_results



def get_folder_statistics(results):
    """获取文件夹统计信息（修复版）
    
    Args:
        results: 搜索结果列表
        
    Returns:
        dict: 文件夹路径到结果数量的映射
    """
    folder_stats = {}
    
    for result in results:
        file_path = result.get('file_path', '')
        if not file_path:
            continue
            
        # 处理存档文件中的项目
        if '::' in file_path:
            archive_path = file_path.split('::', 1)[0]
            folder_path = str(Path(archive_path).parent)
        else:
            folder_path = str(Path(file_path).parent)
            
        # 标准化文件夹路径
        normalized_folder_path = normalize_path_for_display(folder_path)
        
        # 统计每个文件夹的结果数量
        if normalized_folder_path in folder_stats:
            folder_stats[normalized_folder_path] += 1
        else:
            folder_stats[normalized_folder_path] = 1
    
    return folder_stats

def debug_folder_distribution(results):
    """调试文件夹分布情况
    
    Args:
        results: 搜索结果列表
    """
    print("\n=== 文件夹分布调试信息 ===")
    folder_stats = get_folder_statistics(results)
    
    total_files = len(results)
    total_counted = sum(folder_stats.values())
    
    print(f"总搜索结果数: {total_files}")
    print(f"统计的文件数: {total_counted}")
    
    if total_files != total_counted:
        print(f"⚠️  数量不匹配！差异: {total_files - total_counted}")
    
    print("\n文件夹统计:")
    for folder_path, count in sorted(folder_stats.items()):
        print(f"  {folder_path}: {count}个文件")
    
    print("=========================\n")

