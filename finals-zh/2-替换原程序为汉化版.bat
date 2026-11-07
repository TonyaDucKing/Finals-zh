@echo off
cd /d "%~dp0"
set "EXE_ARG="
if not "%~1"=="" set "EXE_ARG=--exe "%~1""
echo Looking for Finals.id Companion App ...
python tools\patch.py install %EXE_ARG%
echo.
pause
