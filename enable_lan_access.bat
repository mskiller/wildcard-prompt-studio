@echo off
setlocal
cd /d "%~dp0"
title Enable Local Network Access - Wildcard Prompt Studio

:: Check for administrative permissions
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrative permissions to update Windows Defender Firewall...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c `\"%~f0`\"' -Verb RunAs"
    exit /b
)

echo ========================================================
echo  Wildcard Prompt Studio - Local Network Access Setup
echo ========================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup_firewall.ps1"

echo.
echo ========================================================
echo  Setup complete! Press any key to close this window.
echo ========================================================
pause >nul
