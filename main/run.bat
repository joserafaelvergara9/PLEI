@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python 3.10 or newer from https://www.python.org and tick "Add Python to PATH".
    pause
    exit /b 1
)
python -c "import matplotlib" >nul 2>nul
if errorlevel 1 (
    echo Installing the charting library ^(matplotlib^), one time only...
    python -m pip install matplotlib
)
python cli_app.py
if errorlevel 1 pause
endlocal