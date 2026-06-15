<template>
  <section class="page">
    <!-- Directorio -->
    <template v-if="vista === 'directorio'">
      <div class="page-header">
        <div>
          <p class="eyebrow">Directorio</p>
          <h2 class="page-title">Comunidad</h2>
          <p class="page-description">
            Conoce a los miembros de TuTrueque, sus talentos principales y su reputacion en la comunidad.
          </p>
        </div>
      </div>

      <div v-if="!cargando && miembros.length" class="metric-row metric-row--comunidad">
        <article class="metric">
          <span class="metric__value">{{ miembros.length }}</span>
          <span class="metric__label">Miembros registrados</span>
        </article>
        <article class="metric">
          <span class="metric__value">{{ totalMiembrosActivos }}</span>
          <span class="metric__label">Miembros activos</span>
        </article>
      </div>

      <section class="panel">
        <div class="panel__header">
          <h3 class="panel__title">Miembros de la comunidad</h3>
        </div>
        <div class="panel__body">
          <div v-if="cargando" class="loading-state">Cargando comunidad...</div>
          <p v-else-if="error" class="alert alert--error">{{ error }}</p>
          <div v-else-if="miembros.length" class="member-grid">
            <article
              v-for="miembro in miembros"
              :key="miembro.id"
              class="member-card"
              role="button"
              tabindex="0"
              @click="verDetalle(miembro)"
              @keyup.enter="verDetalle(miembro)"
            >
              <div class="member-card__header">
                <div class="member-avatar" :style="{ backgroundColor: getAvatarColor(miembro.username) }">
                  {{ getInitials(miembro.nombre_real, miembro.username) }}
                </div>
                <div class="member-card__info">
                  <h3 class="member-card__name">{{ miembro.nombre_real }}</h3>
                  <p class="member-card__stars">{{ formatearEstrellas(miembro.promedio_estrellas) }} / 5.0</p>
                </div>
              </div>

              <div v-if="miembro.es_miembro_activo" class="member-card__badges">
                <span class="badge badge--activa">Miembro Activo</span>
              </div>

              <div class="member-card__talentos">
                <p class="member-card__label">Talentos principales</p>
                <ul v-if="miembro.talentos_principales?.length" class="member-card__lista">
                  <li v-for="titulo in miembro.talentos_principales" :key="titulo">{{ titulo }}</li>
                </ul>
                <p v-else class="member-card__vacio">Sin talentos activos publicados</p>
              </div>

              <p class="member-card__cta">Ver perfil →</p>
            </article>
          </div>
          <div v-else class="empty-state">
            No hay miembros en la comunidad por el momento.
          </div>
        </div>
      </section>
    </template>

    <!-- Detalle de miembro -->
    <template v-else>
      <div class="page-header">
        <div>
          <p class="eyebrow">Perfil publico</p>
          <h2 class="page-title">{{ detallePerfil?.nombre_real || 'Miembro' }}</h2>
          <p class="page-description">Informacion publica del miembro. Solo lectura.</p>
        </div>
        <div class="page-header__actions">
          <button
            v-if="puedeEnviarPropuesta"
            class="button button--primary"
            type="button"
            @click="abrirSelectorModo"
          >
            Realizar trueque
          </button>
          <button class="button button--secondary" type="button" @click="volverAlDirectorio">
            Volver
          </button>
        </div>
      </div>

      <section class="panel">
        <div class="panel__body">
          <div v-if="cargandoDetalle" class="loading-state">Cargando perfil...</div>
          <p v-else-if="errorDetalle" class="alert alert--error">{{ errorDetalle }}</p>
          <div v-else-if="detallePerfil" class="perfil-publico">
            <div class="perfil-publico__header">
              <div
                class="member-avatar member-avatar--large"
                :style="{ backgroundColor: getAvatarColor(detallePerfil.usuario?.username) }"
              >
                {{ getInitials(detallePerfil.nombre_real, detallePerfil.usuario?.username) }}
              </div>
              <div>
                <h3 class="perfil-publico__nombre">{{ detallePerfil.nombre_real }}</h3>
                <p class="perfil-publico__estrellas">
                  {{ formatearEstrellas(detallePerfil.promedio_estrellas) }} / 5.0
                </p>
              </div>
            </div>

            <div class="perfil-publico__seccion">
              <h4>Talentos activos ({{ talentosActivos.length }})</h4>
              <div v-if="talentosActivos.length" class="publicaciones-publicas">
                <article
                  v-for="pub in talentosActivos"
                  :key="pub.id"
                  class="publicacion-publica"
                >
                  <h5>{{ pub.titulo }}</h5>
                  <p>{{ pub.descripcion }}</p>
                  <span class="categoria">{{ pub.categoria }}</span>
                </article>
              </div>
              <div v-else class="empty-state">Este miembro no tiene talentos activos publicados.</div>
            </div>

            <div class="perfil-publico__seccion">
              <h4>Necesidades activas ({{ necesidadesActivas.length }})</h4>
              <div v-if="necesidadesActivas.length" class="publicaciones-publicas">
                <article
                  v-for="pub in necesidadesActivas"
                  :key="pub.id"
                  class="publicacion-publica publicacion-publica--necesidad"
                >
                  <h5>{{ pub.titulo }}</h5>
                  <p>{{ pub.descripcion }}</p>
                  <span class="categoria">{{ pub.categoria }}</span>
                </article>
              </div>
              <div v-else class="empty-state">Este miembro no tiene necesidades activas publicadas.</div>
            </div>

            <div class="perfil-publico__seccion">
              <h4>Resenas ({{ cantidadResenasPublicas }})</h4>
              <div v-if="detallePerfil.resenas?.length" class="resenas-publicas">
                <article v-for="resena in detallePerfil.resenas" :key="resena.id" class="resena-publica">
                  <p class="resena-publica__estrellas">{{ '★'.repeat(resena.estrellas) }}</p>
                  <p class="resena-publica__autor">por @{{ nombreCalificador(resena) }}</p>
                  <p class="resena-publica__comentario">{{ resena.comentario }}</p>
                </article>
              </div>
              <div v-else class="empty-state">Este miembro aun no tiene resenas.</div>
            </div>
          </div>
        </div>
      </section>
    </template>

    <!-- Selector de modo para propuesta desde Comunidad -->
    <div
      v-if="mostrarSelectorModo"
      class="modal-overlay"
      @click.self="cerrarSelectorModo"
    >
      <div class="modal-content modal-content--modo-propuesta">
        <div class="modal-header">
          <h3 class="modal-title">¿Cómo quieres truequear?</h3>
          <button class="modal-close" type="button" aria-label="Cerrar" @click="cerrarSelectorModo">×</button>
        </div>
        <div class="modal-body">
          <p class="modo-propuesta-intro">
            Elige cómo quieres intercambiar con <strong>{{ detallePerfil?.nombre_real }}</strong>.
            Cada opción define qué publicaciones puedes seleccionar.
          </p>
          <div class="modo-propuesta-opciones">
            <button
              class="modo-propuesta-btn"
              type="button"
              @click="elegirModoPropuesta('pedir_ayuda')"
            >
              <span class="modo-propuesta-btn__titulo">Quiero que me ayude</span>
              <span class="modo-propuesta-btn__detalle">
                Elijo mi necesidad y su talento · Impacto: −1 h para mí
              </span>
            </button>
            <button
              class="modo-propuesta-btn"
              type="button"
              @click="elegirModoPropuesta('ofrecer_ayuda')"
            >
              <span class="modo-propuesta-btn__titulo">Quiero ayudarle</span>
              <span class="modo-propuesta-btn__detalle">
                Elijo mi talento y su necesidad · Impacto: +1 h para mí
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
/*
 * Checklist validación manual Fase 2 — Comunidad (dos modos de propuesta):
 * TEST M1 — Quiero que me ayude
 *   [ ] Solo mis NECESIDADES en el primer select
 *   [ ] Solo TALENTOS del vecino en el segundo
 *   [ ] No se puede elegir NECESIDAD del vecino
 *   [ ] Impacto muestra −1 h para mí
 *   [ ] Propuesta llega al vecino con mensaje coherente
 *   [ ] Aceptar → confirmar ×2 → saldo: yo −1, vecino +1
 * TEST M2 — Quiero ayudarle
 *   [ ] Solo mis TALENTOS / NECESIDADES del vecino
 *   [ ] Impacto +1 h · Tras finalizar: yo +1, vecino −1
 * TEST M3 — Sin publicaciones del tipo requerido → mensaje claro, submit deshabilitado
 * TEST M4 — Match automático sin cambios (TALENTO+TALENTO, 0 h, dos parejas)
 * TEST M5 — Perfil / Cartelera sin regresiones
 */
import { computed, inject, onMounted, ref, watch } from 'vue';

const authController = inject('authController');
const carteleraController = inject('carteleraController');
const comunidadController = inject('comunidadController');
const hu4 = inject('hu4', null);

const AVATAR_COLORS = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b', '#fa709a', '#fee140'];

const vista = ref('directorio');
const miembros = ref([]);
const detallePerfil = ref(null);
const cargando = ref(true);
const cargandoDetalle = ref(false);
const error = ref('');
const errorDetalle = ref('');
const mostrarSelectorModo = ref(false);
const sesionLocalId = ref(null)
const usuarioActualId = computed(() => hu4?.usuarioActualId?.value ?? sesionLocalId.value)

const totalMiembrosActivos = computed(() => miembros.value.filter((m) => m.es_miembro_activo).length);

const puedeEnviarPropuesta = computed(() => {
  const perfilId = detallePerfil.value?.usuario?.id
  return Boolean(perfilId && usuarioActualId.value && perfilId !== usuarioActualId.value)
});

const sincronizarSesion = async () => {
  if (hu4?.usuarioActualId?.value) {
    sesionLocalId.value = hu4.usuarioActualId.value
    return
  }
  const sesion = await authController.obtenerSesionActual()
  sesionLocalId.value = sesion?.id ?? null
};

const talentosActivos = computed(() => {
  if (!detallePerfil.value?.publicaciones) return [];
  return detallePerfil.value.publicaciones.filter((pub) => pub.tipo === 'TALENTO');
});

const necesidadesActivas = computed(() => {
  if (!detallePerfil.value?.publicaciones) return [];
  return detallePerfil.value.publicaciones.filter((pub) => pub.tipo === 'NECESIDAD');
});

const cantidadResenasPublicas = computed(() => {
  if (!detallePerfil.value) return 0;
  if (typeof detallePerfil.value.cantidad_resenas === 'number') {
    return detallePerfil.value.cantidad_resenas;
  }
  return detallePerfil.value.resenas?.length ?? 0;
});

const nombreCalificador = (resena) => {
  if (resena.calificador_username) return resena.calificador_username;
  if (resena.calificador?.username) return resena.calificador.username;
  if (resena.calificador_nombre) return resena.calificador_nombre;
  return 'usuario';
};

const getInitials = (nombreReal, username) => {
  const nombre = nombreReal || username || 'U';
  return nombre.charAt(0).toUpperCase();
};

const getAvatarColor = (username) => {
  const index = (username || 'u').charCodeAt(0) % AVATAR_COLORS.length;
  return AVATAR_COLORS[index];
};

const formatearEstrellas = (valor) => Number(valor || 5).toFixed(1);

const cargarComunidad = async () => {
  cargando.value = true;
  error.value = '';

  try {
    const data = await comunidadController.obtenerComunidad();
    miembros.value = data.miembros || [];
  } catch (err) {
    error.value = err.message || 'No se pudo cargar el directorio de la comunidad.';
    miembros.value = [];
  } finally {
    cargando.value = false;
  }
};

const verDetalle = async (miembro) => {
  vista.value = 'detalle';
  cargandoDetalle.value = true;
  errorDetalle.value = '';
  detallePerfil.value = null;

  try {
    detallePerfil.value = await comunidadController.obtenerPerfilUsuario(miembro.id);
  } catch (err) {
    errorDetalle.value = err.message || 'No se pudo cargar el perfil del miembro.';
  } finally {
    cargandoDetalle.value = false;
  }
};

const volverAlDirectorio = () => {
  vista.value = 'directorio';
  detallePerfil.value = null;
  errorDetalle.value = '';
  mostrarSelectorModo.value = false;
};

const abrirSelectorModo = () => {
  if (!detallePerfil.value) return;
  mostrarSelectorModo.value = true;
};

const cerrarSelectorModo = () => {
  mostrarSelectorModo.value = false;
};

const elegirModoPropuesta = async (modo) => {
  if (!hu4?.abrirModalPropuesta || !detallePerfil.value) return;

  mostrarSelectorModo.value = false;

  const misPublicaciones = await carteleraController.obtenerMisPublicaciones();
  const config = {
    receptorId: detallePerfil.value.usuario.id,
    receptorNombre: detallePerfil.value.nombre_real,
    misPublicaciones,
    publicacionesVecino: detallePerfil.value.publicaciones || [],
    modoPropuesta: modo,
    tipoMiPublicacion: modo === 'pedir_ayuda' ? 'NECESIDAD' : 'TALENTO',
    tipoVecinoPublicacion: modo === 'pedir_ayuda' ? 'TALENTO' : 'NECESIDAD',
  };

  await hu4.abrirModalPropuesta(config);
};

watch(vista, sincronizarSesion)

onMounted(async () => {
  await sincronizarSesion()
  await cargarComunidad()
});
</script>
