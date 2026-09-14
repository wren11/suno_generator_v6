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

set "SONG_URL=%~1"
if not "%SONG_URL%"=="" goto :run_trainer

echo ============================================================
echo   SUNO SONG INGESTION ^& RETRAINING TOOL
echo ============================================================
echo Examples:
echo   1. Song URL:  https://suno.com/song/8ac118c0-3aab-43ac-af8f-57dbd1368e29
echo   2. Profile:   @wren (fetches all songs from suno.com/@wren)
echo   3. Created:   created (ingests all created songs ^& prompts)
echo   4. All:       all (trains on @wren profile + created songs)
echo.
set /p SONG_URL="Enter Song URL, Profile (@wren), or 'created': "

if "%SONG_URL%"=="" (
    echo [!] No song URL provided. Exiting.
    pause
    exit /b 1
)

:run_trainer
"%PYTHON_EXE%" -m src.trainer %SONG_URL% --catalog dist/models/suno_song_catalog.json --inference dist/models/suno_song_inference_model.json --audio-dir dist/output/audio --transcripts-dir dist/output/transcripts

if "%~1"=="" if "%NONINTERACTIVE%"=="" (
    echo.
    echo Press any key to exit...
    pause >nul
)
endlocal
