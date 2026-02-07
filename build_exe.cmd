@echo off
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File build_exe.ps1
echo.
echo EXE build complete. Check dist\MilkBillingSystem.exe
pause
