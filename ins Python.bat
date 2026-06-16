@echo off
chcp 65001 >nul
title Python 3.13.2 自动安装脚本

echo ========================================
echo    Python 3.13.2 自动安装 (BFPL 所需)
echo ========================================
echo.

set "INSTALLER=python-3.13.2-amd64.exe"
set "DOWNLOAD_URL=https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe"

:: 检查是否已安装 Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [√] 系统中已检测到 Python，跳过安装。
    python --version
    goto :check_pip
)

:: 下载安装包
if not exist "%INSTALLER%" (
    echo [*] 正在下载 Python 3.13.2 ...
    curl -L -o "%INSTALLER%" "%DOWNLOAD_URL%"
    if %errorlevel% neq 0 (
        echo [×] 下载失败，请检查网络后重试。
        pause
        exit /b 1
    )
    echo [√] 下载完成。
) else (
    echo [√] 安装包已存在，跳过下载。
)

:: 静默安装 (为所有用户安装，添加到 PATH，不创建快捷方式)
echo [*] 正在安装 Python (可能需要几分钟)...
start /wait %INSTALLER% /quiet InstallAllUsers=1 PrependPath=1 Include_launcher=0

:: 刷新环境变量（使 PATH 立即生效）
call :RefreshEnv

:: 验证安装
:check_pip
python --version
if %errorlevel% neq 0 (
    echo [×] Python 安装失败，请手动安装。
    pause
    exit /b 1
)

echo [*] 检查 pip...
pip --version
if %errorlevel% neq 0 (
    echo [×] pip 不可用，尝试修复...
    python -m ensurepip --upgrade
)

echo.
echo ========================================
echo    Python 环境准备完成！
echo ========================================
echo.
echo 现在你可以使用 BFPL 了：
echo   1. 进入 bfpl.py 所在目录
echo   2. 运行: python bfpl.py 你的程序.bfpl
echo.
echo 也可以将 bfpl.py 所在目录加入 PATH 后直接调用。
echo.
pause
exit /b

:RefreshEnv
:: 临时刷新环境变量（简单处理，不处理 REG_EXPAND_SZ，建议用户重启终端）
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul ^| find "REG_"') do (
    set "SysPath=%%b"
)
if defined SysPath set "PATH=%SysPath%;%PATH%"
exit /b