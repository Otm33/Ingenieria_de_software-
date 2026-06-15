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
        <li>
          <strong>Cartelera:</strong> publicas una necesidad para buscar trueque directo con otro miembro.
        </li>
        <li>
          <strong>Impacto Social:</strong> publicas una causa validada que puede recibir donaciones solidarias de horas.
        </li>
      </ul>
      <p class="alert__nota">
        Las solicitudes sociales requieren aprobación del administrador y usan títulos del catálogo de cartelera
        orientados a necesidades vulnerables (sin mejoras personales del hogar).
        Al aprobar tu solicitud, quedarás catalogado como Usuario Vulnerable.
      </p>
    </div>

    <div v-if="cargando" class="loading-state">Cargando impacto social...</div>
    <p v-else-if="error" class="alert alert--error">{{ error }}</p>

    <template v-else>
      <section class="panel panel--metricas">
        <div class="panel__header">
          <h3 class="panel__title">Mi impacto social</h3>
        </div>
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

      <p v-if="!puedeDonar" class="alert alert--error">
        {{ MENSAJE_SALDO_POSITIVO_DONACION }}
      </p>
      <p v-else-if="avisoDonacion" class="alert alert--error">{{ avisoDonacion }}</p>

      <section class="panel">
        <div class="panel__header">
          <h3 class="panel__title">Publicar solicitud de apoyo</h3>
        </div>
        <div class="panel__body">
          <p class="panel__hint">
            Publica tu solicitud de apoyo social con necesidades del catálogo de cartelera
            (solo opciones orientadas a apoyo vulnerable).
            Un administrador la revisará y, si la aprueba, quedarás catalogado como
            Usuario Vulnerable y podrás recibir donaciones solidarias.
          </p>
          <p class="panel__hint panel__hint--inline">
            Selecciona una necesidad del catálogo compartido con la cartelera. No uses esta sección para
            mejoras personales del hogar; para trueques directos sin validación social usa la Cartelera.
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
                <select
                  id="titulo_solicitud"
                  v-model="formSolicitud.titulo"
                  class="select"
                  required
                  :disabled="!formSolicitud.categoria"
                >
                  <option value="">Selecciona una necesidad</option>
                  <option v-for="titulo in titulosCausaDisponibles" :key="titulo" :value="titulo">
                    {{ titulo }}
                  </option>
                </select>
              </div>
              <div class="form-group form-group--full">
                <label for="descripcion_solicitud">Descripción</label>
                <textarea
                  id="descripcion_solicitud"
                  v-model="formSolicitud.descripcion"
                  class="input"
                  rows="4"
                  required
                />
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

      <section class="panel">
        <div class="panel__header">
          <h3 class="panel__title">Mis solicitudes</h3>
        </div>
        <div class="panel__body">
          <div v-if="misSolicitudes.length" class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Categoría</th>
                  <th>Título</th>
                  <th>Estado</th>
                  <th>Horas recibidas</th>
                  <th>Horas solidarias disp.</th>
                  <th>Horas utilizadas</th>
                  <th>Necesidad vinculada</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="solicitud in misSolicitudes" :key="solicitud.id">
                  <td>{{ solicitud.categoria || '—' }}</td>
                  <td>
                    <strong>{{ solicitud.titulo }}</strong>
                    <p class="panel__hint panel__hint--inline">{{ solicitud.descripcion }}</p>
                  </td>
                  <td>
                    <span :class="['badge', claseEstadoSolicitud(solicitud.estado)]">
                      {{ etiquetaEstadoSolicitud(solicitud.estado) }}
                    </span>
                    <span v-if="solicitud.estado === 'APROBADA'" class="badge badge--normal">
                      Tu causa
                    </span>
                  </td>
                  <td>{{ solicitud.horasRecibidas.toFixed(1) }}</td>
                  <td>{{ solicitud.horasSolidariasDisponibles.toFixed(1) }}</td>
                  <td>{{ solicitud.horasSolidariasUtilizadas.toFixed(1) }}</td>
                  <td>{{ solicitud.necesidadActiva || solicitud.publicacionId ? 'Sí' : 'No' }}</td>
                  <td class="acciones-celda">
                    <button
                      v-if="puedeActivarNecesidad(solicitud)"
                      class="button button--secondary button--compact"
                      type="button"
                      :disabled="procesandoActivacionId === solicitud.id"
                      @click="activarNecesidad(solicitud.id)"
                    >
                      {{ procesandoActivacionId === solicitud.id ? 'Activando...' : 'Activar necesidad en cartelera' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-state">Aún no has publicado solicitudes de apoyo.</div>
          <p v-if="mensajeActivacion" class="alert alert--success">{{ mensajeActivacion }}</p>
          <p v-if="errorActivacion" class="alert alert--error">{{ errorActivacion }}</p>
        </div>
      </section>

      <section class="panel">
        <div class="panel__header">
          <h3 class="panel__title">Causas aprobadas</h3>
          <p class="panel__hint panel__hint--inline">
            Solo las solicitudes aprobadas por el administrador pueden recibir donaciones.
          </p>
        </div>
        <div class="panel__body">
          <div v-if="causasDonables.length" class="member-grid">
            <article v-for="causa in causasDonables" :key="causa.id" class="member-card">
              <div class="member-card__header">
                <div
                  class="member-avatar"
                  :style="{ backgroundColor: getAvatarColor(causa.solicitanteNombre || causa.titulo) }"
                >
                  {{ getInitials(causa.solicitanteNombre, causa.titulo) }}
                </div>
                <div class="member-card__info">
                  <h3 class="member-card__name">{{ causa.titulo }}</h3>
                  <p class="member-card__stars">{{ causa.solicitanteNombre }}</p>
                  <p class="member-card__vacio">{{ causa.descripcion }}</p>
                </div>
              </div>
              <div class="member-card__badges">
                <span v-if="causa.categoria" class="badge badge--normal">{{ causa.categoria }}</span>
                <span v-if="etiquetaEstadoSocial(causa.estadoSocialSolicitante)" :class="['badge', claseEstadoSocial(causa.estadoSocialSolicitante)]">
                  {{ etiquetaEstadoSocial(causa.estadoSocialSolicitante) }}
                </span>
                <span
                  :class="[
                    'badge',
                    receptorAlcanzoTopeDonaciones(causa) ? 'badge--critica' : 'badge--activa',
                  ]"
                >
                  {{ formatearTopeDonacionesUsuario(causa) }}
                </span>
                <span v-if="causa.horasRecibidas > 0" class="badge badge--normal">
                  {{ causa.horasRecibidas.toFixed(1) }} h en esta causa
                </span>
              </div>
              <div class="form-actions">
                <button
                  class="button button--primary"
                  type="button"
                  :disabled="!puedeDonar || !receptorPuedeRecibirDonacion(causa)"
                  :title="tituloBotonDonarCausa(causa)"
                  @click="abrirModalDonacion('causa', causa)"
                >
                  Donar Horas
                </button>
                <p
                  v-if="mensajeAvisoReceptorCausa(causa)"
                  :class="[
                    'panel__hint panel__hint--inline aviso-causa',
                    receptorAlcanzoTopeDonaciones(causa) ? 'aviso-causa--tope' : '',
                  ]"
                >
                  {{ mensajeAvisoReceptorCausa(causa) }}
                </p>
              </div>
            </article>
          </div>
          <div v-else class="empty-state">
            {{ causasAprobadas.length && !causasDonables.length
              ? 'No hay otras causas aprobadas para donar en este momento.'
              : 'No hay causas aprobadas disponibles. Publica una solicitud o espera la aprobación del administrador.' }}
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="panel__header">
          <h3 class="panel__title">Fondo Comunitario</h3>
        </div>
        <div class="panel__body">
          <p class="panel__hint">
            Contribuye al pozo común para que el administrador redistribuya horas a usuarios vulnerables o críticos.
          </p>
          <div class="form-actions">
            <button
              class="button button--secondary"
              type="button"
              :title="puedeDonar ? '' : MENSAJE_SALDO_POSITIVO_DONACION"
              @click="abrirModalDonacion('fondo')"
            >
              Donar al Fondo Comunitario
            </button>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="panel__header">
          <h3 class="panel__title">Historial de donaciones</h3>
        </div>
        <div class="panel__body">
          <h4 class="panel__subtitle">Donaciones realizadas</h4>
          <div v-if="donacionesRealizadas.length" class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th>Monto</th>
                  <th>Receptor</th>
                  <th>Comprobante</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="donacion in donacionesRealizadas" :key="`realizada-${donacion.id}`">
                  <td>{{ formatearFecha(donacion.fecha) }}</td>
                  <td>{{ etiquetaTipoDonacion(donacion.tipoDestino) }}</td>
                  <td>{{ donacion.monto.toFixed(1) }} h</td>
                  <td>{{ donacion.receptorNombre }}</td>
                  <td>{{ donacion.comprobanteId }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-state">Aún no has realizado donaciones solidarias.</div>

          <h4 class="panel__subtitle">Donaciones recibidas</h4>
          <div v-if="donacionesRecibidas.length" class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th>Monto</th>
                  <th>Donante</th>
                  <th>Comprobante</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="donacion in donacionesRecibidas" :key="`recibida-${donacion.id}`">
                  <td>{{ formatearFecha(donacion.fecha) }}</td>
                  <td>{{ etiquetaTipoDonacion(donacion.tipoDestino) }}</td>
                  <td>{{ donacion.monto.toFixed(1) }} h</td>
                  <td>{{ donacion.donanteNombre }}</td>
                  <td>{{ donacion.comprobanteId }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-state">Aún no has recibido donaciones solidarias.</div>
        </div>
      </section>

      <div v-if="comprobanteDonacion" class="comprobante comprobante--success">
        <p class="comprobante__titulo">{{ MENSAJE_DONACION_EXITOSA }}</p>
        <dl class="comprobante__grid">
          <div class="comprobante__item">
            <dt>Monto donado</dt>
            <dd>{{ comprobanteDonacion.monto.toFixed(1) }} h</dd>
          </div>
          <div v-if="comprobanteDonacion.receptorNombre" class="comprobante__item">
            <dt>Receptor</dt>
            <dd>{{ comprobanteDonacion.receptorNombre }}</dd>
          </div>
          <div v-if="comprobanteDonacion.tipoDestino === 'FONDO'" class="comprobante__item">
            <dt>Destino</dt>
            <dd>Fondo Comunitario</dd>
          </div>
          <div v-if="comprobanteDonacion.comprobanteId" class="comprobante__item">
            <dt>Comprobante</dt>
            <dd>{{ comprobanteDonacion.comprobanteId }}</dd>
          </div>
        </dl>
        <p class="comprobante__balance">
          Saldo restante:
          <strong>{{ comprobanteDonacion.saldoRestante.toFixed(1) }} h</strong>
        </p>
      </div>
    </template>

    <Teleport to="body">
      <div v-if="mostrarModalDonacion" class="modal-overlay" @click.self="cerrarModalDonacion">
        <div class="modal-content modal-content--confirmacion" role="dialog" aria-modal="true">
          <div class="modal-header">
            <h3 class="modal-title">
              {{ modalDonacion.tipo === 'fondo' ? 'Donar al Fondo Comunitario' : 'Donar Horas a causa' }}
            </h3>
            <button class="modal-close" type="button" aria-label="Cerrar" @click="cerrarModalDonacion">×</button>
          </div>
          <div class="modal-body">
            <p v-if="modalDonacion.tipo === 'causa'" class="panel__hint">
              Causa: <strong>{{ modalDonacion.titulo }}</strong>
            </p>
            <p
              v-if="modalDonacion.tipo === 'causa' && avisoReceptorModal"
              :class="['alert', avisoReceptorModal.tipo === 'error' ? 'alert--error' : 'alert--info']"
            >
              {{ avisoReceptorModal.texto }}
            </p>
            <p v-else-if="modalDonacion.tipo !== 'causa'" class="panel__hint">
              Tus horas se acreditarán al Fondo Comunitario del sistema.
            </p>

            <form class="form-grid" @submit.prevent="confirmarDonacion">
              <div class="form-group form-group--full">
                <label for="monto_donacion">Monto en horas</label>
                <input
                  id="monto_donacion"
                  v-model="modalDonacion.monto"
                  class="input"
                  type="number"
                  min="0.5"
                  step="0.1"
                  :max="saldoDonable > 0 ? saldoDonable : undefined"
                  required
                />
                <p class="panel__hint panel__hint--inline">
                  Mínimo 0.5 h. Máximo disponible: {{ saldoDonable.toFixed(1) }} h
                </p>
                <p v-if="modalDonacion.monto && !montoModalValido" class="alert alert--error">
                  {{ errorMontoModal }}
                </p>
              </div>
              <div class="modal-footer">
                <button class="button button--secondary" type="button" @click="cerrarModalDonacion">
                  Cancelar
                </button>
                <button
                  class="button button--primary"
                  type="submit"
                  :disabled="procesandoDonacion || !puedeDonar || !montoModalValido"
                >
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
import { computed, inject, onMounted, reactive, ref, watch } from 'vue'
import {
  MENSAJE_DONACION_EXITOSA,
  MENSAJE_RECEPTOR_MAS_10_HORAS,
  MENSAJE_SALDO_POSITIVO_DONACION,
  MENSAJE_TOPE_HORAS_RECIBIDAS,
  MENSAJE_TOPE_USUARIO_ALCANZADO,
  TOPE_HORAS_RECIBIDAS_DONACION,
  calcularHorasRestantesReceptor,
  calcularHorasSolidariasTotales,
  calcularMontoDonacionesTotales,
  etiquetaEstadoSocial,
  etiquetaTipoDonacion,
} from '../controllers/ImpactoSocialController.js'
import {
  CATEGORIAS_CAUSA_SOCIAL,
  titulosCausaSocialPorCategoria,
} from '../data/catalogoCausasSociales.js'

const authController = inject('authController')
const impactoSocialController = inject('impactoSocialController')

const AVATAR_COLORS = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b', '#fa709a', '#fee140']

const cargando = ref(true)
const error = ref('')
const saldoDonable = ref(0)
const estadoSocial = ref('NINGUNO')
const usuarioActualId = ref(null)
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
const avisoDonacion = ref('')
const comprobanteDonacion = ref(null)

const modalDonacion = reactive({
  tipo: 'causa',
  solicitudId: null,
  titulo: '',
  monto: '',
  horasRecibidasDonacionSolicitante: 0,
  horasDeVidaSolicitante: 0,
})

const puedeDonar = computed(() => saldoDonable.value > 0)

const totalHorasSolidarias = computed(() => calcularHorasSolidariasTotales(misSolicitudes.value))

const totalHorasDonadas = computed(() => calcularMontoDonacionesTotales(donacionesRealizadas.value))

const esPropiaCausa = (causa) => Number(causa.solicitanteId) === Number(usuarioActualId.value)

const causasDonables = computed(() => (
  causasAprobadas.value.filter((causa) => !esPropiaCausa(causa))
))

const mostrarBadgeEstadoSocial = computed(() => ['VULNERABLE', 'CRITICO'].includes(estadoSocial.value))

const titulosCausaDisponibles = computed(() => titulosCausaSocialPorCategoria(formSolicitud.categoria))

watch(() => formSolicitud.categoria, () => {
  formSolicitud.titulo = ''
})

const horasRestantesReceptor = computed(() => {
  if (modalDonacion.tipo !== 'causa') return null
  return calcularHorasRestantesReceptor(
    modalDonacion.horasRecibidasDonacionSolicitante,
    modalDonacion.horasDeVidaSolicitante,
  )
})

const avisoReceptorModal = computed(() => {
  if (modalDonacion.tipo !== 'causa') return null

  if (modalDonacion.horasDeVidaSolicitante > TOPE_HORAS_RECIBIDAS_DONACION) {
    return { tipo: 'error', texto: MENSAJE_RECEPTOR_MAS_10_HORAS }
  }

  const restantes = horasRestantesReceptor.value ?? 0
  if (restantes === 0) {
    return {
      tipo: 'error',
      texto: Number(modalDonacion.horasRecibidasDonacionSolicitante) >= TOPE_HORAS_RECIBIDAS_DONACION
        ? MENSAJE_TOPE_USUARIO_ALCANZADO
        : MENSAJE_TOPE_HORAS_RECIBIDAS,
    }
  }

  return {
    tipo: 'info',
    texto: (
      `Este usuario recibió ${Number(modalDonacion.horasRecibidasDonacionSolicitante).toFixed(1)} / ` +
      `${TOPE_HORAS_RECIBIDAS_DONACION} h y puede recibir hasta ${restantes.toFixed(1)} h más.`
    ),
  }
})

const horasRecibidasDonacionUsuario = (causa) => (
  Number(causa.horasRecibidasDonacionSolicitante || 0)
)

const horasRestantesReceptorCausa = (causa) => calcularHorasRestantesReceptor(
  horasRecibidasDonacionUsuario(causa),
  causa.horasDeVidaSolicitante,
)

const receptorAlcanzoTopeDonaciones = (causa) => (
  horasRecibidasDonacionUsuario(causa) >= TOPE_HORAS_RECIBIDAS_DONACION
)

const receptorPuedeRecibirDonacion = (causa) => (
  horasRestantesReceptorCausa(causa) > 0
)

const formatearTopeDonacionesUsuario = (causa) => (
  `${horasRecibidasDonacionUsuario(causa).toFixed(1)} / ${TOPE_HORAS_RECIBIDAS_DONACION} h recibidas (total)`
)

const mensajeAvisoReceptorCausa = (causa) => {
  if (Number(causa.horasDeVidaSolicitante) > TOPE_HORAS_RECIBIDAS_DONACION) {
    return MENSAJE_RECEPTOR_MAS_10_HORAS
  }
  if (receptorAlcanzoTopeDonaciones(causa)) {
    return MENSAJE_TOPE_USUARIO_ALCANZADO
  }
  return ''
}

const tituloBotonDonarCausa = (causa) => {
  if (!puedeDonar.value) return MENSAJE_SALDO_POSITIVO_DONACION
  return mensajeAvisoReceptorCausa(causa)
}

const puedeAbrirModalDonacion = (tipo, causa = null) => {
  if (!puedeDonar.value) {
    avisoDonacion.value = MENSAJE_SALDO_POSITIVO_DONACION
    return false
  }

  if (tipo === 'causa' && causa) {
    if (esPropiaCausa(causa)) {
      avisoDonacion.value = 'No puedes donar horas a tu propia causa.'
      return false
    }

    const avisoReceptor = mensajeAvisoReceptorCausa(causa)
    if (avisoReceptor) {
      avisoDonacion.value = avisoReceptor
      return false
    }
  }

  return true
}

const montoModalValido = computed(() => {
  const monto = Number(modalDonacion.monto)
  if (!Number.isFinite(monto)) return false
  if (monto < 0.5) return false
  if (saldoDonable.value <= 0) return false
  if (monto > saldoDonable.value) return false

  if (modalDonacion.tipo === 'causa') {
    if (modalDonacion.horasDeVidaSolicitante > TOPE_HORAS_RECIBIDAS_DONACION) return false
    if (monto > (horasRestantesReceptor.value ?? 0)) return false
  }

  return true
})

const errorMontoModal = computed(() => {
  const monto = Number(modalDonacion.monto)
  if (!Number.isFinite(monto) || monto < 0.5) {
    return 'El monto mínimo de donación es 0.5 horas'
  }
  if (saldoDonable.value <= 0) {
    return MENSAJE_SALDO_POSITIVO_DONACION
  }
  if (monto > saldoDonable.value) {
    return 'No puedes donar tiempo prestado'
  }
  if (modalDonacion.tipo === 'causa') {
    if (modalDonacion.horasDeVidaSolicitante > TOPE_HORAS_RECIBIDAS_DONACION) {
      return MENSAJE_RECEPTOR_MAS_10_HORAS
    }
    if (monto > (horasRestantesReceptor.value ?? 0)) {
      return Number(modalDonacion.horasRecibidasDonacionSolicitante) >= TOPE_HORAS_RECIBIDAS_DONACION
        ? MENSAJE_TOPE_USUARIO_ALCANZADO
        : `El monto supera el cupo restante (${(horasRestantesReceptor.value ?? 0).toFixed(1)} h).`
    }
  }
  return ''
})

const getInitials = (nombre, fallback) => (nombre || fallback || 'C').charAt(0).toUpperCase()

const getAvatarColor = (texto) => {
  const index = (texto || 'c').charCodeAt(0) % AVATAR_COLORS.length
  return AVATAR_COLORS[index]
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

const claseEstadoSocial = (estado) => {
  if (estado === 'VULNERABLE') return 'badge--alta'
  if (estado === 'CRITICO') return 'badge--critica'
  return 'badge--normal'
}

const puedeActivarNecesidad = (solicitud) => (
  solicitud.estado === 'APROBADA'
  && !solicitud.publicacionId
  && !solicitud.necesidadActiva
)

const formatearFecha = (fecha) => {
  if (!fecha) return '—'
  return new Date(fecha).toLocaleString('es-ES')
}

const cargarSaldoUsuario = async () => {
  const sesion = await authController.obtenerSesionActual()
  usuarioActualId.value = sesion?.id ?? null
  saldoDonable.value = Number(sesion?.horasDeVida || 0)
  estadoSocial.value = sesion?.estadoSocial || 'NINGUNO'
}

const cargarDatos = async () => {
  cargando.value = true
  error.value = ''

  try {
    await cargarSaldoUsuario()

    const [causas, propias, historial] = await Promise.all([
      impactoSocialController.obtenerSolicitudesAprobadas(),
      impactoSocialController.obtenerMisSolicitudes(),
      impactoSocialController.obtenerMisDonaciones(),
    ])

    causasAprobadas.value = causas.solicitudes || []
    misSolicitudes.value = propias.solicitudes || []
    donacionesRealizadas.value = historial.realizadas || []
    donacionesRecibidas.value = historial.recibidas || []
  } catch (err) {
    error.value = err.message || 'No se pudo cargar la sección de impacto social.'
  } finally {
    cargando.value = false
  }
}

const publicarSolicitud = async () => {
  procesandoSolicitud.value = true
  mensajeSolicitud.value = ''
  errorSolicitud.value = ''
  mensajeActivacion.value = ''
  errorActivacion.value = ''

  try {
    const respuesta = await impactoSocialController.crearSolicitud(
      formSolicitud.categoria,
      formSolicitud.titulo,
      formSolicitud.descripcion,
    )
    mensajeSolicitud.value = respuesta.mensaje
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
    const respuesta = await impactoSocialController.activarNecesidadVinculada(solicitudId)
    mensajeActivacion.value = respuesta.mensaje
    await cargarDatos()
  } catch (err) {
    errorActivacion.value = err.message || 'No se pudo activar la necesidad vinculada.'
  } finally {
    procesandoActivacionId.value = null
  }
}

const abrirModalDonacion = (tipo, causa = null) => {
  errorDonacion.value = ''

  if (!puedeAbrirModalDonacion(tipo, causa)) {
    mostrarModalDonacion.value = false
    return
  }

  avisoDonacion.value = ''
  comprobanteDonacion.value = null
  modalDonacion.tipo = tipo
  modalDonacion.solicitudId = causa?.id || null
  modalDonacion.titulo = causa?.titulo || 'Fondo Comunitario'
  modalDonacion.monto = ''
  modalDonacion.horasRecibidasDonacionSolicitante = causa?.horasRecibidasDonacionSolicitante ?? 0
  modalDonacion.horasDeVidaSolicitante = causa?.horasDeVidaSolicitante ?? 0
  mostrarModalDonacion.value = true
}

const cerrarModalDonacion = () => {
  mostrarModalDonacion.value = false
  errorDonacion.value = ''
}

const confirmarDonacion = async () => {
  if (!montoModalValido.value) {
    errorDonacion.value = errorMontoModal.value
    return
  }

  procesandoDonacion.value = true
  errorDonacion.value = ''

  try {
    const respuesta = modalDonacion.tipo === 'fondo'
      ? await impactoSocialController.donarAFondo(modalDonacion.monto, saldoDonable.value)
      : await impactoSocialController.donarACausa(
        modalDonacion.solicitudId,
        modalDonacion.monto,
        saldoDonable.value,
        modalDonacion.horasRecibidasDonacionSolicitante,
        modalDonacion.horasDeVidaSolicitante,
      )

    saldoDonable.value = respuesta.saldoRestante
    comprobanteDonacion.value = {
      monto: respuesta.monto,
      receptorNombre: respuesta.receptorNombre || (modalDonacion.tipo === 'fondo' ? 'Fondo Comunitario' : modalDonacion.titulo),
      tipoDestino: respuesta.comprobante?.tipoDestino || (modalDonacion.tipo === 'fondo' ? 'FONDO' : 'CAUSA'),
      comprobanteId: respuesta.comprobante?.comprobanteId || null,
      saldoRestante: respuesta.saldoRestante,
    }
    cerrarModalDonacion()
    avisoDonacion.value = ''
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
.panel--metricas {
  margin-bottom: 0;
}

.panel--metricas .panel__body {
  padding-top: 0.5rem;
}

.metric-row--impacto {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.metric--destacada {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border: 2px solid #43a047;
  border-radius: 10px;
  padding: 0.75rem 1rem;
}

.metric--destacada .metric__value {
  color: #2e7d32;
}

.metric--destacada .metric__label {
  color: #1b5e20;
  font-weight: 600;
}

.page-header__badge {
  margin: 0.75rem 0 0;
}

.panel__hint--inline {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
  color: #666;
}

.panel__subtitle {
  margin: 1.25rem 0 0.75rem;
  font-size: 1rem;
  font-weight: 600;
  color: #333;
}

.panel__subtitle:first-child {
  margin-top: 0;
}

.comprobante {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #c3e6cb;
  background: #f4fbf6;
}

.comprobante__titulo {
  margin: 0 0 0.75rem;
  font-weight: 700;
  color: #155724;
}

.comprobante__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin: 0 0 0.75rem;
}

.comprobante__item {
  margin: 0;
}

.comprobante__item dt {
  margin: 0 0 0.15rem;
  font-size: 0.75rem;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.comprobante__item dd {
  margin: 0;
  font-weight: 600;
  color: #333;
}

.comprobante__balance {
  margin: 0;
  font-size: 0.9rem;
  color: #444;
}

.alert--diferencia-cartelera {
  margin-top: 0;
}

.alert__titulo {
  margin: 0 0 0.5rem;
  font-weight: 700;
}

.alert__lista {
  margin: 0 0 0.75rem;
  padding-left: 1.25rem;
}

.alert__lista li {
  margin-bottom: 0.35rem;
}

.alert__nota {
  margin: 0;
  font-size: 0.92rem;
}

.acciones-celda {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.aviso-causa {
  flex-basis: 100%;
  margin: 0.35rem 0 0;
  color: #856404;
}

.aviso-causa--tope {
  color: #842029;
  font-weight: 600;
}

@media (max-width: 640px) {
  .metric-row--impacto {
    grid-template-columns: 1fr;
  }
}

.button--compact {
  padding: 0.35rem 0.75rem;
  font-size: 0.85rem;
}
</style>
