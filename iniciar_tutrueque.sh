#!/bin/bash

# Script de inicio para TuTrueque en Linux

# Cambiar al directorio del script
cd "$(dirname "$0")"

# Verificar y crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
source venv/bin/activate

echo "Instalando dependencias de Python..."
pip install -r requirements.txt

# Verificar PostgreSQL
if command -v psql &> /dev/null; then
    echo "Verificando base de datos Tu_Trueque..."
    export PGPASSWORD=admin123
    
    # Verificar si la base de datos existe
    if ! psql -U postgres -h 127.0.0.1 -tc "SELECT 1 FROM pg_database WHERE datname='Tu_Trueque';" | grep -q 1; then
        echo "Creando base de datos Tu_Trueque..."
        psql -U postgres -h 127.0.0.1 -c "CREATE DATABASE \"Tu_Trueque\";"
    fi
else
    echo "No se encontró psql. Si la base de datos no existe, créala manualmente una vez."
fi

echo "Aplicando migraciones..."
python manage.py makemigrations
python manage.py migrate

echo "Creando superusuario admin si no existe..."
python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@admin.com', 'admin', nombre_real='Administrador')"

if [ ! -d "frontend/node_modules" ]; then
    echo "Instalando dependencias de Node..."
    cd frontend
    npm install
    cd ..
fi

echo "Iniciando backend en http://127.0.0.1:8000"
gnome-terminal -- bash -c "cd $(pwd) && source venv/bin/activate && python manage.py runserver; exec bash" &
sleep 2

echo "Iniciando frontend en http://127.0.0.1:5173"
cd frontend
gnome-terminal -- bash -c "cd $(pwd) && npm run dev; exec bash" &

echo "Proyecto iniciado. Puedes cerrar esta ventana."

