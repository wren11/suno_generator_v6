@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0\.."

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

:: If arguments provided, pass to CLI; else launch REPL
if not "%~1"=="" (
    "%PYTHON_EXE%" -m src.cli %*
) else (
    "%PYTHON_EXE%" -m src.repl --catalog dist/models/suno_song_catalog.json --inference dist/models/suno_song_inference_model.json --prompts-dir dist/output/prompts
)

endlocal
