<template>
  <div class="p-8 max-w-xl mx-auto bg-white rounded-xl shadow-md space-y-4 mt-10">
    <h2 class="text-2xl font-bold text-gray-800">Cargar Comunidad Autorizada (.CSV)</h2>
    <div class="border-2 border-dashed border-gray-300 p-6 rounded-lg text-center">
      <input type="file" @change="seleccionarArchivo" accept=".csv" class="mb-4 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
      <button @click="subirArchivo" class="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition">Procesar Lista</button>
    </div>
    <p v-if="mensaje" class="text-green-600 font-medium text-sm text-center">{{ mensaje }}</p>
    <p v-if="error" class="text-red-600 font-medium text-sm text-center">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const archivo = ref(null);
const mensaje = ref('');
const error = ref('');

const seleccionarArchivo = (event) => {
  const file = event.target.files[0];
  
  if (!file) {
    archivo.value = null;
    return;
  }

  // Convertimos a minúsculas para evitar problemas si el archivo termina en .CSV o .csv
  const nombreArchivo = file.name.toLowerCase();

  if (nombreArchivo.endsWith('.csv')) {
    error.value = '';
    archivo.value = file; // Aquí guardamos el archivo con éxito
    console.log("Archivo seleccionado correctamente:", file.name);
  } else {
    error.value = "Formato de archivo incorrecto. Solo se acepta .csv";
    archivo.value = null; // Si no es CSV, lo limpia por seguridad
    event.target.value = ''; // Resetea el input de la pantalla
  }
};

const subirArchivo = async () => {
  if (!archivo.value) {
    error.value = "Por favor, selecciona un archivo primero.";
    return;
  }
  
  const formData = new FormData();
  formData.append('archivo_csv', archivo.value);

  mensaje.value = '';
  error.value = '';

  try {
    const response = await axios.post('/api/cargar-csv/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    // Django suele responder con un JSON que tiene la clave 'mensaje' o 'message'
    mensaje.value = response.data.mensaje || response.data.message || "Archivo procesado con éxito.";
  } catch (err) {
    console.error("Error completo del servidor:", err);
    error.value = err.response?.data?.error || "Error al procesar el archivo masivo en el servidor.";
  }
};
</script>
