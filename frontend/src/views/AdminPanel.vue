<template>
  <section class="page">
    <div class="page-header">
      <div>
        <p class="eyebrow">Administracion</p>
        <h2 class="page-title">Panel de Administracion</h2>
        <p class="page-description">
          Gestion completa de la comunidad. Administra usuarios, publicaciones, trueques, resenas, saldos e impacto social.
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
    <div v-if="seccionActiva !== 'impacto-social'" class="admin-search">
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

    <!-- ═══════ Tabla Usuarios ═══════ -->
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
                <th>Estrellas</th>
                <th>Tipo</th>
                <th>Estado</th>
                <th>Rol</th>
                <th>Fecha registro</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in store.usuarios" :key="u.id">
                <td>{{ u.id }}</td>
                <td>{{ u.username }}</td>
                <td>{{ u.email }}</td>
                <td>{{ u.nombre_real }}</td>
                <td>{{ Number(u.horas_de_vida || 0).toFixed(1) }}</td>
                <td>{{ u.promedio_estrellas ? Number(u.promedio_estrellas).toFixed(1) + '★' : '—' }}</td>
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
                <td>{{ formatearFecha(u.date_joined) }}</td>
                <td class="admin-actions">
                  <button
                    class="button button--accent button--sm"
                    type="button"
                    @click="abrirEditarUsuario(u)"
                  >
                    Editar
                  </button>
                  <button
                    class="button button--secondary button--sm"
                    type="button"
                    @click="toggleUsuario(u.id)"
                  >
                    {{ u.is_active ? 'Suspender' : 'Activar' }}
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

    <!-- ═══════ Tabla Publicaciones ═══════ -->
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
                <th>Descripcion</th>
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
                  <span class="badge" :class="'badge--' + (p.urgencia || 'normal').toLowerCase()">{{ p.urgencia }}</span>
                </td>
                <td>
                  <span class="badge" :class="p.esta_activa ? 'badge--activa' : 'badge--pausada'">
                    {{ p.esta_activa ? 'Activa' : 'Pausada' }}
                  </span>
                </td>
                <td class="admin-text-truncate">{{ p.descripcion }}</td>
                <td class="admin-actions">
                  <button
                    class="button button--accent button--sm"
                    type="button"
                    @click="abrirEditarPublicacion(p)"
                  >
                    Editar
                  </button>
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

    <!-- ═══════ Tabla Trueques ═══════ -->
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
                <th>Emisor</th>
                <th>Receptor</th>
                <th>Pub. Emisor</th>
                <th>Pub. Receptor</th>
                <th>Estado</th>
                <th>Codigo</th>
                <th>Confirmaciones</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in store.trueques" :key="t.id">
                <td>{{ t.id }}</td>
                <td>{{ t.emisor_nombre || t.emisor_id }}</td>
                <td>{{ t.receptor_nombre || t.receptor_id }}</td>
                <td>{{ t.publicacion_emisor_titulo || t.publicacion_emisor_id || '—' }}</td>
                <td>{{ t.publicacion_receptor_titulo || t.publicacion_receptor_id || '—' }}</td>
                <td>
                  <span class="badge" :class="badgeEstado(t.estado)">{{ t.estado }}</span>
                </td>
                <td>{{ t.codigo_confirmacion || '—' }}</td>
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

    <!-- ═══════ Tabla Trueques Multiples ═══════ -->
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

    <!-- ═══════ Tabla Resenas ═══════ -->
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
                <td>{{ r.calificador_nombre || r.calificador_id }}</td>
                <td>{{ r.calificado_nombre || r.calificado_id }}</td>
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

    <!-- ═══════ Tabla Resenas Multiples ═══════ -->
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

    <!-- ═══════ Tabla Saldos ═══════ -->
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

    <!-- ═══════ Impacto Social (integrado) ═══════ -->
    <section v-if="seccionActiva === 'impacto-social'" class="panel">
      <div v-if="impactoCargando" class="loading-state">Cargando datos de impacto social...</div>
      <template v-else>
        <p v-if="impactoMensaje" class="alert alert--success">{{ impactoMensaje }}</p>
        <p v-if="impactoError" class="alert alert--error">{{ impactoError }}</p>

        <div class="metric-row admin-metric-row" style="margin-bottom: 16px;">
          <div class="metric">
            <span class="metric__value">{{ saldoFondo.toFixed(1) }}</span>
            <span class="metric__label">Saldo Fondo Comunitario</span>
          </div>
          <div class="metric">
            <span class="metric__value">{{ solicitudesPendientes.length }}</span>
            <span class="metric__label">Solicitudes pendientes</span>
          </div>
          <div class="metric">
            <span class="metric__value">{{ impactoUsuarios.length }}</span>
            <span class="metric__label">Usuarios gestionables</span>
          </div>
        </div>

        <!-- Solicitudes pendientes -->
        <div class="panel" style="margin-bottom: 16px;">
          <div class="panel__header">
            <h3 class="panel__title">Solicitudes pendientes de aprobacion</h3>
          </div>
          <div class="panel__body">
            <div v-if="solicitudesPendientes.length" class="table-container">
              <table class="data-table">
                <thead><tr><th>Solicitante</th><th>Categoria</th><th>Necesidad</th><th>Descripcion</th><th>Acciones</th></tr></thead>
                <tbody>
                  <tr v-for="s in solicitudesPendientes" :key="s.id">
                    <td>{{ s.solicitante_nombre || '—' }}</td>
                    <td>{{ s.categoria || '—' }}</td>
                    <td><strong>{{ s.titulo }}</strong></td>
                    <td>{{ s.descripcion }}</td>
                    <td class="admin-actions">
                      <button class="button button--primary button--sm" type="button"
                        :disabled="procesandoImpactoId === s.id" @click="aprobarSolicitud(s.id)">Aprobar</button>
                      <button class="button button--secondary button--sm" type="button"
                        :disabled="procesandoImpactoId === s.id" @click="rechazarSolicitud(s.id)">Rechazar</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty-state">No hay solicitudes pendientes.</div>
          </div>
        </div>

        <!-- Usuarios y estado social -->
        <div class="panel" style="margin-bottom: 16px;">
          <div class="panel__header">
            <h3 class="panel__title">Usuarios y estado social</h3>
          </div>
          <div class="panel__body">
            <div v-if="impactoUsuarios.length" class="table-container">
              <table class="data-table">
                <thead><tr><th>Usuario</th><th>Horas de vida</th><th>Horas donacion</th><th>Estado social</th></tr></thead>
                <tbody>
                  <tr v-for="u in impactoUsuarios" :key="u.id">
                    <td><strong>{{ u.nombre_real }}</strong> <span style="color:var(--text-muted);">@{{ u.username }}</span></td>
                    <td>{{ Number(u.horas_de_vida || 0).toFixed(1) }}</td>
                    <td>{{ Number(u.horas_recibidas_donacion || 0).toFixed(1) }}</td>
                    <td>
                      <select class="select select--sm" :value="u.estado_social"
                        :disabled="procesandoImpactoId === u.id"
                        @change="actualizarEstadoSocial(u, $event.target.value)">
                        <option value="NINGUNO">Ninguno</option>
                        <option value="VULNERABLE">Vulnerable</option>
                        <option value="CRITICO">Critico</option>
                      </select>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty-state">No hay usuarios.</div>
          </div>
        </div>

        <!-- Asignar desde fondo -->
        <div class="panel">
          <div class="panel__header"><h3 class="panel__title">Asignar horas desde el Fondo Comunitario</h3></div>
          <div class="panel__body">
            <p class="panel__hint" style="margin-bottom: 8px;">Solo usuarios marcados como Vulnerable o Critico pueden recibir asignaciones.</p>
            <form class="form-grid" @submit.prevent="asignarDesdeFondo">
              <div class="form-group">
                <label for="imp_usuario">Usuario receptor</label>
                <select id="imp_usuario" v-model.number="formImpacto.usuarioId" class="select" required>
                  <option disabled :value="null">Selecciona usuario</option>
                  <option v-for="u in usuariosAsignables" :key="u.id" :value="u.id">
                    {{ u.nombre_real }} — {{ u.estado_social === 'CRITICO' ? 'Critico' : 'Vulnerable' }}
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label for="imp_solicitud">Solicitud aprobada</label>
                <select id="imp_solicitud" v-model.number="formImpacto.solicitudId" class="select" required :disabled="!formImpacto.usuarioId">
                  <option disabled :value="null">Selecciona causa</option>
                  <option v-for="s in solicitudesReceptor" :key="s.id" :value="s.id">
                    {{ s.titulo }} ({{ Number(s.horas_recibidas || 0).toFixed(1) }} h)
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label for="imp_monto">Monto (horas)</label>
                <input id="imp_monto" v-model="formImpacto.monto" class="input" type="number" min="0.5" step="0.1" required />
                <span style="font-size: 0.82rem; color: var(--text-muted);">Fondo: {{ saldoFondo.toFixed(1) }} h</span>
              </div>
              <div class="form-group" style="display: flex; align-items: flex-end;">
                <button class="button button--primary" type="submit" :disabled="procesandoAsignacion">
                  {{ procesandoAsignacion ? 'Asignando...' : 'Asignar' }}
                </button>
              </div>
            </form>
            <p v-if="errorAsignacion" class="alert alert--error" style="margin-top: 8px;">{{ errorAsignacion }}</p>
            <p v-if="mensajeAsignacion" class="alert alert--success" style="margin-top: 8px;">{{ mensajeAsignacion }}</p>
          </div>
        </div>
      </template>
    </section>

    <!-- ═══════ Modal Editar Usuario ═══════ -->
    <div v-if="modalEditarUsuario.visible" class="modal-overlay" @click.self="modalEditarUsuario.visible = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3 class="modal-title">Editar usuario: {{ modalEditarUsuario.username }}</h3>
          <button class="button button--secondary" type="button" @click="modalEditarUsuario.visible = false">X</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-group">
              <label>Nombre real</label>
              <input v-model="modalEditarUsuario.nombre_real" class="input" type="text" />
            </div>
            <div class="form-group">
              <label>Email</label>
              <input v-model="modalEditarUsuario.email" class="input" type="email" />
            </div>
            <div class="form-group">
              <label>Horas de vida</label>
              <input v-model="modalEditarUsuario.horas_de_vida" class="input" type="number" step="0.1" />
            </div>
            <div class="form-group">
              <label>Tipo</label>
              <select v-model="modalEditarUsuario.es_comercio" class="select">
                <option :value="false">Usuario</option>
                <option :value="true">Comercio</option>
              </select>
            </div>
          </div>
          <div class="form-actions">
            <button class="button button--primary" type="button" @click="guardarUsuario">Guardar</button>
            <button class="button button--secondary" type="button" @click="modalEditarUsuario.visible = false">Cancelar</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════ Modal Editar Publicacion ═══════ -->
    <div v-if="modalEditarPub.visible" class="modal-overlay" @click.self="modalEditarPub.visible = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3 class="modal-title">Editar publicacion #{{ modalEditarPub.id }}</h3>
          <button class="button button--secondary" type="button" @click="modalEditarPub.visible = false">X</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-group">
              <label>Titulo</label>
              <input v-model="modalEditarPub.titulo" class="input" type="text" />
            </div>
            <div class="form-group">
              <label>Categoria</label>
              <input v-model="modalEditarPub.categoria" class="input" type="text" />
            </div>
            <div class="form-group">
              <label>Tipo</label>
              <select v-model="modalEditarPub.tipo" class="select">
                <option value="TALENTO">Talento</option>
                <option value="NECESIDAD">Necesidad</option>
              </select>
            </div>
            <div class="form-group">
              <label>Urgencia</label>
              <select v-model="modalEditarPub.urgencia" class="select">
                <option value="NORMAL">Normal</option>
                <option value="ALTA">Alta</option>
                <option value="CRITICA">Critica</option>
              </select>
            </div>
          </div>
          <div class="form-group form-group--full">
            <label>Descripcion</label>
            <textarea v-model="modalEditarPub.descripcion" class="textarea" rows="3"></textarea>
          </div>
          <div class="form-actions">
            <button class="button button--primary" type="button" @click="guardarPublicacion">Guardar</button>
            <button class="button button--secondary" type="button" @click="modalEditarPub.visible = false">Cancelar</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════ Modal Confirmar Eliminar ═══════ -->
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
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useAdminPanelStore } from '../stores/adminPanel.js'
import { useImpactoSocialStore } from '../stores/impactoSocial.js'

const store = useAdminPanelStore()
const impactoStore = useImpactoSocialStore()

const seccionActiva = ref('usuarios')
const terminoBusqueda = ref('')
const mostrarFormPublicacion = ref(false)

const formPublicacion = reactive({
  titulo: '', descripcion: '', categoria: '', tipo: 'TALENTO', urgencia: 'NORMAL',
})

const modalEliminar = reactive({ visible: false, tipo: '', id: null, nombre: '' })
const modalEditarUsuario = reactive({
  visible: false, id: null, username: '', nombre_real: '', email: '', horas_de_vida: 0, es_comercio: false,
})
const modalEditarPub = reactive({
  visible: false, id: null, titulo: '', descripcion: '', categoria: '', tipo: 'TALENTO', urgencia: 'NORMAL',
})

// Impacto social state
const impactoCargando = ref(false)
const impactoMensaje = ref('')
const impactoError = ref('')
const saldoFondo = ref(0)
const solicitudesPendientes = ref([])
const solicitudesAprobadas = ref([])
const impactoUsuarios = ref([])
const procesandoImpactoId = ref(null)
const procesandoAsignacion = ref(false)
const errorAsignacion = ref('')
const mensajeAsignacion = ref('')
const formImpacto = reactive({ usuarioId: null, solicitudId: null, monto: '' })

const usuariosAsignables = computed(() =>
  impactoUsuarios.value.filter((u) => ['VULNERABLE', 'CRITICO'].includes(u.estado_social))
)
const solicitudesReceptor = computed(() => {
  if (!formImpacto.usuarioId) return []
  return solicitudesAprobadas.value.filter((s) => s.solicitante === formImpacto.usuarioId)
})

watch(() => formImpacto.usuarioId, () => { formImpacto.solicitudId = null })

const tabs = [
  { key: 'usuarios', label: 'Usuarios' },
  { key: 'publicaciones', label: 'Publicaciones' },
  { key: 'trueques', label: 'Trueques' },
  { key: 'trueques-multiples', label: 'T. Multiples' },
  { key: 'resenas', label: 'Resenas' },
  { key: 'resenas-multiples', label: 'R. Multiples' },
  { key: 'saldos', label: 'Saldos' },
  { key: 'impacto-social', label: 'Impacto Social' },
]

const estadosTrueque = ['PENDIENTE', 'ACEPTADO', 'RECHAZADO', 'EN_CURSO', 'FINALIZADO']
const estadosTruequeMultiple = ['PENDIENTE', 'ACEPTADO', 'RECHAZADO', 'EN_CURSO', 'FINALIZADO', 'EXPIRADO']

let debounceTimer = null

const cargarSeccion = async (seccion, busqueda = '') => {
  if (seccion === 'impacto-social') {
    await cargarImpactoSocial()
    return
  }
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

// CRUD
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

// Editar usuario
const abrirEditarUsuario = (u) => {
  Object.assign(modalEditarUsuario, {
    visible: true, id: u.id, username: u.username,
    nombre_real: u.nombre_real || '', email: u.email || '',
    horas_de_vida: u.horas_de_vida || 0, es_comercio: u.es_comercio || false,
  })
}

const guardarUsuario = async () => {
  try {
    await store.editarUsuario(modalEditarUsuario.id, {
      nombre_real: modalEditarUsuario.nombre_real,
      email: modalEditarUsuario.email,
      horas_de_vida: Number(modalEditarUsuario.horas_de_vida),
      es_comercio: modalEditarUsuario.es_comercio,
    })
    modalEditarUsuario.visible = false
  } catch { /* error en store */ }
}

// Editar publicacion
const abrirEditarPublicacion = (p) => {
  Object.assign(modalEditarPub, {
    visible: true, id: p.id, titulo: p.titulo || '', descripcion: p.descripcion || '',
    categoria: p.categoria || '', tipo: p.tipo || 'TALENTO', urgencia: p.urgencia || 'NORMAL',
  })
}

const guardarPublicacion = async () => {
  try {
    await store.editarPublicacion(modalEditarPub.id, {
      titulo: modalEditarPub.titulo,
      descripcion: modalEditarPub.descripcion,
      categoria: modalEditarPub.categoria,
      tipo: modalEditarPub.tipo,
      urgencia: modalEditarPub.urgencia,
    })
    modalEditarPub.visible = false
  } catch { /* error en store */ }
}

// Eliminar
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

// Impacto social
const cargarImpactoSocial = async () => {
  impactoCargando.value = true
  impactoError.value = ''
  try {
    const [pendientes, listaUsuarios, fondo, aprobadas] = await Promise.all([
      impactoStore.obtenerSolicitudesPendientes(),
      impactoStore.obtenerUsuariosAdmin(),
      impactoStore.obtenerSaldoFondo(),
      impactoStore.obtenerSolicitudesAprobadas(),
    ])
    solicitudesPendientes.value = pendientes.solicitudes || []
    impactoUsuarios.value = listaUsuarios.usuarios || []
    saldoFondo.value = Number(fondo.saldo || 0)
    solicitudesAprobadas.value = aprobadas.solicitudes || []
  } catch (err) {
    impactoError.value = err.message || 'Error al cargar impacto social.'
  } finally {
    impactoCargando.value = false
  }
}

const aprobarSolicitud = async (id) => {
  procesandoImpactoId.value = id
  impactoMensaje.value = ''
  try {
    const data = await impactoStore.aprobarSolicitud(id)
    impactoMensaje.value = data.mensaje || 'Solicitud aprobada.'
    await cargarImpactoSocial()
  } catch (err) {
    impactoError.value = err.message || 'Error al aprobar.'
  } finally {
    procesandoImpactoId.value = null
  }
}

const rechazarSolicitud = async (id) => {
  procesandoImpactoId.value = id
  impactoMensaje.value = ''
  try {
    await impactoStore.rechazarSolicitud(id)
    impactoMensaje.value = 'Solicitud rechazada.'
    await cargarImpactoSocial()
  } catch (err) {
    impactoError.value = err.message || 'Error al rechazar.'
  } finally {
    procesandoImpactoId.value = null
  }
}

const actualizarEstadoSocial = async (usuario, nuevoEstado) => {
  if (usuario.estado_social === nuevoEstado) return
  procesandoImpactoId.value = usuario.id
  impactoMensaje.value = ''
  try {
    const data = await impactoStore.actualizarEstadoSocial(usuario.id, nuevoEstado)
    usuario.estado_social = data.estado_social || nuevoEstado
    impactoMensaje.value = `Estado social actualizado a ${nuevoEstado}.`
  } catch (err) {
    impactoError.value = err.message || 'Error al actualizar.'
  } finally {
    procesandoImpactoId.value = null
  }
}

const asignarDesdeFondo = async () => {
  errorAsignacion.value = ''
  mensajeAsignacion.value = ''
  procesandoAsignacion.value = true
  try {
    const data = await impactoStore.asignarDesdeFondo(formImpacto.usuarioId, formImpacto.solicitudId, Number(formImpacto.monto))
    mensajeAsignacion.value = data.mensaje || 'Asignacion realizada.'
    saldoFondo.value = Number(data.saldo_fondo ?? 0)
    formImpacto.monto = ''
    formImpacto.solicitudId = null
    await cargarImpactoSocial()
  } catch (err) {
    errorAsignacion.value = err.message || 'Error al asignar.'
  } finally {
    procesandoAsignacion.value = false
  }
}

const badgeEstado = (estado) => {
  const map = {
    'PENDIENTE': 'badge--necesidad', 'ACEPTADO': 'badge--talento',
    'RECHAZADO': 'badge--critica', 'EN_CURSO': 'badge--alta',
    'FINALIZADO': 'badge--activa', 'EXPIRADO': 'badge--pausada',
  }
  return map[estado] || 'badge--normal'
}

const formatearFecha = (fecha) => {
  if (!fecha) return '—'
  try {
    return new Date(fecha).toLocaleDateString('es-VE', { year: 'numeric', month: 'short', day: 'numeric' })
  } catch { return fecha }
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

.panel__hint {
  font-size: 0.85rem;
  color: #666;
}

@media (max-width: 860px) {
  .admin-metric-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
