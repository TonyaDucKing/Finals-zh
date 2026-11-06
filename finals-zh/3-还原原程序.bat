@echo off
cd /d "%~dp0"
echo Restoring the original exe from finals-companion.exe.bak ...
python tools\patch.py restore
echo.
pause
