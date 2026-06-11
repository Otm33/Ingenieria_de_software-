<template>
  <div v-if="visible" class="modal-overlay" @click.self="cerrar">
    <div class="modal-content modal-content--confirmacion">
      <div class="modal-header">
        <h3 class="modal-title">Proponer trueque</h3>
        <button class="modal-close" type="button" aria-label="Cerrar" @click="cerrar">×</button>
      </div>
      <form class="modal-body" @submit.prevent="confirmar">
        <p v-if="receptorNombre" class="match-mensaje">
          Intercambio con <strong>{{ receptorNombre }}</strong>
        </p>
        <p v-if="esModoComunidad" class="field-hint">
          Modo:
          <strong>{{ modoPropuesta === 'pedir_ayuda' ? 'Quiero que me ayude' : 'Quiero ayudarle' }}</strong>
          · Impacto estimado al finalizar: <strong>{{ impactoEstimado }}</strong>
        </p>
        <p v-else-if="esIntercambioMutuo" class="alert alert--success">
          Intercambio equilibrado: ambos ofrecen un talento. <strong>0 horas netas</strong> al finalizar.
        </p>
        <p v-else-if="publicacionEmisorId && publicacionReceptorId" class="field-hint">
          Impacto estimado al finalizar: <strong>{{ impactoEstimado }}</strong>
        </p>

        <p v-if="mensajeSinMisPublicaciones" class="alert alert--warning">
          {{ mensajeSinMisPublicaciones }}
        </p>
        <p v-if="mensajeSinPublicacionesVecino" class="alert alert--warning">
          {{ mensajeSinPublicacionesVecino }}
        </p>

        <div class="form-group">
          <label for="mi_publicacion">{{ etiquetaMiPublicacion }}</label>
          <select
            id="mi_publicacion"
            v-model="publicacionEmisorId"
            class="select"
            :required="misPublicacionesFiltradas.length > 0"
            :disabled="!misPublicacionesFiltradas.length"
          >
            <option value="">Selecciona tu publicación</option>
            <option v-for="pub in misPublicacionesFiltradas" :key="pub.id" :value="pub.id">
              {{ pub.titulo }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="pub_vecino">{{ etiquetaVecinoPublicacion }}</label>
          <select
            id="pub_vecino"
            v-model="publicacionReceptorId"
            class="select"
            :required="publicacionesVecinoFiltradas.length > 0"
            :disabled="!publicacionesVecinoFiltradas.length"
          >
            <option value="">Selecciona publicación del vecino</option>
            <option v-for="pub in publicacionesVecinoFiltradas" :key="pub.id" :value="pub.id">
              {{ pub.titulo }}
            </option>
          </select>
        </div>

        <p v-if="error" class="alert alert--error">{{ error }}</p>

        <div class="modal-footer">
          <button class="button button--secondary" type="button" @click="cerrar">Cancelar</button>
          <button class="button button--primary" type="submit" :disabled="!puedeEnviar">
            {{ enviando ? 'Enviando...' : 'Confirmar propuesta' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  receptorId: { type: [Number, String], default: null },
  receptorNombre: { type: String, default: '' },
  misPublicaciones: { type: Array, default: () => [] },
  publicacionesVecino: { type: Array, default: () => [] },
  modoPropuesta: { type: String, default: '' },
  tipoMiPublicacion: { type: String, default: '' },
  tipoVecinoPublicacion: { type: String, default: '' },
  publicacionEmisorPreseleccionada: { type: [Number, String], default: null },
  publicacionReceptorPreseleccionada: { type: [Number, String], default: null },
})

const emit = defineEmits(['update:visible', 'creada'])

const userController = inject('userController')
const publicacionEmisorId = ref('')
const publicacionReceptorId = ref('')
const enviando = ref(false)
const error = ref('')

const esModoComunidad = computed(() => (
  props.modoPropuesta === 'pedir_ayuda' || props.modoPropuesta === 'ofrecer_ayuda'
))

const misPublicacionesFiltradas = computed(() => {
  const activas = props.misPublicaciones.filter((pub) => pub.esta_activa !== false)
  if (!props.tipoMiPublicacion) return activas
  return activas.filter((pub) => pub.tipo === props.tipoMiPublicacion)
})

const publicacionesVecinoFiltradas = computed(() => {
  const activas = props.publicacionesVecino.filter((pub) => pub.esta_activa !== false)
  if (!props.tipoVecinoPublicacion) return activas
  return activas.filter((pub) => pub.tipo === props.tipoVecinoPublicacion)
})

const etiquetaMiPublicacion = computed(() => {
  if (props.modoPropuesta === 'pedir_ayuda') return 'Lo que yo necesito'
  if (props.modoPropuesta === 'ofrecer_ayuda') return 'Mi talento (lo que ofrezco)'
  const tipo = props.tipoMiPublicacion || 'TALENTO o NECESIDAD'
  return `Mi publicación (${tipo})`
})

const etiquetaVecinoPublicacion = computed(() => {
  if (props.modoPropuesta === 'pedir_ayuda') return 'Talento del vecino que me puede ayudar'
  if (props.modoPropuesta === 'ofrecer_ayuda') return 'Necesidad del vecino que puedo resolver'
  const tipo = props.tipoVecinoPublicacion || 'TALENTO o NECESIDAD'
  return `Publicación del vecino (${tipo})`
})

const publicacionEmisorSeleccionada = computed(() => (
  props.misPublicaciones.find((pub) => Number(pub.id) === Number(publicacionEmisorId.value))
))

const publicacionReceptorSeleccionada = computed(() => (
  props.publicacionesVecino.find((pub) => Number(pub.id) === Number(publicacionReceptorId.value))
))

const esIntercambioMutuo = computed(() => (
  !esModoComunidad.value
  && publicacionEmisorSeleccionada.value?.tipo === 'TALENTO'
  && publicacionReceptorSeleccionada.value?.tipo === 'TALENTO'
))

const impactoEstimado = computed(() => {
  if (props.modoPropuesta === 'pedir_ayuda') return '-1 h para ti'
  if (props.modoPropuesta === 'ofrecer_ayuda') return '+1 h para ti'
  if (esIntercambioMutuo.value) return '0 horas netas'
  const mi = publicacionEmisorSeleccionada.value
  const vecino = publicacionReceptorSeleccionada.value
  if (mi?.tipo === 'TALENTO' && vecino?.tipo === 'NECESIDAD') return '+1 h para ti'
  if (mi?.tipo === 'NECESIDAD' && vecino?.tipo === 'TALENTO') return '-1 h para ti'
  return '±1 h según roles'
})

const mensajeSinMisPublicaciones = computed(() => {
  if (!esModoComunidad.value || misPublicacionesFiltradas.value.length) return ''
  if (props.modoPropuesta === 'pedir_ayuda') {
    return 'No tienes necesidades activas publicadas. Publica una necesidad antes de solicitar ayuda.'
  }
  return 'No tienes talentos activos publicados. Publica un talento antes de ofrecer ayuda.'
})

const mensajeSinPublicacionesVecino = computed(() => {
  if (!esModoComunidad.value || publicacionesVecinoFiltradas.value.length) return ''
  if (props.modoPropuesta === 'pedir_ayuda') {
    return 'Este vecino no tiene talentos activos que puedan ayudarte.'
  }
  return 'Este vecino no tiene necesidades activas que puedas resolver.'
})

const puedeEnviar = computed(() => (
  !enviando.value
  && misPublicacionesFiltradas.value.length > 0
  && publicacionesVecinoFiltradas.value.length > 0
))

const validarCombinacion = () => {
  if (!esModoComunidad.value) return true

  const mi = publicacionEmisorSeleccionada.value
  const vecino = publicacionReceptorSeleccionada.value

  if (!mi || !vecino) {
    error.value = 'Selecciona ambas publicaciones para continuar.'
    return false
  }

  if (props.modoPropuesta === 'pedir_ayuda') {
    if (mi.tipo !== 'NECESIDAD' || vecino.tipo !== 'TALENTO') {
      error.value = 'En este modo debes elegir tu necesidad y un talento del vecino.'
      return false
    }
  }

  if (props.modoPropuesta === 'ofrecer_ayuda') {
    if (mi.tipo !== 'TALENTO' || vecino.tipo !== 'NECESIDAD') {
      error.value = 'En este modo debes elegir tu talento y una necesidad del vecino.'
      return false
    }
  }

  return true
}

const aplicarPreseleccion = () => {
  publicacionEmisorId.value = props.publicacionEmisorPreseleccionada || ''
  publicacionReceptorId.value = props.publicacionReceptorPreseleccionada || ''
  error.value = ''
}

watch(
  () => props.visible,
  (visible) => {
    if (visible) aplicarPreseleccion()
  },
)

const cerrar = () => {
  emit('update:visible', false)
}

const confirmar = async () => {
  if (!props.receptorId) {
    error.value = 'Falta el receptor de la propuesta.'
    return
  }

  if (!validarCombinacion()) {
    return
  }

  enviando.value = true
  error.value = ''

  try {
    const resultado = await userController.crearPropuesta(
      props.receptorId,
      publicacionEmisorId.value,
      publicacionReceptorId.value,
    )
    emit('creada', resultado)
    emit('update:visible', false)
  } catch (err) {
    error.value = err.message || 'No se pudo enviar la propuesta.'
  } finally {
    enviando.value = false
  }
}
</script>
