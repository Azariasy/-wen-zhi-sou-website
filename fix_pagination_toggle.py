#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复折叠/展开时页码消失问题的脚本
"""

import os
import re

def fix_pagination_toggle():
    """修复折叠/展开时页码消失的问题"""
    
    file_path = "search_gui_pyside.py"
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并替换处理折叠/展开的代码
    old_code = '''                # 修改：直接渲染当前结果，而不是重新筛选
                print("  直接渲染当前结果...")
                # 创建搜索结果的副本，以避免引用问题
                results_copy = self.search_results.copy()
                # 直接调用display_search_results_slot更新视图
                self.display_search_results_slot(results_copy)'''
    
    new_code = '''                # 修改：直接渲染当前结果，保持分页格式
                print("  直接渲染当前结果...")
                # 确保保持分页格式
                if hasattr(self, 'original_search_results') and self.original_search_results:
                    # 使用original_search_results重新构建带分页信息的结果
                    if isinstance(self.original_search_results, dict) and 'results' in self.original_search_results:
                        # 已经是字典格式，直接使用
                        results_with_pagination = self.original_search_results.copy()
                    elif isinstance(self.original_search_results, list):
                        # 是列表格式，需要转换为字典格式
                        results_with_pagination = {
                            'results': self.original_search_results.copy(),
                            'pagination': {
                                'current_page': getattr(self, 'current_page', 1),
                                'page_size': getattr(self, 'page_size', 50),
                                'total_count': len(self.original_search_results),
                                'total_pages': max(1, (len(self.original_search_results) + getattr(self, 'page_size', 50) - 1) // getattr(self, 'page_size', 50)),
                                'has_next': False,
                                'has_prev': False
                            }
                        }
                    else:
                        # 其他格式，使用当前搜索结果
                        results_with_pagination = {
                            'results': self.search_results.copy() if hasattr(self, 'search_results') else [],
                            'pagination': {
                                'current_page': 1,
                                'page_size': 50,
                                'total_count': len(self.search_results) if hasattr(self, 'search_results') else 0,
                                'total_pages': 1,
                                'has_next': False,
                                'has_prev': False
                            }
                        }
                else:
                    # 没有original_search_results，使用当前搜索结果
                    results_with_pagination = {
                        'results': self.search_results.copy() if hasattr(self, 'search_results') else [],
                        'pagination': {
                            'current_page': 1,
                            'page_size': 50,
                            'total_count': len(self.search_results) if hasattr(self, 'search_results') else 0,
                            'total_pages': 1,
                            'has_next': False,
                            'has_prev': False
                        }
                    }
                
                # 直接调用display_search_results_slot更新视图
                self.display_search_results_slot(results_with_pagination)'''
    
    # 替换代码
    if old_code in content:
        new_content = content.replace(old_code, new_code)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ 成功修复折叠/展开时页码消失的问题")
        print("📋 修复内容:")
        print("   - 在处理折叠/展开时保持分页格式")
        print("   - 确保传递带有pagination信息的字典对象")
        print("   - 兼容不同格式的搜索结果数据")
        return True
    else:
        print("❌ 未找到需要修复的代码段")
        print("💡 可能代码已经被修改或文件结构发生变化")
        return False

if __name__ == "__main__":
    print("🔧 开始修复折叠/展开时页码消失问题...")
    fix_pagination_toggle()
    print("🎯 修复完成！重新启动程序以查看效果。") 