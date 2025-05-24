@echo off
chcp 65001 >nul
setlocal

echo 文智搜 - 高级文档搜索工具
echo 支持托盘功能和全局热键(双击Ctrl快速召唤)
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
    echo 错误: 找不到托盘启动脚本 "%TRAY_SCRIPT%"
    pause
    exit /b 1
)

REM 参数处理
if "%~1"=="--help" (
    echo 使用说明:
    echo   启动文智搜.bat [选项] [搜索关键词]
    echo.
    echo 选项:
    echo   --minimized, -m    最小化到托盘启动
    echo   --search "关键词"  启动后立即搜索
    echo   --help             显示此帮助信息
    echo.
    echo 热键功能:
    echo   双击Ctrl          快速召唤搜索窗口
    exit /b 0
)

set MINIMIZED=
set SEARCH=

:parse
if "%~1"=="" goto :endparse
if "%~1"=="--minimized" set "MINIMIZED=--minimized" & goto :nextarg
if "%~1"=="-m" set "MINIMIZED=--minimized" & goto :nextarg
if "%~1"=="--search" (
    if not "%~2"=="" (
        set "SEARCH=--search "%~2""
        shift
    )
    goto :nextarg
)
if not "%SEARCH%"=="" goto :nextarg
set "SEARCH=--search "%~1""

:nextarg
shift
goto :parse

:endparse
set "CMD_ARGS=%MINIMIZED% %SEARCH%"
echo 正在启动文智搜...
echo 启动参数: %CMD_ARGS%

%PYTHON_CMD% "%TRAY_SCRIPT%" %CMD_ARGS%

exit /b %ERRORLEVEL% 