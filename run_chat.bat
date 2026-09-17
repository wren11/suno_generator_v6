@echo off
chcp 65001 >nul
setlocal
cd /d %~dp0

:: Detect Python executable
set PYTHON_EXE=
if exist .venv\Scripts\python.exe set PYTHON_EXE=.venv\Scripts\python.exe
if not defined PYTHON_EXE if exist ..\.venv\Scripts\python.exe set PYTHON_EXE=..\.venv\Scripts\python.exe
if not defined PYTHON_EXE (
    for %%P in (python.exe) do set PYTHON_EXE=%%~
)

if not defined PYTHON_EXE (
    echo [ERROR] Python not found! Please install Python 3.10+ or set up a virtual environment.
    pause
    exit /b 1
)

echo ======================================================================
echo   SUNOGPT STUDIO: CHATGPT INTERFACE FOR SUNO AI ^& SCANSION-LM
echo   Connecting to 21,087-song Reference Model ^& Scansion Neural Model...
echo   Open in your browser: http://localhost:7861
echo ======================================================================
%PYTHON_EXE% chat_app.py
pause
