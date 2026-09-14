@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

:: Detect Python executable
set "PYTHON_EXE="
if exist "..\.venv\Scripts\python.exe" set "PYTHON_EXE=..\.venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
if not defined PYTHON_EXE (
    for %%P in (python.exe) do set "PYTHON_EXE=%%~$PATH:P"
)

if not defined PYTHON_EXE (
    echo [ERROR] Python not found! Please ensure Python or .venv is installed.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -m src.deploy %*

if "%~1"=="" (
    echo.
    echo Press any key to exit...
    pause >nul
)
endlocal
