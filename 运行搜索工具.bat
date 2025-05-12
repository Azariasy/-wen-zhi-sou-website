@echo off
REM 获取批处理文件所在的目录
set SCRIPT_DIR=%~dp0
REM 尝试从PATH中查找Python解释器
where python > nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_EXE=python
) else (
    REM 如果PATH中没有，尝试常见的安装位置
    if exist "C:\Python313\python.exe" (
        set PYTHON_EXE="C:\Python313\python.exe"
    ) else if exist "C:\Program Files\Python310\python.exe" (
        set PYTHON_EXE="C:\Program Files\Python310\python.exe"
    ) else if exist "C:\Program Files\Python311\python.exe" (
        set PYTHON_EXE="C:\Program Files\Python311\python.exe"
    ) else if exist "C:\Program Files\Python312\python.exe" (
        set PYTHON_EXE="C:\Program Files\Python312\python.exe"
    ) else if exist "C:\Program Files\Python313\python.exe" (
        set PYTHON_EXE="C:\Program Files\Python313\python.exe"
    ) else (
        echo 错误: 找不到Python解释器，请输入Python解释器的完整路径:
        set /p PYTHON_EXE=
        if not exist !PYTHON_EXE! (
            echo 错误: 指定的路径不存在
            pause
            exit /b 1
        )
    )
)

REM GUI 脚本的绝对路径
set GUI_SCRIPT="%SCRIPT_DIR%search_gui_pyside.py"

REM 检查 GUI 脚本是否存在
if not exist %GUI_SCRIPT% (
    echo 错误: 找不到 GUI 脚本 %GUI_SCRIPT%
    pause
    exit /b 1
)

REM 使用指定的 Python 解释器运行 GUI 脚本
echo 正在启动搜索工具...使用解释器: %PYTHON_EXE%
%PYTHON_EXE% %GUI_SCRIPT%

pause
exit /b 0