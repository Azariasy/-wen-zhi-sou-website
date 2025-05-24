@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo 文智搜 - 创建桌面快捷方式
echo --------------------------------------------

set "SCRIPT_DIR=%~dp0"
set "DESKTOP_DIR=%USERPROFILE%\Desktop"

echo 正在创建桌面快捷方式...

REM 创建文智搜主程序快捷方式
echo 创建文智搜主程序快捷方式...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_DIR%\文智搜.lnk'); $Shortcut.TargetPath = '%SCRIPT_DIR%启动文智搜.bat'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.IconLocation = '%SCRIPT_DIR%app_icon.ico'; $Shortcut.Description = '文智搜 - 高级文档搜索工具'; $Shortcut.Save()"

REM 创建快速搜索快捷方式
echo 创建快速搜索快捷方式...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_DIR%\文智搜 - 快速搜索.lnk'); $Shortcut.TargetPath = '%SCRIPT_DIR%快速搜索.bat'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.IconLocation = '%SCRIPT_DIR%app_icon.ico'; $Shortcut.Description = '文智搜 - 轻量级搜索'; $Shortcut.Save()"

echo 桌面快捷方式创建完成！
echo.
echo 您现在可以通过以下方式启动文智搜:
echo 1. 双击桌面上的"文智搜"图标启动完整应用
echo 2. 双击桌面上的"文智搜 - 快速搜索"图标启动轻量级搜索
echo 3. 使用Alt+Space热键随时调出轻量级搜索窗口

echo 提示: 您可以在托盘菜单的"热键设置"中自定义热键

pause 