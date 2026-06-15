@echo off
title TuTrueque - Iniciador
color 0A

cls
echo ==========================================
echo       TuTrueque - Configuracion Inicial
echo ==========================================
echo.

REM Verificar/crear entorno virtual Python
if not exist "venv\Scripts\activate.bat" (
    echo [1/6] Creando entorno virtual Python...
    python -m venv venv
    echo Entorno virtual creado.
) else (
    echo [1/6] Entorno virtual Python ya existe.
)

REM Activar entorno virtual
call venv\Scripts\activate.bat

REM Instalar dependencias Python
echo [2/6] Instalando dependencias Python...
pip install -r requirements.txt -q
echo Dependencias Python instaladas.

REM Instalar dependencias Node.js
echo [3/6] Instalando dependencias Node.js...
cd frontend
if not exist "node_modules" (
    call npm install
) else (
    echo node_modules ya existe.
)
cd ..

REM Verificar base de datos PostgreSQL
echo [4/6] Verificando base de datos PostgreSQL...
echo Asegurate de que PostgreSQL este corriendo con usuario 'postgres' y clave 'admin123'
echo La base de datos 'tutrueque_db' debe existir.
pause

REM Ejecutar migraciones
echo [5/6] Ejecutando migraciones de Django...
python manage.py migrate

REM Iniciar servidores
echo [6/6] Iniciando servidores...
cls
echo ==========================================
echo       TuTrueque - Servidores Iniciados
echo ==========================================
echo.
start "TuTrueque - Backend" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate.bat && python manage.py runserver"
timeout /t 2 >nul
start "TuTrueque - Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"
echo.
echo - Backend: http://127.0.0.1:8000/
echo - Frontend: http://127.0.0.1:5173/
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul
