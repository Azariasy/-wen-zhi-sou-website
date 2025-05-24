@echo off
REM 文智搜轻量级搜索启动脚本
REM 此批处理文件用于快速启动文智搜的轻量级搜索窗口

echo 正在启动文智搜轻量级搜索...

REM 检查是否提供了搜索参数
if "%~1"=="" (
    REM 无参数启动轻量级搜索
    start pythonw start_tray_fixed.py --quick-search
) else (
    REM 带参数启动轻量级搜索
    start pythonw start_tray_fixed.py --quick-search --search "%~1"
)

echo 已启动轻量级搜索窗口。
echo 提示：您可以使用Alt+Space热键随时调出轻量级搜索窗口。
timeout /t 3 > nul 