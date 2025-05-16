import os
import sys
from pathlib import Path
import traceback
from PySide6.QtCore import Qt, Signal, QSettings, Slot
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox
)

class SkippedFilesDialog(QDialog):
    """跳过文件对话框，显示索引过程中被跳过的文件及其原因"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("跳过的文件")
        self.setMinimumSize(800, 600)
        self.settings = QSettings()
        
        # 恢复窗口大小
        if self.settings.contains("skippedFilesDialog/geometry"):
            self.restoreGeometry(self.settings.value("skippedFilesDialog/geometry"))
            
        # 初始化变量
        self.skipped_files = []
        self.filtered_files = []
        self.current_page = 0
        self.page_size = 100  # 每页显示的记录数
        
        # 创建UI
        self._create_ui()
        
        # 加载数据
        self._load_skipped_files()
        
    def _create_ui(self):
        """创建用户界面"""
        layout = QVBoxLayout(self)
        
        # 创建过滤和控制区域
        filter_layout = QHBoxLayout()
        filter_label = QLabel("过滤类型:", self)
        self.filter_type_combo = QComboBox(self)
        self.filter_type_combo.addItem("全部", "all")
        self.filter_type_combo.addItem("PDF处理超时", "pdf_timeout")
        self.filter_type_combo.addItem("内容超过大小限制", "content_limit")
        self.filter_type_combo.addItem("需要密码的压缩包", "password_archive")
        self.filter_type_combo.addItem("损坏的压缩包", "corrupted_archive")
        self.filter_type_combo.addItem("许可证限制", "license_limit")
        
        self.refresh_button = QPushButton("刷新", self)
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_type_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(self.refresh_button)
        layout.addLayout(filter_layout)
        
        # 创建表格
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["文件名", "文件路径", "跳过原因", "时间"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 文件名列
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # 文件路径列
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 跳过原因列
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 时间列
        layout.addWidget(self.table)
        
        # 创建分页控件
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("上一页", self)
        self.page_info_label = QLabel("1/1", self)
        self.page_info_label.setAlignment(Qt.AlignCenter)
        self.next_button = QPushButton("下一页", self)
        
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_info_label)
        pagination_layout.addWidget(self.next_button)
        layout.addLayout(pagination_layout)
        
        # 创建底部按钮区域
        button_layout = QHBoxLayout()
        self.open_file_button = QPushButton("打开文件", self)
        self.open_folder_button = QPushButton("打开所在文件夹", self)
        self.clear_log_button = QPushButton("清空记录", self)
        self.close_button = QPushButton("关闭", self)
        
        button_layout.addWidget(self.open_file_button)
        button_layout.addWidget(self.open_folder_button)
        button_layout.addStretch()
        button_layout.addWidget(self.clear_log_button)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
        
        # 连接信号
        self.filter_type_combo.currentIndexChanged.connect(self._apply_filter)
        self.refresh_button.clicked.connect(self._load_skipped_files)
        self.prev_button.clicked.connect(self._go_to_prev_page)
        self.next_button.clicked.connect(self._go_to_next_page)
        self.open_file_button.clicked.connect(self._open_selected_file)
        self.open_folder_button.clicked.connect(self._open_selected_folder)
        self.clear_log_button.clicked.connect(self._clear_log)
        self.close_button.clicked.connect(self.reject)
        self.table.itemSelectionChanged.connect(self._update_button_states)
        
        # 初始化按钮状态
        self._update_button_states()

    def _load_skipped_files(self):
        """加载跳过文件的记录"""
        # 获取索引目录
        default_index_path = str(Path.home() / "Documents" / "DocumentSearchIndex")
        index_dir = self.settings.value("indexing/indexDirectory", default_index_path)
        
        if not index_dir or not os.path.exists(index_dir):
            print("警告: 索引目录不存在或未配置！请先配置并创建索引。")
            self.skipped_files = []
            self._apply_filter()
            return
            
        # 构建日志文件路径
        log_file_path = os.path.join(index_dir, "index_skipped_files.tsv")
        
        if not os.path.exists(log_file_path):
            print("提示: 未找到跳过文件的记录，可能没有文件被跳过。")
            self.skipped_files = []
            self._apply_filter()
            return
            
        try:
            # 读取TSV文件
            self.skipped_files = []
            expected_headers = ["文件路径", "跳过原因", "时间"] # 定义预期的表头
            
            with open(log_file_path, 'r', encoding='utf-8') as f:
                import csv
                reader = csv.reader(f, delimiter='\t')
                
                # 尝试读取文件头进行验证，但不强制要求与预期完全一致
                try:
                    header_row = next(reader)
                    print(f"DEBUG: TSV文件头: {header_row}")
                    if header_row != expected_headers:
                         print(f"警告: TSV文件头不符合预期: {header_row} vs {expected_headers}")
                except StopIteration:
                    print("警告: TSV文件为空或只有表头。")
                    self._apply_filter() # 确保UI更新为空状态
                    return # 文件为空，无需继续

                # 读取数据行
                for idx, row in enumerate(reader):
                    # 增加检查，如果当前行内容与表头相同，则跳过
                    if row == expected_headers:
                        print(f"DEBUG: 跳过第 {idx+2} 行，内容疑似表头: {row}")
                        continue
                        
                    if len(row) >= 3:
                        file_path, reason, timestamp = row[0], row[1], row[2]
                        
                        # 提取原因类型
                        reason_type = "unknown"
                        if "PDF处理超时" in reason:
                            reason_type = "pdf_timeout"
                        elif "内容大小超过限制" in reason:
                            reason_type = "content_limit"
                        elif "需要密码的ZIP" in reason or "需要密码的RAR" in reason:
                            reason_type = "password_archive"
                        elif "损坏的ZIP" in reason or "损坏的RAR" in reason:
                            reason_type = "corrupted_archive"
                        elif "许可证限制" in reason:
                            reason_type = "license_limit"
                        
                        self.skipped_files.append({
                            "file_path": file_path,
                            "reason": reason,
                            "reason_type": reason_type,
                            "timestamp": timestamp
                        })
                    else:
                        print(f"警告: 跳过格式不正确的行 {idx+2}: {row}")
            
            # 按时间戳倒序排序（最新的在前面）
            self.skipped_files.sort(key=lambda x: x["timestamp"], reverse=True)
            print(f"DEBUG: 加载了 {len(self.skipped_files)} 条有效跳过文件记录")
            
            # 应用过滤器并更新UI
            self._apply_filter()
            
        except Exception as e:
            print(f"加载跳过文件错误: {e}")
            import traceback
            print(traceback.format_exc())
            self.skipped_files = []
            self._apply_filter()
    
    def _apply_filter(self):
        """根据过滤条件筛选记录"""
        filter_type = self.filter_type_combo.currentData()
        print(f"DEBUG: 应用过滤器 - 类型: {filter_type}")
        
        if filter_type == "all":
            self.filtered_files = self.skipped_files.copy()
        else:
            self.filtered_files = [item for item in self.skipped_files if item["reason_type"] == filter_type]
            
        # 重置当前页码并更新UI
        self.current_page = 0
        self._update_ui()
    
    def _update_ui(self):
        """更新UI显示"""
        # 清空表格内容，保留表头 - 只移除所有行，不清除表头
        self.table.setRowCount(0)
        
        # 计算总页数
        total_items = len(self.filtered_files)
        print(f"DEBUG: 更新UI，过滤后文件总数: {total_items}")
        total_pages = max(1, (total_items + self.page_size - 1) // self.page_size)
        
        # 更新页码信息
        if total_items == 0:
            self.page_info_label.setText("0/0")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            return  # 没有记录，直接返回
        else:
            self.current_page = min(self.current_page, total_pages - 1)
            self.page_info_label.setText(f"{self.current_page + 1}/{total_pages}")
            self.prev_button.setEnabled(self.current_page > 0)
            self.next_button.setEnabled(self.current_page < total_pages - 1)
        
        # 获取当前页的数据
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, total_items)
        current_page_data = self.filtered_files[start_idx:end_idx]
        print(f"DEBUG: 当前页显示 {start_idx} 到 {end_idx} 的记录，共 {len(current_page_data)} 条")
        
        # 添加到表格 - 确保表格列数与表头一致
        for row_idx, item_data in enumerate(current_page_data):
            file_path = item_data["file_path"]
            # 从文件路径中提取文件名
            file_name = Path(file_path).name
            reason = item_data["reason"]
            timestamp = item_data["timestamp"]
            
            # 插入新行
            self.table.insertRow(row_idx)
            
            # 设置各列的数据
            try:
                # 第一列是文件名（从路径提取）
                self.table.setItem(row_idx, 0, QTableWidgetItem(file_name))
                # 第二列是完整路径
                self.table.setItem(row_idx, 1, QTableWidgetItem(file_path))
                # 第三列是跳过原因
                self.table.setItem(row_idx, 2, QTableWidgetItem(reason))
                # 第四列是时间戳
                self.table.setItem(row_idx, 3, QTableWidgetItem(timestamp))
                
                # 存储完整数据到第一个单元格
                self.table.item(row_idx, 0).setData(Qt.UserRole, item_data)
            except Exception as e:
                print(f"设置表格单元格时出错: {e}")
                
        # 更新按钮状态
        self._update_button_states()
    
    def _go_to_prev_page(self):
        """转到上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_ui()
            
    def _go_to_next_page(self):
        """转到下一页"""
        total_pages = (len(self.filtered_files) + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._update_ui()
    
    def _open_selected_file(self):
        """打开选中的文件"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        # 从第一个单元格获取存储的完整数据
        item_data = self.table.item(row, 0).data(Qt.UserRole)
        file_path = item_data["file_path"]
        
        # 处理压缩包内文件
        if "::" in file_path:
            archive_path = file_path.split("::")[0]
            file_path = archive_path  # 打开压缩包而不是里面的文件
            
        # 使用主窗口的方法打开文件
        if self.parent():
            self.parent()._open_path_with_desktop_services(file_path, is_file=True)
    
    def _open_selected_folder(self):
        """打开选中文件所在的文件夹"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        # 从第一个单元格获取存储的完整数据
        item_data = self.table.item(row, 0).data(Qt.UserRole)
        file_path = item_data["file_path"]
        
        # 获取文件夹路径
        folder_path = ""
        if "::" in file_path:
            archive_path = file_path.split("::")[0]
            folder_path = str(Path(archive_path).parent)
        else:
            folder_path = str(Path(file_path).parent)
            
        # 使用主窗口的方法打开文件夹
        if self.parent():
            self.parent()._open_path_with_desktop_services(folder_path, is_file=False)
    
    def _clear_log(self):
        """清空跳过文件的日志"""
        reply = QMessageBox.question(self, "确认清空", 
                                   "确定要清空跳过文件的记录吗？此操作不可撤销。",
                                   QMessageBox.Yes | QMessageBox.No, 
                                   QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
            
        # 获取索引目录
        default_index_path = str(Path.home() / "Documents" / "DocumentSearchIndex")
        index_dir = self.settings.value("indexing/indexDirectory", default_index_path)
        
        if not index_dir or not os.path.exists(index_dir):
            QMessageBox.warning(self, "错误", "索引目录不存在或未配置！")
            return
            
        # 构建日志文件路径
        log_file_path = os.path.join(index_dir, "index_skipped_files.tsv")
        
        try:
            # 清空文件，但保留表头 - 确保使用与读取时相同的字段名
            import csv
            with open(log_file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f, delimiter='\t')
                # 使用与_load_skipped_files方法中相同的表头字段
                writer.writerow(["文件路径", "跳过原因", "时间"])
                
            print(f"DEBUG: 已清空跳过文件记录，创建了新的TSV文件，表头: ['文件路径', '跳过原因', '时间']")
                
            # 清空内存中的记录并更新UI
            self.skipped_files = []
            self._apply_filter()
            QMessageBox.information(self, "已清空", "跳过文件记录已清空。")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"清空记录时出错: {e}")
            import traceback
            print(f"清空记录错误: {e}\n{traceback.format_exc()}")
    
    def showEvent(self, event):
        """窗口显示时仅调用父类方法并打印调试信息"""
        print("DEBUG: SkippedFilesDialog showEvent triggered.") # Simple debug message
        super().showEvent(event)
        # 不再在此处加载数据或清空表格，因为__init__和_update_ui会处理

    def closeEvent(self, event):
        """保存窗口大小并确保正确关闭"""
        try:
            self.settings.setValue("skippedFilesDialog/geometry", self.saveGeometry())
        except Exception as e:
            print(f"保存窗口几何信息时出错: {e}")
        
        # 确保关闭事件被接受
        event.accept()
        super().closeEvent(event)

    def _update_button_states(self):
        """根据当前选择状态更新按钮的启用状态"""
        has_selection = len(self.table.selectedItems()) > 0
        self.open_file_button.setEnabled(has_selection)
        self.open_folder_button.setEnabled(has_selection) 