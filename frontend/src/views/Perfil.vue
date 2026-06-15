<template>
  <section class="perfil-page">
    <div class="panel panel--compact">
      <div class="panel__header">
        <h2 class="panel__title">Mi Perfil</h2>
      </div>
      <div class="panel__body" v-if="cargando">
        <div class="loading-state">Cargando perfil...</div>
      </div>
      <div class="panel__body" v-else-if="error">
        <p class="alert alert--error">{{ error }}</p>
      </div>
      <div class="panel__body" v-else-if="datosPerfil">
        <div class="perfil-info">
          <div class="perfil-header">
            <div class="perfil-avatar" :style="{ backgroundColor: getAvatarColor() }">
              {{ getInitials() }}
            </div>
            <div class="perfil-datos-principales">
              <div class="perfil-nombre-fila">
                <h3>{{ datosPerfil.usuario.nombre_real }}</h3>
                <span v-if="esComercioAfiliado" class="badge badge--activa">Comercio Afiliado</span>
                <span v-else-if="esMiembroActivo" class="badge badge--activa">Miembro Activo</span>
              </div>
              <p class="perfil-username">@{{ datosPerfil.usuario.username }}</p>
              <p class="perfil-email">{{ datosPerfil.usuario.email }}</p>
            </div>
          </div>

          <div v-if="!esComercioAfiliado" class="perfil-estadisticas">
            <div class="estadistica-card">
              <div class="estadistica-icon">ESTRELLAS</div>
              <div class="estadistica-info">
                <div class="estadistica-valor">{{ promedioEstrellas.toFixed(1) }}</div>
                <div class="estadistica-label">Calificación</div>
              </div>
            </div>
            <div class="estadistica-card">
              <div class="estadistica-icon">HORAS</div>
              <div class="estadistica-info">
                <div class="estadistica-valor">{{ datosPerfil.usuario.horas_de_vida.toFixed(1) }}</div>
                <div class="estadistica-label">Horas de vida (general)</div>
              </div>
            </div>
            <div v-if="tieneSaldoComercial" class="estadistica-card">
              <div class="estadistica-icon">SALDO</div>
              <div class="estadistica-info">
                <div class="estadistica-valor">{{ saldoComercial.toFixed(2) }}</div>
                <div class="estadistica-label">Saldo a favor</div>
              </div>
            </div>
          </div>

          <template v-if="esComercioAfiliado">
            <p class="alert alert--info perfil-comercial-aviso">
              Tu cuenta es comercial; gestiona operaciones en Red Comercial.
            </p>
            <p class="perfil-comercial-resumen">
              Consulta tu balance e historial de movimientos en Red Comercial.
            </p>
            <p class="perfil-red-comercial-link">
              <button class="link-button" type="button" @click="irRedComercial">
                Ir a Red Comercial →
              </button>
            </p>
          </template>

          <p v-else-if="tieneSaldoComercial" class="perfil-red-comercial-link">
            <button class="link-button" type="button" @click="irRedComercial">
              Ir a Red Comercial →
            </button>
          </p>

          <template v-if="!esComercioAfiliado">
          <div class="perfil-seccion">
            <h4>Publicaciones Activas ({{ publicacionesActivas.length }})</h4>
            <div v-if="publicacionesActivas.length === 0" class="empty-state">
              No tienes publicaciones activas
            </div>
            <div v-else class="publicaciones-lista">
              <div
                v-for="pub in publicacionesActivas"
                :key="pub.id"
                class="publicacion-item"
              >
                <div class="publicacion-tipo" :class="'publicacion-tipo--' + pub.tipo.toLowerCase()">
                  {{ pub.tipo === 'TALENTO' ? 'Talento' : 'Necesidad' }}
                </div>
                <div class="publicacion-info">
                  <div class="publicacion-estado">
                    <span class="estado-badge estado-badge--activa">Activa</span>
                  </div>
                  <h5>{{ pub.titulo }}</h5>
                  <p>{{ pub.descripcion }}</p>
                  <div class="publicacion-meta">
                    <span class="categoria">{{ pub.categoria }}</span>
                    <span class="urgencia" :class="'urgencia--' + pub.urgencia.toLowerCase()">
                      {{ pub.urgencia }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="publicacionesPausadas.length" class="perfil-seccion">
            <h4>Publicaciones Pausadas ({{ publicacionesPausadas.length }})</h4>
            <div class="publicaciones-lista">
              <div
                v-for="pub in publicacionesPausadas"
                :key="pub.id"
                class="publicacion-item publicacion-item--pausada"
              >
                <div class="publicacion-tipo" :class="'publicacion-tipo--' + pub.tipo.toLowerCase()">
                  {{ pub.tipo === 'TALENTO' ? 'Talento' : 'Necesidad' }}
                </div>
                <div class="publicacion-info">
                  <div class="publicacion-estado">
                    <span class="estado-badge estado-badge--pausada">Pausada</span>
                  </div>
                  <h5>{{ pub.titulo }}</h5>
                  <p>{{ pub.descripcion }}</p>
                  <div class="publicacion-meta">
                    <span class="categoria">{{ pub.categoria }}</span>
                    <span class="urgencia" :class="'urgencia--' + pub.urgencia.toLowerCase()">
                      {{ pub.urgencia }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="perfil-seccion">
            <h4>⭐ Reseñas Recibidas ({{ cantidadResenas }})</h4>
            <div v-if="!datosPerfil?.resenas_recibidas || datosPerfil.resenas_recibidas.length === 0" class="empty-state">
              No has recibido reseñas aún
            </div>
            <div v-else class="resenas-lista">
              <div v-for="resena in datosPerfil.resenas_recibidas" :key="resena.id" class="resena-item">
                <div class="resena-calificacion">
                  <span class="estrellas">{{ '⭐'.repeat(resena.estrellas) }}</span>
                  <span class="calificador">por @{{ nombreCalificador(resena) }}</span>
                </div>
                <p class="resena-comentario">{{ resena.comentario }}</p>
              </div>
            </div>
          </div>

          <div class="perfil-seccion">
            <h4>Mis trueques ({{ misTrueques.length }})</h4>
            <div v-if="cargandoTrueques" class="loading-state">Cargando trueques...</div>
            <div v-else-if="!misTrueques.length" class="empty-state">
              No tienes acuerdos de trueque registrados.
            </div>
            <div v-else class="trueques-grid">
              <article v-for="trueque in misTrueques" :key="trueque.id" class="trueque-card">
                <div class="trueque-card__header">
                  <strong>{{ nombreContraparte(trueque) }}</strong>
                  <span :class="['trueque-card__estado', claseEstado(trueque.estado)]">
                    {{ trueque.estado }}
                  </span>
                </div>
                <div class="trueque-card__pubs">
                  <span v-if="trueque.es_intercambio_mutuo" class="trueque-mutuo-badge">
                    Intercambio equilibrado (0 horas netas)
                  </span>
                  <span v-if="etiquetaOfertaPropia(trueque)">
                    {{ etiquetaOfertaPropia(trueque) }}: {{ tituloOfertaPropia(trueque) }}
                  </span>
                  <span v-if="etiquetaOfertaContraparte(trueque)">
                    {{ etiquetaOfertaContraparte(trueque) }}: {{ tituloOfertaContraparte(trueque) }}
                  </span>
                  <span
                    v-if="!trueque.es_intercambio_mutuo && trueque.impacto_horas"
                    class="trueque-impacto"
                  >
                    Impacto en tus horas: {{ formatearImpacto(trueque.impacto_horas) }}
                  </span>
                </div>
                <p v-if="mensajeEspera(trueque)" class="trueque-espera">
                  {{ mensajeEspera(trueque) }}
                </p>
                <div class="trueque-card__actions">
                  <button
                    v-if="trueque.estado === 'PENDIENTE'"
                    class="button button--primary button--small"
                    type="button"
                    @click="completarPropuesta(trueque)"
                  >
                    {{ etiquetaPropuestaPendiente(trueque) }}
                  </button>
                  <button
                    v-if="trueque.puede_confirmar"
                    class="button button--primary button--small"
                    type="button"
                    :disabled="procesandoTruequeId === trueque.id"
                    @click="confirmarFinalizacion(trueque)"
                  >
                    Confirmar finalización
                  </button>
                  <button
                    v-if="trueque.pendiente_resena"
                    class="button button--secondary button--small"
                    type="button"
                    @click="abrirResena(trueque)"
                  >
                    Dejar reseña
                  </button>
                </div>
                <p
                  v-if="feedbackTrueque[trueque.id]"
                  :class="['alert', feedbackTruequeOk[trueque.id] ? 'alert--success' : 'alert--error']"
                >
                  {{ feedbackTrueque[trueque.id] }}
                </p>
              </article>
            </div>
          </div>

          <div class="perfil-seccion">
            <h4>Actividad de Trueques</h4>
            <div class="trueques-info">
              <div class="trueque-stat">
                <span class="trueque-label">Propuestas enviadas:</span>
                <span class="trueque-valor">{{ datosPerfil.trueques_enviados_count }}</span>
              </div>
              <div class="trueque-stat">
                <span class="trueque-label">Propuestas recibidas:</span>
                <span class="trueque-valor">{{ datosPerfil.trueques_recibidos_count }}</span>
              </div>
            </div>
          </div>
          </template>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, inject, onMounted, onUnmounted, reactive, ref } from 'vue'

const emit = defineEmits(['ir-red-comercial'])

const authController = inject('authController')
const truequeController = inject('truequeController')
const hu4 = inject('hu4', null)
const datosPerfil = ref(null)
const cargando = ref(true)
const error = ref('')
const misTrueques = ref([])
const cargandoTrueques = ref(false)
const procesandoTruequeId = ref(null)
const feedbackTrueque = reactive({})
const feedbackTruequeOk = reactive({})
const usuarioActualId = ref(null)

const publicacionesActivas = computed(() => {
  if (!datosPerfil.value) return []
  if (Array.isArray(datosPerfil.value.publicaciones_activas)) {
    return datosPerfil.value.publicaciones_activas
  }
  return (datosPerfil.value.publicaciones || []).filter((pub) => pub.esta_activa)
})

const publicacionesPausadas = computed(() => {
  if (!datosPerfil.value) return []
  if (Array.isArray(datosPerfil.value.publicaciones_pausadas)) {
    return datosPerfil.value.publicaciones_pausadas
  }
  return (datosPerfil.value.publicaciones || []).filter((pub) => !pub.esta_activa)
})

const esMiembroActivo = computed(() => {
  if (!datosPerfil.value) return false
  if (typeof datosPerfil.value.es_miembro_activo === 'boolean') {
    return datosPerfil.value.es_miembro_activo
  }
  const usuario = datosPerfil.value.usuario
  const publicaciones = datosPerfil.value.publicaciones || []
  return Boolean(usuario?.nombre_real?.trim() && publicaciones.length > 0)
})

const promedioEstrellas = computed(() => {
  if (!datosPerfil.value) return 5.0
  return datosPerfil.value.promedio_estrellas
    ?? datosPerfil.value.usuario?.promedio_estrellas
    ?? 5.0
})

const cantidadResenas = computed(() => {
  if (!datosPerfil.value) return 0
  if (typeof datosPerfil.value.cantidad_resenas === 'number') {
    return datosPerfil.value.cantidad_resenas
  }
  return datosPerfil.value.resenas_recibidas?.length ?? 0
})

const esComercioAfiliado = computed(() => Boolean(datosPerfil.value?.usuario?.es_comercio))

const tieneSaldoComercial = computed(() => datosPerfil.value?.saldo_comercial != null)

const saldoComercial = computed(() => Number(datosPerfil.value?.saldo_comercial ?? 0))

const irRedComercial = () => emit('ir-red-comercial')

const nombreCalificador = (resena) => {
  if (resena.calificador_username) return resena.calificador_username
  if (resena.calificador?.username) return resena.calificador.username
  if (resena.calificador_nombre) return resena.calificador_nombre
  return 'usuario'
}

const cargarPerfil = async () => {
  try {
    const response = await authController.obtenerMiPerfil()
    datosPerfil.value = response
  } catch (err) {
    error.value = 'Error al cargar el perfil: ' + (err.message || 'Error desconocido')
  } finally {
    cargando.value = false
  }
}

const cargarMisTrueques = async () => {
  cargandoTrueques.value = true
  try {
    const data = await truequeController.obtenerMisTrueques()
    misTrueques.value = data.trueques || []
  } catch {
    misTrueques.value = []
  } finally {
    cargandoTrueques.value = false
  }
}

const nombreContraparte = (trueque) => {
  if (Number(trueque.emisor) === Number(usuarioActualId.value)) return trueque.receptor_nombre
  return trueque.emisor_nombre
}

const tituloOfertaPropia = (trueque) => (
  trueque.oferta_propia_titulo
  || (Number(trueque.emisor) === Number(usuarioActualId.value)
    ? trueque.publicacion_emisor?.titulo
    : trueque.publicacion_receptor?.titulo)
  || ''
)

const tituloOfertaContraparte = (trueque) => (
  trueque.oferta_contraparte_titulo
  || (Number(trueque.emisor) === Number(usuarioActualId.value)
    ? trueque.publicacion_receptor?.titulo
    : trueque.publicacion_emisor?.titulo)
  || ''
)

const etiquetaOfertaPropia = (trueque) => (trueque.es_intercambio_mutuo ? 'Yo ofrezco' : 'Ofrezco')

const etiquetaOfertaContraparte = (trueque) => (
  trueque.es_intercambio_mutuo ? 'Recibo de contraparte' : 'Solicito'
)

const formatearImpacto = (impacto) => {
  if (impacto > 0) return `+${impacto.toFixed(1)} h`
  if (impacto < 0) return `${impacto.toFixed(1)} h`
  return '0 h'
}

const claseEstado = (estado) => {
  const mapa = {
    ACEPTADO: 'trueque-card__estado--aceptado',
    FINALIZADO: 'trueque-card__estado--finalizado',
    RECHAZADO: 'trueque-card__estado--rechazado',
    PENDIENTE: 'trueque-card__estado--pendiente',
  }
  return mapa[estado] || 'trueque-card__estado--pendiente'
}

const mensajeEspera = (trueque) => {
  if (trueque.estado !== 'ACEPTADO') return ''
  if (trueque.emisor === usuarioActualId.value && trueque.emisor_confirmado && !trueque.receptor_confirmado) {
    return `Esperando confirmación de ${trueque.receptor_nombre}`
  }
  if (trueque.receptor === usuarioActualId.value && trueque.receptor_confirmado && !trueque.emisor_confirmado) {
    return `Esperando confirmación de ${trueque.emisor_nombre}`
  }
  return ''
}

const confirmarFinalizacion = async (trueque) => {
  procesandoTruequeId.value = trueque.id
  feedbackTrueque[trueque.id] = ''
  feedbackTruequeOk[trueque.id] = false

  try {
    const resultado = await truequeController.finalizarTrueque(trueque.id)
    feedbackTruequeOk[trueque.id] = true
    feedbackTrueque[trueque.id] = resultado.message || 'Confirmación registrada.'
    await cargarPerfil()

    if (resultado.habilitar_resena) {
      await cargarMisTrueques()
      const truequeActualizado = misTrueques.value.find((item) => item.id === trueque.id)
      if (truequeActualizado?.pendiente_resena && hu4?.abrirModalResenaPrioritario) {
        hu4.abrirModalResenaPrioritario(truequeActualizado)
      }
    } else {
      await cargarMisTrueques()
    }

    if (hu4?.refrescarDatosHu4) {
      await hu4.refrescarDatosHu4({ omitirModalesAutomaticos: resultado.habilitar_resena })
    }
  } catch (err) {
    feedbackTrueque[trueque.id] = err.message || 'No se pudo confirmar el trueque.'
  } finally {
    procesandoTruequeId.value = null
  }
}

const abrirResena = (trueque) => {
  if (hu4?.abrirModalResena) {
    hu4.abrirModalResena(trueque)
  }
}

const etiquetaPropuestaPendiente = (trueque) => {
  if (trueque.publicacion_emisor && trueque.publicacion_receptor) {
    return 'Completar propuesta'
  }
  return 'Realizar trueque'
}

const completarPropuesta = async (trueque) => {
  if (hu4?.abrirModalPropuestaDesdeTrueque) {
    await hu4.abrirModalPropuestaDesdeTrueque(trueque)
  }
}

const getInitials = () => {
  const nombre = datosPerfil.value?.usuario?.nombre_real || datosPerfil.value?.usuario?.username || 'U'
  return nombre.charAt(0).toUpperCase()
}

const getAvatarColor = () => {
  const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b', '#fa709a', '#fee140']
  const username = datosPerfil.value?.usuario?.username || ''
  const index = username.charCodeAt(0) % colors.length
  return colors[index]
}

const refrescarVistaPerfil = async () => {
  await cargarPerfil()
  if (!datosPerfil.value?.usuario?.es_comercio) {
    await cargarMisTrueques()
  }
}

onMounted(async () => {
  const sesion = await authController.obtenerSesionActual()
  usuarioActualId.value = sesion?.id ?? null
  if (hu4?.registrarRefrescarPerfil) {
    hu4.registrarRefrescarPerfil(refrescarVistaPerfil)
  }
  await refrescarVistaPerfil()
})

onUnmounted(() => {
  if (hu4?.registrarRefrescarPerfil) {
    hu4.registrarRefrescarPerfil(null)
  }
})
</script>

<style scoped>
.perfil-page {
  padding: 1rem;
  max-width: 800px;
  margin: 0 auto;
}

.panel--compact {
  max-width: 100%;
  margin: 0 auto;
}

.perfil-info {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.perfil-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e0e0e0;
}

.perfil-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  font-weight: bold;
  color: white;
  flex-shrink: 0;
}

.perfil-nombre-fila {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 0.25rem;
}

.perfil-datos-principales h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #333;
}

.perfil-username {
  margin: 0 0 0.25rem 0;
  color: #666;
  font-weight: 500;
  font-size: 0.9rem;
}

.perfil-email {
  margin: 0;
  color: #888;
  font-size: 0.8rem;
}

.perfil-estadisticas {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.75rem;
}

.perfil-red-comercial-link {
  margin: 0 0 1rem;
}

.perfil-comercial-resumen {
  margin: 0 0 0.5rem;
  color: #666;
  font-size: 0.9rem;
}

.estadistica-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.estadistica-icon {
  font-size: 1.5rem;
}

.estadistica-valor {
  font-size: 1.2rem;
  font-weight: bold;
  color: #333;
}

.estadistica-label {
  color: #666;
  font-size: 0.8rem;
}

.perfil-seccion {
  margin-top: 1.5rem;
}

.perfil-seccion h4 {
  margin: 0 0 0.75rem 0;
  color: #333;
  font-size: 1.1rem;
}

.empty-state {
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
  color: #666;
  text-align: center;
  border: 1px dashed #ccc;
  font-size: 0.9rem;
}

.publicaciones-lista,
.resenas-lista {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.publicacion-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #667eea;
  font-size: 0.9rem;
}

.publicacion-item--pausada {
  opacity: 0.72;
  border-left-color: #adb5bd;
  background: #f1f3f5;
}

.publicacion-estado {
  margin-bottom: 0.35rem;
}

.estado-badge {
  display: inline-block;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
}

.estado-badge--activa {
  background: #e7f7f1;
  color: #175f49;
}

.estado-badge--pausada {
  background: #e9ecef;
  color: #5f6b7a;
}

.publicacion-tipo {
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-weight: bold;
  font-size: 0.7rem;
  white-space: nowrap;
}

.publicacion-tipo--talento {
  background: #d4edda;
  color: #155724;
}

.publicacion-tipo--necesidad {
  background: #fff3cd;
  color: #856404;
}

.publicacion-info h5 {
  margin: 0 0 0.25rem 0;
  color: #333;
  font-size: 1rem;
}

.publicacion-info p {
  margin: 0 0 0.25rem 0;
  color: #666;
  font-size: 0.85rem;
}

.publicacion-meta {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.categoria {
  padding: 0.25rem 0.5rem;
  background: #e9ecef;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #495057;
}

.urgencia {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: bold;
}

.urgencia--normal {
  background: #d4edda;
  color: #155724;
}

.urgencia--alta {
  background: #fff3cd;
  color: #856404;
}

.urgencia--critica {
  background: #f8d7da;
  color: #721c24;
}

.resena-item {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #ffc107;
}

.resena-calificacion {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.estrellas {
  color: #ffc107;
  font-size: 1.2rem;
}

.calificador {
  color: #666;
  font-weight: 500;
}

.resena-comentario {
  margin: 0;
  color: #333;
  font-style: italic;
}

.trueques-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.trueque-stat {
  display: flex;
  justify-content: space-between;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.trueque-label {
  color: #666;
}

.trueque-valor {
  font-weight: bold;
  color: #333;
  font-size: 1.2rem;
}
</style>
