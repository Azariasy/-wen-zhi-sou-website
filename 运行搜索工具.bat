@echo off
chcp 65001 >nul
setlocal

echo 文智搜 - 智能文档搜索工具 (托盘版)
echo 支持托盘功能、全局热键和轻量级搜索
echo --------------------------------------------

set "SCRIPT_DIR=%~dp0"
set "MAIN_SCRIPT=%SCRIPT_DIR%文智搜.py"

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
if not exist "%MAIN_SCRIPT%" (
    echo 错误: 找不到主程序文件 "%MAIN_SCRIPT%"
    pause
    exit /b 1
)

REM 参数处理
if "%~1"=="--help" (
    echo 使用说明:
    echo   运行搜索工具.bat [选项] [搜索关键词]
    echo.
    echo 选项:
    echo   --minimized, -m    最小化到托盘启动
    echo   --search "关键词"  启动后立即搜索
    echo   --quick-search     显示轻量级搜索窗口
    echo   --help             显示此帮助信息
    echo.
    echo 热键功能:
    echo   双击Ctrl          快速召唤主搜索窗口
    echo   Ctrl+Alt+Q        显示轻量级搜索窗口
    echo.
    echo 托盘功能:
    echo   - 最小化到系统托盘
    echo   - 右键菜单快速操作
    echo   - 最近搜索历史
    echo   - 全局热键支持
    echo.
    pause
    exit /b 0
)

echo 正在启动文智搜托盘版...
%PYTHON_CMD% "%MAIN_SCRIPT%" %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo 程序异常退出，错误代码: %ERRORLEVEL%
    pause
)

exit /b %ERRORLEVEL% 