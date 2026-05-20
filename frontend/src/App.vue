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
.contenedor-principal {
  width: 100%;
  max-width: 600px;
  margin: 20px;
  padding: 30px;
  background-color: var(--bg-tarjeta);
  border: 1px solid var(--color-borde);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

header {
  text-align: center;
  margin-bottom: 30px;
  border-bottom: 1px solid var(--color-borde);
  padding-bottom: 20px;
}

header h1 {
  color: var(--color-primario);
  margin: 0 0 8px 0;
  font-size: 1.8rem;
}

.subtitulo {
  color: var(--texto-secundario);
  margin: 0;
  font-size: 0.95rem;
}
</style>

