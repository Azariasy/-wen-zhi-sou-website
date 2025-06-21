#!/usr/bin/env python3
"""
快速文件名搜索模块

专门用于快速搜索文件名，不涉及文件内容搜索
设计原则：
1. 只搜索文件名，不搜索文件内容
2. 直接遍历文件系统，不依赖索引
3. 极速响应，毫秒级搜索
4. 简单直接，避免复杂逻辑
"""

import os
import time
import fnmatch
from pathlib import Path
from typing import List, Dict, Optional
from PySide6.QtCore import QThread, Signal, QObject


class QuickFilenameSearcher(QObject):
    """快速文件名搜索器"""
    
    # 信号定义
    search_completed = Signal(list)  # 搜索完成信号
    search_progress = Signal(str)    # 搜索进度信号
    
    def __init__(self, source_directories: List[str] = None, license_manager=None):
        super().__init__()
        self.source_directories = source_directories or []
        self.license_manager = license_manager
        
        # 根据许可证设置支持的文件扩展名
        if self.license_manager:
            self.supported_extensions = self._get_allowed_extensions()
        else:
            # 默认支持所有类型（向后兼容）
            self.supported_extensions = {
                '.txt', '.md', '.doc', '.docx', '.pdf', '.xls', '.xlsx', 
                '.ppt', '.pptx', '.rtf', '.html', '.htm', '.xml', '.json',
                '.py', '.js', '.css', '.java', '.cpp', '.c', '.h'
            }
        
    def set_source_directories(self, directories: List[str]):
        """设置搜索目录"""
        self.source_directories = directories
    
    def _get_allowed_extensions(self):
        """根据许可证获取允许的文件扩展名"""
        # 基础版支持的文件类型
        allowed = {'.docx', '.xlsx', '.htm', '.html', '.pptx', '.rtf', '.txt'}
        
        if self.license_manager:
            from license_manager import Features
            # 检查专业版功能
            if self.license_manager.is_feature_available(Features.PDF_SUPPORT):
                allowed.add('.pdf')
            if self.license_manager.is_feature_available(Features.MARKDOWN_SUPPORT):
                allowed.add('.md')
            if self.license_manager.is_feature_available(Features.EMAIL_SUPPORT):
                allowed.update({'.eml', '.msg'})
            if self.license_manager.is_feature_available(Features.MULTIMEDIA_SUPPORT):
                allowed.update({'.mp3', '.mp4', '.avi', '.wmv', '.mov', '.jpg', '.jpeg', '.png', '.gif', '.bmp'})
        
        print(f"📋 快捷搜索允许的文件类型: {sorted(allowed)}")
        return allowed
        
    def search_filenames(self, query: str, max_results: int = 100) -> List[Dict]:
        """
        快速搜索文件名
        
        Args:
            query: 搜索查询词
            max_results: 最大结果数
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        if not query or not query.strip():
            return []
        
        # 检查源目录是否为空 - 与主窗口逻辑保持一致
        if not self.source_directories:
            print("⚠️ 快捷搜索：源目录为空，返回空结果")
            return []
            
        query = query.strip().lower()
        results = []
        total_found = 0  # 实际找到的总数量
        start_time = time.time()
        
        print(f"🚀 快速文件名搜索开始：'{query}'")
        
        try:
            for directory in self.source_directories:
                if not os.path.exists(directory):
                    continue
                    
                self.search_progress.emit(f"搜索目录: {os.path.basename(directory)}")
                
                # 递归搜索文件
                for root, dirs, files in os.walk(directory):
                    # 跳过隐藏目录
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    
                    for file in files:
                        # 检查文件扩展名
                        file_ext = Path(file).suffix.lower()
                        if file_ext not in self.supported_extensions:
                            continue
                            
                        # 检查文件名是否匹配查询词
                        if self._matches_query(file.lower(), query):
                            total_found += 1  # 增加总数量计数
                            
                            # 只有在未达到限制时才添加到结果中
                            if len(results) < max_results:
                                file_path = os.path.join(root, file)
                                
                                # 获取文件信息
                                try:
                                    stat_info = os.stat(file_path)
                                    file_size = stat_info.st_size
                                    modified_time = stat_info.st_mtime
                                    
                                    result = {
                                        'file_path': file_path,
                                        'filename': file,
                                        'directory': root,
                                        'file_size': file_size,
                                        'modified_time': modified_time,
                                        'file_type': file_ext,
                                        'match_score': self._calculate_match_score(file.lower(), query)
                                    }
                                    
                                    results.append(result)
                                        
                                except (OSError, IOError) as e:
                                    # 跳过无法访问的文件
                                    continue
            
            # 按修改时间和匹配分数的加权排序（时间权重更高）
            # 使用时间戳差值来计算时间权重，越新的文件权重越高
            current_time = time.time()
            
            def calculate_sort_key(result):
                modified_time = result['modified_time']
                match_score = result['match_score']
                
                # 计算时间权重：距离当前时间越近，权重越高
                # 1天 = 86400秒，用于标准化时间差
                time_diff_days = (current_time - modified_time) / 86400
                
                # 时间权重：最近1天=100分，之后每天递减1分，最低10分
                time_weight = max(10, 100 - time_diff_days)
                
                # 综合分数：时间权重70%，匹配分数30%
                combined_score = (time_weight * 0.7) + (match_score * 0.3)
                
                return combined_score
            
            results.sort(key=calculate_sort_key, reverse=True)
            
            elapsed_time = time.time() - start_time
            print(f"✅ 快速文件名搜索完成：找到 {total_found} 个结果，显示前 {len(results)} 个，耗时 {elapsed_time*1000:.1f}ms")
            
            # 如果找到的总数量大于返回的结果数量，在第一个结果前插入总数量信息
            if total_found > len(results):
                # 创建一个特殊的元数据项，包含总数量信息
                metadata = {
                    'is_metadata': True,
                    'total_found': total_found,
                    'displayed_count': len(results),
                    'max_results': max_results
                }
                return [metadata] + results
            
            return results
            
        except Exception as e:
            print(f"❌ 快速文件名搜索出错：{str(e)}")
            return []
    
    def _matches_query(self, filename: str, query: str) -> bool:
        """
        检查文件名是否匹配查询词
        
        Args:
            filename: 文件名（小写）
            query: 查询词（小写）
            
        Returns:
            bool: 是否匹配
        """
        # 1. 完全匹配（不含扩展名）
        name_without_ext = Path(filename).stem.lower()
        if query in name_without_ext:
            return True
            
        # 2. 模糊匹配（支持通配符）
        try:
            if fnmatch.fnmatch(name_without_ext, f"*{query}*"):
                return True
        except:
            pass
            
        # 3. 分词匹配（中文支持）
        query_chars = list(query)
        if all(char in name_without_ext for char in query_chars):
            return True
            
        return False
    
    def _calculate_match_score(self, filename: str, query: str) -> float:
        """
        计算匹配分数
        
        Args:
            filename: 文件名（小写）
            query: 查询词（小写）
            
        Returns:
            float: 匹配分数（0-100）
        """
        name_without_ext = Path(filename).stem.lower()
        
        # 基础分数
        score = 0.0
        
        # 1. 完全匹配加分
        if query == name_without_ext:
            score += 100
        elif query in name_without_ext:
            # 包含匹配，根据位置和长度加分
            index = name_without_ext.find(query)
            if index == 0:  # 开头匹配
                score += 80
            else:  # 中间匹配
                score += 60
            
            # 长度匹配度
            length_ratio = len(query) / len(name_without_ext)
            score += length_ratio * 20
        
        # 2. 字符匹配度
        query_chars = set(query)
        name_chars = set(name_without_ext)
        char_match_ratio = len(query_chars & name_chars) / len(query_chars) if query_chars else 0
        score += char_match_ratio * 10
        
        # 3. 文件类型加分（常用文档类型）
        common_types = {'.txt', '.md', '.doc', '.docx', '.pdf'}
        file_ext = Path(filename).suffix.lower()
        if file_ext in common_types:
            score += 5
            
        return min(score, 100.0)


class QuickFilenameSearchThread(QThread):
    """快速文件名搜索线程"""
    
    # 信号定义
    search_completed = Signal(list)
    search_progress = Signal(str)
    search_error = Signal(str)
    
    def __init__(self, source_directories: List[str] = None):
        super().__init__()
        self.searcher = QuickFilenameSearcher(source_directories)
        self.query = ""
        self.max_results = 100
        
        # 连接信号
        self.searcher.search_completed.connect(self.search_completed)
        self.searcher.search_progress.connect(self.search_progress)
    
    def search(self, query: str, max_results: int = 100):
        """启动搜索"""
        self.query = query
        self.max_results = max_results
        self.start()
    
    def run(self):
        """线程运行方法"""
        try:
            results = self.searcher.search_filenames(self.query, self.max_results)
            self.search_completed.emit(results)
        except Exception as e:
            self.search_error.emit(str(e))


# 使用示例
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication
    
    app = QApplication(sys.argv)
    
    # 测试快速文件名搜索
    test_directories = [
        "D:/OneDrive/person/文件搜索工具/测试文件夹",
        "D:/OneDrive/person/文件搜索工具/新建文件夹"
    ]
    
    searcher = QuickFilenameSearcher(test_directories)
    
    # 测试搜索
    test_queries = ["计划", "手册", "制度", "项目"]
    
    for query in test_queries:
        print(f"\n🔍 测试搜索：'{query}'")
        results = searcher.search_filenames(query, max_results=10)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['filename']} (分数: {result['match_score']:.1f})")
                print(f"     路径: {result['file_path']}")
        else:
            print("  未找到结果")
    
    print("\n✅ 快速文件名搜索测试完成") 