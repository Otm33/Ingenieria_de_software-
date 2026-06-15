<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="topbar__inner">
        <nav class="nav nav--main" aria-label="Navegacion principal">
          <button
            v-if="!usuarioActual?.esComercio"
            class="nav__link nav__link--icon"
            type="button"
            @click="seccionActiva = 'cartelera'"
            title="Cartelera"
          >
            <span>Cartelera</span>
          </button>
          <button
            v-if="!usuarioActual?.esComercio"
            class="nav__link nav__link--icon"
            type="button"
            @click="seccionActiva = 'publicar'"
            title="Publicar"
          >
            <span>Publicar</span>
          </button>
          <button
            v-if="!usuarioActual?.esComercio"
            class="nav__link nav__link--icon"
            type="button"
            @click="seccionActiva = 'comunidad'"
            title="Comunidad"
          >
            <span>Comunidad</span>
          </button>
          <button
            v-if="!usuarioActual?.esComercio"
            class="nav__link nav__link--icon"
            type="button"
            @click="seccionActiva = 'impacto-social'"
            title="Impacto Social"
          >
            <span>Impacto Social</span>
          </button>
          <button class="nav__link nav__link--icon" type="button" @click="seccionActiva = 'red-comercial'" title="Red Comercial">
            <span>Red Comercial</span>
          </button>
        </nav>

        <nav v-if="usuarioActual?.esStaff || usuarioActual?.esSuperusuario" class="nav nav--admin" aria-label="Navegacion administrativa">
          <button class="nav__link" type="button" @click="seccionActiva = 'csv'">Usuarios CSV</button>
          <button class="nav__link" type="button" @click="seccionActiva = 'admin-impacto-social'">
            Gestión Impacto Social
          </button>
          <a class="nav__link" href="http://127.0.0.1:8000/admin/" target="_blank">Admin Django</a>
        </nav>

        <div v-if="usuarioActual" class="session-box">
          <button
            v-if="!usuarioActual.esComercio"
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

      <section v-else-if="!usuarioActual" class="auth-page">
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
              <button
                class="link-button"
                :class="{ 'link-button--active': tipoRegistroActivo === 'usuario' }"
                type="button"
                @click="mostrarRegistroUsuario"
              >
                No tengo cuenta
              </button>
              <button
                class="link-button"
                :class="{ 'link-button--active': tipoRegistroActivo === 'comercio' }"
                type="button"
                @click="mostrarRegistroComercio"
              >
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
        <Perfil v-else-if="seccionActiva === 'perfil'" @ir-red-comercial="seccionActiva = 'red-comercial'" />
        <Comunidad v-else-if="seccionActiva === 'comunidad'" />
        <ImpactoSocial v-else-if="seccionActiva === 'impacto-social'" />
        <RedComercial v-else-if="seccionActiva === 'red-comercial'" />
        <Register v-else-if="usuarioActual.esStaff && seccionActiva === 'registro'" />
        <AdminCSV v-else-if="usuarioActual.esStaff && seccionActiva === 'csv'" />
        <AdminImpactoSocial
          v-else-if="(usuarioActual.esStaff || usuarioActual.esSuperusuario) && seccionActiva === 'admin-impacto-social'"
        />
        <Cartelera v-else />
      </template>
    </main>

    <ModalNotificaciones
      v-model:visible="mostrarModalNotificaciones"
      :notificaciones="notificacionesVisibles"
      @realizar-trueque="abrirPropuestaDesdeNotificacion"
      @actualizado="cargarDatosHu4"
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
      v-model:visible="mostrarModalResena"
      :trueque-id="truequeResena?.id"
      :contraparte-nombre="truequeResena?.contraparteNombre"
      :estado-trueque="truequeResena?.estado"
      @enviada="onResenaEnviada"
    />
  </div>
</template>

<script setup>
import { computed, inject, onMounted, provide, reactive, ref, watch } from 'vue'
import AdminCSV from './views/AdminCSV.vue'
import AdminImpactoSocial from './views/AdminImpactoSocial.vue'
import Cartelera from './views/Cartelera.vue'
import Register from './views/Register.vue'
import Perfil from './views/Perfil.vue'
import Comunidad from './views/Comunidad.vue'
import ImpactoSocial from './views/ImpactoSocial.vue'
import RedComercial from './views/RedComercial.vue'
import ModalNotificaciones from './components/ModalNotificaciones.vue'
import ModalPropuesta from './components/ModalPropuesta.vue'
import ModalResena from './components/ModalResena.vue'

const authController = inject('authController')
const carteleraController = inject('carteleraController')
const truequeController = inject('truequeController')
const usuarioActual = ref(null)
const cargandoSesion = ref(true)
const procesandoLogin = ref(false)
const loginError = ref('')
const seccionActiva = ref('cartelera')
const tipoRegistroActivo = ref('')
const mensajeBienvenida = ref('')
const loginForm = reactive({ username: '', password: '' })

const seccionInicialParaUsuario = (usuario) => (usuario?.esComercio ? 'red-comercial' : 'cartelera')

const normalizarSeccionComercio = () => {
  if (usuarioActual.value?.esComercio && ['cartelera', 'publicar', 'comunidad', 'impacto-social'].includes(seccionActiva.value)) {
    seccionActiva.value = 'red-comercial'
  }
}

const notificacionesVisibles = ref([])
const misTrueques = ref([])
const mostrarModalNotificaciones = ref(false)
const mostrarModalPropuesta = ref(false)
const mostrarModalResena = ref(false)
const truequeResena = ref(null)

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

const notificacionesAccionables = computed(() => notificacionesVisibles.value)

const obtenerContraparteNombre = (trueque) => {
  if (!usuarioActual.value) return ''
  if (Number(trueque.emisor) === Number(usuarioActual.value.id)) return trueque.receptor_nombre
  return trueque.emisor_nombre
}

let refrescarPerfilFn = null

const registrarRefrescarPerfil = (fn) => {
  refrescarPerfilFn = fn
}

const refrescarPerfil = async () => {
  if (refrescarPerfilFn) {
    await refrescarPerfilFn()
  }
}

const revisarResenaPendiente = () => {
  if (mostrarModalResena.value || mostrarModalNotificaciones.value) return

  const pendiente = misTrueques.value.find((trueque) => trueque.pendiente_resena)
  if (pendiente) {
    abrirModalResena(pendiente)
    return
  }
  truequeResena.value = null
}

const cargarDatosHu4 = async (opciones = {}) => {
  const { omitirModalesAutomaticos = false } = opciones
  if (!usuarioActual.value || usuarioActual.value.esComercio) return

  try {
    const datos = await truequeController.cargarDatosHu4(carteleraController)

    misTrueques.value = datos.trueques || []
    notificacionesVisibles.value = datos.notificaciones || []

    if (!omitirModalesAutomaticos) {
      if (notificacionesVisibles.value.length && !mostrarModalPropuesta.value && !mostrarModalNotificaciones.value) {
        mostrarModalNotificaciones.value = true
      }
      revisarResenaPendiente()
    }

    return { misPublicaciones: datos.misPublicaciones }
  } catch {
    notificacionesVisibles.value = []
    misTrueques.value = []
  }
}

const abrirModalPropuesta = async (config) => {
  const misPublicaciones = config.misPublicaciones?.length
    ? config.misPublicaciones
    : await carteleraController.obtenerMisPublicaciones()

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
  if (!usuarioActual.value || !trueque) return

  const soyEmisor = Number(trueque.emisor) === Number(usuarioActual.value.id)
  const contraparteId = soyEmisor ? trueque.receptor : trueque.emisor
  const contraparteNombre = obtenerContraparteNombre(trueque)
  const misPublicaciones = await carteleraController.obtenerMisPublicaciones()
  let publicacionesVecino = []

  try {
    const perfil = await authController.obtenerPerfilUsuario(contraparteId)
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
    const perfil = await authController.obtenerPerfilUsuario(notif.remitente_id)
    publicacionesVecino = perfil.publicaciones || []
  } catch {
    publicacionesVecino = []
  }

  await abrirModalPropuesta({
    receptorId: notif.remitente_id,
    receptorNombre: notif.remitente_nombre,
    misPublicaciones: await carteleraController.obtenerMisPublicaciones(),
    publicacionesVecino,
    truequeIdOrigen: notif.trueque_id || null,
  })
}

const abrirPanelNotificaciones = async () => {
  await cargarDatosHu4()
  mostrarModalNotificaciones.value = true
}

const onPropuestaCreada = async () => {
  const truequeId = propuestaConfig.truequeIdOrigen
  if (truequeId) {
    try {
      await truequeController.marcarNotificacionesTruequeLeidas(truequeId)
    } catch {
      // Ignorar errores al marcar notificaciones del match.
    }
  }
  propuestaConfig.truequeIdOrigen = null
  await cargarDatosHu4()
}

const onResenaEnviada = async () => {
  mostrarModalResena.value = false
  truequeResena.value = null
  await cargarDatosHu4()
  await refrescarPerfil()
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
  refrescarPerfil,
  misTrueques,
  usuarioActualId: computed(() => usuarioActual.value?.id ?? null),
})

const cargarSesion = async () => {
  try {
    usuarioActual.value = await authController.obtenerSesionActual()
    if (usuarioActual.value) {
      seccionActiva.value = seccionInicialParaUsuario(usuarioActual.value)
      normalizarSeccionComercio()
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
    usuarioActual.value = await authController.iniciarSesion(loginForm)
    seccionActiva.value = seccionInicialParaUsuario(usuarioActual.value)
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
      usuarioActual.value = await authController.procesarSesionPostRegistro(credenciales)

      if (credenciales.esComercio) {
        mensajeBienvenida.value = '¡Bienvenido, Comercio Afiliado! Ya puedes emitir vuelto comercial en la Red Comercial.'
        seccionActiva.value = 'red-comercial'
      } else {
        mensajeBienvenida.value = '¡Bienvenido, Miembro Activo! Tu perfil y primer talento ya están publicados en la comunidad.'
        seccionActiva.value = 'perfil'
      }

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
  await authController.cerrarSesion()
  usuarioActual.value = null
  seccionActiva.value = 'cartelera'
  notificacionesVisibles.value = []
  misTrueques.value = []
  mostrarModalNotificaciones.value = false
  mostrarModalPropuesta.value = false
  mostrarModalResena.value = false
}

watch(seccionActiva, async (nueva) => {
  if (usuarioActual.value && !usuarioActual.value.esComercio && ['perfil', 'comunidad', 'cartelera'].includes(nueva)) {
    await cargarDatosHu4()
  }
})

watch(mostrarModalPropuesta, (visible) => {
  if (!visible) {
    limpiarPropuestaConfig()
  }
})

onMounted(cargarSesion)
</script>
