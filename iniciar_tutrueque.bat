@echo off
title TuTrueque - Iniciador
color 0A

cls
echo ==========================================
echo       TuTrueque - Iniciando Servidores
echo ==========================================
echo.
echo Iniciando ambos servidores...
start "TuTrueque - Backend" cmd /k "cd /d "%~dp0" && python manage.py runserver"
timeout /t 3 >nul
start "TuTrueque - Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"
echo Ambos servidores iniciados en ventanas separadas.
echo.
echo - Backend: http://127.0.0.1:8000/
echo - Frontend: http://127.0.0.1:5173/
echo.
timeout /t 2 >nul
