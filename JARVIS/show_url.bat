@echo off
:: ================================================
::  Show ULTRON's current live Cloudflare URL
:: ================================================
set LOG="c:\Users\saikrishna rajan\OneDrive\Desktop\SKR\JARVIS\ultron_tunnel.log"

if not exist %LOG% (
    echo [!] Tunnel log not found. Is ULTRON running?
    pause
    exit /b
)

echo.
echo  Searching for live ULTRON URL...
echo.

findstr /I "trycloudflare.com" %LOG%

echo.
echo  (Copy the https://... link above to share ULTRON)
pause
