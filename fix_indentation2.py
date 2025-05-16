import re

def main():
    # 读取原始文件内容
    with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 修复第1463-1465行附近的缩进错误
    pattern1 = r'(                else:\n                    # 基础版功能\n)(\s*)type_filter_layout\.addWidget\(checkbox\)'
    replacement1 = r'\1                    type_filter_layout.addWidget(checkbox)'
    content = re.sub(pattern1, replacement1, content)

    # 修复_show_pro_feature_dialog_message方法中的缩进错误 (QMessageBox缩进太多)
    pattern2 = r'def _show_pro_feature_dialog_message\(self, type_name\):\n(\s+)"""显示专业版功能对话框的实际消息"""\n(\s+)# 显示提示对话框\n(\s+)QMessageBox\.information'
    replacement2 = r'def _show_pro_feature_dialog_message(self, type_name):\n\1"""显示专业版功能对话框的实际消息"""\n\1# 显示提示对话框\n\1QMessageBox.information'
    content = re.sub(pattern2, replacement2, content)

    # 将修复后的内容写回文件
    with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("缩进修复完成！")

if __name__ == "__main__":
    main() 