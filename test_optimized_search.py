#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化搜索引擎性能测试脚本
测试不同查询的性能表现和缓存效果
"""

import sys
import time
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

import document_search

def test_search_performance():
    """测试搜索性能"""
    # 测试用例
    test_queries = [
        {"query": "十四五", "expected_results": "> 0", "complexity": "simple"},
        {"query": "计划", "expected_results": "> 100", "complexity": "simple"},
        {"query": "中国移动", "expected_results": "> 0", "complexity": "simple"},
        {"query": "*报告*", "expected_results": "> 0", "complexity": "medium"},
        {"query": "会议纪要", "expected_results": "> 0", "complexity": "medium"},
    ]
    
    # 索引路径
    index_dir = r"C:\软件\文智搜\suoyin"
    if not os.path.exists(index_dir):
        print(f"❌ 索引目录不存在: {index_dir}")
        return
    
    print("🚀 开始优化搜索引擎性能测试...")
    print("=" * 60)
    
    # 获取优化搜索引擎实例
    engine = document_search.get_optimized_search_engine()
    
    # 清理缓存以确保公平测试
    engine.clear_cache()
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        expected_complexity = test_case["expected_results"]
        
        print(f"\n🧪 测试 {i}: '{query}'")
        print("-" * 40)
        
        # 第一次搜索（无缓存）
        print("📊 第一次搜索（无缓存）:")
        start_time = time.time()
        
        try:
            results = document_search.optimized_search_sync(
                query, index_dir, 
                search_mode='phrase',
                search_scope='fulltext'
            )
            first_search_time = time.time() - start_time
            print(f"⏱️  耗时: {first_search_time:.2f} 秒")
            print(f"📄 结果数量: {len(results)}")
            
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            continue
        
        # 第二次搜索（测试缓存）
        print("\n💾 第二次搜索（测试缓存）:")
        start_time = time.time()
        
        try:
            cached_results = document_search.optimized_search_sync(
                query, index_dir,
                search_mode='phrase', 
                search_scope='fulltext'
            )
            second_search_time = time.time() - start_time
            print(f"⏱️  耗时: {second_search_time:.2f} 秒")
            print(f"📄 结果数量: {len(cached_results)}")
            
            # 计算性能提升
            if first_search_time > 0:
                improvement = ((first_search_time - second_search_time) / first_search_time) * 100
                print(f"🚀 缓存性能提升: {improvement:.1f}%")
                
        except Exception as e:
            print(f"❌ 缓存搜索失败: {e}")
    
    # 缓存统计
    print("\n" + "=" * 60)
    print("📈 缓存统计:")
    cache_stats = engine.get_cache_stats()
    print(f"📦 缓存条目总数: {cache_stats['total_entries']}")
    print(f"✅ 有效缓存条目: {cache_stats['valid_entries']}")
    print(f"🎯 缓存命中潜力: {cache_stats['cache_hit_potential']:.1%}")

def test_different_complexities():
    """测试不同复杂度查询的性能"""
    print("\n🔬 测试不同复杂度查询...")
    print("=" * 60)
    
    index_dir = r"C:\软件\文智搜\suoyin"
    engine = document_search.get_optimized_search_engine()
    
    # 不同复杂度的查询
    complexity_tests = [
        {
            "name": "简单查询",
            "query": "报告", 
            "params": {}
        },
        {
            "name": "中等复杂度查询",
            "query": "*计划*",
            "params": {"file_type_filter": ["docx", "xlsx"]}
        },
        {
            "name": "复杂查询",
            "query": "*会议*纪要*",
            "params": {
                "file_type_filter": ["docx", "pdf", "txt"],
                "min_size_kb": 10,
                "max_size_kb": 5000
            }
        }
    ]
    
    for test in complexity_tests:
        print(f"\n🧪 {test['name']}: '{test['query']}'")
        print("-" * 30)
        
        start_time = time.time()
        try:
            results = document_search.optimized_search_sync(
                test['query'], index_dir,
                search_mode='phrase',
                search_scope='fulltext',
                **test['params']
            )
            search_time = time.time() - start_time
            print(f"⏱️  耗时: {search_time:.2f} 秒")
            print(f"📄 结果数量: {len(results)}")
            
            # 性能评级
            if search_time < 0.5:
                rating = "🟢 优秀"
            elif search_time < 1.0:
                rating = "🟡 良好"
            elif search_time < 2.0:
                rating = "🟠 一般"
            else:
                rating = "🔴 需要优化"
                
            print(f"📊 性能评级: {rating}")
            
        except Exception as e:
            print(f"❌ 搜索失败: {e}")

def benchmark_vs_original():
    """基准测试：优化搜索 vs 原始搜索"""
    print("\n⚔️  基准测试：优化搜索 vs 原始搜索")
    print("=" * 60)
    
    index_dir = r"C:\软件\文智搜\suoyin"
    test_query = "十四五"
    
    # 原始搜索
    print("🐌 原始搜索:")
    start_time = time.time()
    try:
        original_results = document_search.search_index(
            test_query, index_dir,
            search_mode='phrase',
            search_scope='fulltext'
        )
        original_time = time.time() - start_time
        print(f"⏱️  耗时: {original_time:.2f} 秒")
        print(f"📄 结果数量: {len(original_results)}")
    except Exception as e:
        print(f"❌ 原始搜索失败: {e}")
        return
    
    # 优化搜索
    print("\n🚀 优化搜索:")
    start_time = time.time()
    try:
        optimized_results = document_search.optimized_search_sync(
            test_query, index_dir,
            search_mode='phrase',
            search_scope='fulltext'
        )
        optimized_time = time.time() - start_time
        print(f"⏱️  耗时: {optimized_time:.2f} 秒")
        print(f"📄 结果数量: {len(optimized_results)}")
        
        # 性能对比
        if original_time > 0:
            improvement = ((original_time - optimized_time) / original_time) * 100
            print(f"\n🏆 性能提升: {improvement:.1f}%")
            
            if improvement > 50:
                print("🎉 显著性能提升！")
            elif improvement > 20:
                print("✅ 性能有所改善")
            elif improvement > 0:
                print("🔧 轻微性能改善")
            else:
                print("⚠️  性能无明显改善")
                
    except Exception as e:
        print(f"❌ 优化搜索失败: {e}")

if __name__ == "__main__":
    print("🧪 文智搜优化搜索引擎性能测试")
    print("🎯 目标：验证搜索性能优化效果")
    print("📅 " + time.strftime("%Y-%m-%d %H:%M:%S"))
    
    try:
        # 运行所有测试
        test_search_performance()
        test_different_complexities()
        benchmark_vs_original()
        
        print("\n" + "=" * 60)
        print("✅ 性能测试完成！")
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc() 