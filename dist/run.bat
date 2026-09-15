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

:: If arguments were provided, pass them directly to the CLI
if not "%~1"=="" (
    "%PYTHON_EXE%" -m src.cli %*
) else (
    :: Default with no arguments: start interactive REPL with Wizard, Hit Generator, and Suno Integration
    "%PYTHON_EXE%" -m src.cli repl
)

endlocal
