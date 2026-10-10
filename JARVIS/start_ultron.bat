@echo off
:: ================================================
::  ULTRON Auto-Start Launcher
::  Starts Flask server + Cloudflare live tunnel
:: ================================================
cd /d "c:\Users\saikrishna rajan\OneDrive\Desktop\SKR\JARVIS"

:: Kill any previous instances
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM cloudflared.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

:: Start ULTRON web server (hidden)
start "" /B pythonw main.py --web

:: Wait for server to come up
timeout /t 5 /nobreak >nul

:: Start Cloudflare tunnel (hidden) and log the URL
start "" /B cloudflared tunnel --url http://127.0.0.1:5000 > "%~dp0ultron_tunnel.log" 2>&1

echo ULTRON started. Tunnel URL will appear in ultron_tunnel.log
