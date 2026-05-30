@echo off
setlocal

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo Creando entorno virtual...
    python -m venv venv
)

call "venv\Scripts\activate.bat"

echo Instalando dependencias de Python...
python -m pip install -r requirements.txt

set PSQL_EXE=
for /f "delims=" %%P in ('dir /b /s "C:\Program Files\PostgreSQL\psql.exe" 2^>nul') do (
    set "PSQL_EXE=%%P"
)
for /f "delims=" %%P in ('dir /b /s "C:\Program Files\PostgreSQL\*\bin\psql.exe" 2^>nul') do (
    set "PSQL_EXE=%%P"
)

if defined PSQL_EXE (
    echo Verificando base de datos Tu_Trueque...
    set PGPASSWORD=admin123
    "%PSQL_EXE%" -U postgres -h 127.0.0.1 -tc "SELECT 1 FROM pg_database WHERE datname='Tu_Trueque';" | findstr /C:"1" >nul
    if errorlevel 1 (
        "%PSQL_EXE%" -U postgres -h 127.0.0.1 -c "CREATE DATABASE ""Tu_Trueque"";"
    )
) else (
    echo No se encontro psql.exe. Si la base no existe, creala manualmente una vez.
)

echo Aplicando migraciones...
python manage.py makemigrations
python manage.py migrate

echo Creando superusuario admin si no existe...
python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@admin.com', 'admin', nombre_real='Administrador')"

if not exist "frontend\node_modules" (
    echo Instalando dependencias de Node...
    pushd frontend
    npm install
    popd
)

echo Iniciando backend en http://127.0.0.1:8000
start "TuTrueque Backend" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && python manage.py runserver"

echo Iniciando frontend en http://127.0.0.1:5173
start "TuTrueque Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo Proyecto iniciado. Puedes cerrar esta ventana.
endlocal
