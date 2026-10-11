@echo off
rem SIP Compass - refresh public fund data (NAV history, expense ratios, fund sizes).
rem Double-click to run. Your goals and holdings are never read or sent anywhere.
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0updater\Run-Updater.ps1"
set "SIP_EXIT=%ERRORLEVEL%"
echo.
pause
exit /b %SIP_EXIT%
