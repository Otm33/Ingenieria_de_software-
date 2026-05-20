<script setup lang="ts">
import ImportarMiembros from './components/ImportarMiembros.vue'
</script>

<template>
  <div class="contenedor-principal">
    <header>
      <h1>Plataforma TuTrueque</h1>
    </header>

    <main>
      <ImportarMiembros />
    </main>
  </div>
</template>

<style>
/* Estilos básicos para que se vea ordenado */
body {
  font-family: Arial, sans-serif;
  background-color: #f4f6f9;
  margin: 0;
  padding: 0;
}
.contenedor-principal {
  max-width: 800px;
  margin: 40px auto;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
header h1 {
  color: #2c3e50;
  text-align: center;
  border-bottom: 2px solid #ecf0f1;
  padding-bottom: 20px;
}
</style>
