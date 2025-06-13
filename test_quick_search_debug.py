#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快捷搜索调试测试程序
用于分析快捷搜索结果数量不匹配的问题
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_window_tray import TrayMainWindow
from quick_search_controller import QuickSearchController

def test_search_comparison():
    """测试快捷搜索和主窗口搜索的结果对比"""
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = TrayMainWindow()
    
    # 创建快捷搜索控制器
    controller = QuickSearchController(main_window)
    
    # 测试查询
    test_query = "手册"
    
    print(f"=== 开始测试搜索对比 ===")
    print(f"测试查询: '{test_query}'")
    print()
    
    # 1. 测试主窗口搜索
    print("1. 主窗口搜索测试:")
    try:
        # 全文搜索
        fulltext_results = main_window._perform_search(
            query=test_query,
            max_results=100,
            quick_search=False,
            search_scope="fulltext"
        )
        print(f"   全文搜索结果: {len(fulltext_results)} 个")
        
        # 文件名搜索
        filename_results = main_window._perform_search(
            query=test_query,
            max_results=100,
            quick_search=False,
            search_scope="filename"
        )
        print(f"   文件名搜索结果: {len(filename_results)} 个")
        
    except Exception as e:
        print(f"   主窗口搜索失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 2. 测试快捷搜索
    print("2. 快捷搜索测试:")
    try:
        # 快捷搜索（使用文件名搜索）
        quick_results = main_window._perform_search(
            query=test_query,
            max_results=8,
            quick_search=True,
            search_scope="filename"
        )
        print(f"   快捷搜索结果: {len(quick_results)} 个")
        
        # 打印前几个结果
        if quick_results:
            print("   前几个结果:")
            for i, result in enumerate(quick_results[:5]):
                file_path = result.get('file_path', '未知')
                file_name = os.path.basename(file_path) if file_path else '未知文件'
                print(f"     {i+1}. {file_name}")
        
    except Exception as e:
        print(f"   快捷搜索失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 3. 分析差异
    print("3. 差异分析:")
    if 'fulltext_results' in locals() and 'filename_results' in locals() and 'quick_results' in locals():
        print(f"   全文搜索: {len(fulltext_results)} 个结果")
        print(f"   文件名搜索: {len(filename_results)} 个结果")
        print(f"   快捷搜索: {len(quick_results)} 个结果")
        print(f"   快捷搜索限制: 8 个结果")
        
        if len(filename_results) != len(quick_results):
            print(f"   ⚠️ 文件名搜索和快捷搜索结果数量不一致!")
            print(f"   可能原因:")
            print(f"     - 快捷搜索有结果数量限制 (max_results=8)")
            print(f"     - 搜索参数或逻辑不同")
            print(f"     - 缓存或状态问题")
    
    print()
    print("=== 测试完成 ===")
    
    # 退出应用
    QTimer.singleShot(1000, app.quit)
    return app.exec()

def test_controller_search():
    """测试控制器的搜索逻辑"""
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = TrayMainWindow()
    
    # 创建快捷搜索控制器
    controller = QuickSearchController(main_window)
    
    test_query = "手册"
    
    print(f"=== 测试控制器搜索逻辑 ===")
    print(f"测试查询: '{test_query}'")
    print()
    
    # 1. 检查控制器设置
    print("1. 控制器设置:")
    print(f"   max_results: {controller.max_results}")
    print(f"   preview_length: {controller.preview_length}")
    print()
    
    # 2. 测试原始搜索
    print("2. 原始搜索测试:")
    try:
        raw_results = controller._execute_search_via_main_window(test_query)
        print(f"   原始搜索结果: {len(raw_results)} 个")
        
        if raw_results:
            print("   原始结果结构:")
            first_result = raw_results[0]
            print(f"     类型: {type(first_result)}")
            if hasattr(first_result, 'keys'):
                print(f"     键: {list(first_result.keys())}")
            elif hasattr(first_result, '__len__') and len(first_result) > 0:
                print(f"     长度: {len(first_result)}")
                print(f"     第一个元素: {first_result[0] if len(first_result) > 0 else 'None'}")
        
    except Exception as e:
        print(f"   原始搜索失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 3. 测试格式化
    print("3. 格式化测试:")
    try:
        if 'raw_results' in locals() and raw_results:
            formatted_results = controller._format_search_results(raw_results)
            print(f"   格式化结果: {len(formatted_results)} 个")
            
            if formatted_results:
                print("   格式化结果示例:")
                for i, result in enumerate(formatted_results[:3]):
                    file_path = result.get('file_path', '未知')
                    file_name = os.path.basename(file_path) if file_path else '未知文件'
                    preview = result.get('content_preview', '无预览')[:50]
                    print(f"     {i+1}. {file_name} - {preview}...")
        else:
            print("   没有原始结果可以格式化")
    
    except Exception as e:
        print(f"   格式化失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=== 控制器测试完成 ===")
    
    # 退出应用
    QTimer.singleShot(1000, app.quit)
    return app.exec()

if __name__ == "__main__":
    print("选择测试模式:")
    print("1. 搜索结果对比测试")
    print("2. 控制器搜索逻辑测试")
    
    choice = input("请输入选择 (1 或 2): ").strip()
    
    if choice == "1":
        test_search_comparison()
    elif choice == "2":
        test_controller_search()
    else:
        print("无效选择，运行默认测试")
        test_search_comparison() 