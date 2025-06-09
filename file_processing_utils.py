#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理工具模块

提供统一的文件处理工具，包括取消检查装饰器、错误处理等
"""

import functools
from typing import Callable, Any, Optional


class FileProcessingError(Exception):
    """文件处理异常基类"""
    pass


class FileProcessingCancelledException(FileProcessingError):
    """文件处理被取消异常"""
    pass


def check_cancellation(cancel_callback: Optional[Callable] = None, operation_context: str = "操作"):
    """
    统一的取消检查函数
    
    Args:
        cancel_callback: 取消回调函数，如果返回True表示需要取消
        operation_context: 操作上下文信息，用于异常消息
        
    Raises:
        FileProcessingCancelledException: 当检测到取消请求时
    """
    if cancel_callback and cancel_callback():
        raise FileProcessingCancelledException(f"{operation_context}被用户取消")


def cancellable_operation(func: Callable) -> Callable:
    """
    可取消操作装饰器
    
    为文件处理函数添加统一的取消检查逻辑
    自动在函数开始和结束时检查取消状态
    
    Args:
        func: 要装饰的函数，必须接受cancel_callback参数
        
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 获取cancel_callback参数
        cancel_callback = kwargs.get('cancel_callback', None)
        
        # 在函数开始时检查取消状态
        try:
            check_cancellation(cancel_callback, f"函数 {func.__name__}")
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 在函数结束时再次检查取消状态
            check_cancellation(cancel_callback, f"函数 {func.__name__}")
            
            return result
            
        except FileProcessingCancelledException:
            # 保持原有的异常类型，确保向后兼容
            raise InterruptedError(f"{func.__name__}操作被用户取消")
            
        except Exception as e:
            # 在发生其他异常时也检查是否被取消
            if cancel_callback and cancel_callback():
                raise InterruptedError(f"{func.__name__}操作被用户取消")
            raise e
            
    return wrapper


def periodic_cancellation_check(cancel_callback: Optional[Callable], 
                               interval: int, 
                               current_count: int, 
                               operation_context: str = "批处理操作"):
    """
    周期性取消检查函数
    
    在循环处理中使用，每隔指定间隔检查一次取消状态
    
    Args:
        cancel_callback: 取消回调函数
        interval: 检查间隔
        current_count: 当前计数
        operation_context: 操作上下文信息
        
    Raises:
        InterruptedError: 当检测到取消请求时
    """
    if current_count % interval == 0 and cancel_callback and cancel_callback():
        raise InterruptedError(f"{operation_context}被用户取消")


# 向后兼容性：确保正确的异常继承关系
class InterruptedError(FileProcessingCancelledException):
    """操作被中断异常 - 保持向后兼容"""
    pass


def test_cancellation_utils():
    """测试取消检查工具函数"""
    print("=== 测试取消检查工具函数 ===")
    
    # 测试1: 正常操作（无取消）
    def no_cancel():
        return False
    
    try:
        check_cancellation(no_cancel, "测试操作1")
        print("✅ 测试1通过: 无取消检查正常")
    except Exception as e:
        print(f"❌ 测试1失败: {e}")
    
    # 测试2: 取消操作
    def should_cancel():
        return True
    
    try:
        check_cancellation(should_cancel, "测试操作2")
        print("❌ 测试2失败: 应该检测到取消")
    except (FileProcessingCancelledException, InterruptedError):
        print("✅ 测试2通过: 正确检测到取消")
    except Exception as e:
        print(f"❌ 测试2失败: 异常类型错误 {e}")
    
    # 测试3: 装饰器测试
    @cancellable_operation
    def test_function(data, cancel_callback=None):
        return f"处理数据: {data}"
    
    try:
        result = test_function("test_data", cancel_callback=no_cancel)
        print(f"✅ 测试3通过: 装饰器正常工作 - {result}")
    except Exception as e:
        print(f"❌ 测试3失败: {e}")
    
    # 测试4: 装饰器取消测试
    try:
        result = test_function("test_data", cancel_callback=should_cancel)
        print("❌ 测试4失败: 装饰器应该检测到取消")
    except InterruptedError:
        print("✅ 测试4通过: 装饰器正确检测到取消")
    except Exception as e:
        print(f"❌ 测试4失败: 异常类型错误 {e}")
    
    # 测试5: 周期性检查测试
    try:
        for i in range(25):
            periodic_cancellation_check(no_cancel, 10, i, "循环测试")
        print("✅ 测试5通过: 周期性检查正常")
    except Exception as e:
        print(f"❌ 测试5失败: {e}")
    
    # 测试6: 周期性检查取消测试
    try:
        for i in range(25):
            periodic_cancellation_check(should_cancel, 10, i, "循环测试")
        print("❌ 测试6失败: 周期性检查应该检测到取消")
    except InterruptedError:
        print("✅ 测试6通过: 周期性检查正确检测到取消")
    except Exception as e:
        print(f"❌ 测试6失败: 异常类型错误 {e}")
    
    print("=== 取消检查工具函数测试完成 ===")


if __name__ == "__main__":
    test_cancellation_utils() 