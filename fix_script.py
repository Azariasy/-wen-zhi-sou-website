#!/usr/bin/env python
"""
重写search_gui_pyside.py文件中的问题方法
"""
import re
import os

def fix_file():
    # 打开文件
    with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 获取文件的行
    lines = content.split('\n')
    
    # 1. 修复 _setup_worker_thread 方法
    # 查找方法开始的位置
    worker_thread_start = -1
    worker_thread_end = -1
    
    for i, line in enumerate(lines):
        if "def _setup_worker_thread" in line:
            worker_thread_start = i
            # 找到方法结束的位置
            indent_level = len(line) - len(line.lstrip())
            for j in range(i + 1, len(lines)):
                # 检查是否遇到了同级或更高级的缩进（即方法结束）
                if lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) <= indent_level:
                    worker_thread_end = j - 1
                    break
            break
    
    # 如果找到了方法
    if worker_thread_start != -1 and worker_thread_end != -1:
        print(f"找到 _setup_worker_thread 方法: 行 {worker_thread_start+1} 到 {worker_thread_end+1}")
        
        # 替换为正确的方法实现
        correct_method = """    def _setup_worker_thread(self):
        \"\"\"创建并设置工作线程及其工作对象\"\"\"
        try:
            # 如果已存在线程，确保它被正确清理
            if hasattr(self, 'worker_thread') and self.worker_thread and self.worker_thread.isRunning():
                print("警告: 工作线程已存在，先清理...")
                self.worker_thread.quit()
                if not self.worker_thread.wait(3000):  # 等待最多3秒
                    print("警告: 线程未能在3秒内退出，将强制终止")
                    self.worker_thread.terminate()
                    self.worker_thread.wait(1000)
                
                if hasattr(self, 'worker') and self.worker:
                    self.worker.deleteLater()
                
                self.worker_thread.deleteLater()
            
            # 创建新的线程和工作对象
            self.worker_thread = QThread()
            self.worker = Worker()
            self.worker.moveToThread(self.worker_thread)
            
            # 连接工作线程信号到主线程槽函数
            self.worker.statusChanged.connect(self.update_status_label_slot)
            self.worker.progressUpdated.connect(self.update_progress_bar_slot)
            self.worker.resultsReady.connect(self._handle_new_search_results_slot)
            self.worker.indexingComplete.connect(self.indexing_finished_slot)
            self.worker.errorOccurred.connect(self.handle_error_slot)
            
            # 连接主线程信号到工作线程槽函数
            self.startIndexingSignal.connect(self.worker.run_indexing)
            self.startSearchSignal.connect(self.worker.run_search)
            
            # 连接线程完成信号
            self.worker_thread.finished.connect(self.thread_finished_slot)
            
            # 启动线程
            self.worker_thread.start()
            print("工作线程已成功创建并启动")
        except Exception as e:
            print(f"创建工作线程时发生错误: {str(e)}")
            # 确保清理任何可能部分创建的资源
            if hasattr(self, 'worker') and self.worker:
                self.worker.deleteLater()
                self.worker = None
            
            if hasattr(self, 'worker_thread') and self.worker_thread:
                self.worker_thread.quit()
                self.worker_thread.wait(1000)
                self.worker_thread.deleteLater()
                self.worker_thread = None
            
            # 显示错误消息
            QMessageBox.critical(self, "错误", f"创建工作线程时发生错误: {str(e)}")"""
        
        # 用正确的方法替换原始方法
        lines[worker_thread_start:worker_thread_end+1] = correct_method.split('\n')
    
    # 2. 修复 closeEvent 方法中的缩进问题
    for i, line in enumerate(lines):
        if "self.settings.setValue(\"skippedFilesDialog/geometry\"" in line:
            # 修复缩进
            lines[i] = "            self.settings.setValue(\"skippedFilesDialog/geometry\", self.saveGeometry())"
            print(f"修复 closeEvent 方法在行 {i+1}")
    
    # 3. 找到apply_theme方法并完全重写以修复try-except结构问题
    apply_theme_start = -1
    apply_theme_end = -1
    
    for i, line in enumerate(lines):
        if "def apply_theme" in line:
            apply_theme_start = i
            # 找到方法结束的位置
            indent_level = len(line) - len(line.lstrip())
            for j in range(i + 1, len(lines)):
                # 检查是否遇到了同级或更高级的缩进（即方法结束）
                if lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) <= indent_level:
                    apply_theme_end = j - 1
                    break
            if apply_theme_end == -1:  # 如果没有找到结束位置，可能是文件的最后一个方法
                apply_theme_end = len(lines) - 1
            break
    
    if apply_theme_start != -1 and apply_theme_end != -1:
        print(f"找到 apply_theme 方法: 行 {apply_theme_start+1} 到 {apply_theme_end+1}")
        
        # 替换为正确的方法实现 - 注意解决引号转义问题
        correct_apply_theme = '''    def apply_theme(self, theme_name):
        """应用程序主题设置"""
        app = QApplication.instance()
        
        if theme_name == "浅色":
            # 使用light/default系统样式
            app.setStyleSheet("")  # 清除任何可能应用的样式表
            print("Applied light theme (system default)")
            
        elif theme_name == "深色":
            # 尝试使用QDarkStyle
            try:
                import qdarkstyle
                app.setStyleSheet(qdarkstyle.load_stylesheet())
                print("Applied dark theme using QDarkStyle")
            except ImportError:
                print("QDarkStyle not found, falling back to system stylesheet")
                app.setStyleSheet("")
        
        elif theme_name == "现代蓝":
            # 使用现代蓝色主题
            try:
                # 加载蓝色样式表
                style_path = os.path.join(os.path.dirname(__file__), "blue_style.qss")
                if os.path.exists(style_path):
                    with open(style_path, "r", encoding="utf-8") as f:
                        stylesheet = f.read()
                    app.setStyleSheet(stylesheet)
                    print("Applied modern blue theme.")
                else:
                    print(f"Blue style file not found: {style_path}")
                    # 回退到系统默认
                    app.setStyleSheet("")
            except Exception as e:
                print(f"Error applying modern blue style: {e}. Falling back to system default.")
                app.setStyleSheet("")
                
        elif theme_name == "现代绿":
            # 使用现代绿色主题
            try:
                # 加载绿色样式表
                style_path = os.path.join(os.path.dirname(__file__), "green_style.qss")
                if os.path.exists(style_path):
                    with open(style_path, "r", encoding="utf-8") as f:
                        stylesheet = f.read()
                    app.setStyleSheet(stylesheet)
                    print("Applied modern green theme.")
                else:
                    print(f"Green style file not found: {style_path}")
                    # 回退到现代蓝
                    self._apply_fallback_blue_theme()
            except Exception as e:
                print(f"Error applying modern green style: {e}. Falling back to modern blue theme.")
                self._apply_fallback_blue_theme()
                
        elif theme_name == "现代紫":
            # 使用现代紫色主题
            try:
                # 加载紫色样式表
                style_path = os.path.join(os.path.dirname(__file__), "purple_style.qss")
                if os.path.exists(style_path):
                    with open(style_path, "r", encoding="utf-8") as f:
                        stylesheet = f.read()
                    app.setStyleSheet(stylesheet)
                    print("Applied modern purple theme.")
                else:
                    print(f"Purple style file not found: {style_path}")
                    # 回退到现代蓝
                    self._apply_fallback_blue_theme()
            except Exception as e:
                print(f"Error applying modern purple style: {e}. Falling back to modern blue theme.")
                self._apply_fallback_blue_theme()
        else:
            # 对于任何未知主题或系统默认，使用现代蓝
            self._apply_fallback_blue_theme()'''
        
        # 用正确的方法替换原始方法
        lines[apply_theme_start:apply_theme_end+1] = correct_apply_theme.split('\n')
    
    # 将修复后的内容写回文件
    with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("文件修复完成！")

if __name__ == "__main__":
    fix_file() 