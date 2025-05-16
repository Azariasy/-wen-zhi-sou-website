import re

# 要插入的方法代码
method_code = '''
    @Slot()
    def show_skipped_files_dialog_slot(self):
        """显示被跳过文件的对话框"""
        try:
            # 如果对话框已经存在，则只需显示它
            if hasattr(self, 'skipped_files_dialog') and self.skipped_files_dialog:
                self.skipped_files_dialog.show()
                self.skipped_files_dialog.raise_()  # 确保对话框位于前台
                return
                
            # 动态导入对话框类
            try:
                from skipped_files_dialog import SkippedFilesDialog
                # 创建跳过文件对话框实例
                self.skipped_files_dialog = SkippedFilesDialog(self)
                self.skipped_files_dialog.show()
            except ImportError as e:
                print(f"无法导入SkippedFilesDialog类: {e}")
                QMessageBox.critical(self, "错误", "无法打开跳过文件对话框，缺少必要的组件。")
        except Exception as e:
            print(f"显示跳过文件对话框时出错: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"显示跳过文件对话框时发生错误: {str(e)}")
'''

# 读取文件内容
with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 确定插入位置 - 在"# --- Cleanup ---"注释之前
target = '    # --- Cleanup --- --------------------------------------'
replacement = method_code + '\n' + target

# 替换内容
new_content = content.replace(target, replacement)

# 写回文件
with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("方法已成功添加!") 