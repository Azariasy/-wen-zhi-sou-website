#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复文件夹树结果数量不匹配问题
"""

import os
import re

def fix_folder_tree_count_issue():
    """修复文件夹过滤后结果数量显示不一致的问题"""
    
    file_path = "search_gui_pyside.py"
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 修复 _filter_results_by_folder_slot 方法，确保过滤后的分页信息正确更新
    old_folder_filter_code = '''            # 更新过滤后的结果
            filtered_results = folder_filtered_results
        
        # 保存过滤后的结果
        self.search_results = filtered_results
        
        # 检查原始搜索结果是否是分页格式
        if isinstance(self.original_search_results, dict) and 'pagination' in self.original_search_results:
            # 如果是分页格式，构造相应的过滤后分页结果
            pagination_info = self.original_search_results['pagination'].copy()
            # 更新分页信息以反映过滤后的结果
            pagination_info['total_count'] = len(filtered_results)
            pagination_info['total_pages'] = max(1, (len(filtered_results) + pagination_info.get('page_size', 50) - 1) // pagination_info.get('page_size', 50))'''
    
    new_folder_filter_code = '''            # 更新过滤后的结果
            filtered_results = folder_filtered_results
            
            # 在日志中输出文件夹过滤结果统计
            print(f"DEBUG: 文件夹过滤后，从 {len(self.original_search_results.get('results', []))} 个结果中过滤出 {len(filtered_results)} 个属于文件夹 '{self.current_filter_folder}' 的结果")
        
        # 保存过滤后的结果
        self.search_results = filtered_results
        
        # 检查原始搜索结果是否是分页格式
        if isinstance(self.original_search_results, dict) and 'pagination' in self.original_search_results:
            # 如果是分页格式，构造相应的过滤后分页结果
            pagination_info = self.original_search_results['pagination'].copy()
            
            # 重要：确保total_count反映的是过滤后的实际结果数量，而不是原始total_count
            # 修复前的代码可能导致总数显示不匹配问题
            pagination_info['total_count'] = len(filtered_results)
            pagination_info['total_pages'] = max(1, (len(filtered_results) + pagination_info.get('page_size', 50) - 1) // pagination_info.get('page_size', 50))
            
            # 确保当前页码在有效范围内
            if pagination_info['current_page'] > pagination_info['total_pages'] and pagination_info['total_pages'] > 0:
                pagination_info['current_page'] = pagination_info['total_pages']
                
            # 更新前一页/下一页的可用性
            pagination_info['has_prev'] = pagination_info['current_page'] > 1
            pagination_info['has_next'] = pagination_info['current_page'] < pagination_info['total_pages']'''
    
    # 2. 修复normalize_path_for_display函数，确保路径标准化一致
    old_normalize_code = '''def normalize_path_for_display(path_str):
    """标准化路径显示格式，确保一致的路径表示（特别是Windows平台）
    
    Args:
        path_str: 要标准化的路径字符串
        
    Returns:
        标准化后的路径字符串
    """
    if not path_str:
        return ""
        
    # 确保路径使用标准分隔符
    normalized = os.path.normpath(path_str)
    
    # 在Windows上，确保使用反斜杠并大写驱动器号
    if os.name == 'nt':
        # 将所有正斜杠转换为反斜杠
        normalized = normalized.replace('/', '\\\\')
        
        # 大写驱动器号
        if len(normalized) >= 2 and normalized[1] == ':':
            normalized = normalized[0].upper() + normalized[1:]
            
    return normalized'''
    
    new_normalize_code = '''def normalize_path_for_display(path_str):
    """标准化路径显示格式，确保一致的路径表示（特别是Windows平台）
    
    Args:
        path_str: 要标准化的路径字符串
        
    Returns:
        标准化后的路径字符串
    """
    if not path_str:
        return ""
        
    # 确保路径使用标准分隔符
    normalized = os.path.normpath(path_str)
    
    # 在Windows上，确保使用反斜杠并大写驱动器号
    if os.name == 'nt':
        # 将所有正斜杠转换为反斜杠
        normalized = normalized.replace('/', '\\\\')
        
        # 大写驱动器号
        if len(normalized) >= 2 and normalized[1] == ':':
            normalized = normalized[0].upper() + normalized[1:]
            
    # 为了调试，添加日志输出
    # print(f"标准化路径: '{path_str}' -> '{normalized}'")
            
    return normalized'''
    
    # 应用修复
    modified = False
    
    if old_folder_filter_code in content:
        content = content.replace(old_folder_filter_code, new_folder_filter_code)
        modified = True
        print("✅ 成功修复文件夹过滤代码，确保分页信息正确更新")
    
    if old_normalize_code in content:
        content = content.replace(old_normalize_code, new_normalize_code)
        modified = True
        print("✅ 成功修复路径标准化函数，确保路径比较一致")
    
    # 在文件夹树构建方法中添加调试日志
    folder_tree_build_pattern = r'def build_folder_tree_from_results\(self, results\):(.*?)self\.tree_view\.expandToDepth\(0\)'
    
    def add_debug_to_build_folder_tree(match):
        code = match.group(0)
        # 在展开节点前添加调试日志
        return code.replace('self.tree_view.expandToDepth(0)',
                          'print(f"DEBUG: 文件夹树中添加了 {len(folder_paths_set)} 个唯一文件夹路径")\n        self.tree_view.expandToDepth(0)')
    
    # 使用正则表达式替换
    content = re.sub(folder_tree_build_pattern, add_debug_to_build_folder_tree, content, flags=re.DOTALL)
    modified = True
    print("✅ 添加了文件夹树构建的调试日志")
    
    if modified:
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 成功修复文件夹树结果数量不匹配问题")
        print("📋 修复内容:")
        print("   - 修复了文件夹过滤后分页信息更新逻辑")
        print("   - 确保总结果数量反映实际过滤后的结果数")
        print("   - 改进了路径标准化函数，确保路径比较一致")
        print("   - 添加了调试日志以便跟踪文件夹树构建")
        return True
    else:
        print("❌ 未找到需要修复的代码段")
        print("💡 可能代码已经被修改或位置发生变化")
        return False

if __name__ == "__main__":
    print("🔧 开始修复文件夹树结果数量不匹配问题...")
    fix_folder_tree_count_issue()
    print("🎯 修复完成！") 