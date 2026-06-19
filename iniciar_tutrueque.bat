@echo off
title TuTrueque - Iniciador
color 0A

cls
echo ==========================================
echo       TuTrueque - Configurando Entorno
echo ==========================================
echo.

REM Verificar/crear entorno virtual
if not exist "venv\Scripts\activate.bat" (
    echo Creando entorno virtual...
    python -m venv venv
    echo Entorno virtual creado.
) else (
    echo Entorno virtual ya existe.
)

REM Activar entorno virtual
call venv\Scripts\activate.bat

REM Instalar dependencias de Python
echo Instalando dependencias de Python...
pip install -r requirements.txt

REM Instalar dependencias de Node.js
echo Instalando dependencias de Node.js...
cd frontend
if not exist "node_modules" (
    call npm install
) else (
    echo node_modules ya existe.
)
cd ..

REM Ejecutar migraciones
echo Ejecutando migraciones de Django...
python manage.py migrate

REM Crear superusuario si no existe
echo Verificando superusuario...
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.config.settings'); django.setup(); from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin')"

cls
echo ==========================================
echo       TuTrueque - Iniciando Servidores
echo ==========================================
echo.
echo Iniciando ambos servidores...
start "TuTrueque - Backend" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate.bat && python manage.py runserver"
timeout /t 2 >nul
start "TuTrueque - Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"
echo Ambos servidores iniciados en ventanas separadas.
echo.
echo - Backend: http://127.0.0.1:8000/
echo - Frontend: http://127.0.0.1:5173/
echo - Admin: http://127.0.0.1:8000/admin/ (admin/admin)
echo.
timeout /t 5 >nul
