<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="topbar__inner">
        <a class="brand" href="/" aria-label="Ir al inicio">
          <img class="brand__logo" src="/tutrueque-logo.png" alt="TuTrueque" />
          <div>
            <h1 class="brand__title">TuTrueque</h1>
            <p class="brand__subtitle">Intercambio comunitario de servicios</p>
          </div>
        </a>

        <nav v-if="usuarioActual?.esAdmin" class="nav" aria-label="Navegacion administrativa">
          <!-- CAMBIO VISTA: estas opciones solo se renderizan para staff o superusuario. -->
          <button class="nav__link" type="button" @click="seccionActiva = 'cartelera'">Cartelera</button>
          <button class="nav__link" type="button" @click="seccionActiva = 'registro'">Registro</button>
          <button class="nav__link" type="button" @click="seccionActiva = 'csv'">Usuarios CSV</button>
          <a class="nav__link" href="http://127.0.0.1:8000/admin/">Admin Django</a>
        </nav>

        <div v-if="usuarioActual" class="session-box">
          <span>{{ usuarioActual.nombreReal || usuarioActual.username }}</span>
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
          </form>
        </section>

        <!-- CAMBIO VISTA: si no hay sesion, el registro aparece debajo del login en la misma pagina. -->
        <Register @registered="iniciarSesionDespuesDeRegistro" />
      </section>

      <template v-else>
        <Cartelera v-if="seccionActiva === 'cartelera'" />
        <Register v-else-if="usuarioActual.esAdmin && seccionActiva === 'registro'" />
        <AdminCSV v-else-if="usuarioActual.esAdmin && seccionActiva === 'csv'" />
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

const userController = inject('userController')
const usuarioActual = ref(null)
const cargandoSesion = ref(true)
const procesandoLogin = ref(false)
const loginError = ref('')
const seccionActiva = ref('cartelera')
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
    loginForm.username = ''
    loginForm.password = ''
  } catch (error) {
    loginError.value = error.message || 'No se pudo iniciar sesion.'
  } finally {
    procesandoLogin.value = false
  }
}

const iniciarSesionDespuesDeRegistro = async (credenciales) => {
  loginForm.username = credenciales.username
  loginForm.password = credenciales.password
  await iniciarSesion()
}

const cerrarSesion = async () => {
  await userController.cerrarSesion()
  usuarioActual.value = null
  seccionActiva.value = 'cartelera'
}

onMounted(cargarSesion)
</script>
