from PySide6.QtCore import Qt, QEvent, QSettings, QThread
from PySide6.QtWidgets import QMainWindow, QSystemTrayIcon, QMessageBox, QMenu, QDialog
from PySide6.QtGui import QCloseEvent, QIcon, QAction
import os

from search_gui_pyside import MainWindow, ORGANIZATION_NAME, APPLICATION_NAME
from quick_search_controller import QuickSearchController

class TrayMainWindow(MainWindow):
    """继承原MainWindow并添加托盘支持的主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 托盘图标实例，会在main_tray.py中设置
        self.tray_icon = None
        
        # 是否首次最小化到托盘标志
        self.first_minimize = True
        
        # 是否直接退出（不最小化到托盘）
        self.force_quit = False
        
        # 用户首选项设置 - 使用与主程序相同的设置路径
        self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        
        # 设置窗口标题
        self.setWindowTitle("文智搜 (支持托盘)")
        
        # 创建轻量级搜索控制器
        self.quick_search_controller = QuickSearchController(self)
    
    def _add_tray_settings_menu(self):
        """添加托盘设置菜单 - 简化版本"""
        # 移除此方法，不再创建单独的托盘菜单
        # 托盘设置应该通过设置菜单访问
        pass
    
    def set_tray_icon(self, tray_icon):
        """设置托盘图标实例"""
        self.tray_icon = tray_icon
    
    def changeEvent(self, event):
        """处理窗口状态改变事件"""
        if event.type() == QEvent.WindowStateChange:
            # 读取最小化到托盘设置
            minimize_to_tray = self.settings.value("tray/minimize_to_tray", False, type=bool)
            
            if self.isMinimized() and minimize_to_tray and self.tray_icon:
                # 窗口被最小化且设置了最小化到托盘
                event.ignore()
                self.hide()
                
                # 如果是首次最小化到托盘，显示提示
                if self.first_minimize:
                    self.tray_icon.showMessage(
                        "文智搜已最小化到托盘",
                        "应用程序将继续在后台运行。点击托盘图标可以重新打开主窗口。",
                        QSystemTrayIcon.Information,
                        2000
                    )
                    self.first_minimize = False
                return
        
        # 处理其他类型的事件
        super().changeEvent(event)
    
    def closeEvent(self, event: QCloseEvent):
        """处理窗口关闭事件"""
        # 读取托盘行为设置
        close_to_tray = self.settings.value("tray/close_to_tray", True, type=bool)
        
        # 如果设置了强制退出或关闭时不最小化到托盘，则正常关闭
        if self.force_quit or not close_to_tray:
            # 调用原closeEvent进行清理
            self._shutdown_threads()
            super().closeEvent(event)
            return
        
        # 否则，将窗口最小化到托盘
        event.ignore()  # 忽略原始关闭事件
        self.hide()     # 隐藏窗口
        
        # 如果是首次最小化到托盘，显示提示
        if self.first_minimize and self.tray_icon:
            self.tray_icon.showMessage(
                "文智搜已最小化到托盘",
                "应用程序将继续在后台运行。点击托盘图标可以重新打开主窗口。",
                QSystemTrayIcon.Information,
                3000
            )
            self.first_minimize = False
    
    def _shutdown_threads(self):
        """确保所有线程安全停止"""
        try:
            print("正在关闭所有线程...")
            
            # 检查是否有搜索线程在运行
            if hasattr(self, 'search_thread') and self.search_thread and self.search_thread.isRunning():
                print("正在停止搜索线程...")
                self.search_thread.terminate()
                self.search_thread.wait(1000)
                
            # 检查是否有索引线程在运行
            if hasattr(self, 'indexing_thread') and self.indexing_thread and self.indexing_thread.isRunning():
                print("正在停止索引线程...")
                self.indexing_thread.terminate()
                self.indexing_thread.wait(1000)
            
            # 检查是否有工作线程在运行
            if hasattr(self, 'worker_thread') and self.worker_thread and self.worker_thread.isRunning():
                print("正在停止工作线程...")
                # 通知工作线程停止
                if hasattr(self, 'worker') and hasattr(self.worker, 'stop_requested'):
                    self.worker.stop_requested = True
                self.worker_thread.terminate()
                self.worker_thread.wait(1000)
                
            # 检查所有QThread子类（查找所有线程）
            all_threads = []
            for attr_name in dir(self):
                attr = getattr(self, attr_name)
                if isinstance(attr, QThread) and attr.isRunning():
                    print(f"正在停止额外线程: {attr_name}")
                    attr.terminate()
                    attr.wait(1000)
                    all_threads.append(attr)
                    
            print(f"已关闭 {len(all_threads)} 个额外线程")
        except Exception as e:
            print(f"关闭线程时出错: {e}")
    
    def force_close(self):
        """强制关闭窗口（不最小化到托盘）"""
        self.force_quit = True
        self._shutdown_threads()
        self.close()
    
    def show_tray_settings_dialog(self):
        """显示托盘设置对话框"""
        from tray_settings import TraySettingsDialog
        dialog = TraySettingsDialog(self)
        dialog.exec()
    
    def show_tray_settings_dialog_slot(self):
        """显示托盘设置对话框的槽方法"""
        try:
            from tray_settings import TraySettingsDialog
            dialog = TraySettingsDialog(self)
            dialog.exec()
        except ImportError:
            QMessageBox.information(self, "托盘设置", "托盘设置功能暂不可用。")
    
    def show_startup_settings_dialog_slot(self):
        """显示启动设置对话框的槽方法"""
        try:
            from startup_settings import StartupSettingsDialog
            dialog = StartupSettingsDialog(self)
            dialog.exec()
        except ImportError as e:
            QMessageBox.warning(self, "启动设置", f"启动设置功能暂不可用:\n{str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开启动设置时出现错误:\n{str(e)}")
    
    def show_hotkey_settings_dialog(self):
        """显示热键设置对话框"""
        # 显示热键设置对话框
        try:
            from hotkey_settings import HotkeySettingsDialog
            dialog = HotkeySettingsDialog(self)  # 只传递一个参数
            result = dialog.exec()
            
            # 如果用户接受了更改，重新加载热键设置
            if result == QDialog.Accepted:
                # 重新加载热键设置
                if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
                    self.hotkey_manager.reload_hotkeys()
                    print("已重新加载热键设置")
                    
                # 更新托盘菜单显示
                self._on_hotkey_settings_updated()
        except ImportError as e:
            QMessageBox.warning(self, "热键设置", f"热键设置功能暂不可用:\n{str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开热键设置时出现错误:\n{str(e)}")
    
    def show_hotkey_settings_dialog_slot(self):
        """显示热键设置对话框的槽方法"""
        try:
            from hotkey_settings import HotkeySettingsDialog
            dialog = HotkeySettingsDialog(self)  # 只传递一个参数
            # 连接设置更新信号
            dialog.hotkey_updated_signal.connect(self._on_hotkey_settings_updated)
            dialog.exec()
        except ImportError as e:
            QMessageBox.warning(self, "热键设置", f"热键设置功能暂不可用:\n{str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开热键设置时出现错误:\n{str(e)}")
    
    def _on_hotkey_settings_updated(self):
        """热键设置更新后的处理"""
        print("托盘版本: 热键设置已更新，正在重新加载...")
        
        # 重新加载热键设置
        if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
            self.hotkey_manager.reload_hotkeys()
            print("热键管理器已重新加载设置")
            
        # 更新托盘菜单中的热键显示
        if hasattr(self, 'tray_icon') and self.tray_icon:
            try:
                # 调用托盘图标的刷新方法
                if hasattr(self.tray_icon, 'refresh_hotkey_display'):
                    self.tray_icon.refresh_hotkey_display()
                    print("托盘菜单热键显示已更新")
                else:
                    # 备用方法
                    from dynamic_tray_menu import update_tray_menu_hotkeys
                    update_tray_menu_hotkeys(self.tray_icon)
                    print("托盘菜单热键显示已更新（备用方法）")
            except ImportError:
                print("无法导入dynamic_tray_menu模块")
            except Exception as e:
                print(f"更新托盘菜单时出错: {e}")
                
        self.statusBar().showMessage("热键设置已更新并立即生效", 3000)
    
    def show_quick_search_dialog(self, initial_query=None):
        """显示轻量级搜索对话框
        
        Args:
            initial_query: 初始搜索关键词，可选
        """
        # 使用轻量级搜索控制器显示对话框
        self.quick_search_controller.show_quick_search(initial_query)
        
        # 同步主题到快捷搜索窗口
        self._sync_theme_to_quick_search()
    
    def _sync_theme_to_quick_search(self):
        """同步主题到快捷搜索窗口"""
        if hasattr(self, 'quick_search_controller') and self.quick_search_controller:
            current_theme = self.settings.value("ui/theme", "现代蓝")
            # 通知快捷搜索控制器更新主题
            if hasattr(self.quick_search_controller, 'update_theme'):
                self.quick_search_controller.update_theme(current_theme)
    
    def apply_theme(self, theme_name):
        """应用主题（重写父类方法以添加快捷搜索同步）"""
        # 调用父类的主题应用方法
        super().apply_theme(theme_name)
        
        # 同步主题到快捷搜索窗口
        self._sync_theme_to_quick_search()
        
        # 更新托盘图标的主题显示
        if hasattr(self, 'tray_icon') and self.tray_icon:
            try:
                if hasattr(self.tray_icon, 'update_theme_display'):
                    self.tray_icon.update_theme_display(theme_name)
            except Exception as e:
                print(f"更新托盘图标主题显示时出错: {e}")
    
    def _on_theme_changed(self, theme_name):
        """主题变化时的处理（新增方法）"""
        print(f"托盘版本: 主题已变更为 {theme_name}")
        
        # 应用新主题
        self.apply_theme(theme_name)
        
        # 同步到快捷搜索窗口
        self._sync_theme_to_quick_search()
        
        # 显示状态消息
        self.statusBar().showMessage(f"主题已切换为: {theme_name}", 2000)
    
    def _perform_search(self, query, max_results=50, quick_search=False, search_scope="fulltext"):
        """执行搜索，供轻量级搜索控制器调用
        
        Args:
            query: 搜索查询词
            max_results: 最大结果数
            quick_search: 是否是快速搜索模式
            search_scope: 搜索范围，"filename"为文件名搜索，"fulltext"为全文搜索
            
        Returns:
            list: 搜索结果
        """
        try:
            print(f"主窗口执行搜索: '{query}', 最大结果数: {max_results}, 搜索范围: {search_scope}")
            
            # 设置搜索查询框的文本
            if hasattr(self, 'search_line_edit'):
                self.search_line_edit.setText(query)
            
            # 设置搜索范围
            if hasattr(self, 'scope_combo'):
                if search_scope == "filename":
                    # 设置为文件名搜索 (索引1)
                    self.scope_combo.setCurrentIndex(1)
                    print(f"设置搜索范围为文件名搜索")
                elif search_scope == "fulltext":
                    # 设置为全文搜索 (索引0)
                    self.scope_combo.setCurrentIndex(0)
                    print(f"设置搜索范围为全文搜索")
            else:
                print("未找到scope_combo控件")
            
            # 对于轻量级搜索，临时禁用文件类型过滤
            original_blocking_state = None
            if quick_search:
                print("轻量级搜索模式：设置快速搜索模式标志")
                # 为轻量级搜索设置一个标志，让过滤方法知道要直接显示结果
                self._quick_search_mode = True
            
            # 清空当前搜索结果
            if hasattr(self, 'results_table') and self.results_table:
                self.results_table.setRowCount(0)
            
            # 执行搜索
            search_triggered = False
            if hasattr(self, 'start_search_slot'):
                self.start_search_slot()
                search_triggered = True
                print("通过start_search_slot触发搜索")
            elif hasattr(self, '_start_search_common'):
                # 根据搜索范围调用不同的搜索方法
                scope_param = search_scope if search_scope in ["filename", "fulltext"] else "fulltext"
                self._start_search_common("phrase", query, scope_param)
                search_triggered = True
                print(f"通过_start_search_common触发搜索，范围: {scope_param}")
            else:
                print("没有找到合适的搜索方法")
            
            if not search_triggered:
                return []
            
            # 动态等待搜索完成 - 基于搜索状态而非固定时间
            import time
            from PySide6.QtCore import QCoreApplication
            
            # 🔧 修复动态等待机制：清空旧结果，确保获取新结果
            # 先清空旧的搜索结果，避免获取到缓存的旧结果
            if hasattr(self, 'original_search_results'):
                self.original_search_results = None
                print(f"{'快捷搜索' if quick_search else '普通搜索'}：已清空旧的original_search_results")
            
            # 动态等待策略：基于搜索完成状态，而非固定时间
            max_wait_time = 30 if not quick_search else 15  # 最大等待时间（防止死锁）
            check_interval = 0.05  # 更频繁的检查间隔（50ms）
            
            elapsed = 0
            search_completed = False
            results_available = False
            
            print(f"{'快捷搜索' if quick_search else '普通搜索'}：开始动态等待搜索完成...")
            
            while elapsed < max_wait_time and not search_completed:
                QCoreApplication.processEvents()  # 处理Qt事件
                time.sleep(check_interval)
                elapsed += 1  # 计数器（每次+1代表50ms）
                
                # 检查搜索是否完成的多个指标
                original_results_ready = (hasattr(self, 'original_search_results') and 
                                        self.original_search_results is not None and
                                        len(self.original_search_results) >= 0)  # 包括0个结果的情况
                
                table_has_results = (hasattr(self, 'results_table') and 
                                   self.results_table.rowCount() >= 0)  # 包括0个结果的情况
                
                # 检查搜索进行标志（如果主窗口有这个标志）
                search_not_in_progress = True
                if hasattr(self, '_search_in_progress'):
                    search_not_in_progress = not self._search_in_progress
                
                # 判断搜索是否完成 - 修复：确保获取的是新结果
                if original_results_ready and search_not_in_progress:
                    results_available = True
                    search_completed = True
                    result_count = len(self.original_search_results) if self.original_search_results else 0
                    print(f"{'快捷搜索' if quick_search else '普通搜索'}：检测到新的original_search_results可用({result_count}个)，搜索完成（{elapsed*0.05:.2f}秒）")
                    break
                elif table_has_results and search_not_in_progress:
                    results_available = True
                    search_completed = True
                    table_count = self.results_table.rowCount() if hasattr(self, 'results_table') else 0
                    print(f"{'快捷搜索' if quick_search else '普通搜索'}：检测到results_table有结果({table_count}个)且搜索不在进行中，搜索完成（{elapsed*0.05:.2f}秒）")
                    break
                
                # 定期输出进度（每1秒输出一次，减少日志噪音）
                if elapsed % 20 == 0 and elapsed > 0:  # 20 * 0.05 = 1秒
                    print(f"{'快捷搜索' if quick_search else '普通搜索'}：等待中... {elapsed*0.05:.1f}秒")
            
            # 输出等待结果
            if search_completed:
                print(f"{'快捷搜索' if quick_search else '普通搜索'}：搜索完成，总等待时间: {elapsed*0.05:.2f}秒")
            else:
                print(f"{'快捷搜索' if quick_search else '普通搜索'}：等待超时，总等待时间: {elapsed*0.05:.2f}秒")
            
            # 优先返回original_search_results
            if hasattr(self, 'original_search_results') and self.original_search_results is not None:
                results_count = len(self.original_search_results)
                print(f"{'快捷搜索' if quick_search else '普通搜索'}：使用original_search_results，共{results_count}个结果")
                # 确保返回的结果格式正确
                if results_count > 0:
                    return self.original_search_results[:max_results]
                else:
                    print(f"⚠️ original_search_results为空，尝试从results_table获取")
            else:
                print(f"⚠️ original_search_results不可用，尝试从results_table获取")
            
            # 备用方案：从results_table获取结果
            if hasattr(self, 'results_table') and self.results_table.rowCount() > 0:
                table_rows = self.results_table.rowCount()
                print(f"{'快捷搜索' if quick_search else '普通搜索'}：从results_table获取结果，共{table_rows}个")
                results = []
                for row in range(min(table_rows, max_results)):
                    try:
                        file_path_item = self.results_table.item(row, 0)
                        content_item = self.results_table.item(row, 1)
                        
                        if file_path_item:
                            file_path = file_path_item.text()
                            content = content_item.text() if content_item else ""
                            results.append({
                                'file_path': file_path,
                                'content_preview': content
                            })
                    except Exception as e:
                        print(f"处理结果行{row}时出错: {str(e)}")
                        continue
                
                return results
            
            print(f"{'快捷搜索' if quick_search else '普通搜索'}：未找到任何结果")
            return []
                
        except Exception as e:
            print(f"轻量级搜索执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def open_file(self, path):
        """打开文件（供轻量级搜索控制器调用）
        
        Args:
            path: 文件路径
        """
        # 使用主窗口现有的文件打开逻辑
        try:
            # 这里需要根据主窗口实际实现调整
            # 例如，可能需要调用特定的方法来打开文件
            
            # 如果有专门的文件打开方法，使用它
            if hasattr(self, 'open_path_with_desktop_services'):
                self.open_path_with_desktop_services(path)
            # 或者使用操作系统默认程序打开
            else:
                import os
                os.startfile(path)
        except Exception as e:
            print(f"打开文件失败: {str(e)}")
            import traceback
            traceback.print_exc() 