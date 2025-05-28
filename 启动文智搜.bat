@echo off
chcp 65001 >nul
setlocal

echo 文智搜 - 智能文档搜索工具 (完整版)
echo 支持全功能搜索、索引管理和高级设置
echo --------------------------------------------

set "SCRIPT_DIR=%~dp0"
set "MAIN_SCRIPT=%SCRIPT_DIR%search_gui_pyside.py"

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
    echo   启动文智搜.bat [选项]
    echo.
    echo 选项:
    echo   --help             显示此帮助信息
    echo.
    echo 功能特点:
    echo   - 完整的文档搜索功能
    echo   - 高级索引管理
    echo   - 文件夹树视图
    echo   - 多种主题支持
    echo   - 详细的搜索结果
    echo.
    pause
    exit /b 0
)

echo 正在启动文智搜完整版...
%PYTHON_CMD% "%MAIN_SCRIPT%" %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo 程序异常退出，错误代码: %ERRORLEVEL%
    pause
)

exit /b %ERRORLEVEL% 