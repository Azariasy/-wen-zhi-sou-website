"""
单实例管理器 - 防止程序重复启动

使用文件锁机制确保同一时间只能运行一个程序实例
"""

import os
import sys
import time
import tempfile
import atexit
try:
    if sys.platform != "win32":
        import fcntl
    else:
        fcntl = None
except ImportError:
    fcntl = None
from pathlib import Path

class SingleInstance:
    """单实例管理器"""
    
    def __init__(self, app_name="文智搜"):
        """初始化单实例管理器
        
        Args:
            app_name: 应用程序名称，用于生成唯一的锁文件名
        """
        self.app_name = app_name
        self.lock_file = None
        self.lock_file_path = None
        self._setup_lock_file()
        
    def _setup_lock_file(self):
        """设置锁文件路径"""
        # 使用临时目录创建锁文件
        temp_dir = tempfile.gettempdir()
        # 创建唯一的锁文件名
        lock_filename = f"{self.app_name}_single_instance.lock"
        self.lock_file_path = os.path.join(temp_dir, lock_filename)
        
    def is_already_running(self):
        """检查程序是否已在运行
        
        Returns:
            bool: True表示已有实例在运行，False表示没有
        """
        try:
            # 如果锁文件存在，检查是否仍然有效
            if os.path.exists(self.lock_file_path):
                if self._is_lock_file_valid():
                    print(f"检测到有效的锁文件: {self.lock_file_path}")
                    return True
                else:
                    # 锁文件无效，删除它
                    print(f"删除无效的锁文件: {self.lock_file_path}")
                    try:
                        os.remove(self.lock_file_path)
                    except OSError:
                        pass
            
            # 尝试创建新的锁文件
            try:
                # 使用独占模式创建文件
                if sys.platform == "win32":
                    # Windows: 使用独占模式
                    self.lock_file = open(self.lock_file_path, 'x')
                else:
                    # Unix: 使用文件锁
                    self.lock_file = open(self.lock_file_path, 'w')
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                # 写入当前进程ID
                self.lock_file.write(str(os.getpid()))
                self.lock_file.flush()
                
                print(f"成功创建锁文件: {self.lock_file_path} (PID: {os.getpid()})")
                
                # 注册退出时清理函数
                atexit.register(self.cleanup)
                
                return False
                
            except (FileExistsError, IOError, OSError) as e:
                print(f"无法创建锁文件，可能已有实例在运行: {e}")
                return True
            
        except Exception as e:
            print(f"单实例检查时发生错误: {e}")
            # 出错时假设没有其他实例在运行
            return False
    
    def _is_lock_file_valid(self):
        """检查锁文件是否仍然有效
        
        Returns:
            bool: True表示锁文件有效，False表示无效
        """
        try:
            with open(self.lock_file_path, 'r') as f:
                pid_str = f.read().strip()
                if not pid_str:
                    print("锁文件为空")
                    return False
                
                try:
                    pid = int(pid_str)
                except ValueError:
                    print(f"锁文件包含无效的PID: {pid_str}")
                    return False
                
                print(f"检查锁文件中的PID: {pid}")
                
                # 在Windows上检查进程是否存在
                if sys.platform == "win32":
                    import subprocess
                    try:
                        # 使用tasklist命令检查进程是否存在
                        result = subprocess.run(
                            ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        # 检查输出中是否包含该PID
                        lines = result.stdout.strip().split('\n')
                        if len(lines) > 1:  # 第一行是标题
                            print(f"进程 {pid} 仍在运行")
                            return True
                        else:
                            print(f"进程 {pid} 不存在")
                            return False
                    except Exception as e:
                        print(f"检查进程时出错: {e}")
                        return False
                else:
                    # 在Unix系统上使用kill信号检查
                    try:
                        os.kill(pid, 0)
                        print(f"进程 {pid} 仍在运行")
                        return True
                    except OSError:
                        print(f"进程 {pid} 不存在")
                        return False
                        
        except (IOError, OSError) as e:
            print(f"读取锁文件时出错: {e}")
            return False
    
    def cleanup(self):
        """清理锁文件"""
        try:
            if self.lock_file:
                self.lock_file.close()
                self.lock_file = None
                print("锁文件已关闭")
            
            if self.lock_file_path and os.path.exists(self.lock_file_path):
                os.remove(self.lock_file_path)
                print(f"锁文件已删除: {self.lock_file_path}")
                
        except (IOError, OSError) as e:
            print(f"清理锁文件时出错: {e}")
    
    def show_already_running_message(self):
        """显示程序已在运行的消息"""
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            from PySide6.QtCore import Qt
            
            # 创建临时应用程序实例来显示消息框
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
                app_created = True
            else:
                app_created = False
            
            # 创建消息框
            msg_box = QMessageBox()
            msg_box.setWindowTitle("文智搜")
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setText("文智搜已在运行中")
            msg_box.setInformativeText("程序已在系统托盘中运行。\n请检查系统托盘区域或使用热键调出程序。")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.setDefaultButton(QMessageBox.Ok)
            
            # 设置窗口属性
            msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint)
            
            # 显示消息框
            msg_box.exec()
            
            # 如果我们创建了应用程序实例，需要清理
            if app_created:
                app.quit()
                
        except ImportError:
            # 如果PySide6不可用，使用控制台输出
            print("文智搜已在运行中，请检查系统托盘。")
        except Exception as e:
            print(f"显示消息时出错: {e}")
            print("文智搜已在运行中，请检查系统托盘。")

def check_single_instance():
    """检查单实例，如果已有实例在运行则显示消息并退出
    
    Returns:
        SingleInstance: 单实例管理器对象，如果程序应该继续运行
        None: 如果检测到重复实例，程序应该退出
    """
    print("开始单实例检查...")
    instance_manager = SingleInstance()
    
    if instance_manager.is_already_running():
        print("检测到程序已在运行")
        instance_manager.show_already_running_message()
        return None
    
    print("单实例检查通过")
    return instance_manager 