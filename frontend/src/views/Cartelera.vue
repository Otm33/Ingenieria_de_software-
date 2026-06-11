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

        </div>

        <div
          v-if="formPublicacion.tipo === 'NECESIDAD'"
          class="form-group form-group--full form-group--urgencia-publicacion"
        >
          <label for="urgencia_publicacion">Nivel de urgencia de la publicación</label>
          <select id="urgencia_publicacion" v-model="formPublicacion.urgencia" class="select" required>
            <option value="NORMAL">Normal</option>
            <option value="ALTA">Emergencia de urgencia alta</option>
            <option value="CRITICA">Necesidad crítica</option>
          </select>
          <p class="field-hint">
            La urgencia aplica a necesidades. Los talentos se publican con prioridad normal.
          </p>
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
            <span>Urgencia</span>
            <label class="checkbox-label">
              <input v-model="filtroEmergenciaAlta" type="checkbox" />
              Emergencias de urgencia alta
            </label>
            <label class="checkbox-label">
              <input v-model="filtroNecesidadCritica" type="checkbox" />
              Necesidades críticas
            </label>
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

        <template v-else-if="publicaciones.length">
          <div class="service-grid service-grid--selectable">
            <article
              v-for="pub in publicaciones"
              :key="pub.id"
              :class="[
                'service-card',
                clasePorUrgencia(pub.urgencia),
                { 'service-card--seleccionada': publicacionSeleccionadaId === pub.id },
              ]"
              role="button"
              tabindex="0"
              @click="seleccionarPublicacion(pub.id)"
              @keydown.enter.prevent="seleccionarPublicacion(pub.id)"
              @keydown.space.prevent="seleccionarPublicacion(pub.id)"
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
            </article>
          </div>

          <div v-if="publicacionSeleccionadaInfo" class="seleccion-info">
            <p>
              Has seleccionado: {{ publicacionSeleccionadaInfo.titulo }} — ofrecido por
              {{ publicacionSeleccionadaInfo.usuarioNombreReal || 'Usuario' }}
            </p>
            <button
              class="button button--primary button--small"
              type="button"
              :disabled="buscandoCoincidencias"
              @click="verCoincidencias"
            >
              {{ buscandoCoincidencias ? 'Buscando...' : 'Ver coincidencias' }}
            </button>
            <p v-if="feedbackCoincidencias" :class="['alert', coincidenciasExitosas ? 'alert--success' : 'alert--error']">
              {{ feedbackCoincidencias }}
            </p>
          </div>
        </template>

        <div v-else class="empty-state">
          {{ mensajeVacio }}
        </div>
      </div>
    </section>

    <ModalConfirmacion
      :visible="mostrarModalConfirmacion"
      @update:visible="mostrarModalConfirmacion = $event"
      :titulo="datosModalConfirmacion.titulo"
      :mensaje="datosModalConfirmacion.mensaje"
      :submensaje="datosModalConfirmacion.submensaje"
      :textoConfirmar="datosModalConfirmacion.textoConfirmar"
      :textoCancelar="datosModalConfirmacion.textoCancelar"
      :claseBotonConfirmar="datosModalConfirmacion.claseBotonConfirmar"
      @confirmar="confirmarCambioEstado"
      @cancelar="mostrarModalConfirmacion = false"
    />
  </section>
</template>

<script setup>
import { computed, inject, onMounted, reactive, ref, toRefs, watch } from 'vue';
import { CATEGORIAS, titulosParaCategoria } from '../data/catalogoServicios.js';
import ModalConfirmacion from '../components/ModalConfirmacion.vue';

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
const hu4 = inject('hu4', null);
const publicaciones = ref([]);
const misPublicaciones = ref([]);
const usuarioActualId = ref(null);
const filtroCategoria = ref('');
const filtroEmergenciaAlta = ref(false);
const filtroNecesidadCritica = ref(false);
const filtrosActivos = ref(false);
const publicacionSeleccionadaId = ref(null);
const cargando = ref(false);
const cargandoMisPublicaciones = ref(false);
const errorFiltro = ref('');
const publicando = ref(false);
const feedbackPublicacion = ref('');
const publicacionExitosa = ref(false);
const feedbackEstadoPublicacion = ref('');
const feedbackEstadoExitoso = ref(false);
const procesandoEstadoId = ref(null);
const mostrarModalConfirmacion = ref(false);
const datosModalConfirmacion = ref({
  titulo: '',
  mensaje: '',
  submensaje: '',
  textoConfirmar: 'Confirmar',
  textoCancelar: 'Cancelar',
  claseBotonConfirmar: 'button--primary',
  publicacion: null,
  reactivar: false
});
const buscandoCoincidencias = ref(false);
const feedbackCoincidencias = ref('');
const coincidenciasExitosas = ref(false);
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
const mensajeVacio = computed(() =>
  filtrosActivos.value
    ? 'No hay servicios de esta categoría en este momento'
    : 'No hay servicios disponibles en la cartelera.'
);
const publicacionSeleccionadaInfo = computed(() => {
  if (!publicacionSeleccionadaId.value) return null;
  return publicaciones.value.find((pub) => pub.id === publicacionSeleccionadaId.value) || null;
});

watch(() => formPublicacion.categoria, () => {
  formPublicacion.titulo = '';
});

watch(() => formPublicacion.tipo, (nuevoTipo) => {
  if (nuevoTipo === 'TALENTO') {
    formPublicacion.urgencia = 'NORMAL';
  }
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
  if (!conFiltros) {
    errorFiltro.value = '';
  }

  try {
    let params = {};
    if (conFiltros) {
      params = { categoria: filtroCategoria.value };
      const urgencias = [];
      if (filtroEmergenciaAlta.value) urgencias.push('ALTA');
      if (filtroNecesidadCritica.value) urgencias.push('CRITICA');
      if (urgencias.length) params.urgencias = urgencias;
      filtrosActivos.value = true;
    } else {
      filtrosActivos.value = false;
      publicacionSeleccionadaId.value = null;
    }

    const todasPublicaciones = await userController.obtenerCartelera(params);
    publicaciones.value = todasPublicaciones.filter((pub) => pub.usuario !== usuarioActualId.value);
  } catch (err) {
    errorFiltro.value = 'No se pudo cargar la cartelera. Verifica que el backend esté activo.';
  } finally {
    cargando.value = false;
  }
};

const aplicarFiltros = () => {
  if (!filtroCategoria.value) {
    errorFiltro.value = 'Debe seleccionar una categoría para aplicar filtros.';
    return;
  }
  errorFiltro.value = '';
  publicacionSeleccionadaId.value = null;
  obtenerPublicaciones(true);
};

const restablecerFiltros = () => {
  filtroCategoria.value = '';
  filtroEmergenciaAlta.value = false;
  filtroNecesidadCritica.value = false;
  errorFiltro.value = '';
  filtrosActivos.value = false;
  publicacionSeleccionadaId.value = null;
  obtenerPublicaciones(false);
};

const seleccionarPublicacion = (publicacionId) => {
  publicacionSeleccionadaId.value = publicacionSeleccionadaId.value === publicacionId
    ? null
    : publicacionId;
  feedbackCoincidencias.value = '';
  coincidenciasExitosas.value = false;
};

const verCoincidencias = async () => {
  const pub = publicacionSeleccionadaInfo.value;
  if (!pub || !hu4?.abrirModalPropuesta) return;

  buscandoCoincidencias.value = true;
  feedbackCoincidencias.value = '';
  coincidenciasExitosas.value = false;

  try {
    const coincidencia = await userController.verificarCoincidenciaPorTitulo(pub.id);
    const { matches } = await userController.obtenerMatchesEnriquecidos(pub.id);

    if (!coincidencia.tiene_coincidencia && !matches.length) {
      feedbackCoincidencias.value = 'No se encontraron coincidencias por título para esta publicación.';
      return;
    }

    const tipoVecino = pub.tipo;
    const tipoMi = pub.tipo === 'TALENTO' ? 'NECESIDAD' : 'TALENTO';
    const misPublicaciones = await userController.obtenerMisPublicaciones();

    if (matches.length) {
      const match = matches[0];
      const sugerencia = match?.publicacionesSugeridas?.[0];
      const perfilVecino = await userController.obtenerPerfilUsuario(match.usuario.id);

      await hu4.abrirModalPropuesta({
        receptorId: match.usuario.id,
        receptorNombre: match.usuario.nombreReal,
        misPublicaciones,
        publicacionesVecino: perfilVecino.publicaciones || [],
        tipoMiPublicacion: tipoMi,
        tipoVecinoPublicacion: tipoVecino,
        publicacionEmisorId: sugerencia?.mi_pub_id || coincidencia.publicaciones_coincidentes?.[0]?.id || null,
        publicacionReceptorId: sugerencia?.su_pub_id || pub.id,
      });
    } else {
      const perfilVecino = await userController.obtenerPerfilUsuario(pub.usuario);

      await hu4.abrirModalPropuesta({
        receptorId: pub.usuario,
        receptorNombre: perfilVecino.nombre_real,
        misPublicaciones,
        publicacionesVecino: perfilVecino.publicaciones || [],
        tipoMiPublicacion: tipoMi,
        tipoVecinoPublicacion: tipoVecino,
        publicacionEmisorId: coincidencia.publicaciones_coincidentes?.[0]?.id || null,
        publicacionReceptorId: pub.id,
      });
    }

    coincidenciasExitosas.value = true;
    feedbackCoincidencias.value = 'Se encontró una coincidencia. Completa la propuesta de trueque.';
  } catch (err) {
    feedbackCoincidencias.value = err.message || 'No se pudieron buscar coincidencias.';
  } finally {
    buscandoCoincidencias.value = false;
  }
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

const actualizarEstadoPublicacion = (publicacion) => {
  const reactivar = !publicacion.esta_activa;
  datosModalConfirmacion.value = {
    titulo: reactivar ? 'Reactivar publicación' : 'Pausar publicación',
    mensaje: reactivar
    ? `¿Deseas reactivar esta publicación?`
    : `¿Deseas pausar esta publicación?`,
    submensaje: reactivar
      ? 'Volverá a ser visible para otros usuarios en la cartelera y podrás recibir propuestas de trueque.'
      : 'Tu publicación dejará de aparecer en la cartelera pública temporalmente. Podrás reactivarla cuando lo desees.',
    textoConfirmar: reactivar ? 'Reactivar' : 'Pausar',
    textoCancelar: 'Cancelar',
    claseBotonConfirmar: reactivar ? 'button--primary' : 'button--secondary',
    publicacion: publicacion,
    reactivar: reactivar
  };
  
  mostrarModalConfirmacion.value = true;
};

const confirmarCambioEstado = async () => {
  const { publicacion, reactivar } = datosModalConfirmacion.value;
  
  mostrarModalConfirmacion.value = false;

  if (!publicacion) {
    return;
  }

  procesandoEstadoId.value = publicacion.id;
  feedbackEstadoPublicacion.value = '';
  feedbackEstadoExitoso.value = false;

  try {
    await userController.actualizarEstadoPublicacion(publicacion.id, reactivar);
    feedbackEstadoExitoso.value = true;
    feedbackEstadoPublicacion.value = reactivar
      ? '✅ Publicación reactivada correctamente. Ahora es visible en la cartelera.'
      : '✅ Publicación pausada correctamente. Ya no aparece en la cartelera pública.';
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
