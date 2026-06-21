<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="topbar__inner">
        <nav class="nav nav--main" aria-label="Navegacion principal">
          <button class="nav__link nav__link--icon" type="button" @click="seccionActiva = 'cartelera'" title="Cartelera">
            <span>Cartelera</span>
          </button>
          <button class="nav__link nav__link--icon" type="button" @click="seccionActiva = 'publicar'" title="Publicar">
            <span>Publicar</span>
          </button>
          <button class="nav__link nav__link--icon" type="button" @click="seccionActiva = 'comunidad'" title="Comunidad">
            <span>Comunidad</span>
          </button>
          <button class="nav__link nav__link--icon" type="button" @click="seccionActiva = 'red-comercial'" title="Red Comercial">
            <span>Red Comercial</span>
          </button>
          <button class="nav__link nav__link--icon" type="button" @click="seccionActiva = 'impacto-social'" title="Impacto Social">
            <span>Impacto Social</span>
          </button>
        </nav>

        <nav v-if="authStore.usuarioActual?.esStaff || authStore.usuarioActual?.esSuperusuario" class="nav nav--admin" aria-label="Navegacion administrativa">
          <button class="nav__link" type="button" @click="seccionActiva = 'csv'">Usuarios CSV</button>
          <button class="nav__link" type="button" @click="seccionActiva = 'admin-panel'">Admin</button>
        </nav>

        <div v-if="authStore.usuarioActual" class="session-box">
          <button
            class="nav__link nav__link--icon nav__link--notificaciones"
            type="button"
            title="Notificaciones"
            @click="abrirPanelNotificaciones"
          >
            <span>Notificaciones</span>
            <span v-if="notificacionesAccionables.length" class="nav-badge">
              {{ notificacionesAccionables.length }}
            </span>
          </button>
          <button class="nav__link nav__link--icon" type="button" @click="seccionActiva = 'perfil'" title="Mi Perfil">
            <span>Perfil</span>
          </button>
          <button class="button button--secondary" type="button" @click="cerrarSesion">Salir</button>
        </div>
      </div>
    </header>

    <main>
      <section v-if="cargandoSesion" class="page">
        <div class="loading-state">Verificando sesion...</div>
      </section>

      <section v-else-if="!authStore.usuarioActual" class="auth-page">
        <section class="auth-panel">
          <div class="panel__header">
            <h2 class="panel__title">Iniciar sesion</h2>
          </div>
          <form class="panel__body" @submit.prevent="iniciarSesion">
            <div class="form-grid">
              <div class="form-group">
                <label for="login_username">Usuario</label>
                <input id="login_username" v-model="loginForm.username" class="input" type="text" required />
              </div>
              <div class="form-group">
                <label for="login_password">Contrasena</label>
                <input id="login_password" v-model="loginForm.password" class="input" type="password" required />
              </div>
            </div>

            <div class="form-actions">
              <button class="button button--primary" type="submit" :disabled="procesandoLogin">
                {{ procesandoLogin ? 'Entrando...' : 'Entrar' }}
              </button>
            </div>

            <p v-if="loginError" class="alert alert--error">{{ loginError }}</p>

            <div class="auth-links">
              <button class="link-button" type="button" @click="mostrarRegistroUsuario">
                No tengo cuenta
              </button>
              <button class="link-button" type="button" @click="mostrarRegistroComercio">
                ¿Usted es un comercio?
              </button>
            </div>
          </form>
        </section>

        <Register
          v-if="tipoRegistroActivo"
          :key="tipoRegistroActivo"
          :es-comercio="tipoRegistroActivo === 'comercio'"
          @registered="iniciarSesionDespuesDeRegistro"
        />
      </section>

      <template v-else>
        <p v-if="mensajeBienvenida" class="welcome-banner alert alert--success">
          {{ mensajeBienvenida }}
          <button class="welcome-banner__close" type="button" @click="mensajeBienvenida = ''" aria-label="Cerrar mensaje">
            ×
          </button>
        </p>

        <Cartelera v-if="seccionActiva === 'cartelera'" />
        <Cartelera v-else-if="seccionActiva === 'publicar'" :modo-publicar="true" @volver-cartelera="seccionActiva = 'cartelera'" />
        <Perfil v-else-if="seccionActiva === 'perfil'" />
        <Comunidad v-else-if="seccionActiva === 'comunidad'" />
        <RedComercial v-else-if="seccionActiva === 'red-comercial'" :usuario-actual="authStore.usuarioActual" />
        <AdminImpactoSocial v-else-if="(authStore.usuarioActual.esStaff || authStore.usuarioActual.esSuperusuario) && seccionActiva === 'impacto-social'" />
        <ImpactoSocial v-else-if="seccionActiva === 'impacto-social'" />
        <Register v-else-if="authStore.usuarioActual.esStaff && seccionActiva === 'registro'" />
        <AdminCSV v-else-if="(authStore.usuarioActual.esStaff || authStore.usuarioActual.esSuperusuario) && seccionActiva === 'csv'" />
        <AdminPanel v-else-if="(authStore.usuarioActual.esStaff || authStore.usuarioActual.esSuperusuario) && seccionActiva === 'admin-panel'" />
        <Cartelera v-else />
      </template>
    </main>

    <ModalNotificaciones
      v-model:visible="mostrarModalNotificaciones"
      :notificaciones="notificacionesVisibles"
      @realizar-trueque="abrirPropuestaDesdeNotificacion"
      @actualizado="cargarDatosHu4"
      @ir-a-resena="irAReseñaDesdeNotificacion"
    />

    <ModalPropuesta
      v-model:visible="mostrarModalPropuesta"
      :receptor-id="propuestaConfig.receptorId"
      :receptor-nombre="propuestaConfig.receptorNombre"
      :mis-publicaciones="propuestaConfig.misPublicaciones"
      :publicaciones-vecino="propuestaConfig.publicacionesVecino"
      :modo-propuesta="propuestaConfig.modoPropuesta"
      :tipo-mi-publicacion="propuestaConfig.tipoMiPublicacion"
      :tipo-vecino-publicacion="propuestaConfig.tipoVecinoPublicacion"
      :publicacion-emisor-preseleccionada="propuestaConfig.publicacionEmisorId"
      :publicacion-receptor-preseleccionada="propuestaConfig.publicacionReceptorId"
      @creada="onPropuestaCreada"
    />


    <ModalResena
      :visible="mostrarModalResena"
      :trueque-id="truequeResena?.id"
      :contraparte-nombre="truequeResena?.contraparteNombre"
      :estado-trueque="truequeResena?.estado"
      @update:visible="(val) => { if (!val) onResenaCerrada() }"
      @enviada="onResenaEnviada"
    />

  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, provide, reactive, ref, watch } from 'vue'
import { useAuthStore } from './stores/auth.js'
import { useCarteleraStore } from './stores/cartelera.js'
import { useComunidadStore } from './stores/comunidad.js'
import { useTruequeStore } from './stores/trueque.js'
import AdminCSV from './views/AdminCSV.vue'
import AdminImpactoSocial from './views/AdminImpactoSocial.vue'
import AdminPanel from './views/AdminPanel.vue'
import Cartelera from './views/Cartelera.vue'
import Register from './views/Register.vue'
import Perfil from './views/Perfil.vue'
import Comunidad from './views/Comunidad.vue'
import ImpactoSocial from './views/ImpactoSocial.vue'
import RedComercial from './views/RedComercial.vue'
import ModalNotificaciones from './components/ModalNotificaciones.vue'
import ModalPropuesta from './components/ModalPropuesta.vue'
import ModalResena from './components/ModalResena.vue'

const authStore = useAuthStore()
const carteleraStore = useCarteleraStore()
const comunidadStore = useComunidadStore()
const truequeStore = useTruequeStore()
const cargandoSesion = ref(true)
const procesandoLogin = computed(() => authStore.loading)
const loginError = computed(() => authStore.error)
// Recuperar la sección guardada en la sesión (hash URL o sessionStorage)
const _seccionInicial = (() => {
  const secciones = ['cartelera', 'publicar', 'comunidad', 'red-comercial', 'impacto-social', 'perfil', 'csv', 'admin-panel']
  const hash = window.location.hash.replace('#', '')
  if (secciones.includes(hash)) return hash
  const guardada = sessionStorage.getItem('tutruequeSección')
  if (secciones.includes(guardada)) return guardada
  return 'cartelera'
})()
const seccionActiva = ref(_seccionInicial)
const tipoRegistroActivo = ref('')
const mensajeBienvenida = ref('')
const loginForm = reactive({ username: '', password: '' })

const notificacionesVisibles = ref([])
const misTrueques = ref([])
const mostrarModalNotificaciones = ref(false)
const mostrarModalPropuesta = ref(false)
const mostrarModalResena = ref(false)
const truequeResena = ref(null)

// IDs de trueques cuya reseña fue pospuesta ("Más tarde") en esta sesión de navegación.
// Se usa solo en memoria (NO sessionStorage) para que al refrescar la página
// el modal vuelva a aparecer si el trueque aún tiene reseña pendiente.
const resenasPospuestas = ref(new Set())

const posponerResena = (truequeId) => {
  resenasPospuestas.value.add(String(truequeId))
}

const limpiarResenaPospuesta = (truequeId) => {
  resenasPospuestas.value.delete(String(truequeId))
}

const propuestaConfig = reactive({
  receptorId: null,
  receptorNombre: '',
  misPublicaciones: [],
  publicacionesVecino: [],
  modoPropuesta: '',
  tipoMiPublicacion: '',
  tipoVecinoPublicacion: '',
  publicacionEmisorId: null,
  publicacionReceptorId: null,
  truequeIdOrigen: null,
})

const limpiarPropuestaConfig = () => {
  Object.assign(propuestaConfig, {
    receptorId: null,
    receptorNombre: '',
    misPublicaciones: [],
    publicacionesVecino: [],
    modoPropuesta: '',
    tipoMiPublicacion: '',
    tipoVecinoPublicacion: '',
    publicacionEmisorId: null,
    publicacionReceptorId: null,
    truequeIdOrigen: null,
  })
}

const filtrarNotificacionesAccionables = (notificaciones) => (
  (notificaciones || []).filter((notif) => notif.estado === 'PENDIENTE')
)

const notificacionesAccionables = computed(() => notificacionesVisibles.value)

const obtenerContraparteNombre = (trueque) => {
  if (!authStore.usuarioActual) return ''
  if (Number(trueque.emisor) === Number(authStore.usuarioActual.id)) return trueque.receptor_nombre
  return trueque.emisor_nombre
}

let refrescarPerfilFn = null
let resenaEnviadaFn = null

const registrarRefrescarPerfil = (fn) => {
  refrescarPerfilFn = fn
}

const registrarResenaEnviada = (fn) => {
  resenaEnviadaFn = fn
}

const refrescarPerfil = async () => {
  if (refrescarPerfilFn) {
    await refrescarPerfilFn()
  }
}

const revisarResenaPendiente = () => {
  if (mostrarModalResena.value || mostrarModalNotificaciones.value) return

  // Solo abrir el modal si el trueque no fue pospuesto por el usuario en esta sesión
  const pendiente = misTrueques.value.find(
    (trueque) => trueque.pendiente_resena && !resenasPospuestas.value.has(String(trueque.id))
  )
  if (pendiente) {
    abrirModalResena(pendiente)
    return
  }
  truequeResena.value = null
}

const cargarDatosHu4 = async (opciones = {}) => {
  const { omitirModalesAutomaticos = false, omitirResenas = false } = opciones
  if (!authStore.usuarioActual) return

  try {
    const [notificacionesData, truequesData, truequesMultiplesData, misPublicaciones] = await Promise.all([
      truequeStore.cargarNotificaciones(false),
      truequeStore.obtenerMisTrueques(),
      truequeStore.obtenerMisTruequesMultiples(),
      carteleraStore.cargarMisPublicaciones(),
    ])

    // Combinar trueques simples y múltiples en un solo array
    const truequesSimples = (truequesData.trueques || []).map(t => ({ ...t, es_multiple: false }))
    const truequesMultiples = (truequesMultiplesData.trueques_multiple || []).map(t => ({ ...t, es_multiple: true }))
    misTrueques.value = [...truequesSimples, ...truequesMultiples]
    
    notificacionesVisibles.value = filtrarNotificacionesAccionables(
      notificacionesData.notificaciones,
    )

    const tieneResenaPendiente = misTrueques.value.some(
      (trueque) => trueque.pendiente_resena && !resenasPospuestas.value.has(String(trueque.id))
    )

    if (!omitirModalesAutomaticos && !tieneResenaPendiente) {
      // Login/navegación: mostrar notificaciones automáticamente
      if (notificacionesVisibles.value.length && !mostrarModalPropuesta.value && !mostrarModalNotificaciones.value) {
        mostrarModalNotificaciones.value = true
      }
    }

    // Siempre revisar reseñas pendientes (incluido durante polling)
    // a menos que se indique explícitamente lo contrario
    if (!omitirResenas) {
      revisarResenaPendiente()
    }

    return { misPublicaciones }
  } catch {
    notificacionesVisibles.value = []
    misTrueques.value = []
  }
}

const abrirModalPropuesta = async (config) => {
  const misPublicaciones = config.misPublicaciones?.length
    ? config.misPublicaciones
    : await carteleraStore.cargarMisPublicaciones()

  Object.assign(propuestaConfig, {
    receptorId: config.receptorId,
    receptorNombre: config.receptorNombre || '',
    misPublicaciones,
    publicacionesVecino: config.publicacionesVecino || [],
    modoPropuesta: config.modoPropuesta || '',
    tipoMiPublicacion: config.tipoMiPublicacion || '',
    tipoVecinoPublicacion: config.tipoVecinoPublicacion || '',
    publicacionEmisorId: config.publicacionEmisorId || null,
    publicacionReceptorId: config.publicacionReceptorId || null,
    truequeIdOrigen: config.truequeIdOrigen || null,
  })
  mostrarModalPropuesta.value = true
}

const abrirModalPropuestaDesdeTrueque = async (trueque) => {
  if (!authStore.usuarioActual || !trueque) return

  const soyEmisor = Number(trueque.emisor) === Number(authStore.usuarioActual.id)
  const contraparteId = soyEmisor ? trueque.receptor : trueque.emisor
  const contraparteNombre = obtenerContraparteNombre(trueque)
  const misPublicaciones = await carteleraStore.cargarMisPublicaciones()
  let publicacionesVecino = []

  try {
    const perfil = await comunidadStore.cargarPerfilUsuario(contraparteId)
    publicacionesVecino = perfil.publicaciones || []
  } catch {
    publicacionesVecino = []
  }

  const miPublicacion = soyEmisor ? trueque.publicacion_emisor : trueque.publicacion_receptor
  const pubVecino = soyEmisor ? trueque.publicacion_receptor : trueque.publicacion_emisor

  await abrirModalPropuesta({
    receptorId: contraparteId,
    receptorNombre: contraparteNombre,
    misPublicaciones,
    publicacionesVecino,
    publicacionEmisorId: miPublicacion?.id || null,
    publicacionReceptorId: pubVecino?.id || null,
    tipoMiPublicacion: miPublicacion?.tipo || '',
    tipoVecinoPublicacion: pubVecino?.tipo || '',
    truequeIdOrigen: trueque.id,
  })
}

const abrirPropuestaDesdeNotificacion = async (notif) => {
  mostrarModalNotificaciones.value = false

  const trueque = misTrueques.value.find(
    (item) => Number(item.id) === Number(notif.trueque_id),
  )
  if (trueque) {
    await abrirModalPropuestaDesdeTrueque(trueque)
    return
  }

  let publicacionesVecino = []
  try {
    const perfil = await comunidadStore.cargarPerfilUsuario(notif.remitente_id)
    publicacionesVecino = perfil.publicaciones || []
  } catch {
    publicacionesVecino = []
  }

  await abrirModalPropuesta({
    receptorId: notif.remitente_id,
    receptorNombre: notif.remitente_nombre,
    misPublicaciones: await carteleraStore.cargarMisPublicaciones(),
    publicacionesVecino,
    truequeIdOrigen: notif.trueque_id || null,
  })
}

const irAReseñaDesdeNotificacion = async (notif) => {
  mostrarModalNotificaciones.value = false
  
  // Marcar la notificación como leída
  try {
    await truequeStore.marcarNotificacionLeida(notif.id)
  } catch {
    // Ignorar error al marcar como leída
  }
  
  // Si es trueque múltiple, navegar al perfil donde ya existe la interfaz de reseñas múltiples
  if (notif.trueque_multiple_id) {
    seccionActiva.value = 'perfil'
    await cargarDatosHu4({ omitirModalesAutomaticos: true })
    await refrescarPerfil()
    return
  }
  
  // Para trueques simples, buscar el trueque y abrir el modal
  const trueque = misTrueques.value.find(
    (item) => Number(item.id) === Number(notif.trueque_id) && !item.es_multiple
  )
  
  if (trueque && trueque.pendiente_resena) {
    abrirModalResena(trueque)
  } else {
    // Si no se encuentra, navegar al perfil
    seccionActiva.value = 'perfil'
    await cargarDatosHu4({ omitirModalesAutomaticos: true })
    await refrescarPerfil()
  }
}

const abrirPanelNotificaciones = async () => {
  await cargarDatosHu4()
  mostrarModalNotificaciones.value = true
}

const onPropuestaCreada = async () => {
  const truequeId = propuestaConfig.truequeIdOrigen
  if (truequeId) {
    try {
      await truequeStore.marcarNotificacionesTruequeLeidas(truequeId)
    } catch {
      // Ignorar errores al marcar notificaciones del match.
    }
  }
  propuestaConfig.truequeIdOrigen = null
  await cargarDatosHu4()
}

const onResenaEnviada = async () => {
  // Capturar el ID antes de limpiar el estado
  const truequeId = truequeResena.value?.id

  // Cerrar el modal inmediatamente
  mostrarModalResena.value = false
  truequeResena.value = null

  // Marcar temporalmente como pospuesto para que revisarResenaPendiente()
  // no vuelva a abrir el modal mientras recargamos datos del backend
  // (el backend puede tardar en reflejar que la reseña ya fue enviada)
  if (truequeId) {
    posponerResena(truequeId)
  }

  // Recargar datos SIN revisar reseñas automáticas para evitar reapertura
  await cargarDatosHu4({ omitirResenas: true })
  await refrescarPerfil()

  // Ahora que los datos están frescos, limpiar el pospuesto
  // El trueque ya no debería aparecer como pendiente_resena
  if (truequeId) {
    limpiarResenaPospuesta(truequeId)
  }

  if (resenaEnviadaFn) {
    await resenaEnviadaFn()
  }
}

const onResenaCerrada = () => {
  // El usuario cerró el modal sin enviar la reseña ("Más tarde")
  // Posponer para esta sesión y no volver a abrir automáticamente
  if (truequeResena.value?.id) {
    posponerResena(truequeResena.value.id)
  }
  mostrarModalResena.value = false
  truequeResena.value = null
}

const abrirModalResena = (trueque) => {
  truequeResena.value = {
    id: trueque.id,
    contraparteNombre: obtenerContraparteNombre(trueque),
    estado: trueque.estado,
  }
  mostrarModalResena.value = true
}

const abrirModalResenaPrioritario = (trueque) => {
  mostrarModalNotificaciones.value = false
  mostrarModalPropuesta.value = false
  abrirModalResena(trueque)
}

provide('hu4', {
  abrirModalPropuesta,
  abrirModalPropuestaDesdeTrueque,
  abrirModalResena,
  abrirModalResenaPrioritario,
  refrescarDatosHu4: cargarDatosHu4,
  registrarRefrescarPerfil,
  registrarResenaEnviada,
  refrescarPerfil,
  misTrueques,
  usuarioActualId: computed(() => authStore.usuarioActual?.id ?? null),
})

const cargarSesion = async () => {
  try {
    await authStore.obtenerSesionActual()
    if (authStore.usuarioActual) {
      await cargarDatosHu4()
    }
  } finally {
    cargandoSesion.value = false
  }
}

const iniciarSesion = async () => {
  procesandoLogin.value = true
  loginError.value = ''

  try {
    await authStore.iniciarSesion(loginForm)

    seccionActiva.value = 'cartelera'
    tipoRegistroActivo.value = ''
    loginForm.username = ''
    loginForm.password = ''
    await cargarDatosHu4()
  } catch (error) {
    loginError.value = error.message || 'No se pudo iniciar sesion.'
  } finally {
    procesandoLogin.value = false
  }
}

const iniciarSesionDespuesDeRegistro = async (credenciales) => {
  try {
    if (credenciales.esNuevoMiembro) {
      await authStore.obtenerSesionActual()
      if (!authStore.usuarioActual) {
        await authStore.iniciarSesion(credenciales)
      }
      mensajeBienvenida.value = '¡Bienvenido, Miembro Activo! Tu perfil y primer talento ya están publicados en la comunidad.'
      seccionActiva.value = 'perfil'
      tipoRegistroActivo.value = ''
      loginForm.username = ''
      loginForm.password = ''
      await cargarDatosHu4()
      return
    }

    loginForm.username = credenciales.username
    loginForm.password = credenciales.password
    await iniciarSesion()
  } catch (error) {
    loginError.value = error.message || 'No se pudo iniciar sesion despues del registro.'
  }
}

const mostrarRegistroUsuario = () => {
  tipoRegistroActivo.value = tipoRegistroActivo.value === 'usuario' ? '' : 'usuario'
}

const mostrarRegistroComercio = () => {
  tipoRegistroActivo.value = tipoRegistroActivo.value === 'comercio' ? '' : 'comercio'
}

const cerrarSesion = async () => {
  await authStore.cerrarSesion()
  seccionActiva.value = 'cartelera'
  sessionStorage.removeItem('tutruequeSección')
  window.location.hash = ''
  notificacionesVisibles.value = []
  misTrueques.value = []
  mostrarModalNotificaciones.value = false
  mostrarModalPropuesta.value = false
  mostrarModalResena.value = false
  resenasPospuestas.value = new Set()
}


watch(seccionActiva, async (nueva) => {
  // Persistir la pestaña activa en la URL y en sessionStorage
  window.location.hash = nueva
  sessionStorage.setItem('tutruequeSección', nueva)

  if (!authStore.usuarioActual) return

  // Refrescar datos al cambiar de sección
  await cargarDatosHu4({ omitirModalesAutomaticos: true })

  // Si navegamos al perfil, refrescarlo explícitamente
  if (nueva === 'perfil') {
    await refrescarPerfil()
  }
})

watch(mostrarModalPropuesta, (visible) => {
  if (!visible) {
    limpiarPropuestaConfig()
  }
})

onMounted(cargarSesion)

// Auto-refresh: recargar datos cada 30 segundos para mantener la página actualizada
let pollingInterval = null

const iniciarPolling = () => {
  if (pollingInterval) return
  pollingInterval = setInterval(async () => {
    if (authStore.usuarioActual && !mostrarModalResena.value && !mostrarModalPropuesta.value) {
      await cargarDatosHu4({ omitirModalesAutomaticos: true })
      // Si el usuario está en el perfil, refrescarlo también
      if (seccionActiva.value === 'perfil') {
        await refrescarPerfil()
      }
    }
  }, 15000)
}

const detenerPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
}

watch(() => authStore.usuarioActual, (usuario) => {
  if (usuario) {
    iniciarPolling()
  } else {
    detenerPolling()
  }
})

onMounted(() => {
  if (authStore.usuarioActual) iniciarPolling()
})

onUnmounted(detenerPolling)
</script>
