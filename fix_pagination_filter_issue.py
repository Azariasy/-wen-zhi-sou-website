#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复文件类型筛选与分页交互的问题

问题描述：
1. 搜索"计划"得到2页结果
2. 选择Word筛选后得到1页结果  
3. 取消Word筛选后应该回到2页结果，但现在停留在1页

根本原因：
当没有选中文件类型时，_filter_results_by_type_slot方法使用缓存的当前页结果，
而不是重新执行搜索获取完整的分页结果。

解决方案：
修改_filter_results_by_type_slot方法，当没有选中文件类型且处于分页环境时，
重新执行搜索以获取完整的分页结果。
"""

import re

def fix_pagination_filter_issue():
    print("开始修复分页筛选交互问题...")
    
    with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("✅ 读取文件成功")
    
    # 查找需要替换的具体代码段 - 基于实际文件内容
    problem_code = '''        # 如果没有选择文件类型，使用所有原始结果
        if not checked_types:
            print("DEBUG: No file types checked, using all original results")  # DEBUG
            # 检查是否有分页格式的原始结果
            if isinstance(self.original_search_results, dict) and 'results' in self.original_search_results:
                filtered_results = self.original_search_results['results'].copy()
            else:
                filtered_results = self.original_search_results.copy() if isinstance(self.original_search_results, list) else []'''
    
    if problem_code not in content:
        print("❌ 未找到需要修复的代码段")
        print("尝试搜索部分关键内容...")
        if "# 如果没有选择文件类型，使用所有原始结果" in content:
            print("✅ 找到关键注释")
        else:
            print("❌ 未找到关键注释")
        return False
    
    print("✅ 找到需要修复的代码段")
    
    # 新的代码段 - 添加分页环境检查
    fixed_code = '''        # 如果没有选择文件类型，需要检查是否重新执行搜索以获取完整分页结果
        if not checked_types:
            print("DEBUG: No file types checked, checking pagination context")  # DEBUG
            # 检查是否有当前搜索参数并且处于分页环境
            if hasattr(self, 'current_search_params') and self.current_search_params and hasattr(self, 'current_page'):
                # 当前处于分页结果状态，重新执行搜索以获取完整的分页结果
                print("DEBUG: In pagination context, re-triggering search for full results")  # DEBUG
                self.current_page = 1  # 重置到第1页
                self._perform_paginated_search()
                return
            else:
                # 非分页环境，使用本地结果处理
                print("DEBUG: Not in pagination context, using local cached results")  # DEBUG
                # 检查是否有分页格式的原始结果
                if isinstance(self.original_search_results, dict) and 'results' in self.original_search_results:
                    filtered_results = self.original_search_results['results'].copy()
                else:
                    filtered_results = self.original_search_results.copy() if isinstance(self.original_search_results, list) else []'''
    
    # 替换代码
    new_content = content.replace(problem_code, fixed_code)
    
    if new_content == content:
        print("❌ 代码替换失败，内容未改变")
        return False
    
    # 写入文件
    with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 成功修复分页筛选交互问题")
    print("修复内容：")
    print("- 当没有选中文件类型时，检查是否处于分页环境")
    print("- 如果在分页环境下，重新执行搜索获取完整结果")
    print("- 如果不在分页环境，使用本地缓存结果")
    print("- 重置到第1页以确保用户看到完整的第一页结果")
    
    return True

if __name__ == "__main__":
    success = fix_pagination_filter_issue()
    if success:
        print("\n🎉 修复完成！请测试以下场景：")
        print("1. 搜索一个词（如'计划'）确保得到多页结果")
        print("2. 选择Word文件类型筛选，观察结果减少")
        print("3. 取消Word筛选，应该重新回到原本的多页结果")
        print("4. 验证分页控件显示正确的页数")
    else:
        print("\n❌ 修复失败，请检查文件内容") 