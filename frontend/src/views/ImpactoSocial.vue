<template>
  <section class="page">
    <div class="page-header">
      <div>
        <p class="eyebrow">Impacto Social</p>
        <h2 class="page-title">Donaciones solidarias de Horas de Vida</h2>
        <p class="page-description">
          Publica solicitudes de apoyo, dona a causas aprobadas o contribuye al Fondo Comunitario.
        </p>
        <p v-if="mostrarBadgeEstadoSocial" class="page-header__badge">
          <span :class="['badge', claseEstadoSocial(estadoSocial)]">
            {{ etiquetaEstadoSocial(estadoSocial) }}
          </span>
        </p>
      </div>
    </div>

    <p class="alert alert--info">
      Las donaciones solidarias son irreversibles y usan tus Horas de Vida acumuladas, no el saldo comercial.
    </p>

    <div class="alert alert--info alert--diferencia-cartelera">
      <p class="alert__titulo">¿En qué se diferencia de la Cartelera?</p>
      <ul class="alert__lista">
        <li><strong>Cartelera:</strong> publicas una necesidad para buscar trueque directo con otro miembro.</li>
        <li><strong>Impacto Social:</strong> publicas una causa validada que puede recibir donaciones solidarias de horas.</li>
      </ul>
      <p class="alert__nota">
        Las solicitudes sociales requieren aprobación del administrador y usan títulos del catálogo de cartelera
        orientados a necesidades vulnerables (sin mejoras personales del hogar).
        Al aprobar tu solicitud, quedarás catalogado como Usuario Vulnerable.
      </p>
    </div>

    <div v-if="cargando" class="loading-state">Cargando impacto social...</div>
    <p v-else-if="errorGeneral" class="alert alert--error">{{ errorGeneral }}</p>

    <template v-else>
      <!-- Métricas -->
      <section class="panel panel--metricas">
        <div class="panel__header"><h3 class="panel__title">Mi impacto social</h3></div>
        <div class="panel__body">
          <div class="metric-row metric-row--comunidad metric-row--impacto">
            <article class="metric">
              <span class="metric__value">{{ saldoDonable.toFixed(1) }}</span>
              <span class="metric__label">Horas donables</span>
            </article>
            <article class="metric">
              <span class="metric__value">{{ totalHorasDonadas.toFixed(1) }}</span>
              <span class="metric__label">Horas donadas</span>
            </article>
            <article class="metric metric--destacada">
              <span class="metric__value">{{ totalHorasSolidarias.toFixed(1) }}</span>
              <span class="metric__label">Horas solidarias disponibles</span>
            </article>
          </div>
        </div>
      </section>

      <p v-if="!puedeDonar" class="alert alert--error">{{ MENSAJE_SALDO_POSITIVO }}</p>

      <!-- Publicar solicitud -->
      <section class="panel">
        <div class="panel__header"><h3 class="panel__title">Publicar solicitud de apoyo</h3></div>
        <div class="panel__body">
          <p class="panel__hint">
            Selecciona una necesidad del catálogo orientado a apoyo vulnerable.
            Un administrador la revisará y, si la aprueba, quedarás catalogado como Usuario Vulnerable.
          </p>
          <form class="form-grid" @submit.prevent="publicarSolicitud">
            <div class="form-group form-group--full">
              <label for="categoria_solicitud">Categoría de causa social</label>
              <select id="categoria_solicitud" v-model="formSolicitud.categoria" class="select" required>
                <option value="">Selecciona una categoría</option>
                <option v-for="cat in CATEGORIAS_CAUSA_SOCIAL" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
            <div class="form-group form-group--full">
              <label for="titulo_solicitud">Necesidad de apoyo</label>
              <select id="titulo_solicitud" v-model="formSolicitud.titulo" class="select" required :disabled="!formSolicitud.categoria">
                <option value="">Selecciona una necesidad</option>
                <option v-for="titulo in titulosCausaDisponibles" :key="titulo" :value="titulo">{{ titulo }}</option>
              </select>
            </div>
            <div class="form-group form-group--full">
              <label for="descripcion_solicitud">Descripción</label>
              <textarea id="descripcion_solicitud" v-model="formSolicitud.descripcion" class="input" rows="4" required />
            </div>
            <div class="form-actions">
              <button class="button button--primary" type="submit" :disabled="procesandoSolicitud">
                {{ procesandoSolicitud ? 'Publicando...' : 'Publicar solicitud' }}
              </button>
            </div>
          </form>
          <p v-if="mensajeSolicitud" class="alert alert--success">{{ mensajeSolicitud }}</p>
          <p v-if="errorSolicitud" class="alert alert--error">{{ errorSolicitud }}</p>
        </div>
      </section>

      <!-- Mis solicitudes -->
      <section class="panel">
        <div class="panel__header"><h3 class="panel__title">Mis solicitudes</h3></div>
        <div class="panel__body">
          <div v-if="misSolicitudes.length" class="table-container">
            <div class="data-table-grid">
              <div class="table-header">
                <div class="table-cell">Categoría</div>
                <div class="table-cell">Título</div>
                <div class="table-cell">Estado</div>
                <div class="table-cell">Horas recibidas</div>
                <div class="table-cell">Horas solidarias disp.</div>
                <div class="table-cell">Necesidad vinculada</div>
                <div class="table-cell">Acciones</div>
              </div>
              <div v-for="s in misSolicitudes" :key="s.id" class="table-row">
                <div class="table-cell">{{ s.categoria || '—' }}</div>
                <div class="table-cell"><strong>{{ s.titulo }}</strong></div>
                <div class="table-cell"><span :class="['badge', claseEstadoSolicitud(s.estado)]">{{ etiquetaEstadoSolicitud(s.estado) }}</span></div>
                <div class="table-cell">{{ Number(s.horas_recibidas || 0).toFixed(1) }}</div>
                <div class="table-cell">{{ Number(s.horas_solidarias_disponibles || 0).toFixed(1) }}</div>
                <div class="table-cell">{{ s.necesidad_activa || s.publicacion_id ? 'Sí' : 'No' }}</div>
                <div class="table-cell acciones-celda">
                  <button
                    v-if="s.estado === 'APROBADA' && !s.necesidad_activa"
                    class="button button--secondary button--compact" type="button"
                    :disabled="procesandoActivacionId === s.id"
                    @click="activarNecesidad(s.id)"
                  >
                    {{ procesandoActivacionId === s.id ? 'Activando...' : 'Activar necesidad' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">Aún no has publicado solicitudes de apoyo.</div>
          <p v-if="mensajeActivacion" class="alert alert--success">{{ mensajeActivacion }}</p>
          <p v-if="errorActivacion" class="alert alert--error">{{ errorActivacion }}</p>
        </div>
      </section>

      <!-- Causas aprobadas -->
      <section class="panel">
        <div class="panel__header">
          <h3 class="panel__title">Causas aprobadas</h3>
          <p class="panel__hint panel__hint--inline">Solo las solicitudes aprobadas pueden recibir donaciones.</p>
        </div>
        <div class="panel__body">
          <div v-if="causasDonables.length" class="member-grid">
            <article v-for="causa in causasDonables" :key="causa.id" class="member-card">
              <div class="member-card__header">
                <div class="member-avatar" :style="{ backgroundColor: getAvatarColor(causa.solicitante_nombre || causa.titulo) }">
                  {{ getInitials(causa.solicitante_nombre, causa.titulo) }}
                </div>
                <div class="member-card__info">
                  <h3 class="member-card__name">{{ causa.titulo }}</h3>
                  <p class="member-card__stars">{{ causa.solicitante_nombre }}</p>
                  <p class="member-card__vacio">{{ causa.descripcion }}</p>
                </div>
              </div>
              <div class="member-card__badges">
                <span v-if="causa.categoria" class="badge badge--normal">{{ causa.categoria }}</span>
              </div>
              <div class="form-actions">
                <button class="button button--primary" type="button" :disabled="!puedeDonar" @click="abrirModalDonacion('causa', causa)">
                  Donar Horas
                </button>
              </div>
            </article>
          </div>
          <div v-else class="empty-state">No hay causas aprobadas disponibles.</div>
        </div>
      </section>

      <!-- Fondo Comunitario -->
      <section class="panel">
        <div class="panel__header"><h3 class="panel__title">Fondo Comunitario</h3></div>
        <div class="panel__body">
          <p class="panel__hint">Contribuye al pozo común para que el administrador redistribuya horas a usuarios vulnerables.</p>
          <div class="form-actions">
            <button class="button button--secondary" type="button" @click="abrirModalDonacion('fondo')">
              Donar al Fondo Comunitario
            </button>
          </div>
        </div>
      </section>

      <!-- Historial de donaciones -->
      <section class="panel">
        <div class="panel__header"><h3 class="panel__title">Historial de donaciones</h3></div>
        <div class="panel__body">
          <h4 class="panel__subtitle">Donaciones realizadas</h4>
          <div v-if="donacionesRealizadas.length" class="table-container">
            <table class="data-table">
              <thead><tr><th>Fecha</th><th>Tipo</th><th>Monto</th><th>Receptor</th><th>Comprobante</th></tr></thead>
              <tbody>
                <tr v-for="d in donacionesRealizadas" :key="`r-${d.id}`">
                  <td>{{ formatearFecha(d.fecha) }}</td>
                  <td>{{ d.tipo_destino === 'FONDO' ? 'Fondo' : 'Causa' }}</td>
                  <td>{{ Number(d.monto).toFixed(1) }} h</td>
                  <td>{{ d.receptor_nombre }}</td>
                  <td>{{ d.comprobante_id }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-state">Aún no has realizado donaciones solidarias.</div>

          <h4 class="panel__subtitle">Donaciones recibidas</h4>
          <div v-if="donacionesRecibidas.length" class="table-container">
            <table class="data-table">
              <thead><tr><th>Fecha</th><th>Tipo</th><th>Monto</th><th>Donante</th><th>Comprobante</th></tr></thead>
              <tbody>
                <tr v-for="d in donacionesRecibidas" :key="`d-${d.id}`">
                  <td>{{ formatearFecha(d.fecha) }}</td>
                  <td>{{ d.tipo_destino === 'FONDO' ? 'Fondo' : 'Causa' }}</td>
                  <td>{{ Number(d.monto).toFixed(1) }} h</td>
                  <td>{{ d.donante_nombre }}</td>
                  <td>{{ d.comprobante_id }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-state">Aún no has recibido donaciones solidarias.</div>
        </div>
      </section>

      <!-- Comprobante -->
      <div v-if="comprobanteDonacion" class="comprobante comprobante--success">
        <p class="comprobante__titulo">Donación Exitosa</p>
        <dl class="comprobante__grid">
          <div class="comprobante__item"><dt>Monto donado</dt><dd>{{ comprobanteDonacion.monto.toFixed(1) }} h</dd></div>
          <div v-if="comprobanteDonacion.receptorNombre" class="comprobante__item"><dt>Receptor</dt><dd>{{ comprobanteDonacion.receptorNombre }}</dd></div>
          <div v-if="comprobanteDonacion.comprobanteId" class="comprobante__item"><dt>Comprobante</dt><dd>{{ comprobanteDonacion.comprobanteId }}</dd></div>
        </dl>
        <p class="comprobante__balance">Saldo restante: <strong>{{ comprobanteDonacion.saldoRestante.toFixed(1) }} h</strong></p>
      </div>
    </template>

    <!-- Modal Donación -->
    <Teleport to="body">
      <div v-if="mostrarModalDonacion" class="modal-overlay" @click.self="cerrarModalDonacion">
        <div class="modal-content modal-content--confirmacion" role="dialog" aria-modal="true">
          <div class="modal-header">
            <h3 class="modal-title">{{ modalDonacion.tipo === 'fondo' ? 'Donar al Fondo Comunitario' : 'Donar Horas a causa' }}</h3>
            <button class="modal-close" type="button" aria-label="Cerrar" @click="cerrarModalDonacion">×</button>
          </div>
          <div class="modal-body">
            <p v-if="modalDonacion.tipo === 'causa'" class="panel__hint">Causa: <strong>{{ modalDonacion.titulo }}</strong></p>
            <p v-else class="panel__hint">Tus horas se acreditarán al Fondo Comunitario del sistema.</p>
            <form class="form-grid" @submit.prevent="confirmarDonacion">
              <div class="form-group form-group--full">
                <label for="monto_donacion">Monto en horas</label>
                <input id="monto_donacion" v-model="modalDonacion.monto" class="input" type="number" min="0.5" step="0.1" :max="saldoDonable > 0 ? saldoDonable : undefined" required :disabled="!puedeDonar" />
                <p class="panel__hint panel__hint--inline" style="line-height: 1.4;">
                  Mínimo: 0.5 h<br />
                  Disponible: {{ saldoDonable.toFixed(1) }} h
                </p>
              </div>
              <p v-if="!puedeDonar" class="alert alert--error" style="margin-bottom: 1rem;">
                No tienes horas disponibles para donar.
              </p>
              <div class="modal-footer">
                <button class="button button--secondary" type="button" @click="cerrarModalDonacion">Cancelar</button>
                <button class="button button--primary" type="submit" :disabled="procesandoDonacion || !puedeDonar">
                  {{ procesandoDonacion ? 'Donando...' : 'Confirmar donación' }}
                </button>
              </div>
            </form>
            <p v-if="errorDonacion" class="alert alert--error">{{ errorDonacion }}</p>
          </div>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { useImpactoSocialStore } from '../stores/impactoSocial.js'
import { CATEGORIAS_CAUSA_SOCIAL, titulosCausaSocialPorCategoria } from '../data/catalogoCausasSociales.js'

const authStore = useAuthStore()
const impactoStore = useImpactoSocialStore()

const MENSAJE_SALDO_POSITIVO = 'Necesitas saldo positivo para realizar donaciones solidarias'
const AVATAR_COLORS = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b', '#fa709a', '#fee140']

const cargando = ref(true)
const errorGeneral = ref('')
const saldoDonable = ref(0)
const estadoSocial = ref('NINGUNO')
const causasAprobadas = ref([])
const misSolicitudes = ref([])
const donacionesRealizadas = ref([])
const donacionesRecibidas = ref([])

const formSolicitud = reactive({ categoria: '', titulo: '', descripcion: '' })
const procesandoSolicitud = ref(false)
const mensajeSolicitud = ref('')
const errorSolicitud = ref('')
const procesandoActivacionId = ref(null)
const mensajeActivacion = ref('')
const errorActivacion = ref('')

const mostrarModalDonacion = ref(false)
const procesandoDonacion = ref(false)
const errorDonacion = ref('')
const comprobanteDonacion = ref(null)

const modalDonacion = reactive({ tipo: 'causa', solicitudId: null, titulo: '', monto: '' })

const puedeDonar = computed(() => saldoDonable.value > 0)

const totalHorasSolidarias = computed(() =>
  (misSolicitudes.value || [])
    .filter((s) => s.estado === 'APROBADA')
    .reduce((sum, s) => sum + Number(s.horas_solidarias_disponibles || 0), 0)
)

const totalHorasDonadas = computed(() =>
  (donacionesRealizadas.value || []).reduce((sum, d) => sum + Number(d.monto || 0), 0)
)

const causasDonables = computed(() => {
  const miId = authStore.usuarioActual?.id
  return causasAprobadas.value.filter((c) => Number(c.solicitante_id) !== Number(miId))
})

const mostrarBadgeEstadoSocial = computed(() => ['VULNERABLE', 'CRITICO'].includes(estadoSocial.value))

const titulosCausaDisponibles = computed(() => titulosCausaSocialPorCategoria(formSolicitud.categoria))

watch(() => formSolicitud.categoria, () => { formSolicitud.titulo = '' })

const etiquetaEstadoSocial = (estado) => {
  if (estado === 'VULNERABLE' || estado === 'CRITICO') return 'Usuario Vulnerable'
  return null
}
const claseEstadoSocial = (estado) => {
  if (estado === 'VULNERABLE') return 'badge--alta'
  if (estado === 'CRITICO') return 'badge--critica'
  return 'badge--normal'
}
const etiquetaEstadoSolicitud = (estado) => {
  if (estado === 'APROBADA') return 'Aprobada'
  if (estado === 'RECHAZADA') return 'Rechazada'
  return 'Pendiente'
}
const claseEstadoSolicitud = (estado) => {
  if (estado === 'APROBADA') return 'badge--activa'
  if (estado === 'RECHAZADA') return 'badge--critica'
  return 'badge--alta'
}
const formatearFecha = (fecha) => fecha ? new Date(fecha).toLocaleString('es-ES') : '—'
const getInitials = (nombre, fallback) => (nombre || fallback || 'C').charAt(0).toUpperCase()
const getAvatarColor = (texto) => AVATAR_COLORS[(texto || 'c').charCodeAt(0) % AVATAR_COLORS.length]

const cargarSaldoUsuario = async () => {
  const sesion = authStore.usuarioActual
  saldoDonable.value = Number(sesion?.horasDeVida || sesion?.horas_de_vida || 0)
  estadoSocial.value = sesion?.estadoSocial || sesion?.estado_social || 'NINGUNO'
}

const cargarDatos = async () => {
  cargando.value = true
  errorGeneral.value = ''
  try {
    await authStore.obtenerSesionActual(true)
    await cargarSaldoUsuario()

    const [causas, propias, historial] = await Promise.all([
      impactoStore.obtenerSolicitudesAprobadas(),
      impactoStore.obtenerMisSolicitudes(),
      impactoStore.obtenerMisDonaciones(),
    ])

    causasAprobadas.value = causas.solicitudes || []
    misSolicitudes.value = propias.solicitudes || []
    donacionesRealizadas.value = historial.realizadas || []
    donacionesRecibidas.value = historial.recibidas || []
  } catch (err) {
    errorGeneral.value = err.message || 'No se pudo cargar la sección de impacto social.'
  } finally {
    cargando.value = false
  }
}

const publicarSolicitud = async () => {
  procesandoSolicitud.value = true
  mensajeSolicitud.value = ''
  errorSolicitud.value = ''
  try {
    await impactoStore.crearSolicitud(formSolicitud.categoria, formSolicitud.titulo, formSolicitud.descripcion)
    mensajeSolicitud.value = 'Tu solicitud quedó pendiente de aprobación. Si el administrador la aprueba, podrás recibir donaciones.'
    formSolicitud.categoria = ''
    formSolicitud.titulo = ''
    formSolicitud.descripcion = ''
    await cargarDatos()
  } catch (err) {
    errorSolicitud.value = err.message || 'No se pudo publicar la solicitud.'
  } finally {
    procesandoSolicitud.value = false
  }
}

const activarNecesidad = async (solicitudId) => {
  procesandoActivacionId.value = solicitudId
  mensajeActivacion.value = ''
  errorActivacion.value = ''
  try {
    await impactoStore.activarNecesidadVinculada(solicitudId)
    mensajeActivacion.value = 'Necesidad activada en la cartelera.'
    await cargarDatos()
  } catch (err) {
    errorActivacion.value = err.message || 'No se pudo activar la necesidad.'
  } finally {
    procesandoActivacionId.value = null
  }
}

const abrirModalDonacion = (tipo, causa = null) => {
  errorDonacion.value = ''
  comprobanteDonacion.value = null
  modalDonacion.tipo = tipo
  modalDonacion.solicitudId = causa?.id || null
  modalDonacion.titulo = causa?.titulo || 'Fondo Comunitario'
  modalDonacion.monto = ''
  mostrarModalDonacion.value = true
}

const cerrarModalDonacion = () => {
  mostrarModalDonacion.value = false
  errorDonacion.value = ''
}

const confirmarDonacion = async () => {
  procesandoDonacion.value = true
  errorDonacion.value = ''
  try {
    const respuesta = modalDonacion.tipo === 'fondo'
      ? await impactoStore.donarAFondo(Number(modalDonacion.monto))
      : await impactoStore.donarACausa(modalDonacion.solicitudId, Number(modalDonacion.monto))

    saldoDonable.value = Number(respuesta.saldo_restante ?? 0)
    comprobanteDonacion.value = {
      monto: Number(respuesta.monto || modalDonacion.monto),
      receptorNombre: respuesta.receptor_nombre || (modalDonacion.tipo === 'fondo' ? 'Fondo Comunitario' : modalDonacion.titulo),
      comprobanteId: respuesta.comprobante?.comprobante_id || null,
      saldoRestante: Number(respuesta.saldo_restante ?? 0),
    }
    cerrarModalDonacion()
    await cargarDatos()
  } catch (err) {
    errorDonacion.value = err.message || 'No se pudo completar la donación.'
  } finally {
    procesandoDonacion.value = false
  }
}

onMounted(cargarDatos)
</script>

<style scoped>
.panel--metricas { margin-bottom: 0; }
.panel--metricas .panel__body { padding-top: 0.5rem; }
.metric-row--impacto { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.metric--destacada {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border: 2px solid #43a047; border-radius: 10px; padding: 0.75rem 1rem;
}
.metric--destacada .metric__value { color: #2e7d32; }
.metric--destacada .metric__label { color: #1b5e20; font-weight: 600; }
.page-header__badge { margin: 0.75rem 0 0; }
.panel__hint--inline { margin: 0.25rem 0 0; font-size: 0.85rem; color: #666; }
.panel__subtitle { margin: 1.25rem 0 0.75rem; font-size: 1rem; font-weight: 600; color: #333; }
.panel__subtitle:first-child { margin-top: 0; }
.comprobante { margin-top: 1rem; padding: 1rem; border-radius: 8px; border: 1px solid #c3e6cb; background: #f4fbf6; }
.comprobante__titulo { margin: 0 0 0.75rem; font-weight: 700; color: #155724; }
.comprobante__grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.75rem; margin: 0 0 0.75rem; }
.comprobante__item { margin: 0; }
.comprobante__item dt { margin: 0 0 0.15rem; font-size: 0.75rem; color: #666; text-transform: uppercase; }
.comprobante__item dd { margin: 0; font-weight: 600; color: #333; }
.comprobante__balance { margin: 0; font-size: 0.9rem; color: #444; }
.alert--diferencia-cartelera { margin-top: 0; }
.alert__titulo { margin: 0 0 0.5rem; font-weight: 700; }
.alert__lista { margin: 0 0 0.75rem; padding-left: 1.25rem; }
.alert__lista li { margin-bottom: 0.35rem; }
.alert__nota { margin: 0; font-size: 0.92rem; }
.acciones-celda { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
.button--compact { padding: 0.35rem 0.75rem; font-size: 0.85rem; }
.data-table-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 0.5rem; }
.table-header { display: contents; font-weight: 600; }
.table-header .table-cell { font-weight: 600; color: #333; }
.table-row { display: contents; }
.table-cell { padding: 0.75rem 0.5rem; display: flex; align-items: center; }
.table-cell:first-child { padding-left: 0; }
.table-cell:last-child { padding-right: 0; }
@media (max-width: 640px) { .metric-row--impacto { grid-template-columns: 1fr; } }
</style>
