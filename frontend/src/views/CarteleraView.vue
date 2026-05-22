<template>
  <div class="cartelera-container mx-auto p-4 max-w-4xl">
    <h1 class="text-2xl font-bold mb-6">Cartelera de TuTrueque</h1>

    <div class="filtros-panel bg-gray-100 p-4 rounded mb-6 flex gap-4 items-end">
      <div class="w-1/3">
        <label class="block text-sm font-medium text-gray-700">Categoría</label>
        <select v-model="filtros.categoria" class="w-full border p-2 rounded mt-1">
          <option value="">Todas las categorías</option>
          <option value="Hogar">Hogar</option>
          <option value="Educación">Educación</option>
          <option value="Tecnología">Tecnología</option>
          <option value="Salud">Salud</option>
        </select>
      </div>

      <div class="w-1/3">
        <label class="block text-sm font-medium text-gray-700">Filtrar por Emergencia</label>
        <select v-model="filtros.urgencia" class="w-full border p-2 rounded mt-1">
          <option value="">Cualquier urgencia</option>
          <option value="ALTA">Urgencia Alta</option>
          <option value="CRITICA">Necesidad Crítica</option>
          <option value="NORMAL">Normal</option>
        </select>
      </div>

      <div class="w-1/3 flex gap-2">
        <button @click="aplicarFiltros" class="w-full bg-blue-600 text-white p-2 rounded font-bold hover:bg-blue-700">
          Aplicar Filtros
        </button>
        <button @click="restablecerFiltros" class="w-full bg-gray-400 text-white p-2 rounded font-bold hover:bg-gray-500">
          Restablecer
        </button>
      </div>
    </div>

    <div v-if="cargando" class="text-center font-bold">Cargando cartelera...</div>
    
    <div v-else-if="publicaciones.length === 0" class="text-center p-6 bg-yellow-100 rounded text-yellow-800 font-medium">
      No hay servicios de esta categoría en este momento
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div 
        v-for="pub in publicaciones" 
        :key="pub.id"
        :class="['border p-4 rounded shadow relative', clasePorUrgencia(pub.urgencia)]"
      >
        <span v-if="pub.urgencia !== 'NORMAL'" class="absolute top-2 right-2 px-2 py-1 text-xs font-bold rounded bg-red-600 text-white">
          {{ pub.urgencia }}
        </span>

        <h2 class="font-bold text-lg mt-2">{{ pub.titulo }} <span class="text-sm font-normal text-gray-500">({{ pub.tipo }})</span></h2>
        <p class="text-sm text-gray-700 my-2">{{ pub.descripcion }}</p>
        <p class="text-xs text-gray-500">Categoría: <span class="font-bold">{{ pub.categoria }}</span></p>
        
        <div class="mt-4 pt-4 border-t flex justify-between items-center text-sm">
          <span>Usuario: <strong>{{ pub.usuario_nombre_real }}</strong></span>
          <span class="flex items-center text-yellow-500 font-bold">
             ⭐ {{ pub.usuario_estrellas.toFixed(1) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const publicaciones = ref([]);
const cargando = ref(false);
const filtros = ref({
  categoria: '',
  urgencia: ''
});

// Criterio 1 y 2: Cargar y aplicar filtros
const cargarCartelera = async () => {
  cargando.value = true;
  try {
    // Configurar params solo con los valores que no están vacíos
    const params = {};
    if (filtros.value.categoria) params.categoria = filtros.value.categoria;
    if (filtros.value.urgencia) params.urgencia = filtros.value.urgencia;

    // Asegúrate de usar la URL base correcta según tu configuración
    const response = await axios.get('http://localhost:8000/cartelera/', { params });
    publicaciones.value = response.data;
  } catch (error) {
    console.error("Error al cargar la cartelera:", error);
  } finally {
    cargando.value = false;
  }
};

const aplicarFiltros = () => {
  // Regla Restricción 1: No aplicar si está todo vacío (opcional, pero sugerido)
  cargarCartelera();
};

const restablecerFiltros = () => {
  filtros.value = { categoria: '', urgencia: '' };
  cargarCartelera(); // Criterio 2 (Restricción): Vuelve a su estado inicial
};

// Regla de Negocio 1: Las "Emergencias de urgencia alta" deben resaltarse visualmente
const clasePorUrgencia = (urgencia) => {
  if (urgencia === 'CRITICA') return 'border-red-500 bg-red-50';
  if (urgencia === 'ALTA') return 'border-orange-400 bg-orange-50';
  return 'bg-white';
};

// Carga inicial
onMounted(() => {
  cargarCartelera();
});
</script>
