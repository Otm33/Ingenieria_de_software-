<template>
  <section class="page">
    <div v-if="!modoPublicar" class="page-header">
      <div>
        <p class="eyebrow">Cartelera comunitaria</p>
        <h2 class="page-title">Servicios y necesidades disponibles</h2>
        <p class="page-description">
          Explora talentos, necesidades y prioridades de la comunidad. Las publicaciones criticas y de alta urgencia se destacan para facilitar la atencion rapida.
        </p>
      </div>
    </div>

    <div v-if="!modoPublicar" class="metric-row">
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

    <section v-if="modoPublicar" :class="['panel', 'panel--publicar']">
      <div class="panel__header">
        <h3 class="panel__title">📝 Publicar nuevo talento o necesidad</h3>
        <button class="button button--secondary" type="button" @click="volverACartelera">
          ← Volver a Cartelera
        </button>
      </div>
      <form class="panel__body" @submit.prevent="publicarServicio">
        <div class="form-grid">
          <div class="form-group">
            <label for="tipo_publicacion">Tipo</label>
            <select id="tipo_publicacion" v-model="formPublicacion.tipo" class="select" required>
              <option value="TALENTO">Talento</option>
              <option value="NECESIDAD">Necesidad</option>
            </select>
          </div>

          <div class="form-group">
            <label for="categoria_publicacion">Categoria</label>
            <select id="categoria_publicacion" v-model="formPublicacion.categoria" class="select" required>
              <option value="">Selecciona una categoria</option>
              <option v-for="categoria in CATEGORIAS" :key="categoria" :value="categoria">
                {{ categoria }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="titulo_publicacion">Titulo o nombre</label>
            <select id="titulo_publicacion" v-model="formPublicacion.titulo" class="select" required :disabled="!formPublicacion.categoria">
              <option value="">Selecciona un titulo</option>
              <option v-for="titulo in titulosDisponibles" :key="titulo" :value="titulo">
                {{ titulo }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="urgencia_publicacion">Urgencia</label>
            <select id="urgencia_publicacion" v-model="formPublicacion.urgencia" class="select">
              <option value="NORMAL">Normal</option>
              <option value="ALTA">Urgencia alta</option>
              <option value="CRITICA">Necesidad critica</option>
            </select>
          </div>
        </div>

        <div class="form-group form-group--full">
          <label for="descripcion_publicacion">Descripcion</label>
          <textarea
            id="descripcion_publicacion"
            v-model="formPublicacion.descripcion"
            class="textarea"
            rows="4"
            required
            placeholder="Describe que ofreces o que necesitas"
          ></textarea>
        </div>

        <div class="form-actions">
          <button class="button button--primary" type="submit" :disabled="publicando">
            {{ publicando ? 'Publicando...' : 'Publicar' }}
          </button>
          <button class="button button--secondary" type="button" @click="limpiarPublicacion">
            Limpiar
          </button>
        </div>

        <p v-if="feedbackPublicacion" :class="['alert', publicacionExitosa ? 'alert--success' : 'alert--error']">
          {{ feedbackPublicacion }}
        </p>
      </form>
    </section>

    <section v-if="modoPublicar" class="panel">
      <div class="panel__header">
        <h3 class="panel__title">Mis Publicaciones</h3>
      </div>
      <div class="panel__body">
        <div v-if="cargandoMisPublicaciones" class="loading-state">Cargando mis publicaciones...</div>
        <template v-else>
          <p
            v-if="feedbackEstadoPublicacion"
            :class="['alert', feedbackEstadoExitoso ? 'alert--success' : 'alert--error']"
          >
            {{ feedbackEstadoPublicacion }}
          </p>

          <div v-if="misPublicaciones.length" class="service-grid">
          <article
            v-for="pub in misPublicaciones"
            :key="pub.id"
            :class="['service-card', clasePorUrgencia(pub.urgencia), { 'service-card--pausada': !pub.esta_activa }]"
          >
            <div class="service-card__top">
              <div>
                <span :class="['badge', pub.tipo === 'TALENTO' ? 'badge--talento' : 'badge--necesidad']">
                  {{ etiquetaTipo(pub.tipo) }}
                </span>
                <span :class="['badge', pub.esta_activa ? 'badge--activa' : 'badge--pausada']">
                  {{ pub.esta_activa ? 'Activa' : 'Pausada' }}
                </span>
                <h3 class="service-card__title">{{ pub.titulo }}</h3>
              </div>
              <span :class="['badge', badgeUrgencia(pub.urgencia)]">{{ etiquetaUrgencia(pub.urgencia) }}</span>
            </div>
            <p class="service-card__description">{{ pub.descripcion }}</p>
            <div class="service-card__footer">
              <span>{{ pub.categoria }}</span>
              <button
                :class="['button', 'button--small', pub.esta_activa ? 'button--secondary' : 'button--primary']"
                type="button"
                :disabled="procesandoEstadoId === pub.id"
                @click="actualizarEstadoPublicacion(pub)"
              >
                {{
                  procesandoEstadoId === pub.id
                    ? 'Procesando...'
                    : (pub.esta_activa ? 'Pausar' : 'Reactivar')
                }}
              </button>
            </div>
          </article>
          </div>
          <div v-else class="empty-state">
            No tienes publicaciones.
          </div>
        </template>
      </div>
    </section>

    <section v-if="!modoPublicar" class="panel">
      <div class="panel__header">
        <h3 class="panel__title">Filtros de busqueda</h3>
      </div>
      <div class="panel__body">
        <div class="filter-grid">
          <div class="form-group">
            <label for="categoria">Categoria</label>
            <select id="categoria" v-model="filtroCategoria" class="select">
              <option value="">Todas las categorias</option>
              <option v-for="categoria in CATEGORIAS" :key="categoria" :value="categoria">
                {{ categoria }}
              </option>
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

    <section v-if="!modoPublicar" class="panel">
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
            <span class="service-card__category">{{ pub.categoria }}</span>

            <div class="service-card__top">
              <span :class="['badge', pub.tipo === 'TALENTO' ? 'badge--talento' : 'badge--necesidad']">
                {{ etiquetaTipo(pub.tipo) }}
              </span>
              <span :class="['badge', badgeUrgencia(pub.urgencia)]">{{ etiquetaUrgencia(pub.urgencia) }}</span>
            </div>

            <h3 class="service-card__title">{{ pub.titulo }}</h3>

            <p class="service-card__description">{{ pub.descripcion }}</p>

            <div class="service-card__separator"></div>

            <div class="service-card__footer">
              <strong>{{ pub.usuarioNombreReal || 'Usuario' }}</strong>
              <span>{{ estrellas(pub.usuarioEstrellas) }} / 5.0</span>
            </div>

            <div class="service-card__actions">
              <button 
                class="button button--small button--primary" 
                type="button" 
                @click="buscarMatchPorPublicacion(pub.id)"
                :disabled="buscandoMatch"
              >
                {{ buscandoMatch ? 'Buscando...' : '🔍 Buscar Match' }}
              </button>
            </div>
          </article>
        </div>

        <div v-else class="empty-state">
          No hay servicios disponibles con los filtros seleccionados.
        </div>
      </div>
    </section>

    <!-- Modal de resultados de match -->
    <div v-if="mostrarModalMatch" class="modal-overlay" @click="cerrarModalMatch">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">Verificación de Coincidencia</h3>
          <button class="button button--small button--secondary" @click="cerrarModalMatch">✕</button>
        </div>
        
        <div class="modal-body">
          <div v-if="resultadoMatch && resultadoMatch.encontrado" class="match-resultado">
            <p class="match-mensaje">{{ resultadoMatch.mensaje }}</p>
            
            <div v-if="verificacionCoincidencia && verificacionCoincidencia.publicaciones_coincidentes" class="match-lista">
              <div 
                v-for="pub in verificacionCoincidencia.publicaciones_coincidentes" 
                :key="pub.id" 
                class="match-item"
              >
                <div class="match-item-info">
                  <span :class="['badge', pub.tipo === 'TALENTO' ? 'badge--talento' : 'badge--necesidad']">
                    {{ pub.tipo === 'TALENTO' ? 'Talento' : 'Necesidad' }}
                  </span>
                  <strong>{{ pub.titulo }}</strong>
                  <span>{{ pub.categoria }}</span>
                </div>
                <button 
                  class="button button--small button--primary" 
                  @click="confirmarPropuesta"
                >
                  Proponer Trueque
                </button>
              </div>
            </div>
          </div>
          
          <div v-else class="match-vacio">
            <p>{{ resultadoMatch?.mensaje || 'No se encontraron resultados.' }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal de confirmación cuando no hay coincidencias -->
    <div v-if="mostrandoConfirmacion" class="modal-overlay" @click="cancelarConfirmacion">
      <div class="modal-content modal-content--confirmacion" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">¿Estás seguro?</h3>
          <button class="button button--small button--secondary" @click="cancelarConfirmacion">✕</button>
        </div>
        
        <div class="modal-body">
          <div class="confirmacion-mensaje">
            <p class="alert alert--warning">
              {{ resultadoMatch?.mensaje || 'No tienes publicaciones coincidentes.' }}
            </p>
            <p>¿Estás seguro de que quieres realizar este trueque sin tener una publicación complementaria?</p>
          </div>
          
          <div class="form-actions">
            <button class="button button--primary" @click="confirmarPropuesta">
              Confirmar
            </button>
            <button class="button button--secondary" @click="cancelarConfirmacion">
              Cancelar
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, inject, onMounted, reactive, ref, toRefs, watch } from 'vue';
import { CATEGORIAS, titulosParaCategoria } from '../data/catalogoServicios.js';

const props = defineProps({
  modoPublicar: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['volver-cartelera']);

// Desestructurar props para usar en el template
const { modoPublicar } = toRefs(props);

const userController = inject('userController');
const publicaciones = ref([]);
const misPublicaciones = ref([]);
const usuarioActualId = ref(null);
const filtroCategoria = ref('');
const filtroUrgencia = ref('');
const cargando = ref(false);
const cargandoMisPublicaciones = ref(false);
const errorFiltro = ref('');
const publicando = ref(false);
const feedbackPublicacion = ref('');
const publicacionExitosa = ref(false);
const feedbackEstadoPublicacion = ref('');
const feedbackEstadoExitoso = ref(false);
const procesandoEstadoId = ref(null);
const buscandoMatch = ref(false);
const resultadoMatch = ref(null);
const mostrarModalMatch = ref(false);
const verificacionCoincidencia = ref(null);
const publicacionSeleccionada = ref(null);
const mostrandoConfirmacion = ref(false);
const formPublicacion = reactive({
  tipo: 'TALENTO',
  titulo: '',
  descripcion: '',
  categoria: '',
  urgencia: 'NORMAL',
});

const totalCriticas = computed(() => publicaciones.value.filter((pub) => pub.urgencia === 'CRITICA').length);
const totalTalentos = computed(() => publicaciones.value.filter((pub) => pub.tipo === 'TALENTO').length);
const titulosDisponibles = computed(() => titulosParaCategoria(formPublicacion.categoria));

watch(() => formPublicacion.categoria, () => {
  formPublicacion.titulo = '';
});

const cargarMisPublicaciones = async () => {
  if (!modoPublicar.value) {
    return;
  }

  cargandoMisPublicaciones.value = true;
  try {
    const resultado = await userController.obtenerMisPublicaciones();
    misPublicaciones.value = Array.isArray(resultado) ? resultado : [];
  } catch {
    misPublicaciones.value = [];
  } finally {
    cargandoMisPublicaciones.value = false;
  }
};

watch(() => props.modoPublicar, (nuevoValor) => {
  if (nuevoValor) {
    cargarMisPublicaciones();
  }
}, { immediate: true });

const obtenerPublicaciones = async (conFiltros = false) => {
  cargando.value = true;
  errorFiltro.value = '';

  try {
    const params = {};
    if (conFiltros) {
      if (filtroCategoria.value) params.categoria = filtroCategoria.value;
      if (filtroUrgencia.value) params.urgencia = filtroUrgencia.value;
    }

    const todasPublicaciones = await userController.obtenerCartelera(params);
    // Filtrar para excluir las publicaciones del usuario actual
    publicaciones.value = todasPublicaciones.filter(pub => pub.usuario !== usuarioActualId.value);
  } catch (err) {
    errorFiltro.value = 'No se pudo cargar la cartelera. Verifica que el backend este activo.';
  } finally {
    cargando.value = false;
  }
};

const aplicarFiltros = () => {
  obtenerPublicaciones(true);
};

const restablecerFiltros = () => {
  filtroCategoria.value = '';
  filtroUrgencia.value = '';
  errorFiltro.value = '';
  obtenerPublicaciones(false);
};

const limpiarPublicacion = () => {
  formPublicacion.tipo = 'TALENTO';
  formPublicacion.titulo = '';
  formPublicacion.descripcion = '';
  formPublicacion.categoria = '';
  formPublicacion.urgencia = 'NORMAL';
};

const volverACartelera = () => {
  emit('volver-cartelera');
};

const actualizarEstadoPublicacion = async (publicacion) => {
  const reactivar = !publicacion.esta_activa;
  const mensajeConfirmacion = reactivar
    ? '¿Deseas reactivar esta publicación? Volverá a aparecer en la cartelera pública.'
    : '¿Deseas pausar esta publicación? Dejará de aparecer en la cartelera pública.';

  if (!confirm(mensajeConfirmacion)) {
    return;
  }

  procesandoEstadoId.value = publicacion.id;
  feedbackEstadoPublicacion.value = '';
  feedbackEstadoExitoso.value = false;

  try {
    await userController.actualizarEstadoPublicacion(publicacion.id, reactivar);
    feedbackEstadoExitoso.value = true;
    feedbackEstadoPublicacion.value = reactivar
      ? 'Publicación reactivada correctamente.'
      : 'Publicación pausada correctamente.';
    await cargarMisPublicaciones();
    await obtenerPublicaciones(false);
  } catch (err) {
    feedbackEstadoPublicacion.value = err.message || 'No se pudo actualizar el estado de la publicación.';
  } finally {
    procesandoEstadoId.value = null;
  }
};

const publicarServicio = async () => {
  publicando.value = true;
  feedbackPublicacion.value = '';
  publicacionExitosa.value = false;

  try {
    const nuevaPublicacion = await userController.crearPublicacion({ ...formPublicacion });
    publicacionExitosa.value = true;
    feedbackPublicacion.value = 'Publicación creada correctamente.';
    
    // Recargar mis publicaciones si estamos en modo publicación
    if (modoPublicar) {
      await cargarMisPublicaciones();
    }
    
    limpiarPublicacion();
    await obtenerPublicaciones(false);
  } catch (err) {
    feedbackPublicacion.value = err.message || 'No se pudo crear la publicación.';
  } finally {
    publicando.value = false;
  }
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

const buscarMatchPorPublicacion = async (publicacionId) => {
  buscandoMatch.value = true;
  verificacionCoincidencia.value = null;
  publicacionSeleccionada.value = publicacionId;
  
  try {
    const resultado = await userController.verificarCoincidenciaPorTitulo(publicacionId);
    verificacionCoincidencia.value = resultado;
    
    if (resultado.tiene_coincidencia) {
      // El usuario tiene publicaciones con el mismo título
      mostrarModalMatch.value = true;
      resultadoMatch.value = {
        encontrado: true,
        mensaje: `¡Tienes ${resultado.publicaciones_coincidentes.length} publicación(es) con el título "${resultado.titulo}" del tipo ${resultado.tipo_buscado}!`,
        verificacion: resultado
      };
    } else {
      // El usuario NO tiene publicaciones con el mismo título
      mostrandoConfirmacion.value = true;
      resultadoMatch.value = {
        encontrado: false,
        mensaje: `No tienes ninguna publicación con el título "${resultado.titulo}" del tipo ${resultado.tipo_buscado}.`,
        verificacion: resultado
      };
    }
  } catch (err) {
    resultadoMatch.value = {
      encontrado: false,
      mensaje: 'Error al verificar coincidencia: ' + (err.message || 'Error desconocido')
    };
    mostrarModalMatch.value = true;
  } finally {
    buscandoMatch.value = false;
  }
};

const cerrarModalMatch = () => {
  mostrarModalMatch.value = false;
  resultadoMatch.value = null;
  verificacionCoincidencia.value = null;
};

const cancelarConfirmacion = () => {
  mostrandoConfirmacion.value = false;
  resultadoMatch.value = null;
  verificacionCoincidencia.value = null;
  publicacionSeleccionada.value = null;
};

const confirmarPropuesta = async () => {
  try {
    alert('Propuesta enviada al usuario A. Ahora aparecerá en su cartelera como notificación prioritaria.');
    
    mostrandoConfirmacion.value = false;
    resultadoMatch.value = null;
    verificacionCoincidencia.value = null;
  } catch (err) {
    alert('Error al confirmar propuesta: ' + (err.message || 'Error desconocido'));
  }
};

const iniciarTrueque = async (usuarioId) => {
  try {
    alert('Funcionalidad de iniciar trueque será implementada próximamente. Usuario ID: ' + usuarioId);
    cerrarModalMatch();
  } catch (err) {
    alert('Error al iniciar trueque: ' + (err.message || 'Error desconocido'));
  }
};

onMounted(async () => {
  const sesion = await userController.obtenerSesionActual();
  if (sesion) {
    usuarioActualId.value = sesion.id;
  }

  await obtenerPublicaciones(false);
  if (modoPublicar.value) {
    await cargarMisPublicaciones();
  }
});
</script>
