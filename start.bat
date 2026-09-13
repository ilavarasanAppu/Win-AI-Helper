@echo off
REM ============================================================
REM  ⚡ Win AI Helper — One-Click Background Launcher
REM  - Auto-checks dependencies
REM  - Auto-starts Ollama if needed
REM  - Runs application detached in background via pythonw
REM  - Automatically closes this terminal immediately
REM ============================================================

cd /d "%~dp0"

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

REM — Locate Python & Pythonw Executable ————————————————————————
set "PYTHON_EXE="
set "PYTHONW_EXE="

if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    set "PYTHONW_EXE=%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"
) else if exist "%USERPROFILE%\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" (
    set "PYTHON_EXE=%USERPROFILE%\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
    set "PYTHONW_EXE=%USERPROFILE%\AppData\Local\hermes\hermes-agent\venv\Scripts\pythonw.exe"
) else (
    set "PYTHON_EXE=python"
    set "PYTHONW_EXE=pythonw"
)

REM Fallback if pythonw.exe not explicitly found
if not exist "%PYTHONW_EXE%" (
    where pythonw >nul 2>&1 && set "PYTHONW_EXE=pythonw" || set "PYTHONW_EXE=%PYTHON_EXE%"
)

REM — Check & Install Dependencies if Missing ——————————————————
if exist "requirements.txt" (
    "%PYTHON_EXE%" -c "import PySide6" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [i] Installing required packages...
        "%PYTHON_EXE%" -m pip install -r requirements.txt --quiet
    )
)

REM — Ensure Ollama Server is Running ——————————————————————————
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    ollama list >nul 2>&1
    if %errorlevel% neq 0 (
        start /min "" ollama serve
        ping 127.0.0.1 -n 3 >nul 2>&1
    )
)

REM — Launch Application Detached in Background ————————————————
start "" "%PYTHONW_EXE%" "%~dp0main.py"

REM — Close Terminal Window Immediately ————————————————————————
exit