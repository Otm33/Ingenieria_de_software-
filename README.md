# TuTrueque

Aplicación web para el intercambio de servicios y talentos basado en **horas de vida** y **saldos comerciales**, desarrollada como proyecto de Ingeniería de Software.

---

## Arranque Rápido (Windows)

```bat
iniciar_tutrueque.bat
```

El script crea/usa el entorno virtual, instala dependencias, aplica migraciones, crea el superusuario `admin/admin` si no existe y abre dos terminales: backend en `http://127.0.0.1:8000` y frontend en `http://127.0.0.1:5173`.

---

## Requisitos Previos

| Software | Versión Recomendada |
|---|---|
| Python | 3.12+ |
| Node.js | 20+ |
| npm | (incluido con Node.js) |
| Git | Cualquiera reciente |

> **Nota**: La configuración actual usa **SQLite** por defecto (`db.sqlite3`). Si deseas usar PostgreSQL, modifica `DATABASES` en `backend/config/settings.py` e instala PostgreSQL 15+.

---

## Instalación Manual

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd Ingenieria_de_software_TuTrueque
```

### 2. Backend (Django)

```bash
# Crear y activar el entorno virtual
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Iniciar el servidor
python manage.py runserver
```

El backend quedará escuchando en `http://127.0.0.1:8000`.

### 3. Frontend (Vue)

En una nueva terminal:

```bash
cd frontend
npm install
npm run dev
```

El frontend quedará disponible en `http://127.0.0.1:5173`.

---

## URLs de Acceso Local

| Servicio | URL | Descripción |
|---|---|---|
| **Frontend** | http://localhost:5173 | Interfaz de usuario (Vue 3) |
| **Backend API** | http://localhost:8000/api/ | Endpoints REST (Django) |
| **Admin Panel** | http://localhost:8000/admin/ | Administrador de Django |

---

## Arquitectura del Proyecto

El proyecto sigue una **Arquitectura en Capas (N-Tier)** con implementación híbrida de **DDD** y **Clean Architecture**:

```
Presentación → Negocio/Lógica → Persistencia → Base de Datos
```

### Estructura del Backend (`backend/comunidad/`)

```
comunidad/
├── dominio/              # Capa de Dominio — Entidades puras (dataclasses)
│   └── entidades.py      #   UsuarioDominio, PublicacionDominio, AcuerdoTruequeDominio, etc.
│
├── negocio/              # Capa de Negocio — Reglas y validaciones puras (sin ORM)
│   ├── usuario.py        #   tiene_saldo_critico(), puede_publicar(), es_comercio_activo()
│   ├── publicacion.py    #   validar_reglas_negocio(), es_talento(), es_urgente()
│   ├── trueque.py        #   puede_confirmar(), ambas_partes_confirmaron(), contraparte_id()
│   ├── trueque_multiple.py  # todos_aceptaron(), obtener_rol()
│   ├── resena.py         #   calificacion_valida(), comentario_valido()
│   ├── notificacion.py   #   esta_leida(), es_de_tipo_match()
│   └── validaciones/     #   Reglas de contenido (palabras prohibidas)
│
├── interfaces/           # Contratos abstractos (ABC) — Inversión de Dependencias
│   ├── repository_interfaces.py  # IUsuarioRepository, ITruequeRepository, etc.
│   └── service_interfaces.py     # TruequeInterface, ResenaInterface, etc.
│
├── services/             # Capa de Servicios — Orquestación de negocio
│   ├── trueque.py        #   TruequeService: crear propuestas, finalizar trueques
│   ├── publicacion.py    #   PublicacionService: CRUD de publicaciones
│   ├── matchmaking.py    #   MatchmakingService: emparejamiento automático
│   ├── impacto_social.py #   ImpactoSocialService: solicitudes, donaciones, fondo
│   ├── notificacion.py   #   NotificacionService: crear/marcar notificaciones
│   ├── resena.py         #   ResenaService: registrar reseñas
│   ├── comercio.py       #   ComercioService: vuelto comercial, pagos con saldo
│   └── base.py           #   BusinessError (excepción base de negocio)
│
├── controladores/        # Capa de Presentación — Controladores (traducción y orquestación)
│   ├── hu_s1_hu2_registro_publicacion_controller.py
│   ├── hu_s1_hu4_match_trueque_controller.py
│   ├── hu_s1_hu5_comercio_controller.py
│   ├── hu_s2_hu1_impacto_social_controller.py
│   └── ...
│
├── routers/              # Capa de Presentación — Routers (Django Views / endpoints HTTP)
│   ├── hu_s1_hu1_comunidad_router.py
│   ├── hu_s1_hu2_registro_publicacion_router.py
│   ├── hu_s1_hu3_cartelera_router.py
│   └── ...
│
├── dto/                  # Data Transfer Objects — Objetos de entrada HTTP
│   └── request_models.py #   CrearPublicacionRequest, PropuestaRequest, LoginRequest, etc.
│
├── repositorios_implementacion.py  # Capa de Persistencia — Implementaciones de repositorios
├── models.py             # Capa de Base de Datos — Modelos ORM de Django
├── serializers.py        # Serializadores DRF (Presentación)
├── urls.py               # Configuración de URLs
├── admin.py              # Registro de modelos en Django Admin
├── catalogo_causas_sociales.py     # Whitelist de causas sociales
│
├── utils/                # Utilidades compartidas
│   └── conversor_orm_dominio.py    # Conversor ORM→Dominio para autenticación
│
└── tests/                # Tests automatizados
    ├── test_historias_usuario.py
    ├── test_hu4.py
    ├── test_hu4_api.py
    ├── test_impacto_social.py
    └── test_trueque_multiple.py
```

### Flujo de una petición

```
Vue (Frontend) → Pinia Store → ApiService (axios)
    → Django Router (View) → Controlador → Servicio
        → Funciones de Negocio (validaciones puras)
        → Repositorio (ORM ↔ Entidad de Dominio)
            → Django ORM → Base de Datos
```

### Estructura del Frontend (`frontend/src/`)

```
src/
├── views/                # Páginas/vistas Vue (lo que el usuario ve)
│   ├── Cartelera.vue     #   Tablero de publicaciones disponibles
│   ├── Perfil.vue        #   Perfil de usuario e historial
│   ├── RedComercial.vue  #   Gestión de saldo comercial
│   ├── ImpactoSocial.vue #   Solicitudes y donaciones
│   ├── Comunidad.vue     #   Directorio de la comunidad
│   ├── Register.vue      #   Registro de usuarios
│   └── AdminCSV.vue      #   Panel de carga CSV (admin)
│
├── components/           # Componentes Vue reutilizables
│   ├── ModalNotificaciones.vue
│   ├── ModalPropuesta.vue
│   ├── ModalResena.vue
│   └── ModalConfirmacion.vue
│
├── stores/               # Estado global reactivo (Pinia)
│   ├── auth.js           #   Sesión, login, logout
│   ├── cartelera.js      #   Publicaciones y filtros
│   ├── trueque.js        #   Propuestas, matches, trueques
│   ├── comercio.js       #   Saldo comercial
│   ├── impactoSocial.js  #   Impacto social
│   ├── perfil.js         #   Perfil de usuario
│   ├── resena.js         #   Reseñas
│   ├── comunidad.js      #   Directorio de comunidad
│   └── admin.js          #   Panel de administración
│
├── services/api/         # Servicios API (llamadas HTTP al backend)
│   ├── ApiClient.js      #   Cliente axios base (interceptores, CSRF)
│   ├── AuthApiService.js
│   ├── PublicacionApiService.js
│   ├── TruequeApiService.js
│   ├── ComercioApiService.js
│   ├── ImpactoSocialApiService.js
│   ├── UsuarioApiService.js
│   ├── ResenaApiService.js
│   └── AdminApiService.js
│
├── models/               # Modelos/clases JavaScript (espejo del dominio)
│   ├── User.js
│   ├── Publicacion.js
│   ├── Trueque.js
│   └── RequestModels.js  #   DTOs de entrada (equivale a dto/request_models.py)
│
├── data/                 # Datos estáticos y catálogos
│   ├── catalogoServicios.js         # Categorías de servicios
│   └── catalogoCausasSociales.js    # Causas sociales permitidas
│
├── router/               # Configuración de Vue Router (navegación)
│   └── index.js
│
├── App.vue               # Componente raíz de la aplicación
├── main.js               # Punto de entrada de Vue
└── styles.css            # Estilos globales
```

---

## Stack Tecnológico

### Backend
| Tecnología | Versión | Uso |
|---|---|---|
| Django | 5.2.15 | Framework web, ORM, autenticación |
| Django REST Framework | 3.17.1 | Serialización y API REST |
| django-cors-headers | 4.9.0 | CORS para comunicación con Vue |
| psycopg2-binary | 2.9.12 | Adaptador PostgreSQL |
| bcrypt | 5.0.0 | Hashing de contraseñas (BCryptSHA256) |

### Frontend
| Tecnología | Versión | Uso |
|---|---|---|
| Vue.js | 3.5.32 | Framework de UI reactivo |
| Pinia | 3.0.4 | Estado global reactivo |
| Vue Router | 5.0.7 | Navegación SPA |
| Vite | 8.0.8 | Bundler y dev server |

### Base de Datos
- **Desarrollo**: SQLite (archivo `db.sqlite3`, configuración por defecto)
- **Producción**: PostgreSQL 15+ (configurar en `settings.py`)

---

## Historias de Usuario Implementadas

### Sprint 1
| HU | Nombre | Descripción |
|---|---|---|
| HU1 | Gestión de la Comunidad | Carga CSV de usuarios autorizados, validación de email |
| HU2 | Registro y Publicaciones | Registro, login, CRUD de publicaciones (talentos/necesidades) |
| HU3 | Cartelera y Filtros | Tablero de publicaciones con filtros por categoría y urgencia |
| HU4 | Emparejamiento (Match) | Matchmaking automático, propuestas, notificaciones, reseñas |
| HU5 | Red Comercial | Emisión de vuelto, pago con saldo comercial entre comercios |

### Sprint 2
| HU | Nombre | Descripción |
|---|---|---|
| HU1 | Impacto Social | Solicitudes de apoyo, donaciones de horas, fondo comunitario |
| HU2 | Perfil e Historial | Perfil público, historial de trueques, directorio de comunidad |
| HU4 | Trueques Múltiples | Acuerdos de trueque entre 3 participantes (ciclo) |
| HU5 | Finalización con Código | Confirmación de trueques con código de validación |

---

## Diagramas de Arquitectura

Los diagramas PlantUML del proyecto se encuentran en la carpeta `Arquitectura/`:

- `DiagramaActividades.puml` — Flujo general de actividades
- `SecuenciaHU1.puml` a `SecuenciaHU5.puml` — Diagramas de secuencia por HU del Sprint 1

---

## Tests

```bash
# Ejecutar todos los tests
python manage.py test comunidad

# Tests específicos
python manage.py test comunidad.tests.test_hu4
python manage.py test comunidad.tests.test_impacto_social
python manage.py test comunidad.tests.test_trueque_multiple
```

---

## Comandos Útiles

```bash
# Crear nuevas migraciones
python manage.py makemigrations

# Aplicar migraciones pendientes
python manage.py migrate

# Abrir shell de Django
python manage.py shell

# Crear superusuario
python manage.py createsuperuser
```
