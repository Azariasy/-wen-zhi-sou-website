import re

# 要插入的方法代码
method_code = '''
    def _update_theme_icons(self, theme_name):
        """更新主题相关的图标
        
        Args:
            theme_name: 主题名称
        """
        # 根据主题选择下拉箭头图标
        if theme_name == "现代蓝" or theme_name == "系统默认":
            arrow_icon_path = get_resource_path("down_arrow_blue.png")
        elif theme_name == "现代绿":
            arrow_icon_path = get_resource_path("down_arrow_green.png")
        elif theme_name == "现代紫":
            arrow_icon_path = get_resource_path("down_arrow_purple.png")
        else:
            # 默认使用蓝色
            arrow_icon_path = get_resource_path("down_arrow_blue.png")
            
        # 直接应用箭头图标
        if os.path.exists(arrow_icon_path):
            self._apply_direct_arrow_icons(arrow_icon_path)
    
    def _apply_direct_arrow_icons(self, arrow_icon_path):
        """直接将箭头图标应用到下拉框
        
        Args:
            arrow_icon_path: 箭头图标路径
        """
        try:
            # 规范化路径，确保在样式表中使用正确的路径分隔符
            icon_path = arrow_icon_path.replace('\\\\', '/').replace('\\', '/')
            
            # 将图标应用到所有下拉框
            for widget in [self.search_combo, self.scope_combo, self.mode_combo, self.sort_combo]:
                if widget:
                    try:
                        # 设置自定义样式表以使用新图标
                        widget.setStyleSheet(f"""
                            QComboBox::down-arrow {{
                                image: url({icon_path});
                                width: 14px;
                                height: 14px;
                            }}
                        """)
                    except Exception as e:
                        print(f"应用箭头图标到下拉框时出错: {e}")
                        
        except Exception as e:
            print(f"应用箭头图标时出错: {e}")
'''

# 读取文件内容
with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找合适的插入位置 - 选择在apply_theme方法结束后插入
# 首先找到apply_theme方法的结束位置
target_method = 'def apply_theme(self, theme_name):'
start_pos = content.find(target_method)
if start_pos != -1:
    # 往后找，寻找方法结束的位置
    # 方法结束的特征是下一个同级方法的定义
    next_method_pos = content.find('    def _apply_fallback_blue_theme', start_pos)
    if next_method_pos != -1:
        # 在apply_theme方法结束后插入新方法
        new_content = content[:next_method_pos] + method_code + content[next_method_pos:]
        
        # 写回文件
        with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("_update_theme_icons和_apply_direct_arrow_icons方法已成功添加!")
    else:
        print("无法找到apply_theme方法后的下一个方法")
else:
    print("无法找到apply_theme方法的位置") 