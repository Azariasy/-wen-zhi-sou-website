@echo off
chcp 65001 >nul
setlocal

echo 文智搜 - 高级文档搜索工具
echo 支持托盘功能和全局热键
echo - 双击Ctrl: 快速召唤主窗口
echo - Alt+Space: 轻量级搜索窗口
echo --------------------------------------------

set "SCRIPT_DIR=%~dp0"
set "TRAY_SCRIPT=%SCRIPT_DIR%start_tray_fixed.py"

REM 检查Python是否在PATH中
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_CMD=python"
) else (
    echo 错误: 找不到Python解释器
    echo 请确保Python已安装并添加到PATH环境变量中
    pause
    exit /b 1
)

REM 检查脚本是否存在
if not exist "%TRAY_SCRIPT%" (
    echo 错误: 找不到托盘启动脚本
    pause
    exit /b 1
)

REM 简化的参数处理
if "%~1"=="--help" (
    echo 使用说明:
    echo   启动文智搜.bat [选项]
    echo.
    echo 选项:
    echo   --minimized       最小化到托盘启动
    echo   --quick-search    启动轻量级搜索窗口
    echo   --help            显示此帮助信息
    echo.
    echo 热键功能:
    echo   双击Ctrl         快速召唤主窗口
    echo   Alt+Space        打开轻量级搜索窗口
    exit /b 0
)

echo 正在启动文智搜...

REM 直接启动，不处理复杂参数
if "%~1"=="--quick-search" (
    echo 启动模式: 轻量级搜索
    %PYTHON_CMD% "%TRAY_SCRIPT%" --quick-search
) else if "%~1"=="--minimized" (
    echo 启动模式: 最小化到托盘
    %PYTHON_CMD% "%TRAY_SCRIPT%" --minimized
) else (
    echo 启动模式: 正常启动
    %PYTHON_CMD% "%TRAY_SCRIPT%"
)

exit /b %ERRORLEVEL% 