#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一路径处理工具模块

这个模块提供了项目中所有路径处理的统一接口，
解决了原本分散在多个文件中的路径标准化函数重复问题。

更新历史：
- 2024-XX-XX: 创建统一路径处理模块
"""

import os
import sys
from pathlib import Path
from typing import Union, Tuple


class PathStandardizer:
    """路径标准化处理类
    
    提供统一的路径标准化接口，支持不同用途的路径格式转换
    """
    
    @staticmethod
    def normalize_for_index(path_str: Union[str, Path]) -> str:
        """
        标准化路径用于索引存储
        
        这个函数用于后端索引系统，确保路径在不同操作系统下的一致性
        
        Args:
            path_str: 要标准化的路径字符串或Path对象
            
        Returns:
            str: 标准化后的路径字符串（用于索引）
        """
        if not path_str:
            return ""
            
        try:
            # 转换为字符串
            path_str = str(path_str)
            
            # 处理压缩包内文件的特殊情况
            if "::" in path_str:
                archive_path, internal_path = path_str.split("::", 1)
                # 分别标准化压缩包路径和内部路径
                norm_archive = PathStandardizer.normalize_for_index(archive_path)
                # 内部路径统一使用正斜杠
                norm_internal = internal_path.replace('\\', '/')
                return f"{norm_archive}::{norm_internal}"
                
            # 普通文件路径处理
            try:
                # 尝试使用Path对象处理
                path_obj = Path(path_str)
                if path_obj.exists():
                    # 如果路径存在，使用resolve()获取绝对路径
                    norm_path = str(path_obj.resolve()).replace('\\', '/')
                else:
                    # 如果路径不存在，则只进行基本的分隔符转换
                    norm_path = str(path_obj).replace('\\', '/')
            except Exception:
                # 路径无法通过Path对象处理，直接进行字符串处理
                norm_path = path_str.replace('\\', '/')
            
            # 统一驱动器字母为小写（用于索引一致性）
            if ':/' in norm_path:
                drive, rest = norm_path.split(':', 1)
                norm_path = drive.lower() + ':' + rest
                
            # 移除可能的尾部斜杠，确保一致性
            if norm_path.endswith('/') and len(norm_path) > 1:
                norm_path = norm_path.rstrip('/')
                
            return norm_path
        except Exception as e:
            print(f"路径索引标准化错误 ({path_str}): {e}")
            # 失败时返回原始路径，但尝试进行最基本的分隔符转换
            try:
                return str(path_str).replace('\\', '/')
            except Exception:
                return str(path_str)
    
    @staticmethod
    def normalize_for_display(path_str: Union[str, Path]) -> str:
        """
        标准化路径用于前端显示
        
        这个函数用于GUI界面显示，遵循操作系统的路径显示习惯
        
        Args:
            path_str: 要标准化的路径字符串或Path对象
            
        Returns:
            str: 标准化后的路径字符串（用于显示）
        """
        if not path_str:
            return ""
            
        try:
            # 转换为字符串
            path_str = str(path_str)
            
            # 处理压缩包内文件的特殊情况
            if "::" in path_str:
                archive_path, internal_path = path_str.split("::", 1)
                # 分别标准化压缩包路径和内部路径
                norm_archive = PathStandardizer.normalize_for_display(archive_path)
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
            except Exception:
                # 路径无法通过Path对象处理，直接进行字符串处理
                norm_path = path_str
            
            # 根据操作系统进行路径标准化
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
            print(f"路径显示标准化错误 ({path_str}): {e}")
            return str(path_str)
    
    @staticmethod
    def split_archive_path(path_str: str) -> Tuple[str, str]:
        """
        分离压缩包路径和内部文件路径
        
        Args:
            path_str: 可能包含压缩包内部路径的字符串
            
        Returns:
            tuple: (压缩包路径, 内部文件路径)，如果不是压缩包则内部路径为空
        """
        if "::" in path_str:
            return path_str.split("::", 1)
        else:
            return path_str, ""
    
    @staticmethod
    def get_folder_path(file_path: Union[str, Path]) -> str:
        """
        获取文件的文件夹路径（用于显示）
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件夹路径
        """
        if not file_path:
            return '未知路径'
        
        file_path_str = str(file_path)
        
        # 处理压缩包内的文件
        if '::' in file_path_str:
            archive_path, _ = PathStandardizer.split_archive_path(file_path_str)
            folder_path = str(Path(archive_path).parent)
        else:
            folder_path = str(Path(file_path_str).parent)
        
        # 标准化路径显示
        normalized_path = PathStandardizer.normalize_for_display(folder_path)
        
        # 如果路径太长，进行缩短
        if len(normalized_path) > 60:
            # 保留开头和结尾，中间用...代替
            parts = normalized_path.split(os.sep)
            if len(parts) > 3:
                return os.sep.join([parts[0], '...', parts[-2], parts[-1]])
        
        return normalized_path if normalized_path else '根目录'


# 为了向后兼容，提供全局函数接口
def normalize_path_for_index(path_str: Union[str, Path]) -> str:
    """向后兼容的索引路径标准化函数"""
    return PathStandardizer.normalize_for_index(path_str)


def normalize_path_for_display(path_str: Union[str, Path]) -> str:
    """向后兼容的显示路径标准化函数"""
    return PathStandardizer.normalize_for_display(path_str)


# 测试函数
def test_path_standardizer():
    """测试路径标准化功能"""
    test_cases = [
        "D:\\OneDrive\\test\\file.pdf",
        "d:/onedrive/test/file.pdf",
        "test.zip::internal/file.txt",
        "D:\\OneDrive\\  工作\\中移（成都）信息通信科技有限公司\\工程资产\\file.pdf",
        "",
        None
    ]
    
    print("=== 路径标准化测试 ===")
    for test_path in test_cases:
        if test_path is not None:
            index_result = PathStandardizer.normalize_for_index(test_path)
            display_result = PathStandardizer.normalize_for_display(test_path)
            print(f"原始路径: {test_path}")
            print(f"索引格式: {index_result}")
            print(f"显示格式: {display_result}")
            print("-" * 50)


if __name__ == "__main__":
    test_path_standardizer() 