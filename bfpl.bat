@echo off
chcp 936 >nul 2>&1
setlocal enabledelayedexpansion

:: 帮助信息
:help
echo BFPL 模拟器 - Brainfuck Pointer Language
echo.
echo 用法: bfpl.cmd ^<源文件.bfpl^> [-d]
echo   -d    启用调试模式（逐条显示指令执行）
echo.
echo 示例:
echo   bfpl.cmd hello.bfpl
echo   bfpl.cmd factorial.bfpl -d
echo.
echo 直接输入 bfpl.cmd /HELP 显示本帮助
exit /b 0

:: 无参数或请求帮助
if "%~1"=="" goto help
if /i "%~1"=="/HELP" goto help
if /i "%~1"=="/h" goto help
if /i "%~1"=="-h" goto help

:: 获取源文件路径
set "source=%~1"
if not exist "%source%" (
    echo 错误: 文件不存在 "%source%"
    exit /b 1
)

:: 查找 Python
set "python_cmd=python"
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到 python，请确保 Python 已安装并加入 PATH
    exit /b 1
)

:: 处理调试参数
set "debug_flag="
if /i "%~2"=="-d" set "debug_flag=-d"
if /i "%~3"=="-d" set "debug_flag=-d"

:: 运行模拟器（假设 bfpl.py 与脚本在同一目录）
set "script_dir=%~dp0"
%python_cmd% "%script_dir%bfpl.py" "%source%" %debug_flag%
exit /b %errorlevel%