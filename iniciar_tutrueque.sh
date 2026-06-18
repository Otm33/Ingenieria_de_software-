#!/bin/bash

# =============================================
#       TuTrueque - Iniciador (Linux/macOS)
# =============================================

# Colores para la terminal
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin color

# Cambiar al directorio del script
cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"

echo ""
echo -e "${CYAN}==========================================${NC}"
echo -e "${CYAN}    TuTrueque - Configurando Entorno${NC}"
echo -e "${CYAN}==========================================${NC}"
echo ""

# --- 1. Entorno virtual ---
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creando entorno virtual...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Entorno virtual creado.${NC}"
else
    echo -e "${GREEN}Entorno virtual ya existe.${NC}"
fi

source venv/bin/activate

# --- 2. Dependencias Python ---
echo -e "${YELLOW}Instalando dependencias de Python...${NC}"
pip install -r requirements.txt --quiet

# --- 3. Dependencias Node.js ---
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Instalando dependencias de Node.js...${NC}"
    cd frontend
    npm install
    cd ..
else
    echo -e "${GREEN}node_modules ya existe.${NC}"
fi

# --- 4. Migraciones ---
echo -e "${YELLOW}Ejecutando migraciones de Django...${NC}"
python manage.py migrate

# --- 5. Superusuario ---
echo -e "${YELLOW}Verificando superusuario...${NC}"
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@admin.com', 'admin', nombre_real='Administrador')
    print('Superusuario admin creado.')
else:
    print('Superusuario admin ya existe.')
"

# --- 6. Iniciar servidores ---
clear
echo ""
echo -e "${CYAN}==========================================${NC}"
echo -e "${CYAN}    TuTrueque - Iniciando Servidores${NC}"
echo -e "${CYAN}==========================================${NC}"
echo ""
echo -e "${YELLOW}Iniciando ambos servidores...${NC}"
echo ""

# Funcion para matar los procesos al salir
cleanup() {
    echo ""
    echo -e "${RED}Deteniendo servidores...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Servidores detenidos.${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# Iniciar backend en background
cd "$SCRIPT_DIR"
source venv/bin/activate
python manage.py runserver &
BACKEND_PID=$!
sleep 2

# Iniciar frontend en background
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}    Ambos servidores iniciados${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo -e "  Backend:  ${CYAN}http://127.0.0.1:8000/${NC}"
echo -e "  Frontend: ${CYAN}http://127.0.0.1:5173/${NC}"
echo -e "  Admin:    ${CYAN}http://127.0.0.1:8000/admin/${NC} (admin/admin)"
echo ""
echo -e "${YELLOW}Presiona Ctrl+C para detener ambos servidores.${NC}"
echo ""

# Esperar a que los procesos terminen
wait
