import re

# 读取文件内容
with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找方法标题和正文
method_pattern = r'def _show_pro_feature_dialog_message\(self, type_name\):\n\s+"""显示专业版功能对话框的实际消息"""\n(\s+)# 显示提示对话框'
new_method = '''def _show_pro_feature_dialog_message(self, type_name):
        """显示专业版功能对话框的实际消息"""
        # 显示提示对话框
        QMessageBox.information(
            self, 
            "专业版功能", 
            f"搜索 {type_name} 文件是专业版功能。\\n\\n"
            f"升级到专业版以解锁此功能和更多高级特性。"
        )'''

# 使用正则表达式查找并替换
content_lines = content.split('\n')
in_method = False
method_start = -1
method_end = -1

for i, line in enumerate(content_lines):
    if 'def _show_pro_feature_dialog_message' in line:
        method_start = i
        in_method = True
    elif in_method and line.strip() == '"""显示专业版功能对话框的实际消息"""':
        # 继续查找方法内容
        pass
    elif in_method and line.strip() == '# 对话框关闭后，重置过滤更新阻断标志':
        method_end = i
        in_method = False
        break

if method_start != -1 and method_end != -1:
    # 替换方法内容
    old_method_content = '\n'.join(content_lines[method_start:method_end])
    new_content = content.replace(old_method_content, new_method)
    
    # 写回文件
    with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("缩进错误已修复!")
else:
    print("无法找到需要修复的方法")

# Define the pattern to match
pattern = r'(\s+)else:\n(\s+)# 基础版功能\ntype_filter_layout\.addWidget\(checkbox\)'

# Replace with proper indentation
replacement = r'\1else:\n\2# 基础版功能\n\2type_filter_layout.addWidget(checkbox)'

# Apply the replacement
new_content = re.sub(pattern, replacement, content)

# Write the fixed content back
with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Indentation fixed successfully.') 