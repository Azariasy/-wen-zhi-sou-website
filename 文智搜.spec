# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['文智搜.py'],
    pathex=[],
    binaries=[],
    datas=[
        # QSS 主题样式文件 - 只保留4个现代化主题
        ('blue_style.qss', '.'),
        ('red_style.qss', '.'),
        ('purple_style.qss', '.'),
        ('orange_style.qss', '.'),
        
        # 图标文件 - 通用图标
        ('checkmark.png', '.'),
        ('down_arrow.png', '.'),
        ('app_icon.ico', '.'),
        ('app_icon.png', '.'),
        ('app_icon_16.png', '.'),
        ('app_icon_32.png', '.'),

        # 蓝色主题图标
        ('checkmark_blue.png', '.'),
        ('radio_checked_blue.png', '.'),
        ('down_arrow_blue.png', '.'),
        
        # 红色主题图标
        ('checkmark_red.png', '.'),
        ('radio_checked_red.png', '.'),
        ('down_arrow_red.png', '.'),
        
        # 紫色主题图标
        ('checkmark_purple.png', '.'),
        ('radio_checked_purple.png', '.'),
        ('down_arrow_purple.png', '.'),
        
        # 橙色主题图标
        ('checkmark_orange.png', '.'),
        ('radio_checked_orange.png', '.'),
        ('down_arrow_orange.png', '.'),
        
        # 文件类型图标目录
        ('file_icons/', 'file_icons/'),
        
        # 更新检查相关文件
        ('docs/latest_version.json', 'docs'),
        
        # 其他必要的配置和资源文件
        ('requirements.txt', '.'),
        ('license_activation.py', '.'),
        ('generate_device_id.py', '.'),
        ('device_manager_dialog.py', '.'),
        ('license_manager.py', '.'),
        ('file_version_info.txt', '.'),
        ('main_window_tray.py', '.'),
        ('tray_app.py', '.'),
        ('hotkey_manager.py', '.'),
        ('hotkey_settings.py', '.'),
        ('startup_settings.py', '.'),
        ('dynamic_tray_menu.py', '.'),
        ('quick_search_dialog.py', '.'),
        ('quick_search_controller.py', '.'),
        ('quick_filename_search.py', '.'),
        ('theme_manager.py', '.'),
        ('tray_settings.py', '.'),
        ('gui_optimization_settings.py', '.'),
        ('path_utils.py', '.'),
        ('file_processing_utils.py', '.'),
        ('single_instance.py', '.'),
        ('main_tray.py', '.'),
        ('document_search.py', '.'),
        ('search_gui_pyside.py', '.'),
    ],
    hiddenimports=[
        # 中文分词
        'jieba',
        
        # 图像处理
        'PIL',
        'pytesseract',
        'pdf2image',
        'PyPDF2',
        'fitz', # PyMuPDF
        
        # 文件解析相关
        'docx',
        'pptx',
        'openpyxl',
        'markdown',
        'bs4',
        'striprtf',
        'email',
        'chardet',
        'extract_msg',
        'lxml',
        
        # 搜索引擎
        'whoosh',
        'whoosh.fields',
        'whoosh.qparser',
        'whoosh.index',
        'whoosh.writing',
        'whoosh.filedb.filestore',
        
        # 数据处理
        'pandas',
        'csv',
        'packaging',
        'packaging.version',
        
        # 网络相关
        'requests',
        'urllib3',
        
        # PySide6 相关模块
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        'PySide6.QtUiTools',
        
        # 热键和系统相关
        'keyboard',
        'psutil',
        'subprocess',  # 单实例检查需要
        'tempfile',    # 单实例检查需要
        'atexit',      # 单实例检查需要
        
        # 应用程序模块
        'main_window_tray',
        'main_tray',
        'tray_app',
        'hotkey_manager',
        'quick_search_dialog',
        'quick_search_controller',
        'theme_manager',
        'single_instance',
        'document_search',
        'search_gui_pyside',  # 确保主界面模块被包含
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 添加版本信息
a.datas += [('version.txt', 'version.txt', 'DATA')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,      # 添加所有二进制文件到exe
    a.zipfiles,      # 添加所有zip文件到exe
    a.datas,         # 添加所有数据文件到exe
    [],
    name='文智搜',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 应用程序图标
    icon='app_icon.ico',
    version='file_version_info.txt',
)
# COLLECT部分已移除，不再创建文件夹，直接生成单个exe文件
