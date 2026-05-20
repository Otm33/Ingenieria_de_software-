<script setup lang="ts">
import { ref } from 'vue';
import { ComunidadService } from '../services/ComunidadService';

const archivo = ref<File | null>(null);
const mensaje = ref('');

const manejarCambioArchivo = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    archivo.value = target.files[0];
  }
};

const subirCSV = async () => {
  if (!archivo.value) return;
  
  try {
    const resultado = await ComunidadService.importarMiembros(archivo.value);
    mensaje.value = '¡Miembros importados con éxito!';
    console.log(resultado);
  } catch (error: any) {
    // 💡 AQUÍ EL CAMBIO: En vez de la frase fija, usamos el error real
    mensaje.value = `Error: ${error.message}`;
    console.error(error);
  }
};



</script>

<template>
  <div class="admin-panel">
    <h2>Importar Miembros (Admin)</h2>
    <input type="file" accept=".csv" @change="manejarCambioArchivo" />
    <button @click="subirCSV" :disabled="!archivo">Cargar CSV</button>
    
    <p v-if="mensaje">{{ mensaje }}</p>
  </div>
</template>
