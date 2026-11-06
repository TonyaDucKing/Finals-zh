@echo off
cd /d "%~dp0"
echo Applying translations.csv and rebuilding...
echo Close finals-companion.zh.exe first if it is running.
python apply_csv.py
python tools\patch.py build
echo.
pause
