@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

title Suno AI Live Trending Monitor and Auto-Trainer

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

:: Check if user passed a bare number as first arg (e.g. auto_train.bat 10)
set "FIRST_ARG=%~1"
set "EXTRA_ARGS=%*"

:: If first argument is just a number, treat it as --recheck <number>
if not "%FIRST_ARG%"=="" (
    set "NOT_NUM="
    for /f "delims=0123456789" %%A in ("%FIRST_ARG%") do set "NOT_NUM=1"
    if not defined NOT_NUM (
        set "EXTRA_ARGS=--recheck %FIRST_ARG%"
    )
)

:: If no arguments provided, default to --recheck 30
if "%EXTRA_ARGS%"=="" set "EXTRA_ARGS=--recheck 30"

"%PYTHON_EXE%" -m src.auto_trainer %EXTRA_ARGS%

if "%NONINTERACTIVE%"=="" (
    echo.
    echo [i] Auto-trainer closed. Press any key to exit...
    pause >nul
)
endlocal
