@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_quiz.ps1"
if errorlevel 1 (
  echo.
  echo Launch failed. Please read the message above.
  pause
)
endlocal
