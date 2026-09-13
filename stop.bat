@echo off
REM ============================================================
REM  🛑 Win AI Helper — Clean Shutdown Script
REM  - Finds and terminates background main.py processes
REM  - Leaves unrelated python processes intact
REM  - Closes automatically after displaying status
REM ============================================================

cd /d "%~dp0"

echo [Win AI Helper] Stopping background application...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$procs = Get-CimInstance Win32_Process | Where-Object { ($_.Name -like 'python*.exe') -and ($_.CommandLine -like '*main.py*') }; if ($procs) { $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host ('[+] Successfully terminated Win AI Helper (PID ' + $_.ProcessId + ')') } } else { Write-Host '[-] Win AI Helper is not running.' }"

echo.
ping 127.0.0.1 -n 3 >nul 2>&1
exit
