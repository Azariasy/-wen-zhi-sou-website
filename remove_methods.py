#!/usr/bin/env python
import re

with open("search_gui_pyside.py", "r", encoding="utf-8") as f:
    content = f.read()

# 删除_create_size_filter_bar方法
pattern1 = r"def _create_size_filter_bar\(self\):.*?return size_filter_layout\n\n"
content = re.sub(pattern1, "", content, flags=re.DOTALL)

# 删除_create_date_filter_bar方法
pattern2 = r"def _create_date_filter_bar\(self\):.*?return date_filter_layout\n\n"
content = re.sub(pattern2, "", content, flags=re.DOTALL)

# 删除clear_dates_slot方法
pattern3 = r"def clear_dates_slot\(self\):.*?self\.end_date_edit\.setDate\(self\.default_end_date\)\n\n"
content = re.sub(pattern3, "", content, flags=re.DOTALL)

# 删除在_setup_connections中对clear_dates_slot的引用 - 更精确的模式
pattern4 = r"[ \t]*self\.clear_dates_button\.clicked\.connect\(self\.clear_dates_slot\).*?\n"
content = re.sub(pattern4, "", content, flags=re.DOTALL)

# 需要手动处理MainWindow.__init__方法中删除对_create_size_filter_bar和_create_date_filter_bar的调用
init_method = re.search(r"def __init__\(self\):.*?# ----------------------------------------------", content, re.DOTALL)
if init_method:
    init_content = init_method.group(0)
    # 移除对_create_size_filter_bar和_create_date_filter_bar方法的调用
    init_content = re.sub(r"[ \t]*size_filter_layout = self\._create_size_filter_bar\(\).*?\n", "", init_content, flags=re.DOTALL)
    init_content = re.sub(r"[ \t]*date_filter_layout = self\._create_date_filter_bar\(\).*?\n", "", init_content, flags=re.DOTALL)
    init_content = re.sub(r"[ \t]*main_layout\.addLayout\(size_filter_layout\).*?\n", "", init_content, flags=re.DOTALL)
    init_content = re.sub(r"[ \t]*main_layout\.addLayout\(date_filter_layout\).*?\n", "", init_content, flags=re.DOTALL)
    # 替换回处理后的内容
    content = content.replace(init_method.group(0), init_content)

# 编写输出文件
with open("search_gui_pyside_final.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Methods and references removed successfully - results in search_gui_pyside_final.py")
