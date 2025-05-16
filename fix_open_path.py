import re

# 读取文件内容
with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 删除文件末尾的_open_path_with_desktop_services方法
pattern = r"    def _open_path_with_desktop_services\(self, path, is_file=True\):.*?QMessageBox\.warning\(self, \"错误\", f\"尝试打开\{'文件' if is_file else '文件夹'\}时出错:\\n\{path\}\\n\\n错误: \{e\}\"\)"
content = re.sub(pattern, "", content, flags=re.DOTALL)

# 在MainWindow类中添加正确的方法
class_end_pattern = r"class IndexDirectoriesDialog\(QDialog\):"
open_path_method = '''
    def _open_path_with_desktop_services(self, path, is_file=True):
        """使用QDesktopServices打开文件或文件夹。

        Args:
            path: 要打开的文件或文件夹路径
            is_file: 如果为True，则打开文件；如果为False，则打开文件夹
        """
        try:
            if not path:
                return

            # 检查路径是否存在
            path_obj = Path(path)
            if not path_obj.exists():
                QMessageBox.warning(self, "路径不存在", f"找不到{'文件' if is_file else '文件夹'}:\\n{path}")
                return

            # 转换为QUrl格式
            url = QUrl.fromLocalFile(str(path_obj))
            
            # 使用QDesktopServices打开文件或文件夹
            result = QDesktopServices.openUrl(url)
            
            if not result:
                if sys.platform == 'win32':
                    # 在Windows上使用备用方法
                    import subprocess
                    try:
                        subprocess.Popen(f'explorer "{path}"', shell=True)
                    except Exception as e:
                        QMessageBox.warning(self, "打开失败", f"无法打开{'文件' if is_file else '文件夹'}:\\n{path}\\n\\n错误: {e}")
                else:
                    QMessageBox.warning(self, "打开失败", f"无法打开{'文件' if is_file else '文件夹'}:\\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"尝试打开{'文件' if is_file else '文件夹'}时出错:\\n{path}\\n\\n错误: {e}")

'''

# 在类结束前插入方法
content = re.sub(class_end_pattern, open_path_method + "\n\n" + class_end_pattern, content)

# 保存修改后的内容
with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("文件已修复，_open_path_with_desktop_services方法已正确添加到MainWindow类中。") 