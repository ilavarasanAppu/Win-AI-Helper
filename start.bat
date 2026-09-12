@echo off
REM ============================================================
REM  ⚡ Win AI Helper — One-Click Launcher
REM  Installs dependencies and launches app in background
REM  Terminal closes automatically after launch
REM ============================================================

cd /d "%~dp0"

REM — Find Python executable —————————————————————————————————————————
set "PYTHON_EXE=python"
if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
)

REM — Check if requirements.txt exists —————————————————————————
if exist "requirements.txt" (
    REM — Install dependencies silently ———————————————————————————
    "%PYTHON_EXE%" -m pip install -r requirements.txt --quiet --upgrade 2>nul
)

REM — Launch the application in background and close this window ———————
start /B "" "%PYTHON_EXE%" "%~dp0main.py"

REM — Close the terminal immediately ———————————————————————————
exit