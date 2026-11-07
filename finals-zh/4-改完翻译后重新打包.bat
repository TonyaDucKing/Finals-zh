@echo off
cd /d "%~dp0"
set "EXE_ARG="
if not "%~1"=="" set "EXE_ARG=--exe "%~1""
set "PY=python"
%PY% -c "import sys" >nul 2>nul
if errorlevel 1 (
  py -3 -c "import sys" >nul 2>nul
  if not errorlevel 1 set "PY=py -3"
)
%PY% -c "import sys" >nul 2>nul
if errorlevel 1 goto :nopy
%PY% -c "import brotli" >nul 2>nul
if not errorlevel 1 goto :ready
echo Installing Python dependency: brotli ...
%PY% -m pip install --user --disable-pip-version-check brotli -i https://pypi.tuna.tsinghua.edu.cn/simple
%PY% -c "import brotli" >nul 2>nul
if not errorlevel 1 goto :ready
echo Retrying with Aliyun mirror ...
%PY% -m pip install --user --disable-pip-version-check brotli -i https://mirrors.aliyun.com/pypi/simple/
%PY% -c "import brotli" >nul 2>nul
if not errorlevel 1 goto :ready
echo Retrying with default PyPI ...
%PY% -m pip install --user brotli
%PY% -c "import brotli" >nul 2>nul
if not errorlevel 1 goto :ready
echo.
echo [!] brotli install failed. Python version:
%PY% --version
echo.
echo Manual command:
echo   %PY% -m pip install --user brotli -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.
pause
exit /b 1

:nopy
echo.
echo [!] Python 3 is not installed, or it is only the Microsoft Store alias.
echo Download Python 3.12 / 3.13 from https://www.python.org/downloads/
echo and tick "Add python.exe to PATH" during setup.
echo.
echo where python:
where python
echo.
pause
exit /b 1

:ready

echo Applying translations.csv and rebuilding...
echo Close finals-companion.zh.exe first if it is running.
%PY% apply_csv.py
%PY% tools\patch.py build %EXE_ARG%
echo.
pause
