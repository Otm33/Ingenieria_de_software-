# GUION DEL VIDEO — Táctica "Autorizar Actores"

---

## PARTE 1: ¿Qué dice la profe y qué dice el libro?

### Lo que pide la profe

La profesora Marlene asignó:

> **Equipo 5 — Seguridad: Táctica "Autorizar Actores"**
> - **Contexto SIVC**: Solo los participantes de un trueque específico pueden marcar una transacción como "finalizada con éxito".
> - **Implementación**: Lógica de control de acceso donde el botón de "Completar Trueque" esté habilitado **única y estrictamente** para el ID del usuario que recibió el servicio, validando su identidad antes de procesar el cambio.
> - **Métrica**: Porcentaje de accesos no autorizados bloqueados.

Resumido: **3 cosas obligatorias**:
1. ✅ Que solo los participantes puedan finalizar
2. ✅ Que el botón solo esté habilitado para quien recibió el servicio
3. ✅ Medir el % de accesos no autorizados bloqueados

### Lo que dice el libro

**Libro**: *Software Architecture in Practice*, Bass, Clements & Kazman, 4ª edición (2023), Capítulo 9: Security.

La táctica **"Authorize Actors"** pertenece al grupo **"Resist Attacks"** (Resistir Ataques). El libro dice:

> "Authorize Actors asegura que un actor autenticado tiene los permisos necesarios para acceder y modificar datos o servicios."

Se basa en responder 3 preguntas antes de cada operación:
- **¿Quién?** → El usuario que hace la petición (su ID)
- **¿Qué quiere hacer?** → Finalizar un trueque o ingresar un código
- **¿Sobre qué recurso?** → El trueque específico

El libro también define el escenario de calidad:

| Elemento | En TuTrueque |
|----------|-------------|
| **Estímulo** | Un usuario intenta finalizar un trueque |
| **Respuesta** | El sistema verifica si es participante y autoriza o bloquea |
| **Medida** | % de accesos no autorizados bloqueados + tiempo de detección |

---

## PARTE 2: ¿Qué dice el código y dónde se implementa?

### # AUTORIZAR ACTORES — Qué hace con respecto a lo pedido

La táctica se implementa en **2 puntos de control** del backend:

| Punto de control | Función que protege | ¿Qué verifica? |
|-----------------|---------------------|-----------------|
| **Finalizar trueque** | `autorizar_actor_finalizacion()` | ¿El usuario es emisor o receptor de este trueque? ¿El trueque está en curso? |
| **Ingresar código** | `autorizar_actor_codigo()` | Lo mismo + ¿El usuario es el **receptor** (no el emisor)? |

---

### Archivo 1: Las funciones de autorización (LÓGICA PURA)

📂 **Ubicación**: [trueque.py (negocio)](file:///c:/Users/Luigi/Downloads/Ingenieria_De_Software_Tu-Trueque/backend/comunidad/negocio/trueque.py#L115-L190)

**`autorizar_actor_finalizacion()`** — Líneas 121-152:

```python
def autorizar_actor_finalizacion(trueque, usuario):
    uid = getattr(usuario, 'id', None)
    emisor_id = getattr(trueque, 'emisor_id', None)
    receptor_id = getattr(trueque, 'receptor_id', None)

    # REGLA 1: ¿Es participante?
    if uid not in (emisor_id, receptor_id):
        return False, "Acceso denegado: no es participante"

    # REGLA 2: ¿El trueque está en un estado válido?
    if estado not in ('ACEPTADO', 'EN_CURSO'):
        return False, "Acceso denegado: estado incorrecto"

    return True, "Autorizado"
```

**`autorizar_actor_codigo()`** — Líneas 155-189:

```python
def autorizar_actor_codigo(trueque, usuario):
    # ... mismas verificaciones ...

    # REGLA EXTRA: Solo el RECEPTOR puede ingresar el código
    if uid == emisor_id:
        return False, "solo el receptor puede introducir el código"

    return True, "Autorizado: es receptor"
```

**¿POR QUÉ se hace así?**
- Son funciones **puras**: no tocan la base de datos, solo comparan IDs. Esto cumple con lo que el libro llama "decisión de diseño de un solo paso".
- Retornan `(bool, motivo)` para que el motivo se registre en el audit log.

---

### Archivo 2: Donde se APLICA la autorización (SERVICIO)

📂 **Ubicación**: [trueque.py (servicio)](file:///c:/Users/Luigi/Downloads/Ingenieria_De_Software_Tu-Trueque/backend/comunidad/services/trueque.py#L192-L223)

En el método `finalizar_trueque()` — Líneas 203-223:

```python
# Autorizar Actores: verificar permisos y medir tiempo
t_inicio = time.perf_counter()                              # ← Arranca cronómetro
autorizado, motivo = autorizar_actor_finalizacion(trueque, usuario)  # ← TÁCTICA
t_deteccion = (time.perf_counter() - t_inicio) * 1000       # ← Tiempo en ms

# Registrar intento en el audit log (SIEMPRE, autorizado o no)
registrar_intento_autorizacion(
    usuario_id=uid, trueque_id=trueque_id,
    accion='FINALIZAR_TRUEQUE',
    resultado=AUTORIZADO if autorizado else BLOQUEADO,
    motivo=motivo,
    tiempo_deteccion_ms=t_deteccion,
)

if not autorizado:
    raise BusinessError(motivo, status_code=403)  # ← HTTP 403 FORBIDDEN
```

Y en `validar_codigo_finalizacion()` — Líneas 309-328 (mismo patrón pero usa `autorizar_actor_codigo`).

**¿POR QUÉ se mide el tiempo?**
- La profe pide medir una **métrica**. El libro dice que el "tiempo de detección" es una medida de respuesta válida.
- Usamos `time.perf_counter()` porque tiene precisión de nanosegundos.

---

### Archivo 3: El Audit Log (REGISTRO Y MÉTRICAS)

📂 **Ubicación**: [audit_log.py](file:///c:/Users/Luigi/Downloads/Ingenieria_De_Software_Tu-Trueque/backend/comunidad/negocio/audit_log.py)

Cada intento de acceso se guarda con:
- `timestamp` — cuándo ocurrió
- `usuario_id` — quién intentó
- `trueque_id` — a qué trueque
- `accion` — FINALIZAR_TRUEQUE o VALIDAR_CODIGO
- `resultado` — AUTORIZADO o BLOQUEADO
- `motivo` — por qué
- `tiempo_deteccion_ms` — cuánto tardó el sistema en decidir

La **métrica principal** se calcula así:

```python
porcentaje_bloqueados = (bloqueados / total_intentos) * 100
```

Y la **efectividad**:

```
Efectividad = accesos ilegítimos bloqueados / total de accesos ilegítimos × 100
→ En nuestro sistema = 100% (todos los ilegítimos se bloquean)
```

---

### Archivo 4: Los Tests (SIMULACIÓN)

📂 **Ubicación**: [test_autorizacion.py](file:///c:/Users/Luigi/Downloads/Ingenieria_De_Software_Tu-Trueque/backend/comunidad/tests/test_autorizacion.py)

8 tests unitarios + 1 simulación completa que ejecuta 5 intentos y muestra las métricas.

Se ejecuta con:
```bash
python manage.py test backend.comunidad.tests.test_autorizacion -v 2
```

---

### Archivo 5: Endpoints de métricas

📂 **Ubicación**: [seguridad_metricas_router.py](file:///c:/Users/Luigi/Downloads/Ingenieria_De_Software_Tu-Trueque/backend/comunidad/routers/seguridad_metricas_router.py)

| Endpoint | Qué da |
|----------|--------|
| `GET /api/seguridad/metricas-autorizacion/` | El % de bloqueados y tiempo promedio |
| `GET /api/seguridad/historial-autorizacion/` | Cada intento individual |

---

### Archivo 6: Frontend (BOTONES CONTROLADOS)

📂 **Ubicación**: [Perfil.vue](file:///c:/Users/Luigi/Downloads/Ingenieria_De_Software_Tu-Trueque/frontend/src/views/Perfil.vue#L506-L547)

```html
<!-- Solo aparece si el trueque está EN_CURSO -->
<div v-if="trueque.estado === 'EN_CURSO' && trueque.codigo_confirmacion">

    <!-- EMISOR: ve el código pero NO puede ingresarlo -->
    <div v-if="Number(trueque.emisor) === Number(datosPerfil?.usuario?.id)">
        Código: {{ trueque.codigo_confirmacion }}
        "Comparte este código con el receptor"
    </div>

    <!-- RECEPTOR: puede ingresar el código pero NO lo ve -->
    <div v-else>
        "Ingresa el código que te compartió el emisor"
        <input v-model="codigoIngresado" />
        <button @click="validarCodigo(trueque)">Validar</button>
    </div>
</div>

<!-- El botón de confirmar solo aparece si el backend dice que puede -->
<button v-if="trueque.puede_confirmar">
    Confirmar finalización
</button>
```

---

## PARTE 3: ¿Qué mostrar en la interfaz para demostrar que funciona?

### Demostración 1: El emisor ve el código pero no el input
- Iniciar sesión como el **emisor** de un trueque EN_CURSO
- Ir a "Mi Perfil" → sección de trueques
- **Mostrar**: aparece el código de confirmación en texto visible
- **Mostrar**: NO hay campo de input para ingresar código (solo dice "Comparte este código con...")
- **Decir**: "Como emisor, yo tengo el código pero NO puedo ingresarlo yo mismo"

### Demostración 2: El receptor ve el input pero no el código
- Iniciar sesión como el **receptor** del mismo trueque
- Ir a "Mi Perfil" → sección de trueques
- **Mostrar**: aparece el mensaje "Ingresa el código que te compartió [emisor]"
- **Mostrar**: hay un botón "Ingresar código" que abre el campo de input
- **Mostrar**: NO se ve el código en ningún lado
- **Decir**: "Como receptor, yo puedo ingresar el código pero no lo veo, tiene que dármelo el emisor"

### Demostración 3: Ejecutar los tests (simulación de fallo)
- En la terminal, ejecutar: `python manage.py test backend.comunidad.tests.test_autorizacion -v 2`
- **Mostrar**: la salida con los 8 tests pasando
- **Mostrar**: el bloque de métricas que imprime la simulación completa:
```
============================================================
RESULTADO — Autorizar Actores
============================================================
Total intentos:               5
Autorizados:                  2
Bloqueados:                   3
% bloqueados:                 60.0%
Tiempo promedio detección:    0.18ms
Efectividad:                  100.0% de accesos no autorizados bloqueados
============================================================
```

### Demostración 4 (opcional): Forzar acceso por API
- Usar Postman o el navegador para hacer un POST directo a `/api/trueques/{id}/finalizar/` con un usuario que NO es participante
- **Mostrar**: respuesta HTTP 403 Forbidden con el mensaje "Acceso denegado"
- **Decir**: "Aunque alguien salte la interfaz y envíe la petición directamente, el backend lo bloquea"

---

## PARTE 4: GUION — Lo que debo decir en el video

---

### 🎬 INTRO (0:00 - 1:00)

> "Hola, somos el Equipo 5, equipo de Seguridad. Nos tocó la táctica **Autorizar Actores** del libro *Software Architecture in Practice* de Bass, Clements y Kazman, edición 2023."
>
> "Vamos a explicar qué es esta táctica, cómo la implementamos en nuestro proyecto TuTrueque, y vamos a demostrar que funciona con una simulación en vivo y midiendo la métrica que nos pidieron."

---

### 📖 EXPLICACIÓN TEÓRICA (1:00 - 3:30)

> "Según el libro, en el Capítulo 9 de Seguridad, las tácticas de seguridad se dividen en tres grupos: detectar ataques, resistir ataques y reaccionar a ataques."
>
> "Autorizar Actores pertenece al grupo de **Resistir Ataques**. Lo que dice es: antes de que un usuario pueda hacer algo en el sistema, hay que verificar que tiene los permisos necesarios. Se responden tres preguntas: **¿Quién es?**, **¿Qué quiere hacer?** y **¿Sobre qué recurso?**"
>
> "En nuestro contexto del SIVC, lo que dice la asignación es: **solo los participantes de un trueque específico pueden marcarlo como finalizado**. Y más específicamente, el botón de Completar Trueque debe estar habilitado **solo para el usuario que recibió el servicio**, o sea, el receptor."
>
> "La métrica que debemos medir es el **porcentaje de accesos no autorizados bloqueados**."

---

### 💻 MOSTRAR EL CÓDIGO (3:30 - 7:00)

> "Ahora les voy a mostrar cómo implementamos esto en el código."

**(Abrir `backend/comunidad/negocio/trueque.py`, líneas 115-190)**

> "Primero, tenemos dos funciones de autorización. Son funciones **puras**, o sea, no tocan la base de datos, solo comparan IDs."
>
> "La primera es `autorizar_actor_finalizacion`. Lo que hace es: recibe el trueque y el usuario, saca el ID del usuario, y verifica dos cosas: **uno**, que el usuario sea el emisor o el receptor del trueque, o sea que sea participante. **Dos**, que el trueque esté en estado ACEPTADO o EN_CURSO. Si alguna de las dos falla, retorna `False` con un motivo explicando por qué se bloqueó."
>
> "La segunda es `autorizar_actor_codigo`, que es más estricta. Además de ser participante, verifica que el usuario sea el **receptor**, no el emisor. ¿Por qué? Porque el emisor es quien tiene el código. Si él pudiera ingresarlo él mismo, no tendría sentido la verificación. El receptor tiene que recibirlo del emisor como prueba de que el servicio se completó."

**(Abrir `backend/comunidad/services/trueque.py`, líneas 203-223)**

> "Ahora, ¿dónde se usan estas funciones? Aquí en el servicio, en el método `finalizar_trueque`. Antes de hacer cualquier cosa, se llama a `autorizar_actor_finalizacion`. Además, medimos el tiempo con `time.perf_counter` para saber cuántos milisegundos tarda el sistema en tomar la decisión."
>
> "Cada intento se registra en el **audit log**, sea autorizado o bloqueado. Y si no está autorizado, se lanza un error HTTP 403 Forbidden. Lo mismo pasa en `validar_codigo_finalizacion` con `autorizar_actor_codigo`."

**(Abrir `backend/comunidad/negocio/audit_log.py`)**

> "El audit log es un registro tipo Singleton que guarda cada intento con su timestamp, quién fue, qué trueque, qué acción, si fue autorizado o bloqueado, el motivo y el tiempo de detección en milisegundos. Después calcula las métricas: el total de intentos, cuántos se autorizaron, cuántos se bloquearon, el porcentaje y el tiempo promedio."

---

### 🖥️ MOSTRAR LA INTERFAZ (7:00 - 9:30)

> "Ahora les voy a mostrar cómo se ve esto en la interfaz."

**(Iniciar sesión como EMISOR, ir a Mi Perfil)**

> "Estoy logueado como el emisor, el que ofreció el servicio. Aquí en mi perfil veo el trueque en estado EN_CURSO. Fíjense que me aparece el **código de confirmación** visible, y me dice 'Comparte este código con el receptor'. Pero **no hay ningún campo** para que yo ingrese un código. Yo lo veo, pero no puedo usarlo."

**(Iniciar sesión como RECEPTOR, ir a Mi Perfil)**

> "Ahora entro como el receptor, el que recibió el servicio. Mismo trueque, pero fíjense la diferencia: a mí me dice 'Ingresa el código que te compartió [nombre del emisor]' y tengo un botón 'Ingresar código'. **Yo no veo el código**, tiene que dármelo el emisor en persona o por otro medio. Esto es la táctica Autorizar Actores aplicada: cada usuario solo ve y puede hacer lo que le corresponde según su rol."

**(Mostrar que el botón "Confirmar finalización" solo aparece si `puede_confirmar` es true)**

> "Y el botón de Confirmar finalización solo aparece si el backend validó que este usuario es participante y aún no ha confirmado. Si no eres participante, ni siquiera ves el trueque."

---

### 🧪 SIMULACIÓN EN VIVO Y MÉTRICAS (9:30 - 13:00)

> "Ahora vamos a correr la simulación. Tenemos tests automatizados que simulan 5 intentos de acceso para medir la métrica."

**(Ejecutar en terminal: `python manage.py test backend.comunidad.tests.test_autorizacion -v 2`)**

> "Ejecutamos los tests... y vemos que los 8 tests unitarios pasan. Pero lo importante es la simulación completa que simula estos 5 escenarios:"

| # | Quién intenta | Qué intenta | Resultado |
|---|---------------|-------------|-----------|
| 1 | Usuario 3 (intruso) | Finalizar trueque | ❌ BLOQUEADO — No es participante |
| 2 | Usuario 4 (intruso) | Ingresar código | ❌ BLOQUEADO — No es participante |
| 3 | Usuario 1 (emisor) | Ingresar código | ❌ BLOQUEADO — Es emisor, no receptor |
| 4 | Usuario 2 (receptor) | Finalizar trueque | ✅ AUTORIZADO |
| 5 | Usuario 2 (receptor) | Ingresar código | ✅ AUTORIZADO |

> "Fíjense en el caso 3: el emisor sí es participante del trueque, pero intenta ingresar el código. Se le bloquea porque solo el receptor puede hacerlo. Esto es exactamente lo que pide la asignación: el botón está habilitado **solo para quien recibió el servicio**."

**(Mostrar la salida de métricas)**

> "Y aquí están las métricas:"
>
> - Total de intentos: **5**
> - Autorizados: **2** (los legítimos)
> - Bloqueados: **3** (los ilegítimos)
> - Porcentaje bloqueados: **60%** del total
> - Tiempo promedio de detección: **~0.18 milisegundos**
> - **Efectividad: 100%** — De los 3 intentos que NO debían pasar, los 3 fueron bloqueados. Cero falsos negativos.
>
> "El 60% no significa que el sistema falla el 40%. El 60% son los intentos ilegítimos que se bloquearon. El 40% son los accesos legítimos que se permitieron correctamente. Lo que importa es la efectividad: de todos los accesos que debían ser bloqueados, el 100% se bloqueó."

---

### 🏁 CONCLUSIÓN (13:00 - 15:00)

> "Para resumir:"
>
> "**Uno**: La táctica Autorizar Actores del libro de Bass, Clements y Kazman dice que antes de cada operación hay que verificar que el actor tiene los permisos necesarios. Nosotros lo implementamos verificando que el usuario sea participante del trueque y tenga el rol correcto."
>
> "**Dos**: La implementación tiene dos capas de seguridad. La primera en el **frontend**, donde los botones y campos de input solo aparecen según el rol del usuario. La segunda en el **backend**, donde las funciones `autorizar_actor_finalizacion` y `autorizar_actor_codigo` validan el acceso antes de procesar cualquier cambio, porque el frontend se puede saltar."
>
> "**Tres**: La métrica que nos pidieron es el porcentaje de accesos no autorizados bloqueados. Nuestro resultado es **100% de efectividad**: todos los accesos ilegítimos fueron bloqueados, con un tiempo de detección de menos de 1 milisegundo."
>
> "**Cuatro**: Todo queda registrado en un audit log con timestamp, usuario, acción, resultado y tiempo, lo que permite auditar la seguridad del sistema en cualquier momento."
>
> "Eso es todo por parte del equipo de Seguridad. Gracias."
