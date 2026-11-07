@echo off
cd /d "%~dp0"
set "EXE_ARG="
if not "%~1"=="" set "EXE_ARG=--exe "%~1""
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3 not found. Install Python 3 from python.org and tick "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)
python -c "import brotli" >nul 2>nul
if errorlevel 1 (
  echo Installing Python dependency: brotli ...
  python -m pip install brotli
  if errorlevel 1 (
    echo Failed to install brotli. Check your network or run: python -m pip install brotli
    echo.
    pause
    exit /b 1
  )
)

python tools\patch.py restore %EXE_ARG%
echo.
pause
