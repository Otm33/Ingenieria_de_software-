<template>
  <div v-if="visible" class="modal-overlay" @click.self="cerrar">
    <div class="modal-content">
      <div class="modal-header">
        <h3 class="modal-title">Notificaciones</h3>
        <button class="modal-close" type="button" aria-label="Cerrar" @click="cerrar">×</button>
      </div>
      <div class="modal-body">
        <div v-if="!notificaciones.length" class="match-vacio">
          No tienes notificaciones pendientes. Puedes retomar matches desde Perfil → Mis trueques.
        </div>
        <div v-else class="match-resultado">
          <article v-for="notif in notificaciones" :key="notif.id" class="match-item match-item--stacked">
            <div class="match-item-info">
              <strong>{{ notif.tipo === 'MATCH' ? 'Match automático' : 'Propuesta de trueque' }}</strong>
              <span>{{ notif.mensaje }}</span>

              <div
                v-if="notif.tipo === 'MATCH' && tieneMatchDetalle(notif)"
                class="match-detalle"
                aria-label="Detalle del intercambio complementario"
              >
                <div
                  v-for="pareja in parejasOrdenadas(notif)"
                  :key="pareja.rol"
                  class="match-detalle-pareja"
                  :class="`match-detalle-pareja--${pareja.rol}`"
                >
                  <span class="match-detalle-line">
                    <span class="match-detalle-label">
                      {{ pareja.rol === 'recibo' ? 'Tú necesitas:' : 'Tú ofreces:' }}
                    </span>
                    {{ pareja.mi_titulo }}
                  </span>
                  <span class="match-detalle-line match-detalle-line--secundaria">
                    <span class="match-detalle-label">
                      {{ pareja.rol === 'recibo' ? 'Ellos ofrecen:' : 'Ellos necesitan:' }}
                    </span>
                    {{ pareja.su_titulo }}
                  </span>
                </div>
              </div>

              <span
                v-if="notif.publicacion_titulo && !(notif.tipo === 'MATCH' && tieneMatchDetalle(notif))"
                class="match-item-meta"
              >
                {{ notif.publicacion_titulo }}
              </span>

              <span v-if="notif.tipo === 'MATCH' && esMatchComplementario(notif)" class="match-item-hint">
                Intercambio equilibrado — 0 horas netas al finalizar
              </span>
            </div>
            <div class="match-item-actions">
              <button
                v-if="notif.tipo === 'MATCH'"
                class="button button--primary button--small"
                type="button"
                :disabled="procesandoId === notif.id"
                @click="realizarTrueque(notif)"
              >
                Realizar trueque
              </button>
              <template v-if="notif.tipo === 'PROPUESTA'">
                <button
                  class="button button--primary button--small"
                  type="button"
                  :disabled="procesandoId === notif.id"
                  @click="responder(notif, 'ACEPTAR')"
                >
                  Aceptar
                </button>
                <button
                  class="button button--danger button--small"
                  type="button"
                  :disabled="procesandoId === notif.id"
                  @click="responder(notif, 'RECHAZAR')"
                >
                  Rechazar
                </button>
              </template>
              <button
                class="button button--secondary button--small"
                type="button"
                :disabled="procesandoId === notif.id"
                @click="descartar(notif)"
              >
                Descartar
              </button>
            </div>
            <p v-if="errorPorId[notif.id]" class="alert alert--error">{{ errorPorId[notif.id] }}</p>
          </article>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/*
 * Checklist validación manual Fase 2 (match complementario):
 * [ ] Dos usuarios con catálogo complementario completo: al publicar la necesidad que
 *     completa el match, ambos ven el modal con las DOS parejas (recibo + doy).
 * [ ] Notificación PROPUESTA sigue mostrando Aceptar/Rechazar sin cambios visuales.
 * [ ] "Realizar trueque" abre ModalPropuesta con publicaciones preseleccionadas.
 * [ ] Notificaciones MATCH antiguas sin match_detalle: solo mensaje + publicacion_titulo.
 */
import { inject, reactive, ref } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  notificaciones: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:visible', 'realizar-trueque', 'actualizado'])

const truequeController = inject('truequeController')
const procesandoId = ref(null)
const errorPorId = reactive({})

const tieneMatchDetalle = (notif) => (
  notif.tipo === 'MATCH'
  && Array.isArray(notif.match_detalle)
  && notif.match_detalle.length >= 2
  && notif.match_detalle.some((entrada) => entrada.rol === 'recibo')
  && notif.match_detalle.some((entrada) => entrada.rol === 'doy')
)

const parejasOrdenadas = (notif) => {
  const orden = { recibo: 0, doy: 1 }
  return [...(notif.match_detalle || [])].sort(
    (a, b) => (orden[a.rol] ?? 2) - (orden[b.rol] ?? 2),
  )
}

const esMatchComplementario = (notif) => (
  notif.tipo === 'MATCH'
  && (
    tieneMatchDetalle(notif)
    || notif.mensaje?.includes('complementario')
    || notif.mensaje?.includes('0 horas netas')
    || notif.mensaje?.includes('Tú necesitas')
  )
)

const cerrar = () => {
  emit('update:visible', false)
}

const descartar = async (notif) => {
  procesandoId.value = notif.id
  errorPorId[notif.id] = ''
  try {
    await truequeController.marcarNotificacionLeida(notif.id)
    emit('actualizado')
  } catch (error) {
    errorPorId[notif.id] = error.message || 'No se pudo descartar la notificación.'
  } finally {
    procesandoId.value = null
  }
}

const realizarTrueque = (notif) => {
  errorPorId[notif.id] = ''
  emit('realizar-trueque', notif)
}

const responder = async (notif, accion) => {
  procesandoId.value = notif.id
  errorPorId[notif.id] = ''
  try {
    await truequeController.responderPropuesta(notif.trueque_id, accion)
    await truequeController.marcarNotificacionLeida(notif.id)
    emit('actualizado')
  } catch (error) {
    errorPorId[notif.id] = error.message || 'No se pudo responder la propuesta.'
  } finally {
    procesandoId.value = null
  }
}
</script>
