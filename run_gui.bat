@echo off
REM 尝试从PATH中查找Python解释器
where python > nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo 使用系统PATH中的Python解释器
    python search_gui_pyside.py
) else (
    REM 如果PATH中没有，尝试常见的安装位置
    if exist "C:\Python313\python.exe" (
        "C:\Python313\python.exe" search_gui_pyside.py
    ) else if exist "C:\Program Files\Python310\python.exe" (
        "C:\Program Files\Python310\python.exe" search_gui_pyside.py
    ) else if exist "C:\Program Files\Python311\python.exe" (
        "C:\Program Files\Python311\python.exe" search_gui_pyside.py
    ) else if exist "C:\Program Files\Python312\python.exe" (
        "C:\Program Files\Python312\python.exe" search_gui_pyside.py
    ) else if exist "C:\Program Files\Python313\python.exe" (
        "C:\Program Files\Python313\python.exe" search_gui_pyside.py
    ) else (
        echo 错误: 找不到Python解释器，请安装Python或确保其在PATH中
    )
)
pause 