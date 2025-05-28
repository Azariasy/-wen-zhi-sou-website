@echo off
chcp 65001 >nul
setlocal

:menu
cls
echo ===============================================
echo           文智搜 - 智能文档搜索工具
echo ===============================================
echo.
echo 请选择要启动的版本:
echo.
echo [1] 完整版 - 全功能界面
echo     • 完整的搜索和索引功能
echo     • 文件夹树视图
echo     • 高级设置和主题
echo     • 详细的搜索结果显示
echo.
echo [2] 托盘版 - 轻量级体验
echo     • 系统托盘集成
echo     • 全局热键支持
echo     • 轻量级快速搜索
echo     • 最小化到托盘
echo.
echo [3] 查看帮助信息
echo [4] 退出
echo.
echo ===============================================

set /p choice="请输入选择 (1-4): "

if "%choice%"=="1" goto :full_version
if "%choice%"=="2" goto :tray_version
if "%choice%"=="3" goto :help
if "%choice%"=="4" goto :exit
echo 无效选择，请重新输入...
timeout /t 2 >nul
goto :menu

:full_version
echo.
echo 正在启动完整版...
call "启动文智搜.bat"
goto :end

:tray_version
echo.
echo 正在启动托盘版...
call "运行搜索工具.bat"
goto :end

:help
cls
echo ===============================================
echo                   帮助信息
echo ===============================================
echo.
echo 完整版特点:
echo • 传统桌面应用界面
echo • 完整的文档搜索和索引功能
echo • 支持文件夹树视图
echo • 多种主题和高级设置
echo • 适合需要完整功能的用户
echo.
echo 托盘版特点:
echo • 最小化到系统托盘
echo • 支持全局热键 (双击Ctrl, Ctrl+Alt+Q)
echo • 轻量级快速搜索窗口
echo • 右键菜单快速操作
echo • 适合需要快速访问的用户
echo.
echo 推荐使用:
echo • 日常办公: 选择托盘版
echo • 深度搜索: 选择完整版
echo • 首次使用: 建议先试用完整版
echo.
echo ===============================================
echo.
pause
goto :menu

:exit
echo 感谢使用文智搜！
exit /b 0

:end
echo.
echo 程序已退出，按任意键返回菜单...
pause >nul
goto :menu 