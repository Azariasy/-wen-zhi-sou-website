
def apply_theme(self, theme_name):
    """应用程序主题设置"""
    app = QApplication.instance()
    
    # 检查非蓝色主题是否可用（是否有专业版许可证）
    advanced_themes_available = self.license_manager.is_feature_available(Features.ADVANCED_THEMES)
    
    # 如果选择了非蓝色主题但没有专业版许可证，就强制使用蓝色主题
    if theme_name != "现代蓝" and not advanced_themes_available:
        if not hasattr(self, '_theme_warning_shown'):
            self._theme_warning_shown = False
            
        if not self._theme_warning_shown:
            self._theme_warning_shown = True
            QMessageBox.information(
                self, 
                "主题限制", 
                "高级主题（现代绿、现代紫）仅在专业版中可用。\n"
                "已自动切换到现代蓝主题。\n"
                "升级到专业版以解锁所有主题。"
            )
        
        # 强制使用现代蓝主题并保存设置
        theme_name = "现代蓝"
        self.settings.setValue("ui/theme", theme_name)
    
    if theme_name == "现代蓝":
        # 使用现代蓝色主题
        try:
            # 加载蓝色样式表
            style_path = os.path.join(os.path.dirname(__file__), "blue_style.qss")
            if os.path.exists(style_path):
                with open(style_path, "r", encoding="utf-8") as f:
                    stylesheet = f.read()
                # 确保QSS使用正确的checkmark图标
                stylesheet = stylesheet.replace("image: url(checkmark.png)", "image: url(checkmark_blue.png)")
                app.setStyleSheet(stylesheet)
                print("Applied modern blue theme.")
            else:
                print(f"Blue style file not found: {style_path}")
                # 回退到系统默认
                app.setStyleSheet("")
        except Exception as e:
            print(f"Error applying modern blue style: {e}. Falling back to system default.")
            app.setStyleSheet("")
            
    elif theme_name == "现代绿":
        # 使用现代绿色主题
        try:
            # 加载绿色样式表
            style_path = os.path.join(os.path.dirname(__file__), "green_style.qss")
            if os.path.exists(style_path):
                with open(style_path, "r", encoding="utf-8") as f:
                    stylesheet = f.read()
                # 确保QSS使用正确的checkmark图标
                stylesheet = stylesheet.replace("image: url(checkmark.png)", "image: url(checkmark_green.png)")
                app.setStyleSheet(stylesheet)
                print("Applied modern green theme.")
            else:
                print(f"Green style file not found: {style_path}")
                # 回退到现代蓝
                self._apply_fallback_blue_theme()
        except Exception as e:
            print(f"Error applying modern green style: {e}. Falling back to modern blue theme.")
            self._apply_fallback_blue_theme()
            
    elif theme_name == "现代紫":
        # 使用现代紫色主题
        try:
            # 加载紫色样式表
            style_path = os.path.join(os.path.dirname(__file__), "purple_style.qss")
            if os.path.exists(style_path):
                with open(style_path, "r", encoding="utf-8") as f:
                    stylesheet = f.read()
                # 确保QSS使用正确的checkmark图标
                stylesheet = stylesheet.replace("image: url(checkmark.png)", "image: url(checkmark_purple.png)")
                app.setStyleSheet(stylesheet)
                print("Applied modern purple theme.")
            else:
                print(f"Purple style file not found: {style_path}")
                # 回退到现代蓝
                self._apply_fallback_blue_theme()
        except Exception as e:
            print(f"Error applying modern purple style: {e}. Falling back to modern blue theme.")
            self._apply_fallback_blue_theme()
    else:
        # 对于任何未知主题，使用现代蓝
        self._apply_fallback_blue_theme()
