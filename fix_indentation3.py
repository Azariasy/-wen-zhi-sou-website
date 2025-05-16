# 修复search_gui_pyside.py文件中的所有缩进错误

def main():
    # 读取文件内容
    with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 修复所有已知的缩进问题
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 修复第1463-1465行附近的缩进错误
        if i == 1464 and line.strip() == "# 基础版功能" and not line.startswith("                    "):
            fixed_lines.append("                    # 基础版功能\n")
            i += 1
            if i < len(lines) and "type_filter_layout.addWidget(checkbox)" in lines[i]:
                fixed_lines.append("                    type_filter_layout.addWidget(checkbox)\n")
            else:
                fixed_lines.append(lines[i])
            i += 1
            continue
            
        # 修复_show_pro_feature_dialog_message方法中的缩进错误
        elif i >= 1524 and i <= 1530 and "def _show_pro_feature_dialog_message" in line:
            fixed_lines.append(line)  # add the def line
            i += 1
            
            # 添加注释行
            if i < len(lines) and '"""显示专业版功能对话框的实际消息"""' in lines[i]:
                fixed_lines.append(lines[i])
                i += 1
            
            # 添加"# 显示提示对话框"行
            if i < len(lines) and '# 显示提示对话框' in lines[i]:
                fixed_lines.append(lines[i])
                i += 1
            
            # 修复QMessageBox.information的缩进
            if i < len(lines) and 'QMessageBox.information' in lines[i]:
                # 确保与上一行缩进相同
                indent = fixed_lines[-1].split('#')[0]
                fixed_lines.append(f"{indent}QMessageBox.information(\n")
                i += 1
            
            continue
            
        # 修复except缩进问题（检查多处位置）
        elif "self._update_theme_icons(theme_name)" in line:
            fixed_lines.append(line)
            i += 1
            
            # 检查下一行是否有缩进过多的except
            if i < len(lines) and lines[i].strip().startswith("except Exception as e:") and lines[i].startswith("                    "):
                # 修正except的缩进，减少一个缩进级别
                fixed_lines.append("            except Exception as e:\n")
            else:
                fixed_lines.append(lines[i] if i < len(lines) else "")
            i += 1
            continue
        
        fixed_lines.append(line)
        i += 1
    
    # 写回文件
    with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("所有缩进错误已修复！")

if __name__ == "__main__":
    main() 