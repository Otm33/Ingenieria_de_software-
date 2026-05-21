<template>
  <div class="p-6 max-w-7xl mx-auto">
    <h2 class="text-3xl font-bold mb-6 text-gray-800">Cartelera de Intercambios</h2>

    <div class="flex flex-wrap gap-4 mb-8 bg-gray-50 p-4 rounded-xl shadow-inner">
      <select v-model="filtroCategoria" @change="obtenerPublicaciones" class="border p-2.5 rounded-lg bg-white">
        <option value="">Todas las Categorías</option>
        <option value="Salud">Salud</option>
        <option value="Educación">Educación</option>
        <option value="Mantenimiento">Mantenimiento</option>
      </select>

      <select v-model="filtroUrgencia" @change="obtenerPublicaciones" class="border p-2.5 rounded-lg bg-white">
        <option value="">Cualquier Prioridad</option>
        <option value="ALTA">Urgencia Alta</option>
        <option value="CRITICA">Necesidades Críticas</option>
      </select>
    </div>

    <div v-if="publicaciones.length" class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div 
        v-for="pub in publicaciones" 
        :key="pub.id" 
        :class="[
          'p-5 rounded-xl border-2 transition-all relative',
          pub.urgencia === 'CRITICA' || pub.urgencia === 'ALTA' 
            ? 'border-red-500 bg-red-50 animate-pulse' 
            : 'border-gray-200 bg-white shadow-sm'
        ]"
      >
        <span v-if="pub.urgencia === 'CRITICA'" class="absolute -top-3 right-4 bg-red-600 text-white text-xs font-bold px-2 py-0.5 rounded-full">🚨 CRÍTICO</span>
        <h3 class="text-xl font-bold text-gray-900 mb-2">{{ pub.titulo }}</h3>
        <p class="text-gray-600 text-sm mb-4">{{ pub.descripcion }}</p>
        
        <div class="border-t pt-3 flex justify-between items-center text-xs text-gray-500">
          <div>
            <p class="font-semibold text-gray-800">Ofrecido por: {{ pub.usuario_nombre_real }}</p>
            <p class="text-yellow-600 font-medium">⭐ {{ pub.usuario_estrellas.toFixed(1) }} / 5.0</p>
          </div>
          <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full font-bold">{{ pub.categoria }}</span>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-12">
      <p class="text-xl text-gray-500 font-medium">No hay servicios de esta categoría en este momento.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const publicaciones = ref([]);
const filtroCategoria = ref('');
const filtroUrgencia = ref('');

const obtenerPublicaciones = async () => {
  try {
    const response = await axios.get('/api/cartelera/', {
      params: {
        categoria: filtroCategoria.value,
        urgencia: filtroUrgencia.value
      }
    });
    publicaciones.value = response.data;
  } catch (err) {
    console.error("Error al refrescar la cartelera", err);
  }
};

onMounted(obtenerPublicaciones);
</script>
