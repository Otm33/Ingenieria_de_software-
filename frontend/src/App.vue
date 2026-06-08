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
        </nav>

        <nav v-if="usuarioActual?.esStaff || usuarioActual?.esSuperusuario" class="nav nav--admin" aria-label="Navegacion administrativa">
          <button class="nav__link" type="button" @click="seccionActiva = 'csv'">Usuarios CSV</button>
          <a class="nav__link" href="http://127.0.0.1:8000/admin/" target="_blank">Admin Django</a>
        </nav>

        <div v-if="usuarioActual" class="session-box">
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
            <!-- CAMBIO AUTH: el login aparece primero al entrar a http://127.0.0.1:5173/. -->
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
        <Register v-else-if="usuarioActual.esStaff && seccionActiva === 'registro'" />
        <AdminCSV v-else-if="usuarioActual.esStaff && seccionActiva === 'csv'" />
        <Cartelera v-else />
      </template>
    </main>
  </div>
</template>

<script setup>
import { inject, onMounted, reactive, ref } from 'vue'
import AdminCSV from './views/AdminCSV.vue'
import Cartelera from './views/Cartelera.vue'
import Register from './views/Register.vue'
import Perfil from './views/Perfil.vue'
import Comunidad from './views/Comunidad.vue'

const userController = inject('userController')
const usuarioActual = ref(null)
const cargandoSesion = ref(true)
const procesandoLogin = ref(false)
const loginError = ref('')
const seccionActiva = ref('cartelera')
const tipoRegistroActivo = ref('')
const mensajeBienvenida = ref('')
const loginForm = reactive({ username: '', password: '' })

const cargarSesion = async () => {
  try {
    // CAMBIO AUTH: la app decide que mostrar segun la sesion real de Django.
    usuarioActual.value = await userController.obtenerSesionActual()
  } finally {
    cargandoSesion.value = false
  }
}

const iniciarSesion = async () => {
  procesandoLogin.value = true
  loginError.value = ''

  try {
    // CAMBIO AUTH: despues de iniciar sesion se muestra la cartelera normal.
    usuarioActual.value = await userController.iniciarSesion(loginForm)
    seccionActiva.value = 'cartelera'
    tipoRegistroActivo.value = ''
    loginForm.username = ''
    loginForm.password = ''
  } catch (error) {
    loginError.value = error.message || 'No se pudo iniciar sesion.'
  } finally {
    procesandoLogin.value = false
  }
}

const iniciarSesionDespuesDeRegistro = async (credenciales) => {
  try {
    if (credenciales.esNuevoMiembro) {
      usuarioActual.value = await userController.obtenerSesionActual()
        || await userController.iniciarSesion(credenciales)
      mensajeBienvenida.value = '¡Bienvenido, Miembro Activo! Tu perfil y primer talento ya están publicados en la comunidad.'
      seccionActiva.value = 'perfil'
      tipoRegistroActivo.value = ''
      loginForm.username = ''
      loginForm.password = ''
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
  await userController.cerrarSesion()
  usuarioActual.value = null
  seccionActiva.value = 'cartelera'
}

onMounted(cargarSesion)
</script>
