@echo off
REM ============================================================
REM  SafeConnect AI - One-click local launcher
REM  Double-click this file to start the backend + frontend and
REM  open the app in your browser.
REM ============================================================

set "ROOT=%~dp0"

echo Starting SafeConnect AI backend...
start "SafeConnect AI - Backend" "%ROOT%_run_backend.bat"

echo Starting SafeConnect AI frontend...
start "SafeConnect AI - Frontend" "%ROOT%_run_frontend.bat"

echo Waiting for servers to start...
timeout /t 4 /nobreak >nul

echo Opening browser...
start "" "http://localhost:5500/index.html"

echo.
echo Two windows just opened: one for the backend, one for the frontend.
echo Keep both windows open while using the app.
echo Close this window any time - it is not needed anymore.
echo.
pause
