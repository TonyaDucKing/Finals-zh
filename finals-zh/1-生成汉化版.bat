@echo off
cd /d "%~dp0"
echo Generating finals-companion.zh.exe from the official build...
python tools\patch.py build
echo.
pause
