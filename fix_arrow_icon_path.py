import re

# 读取文件内容
with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找并修复错误的行
error_line = "            icon_path = arrow_icon_path.replace('\\\\', '/').replace('\\\', '/')"
fixed_line = "            icon_path = arrow_icon_path.replace('\\\\', '/').replace('\\\\', '/')"

# 替换内容
new_content = content.replace(error_line, fixed_line)

# 写回文件
with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("字符串引号错误已修复!") 