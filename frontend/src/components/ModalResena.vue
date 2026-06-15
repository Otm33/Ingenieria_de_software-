<template>
  <div v-if="visible" class="modal-overlay" @click.self="cerrar">
    <div class="modal-content modal-content--confirmacion">
      <div class="modal-header">
        <h3 class="modal-title">Dejar reseña</h3>
        <button class="modal-close" type="button" aria-label="Cerrar" @click="cerrar">×</button>
      </div>
      <form class="modal-body" @submit.prevent="enviar">
        <p v-if="contraparteNombre" class="match-mensaje">
          Califica tu experiencia con <strong>{{ contraparteNombre }}</strong>
        </p>

        <p v-if="estadoTrueque && estadoTrueque !== 'FINALIZADO'" class="alert alert--error">
          Solo puedes dejar reseña cuando el trueque esté <strong>FINALIZADO</strong>.
          Estado actual: {{ estadoTrueque }}.
        </p>

        <div class="form-group">
          <label for="estrellas_resena">Estrellas (1 a 5)</label>
          <select id="estrellas_resena" v-model.number="estrellas" class="select" required>
            <option v-for="n in 5" :key="n" :value="n">{{ n }} {{ n === 1 ? 'estrella' : 'estrellas' }}</option>
          </select>
        </div>

        <div class="form-group">
          <label for="comentario_resena">Comentario (máx. 500 caracteres)</label>
          <textarea
            id="comentario_resena"
            v-model="comentario"
            class="textarea"
            rows="4"
            maxlength="500"
            required
            placeholder="Comparte tu experiencia con el trueque"
          ></textarea>
          <p class="field-hint">{{ comentario.length }}/500</p>
        </div>

        <p v-if="error" class="alert alert--error">{{ error }}</p>

        <div class="modal-footer">
          <button class="button button--secondary" type="button" @click="cerrar">Más tarde</button>
          <button
            class="button button--primary"
            type="submit"
            :disabled="enviando || (estadoTrueque && estadoTrueque !== 'FINALIZADO')"
          >
            {{ enviando ? 'Enviando...' : 'Enviar reseña' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { inject, ref, watch } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  truequeId: { type: [Number, String], default: null },
  contraparteNombre: { type: String, default: '' },
  estadoTrueque: { type: String, default: '' },
})

const emit = defineEmits(['update:visible', 'enviada'])

import { useResenaStore } from '../stores/resena.js'

const resenaStore = useResenaStore()
const estrellas = ref(5)
const comentario = ref('')
const enviando = ref(false)
const error = ref('')

const limpiarFormulario = () => {
  estrellas.value = 5
  comentario.value = ''
  error.value = ''
  enviando.value = false
}

watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      limpiarFormulario()
    }
  },
)

const cerrar = () => {
  limpiarFormulario()
  emit('update:visible', false)
}

const enviar = async () => {
  if (!props.truequeId) {
    error.value = 'No se identificó el trueque.'
    return
  }

  if (props.estadoTrueque && props.estadoTrueque !== 'FINALIZADO') {
    error.value = 'Solo puedes dejar reseña de trueques finalizados.'
    return
  }

  enviando.value = true
  error.value = ''

  try {
    await resenaStore.registrarResena(props.truequeId, estrellas.value, comentario.value.trim())
    limpiarFormulario()
    emit('enviada')
    emit('update:visible', false)
  } catch (err) {
    error.value = err.message || 'No se pudo registrar la reseña.'
  } finally {
    enviando.value = false
  }
}
</script>
