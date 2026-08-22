@echo off
REM ============================================================
REM  ⚡ Windows AI Helper — Launcher Script
REM  Launches the system-tray application in background.
REM ============================================================

set VENV_PYTHON=%USERPROFILE%\AppData\Local\hermes\hermes-agent\venv\Scripts\pythonw.exe
set VENV_PYTHON_CLI=%USERPROFILE%\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe

if exist "%VENV_PYTHON%" (
    set PYTHON_EXE=%VENV_PYTHON%
) else if exist "%VENV_PYTHON_CLI%" (
    set PYTHON_EXE=%VENV_PYTHON_CLI%
) else (
    set PYTHON_EXE=python
)

REM ── Check if Ollama is running ───────────────────────────────
ollama list >nul 2>&1
if %errorlevel% neq 0 (
    start "Ollama Serve" /min cmd /c "ollama serve"
    timeout /t 2 >nul
)

REM ── Launch the helper app ────────────────────────────────────
cd /d "%~dp0"
"%PYTHON_EXE%" main.py

