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
  python -m pip install --user --disable-pip-version-check brotli -i https://pypi.tuna.tsinghua.edu.cn/simple
  python -c "import brotli" >nul 2>nul
  if errorlevel 1 (
    echo Retrying with Aliyun mirror ...
    python -m pip install --user --disable-pip-version-check brotli -i https://mirrors.aliyun.com/pypi/simple/
  )
  python -c "import brotli" >nul 2>nul
  if errorlevel 1 (
    echo Retrying with default PyPI ...
    python -m pip install --user brotli
  )
  python -c "import brotli" >nul 2>nul
  if errorlevel 1 (
    echo.
    echo [!] brotli install failed. Python version:
    python --version
    echo.
    echo Try manually in cmd:
    echo   python -m pip install --user brotli -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo If it still fails, install Python 3.12 instead of a newer version.
    echo.
    pause
    exit /b 1
  )
)

echo Looking for Finals.id Companion App ...
python tools\patch.py build %EXE_ARG%
echo.
pause
