# TuTrueque

Este es el proyecto de Ingeniería de Software **TuTrueque**, una aplicación web diseñada para el intercambio de servicios y talentos basado en horas de vida y saldos comerciales. El proyecto está completamente dockerizado para facilitar su desarrollo local.

---

## Requisitos Previos

Para ejecutar este proyecto localmente, asegúrate de tener instalado el siguiente software en tu sistema:
* **Python** (versión 3.12 recomendada).
* **Node.js** (versión 20 recomendada) y npm.
* **PostgreSQL** (versión 15 recomendada).
* **Git** (para clonar el repositorio).

---

## Configuración de la Base de Datos

Antes de levantar el proyecto, debes preparar tu servidor de base de datos local:

1. Abre tu gestor de base de datos PostgreSQL (por ejemplo, pgAdmin o la terminal `psql`).
2. Crea una base de datos en blanco llamada `tutrueque_db`.
3. Asegúrate de que las credenciales de conexión (usuario y contraseña) en tu archivo local de configuración de Django (`settings.py` o `.env`) coincidan con las de tu servidor local de PostgreSQL.

---

## Cómo Correr el Proyecto

### 1. Clonar el repositorio y entrar al proyecto
```
git clone <URL_DEL_REPOSITORIO>
cd Ingenieria_de_software_TuTrueque
```
2. Levantar el Backend (Django)Abre una terminal en la carpeta raíz del proyecto para configurar el entorno de Python, que utiliza la versión 4.0 o superior de Django:  Crear y activar el entorno virtual:
En Windows:
```
python -m venv venv
venv\Scripts\activate
```
En Linux/macOS:
```
python3 -m venv venv
source venv/bin/activate
```
Instalar dependencias y migrar la base de datos :

Asegúrate de que el entorno virtual esté activo (deberías ver (venv) en tu terminal) y ejecuta: 
```
python manage.py makemigrations
python manage.py migrate
```

Crear un Superusuario y arrancar el servidor :  
```
python manage.py createsuperuser
python manage.py runserver
```
(Mantén esta terminal abierta. El backend quedará escuchando en el puerto 8000).

3. Levantar el Frontend (Vue)Abre una nueva terminal, entra a la carpeta del frontend e

inicializa el proyecto de Node:  
```
cd frontend
npm install
npm run dev
```
(Mantén esta terminal abierta. El frontend quedará disponible en el puerto 5173) 

## URLs de Acceso Local

Una vez que los contenedores estén corriendo, podrás acceder a los diferentes servicios desde tu navegador:

| Servicio | URL | Descripción |
| --- | --- | --- |
| **Frontend** | http://localhost:5173 | Interfaz de usuario (Vue) |
| **Backend API** | http://localhost:8000/api/ | Endpoints del Backend (Django) |
| **Admin Panel** | http://localhost:8000/admin/ | Administrador de Django |

---


##  Nota para usuarios de Windows


### Usando Git Bash o PowerShell (Sin WSL)
Si usas la terminal clásica de Windows o Git Bash, el comando docker compose funcionará perfectamente, pero el comando make no viene instalado por defecto en Windows.

Para levantar el proyecto: `docker compose up o docker compose up --build`

Para crear el superusuario: `docker compose exec backend python manage.py createsuperuser`

* **Levantar el proyecto:** `docker compose up --build`
* **Crear el superusuario:** `docker compose exec backend python manage.py createsuperuser`


##  Comandos Útiles 

* **Apagar los contenedores:** Presiona `Ctrl + C` en la terminal donde corren o ejecuta `docker compose down`.
* **Ver logs en tiempo real:** `docker compose logs -f`
* **Entrar a la terminal del Backend:** `docker compose exec backend bash`
* **Crear nuevas migraciones de Django:** `docker compose exec backend python manage.py makemigrations`



---
# Como Probar Las Historias de Usuario (Sprint 1)

### HU 1: Gestionar la comunidad (Administrador)

1) Ingresar a la pagina de el front http://localhost:5173
2) Click en la pestaña "Panel CSV"
3) Click en el boton "Seleccionar Archivo"
4) Buscar y seleccionar el archivo csv en la carpeta raiz de el proyecto llamado "usuarios_autorizados_prueba.csv"
5) Click en el boton "Procesar Lista"
6) Click en la pestaña "Registrarse" y usar datos que no estan en el csv
7) Intentar nuevamente pero con un correo que si este en el csv

### HU 2: Gestión y Visualización de Perfiles

1) Registrarse con un correo que si este en el csv
2) Ingresar a la pagina de el back http://localhost:8000/admin/login/?next=/admin/
3) Iniciar sesion usando las credenciales de el super usuario
4) Click en la pestaña "Usuarios"
5) Click en algun usuario y visualizar los datos
6) Click en la pestaña "Publicaciones"
7) Click en la opcion "+Add" y crear 2 talentos con 2 necesidades para usuario(s)
8) Click en el boton "Save" si solo se quiere crear una publicaciones o "Save and add another" si se quiere crear varias publicaciones
9) Volver a la pagina de el front http://localhost:5173
10) Click en la pestaña "Cartelera"
11) Mostrar los intercambios disponibles y quien lo ofrece

### HU 3: Cartelera y Filtros

1) Ingresar a la pagina de el front http://localhost:5173
2) Click en la pestaña "Registrarse" y colocar los datos de un usuario de el csv
3) Click en la pestaña "Cartelera"
4) Mostrar las publicaciones disponibles y todos sus atributos
5) Probar cambiar la categoria y click en el boton "Aplicar Filtros"
6) Probar cambiar la prioridad y click en el boton "Aplicar Filtros"
7) click en el boton "Reestableces"

### HU 4: Emparejamiento y Gestión de Acuerdos (Match)

1) Ingresar a la pagina de el back http://localhost:8000/admin/login/?next=/admin/
2) Colocar en la terminal este comando que abre la shell: docker compose exec backend python manage.py shell
3) Insertar los siguientes pasos en la shell
4) Imprimir las horas de vida de ambos usuarios:
```
from django.contrib.auth import get_user_model
from comunidad.models import AcuerdoTrueque

Usuario = get_user_model()

user_emisor = Usuario.objects.get(username='nom_usuario1')  # REEMPLAZAR Usuario que solicita el servicio
user_receptor = Usuario.objects.get(username='nom_usuario2')  # REEMPLAZAR Usuario que presta el servicio

print(f"[SALDO INICIAL] Emisor ({user_emisor.username}): {user_emisor.horas_de_vida} | Receptor ({user_receptor.username}): {user_receptor.horas_de_vida}")
```
5) Se simula la crecion de un acuerdo en estado pendiente, Imprime el id y el estado de el acuerdo 
```
acuerdo = AcuerdoTrueque.objects.create(
    emisor=user_emisor, 
    receptor=user_receptor,
    estado='PROPUESTO',
    emisor_confirmado=False,
    receptor_confirmado=False
)
print(f"[REGISTRO] Acuerdo ID {acuerdo.id} creado con éxito en estado: {acuerdo.estado}")

```
6) Cierre de el acuerdo y transferencia de el tiempo

```
acuerdo.emisor_confirmado = True
acuerdo.receptor_confirmado = True
acuerdo.estado = 'FINALIZADO'
acuerdo.save()

if acuerdo.estado == 'FINALIZADO' and acuerdo.emisor_confirmado and acuerdo.receptor_confirmado:
    user_receptor.horas_de_vida += 1.0  # Incrementa el saldo de quien prestó el servicio
    user_emisor.horas_de_vida -= 1.0    # Decrementa el saldo de quien recibió el servicio
    
    # Persistir los nuevos estados financieros en la base de datos
    user_receptor.save()
    user_emisor.save()

print("[PROCESAMIENTO] Transacción de Horas de Vida ejecutada correctamente.")

```

7) Verificacion de los saldos de tiempo finales

```
user_receptor.refresh_from_db()
user_emisor.refresh_from_db()

print(f"[SALDO FINAL] Emisor ({user_emisor.username}): {user_emisor.horas_de_vida} | Receptor ({user_receptor.username}): {user_receptor.horas_de_vida}")
```

8) Ingresar a la pagina de el back http://localhost:8000/admin/login/?next=/admin/
9) Click en la pestaña "Usuarios" y mostrar las horas de vida
10) Click en la pestaña "Resenas" y añadir los datos de el acuerdo

### HU 5: Compensación de Excedentes en Red Comercial

1) Ingresar a la pagina de el back http://localhost:8000/admin/login/?next=/admin/
2) Colocar en la terminal este comando que abre la shell: docker compose exec backend python manage.py shell
3) Insertar los siguientes pasos en la shell
4) Configuración de Actores y Calibración de Estados Iniciales

```
from django.contrib.auth import get_user_model
Usuario = get_user_model()
cliente = Usuario.objects.get(username='nom_usuario_cliente') # REEMPLAZAR
comercio_A = Usuario.objects.get(username='nom_usuario_comercio1') #REEMPLAZAR
comercio_B = Usuario.objects.get(username='nom_usuario_comercio2') #REEMPLAZAR
 
cliente.saldo_comercial = 0.0
comercio_A.saldo_comercial = 0.0
comercio_B.saldo_comercial = 0.0
 
print(f"[ESTADO INICIAL CALIBRADO]")
print(f"-> Cliente (nom_usuario_cliente) - Horas de Vida: {cliente.horas_de_vida} | Saldo Comercial: {cliente.saldo_comercial}")  #REEMPLAZAR
print(f"-> Comercio A (nom_usuario_comercio1) - Saldo Comercial: {comercio_A.saldo_comercial}") #REEMPLAZAR
print(f"-> Comercio B (nom_usuario_comercio2) - Saldo Comercial: {comercio_B.saldo_comercial}") #REEMPLAZAR

```
5) Escenario de "Falta de Vuelto Físico" (Comercio A) Se simuló una transacción comercial donde el `Comercio A` no dispone de cambio físico y emite un vuelto digital de `4.50` unidades. El sistema persistió el incremento del activo digital del usuario y el pasivo del comercio de forma aislada: 

```
vuelto_faltante = 4.50
cliente.saldo_comercial += vuelto_faltante
comercio_A.saldo_comercial -= vuelto_faltante 
cliente.save()
comercio_A.save()
print(f"\n[REGISTRO DE EXCEDENTE EN COMERCIO A]")
print(f"-> Cliente - Horas de Vida (Aisladas): {cliente.horas_de_vida} | Saldo Comercial: {cliente.saldo_comercial}")
print(f"-> Comercio A - Balance Comercial: {comercio_A.saldo_comercial}")
```

6) Interoperabilidad Cruzada de la Red (Pago en Comercio B)

El cliente se desplazó al `Comercio B` (un tercero independiente en la red) y efectuó una compra por un valor de `3.00` unidades debitando su saldo digital acumulado. La base de datos consolidó la operación exitosamente:

```
monto_pago = 3.00
cliente.saldo_comercial -= monto_pago
comercio_B.saldo_comercial += monto_pago
cliente.save()
comercio_B.save() 
print(f"\n[COMPRA CRUZADA EN COMERCIO B]")
print(f"-> Cliente - Saldo Comercial Restante: {cliente.saldo_comercial}")
print(f"-> Comercio B - Balance Comercial Actualizado: {comercio_B.saldo_comercial}")

```

7) Balance Final Consolidado. Auditoria Final

```
cliente.refresh_from_db()
comercio_A.refresh_from_db()
comercio_B.refresh_from_db()
 
print(f"\n[DEMOSTRACIÓN FINAL HU5 - RED COMERCIAL INTEROPERABLE]")
print(f"======================================================")

print(f"• Cliente ({cliente.username}) -> Horas de Vida: {cliente.horas_de_vida} (Totalmente Protegidas) ")
print(f"• Cliente ({cliente.username}) -> Crédito Comercial: {cliente.saldo_comercial} (Listo para usar en la red) ") 
print(f"• Comercio A (nom_usuario_comercio1) -> Balance Neto: {comercio_A.saldo_comercial} (Deuda registrada por vuelto faltante) ")  #REEMPLAZAR 
print(f"• Comercio B (nom_usuario_comercio2) -> Balance Neto: {comercio_B.saldo_comercial} (Crédito absorbido por la compra) ")  #REEMPLAZAR
print(f"======================================================")

```
