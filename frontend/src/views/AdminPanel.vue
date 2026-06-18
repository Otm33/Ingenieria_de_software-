<template>
  <section class="page">
    <div class="page-header">
      <div>
        <p class="eyebrow">Sprint 2 HU3</p>
        <h2 class="page-title">Panel de Administracion</h2>
        <p class="page-description">
          Gestion completa de la comunidad. Administra usuarios, publicaciones, trueques, resenas y saldos.
        </p>
      </div>
    </div>

    <!-- Dashboard metricas -->
    <div v-if="store.dashboard" class="metric-row admin-metric-row">
      <div class="metric">
        <span class="metric__value">{{ store.dashboard.usuarios?.total || 0 }}</span>
        <span class="metric__label">Usuarios ({{ store.dashboard.usuarios?.activos || 0 }} activos)</span>
      </div>
      <div class="metric">
        <span class="metric__value">{{ store.dashboard.publicaciones?.total || 0 }}</span>
        <span class="metric__label">Publicaciones ({{ store.dashboard.publicaciones?.activas || 0 }} activas)</span>
      </div>
      <div class="metric">
        <span class="metric__value">{{ store.dashboard.trueques?.total || 0 }}</span>
        <span class="metric__label">Trueques ({{ store.dashboard.trueques?.finalizados || 0 }} finalizados)</span>
      </div>
      <div class="metric">
        <span class="metric__value">{{ store.dashboard.resenas?.total || 0 }}</span>
        <span class="metric__label">Resenas</span>
      </div>
    </div>

    <!-- Pestanas -->
    <nav class="admin-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="admin-tab"
        :class="{ 'admin-tab--active': seccionActiva === tab.key }"
        type="button"
        @click="cambiarSeccion(tab.key)"
      >
        {{ tab.label }}
      </button>
    </nav>

    <!-- Barra de busqueda -->
    <div class="admin-search">
      <input
        id="admin_busqueda"
        v-model="terminoBusqueda"
        class="input"
        type="text"
        placeholder="Buscar..."
        @input="buscarConDebounce"
      />
    </div>

    <!-- Error global -->
    <p v-if="store.error" class="alert alert--error">{{ store.error }}</p>

    <!-- Loading -->
    <div v-if="store.loading" class="loading-state">Cargando datos...</div>

    <!-- Tabla Usuarios -->
    <section v-if="seccionActiva === 'usuarios' && !store.loading" class="panel">
      <div class="panel__header">
        <h3 class="panel__title">Usuarios ({{ store.usuarios.length }})</h3>
      </div>
      <div class="panel__body">
        <div v-if="!store.usuarios.length" class="empty-state">No hay usuarios.</div>
        <div v-else class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Nombre</th>
                <th>Horas</th>
                <th>Tipo</th>
                <th>Estado</th>
                <th>Rol</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in store.usuarios" :key="u.id">
                <td>{{ u.id }}</td>
                <td>{{ u.username }}</td>
                <td>{{ u.email }}</td>
                <td>{{ u.nombre_real }}</td>
                <td>{{ u.horas_de_vida }}</td>
                <td>
                  <span class="badge" :class="u.es_comercio ? 'badge--necesidad' : 'badge--talento'">
                    {{ u.es_comercio ? 'Comercio' : 'Usuario' }}
                  </span>
                </td>
                <td>
                  <span class="badge" :class="u.is_active ? 'badge--activa' : 'badge--pausada'">
                    {{ u.is_active ? 'Activo' : 'Inactivo' }}
                  </span>
                </td>
                <td>
                  <span v-if="u.is_superuser" class="badge badge--critica">Super</span>
                  <span v-else-if="u.is_staff" class="badge badge--alta">Staff</span>
                  <span v-else class="badge badge--normal">Usuario</span>
                </td>
                <td class="admin-actions">
                  <button
                    class="button button--secondary button--sm"
                    type="button"
                    @click="toggleUsuario(u.id)"
                  >
                    {{ u.is_active ? 'Desactivar' : 'Activar' }}
                  </button>
                  <button
                    v-if="!u.is_superuser"
                    class="button button--secondary button--sm"
                    type="button"
                    @click="cambiarRol(u.id, !u.is_staff)"
                  >
                    {{ u.is_staff ? 'Quitar Staff' : 'Hacer Staff' }}
                  </button>
                  <button
                    v-if="!u.is_superuser"
                    class="button button--danger button--sm"
                    type="button"
                    @click="confirmarEliminar('usuario', u.id, u.username)"
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Tabla Publicaciones -->
    <section v-if="seccionActiva === 'publicaciones' && !store.loading" class="panel">
      <div class="panel__header">
        <h3 class="panel__title">Publicaciones ({{ store.publicaciones.length }})</h3>
        <button class="button button--accent button--sm" type="button" @click="mostrarFormPublicacion = !mostrarFormPublicacion">
          {{ mostrarFormPublicacion ? 'Cancelar' : 'Crear publicacion' }}
        </button>
      </div>
      <div v-if="mostrarFormPublicacion" class="panel__body">
        <div class="form-grid">
          <div class="form-group">
            <label for="pub_titulo">Titulo</label>
            <input id="pub_titulo" v-model="formPublicacion.titulo" class="input" type="text" />
          </div>
          <div class="form-group">
            <label for="pub_categoria">Categoria</label>
            <input id="pub_categoria" v-model="formPublicacion.categoria" class="input" type="text" />
          </div>
          <div class="form-group">
            <label for="pub_tipo">Tipo</label>
            <select id="pub_tipo" v-model="formPublicacion.tipo" class="select">
              <option value="TALENTO">Talento</option>
              <option value="NECESIDAD">Necesidad</option>
            </select>
          </div>
          <div class="form-group">
            <label for="pub_urgencia">Urgencia</label>
            <select id="pub_urgencia" v-model="formPublicacion.urgencia" class="select">
              <option value="NORMAL">Normal</option>
              <option value="ALTA">Alta</option>
              <option value="CRITICA">Critica</option>
            </select>
          </div>
        </div>
        <div class="form-group form-group--full">
          <label for="pub_descripcion">Descripcion</label>
          <textarea id="pub_descripcion" v-model="formPublicacion.descripcion" class="textarea" rows="3"></textarea>
        </div>
        <div class="form-actions">
          <button class="button button--primary" type="button" @click="crearPublicacion">Crear</button>
        </div>
      </div>
      <div class="panel__body">
        <div v-if="!store.publicaciones.length" class="empty-state">No hay publicaciones.</div>
        <div v-else class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Titulo</th>
                <th>Tipo</th>
                <th>Categoria</th>
                <th>Usuario</th>
                <th>Urgencia</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in store.publicaciones" :key="p.id">
                <td>{{ p.id }}</td>
                <td>{{ p.titulo }}</td>
                <td>
                  <span class="badge" :class="p.tipo === 'TALENTO' ? 'badge--talento' : 'badge--necesidad'">
                    {{ p.tipo }}
                  </span>
                </td>
                <td>{{ p.categoria }}</td>
                <td>{{ p.usuario_username }}</td>
                <td>
                  <span class="badge" :class="'badge--' + p.urgencia.toLowerCase()">{{ p.urgencia }}</span>
                </td>
                <td>
                  <span class="badge" :class="p.esta_activa ? 'badge--activa' : 'badge--pausada'">
                    {{ p.esta_activa ? 'Activa' : 'Pausada' }}
                  </span>
                </td>
                <td class="admin-actions">
                  <button
                    class="button button--secondary button--sm"
                    type="button"
                    @click="moderarPublicacion(p.id, !p.esta_activa)"
                  >
                    {{ p.esta_activa ? 'Pausar' : 'Activar' }}
                  </button>
                  <button
                    class="button button--danger button--sm"
                    type="button"
                    @click="confirmarEliminar('publicacion', p.id, p.titulo)"
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Tabla Trueques -->
    <section v-if="seccionActiva === 'trueques' && !store.loading" class="panel">
      <div class="panel__header">
        <h3 class="panel__title">Trueques ({{ store.trueques.length }})</h3>
      </div>
      <div class="panel__body">
        <div v-if="!store.trueques.length" class="empty-state">No hay trueques.</div>
        <div v-else class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Emisor ID</th>
                <th>Receptor ID</th>
                <th>Estado</th>
                <th>Confirmaciones</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in store.trueques" :key="t.id">
                <td>{{ t.id }}</td>
                <td>{{ t.emisor_id }}</td>
                <td>{{ t.receptor_id }}</td>
                <td>
                  <span class="badge" :class="badgeEstado(t.estado)">{{ t.estado }}</span>
                </td>
                <td>
                  E: {{ t.emisor_confirmado ? 'Si' : 'No' }} |
                  R: {{ t.receptor_confirmado ? 'Si' : 'No' }}
                </td>
                <td class="admin-actions">
                  <select
                    class="select select--sm"
                    :value="t.estado"
                    @change="actualizarEstadoTrueque(t.id, $event.target.value)"
                  >
                    <option v-for="e in estadosTrueque" :key="e" :value="e">{{ e }}</option>
                  </select>
                  <button
                    class="button button--danger button--sm"
                    type="button"
                    @click="confirmarEliminar('trueque', t.id, `Trueque #${t.id}`)"
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Tabla Trueques Multiples -->
    <section v-if="seccionActiva === 'trueques-multiples' && !store.loading" class="panel">
      <div class="panel__header">
        <h3 class="panel__title">Trueques Multiples ({{ store.truequesMultiples.length }})</h3>
      </div>
      <div class="panel__body">
        <div v-if="!store.truequesMultiples.length" class="empty-state">No hay trueques multiples.</div>
        <div v-else class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Participantes</th>
                <th>Estado</th>
                <th>Aceptaciones</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in store.truequesMultiples" :key="t.id">
                <td>{{ t.id }}</td>
                <td>
                  Par1: {{ t.emisor1_id }}-{{ t.receptor1_id }} |
                  Par2: {{ t.emisor2_id }}-{{ t.receptor2_id }} |
                  Par3: {{ t.emisor3_id }}-{{ t.receptor3_id }}
                </td>
                <td>
                  <span class="badge" :class="badgeEstado(t.estado)">{{ t.estado }}</span>
                </td>
                <td>
                  U1: {{ t.usuario1_aceptado ? 'Si' : 'No' }} |
                  U2: {{ t.usuario2_aceptado ? 'Si' : 'No' }} |
                  U3: {{ t.usuario3_aceptado ? 'Si' : 'No' }}
                </td>
                <td class="admin-actions">
                  <select
                    class="select select--sm"
                    :value="t.estado"
                    @change="actualizarEstadoTruequeMultiple(t.id, $event.target.value)"
                  >
                    <option v-for="e in estadosTruequeMultiple" :key="e" :value="e">{{ e }}</option>
                  </select>
                  <button
                    class="button button--danger button--sm"
                    type="button"
                    @click="confirmarEliminar('trueque-multiple', t.id, `Trueque Multiple #${t.id}`)"
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Tabla Resenas -->
    <section v-if="seccionActiva === 'resenas' && !store.loading" class="panel">
      <div class="panel__header">
        <h3 class="panel__title">Resenas ({{ store.resenas.length }})</h3>
      </div>
      <div class="panel__body">
        <div v-if="!store.resenas.length" class="empty-state">No hay resenas.</div>
        <div v-else class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Trueque</th>
                <th>Calificador</th>
                <th>Calificado</th>
                <th>Estrellas</th>
                <th>Comentario</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in store.resenas" :key="r.id">
                <td>{{ r.id }}</td>
                <td>#{{ r.trueque_id }}</td>
                <td>{{ r.calificador_id }}</td>
                <td>{{ r.calificado_id }}</td>
                <td>{{ '★'.repeat(r.estrellas) }}{{ '☆'.repeat(5 - r.estrellas) }}</td>
                <td class="admin-text-truncate">{{ r.comentario }}</td>
                <td class="admin-actions">
                  <button
                    class="button button--danger button--sm"
                    type="button"
                    @click="confirmarEliminar('resena', r.id, `Resena #${r.id}`)"
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Tabla Resenas Multiples -->
    <section v-if="seccionActiva === 'resenas-multiples' && !store.loading" class="panel">
      <div class="panel__header">
        <h3 class="panel__title">Resenas Multiples ({{ store.resenasMultiples.length }})</h3>
      </div>
      <div class="panel__body">
        <div v-if="!store.resenasMultiples.length" class="empty-state">No hay resenas multiples.</div>
        <div v-else class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Trueque Multiple</th>
                <th>Calificador</th>
                <th>Calificado</th>
                <th>Estrellas</th>
                <th>Comentario</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in store.resenasMultiples" :key="r.id">
                <td>{{ r.id }}</td>
                <td>#{{ r.trueque_multiple_id }}</td>
                <td>{{ r.calificador_id }}</td>
                <td>{{ r.calificado_id }}</td>
                <td>{{ '★'.repeat(r.estrellas) }}{{ '☆'.repeat(5 - r.estrellas) }}</td>
                <td class="admin-text-truncate">{{ r.comentario }}</td>
                <td class="admin-actions">
                  <button
                    class="button button--danger button--sm"
                    type="button"
                    @click="confirmarEliminar('resena-multiple', r.id, `Resena Multiple #${r.id}`)"
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Tabla Saldos -->
    <section v-if="seccionActiva === 'saldos' && !store.loading" class="panel">
      <div class="panel__header">
        <h3 class="panel__title">Saldos Comerciales ({{ store.saldos.length }})</h3>
      </div>
      <div class="panel__body">
        <div v-if="!store.saldos.length" class="empty-state">No hay movimientos de saldo.</div>
        <div v-else class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Comercio</th>
                <th>Cliente</th>
                <th>Monto</th>
                <th>Tipo</th>
                <th>Fecha</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in store.saldos" :key="s.id">
                <td>{{ s.id }}</td>
                <td>{{ s.comercio_username }}</td>
                <td>{{ s.cliente_username }}</td>
                <td>{{ s.monto_excedente }}</td>
                <td>
                  <span class="badge" :class="s.tipo_movimiento === 'EMISION' ? 'badge--talento' : 'badge--necesidad'">
                    {{ s.tipo_movimiento }}
                  </span>
                </td>
                <td>{{ formatearFecha(s.fecha) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Modal de confirmacion para eliminar -->
    <div v-if="modalEliminar.visible" class="modal-overlay" @click.self="modalEliminar.visible = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3 class="modal-title">Confirmar eliminacion</h3>
          <button class="button button--secondary" type="button" @click="modalEliminar.visible = false">X</button>
        </div>
        <div class="modal-body">
          <p>Estas seguro de eliminar <strong>{{ modalEliminar.nombre }}</strong>?</p>
          <p class="admin-warning">Esta accion no se puede deshacer.</p>
          <div class="form-actions">
            <button class="button button--danger" type="button" @click="ejecutarEliminar">Eliminar</button>
            <button class="button button--secondary" type="button" @click="modalEliminar.visible = false">Cancelar</button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useAdminPanelStore } from '../stores/adminPanel.js'

const store = useAdminPanelStore()

const seccionActiva = ref('usuarios')
const terminoBusqueda = ref('')
const mostrarFormPublicacion = ref(false)

const formPublicacion = reactive({
  titulo: '',
  descripcion: '',
  categoria: '',
  tipo: 'TALENTO',
  urgencia: 'NORMAL',
})

const modalEliminar = reactive({
  visible: false,
  tipo: '',
  id: null,
  nombre: '',
})

const tabs = [
  { key: 'usuarios', label: 'Usuarios' },
  { key: 'publicaciones', label: 'Publicaciones' },
  { key: 'trueques', label: 'Trueques' },
  { key: 'trueques-multiples', label: 'Trueques Multiples' },
  { key: 'resenas', label: 'Resenas' },
  { key: 'resenas-multiples', label: 'Resenas Multiples' },
  { key: 'saldos', label: 'Saldos' },
]

const estadosTrueque = ['PENDIENTE', 'ACEPTADO', 'RECHAZADO', 'EN_CURSO', 'FINALIZADO']
const estadosTruequeMultiple = ['PENDIENTE', 'ACEPTADO', 'RECHAZADO', 'EN_CURSO', 'FINALIZADO', 'EXPIRADO']

let debounceTimer = null

const cargarSeccion = async (seccion, busqueda = '') => {
  const acciones = {
    'usuarios': () => store.cargarUsuarios(busqueda),
    'publicaciones': () => store.cargarPublicaciones(busqueda),
    'trueques': () => store.cargarTrueques(busqueda),
    'trueques-multiples': () => store.cargarTruequesMultiples(busqueda),
    'resenas': () => store.cargarResenas(busqueda),
    'resenas-multiples': () => store.cargarResenasMultiples(busqueda),
    'saldos': () => store.cargarSaldos(busqueda),
  }
  if (acciones[seccion]) {
    try { await acciones[seccion]() } catch { /* error ya esta en store */ }
  }
}

const cambiarSeccion = (seccion) => {
  seccionActiva.value = seccion
  terminoBusqueda.value = ''
  cargarSeccion(seccion)
}

const buscarConDebounce = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    cargarSeccion(seccionActiva.value, terminoBusqueda.value)
  }, 300)
}

// Acciones CRUD
const toggleUsuario = async (id) => {
  try { await store.toggleUsuario(id) } catch { /* error en store */ }
}

const cambiarRol = async (id, isStaff) => {
  try { await store.cambiarRol(id, isStaff) } catch { /* error en store */ }
}

const moderarPublicacion = async (id, estaActiva) => {
  try { await store.moderarPublicacion(id, estaActiva) } catch { /* error en store */ }
}

const crearPublicacion = async () => {
  try {
    await store.crearPublicacion({ ...formPublicacion })
    formPublicacion.titulo = ''
    formPublicacion.descripcion = ''
    formPublicacion.categoria = ''
    formPublicacion.tipo = 'TALENTO'
    formPublicacion.urgencia = 'NORMAL'
    mostrarFormPublicacion.value = false
  } catch { /* error en store */ }
}

const actualizarEstadoTrueque = async (id, estado) => {
  try { await store.actualizarEstadoTrueque(id, estado) } catch { /* error en store */ }
}

const actualizarEstadoTruequeMultiple = async (id, estado) => {
  try { await store.actualizarEstadoTruequeMultiple(id, estado) } catch { /* error en store */ }
}

const confirmarEliminar = (tipo, id, nombre) => {
  modalEliminar.visible = true
  modalEliminar.tipo = tipo
  modalEliminar.id = id
  modalEliminar.nombre = nombre
}

const ejecutarEliminar = async () => {
  const { tipo, id } = modalEliminar
  try {
    if (tipo === 'usuario') await store.eliminarUsuario(id)
    else if (tipo === 'publicacion') await store.eliminarPublicacion(id)
    else if (tipo === 'trueque') await store.eliminarTrueque(id)
    else if (tipo === 'trueque-multiple') await store.eliminarTruequeMultiple(id)
    else if (tipo === 'resena') await store.eliminarResena(id)
    else if (tipo === 'resena-multiple') await store.eliminarResenaMultiple(id)
  } catch { /* error en store */ }
  modalEliminar.visible = false
}

const badgeEstado = (estado) => {
  const map = {
    'PENDIENTE': 'badge--necesidad',
    'ACEPTADO': 'badge--talento',
    'RECHAZADO': 'badge--critica',
    'EN_CURSO': 'badge--alta',
    'FINALIZADO': 'badge--activa',
    'EXPIRADO': 'badge--pausada',
  }
  return map[estado] || 'badge--normal'
}

const formatearFecha = (fecha) => {
  if (!fecha) return '-'
  try {
    return new Date(fecha).toLocaleDateString('es-VE', {
      year: 'numeric', month: 'short', day: 'numeric',
    })
  } catch {
    return fecha
  }
}

onMounted(async () => {
  try { await store.cargarDashboard() } catch { /* error en store */ }
  cargarSeccion('usuarios')
})
</script>

<style scoped>
.admin-metric-row {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 20px;
}

.admin-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}

.admin-tab {
  padding: 9px 16px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--surface);
  color: var(--text-muted);
  font-weight: 700;
  font-size: 0.92rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.admin-tab:hover {
  color: var(--primary-dark);
  border-color: var(--primary);
  background: #e8f2f8;
}

.admin-tab--active {
  color: #fff;
  background: var(--primary);
  border-color: var(--primary);
}

.admin-search {
  margin-bottom: 16px;
}

.admin-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.button--sm {
  min-height: 32px;
  padding: 5px 10px;
  font-size: 0.82rem;
}

.button--danger {
  color: #fff;
  background: var(--danger);
}

.button--danger:hover {
  background: #b93636;
}

.select--sm {
  padding: 5px 8px;
  font-size: 0.82rem;
  min-width: 110px;
}

.admin-text-truncate {
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.admin-warning {
  color: var(--danger);
  font-weight: 650;
  margin-top: 8px;
}

@media (max-width: 860px) {
  .admin-metric-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
