#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI优化设置界面
提供用户友好的索引优化参数配置
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QLabel, QSpinBox, QCheckBox, QComboBox, QPushButton, 
    QDialogButtonBox, QSlider, QProgressBar, QTextEdit,
    QTabWidget, QWidget, QFormLayout, QFrame
)
from PySide6.QtCore import Qt, QSettings, Signal, QTimer
from PySide6.QtGui import QFont

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class OptimizationSettingsDialog(QDialog):
    """索引优化设置对话框"""
    
    # 信号：当设置改变时发出
    settingsChanged = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("索引优化设置")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        # 设置对象
        self.settings = QSettings("YourOrganizationName", "DocumentSearchToolPySide")
        
        # 创建UI
        self._create_ui()
        
        # 加载当前设置
        self._load_settings()
        
        # 连接信号
        self._connect_signals()
    
    def _create_ui(self):
        """创建用户界面"""
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # 基础优化选项卡
        basic_tab = self._create_basic_tab()
        tab_widget.addTab(basic_tab, "基础优化")
        
        # 高级优化选项卡
        advanced_tab = self._create_advanced_tab()
        tab_widget.addTab(advanced_tab, "高级优化")
        
        # 性能监控选项卡
        monitoring_tab = self._create_monitoring_tab()
        tab_widget.addTab(monitoring_tab, "性能监控")
        
        layout.addWidget(tab_widget)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings)
        
        layout.addWidget(button_box)
    
    def _create_basic_tab(self):
        """创建基础优化选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 多进程设置组
        multiprocess_group = QGroupBox("多进程设置")
        multiprocess_layout = QFormLayout(multiprocess_group)
        
        # 工作进程数
        self.max_workers_combo = QComboBox()
        self.max_workers_combo.addItems([
            "自动检测（推荐）", "1个进程", "2个进程", "4个进程", 
            "8个进程", "12个进程", "16个进程"
        ])
        self.max_workers_combo.setToolTip("设置用于索引的工作进程数。自动检测会根据CPU核心数优化配置。")
        multiprocess_layout.addRow("工作进程数:", self.max_workers_combo)
        
        layout.addWidget(multiprocess_group)
        
        # 文件过滤设置组
        filter_group = QGroupBox("文件过滤设置")
        filter_layout = QFormLayout(filter_group)
        
        # 最大文件大小
        self.max_file_size_spinbox = QSpinBox()
        self.max_file_size_spinbox.setRange(1, 1000)
        self.max_file_size_spinbox.setValue(100)
        self.max_file_size_spinbox.setSuffix(" MB")
        self.max_file_size_spinbox.setToolTip("跳过超过此大小的文件以避免处理时间过长")
        filter_layout.addRow("最大文件大小:", self.max_file_size_spinbox)
        
        # 跳过系统文件
        self.skip_system_files_checkbox = QCheckBox("跳过系统文件和临时文件")
        self.skip_system_files_checkbox.setChecked(True)
        self.skip_system_files_checkbox.setToolTip("自动跳过系统文件、临时文件和隐藏文件")
        filter_layout.addRow("", self.skip_system_files_checkbox)
        
        layout.addWidget(filter_group)
        
        # 索引策略设置组
        strategy_group = QGroupBox("索引策略")
        strategy_layout = QFormLayout(strategy_group)
        
        # 启用增量索引
        self.incremental_checkbox = QCheckBox("启用增量索引")
        self.incremental_checkbox.setChecked(True)
        self.incremental_checkbox.setToolTip("只处理新增或修改的文件，大幅提升重复索引的速度")
        strategy_layout.addRow("", self.incremental_checkbox)
        
        # 内容大小限制
        self.content_limit_spinbox = QSpinBox()
        self.content_limit_spinbox.setRange(0, 10240)
        self.content_limit_spinbox.setValue(1024)
        self.content_limit_spinbox.setSuffix(" KB")
        self.content_limit_spinbox.setSpecialValueText("无限制")
        self.content_limit_spinbox.setToolTip("限制索引的文件内容大小，0表示无限制")
        strategy_layout.addRow("内容大小限制:", self.content_limit_spinbox)
        
        layout.addWidget(strategy_group)
        
        layout.addStretch()
        return tab
    
    def _create_advanced_tab(self):
        """创建高级优化选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 超时设置组
        timeout_group = QGroupBox("超时设置")
        timeout_layout = QFormLayout(timeout_group)
        
        # 提取超时
        self.extraction_timeout_spinbox = QSpinBox()
        self.extraction_timeout_spinbox.setRange(30, 600)
        self.extraction_timeout_spinbox.setValue(300)
        self.extraction_timeout_spinbox.setSuffix(" 秒")
        self.extraction_timeout_spinbox.setToolTip("单个文件内容提取的最大等待时间")
        timeout_layout.addRow("文件提取超时:", self.extraction_timeout_spinbox)
        
        layout.addWidget(timeout_group)
        
        # PDF优化设置组
        pdf_group = QGroupBox("PDF优化设置")
        pdf_layout = QFormLayout(pdf_group)
        
        # 动态OCR超时
        self.dynamic_ocr_timeout_checkbox = QCheckBox("启用动态OCR超时")
        self.dynamic_ocr_timeout_checkbox.setChecked(True)
        self.dynamic_ocr_timeout_checkbox.setToolTip("根据PDF文件大小自动调整OCR超时时间")
        pdf_layout.addRow("", self.dynamic_ocr_timeout_checkbox)
        
        # OCR超时说明
        ocr_info_label = QLabel(
            "动态OCR超时规则：\n"
            "• 小于5MB: 60秒\n"
            "• 5-20MB: 180秒\n"
            "• 20-50MB: 300秒\n"
            "• 大于50MB: 使用默认超时"
        )
        ocr_info_label.setStyleSheet("color: #666; font-size: 10px;")
        pdf_layout.addRow("", ocr_info_label)
        
        layout.addWidget(pdf_group)
        
        # 内存优化设置组
        memory_group = QGroupBox("内存优化")
        memory_layout = QFormLayout(memory_group)
        
        # 批处理大小
        self.batch_size_spinbox = QSpinBox()
        self.batch_size_spinbox.setRange(10, 1000)
        self.batch_size_spinbox.setValue(100)
        self.batch_size_spinbox.setToolTip("每批处理的文件数量，较小的值使用更少内存")
        memory_layout.addRow("批处理大小:", self.batch_size_spinbox)
        
        layout.addWidget(memory_group)
        
        layout.addStretch()
        return tab
    
    def _create_monitoring_tab(self):
        """创建性能监控选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 实时监控设置组
        monitoring_group = QGroupBox("实时监控")
        monitoring_layout = QFormLayout(monitoring_group)
        
        # 显示详细进度
        self.show_detailed_progress_checkbox = QCheckBox("显示详细进度信息")
        self.show_detailed_progress_checkbox.setChecked(True)
        self.show_detailed_progress_checkbox.setToolTip("在索引过程中显示当前处理的文件名和详细状态")
        monitoring_layout.addRow("", self.show_detailed_progress_checkbox)
        
        # 显示性能指标
        self.show_performance_metrics_checkbox = QCheckBox("显示性能指标")
        self.show_performance_metrics_checkbox.setChecked(True)
        self.show_performance_metrics_checkbox.setToolTip("显示处理速度、文件数量等性能指标")
        monitoring_layout.addRow("", self.show_performance_metrics_checkbox)
        
        # 进度更新频率
        self.progress_update_frequency_spinbox = QSpinBox()
        self.progress_update_frequency_spinbox.setRange(1, 10)
        self.progress_update_frequency_spinbox.setValue(5)
        self.progress_update_frequency_spinbox.setToolTip("每处理多少个文件更新一次进度")
        monitoring_layout.addRow("进度更新频率:", self.progress_update_frequency_spinbox)
        
        layout.addWidget(monitoring_group)
        
        # 性能预测组
        prediction_group = QGroupBox("性能预测")
        prediction_layout = QFormLayout(prediction_group)
        
        # 启用时间估算
        self.enable_time_estimation_checkbox = QCheckBox("启用处理时间估算")
        self.enable_time_estimation_checkbox.setChecked(True)
        self.enable_time_estimation_checkbox.setToolTip("在开始索引前估算所需时间")
        prediction_layout.addRow("", self.enable_time_estimation_checkbox)
        
        layout.addWidget(prediction_group)
        
        # 当前系统信息组
        system_info_group = QGroupBox("系统信息")
        system_info_layout = QVBoxLayout(system_info_group)
        
        # 获取系统信息
        try:
            import document_search
            io_workers = document_search.get_optimal_worker_count("io_intensive")
            cpu_workers = document_search.get_optimal_worker_count("cpu_intensive")
            
            system_info_text = f"""
当前系统配置：
• 推荐I/O密集型工作进程数: {io_workers}
• 推荐CPU密集型工作进程数: {cpu_workers}
• 系统平台: {sys.platform}
• Python版本: {sys.version.split()[0]}
            """.strip()
        except Exception as e:
            system_info_text = f"无法获取系统信息: {e}"
        
        system_info_label = QLabel(system_info_text)
        system_info_label.setStyleSheet("font-family: monospace; background: #f5f5f5; padding: 10px;")
        system_info_layout.addWidget(system_info_label)
        
        layout.addWidget(system_info_group)
        
        layout.addStretch()
        return tab
    
    def _connect_signals(self):
        """连接信号"""
        # 当任何设置改变时，启用应用按钮
        self.max_workers_combo.currentTextChanged.connect(self._on_settings_changed)
        self.max_file_size_spinbox.valueChanged.connect(self._on_settings_changed)
        self.skip_system_files_checkbox.toggled.connect(self._on_settings_changed)
        self.incremental_checkbox.toggled.connect(self._on_settings_changed)
        self.content_limit_spinbox.valueChanged.connect(self._on_settings_changed)
        self.extraction_timeout_spinbox.valueChanged.connect(self._on_settings_changed)
        self.dynamic_ocr_timeout_checkbox.toggled.connect(self._on_settings_changed)
        self.batch_size_spinbox.valueChanged.connect(self._on_settings_changed)
        self.show_detailed_progress_checkbox.toggled.connect(self._on_settings_changed)
        self.show_performance_metrics_checkbox.toggled.connect(self._on_settings_changed)
        self.progress_update_frequency_spinbox.valueChanged.connect(self._on_settings_changed)
        self.enable_time_estimation_checkbox.toggled.connect(self._on_settings_changed)
    
    def _on_settings_changed(self):
        """当设置改变时调用"""
        # 这里可以添加实时预览或验证逻辑
        pass
    
    def _load_settings(self):
        """加载当前设置"""
        # 加载多进程设置
        max_workers = self.settings.value("optimization/max_workers", "auto")
        if max_workers == "auto":
            self.max_workers_combo.setCurrentIndex(0)
        else:
            try:
                workers_map = {"1": 1, "2": 2, "4": 3, "8": 4, "12": 5, "16": 6}
                index = workers_map.get(str(max_workers), 0)
                self.max_workers_combo.setCurrentIndex(index)
            except:
                self.max_workers_combo.setCurrentIndex(0)
        
        # 加载文件过滤设置
        self.max_file_size_spinbox.setValue(
            int(self.settings.value("optimization/max_file_size_mb", 100))
        )
        self.skip_system_files_checkbox.setChecked(
            self.settings.value("optimization/skip_system_files", True, type=bool)
        )
        
        # 加载索引策略设置
        self.incremental_checkbox.setChecked(
            self.settings.value("optimization/incremental", True, type=bool)
        )
        self.content_limit_spinbox.setValue(
            int(self.settings.value("optimization/content_limit_kb", 1024))
        )
        
        # 加载高级设置
        self.extraction_timeout_spinbox.setValue(
            int(self.settings.value("optimization/extraction_timeout", 300))
        )
        self.dynamic_ocr_timeout_checkbox.setChecked(
            self.settings.value("optimization/dynamic_ocr_timeout", True, type=bool)
        )
        self.batch_size_spinbox.setValue(
            int(self.settings.value("optimization/batch_size", 100))
        )
        
        # 加载监控设置
        self.show_detailed_progress_checkbox.setChecked(
            self.settings.value("optimization/show_detailed_progress", True, type=bool)
        )
        self.show_performance_metrics_checkbox.setChecked(
            self.settings.value("optimization/show_performance_metrics", True, type=bool)
        )
        self.progress_update_frequency_spinbox.setValue(
            int(self.settings.value("optimization/progress_update_frequency", 5))
        )
        self.enable_time_estimation_checkbox.setChecked(
            self.settings.value("optimization/enable_time_estimation", True, type=bool)
        )
    
    def _apply_settings(self):
        """应用设置"""
        # 获取当前设置
        settings_dict = self._get_current_settings()
        
        # 保存到QSettings
        for key, value in settings_dict.items():
            self.settings.setValue(f"optimization/{key}", value)
        
        # 发出设置改变信号
        self.settingsChanged.emit(settings_dict)
        
        print("优化设置已保存:", settings_dict)
    
    def _get_current_settings(self):
        """获取当前设置"""
        # 解析工作进程数
        workers_text = self.max_workers_combo.currentText()
        if "自动" in workers_text:
            max_workers = "auto"
        else:
            try:
                max_workers = int(workers_text.split("个")[0])
            except:
                max_workers = "auto"
        
        return {
            "max_workers": max_workers,
            "max_file_size_mb": self.max_file_size_spinbox.value(),
            "skip_system_files": self.skip_system_files_checkbox.isChecked(),
            "incremental": self.incremental_checkbox.isChecked(),
            "content_limit_kb": self.content_limit_spinbox.value(),
            "extraction_timeout": self.extraction_timeout_spinbox.value(),
            "dynamic_ocr_timeout": self.dynamic_ocr_timeout_checkbox.isChecked(),
            "batch_size": self.batch_size_spinbox.value(),
            "show_detailed_progress": self.show_detailed_progress_checkbox.isChecked(),
            "show_performance_metrics": self.show_performance_metrics_checkbox.isChecked(),
            "progress_update_frequency": self.progress_update_frequency_spinbox.value(),
            "enable_time_estimation": self.enable_time_estimation_checkbox.isChecked(),
        }
    
    def accept(self):
        """确定按钮被点击"""
        self._apply_settings()
        super().accept()
    
    def get_optimization_parameters(self):
        """获取用于索引函数的优化参数"""
        settings = self._get_current_settings()
        
        # 转换为索引函数需要的参数格式
        max_workers = None if settings["max_workers"] == "auto" else settings["max_workers"]
        
        return {
            "max_file_size_mb": settings["max_file_size_mb"],
            "skip_system_files": settings["skip_system_files"],
            "incremental": settings["incremental"],
            "content_limit_kb": settings["content_limit_kb"],
            "extraction_timeout": settings["extraction_timeout"],
            "max_workers": max_workers
        }


def main():
    """测试函数"""
    app = QApplication(sys.argv)
    
    dialog = OptimizationSettingsDialog()
    
    def on_settings_changed(settings):
        print("设置已改变:", settings)
        print("索引参数:", dialog.get_optimization_parameters())
    
    dialog.settingsChanged.connect(on_settings_changed)
    
    result = dialog.exec()
    
    if result == QDialog.Accepted:
        print("用户确认了设置")
        print("最终参数:", dialog.get_optimization_parameters())
    else:
        print("用户取消了设置")
    
    sys.exit(0)


if __name__ == "__main__":
    main() 