import re

# 要插入的方法代码
method_code = '''
    def _update_feature_availability(self):
        """更新UI基于许可证状态，启用或禁用专业版功能"""
        # 确保许可证管理器实例是最新的
        self.license_manager = get_license_manager()
        
        # 检查各种功能是否可用
        folder_tree_available = self.license_manager.is_feature_available(Features.FOLDER_TREE)
        pdf_support_available = self.license_manager.is_feature_available(Features.PDF_SUPPORT)
        email_support_available = self.license_manager.is_feature_available(Features.EMAIL_SUPPORT)
        markdown_support_available = self.license_manager.is_feature_available(Features.MARKDOWN_SUPPORT)
        wildcards_available = self.license_manager.is_feature_available(Features.WILDCARDS)
        advanced_themes_available = self.license_manager.is_feature_available(Features.ADVANCED_THEMES)
        
        # 更新主菜单中的专业版菜单
        self._update_pro_menu()
        
        # 更新文件夹树的可见性
        if hasattr(self, 'main_splitter') and hasattr(self, 'folder_tree'):
            # 获取主分隔器中的左侧窗口小部件（应该是包含文件夹树的容器）
            left_container = self.main_splitter.widget(0)
            
            if left_container:
                left_container.setVisible(folder_tree_available)
                
                # 调整分隔器大小
                if folder_tree_available:
                    # 如果显示文件夹树，设置分隔器位置为1/4处
                    self.main_splitter.setSizes([200, 600])
                else:
                    # 如果不显示文件夹树，将宽度设置为0，让右侧搜索结果占满宽度
                    self.main_splitter.setSizes([0, self.main_splitter.width()])
        
        # 更新文件类型复选框的状态
        if hasattr(self, 'file_type_checkboxes') and hasattr(self, 'pro_file_types'):
            # 遍历所有的专业版文件类型复选框
            for checkbox, info in self.pro_file_types.items():
                feature = info.get('feature')
                pro_label = info.get('pro_label')
                available = self.license_manager.is_feature_available(feature)
                
                # 更新复选框状态
                checkbox.setEnabled(available)
                checkbox.setStyleSheet("" if available else "color: #888888;")
                if pro_label:
                    pro_label.setVisible(not available)
                
                # 如果功能不可用，确保复选框未被选中
                if not available:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)
        
        # 更新主题设置
        current_theme = self.settings.value("ui/theme", "现代蓝")
        if not advanced_themes_available and current_theme not in ["现代蓝", "系统默认"]:
            # 如果高级主题不可用，但当前主题是高级主题，切换回基本主题
            self.settings.setValue("ui/theme", "现代蓝")
            self.apply_theme("现代蓝")
'''

# 读取文件内容
with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 寻找合适的插入位置 - 在MainWindow类中
# 选择在_force_ui_refresh方法后插入
target_method = 'def _force_ui_refresh(self):'
target_end = '        print("DEBUG: UI刷新完成")\n'
index = content.find(target_end)
if index != -1:
    # 找到方法结束的位置
    end_pos = index + len(target_end)
    # 在方法后找到下一行的位置
    next_line = content.find('\n', end_pos)
    if next_line != -1:
        # 在方法结束后插入新方法
        new_content = content[:next_line] + method_code + content[next_line:]
        
        # 写回文件
        with open('search_gui_pyside.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("_update_feature_availability方法已成功添加!")
    else:
        print("无法找到_force_ui_refresh方法结束后的换行符")
else:
    print("无法找到_force_ui_refresh方法结束的位置") 