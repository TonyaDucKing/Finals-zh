@echo off
cd /d "%~dp0"
echo Backing up the original exe, then installing the Chinese build...
python tools\patch.py install
echo.
pause
