<template>
  <section class="page">
    <div class="page-header">
      <div>
        <p class="eyebrow">Cartelera comunitaria</p>
        <h2 class="page-title">Servicios y necesidades disponibles</h2>
        <p class="page-description">
          Explora talentos, necesidades y prioridades de la comunidad. Las publicaciones criticas y de alta urgencia se destacan para facilitar la atencion rapida.
        </p>
      </div>
    </div>

    <div class="metric-row">
      <article class="metric">
        <span class="metric__value">{{ publicaciones.length }}</span>
        <span class="metric__label">Publicaciones visibles</span>
      </article>
      <article class="metric">
        <span class="metric__value">{{ totalCriticas }}</span>
        <span class="metric__label">Necesidades criticas</span>
      </article>
      <article class="metric">
        <span class="metric__value">{{ totalTalentos }}</span>
        <span class="metric__label">Talentos ofertados</span>
      </article>
    </div>

    <section class="panel">
      <div class="panel__header">
        <h3 class="panel__title">Filtros de busqueda</h3>
      </div>
      <div class="panel__body">
        <div class="filter-grid">
          <div class="form-group">
            <label for="categoria">Categoria</label>
            <select id="categoria" v-model="filtroCategoria" class="select">
              <option value="">Todas las categorias</option>
              <option value="Salud">Salud</option>
              <option value="Educacion">Educacion</option>
              <option value="Educación">Educacion</option>
              <option value="Mantenimiento">Mantenimiento</option>
              <option value="Hogar">Hogar</option>
              <option value="Tecnologia">Tecnologia</option>
              <option value="Tecnología">Tecnologia</option>
            </select>
          </div>

          <div class="form-group">
            <label for="urgencia">Urgencia</label>
            <select id="urgencia" v-model="filtroUrgencia" class="select">
              <option value="">Cualquier urgencia</option>
              <option value="NORMAL">Normal</option>
              <option value="ALTA">Urgencia alta</option>
              <option value="CRITICA">Necesidad critica</option>
            </select>
          </div>
        </div>

        <div class="form-actions">
          <button class="button button--primary" type="button" @click="aplicarFiltros">
            Aplicar filtros
          </button>
          <button class="button button--secondary" type="button" @click="restablecerFiltros">
            Restablecer
          </button>
        </div>

        <p v-if="errorFiltro" class="alert alert--error">{{ errorFiltro }}</p>
      </div>
    </section>

    <section class="panel">
      <div class="panel__header">
        <h3 class="panel__title">Lista de publicaciones</h3>
        <button class="button button--secondary" type="button" @click="obtenerPublicaciones(false)">
          Actualizar
        </button>
      </div>

      <div class="panel__body">
        <div v-if="cargando" class="loading-state">Cargando publicaciones...</div>

        <div v-else-if="publicaciones.length" class="service-grid">
          <article
            v-for="pub in publicaciones"
            :key="pub.id"
            :class="['service-card', clasePorUrgencia(pub.urgencia)]"
          >
            <div class="service-card__top">
              <div>
                <span :class="['badge', pub.tipo === 'TALENTO' ? 'badge--talento' : 'badge--necesidad']">
                  {{ etiquetaTipo(pub.tipo) }}
                </span>
                <h3 class="service-card__title">{{ pub.titulo }}</h3>
              </div>
              <span :class="['badge', badgeUrgencia(pub.urgencia)]">{{ etiquetaUrgencia(pub.urgencia) }}</span>
            </div>

            <p class="service-card__description">{{ pub.descripcion }}</p>

            <div class="service-card__footer">
              <div>
                <strong>{{ pub.usuarioNombreReal || 'Usuario' }}</strong>
                <div>{{ estrellas(pub.usuarioEstrellas) }} / 5.0</div>
              </div>
              <span>{{ pub.categoria }}</span>
            </div>
          </article>
        </div>

        <div v-else class="empty-state">
          No hay servicios disponibles con los filtros seleccionados.
        </div>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue';

// CAMBIO VISTA: la vista consume el controlador POO en lugar de consultar Axios directamente.
const userController = inject('userController');
const publicaciones = ref([]);
const filtroCategoria = ref('');
const filtroUrgencia = ref('');
const cargando = ref(false);
const errorFiltro = ref('');

const totalCriticas = computed(() => publicaciones.value.filter((pub) => pub.urgencia === 'CRITICA').length);
const totalTalentos = computed(() => publicaciones.value.filter((pub) => pub.tipo === 'TALENTO').length);

const obtenerPublicaciones = async (conFiltros = false) => {
  cargando.value = true;
  errorFiltro.value = '';

  try {
    const params = {};
    if (conFiltros) {
      if (filtroCategoria.value) params.categoria = filtroCategoria.value;
      if (filtroUrgencia.value) params.urgencia = filtroUrgencia.value;
    }

    // CAMBIO VISTA: los filtros pasan por controlador -> servicio -> API Django -> BD.
    publicaciones.value = await userController.obtenerCartelera(params);
  } catch (err) {
    errorFiltro.value = 'No se pudo cargar la cartelera. Verifica que el backend este activo.';
  } finally {
    cargando.value = false;
  }
};

const aplicarFiltros = () => {
  if (!filtroCategoria.value && filtroUrgencia.value) {
    errorFiltro.value = 'Selecciona una categoria antes de filtrar por urgencia.';
    return;
  }

  obtenerPublicaciones(true);
};

const restablecerFiltros = () => {
  filtroCategoria.value = '';
  filtroUrgencia.value = '';
  errorFiltro.value = '';
  obtenerPublicaciones(false);
};

const clasePorUrgencia = (urgencia) => {
  if (urgencia === 'CRITICA') return 'service-card--critica';
  if (urgencia === 'ALTA') return 'service-card--alta';
  return '';
};

const badgeUrgencia = (urgencia) => {
  if (urgencia === 'CRITICA') return 'badge--critica';
  if (urgencia === 'ALTA') return 'badge--alta';
  return 'badge--normal';
};

const etiquetaTipo = (tipo) => (tipo === 'TALENTO' ? 'Talento' : 'Necesidad');
const etiquetaUrgencia = (urgencia) => {
  if (urgencia === 'CRITICA') return 'Critica';
  if (urgencia === 'ALTA') return 'Alta';
  return 'Normal';
};

const estrellas = (valor) => Number(valor || 5).toFixed(1);

onMounted(() => {
  obtenerPublicaciones(false);
});
</script>
