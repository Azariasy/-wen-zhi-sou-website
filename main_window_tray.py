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
                return []
            
            if not search_triggered:
                return []
            
            # 等待搜索完成并获取结果
            import time
            from PySide6.QtCore import QCoreApplication
            
            # 对于轻量级搜索，等待更长时间确保获取到真实结果
            timeout = 80 if quick_search else 50  # 8秒或5秒超时
            elapsed = 0
            results_count = 0
            last_count = -1
            
            print(f"开始等待搜索结果，超时时间: {timeout/10}秒")
            
            while elapsed < timeout:
                QCoreApplication.processEvents()  # 处理Qt事件
                time.sleep(0.1)
                elapsed += 1
                
                # 检查results_table是否有数据
                if hasattr(self, 'results_table') and self.results_table:
                    current_count = self.results_table.rowCount()
                    
                    # 如果结果数量发生变化，记录
                    if current_count != last_count:
                        print(f"  等待{elapsed/10:.1f}秒: results_table行数从{last_count}变为{current_count}")
                        last_count = current_count
                    
                    if current_count > 0:
                        # 如果结果数量没有变化，说明搜索可能已完成
                        if current_count == results_count:
                            # 等待额外的时间确保搜索完全完成
                            if elapsed > 20:  # 至少等待2秒
                                print(f"  结果稳定在{current_count}行，搜索完成")
                                break
                        else:
                            results_count = current_count
                        
                        # 如果已经获取足够的结果，可以提前结束
                        if current_count >= max_results:
                            print(f"  已获取足够的结果({current_count}>={max_results})，提前结束")
                            break
                
                # 每秒输出一次进度
                if elapsed % 10 == 0:
                    print(f"  等待中... {elapsed/10:.0f}秒")
            
            print(f"等待结束，总等待时间: {elapsed/10:.1f}秒")
            
            # 从结果表格获取数据
            results = []
            
            # 对于轻量级搜索，优先使用original_search_results
            if quick_search and hasattr(self, 'original_search_results') and self.original_search_results:
                print(f"轻量级搜索：直接从original_search_results获取 {len(self.original_search_results)} 个结果")
                for i, result in enumerate(self.original_search_results[:max_results]):
                    try:
                        file_path = result.get('file_path', '')
                        if file_path:
                            # 获取预览内容
                            content_preview = result.get('content_preview', '')
                            if not content_preview:
                                # 对于文件名搜索，预览内容可以是文件路径或者简单描述
                                if search_scope == "filename":
                                    content_preview = f"文件名包含关键词 '{query}'"
                                else:
                                    content_preview = f"包含关键词 '{query}' 的文档"
                            
                            results.append({
                                'file_path': file_path,
                                'content_preview': content_preview[:200]
                            })
                    except Exception as e:
                        print(f"处理original_search_results第{i}个结果时出错: {e}")
                        continue
            elif hasattr(self, 'results_table') and self.results_table:
                row_count = self.results_table.rowCount()
                print(f"搜索完成，从results_table获取到 {row_count} 行结果")
                
                for row in range(min(row_count, max_results)):
                    try:
                        path_item = self.results_table.item(row, 0)
                        if path_item:
                            file_path = path_item.text()
                            
                            # 获取预览内容
                            content_preview = ""
                            preview_item = self.results_table.item(row, 1)
                            if preview_item:
                                content_preview = preview_item.text()[:200]
                            else:
                                # 对于文件名搜索，预览内容可以是文件路径或者简单描述
                                if search_scope == "filename":
                                    content_preview = f"文件名包含关键词 '{query}'"
                                else:
                                    content_preview = path_item.toolTip()[:200] if path_item.toolTip() else f"包含关键词 '{query}' 的文档"
                            
                            results.append({
                                'file_path': file_path,
                                'content_preview': content_preview
                            })
                    except Exception as e:
                        print(f"处理搜索结果第{row}行时出错: {e}")
                        continue
            
            # 恢复原始文件类型设置（仅对轻量级搜索）
            if quick_search:
                print("轻量级搜索完成：清除快速搜索模式标志")
                # 清除快速搜索模式标志
                if hasattr(self, '_quick_search_mode'):
                    delattr(self, '_quick_search_mode')
            
            if results:
                print(f"_perform_search 成功获取 {len(results)} 个真实搜索结果")
                # 打印前几个结果用于调试
                for i, result in enumerate(results[:3]):
                    print(f"  结果{i+1}: {os.path.basename(result['file_path'])}")
                return results
            else:
                print(f"未能获取到搜索结果，可能是搜索没有匹配项 (查询: '{query}', 范围: {search_scope})")
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