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

    <p v-if="!esAdmin" class="alert alert--error">No tienes permisos de administrador.</p>

    <template v-else>
      <div v-if="cargando" class="loading-state">Cargando panel administrativo...</div>
      <p v-else-if="errorGeneral" class="alert alert--error">{{ errorGeneral }}</p>

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

        <!-- Solicitudes pendientes -->
        <section class="panel">
          <div class="panel__header">
            <h3 class="panel__title">Solicitudes pendientes de aprobación</h3>
            <p class="panel__hint panel__hint--inline">
              Al aprobar, el solicitante quedará marcado como Usuario Vulnerable.
            </p>
          </div>
          <div class="panel__body">
            <div v-if="solicitudesPendientes.length" class="table-container">
              <table class="data-table">
                <thead><tr><th>Solicitante</th><th>Categoría</th><th>Necesidad</th><th>Descripción</th><th>Acciones</th></tr></thead>
                <tbody>
                  <tr v-for="s in solicitudesPendientes" :key="s.id">
                    <td>{{ s.solicitante_nombre || '—' }}</td>
                    <td>{{ s.categoria || '—' }}</td>
                    <td><strong>{{ s.titulo }}</strong></td>
                    <td>{{ s.descripcion }}</td>
                    <td class="acciones-celda">
                      <button class="button button--primary button--compact" type="button"
                        :disabled="procesandoSolicitudId === s.id" @click="aprobarSolicitud(s.id)">Aprobar</button>
                      <button class="button button--secondary button--compact" type="button"
                        :disabled="procesandoSolicitudId === s.id" @click="rechazarSolicitud(s.id)">Rechazar</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty-state">No hay solicitudes pendientes de revisión.</div>
          </div>
        </section>

        <!-- Usuarios y estado social -->
        <section class="panel">
          <div class="panel__header">
            <h3 class="panel__title">Usuarios y estado social</h3>
            <p class="panel__hint panel__hint--inline">Marca usuarios como Vulnerable o Crítico para priorizar apoyo.</p>
          </div>
          <div class="panel__body">
            <div v-if="usuarios.length" class="table-container">
              <table class="data-table">
                <thead><tr><th>Usuario</th><th>Horas de vida</th><th>Horas recibidas por donación</th><th>Estado social</th></tr></thead>
                <tbody>
                  <tr v-for="u in usuarios" :key="u.id">
                    <td>
                      <strong>{{ u.nombre_real }}</strong>
                      <p class="panel__hint panel__hint--inline">@{{ u.username }}</p>
                    </td>
                    <td>{{ Number(u.horas_de_vida || 0).toFixed(1) }}</td>
                    <td>{{ Number(u.horas_recibidas_donacion || 0).toFixed(1) }}</td>
                    <td>
                      <select class="input input--compact" :value="u.estado_social"
                        :disabled="procesandoUsuarioId === u.id"
                        @change="actualizarEstadoSocial(u, $event.target.value)">
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

        <!-- Asignar desde fondo -->
        <section class="panel">
          <div class="panel__header"><h3 class="panel__title">Asignar horas desde el Fondo Comunitario</h3></div>
          <div class="panel__body">
            <p class="panel__hint">Solo usuarios marcados como Vulnerable o Crítico pueden recibir asignaciones.</p>
            <form class="form-grid" @submit.prevent="asignarDesdeFondo">
              <div class="form-group form-group--full">
                <label for="usuario_asignacion">Usuario receptor</label>
                <select id="usuario_asignacion" v-model.number="formAsignacion.usuarioId" class="input" required>
                  <option disabled :value="null">Selecciona un usuario vulnerable o crítico</option>
                  <option v-for="u in usuariosAsignables" :key="u.id" :value="u.id">
                    {{ u.nombre_real }} — {{ u.estado_social === 'CRITICO' ? 'Crítico' : 'Vulnerable' }}
                  </option>
                </select>
                <p v-if="!usuariosAsignables.length" class="alert alert--info">
                  Marca al menos un usuario como Vulnerable o Crítico.
                </p>
              </div>
              <div class="form-group form-group--full">
                <label for="solicitud_asignacion">Solicitud aprobada del receptor</label>
                <select id="solicitud_asignacion" v-model.number="formAsignacion.solicitudId" class="input" required :disabled="!formAsignacion.usuarioId">
                  <option disabled :value="null">Selecciona la causa destino</option>
                  <option v-for="s in solicitudesReceptorAsignacion" :key="s.id" :value="s.id">
                    {{ s.titulo }} ({{ Number(s.horas_recibidas || 0).toFixed(1) }} h recibidas)
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label for="monto_asignacion">Monto en horas</label>
                <input id="monto_asignacion" v-model="formAsignacion.monto" class="input" type="number" min="0.5" step="0.1" :max="saldoFondo > 0 ? saldoFondo : undefined" required />
                <p class="panel__hint panel__hint--inline">Saldo disponible en fondo: {{ saldoFondo.toFixed(1) }} h</p>
              </div>
              <div class="form-actions">
                <button class="button button--primary" type="submit" :disabled="procesandoAsignacion || !puedeAsignar">
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
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { useImpactoSocialStore } from '../stores/impactoSocial.js'

const authStore = useAuthStore()
const impactoStore = useImpactoSocialStore()

const esAdmin = ref(false)
const cargando = ref(true)
const errorGeneral = ref('')
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

const formAsignacion = reactive({ usuarioId: null, solicitudId: null, monto: '' })

const usuariosAsignables = computed(() =>
  usuarios.value.filter((u) => ['VULNERABLE', 'CRITICO'].includes(u.estado_social))
)

const solicitudesReceptorAsignacion = computed(() => {
  if (!formAsignacion.usuarioId) return []
  return solicitudesAprobadas.value.filter((s) => s.solicitante === formAsignacion.usuarioId)
})

const puedeAsignar = computed(() =>
  Boolean(formAsignacion.usuarioId) &&
  Boolean(formAsignacion.solicitudId) &&
  solicitudesReceptorAsignacion.value.length > 0 &&
  Number(formAsignacion.monto) >= 0.5 &&
  Number(formAsignacion.monto) <= saldoFondo.value
)

watch(() => formAsignacion.usuarioId, () => { formAsignacion.solicitudId = null })

watch(solicitudesReceptorAsignacion, (lista) => {
  if (lista.length === 1) formAsignacion.solicitudId = lista[0].id
  else if (!lista.some((item) => item.id === formAsignacion.solicitudId)) formAsignacion.solicitudId = null
})

const verificarAdmin = () => {
  const user = authStore.usuarioActual
  esAdmin.value = Boolean(user?.esStaff || user?.esSuperusuario || user?.is_staff || user?.is_superuser)
}

const cargarDatos = async () => {
  if (!esAdmin.value) { cargando.value = false; return }

  cargando.value = true
  errorGeneral.value = ''
  mensajeGlobal.value = ''

  try {
    const [pendientes, listaUsuarios, fondo, aprobadas] = await Promise.all([
      impactoStore.obtenerSolicitudesPendientes(),
      impactoStore.obtenerUsuariosAdmin(),
      impactoStore.obtenerSaldoFondo(),
      impactoStore.obtenerSolicitudesAprobadas(),
    ])

    solicitudesPendientes.value = pendientes.solicitudes || []
    usuarios.value = listaUsuarios.usuarios || []
    saldoFondo.value = Number(fondo.saldo || 0)
    solicitudesAprobadas.value = aprobadas.solicitudes || []
  } catch (err) {
    errorGeneral.value = err.message || 'No se pudo cargar el panel de impacto social.'
  } finally {
    cargando.value = false
  }
}

const aprobarSolicitud = async (solicitudId) => {
  procesandoSolicitudId.value = solicitudId
  mensajeGlobal.value = ''
  try {
    const data = await impactoStore.aprobarSolicitud(solicitudId)
    mensajeGlobal.value = data.mensaje || 'Solicitud aprobada. El solicitante fue catalogado como Usuario Vulnerable.'
    await cargarDatos()
  } catch (err) {
    errorGeneral.value = err.message || 'No se pudo aprobar la solicitud.'
  } finally {
    procesandoSolicitudId.value = null
  }
}

const rechazarSolicitud = async (solicitudId) => {
  procesandoSolicitudId.value = solicitudId
  mensajeGlobal.value = ''
  try {
    await impactoStore.rechazarSolicitud(solicitudId)
    mensajeGlobal.value = 'Solicitud rechazada correctamente.'
    await cargarDatos()
  } catch (err) {
    errorGeneral.value = err.message || 'No se pudo rechazar la solicitud.'
  } finally {
    procesandoSolicitudId.value = null
  }
}

const actualizarEstadoSocial = async (usuario, nuevoEstado) => {
  if (usuario.estado_social === nuevoEstado) return
  procesandoUsuarioId.value = usuario.id
  mensajeGlobal.value = ''
  errorGeneral.value = ''
  try {
    const data = await impactoStore.actualizarEstadoSocial(usuario.id, nuevoEstado)
    usuario.estado_social = data.estado_social || nuevoEstado
    mensajeGlobal.value = `Estado social actualizado a ${nuevoEstado}.`
  } catch (err) {
    errorGeneral.value = err.message || 'No se pudo actualizar el estado social.'
  } finally {
    procesandoUsuarioId.value = null
  }
}

const asignarDesdeFondo = async () => {
  errorAsignacion.value = ''
  mensajeAsignacion.value = ''
  procesandoAsignacion.value = true
  try {
    const data = await impactoStore.asignarDesdeFondo(formAsignacion.usuarioId, formAsignacion.solicitudId, Number(formAsignacion.monto))
    mensajeAsignacion.value = data.mensaje || 'Asignación realizada.'
    saldoFondo.value = Number(data.saldo_fondo ?? 0)
    formAsignacion.monto = ''
    formAsignacion.solicitudId = null
    await cargarDatos()
  } catch (err) {
    errorAsignacion.value = err.message || 'No se pudo asignar horas desde el fondo.'
  } finally {
    procesandoAsignacion.value = false
  }
}

onMounted(async () => {
  try {
    verificarAdmin()
    await cargarDatos()
  } catch (err) {
    errorGeneral.value = err.message || 'No tienes permisos de administrador.'
    cargando.value = false
  }
})
</script>

<style scoped>
.panel__hint--inline { margin: 0.25rem 0 0; font-size: 0.85rem; color: #666; }
.acciones-celda { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.button--compact { padding: 0.35rem 0.75rem; font-size: 0.85rem; }
.input--compact { min-width: 10rem; padding: 0.35rem 0.5rem; }
</style>
