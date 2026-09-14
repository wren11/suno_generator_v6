@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

title Suno AI Live Target Monitor and Auto-Trainer

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

:: Argument Routing:
:: Supports:
::   auto_train.bat
::   auto_train.bat 10
::   auto_train.bat @wren
::   auto_train.bat @wren 15
::   auto_train.bat https://suno.com/@wren
::   auto_train.bat https://suno.com/playlist/<uuid>
::   auto_train.bat @wren --once

set "ARG1=%~1"
set "ARG2=%~2"
set "ALL_ARGS=%*"

set "ARG1_IS_NUM="
if not "%ARG1%"=="" (
    set "NOT_NUM="
    for /f "delims=0123456789" %%A in ("%ARG1%") do set "NOT_NUM=1"
    if not defined NOT_NUM set "ARG1_IS_NUM=1"
)

set "ARG2_IS_NUM="
if not "%ARG2%"=="" (
    set "NOT_NUM2="
    for /f "delims=0123456789" %%B in ("%ARG2%") do set "NOT_NUM2=1"
    if not defined NOT_NUM2 set "ARG2_IS_NUM=1"
)

set "RUN_ARGS="

if "%ALL_ARGS%"=="" (
    set "RUN_ARGS=--recheck 30"
) else if defined ARG1_IS_NUM (
    set "RUN_ARGS=--recheck %ARG1%"
) else if not "%ARG1%"=="" (
    if defined ARG2_IS_NUM (
        set "RUN_ARGS=%ARG1% --recheck %ARG2%"
    ) else (
        set "RUN_ARGS=%ALL_ARGS%"
    )
)

"%PYTHON_EXE%" -m src.auto_trainer %RUN_ARGS%

if "%NONINTERACTIVE%"=="" (
    echo.
    echo [i] Auto-trainer session ended. Press any key to exit...
    pause >nul
)
endlocal
