# Guía de Migración de Vistas Vue - MVC Estricto

## Resumen de Cambios Realizados

### Backend (Django) - ✅ COMPLETADO
**Archivos modificados:**
- `comunidad/models.py`: Agregados métodos de negocio a todos los models
- `comunidad/services.py`: Refactorizado para usar métodos de negocio de los models

**Cambios principales:**
- Models ahora contienen lógica de negocio (`usuario.puede_publicar()`, `publicacion.validar_reglas_negocio()`, etc.)
- Services delegan validaciones a métodos de negocio de los models
- Separación clara entre persistencia (Repository) y lógica de negocio (Service + Model methods)

### Frontend (Vue 3) - ✅ COMPLETADO (Infraestructura)

**Archivos nuevos creados:**
- `frontend/src/controllers/BaseController.js`: Controlador base con manejo de errores y estado reactivo
- `frontend/src/controllers/AuthController.js`: Controlador para autenticación (HU2)
- `frontend/src/controllers/CarteleraController.js`: Controlador para cartelera (HU3)
- `frontend/src/controllers/ComunidadController.js`: Controlador para comunidad (HU2)
- `frontend/src/controllers/PerfilController.js`: Controlador para perfil (HU2)
- `frontend/src/controllers/TruequeController.js`: Controlador para trueques (HU4)
- `frontend/src/controllers/AdminController.js`: Controlador para admin (HU1)
- `frontend/src/controllers/ResenaController.js`: Controlador para reseñas (HU4)
- `frontend/src/repositories/ApiClient.js`: Cliente HTTP con sistema de caché en memoria
- `frontend/src/repositories/AuthRepository.js`: Repositorio de autenticación con caché
- `frontend/src/repositories/PublicacionRepository.js`: Repositorio de publicaciones con caché
- `frontend/src/repositories/UsuarioRepository.js`: Repositorio de usuarios con caché
- `frontend/src/repositories/TruequeRepository.js`: Repositorio de trueques con caché
- `frontend/src/repositories/AdminRepository.js`: Repositorio administrativo
- `frontend/src/repositories/ResenaRepository.js`: Repositorio de reseñas con caché
- `frontend/src/models/Trueque.js`: Modelo de Trueque con métodos de negocio

**Archivos modificados:**
- `frontend/src/models/User.js`: Agregados métodos de negocio
- `frontend/src/models/Publicacion.js`: Agregados métodos de negocio

## Guía de Migración de Vistas

Las vistas Vue actuales necesitan ser refactorizadas para usar los nuevos controladores específicos en lugar del `UserController.js` centralizado. A continuación se explica cómo migrar cada vista.

### Paso 1: Configurar Proveedores en main.js

Antes de migrar las vistas, configure los controladores como proveedores globales en `main.js`:

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// Importar controladores
import AuthController from './controllers/AuthController.js'
import CarteleraController from './controllers/CarteleraController.js'
import ComunidadController from './controllers/ComunidadController.js'
import PerfilController from './controllers/PerfilController.js'
import TruequeController from './controllers/TruequeController.js'
import AdminController from './controllers/AdminController.js'
import ResenaController from './controllers/ResenaController.js'

const app = createApp(App)

// Crear instancias de controladores
const authController = new AuthController()
const carteleraController = new CarteleraController()
const comunidadController = new ComunidadController()
const perfilController = new PerfilController()
const truequeController = new TruequeController()
const adminController = new AdminController()
const resenaController = new ResenaController()

// Proveer controladores globalmente
app.provide('authController', authController)
app.provide('carteleraController', carteleraController)
app.provide('comunidadController', comunidadController)
app.provide('perfilController', perfilController)
app.provide('truequeController', truequeController)
app.provide('adminController', adminController)
app.provide('resenaController', resenaController)

app.use(router)
app.mount('#app')
```

### Paso 2: Migrar Register.vue (HU2)

**Cambios principales:**
- Reemplazar `userController` con `authController`
- Eliminar lógica de validación de la vista (delegar al controlador)
- Usar estado reactivo del controlador

**Ejemplo de migración:**

```javascript
// ANTES (código actual)
import { inject } from 'vue'
const userController = inject('userController')

// DESPUÉS (nuevo código)
import { inject } from 'vue'
const authController = inject('authController')

// Reemplazar llamadas:
// userController.validarEmail -> authController.validarEmail
// userController.registrarUsuario -> authController.registrarUsuario
```

**Validaciones a eliminar de la vista:**
- Validación de formato de email (el controlador ya la hace)
- Validación de contraseña (el controlador ya la hace)
- Comparación de contraseñas (el controlador ya la hace)

### Paso 3: Migrar Cartelera.vue (HU3)

**Cambios principales:**
- Reemplazar `userController` con `carteleraController`
- Eliminar lógica de filtros de la vista (delegar al controlador)
- Eliminar lógica de creación de publicaciones de la vista
- Usar estado reactivo del controlador

**Ejemplo de migración:**

```javascript
// ANTES (código actual)
import { inject } from 'vue'
const userController = inject('userController')

// DESPUÉS (nuevo código)
import { inject } from 'vue'
const carteleraController = inject('carteleraController')

// Reemplazar llamadas:
// userController.obtenerCartelera -> carteleraController.cargarCartelera
// userController.crearPublicacion -> carteleraController.crearPublicacion
// userController.obtenerMisPublicaciones -> carteleraController.cargarMisPublicaciones
// userController.actualizarEstadoPublicacion -> carteleraController.actualizarEstadoPublicacion
```

**Lógica a eliminar de la vista:**
- Lógica de filtros (categoría, urgencia)
- Lógica de conteo de publicaciones críticas/talentos
- Lógica de cambio entre modo publicación y visualización
- Validaciones de formulario de publicación

### Paso 4: Migrar Comunidad.vue (HU2)

**Cambios principales:**
- Reemplazar `userController` con `comunidadController`
- Eliminar lógica de navegación entre directorio/detalle
- Eliminar lógica de filtros de miembros
- Usar estado reactivo del controlador

**Ejemplo de migración:**

```javascript
// ANTES (código actual)
import { inject } from 'vue'
const userController = inject('userController')

// DESPUÉS (nuevo código)
import { inject } from 'vue'
const comunidadController = inject('comunidadController')

// Reemplazar llamadas:
// userController.obtenerComunidad -> comunidadController.cargarComunidad
// userController.obtenerPerfilUsuario -> comunidadController.cargarPerfilUsuario
```

**Lógica a eliminar de la vista:**
- Lógica de cambio entre vistas (directorio/detalle)
- Lógica de selección de miembros
- Validaciones de propuestas

### Paso 5: Migrar Perfil.vue (HU2)

**Cambios principales:**
- Reemplazar `userController` con `perfilController` y `truequeController`
- Eliminar lógica de gestión de trueques de la vista
- Eliminar lógica de reseñas de la vista
- Usar estado reactivo de los controladores

**Ejemplo de migración:**

```javascript
// ANTES (código actual)
import { inject } from 'vue'
const userController = inject('userController')

// DESPUÉS (nuevo código)
import { inject } from 'vue'
const perfilController = inject('perfilController')
const truequeController = inject('truequeController')
const resenaController = inject('resenaController')

// Reemplazar llamadas:
// userController.obtenerMiPerfil -> perfilController.cargarMiPerfil
// userController.obtenerMisTrueques -> perfilController.cargarMisTrueques
// userController.finalizarTrueque -> perfilController.finalizarTrueque
// userController.registrarResena -> resenaController.registrarResena
```

**Lógica a eliminar de la vista:**
- Lógica de separación de publicaciones activas/pausadas
- Lógica de cálculo de impacto en horas
- Lógica de estados de trueque
- Validaciones de reseñas

### Paso 6: Migrar AdminCSV.vue (HU1)

**Cambios principales:**
- Reemplazar `userController` con `adminController`
- Eliminar lógica de validación de archivo de la vista
- Usar estado reactivo del controlador

**Ejemplo de migración:**

```javascript
// ANTES (código actual)
import { inject } from 'vue'
const userController = inject('userController')

// DESPUÉS (nuevo código)
import { inject } from 'vue'
const adminController = inject('adminController')

// Reemplazar llamadas:
// userController.cargarUsuariosAutorizados -> adminController.cargarUsuariosAutorizados
// Lógica de selección de archivo -> adminController.seleccionarArchivo
```

**Lógica a eliminar de la vista:**
- Validación de extensión de archivo (.csv)
- Validación de selección de archivo
- Manejo de errores de carga

### Paso 7: Actualizar App.vue para sesión inicial

```javascript
// Agregar en onMounted del componente principal
import { inject, onMounted } from 'vue'

const authController = inject('authController')

onMounted(async () => {
  await authController.obtenerSesionActual()
})
```

### Paso 8: Eliminar archivos obsoletos

Después de migrar todas las vistas, eliminar los siguientes archivos:

```bash
rm frontend/src/controllers/UserController.js
rm frontend/src/models/UserService.js
```

## Diagrama de Secuencia (Texto)

```
Usuario → Vista Vue → Controlador (por HU) → Repositorio (con caché) → API Django → Backend
    ↓           ↓                    ↓                      ↓                    ↓         ↓
   Click    Evento UI        Lógica de Negocio    Caché en memoria    HTTP      Models/Services
                                   + Estado              (Map)            POST/GET    con métodos
                                   Reactivo              GET/            JSON        de negocio
```

## Gestión de Memoria Reactiva

**Características implementadas:**

1. **Caché en memoria (ApiClient):**
   - Cada repositorio usa un `Map` para cachear respuestas
   - Tiempo de vida: 5 minutos por defecto
   - Invalidación automática después de mutaciones (POST, PATCH, DELETE)
   - Estadísticas de uso: hits, misses, hit rate

2. **Estado reactivo (BaseController):**
   - `loading`: Estado de carga compartido
   - `error`: Manejo centralizado de errores
   - `data`: Datos almacenados en memoria
   - Cada controlador específico agrega su propio estado reactivo

3. **Invalidación de caché:**
   - Manual: `repository.invalidate(key)` o `repository.invalidateAll()`
   - Automática: Después de cada mutación (POST, PATCH, DELETE)
   - Por tiempo: Entradas expiran después de 5 minutos

4. **Reactividad Vue:**
   - Los controladores usan `ref()` y `reactive()` de Vue
   - Las vistas se actualizan automáticamente cuando cambia el estado
   - No necesidad de recargar la página

## Validaciones Frontend

**Validaciones implementadas en controladores:**

1. **AuthController:**
   - Formato de email
   - Longitud de contraseña (mínimo 8 caracteres)
   - Coincidencia de contraseñas
   - Campos requeridos

2. **CarteleraController:**
   - Categoría válida
   - Título requerido
   - Descripción mínima (10 caracteres)
   - Urgencia para talentos (solo Normal)

3. **TruequeController:**
   - Receptor requerido
   - Acción válida (ACEPTAR/RECHAZAR)

4. **ResenaController:**
   - Calificación entre 1 y 5
   - Comentario requerido (mínimo 10 caracteres, máximo 500)

5. **AdminController:**
   - Usuario debe ser administrador
   - Archivo debe ser .csv
   - Archivo debe estar seleccionado

## Verificación y Testing

**Pasos para verificar la implementación:**

1. **Ejecutar backend:**
   ```bash
   python manage.py runserver
   ```

2. **Ejecutar frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Probar HU1 (Admin CSV):**
   - Iniciar sesión como admin
   - Cargar archivo CSV de prueba
   - Verificar que se procesen los correos

4. **Probar HU2 (Registro y Perfiles):**
   - Registrarse con correo autorizado
   - Verificar validaciones frontend
   - Verificar perfil miembro
   - Verificar perfiles públicos en comunidad

5. **Probar HU3 (Cartelera):**
   - Verificar carga de publicaciones
   - Aplicar filtros (categoría, urgencia)
   - Crear nueva publicación
   - Pausar/reactivar publicaciones

6. **Probar HU4 (Trueques):**
   - Verificar matches
   - Crear propuesta de trueque
   - Aceptar/rechazar propuesta
   - Finalizar trueque
   - Dejar reseña

7. **Verificar caché:**
   - Abrir DevTools del navegador
   - Ir a Network tab
   - Navegar por la aplicación
   - Verificar que las llamadas repetidas a los mismos endpoints sean menos (caché funcionando)
   - Verificar que después de mutaciones se invaliden las cachés

## Notas Finales

**Cumplimiento de requisitos de la profesora:**

✅ **Services:** Contienen lógica de negocio (en backend)  
✅ **Repositories:** Se encargan de persistencia (backend + frontend)  
✅ **Models:** Tienen métodos de negocio (backend + frontend)  
✅ **Frontend:** Solo es capa de vista (después de migración)  
✅ **Controladores:** Cada HU tiene su propio controlador  
✅ **Persistencia ORM:** Models llaman al Repository en backend  
✅ **Validaciones:** En frontend (controladores) y backend (services)  
✅ **Vista no conoce Repository:** Las vistas llaman a controladores, no a repositorios  
✅ **Guardar en memoria:** Implementado con caché en memoria + estado reactivo  
✅ **Verificar antes de salvar:** Services y validaciones frontend verifican antes de crear/actualizar  

**Arquitectura resultante:**
- Separación clara de responsabilidades
- Controladores testeables (sin dependencias del DOM)
- Estado reactivo para UI automática
- Caché en memoria para mejor rendimiento
- Validaciones robustas en múltiples capas
- Métodos de negocio en models siguiendo principios OO
