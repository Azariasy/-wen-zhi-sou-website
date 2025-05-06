@echo off
REM 获取批处理文件所在的目录
set SCRIPT_DIR=%~dp0
REM Python 解释器的绝对路径 (根据您的设置)
set PYTHON_EXE="C:\Python313\python.exe"
REM GUI 脚本的绝对路径
set GUI_SCRIPT="%SCRIPT_DIR%search_gui_pyside.py"

REM 检查 Python 解释器是否存在
if not exist %PYTHON_EXE% (
    echo 错误: 找不到 Python 解释器 %PYTHON_EXE%
    pause
    exit /b 1
)

REM 检查 GUI 脚本是否存在
if not exist %GUI_SCRIPT% (
    echo 错误: 找不到 GUI 脚本 %GUI_SCRIPT%
    pause
    exit /b 1
)

REM 使用指定的 Python 解释器运行 GUI 脚本
echo 正在启动搜索工具...
REM start "" %PYTHON_EXE% %GUI_SCRIPT%
%PYTHON_EXE% %GUI_SCRIPT% REM 直接运行，以便在当前窗口看到错误

pause REM 添加 pause 以便查看错误
exit /b 0