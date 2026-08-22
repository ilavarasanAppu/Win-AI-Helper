@echo off
REM ============================================================
REM  ⚡ Windows AI Helper — One-Click Setup & Launch
REM  Runs once to install dependencies and start Ollama.
REM ============================================================

REM ── Find Python with PySide6 installed ────────────────────────
REM    The venv at hermes-agent has all deps; fall back to system python
set VENV_PYTHON=%USERPROFILE%\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe

if exist "%VENV_PYTHON%" (
    set PYTHON_EXE=%VENV_PYTHON%
) else (
    set PYTHON_EXE=python
)

cd /d "%~dp0"

echo ================================================================
echo   ⚡ Windows AI Helper — Setup & Launch
echo ================================================================
echo.
echo [i] Using Python: %PYTHON_EXE%

REM ── Install Python packages ───────────────────────────────────
echo [1/3] Installing dependencies...
"%PYTHON_EXE%" -m pip install PySide6 pynput pyautogui pyperclip pyttsx3 sounddevice numpy faster-whisper Pillow
echo.

REM ── Start Ollama server (if not already running) ──────────────
echo [2/3] Starting Ollama...
ollama list >nul 2>&1
if %errorlevel% neq 0 (
    echo   -> Starting ollama serve...
    start "Ollama Serve" cmd /k "ollama serve --model lfm2.5-thinking:latest"
    timeout /t 3 >nul
) else (
    echo   -> Ollama already running — skipping.
)

REM ── Launch the helper app ─────────────────────────────────────
echo [3/3] Launching AI Helper...
echo Starting Win AI Helper...
"%PYTHON_EXE%" -u main.py
echo.
echo [App exited. Check above for errors.]
pause
