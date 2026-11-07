@echo off
cd /d "%~dp0"
set "EXE_ARG="
if not "%~1"=="" set "EXE_ARG=--exe "%~1""
python tools\patch.py restore %EXE_ARG%
echo.
pause
