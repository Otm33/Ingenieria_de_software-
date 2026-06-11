<template>
  <div v-if="visible" class="modal-overlay" @click.self="cerrar">
    <div class="modal-content modal-content--confirmacion">
      <div class="modal-header">
        <h3 class="modal-title">{{ titulo }}</h3>
        <button class="modal-close" type="button" aria-label="Cerrar" @click="cerrar">×</button>
      </div>
      <div class="modal-body">
        <p class="confirmacion-mensaje">{{ mensaje }}</p>
        <p v-if="submensaje" class="field-hint">{{ submensaje }}</p>
      </div>
      <div class="modal-footer">
        <button class="button button--secondary" type="button" @click="cerrar">
          {{ textoCancelar || 'Cancelar' }}
        </button>
        <button 
          class="button" 
          :class="claseBotonConfirmar || 'button--primary'" 
          type="button" 
          @click="confirmar"
          :disabled="procesando"
        >
          {{ procesando ? textoProcesando || 'Procesando...' : textoConfirmar || 'Confirmar' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  titulo: { type: String, default: 'Confirmar acción' },
  mensaje: { type: String, default: '¿Estás seguro de realizar esta acción?' },
  submensaje: { type: String, default: '' },
  textoConfirmar: { type: String, default: 'Confirmar' },
  textoCancelar: { type: String, default: 'Cancelar' },
  textoProcesando: { type: String, default: 'Procesando...' },
  claseBotonConfirmar: { type: String, default: 'button--primary' },
})

const emit = defineEmits(['update:visible', 'confirmar', 'cancelar'])
const procesando = ref(false)

const cerrar = () => {
  emit('update:visible', false)
  emit('cancelar')
}

const confirmar = () => {
  emit('confirmar')
}

const setProcesando = (valor) => {
  procesando.value = valor
}

watch(() => props.visible, (nuevoValor) => {
  if (!nuevoValor) {
    procesando.value = false
  }
})

defineExpose({
  setProcesando
})
</script>
