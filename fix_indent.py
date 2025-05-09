import re

# 读取文件内容
with open('search_gui_pyside.py', 'r', encoding='utf-8') as file:
    content = file.read()

# 修复 _create_sort_bar 方法的缩进问题
# 在注释行和方法定义之间寻找不正确的缩进
fixed_content = re.sub(
    r'(\s+# \(Add other _create_\* helper methods if they were inline before\)\s+)(\s+)(def _create_sort_bar)',
    r'\1def _create_sort_bar',
    content
)

# 写入修复后的内容到临时文件
with open('search_gui_pyside_fixed.py', 'w', encoding='utf-8') as file:
    file.write(fixed_content)

print("修复完成，结果保存在 search_gui_pyside_fixed.py") 