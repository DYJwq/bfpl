@echo off
if "%~1"=="HELP" (
    type %~dp0readme.md
)
if "%~1"=="CODE" (
    type %~dp0bfpl.py
    rem 这样就能输出代码了
)
if "%~1"=="RUN" (
    py bfpl.py %~2 -d
    rem 这样就能运行bfpl的代码
)