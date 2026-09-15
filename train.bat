@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

:: Detect Python executable
set "PYTHON_EXE="
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "..\.venv\Scripts\python.exe" set "PYTHON_EXE=..\.venv\Scripts\python.exe"
if not defined PYTHON_EXE (
    for %%P in (python.exe) do set "PYTHON_EXE=%%~$PATH:P"
)

if not defined PYTHON_EXE (
    echo [ERROR] Python not found! Please install Python 3.10+ or set up a virtual environment.
    pause
    exit /b 1
)

:: If arguments were provided, pass them to trainer
if not "%~1"=="" (
    "%PYTHON_EXE%" -m src.trainer %*
) else (
    :: Default with no arguments: auto-train from live Suno.com trending songs and update catalog & corpus
    echo ======================================================================
    echo   SUNO AUTO-TRAINER: FETCHING LIVE SUNO.COM TRENDING & RETRAINING...
    echo ======================================================================
    "%PYTHON_EXE%" -m src.trainer trending
)

endlocal
