@echo off
REM ============================================================
REM  SafeConnect AI - One-click stop script
REM  Closes the backend (uvicorn) and frontend (serve.py) windows.
REM ============================================================

echo Stopping SafeConnect AI servers...

taskkill /FI "WINDOWTITLE eq SafeConnect AI - Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq SafeConnect AI - Frontend*" /T /F >nul 2>&1

echo Done. Both servers have been stopped (if they were running).
pause
