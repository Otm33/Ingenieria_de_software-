<template>
  <section class="page">
    <div class="page-header">
      <div>
        <p class="eyebrow">Administración</p>
        <h2 class="page-title">Gestión de Impacto Social</h2>
        <p class="page-description">
          Aprueba solicitudes, marca usuarios vulnerables o críticos y redistribuye horas del Fondo Comunitario.
        </p>
      </div>
    </div>

    <p v-if="!esAdmin" class="alert alert--error">
      {{ MENSAJE_SIN_PERMISOS_ADMIN }}
    </p>

    <template v-else>
      <div v-if="cargando" class="loading-state">Cargando panel administrativo...</div>
      <p v-else-if="error" class="alert alert--error">{{ error }}</p>

      <template v-else>
        <p v-if="mensajeGlobal" class="alert alert--success">{{ mensajeGlobal }}</p>

        <div class="metric-row metric-row--comunidad">
          <article class="metric">
            <span class="metric__value">{{ saldoFondo.toFixed(1) }}</span>
            <span class="metric__label">Saldo Fondo Comunitario</span>
          </article>
          <article class="metric">
            <span class="metric__value">{{ solicitudesPendientes.length }}</span>
            <span class="metric__label">Solicitudes pendientes</span>
          </article>
          <article class="metric">
            <span class="metric__value">{{ usuarios.length }}</span>
            <span class="metric__label">Usuarios gestionables</span>
          </article>
        </div>

        <section class="panel">
          <div class="panel__header">
            <h3 class="panel__title">Solicitudes pendientes de aprobación</h3>
            <p class="panel__hint panel__hint--inline">
              Valida que la causa corresponda al catálogo social y al contexto del solicitante.
            </p>
            <p class="panel__hint panel__hint--inline">
              Al aprobar, la causa será visible para donaciones y el solicitante quedará marcado como
              Usuario Vulnerable (si aún no lo estaba).
            </p>
          </div>
          <div class="panel__body">
            <div v-if="solicitudesPendientes.length" class="table-container">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Solicitante</th>
                    <th>Categoría</th>
                    <th>Necesidad</th>
                    <th>Descripción</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="solicitud in solicitudesPendientes" :key="solicitud.id">
                    <td>{{ solicitud.solicitanteNombre || '—' }}</td>
                    <td>{{ solicitud.categoria || '—' }}</td>
                    <td><strong>{{ solicitud.titulo }}</strong></td>
                    <td>{{ solicitud.descripcion }}</td>
                    <td class="acciones-celda">
                      <button
                        class="button button--primary button--compact"
                        type="button"
                        :disabled="procesandoSolicitudId === solicitud.id"
                        @click="aprobarSolicitud(solicitud.id)"
                      >
                        Aprobar
                      </button>
                      <button
                        class="button button--secondary button--compact"
                        type="button"
                        :disabled="procesandoSolicitudId === solicitud.id"
                        @click="rechazarSolicitud(solicitud.id)"
                      >
                        Rechazar
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty-state">No hay solicitudes pendientes de revisión.</div>
          </div>
        </section>

        <section class="panel">
          <div class="panel__header">
            <h3 class="panel__title">Usuarios y estado social</h3>
            <p class="panel__hint panel__hint--inline">
              Marca usuarios como Vulnerable o Crítico para priorizar apoyo y asignación desde el fondo.
            </p>
          </div>
          <div class="panel__body">
            <div v-if="usuarios.length" class="table-container">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Usuario</th>
                    <th>Horas de vida</th>
                    <th>Horas recibidas por donación</th>
                    <th>Estado social</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="usuario in usuarios" :key="usuario.id">
                    <td>
                      <strong>{{ usuario.nombreReal }}</strong>
                      <p class="panel__hint panel__hint--inline">@{{ usuario.username }}</p>
                    </td>
                    <td>{{ usuario.horasDeVida.toFixed(1) }}</td>
                    <td>{{ usuario.horasRecibidasDonacion.toFixed(1) }}</td>
                    <td>
                      <select
                        class="input input--compact"
                        :value="usuario.estadoSocial"
                        :disabled="procesandoUsuarioId === usuario.id"
                        @change="actualizarEstadoSocial(usuario, $event.target.value)"
                      >
                        <option value="NINGUNO">Ninguno</option>
                        <option value="VULNERABLE">Vulnerable</option>
                        <option value="CRITICO">Crítico</option>
                      </select>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty-state">No hay usuarios disponibles para gestionar.</div>
          </div>
        </section>

        <section class="panel">
          <div class="panel__header">
            <h3 class="panel__title">Asignar horas desde el Fondo Comunitario</h3>
          </div>
          <div class="panel__body">
            <p class="panel__hint">
              Solo usuarios marcados como Vulnerable o Crítico pueden recibir asignaciones del fondo.
            </p>

            <form class="form-grid" @submit.prevent="asignarDesdeFondo">
              <div class="form-group form-group--full">
                <label for="usuario_asignacion">Usuario receptor</label>
                <select
                  id="usuario_asignacion"
                  v-model.number="formAsignacion.usuarioId"
                  class="input"
                  required
                >
                  <option disabled :value="null">Selecciona un usuario vulnerable o crítico</option>
                  <option
                    v-for="usuario in usuariosAsignables"
                    :key="usuario.id"
                    :value="usuario.id"
                  >
                    {{ usuario.nombreReal }} — {{ etiquetaEstadoSocial(usuario.estadoSocial) }}
                  </option>
                </select>
                <p v-if="!usuariosAsignables.length" class="alert alert--info">
                  Marca al menos un usuario como Vulnerable o Crítico para habilitar asignaciones.
                </p>
              </div>
              <div class="form-group form-group--full">
                <label for="solicitud_asignacion">Solicitud aprobada del receptor</label>
                <select
                  id="solicitud_asignacion"
                  v-model.number="formAsignacion.solicitudId"
                  class="input"
                  required
                  :disabled="!formAsignacion.usuarioId"
                >
                  <option disabled :value="null">Selecciona la causa destino</option>
                  <option
                    v-for="solicitud in solicitudesReceptorAsignacion"
                    :key="solicitud.id"
                    :value="solicitud.id"
                  >
                    {{ solicitud.titulo }} ({{ solicitud.horasRecibidas.toFixed(1) }} h recibidas)
                  </option>
                </select>
                <p v-if="formAsignacion.usuarioId && !solicitudesReceptorAsignacion.length" class="alert alert--info">
                  El usuario seleccionado no tiene solicitudes aprobadas para acreditar horas solidarias.
                </p>
              </div>
              <div class="form-group">
                <label for="monto_asignacion">Monto en horas</label>
                <input
                  id="monto_asignacion"
                  v-model="formAsignacion.monto"
                  class="input"
                  type="number"
                  min="0.5"
                  step="0.1"
                  :max="saldoFondo > 0 ? saldoFondo : undefined"
                  required
                />
                <p class="panel__hint panel__hint--inline">
                  Saldo disponible en fondo: {{ saldoFondo.toFixed(1) }} h
                </p>
              </div>
              <div class="form-actions">
                <button
                  class="button button--primary"
                  type="submit"
                  :disabled="procesandoAsignacion || !puedeAsignar"
                >
                  {{ procesandoAsignacion ? 'Asignando...' : 'Asignar horas' }}
                </button>
              </div>
            </form>

            <p v-if="errorAsignacion" class="alert alert--error">{{ errorAsignacion }}</p>
            <p v-if="mensajeAsignacion" class="alert alert--success">{{ mensajeAsignacion }}</p>
          </div>
        </section>
      </template>
    </template>
  </section>
</template>

<script setup>
import { computed, inject, onMounted, reactive, ref, watch } from 'vue'
import {
  MENSAJE_SIN_PERMISOS_ADMIN,
  MENSAJE_SOLO_VULNERABLE_CRITICO,
  MENSAJE_SOLICITANTE_MARCADO_VULNERABLE,
  etiquetaEstadoSocial,
} from '../controllers/ImpactoSocialController.js'

const authController = inject('authController')
const impactoSocialController = inject('impactoSocialController')

const esAdmin = ref(false)
const cargando = ref(true)
const error = ref('')
const mensajeGlobal = ref('')
const saldoFondo = ref(0)
const solicitudesPendientes = ref([])
const solicitudesAprobadas = ref([])
const usuarios = ref([])

const procesandoSolicitudId = ref(null)
const procesandoUsuarioId = ref(null)
const procesandoAsignacion = ref(false)
const errorAsignacion = ref('')
const mensajeAsignacion = ref('')

const formAsignacion = reactive({
  usuarioId: null,
  solicitudId: null,
  monto: '',
})

const usuariosAsignables = computed(() => (
  usuarios.value.filter((usuario) => ['VULNERABLE', 'CRITICO'].includes(usuario.estadoSocial))
))

const solicitudesReceptorAsignacion = computed(() => {
  if (!formAsignacion.usuarioId) return []
  return solicitudesAprobadas.value.filter(
    (solicitud) => solicitud.solicitanteId === formAsignacion.usuarioId,
  )
})

const puedeAsignar = computed(() => (
  Boolean(formAsignacion.usuarioId)
  && Boolean(formAsignacion.solicitudId)
  && solicitudesReceptorAsignacion.value.length > 0
  && Number(formAsignacion.monto) >= 0.5
  && Number(formAsignacion.monto) <= saldoFondo.value
  && usuariosAsignables.value.length > 0
))

watch(() => formAsignacion.usuarioId, () => {
  formAsignacion.solicitudId = null
})

watch(solicitudesReceptorAsignacion, (lista) => {
  if (lista.length === 1) {
    formAsignacion.solicitudId = lista[0].id
  } else if (!lista.some((item) => item.id === formAsignacion.solicitudId)) {
    formAsignacion.solicitudId = null
  }
})

const verificarAdmin = async () => {
  const sesion = await authController.obtenerSesionActual()
  esAdmin.value = Boolean(sesion?.esStaff || sesion?.esSuperusuario)
}

const cargarDatos = async () => {
  if (!esAdmin.value) {
    cargando.value = false
    return
  }

  cargando.value = true
  error.value = ''
  mensajeGlobal.value = ''

  try {
    const [pendientes, listaUsuarios, fondo, aprobadas] = await Promise.all([
      impactoSocialController.obtenerSolicitudesPendientesAdmin(),
      impactoSocialController.obtenerUsuariosAdmin(),
      impactoSocialController.obtenerSaldoFondoAdmin(),
      impactoSocialController.obtenerSolicitudesAprobadas(),
    ])

    solicitudesPendientes.value = pendientes.solicitudes || []
    usuarios.value = listaUsuarios.usuarios || []
    saldoFondo.value = fondo.saldo || 0
    solicitudesAprobadas.value = aprobadas.solicitudes || []
  } catch (err) {
    error.value = err.message || 'No se pudo cargar el panel de impacto social.'
  } finally {
    cargando.value = false
  }
}

const aprobarSolicitud = async (solicitudId) => {
  procesandoSolicitudId.value = solicitudId
  mensajeGlobal.value = ''

  try {
    const respuesta = await impactoSocialController.aprobarSolicitudAdmin(solicitudId)
    mensajeGlobal.value = respuesta.mensaje || MENSAJE_SOLICITANTE_MARCADO_VULNERABLE
    await cargarDatos()
  } catch (err) {
    error.value = err.message || 'No se pudo aprobar la solicitud.'
  } finally {
    procesandoSolicitudId.value = null
  }
}

const rechazarSolicitud = async (solicitudId) => {
  procesandoSolicitudId.value = solicitudId
  mensajeGlobal.value = ''

  try {
    const respuesta = await impactoSocialController.rechazarSolicitudAdmin(solicitudId)
    mensajeGlobal.value = respuesta.mensaje
    await cargarDatos()
  } catch (err) {
    error.value = err.message || 'No se pudo rechazar la solicitud.'
  } finally {
    procesandoSolicitudId.value = null
  }
}

const actualizarEstadoSocial = async (usuario, nuevoEstado) => {
  if (usuario.estadoSocial === nuevoEstado) return

  procesandoUsuarioId.value = usuario.id
  mensajeGlobal.value = ''
  error.value = ''

  try {
    const respuesta = await impactoSocialController.actualizarEstadoSocialAdmin(usuario.id, nuevoEstado)
    usuario.estadoSocial = respuesta.usuario.estadoSocial
    mensajeGlobal.value = respuesta.mensaje
    if (formAsignacion.usuarioId && !usuariosAsignables.value.some((item) => item.id === formAsignacion.usuarioId)) {
      formAsignacion.usuarioId = null
      formAsignacion.solicitudId = null
    }
  } catch (err) {
    error.value = err.message || 'No se pudo actualizar el estado social.'
  } finally {
    procesandoUsuarioId.value = null
  }
}

const asignarDesdeFondo = async () => {
  errorAsignacion.value = ''
  mensajeAsignacion.value = ''

  const usuario = usuarios.value.find((item) => item.id === formAsignacion.usuarioId)
  if (!usuario || !['VULNERABLE', 'CRITICO'].includes(usuario.estadoSocial)) {
    errorAsignacion.value = MENSAJE_SOLO_VULNERABLE_CRITICO
    return
  }

  procesandoAsignacion.value = true

  try {
    const respuesta = await impactoSocialController.asignarDesdeFondoAdmin(
      formAsignacion.usuarioId,
      formAsignacion.solicitudId,
      formAsignacion.monto,
      saldoFondo.value,
    )
    mensajeAsignacion.value = respuesta.mensaje
    saldoFondo.value = respuesta.saldoFondo
    formAsignacion.monto = ''
    formAsignacion.solicitudId = null
    await cargarDatos()
  } catch (err) {
    errorAsignacion.value = err.message || MENSAJE_SOLO_VULNERABLE_CRITICO
  } finally {
    procesandoAsignacion.value = false
  }
}

onMounted(async () => {
  try {
    await verificarAdmin()
    await cargarDatos()
  } catch (err) {
    error.value = err.message || MENSAJE_SIN_PERMISOS_ADMIN
    cargando.value = false
  }
})
</script>

<style scoped>
.panel__hint--inline {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
  color: #666;
}

.acciones-celda {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.button--compact {
  padding: 0.35rem 0.75rem;
  font-size: 0.85rem;
}

.input--compact {
  min-width: 10rem;
  padding: 0.35rem 0.5rem;
}
</style>
