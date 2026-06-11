@echo off
title TuTrueque - Iniciador
color 0A

:MENU
cls
echo ==========================================
echo       TuTrueque - Menu de Inicio
echo ==========================================
echo.
echo 1. Iniciar Frontend (Vite/Vue)
echo 2. Iniciar Backend (Django)
echo 3. Iniciar Ambos Servidores
echo 4. Salir
echo.
echo ==========================================
set /p opcion="Selecciona una opcion (1-4): "

if "%opcion%"=="1" goto INICIAR_FRONTEND
if "%opcion%"=="2" goto INICIAR_BACKEND
if "%opcion%"=="3" goto INICIAR_AMBOS
if "%opcion%"=="4" goto SALIR
goto MENU

:INICIAR_FRONTEND
echo.
echo Iniciando Frontend...
start "TuTrueque - Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"
echo Frontend iniciado en ventana separada.
timeout /t 2 >nul
goto MENU

:INICIAR_BACKEND
echo.
echo Iniciando Backend...
start "TuTrueque - Backend" cmd /k "cd /d "%~dp0" && python manage.py runserver"
echo Backend iniciado en ventana separada.
timeout /t 2 >nul
goto MENU

:INICIAR_AMBOS
echo.
echo Iniciando ambos servidores...
start "TuTrueque - Backend" cmd /k "cd /d "%~dp0" && python manage.py runserver"
timeout /t 3 >nul
start "TuTrueque - Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"
echo Ambos servidores iniciados en ventanas separadas.
echo.
echo - Backend: http://127.0.0.1:8000/
echo - Frontend: http://127.0.0.1:5173/
timeout /t 2 >nul
goto MENU

:SALIR
echo.
echo Saliendo...
exit
