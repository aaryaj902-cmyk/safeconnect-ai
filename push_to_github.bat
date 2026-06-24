@echo off
REM ============================================================
REM  SafeConnect AI - Push fixed code to GitHub
REM  Double-click this file to push everything to GitHub.
REM  Run this ONCE after extracting the zip into safeconnect folder.
REM ============================================================

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo.
echo === SafeConnect AI - GitHub Push ===
echo.
echo This will push the fixed code to your GitHub repo.
echo Your repo: https://github.com/aaryaj902-cmyk/safeconnect-ai
echo.

REM Check if git is already initialized
if exist ".git" (
    echo Git repo already exists. Adding remote if needed...
    git remote remove origin 2>nul
    git remote add origin https://github.com/aaryaj902-cmyk/safeconnect-ai.git
) else (
    echo Initializing git repo...
    git init
    git remote add origin https://github.com/aaryaj902-cmyk/safeconnect-ai.git
)

echo.
echo Staging all files...
git add .

echo.
echo Committing...
git commit -m "Final fixed version - all bugs resolved"

echo.
echo Setting branch to main...
git branch -M main

echo.
echo Pushing to GitHub (force push to overwrite old broken files)...
git push --force origin main

echo.
if %ERRORLEVEL% == 0 (
    echo SUCCESS! Code pushed to GitHub.
    echo.
    echo Next step: Go to Render dashboard and change CORS_ALLOW_ORIGINS
    echo from "*" to "https://safeconnect-frontend.onrender.com"
    echo.
    echo Render will auto-redeploy. Wait 5-10 minutes then test:
    echo https://safeconnect-frontend.onrender.com/verification-hub.html
) else (
    echo FAILED. GitHub may have asked for login.
    echo Try running: git push --force origin main
    echo in your terminal manually.
)
echo.
pause
