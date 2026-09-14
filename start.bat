@echo off
title Amazon Listing Automation
cd /d "%~dp0"

set DASHBOARD_PORT=9090

echo ============================================
echo   Amazon Listing Automation - Dashboard
echo ============================================
echo.
echo Iniciando servidor na porta %DASHBOARD_PORT%...
echo Acesse: http://localhost:%DASHBOARD_PORT%
echo.
echo Pressione Ctrl+C para parar.
echo.

start http://localhost:%DASHBOARD_PORT%
python server.py
pause
