# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['search_gui_pyside.py'],
    pathex=[],
    binaries=[],
    datas=[
        # QSS 主题样式文件
        ('blue_style.qss', '.'),
        ('green_style.qss', '.'),
        ('purple_style.qss', '.'),
        
        # 图标文件 - 通用图标
        ('checkmark.png', '.'),
        ('down_arrow.png', '.'),

        # 蓝色主题图标
        ('checkmark_blue.png', '.'),
        ('down_arrow_blue.png', '.'),
        ('radio_checked_blue.png', '.'),
        
        # 绿色主题图标
        ('checkmark_green.png', '.'),
        ('down_arrow_green.png', '.'), 
        ('radio_checked_green.png', '.'),
        
        # 紫色主题图标
        ('checkmark_purple.png', '.'),
        ('down_arrow_purple.png', '.'),
        ('radio_checked_purple.png', '.'),
        
        # 更新检查相关文件
        ('docs/latest_version.json', 'docs'),
        
        # 其他必要的配置和资源文件
        ('requirements.txt', '.'),
        ('license_activation.py', '.'),
        ('generate_device_id.py', '.'),
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
    [],
    exclude_binaries=True,
    name='文智搜',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 应用程序图标，如果有的话可以取消注释此行
    # icon='app_icon.ico',
    version='file_version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='文智搜',
)
