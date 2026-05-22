<template>
  <div class="p-6 max-w-7xl mx-auto">
    <h2 class="text-3xl font-bold mb-6 text-gray-800">Cartelera de Intercambios</h2>

    <div class="flex flex-wrap items-center gap-4 mb-8 bg-gray-50 p-4 rounded-xl shadow-inner">
      <div class="flex flex-col">
        <label class="text-xs font-semibold text-gray-500 mb-1">Categoría *</label>
        <select v-model="filtroCategoria" class="border p-2.5 rounded-lg bg-white min-w-[180px]">
          <option value="">Todas las Categorías</option>
          <option value="Salud">Salud</option>
          <option value="Educación">Educación</option>
          <option value="Mantenimiento">Mantenimiento</option>
          <option value="Hogar">Hogar</option>
          <option value="Tecnología">Tecnología</option>
        </select>
      </div>

      <div class="flex flex-col">
        <label class="text-xs font-semibold text-gray-500 mb-1">Prioridad / Urgencia</label>
        <select v-model="filtroUrgencia" class="border p-2.5 rounded-lg bg-white min-w-[180px]">
          <option value="">Cualquier Prioridad</option>
          <option value="NORMAL">Normal</option>
          <option value="ALTA">Urgencia Alta</option>
          <option value="CRITICA">Necesidades Críticas</option>
        </select>
      </div>

      <div class="flex gap-2 self-end mt-1">
        <button 
          @click="aplicarFiltros" 
          class="bg-blue-600 hover:bg-blue-700 text-white font-bold px-5 py-2.5 rounded-lg text-sm transition-colors shadow-sm"
        >
          Aplicar Filtros
        </button>
        <button 
          @click="restablecerFiltros" 
          class="bg-gray-200 hover:bg-gray-300 text-gray-700 font-bold px-4 py-2.5 rounded-lg text-sm transition-colors"
        >
          Restablecer
        </button>
      </div>
      
      <p v-if="errorFiltro" class="text-red-600 text-xs font-medium w-full mt-1">
        ⚠️ {{ errorFiltro }}
      </p>
    </div>

    <div v-if="cargando" class="text-center py-12">
      <p class="text-xl text-gray-500 font-medium animate-pulse">Cargando cartelera...</p>
    </div>

    <div v-else-if="publicaciones.length" class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div 
        v-for="pub in publicaciones" 
        :key="pub.id" 
        :class="[
          'p-5 rounded-xl border-2 transition-all relative shadow-sm hover:shadow-md',
          clasePorUrgencia(pub.urgencia)
        ]"
      >
        <span v-if="pub.urgencia === 'CRITICA'" class="absolute -top-3 right-4 bg-red-600 text-white text-xs font-bold px-2 py-0.5 rounded-full shadow">🚨 CRÍTICO</span>
        <span v-else-if="pub.urgencia === 'ALTA'" class="absolute -top-3 right-4 bg-amber-500 text-white text-xs font-bold px-2 py-0.5 rounded-full shadow">⚠️ ALTA</span>

        <h3 class="text-xl font-bold text-gray-900 mb-2">{{ pub.titulo }} <span class="text-xs font-normal text-gray-400">({{ pub.tipo }})</span></h3>
        <p class="text-gray-600 text-sm mb-4">{{ pub.descripcion }}</p>
        
        <div class="border-t pt-3 flex justify-between items-center text-xs text-gray-500">
          <div>
            <p class="font-semibold text-gray-800">Ofrecido por: {{ pub.usuario_nombre_real }}</p>
            <p class="text-yellow-600 font-medium">⭐ {{ pub.usuario_estrellas ? pub.usuario_estrellas.toFixed(1) : '5.0' }} / 5.0</p>
          </div>
          <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full font-bold">{{ pub.categoria }}</span>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-12 bg-yellow-50 border border-yellow-200 rounded-xl">
      <p class="text-xl text-yellow-700 font-medium">No hay servicios de esta categoría en este momento.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const publicaciones = ref([]);
const filtroCategoria = ref('');
const filtroUrgencia = ref('');
const cargando = ref(false);
const errorFiltro = ref('');

// Función encargada de realizar la petición HTTP apuntando al puerto 8000 de Django
const obtenerPublicaciones = async (conFiltros = false) => {
  cargando.value = true;
  errorFiltro.value = '';
  try {
    const params = {};
    if (conFiltros) {
      if (filtroCategoria.value) params.categoria = filtroCategoria.value;
      if (filtroUrgencia.value) params.urgencia = filtroUrgencia.value;
    }

    const response = await axios.get('http://localhost:8000/api/cartelera/', { params });
    publicaciones.value = response.data;
  } catch (err) {
    console.error("Error al refrescar la cartelera", err);
  } finally {
    cargando.value = false;
  }
};

// Restricción 1 del ERS
const aplicarFiltros = () => {
  if (!filtroCategoria.value && filtroUrgencia.value) {
    errorFiltro.value = 'Debe seleccionar una Categoría para poder filtrar por nivel de urgencia.';
    return;
  }
  obtenerPublicaciones(true);
};

// Restricción 2 del ERS
const restablecerFiltros = () => {
  filtroCategoria.value = '';
  filtroUrgencia.value = '';
  errorFiltro.value = '';
  obtenerPublicaciones(false);
};

const clasePorUrgencia = (urgencia) => {
  if (urgencia === 'CRITICA') return 'border-red-500 bg-red-50 animate-pulse';
  if (urgencia === 'ALTA') return 'border-amber-400 bg-amber-50';
  return 'border-gray-200 bg-white';
};

onMounted(() => {
  obtenerPublicaciones(false);
});
</script>
