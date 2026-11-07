@echo off
cd /d "%~dp0"
set "EXE_ARG="
if not "%~1"=="" set "EXE_ARG=--exe "%~1""
echo Applying translations.csv and rebuilding...
echo Close finals-companion.zh.exe first if it is running.
python apply_csv.py
python tools\patch.py build %EXE_ARG%
echo.
pause
