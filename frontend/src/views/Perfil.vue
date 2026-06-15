<template>
  <section class="perfil-page">
    <div class="panel panel--compact">
      <div class="panel__header">
        <h2 class="panel__title">Mi Perfil</h2>
      </div>
      <div class="panel__body" v-if="cargando">
        <div class="loading-state">Cargando perfil...</div>
      </div>
      <div class="panel__body" v-else-if="error">
        <p class="alert alert--error">{{ error }}</p>
      </div>
      <div class="panel__body" v-else-if="datosPerfil">
        <div class="perfil-info">
          <div class="perfil-header">
            <div class="perfil-avatar" :style="{ backgroundColor: getAvatarColor() }">
              {{ getInitials() }}
            </div>
            <div class="perfil-datos-principales">
              <div class="perfil-nombre-fila">
                <h3>{{ datosPerfil.usuario.nombre_real }}</h3>
                <span v-if="esMiembroActivo" class="badge badge--activa">Miembro Activo</span>
              </div>
              <p class="perfil-username">@{{ datosPerfil.usuario.username }}</p>
              <p class="perfil-email">{{ datosPerfil.usuario.email }}</p>
            </div>
          </div>

          <div class="perfil-estadisticas">
            <div class="estadistica-card">
              <div class="estadistica-icon">ESTRELLAS</div>
              <div class="estadistica-info">
                <div class="estadistica-valor">{{ promedioEstrellas.toFixed(1) }}</div>
                <div class="estadistica-label">Calificación</div>
              </div>
            </div>
            <div class="estadistica-card">
              <div class="estadistica-icon">HORAS</div>
              <div class="estadistica-info">
                <div class="estadistica-valor">{{ datosPerfil.usuario.horas_de_vida.toFixed(1) }}</div>
                <div class="estadistica-label">Horas de Vida</div>
              </div>
            </div>
          </div>

          <div class="perfil-seccion">
            <h4>Publicaciones Activas ({{ publicacionesActivas.length }})</h4>
            <div v-if="publicacionesActivas.length === 0" class="empty-state">
              No tienes publicaciones activas
            </div>
            <div v-else class="publicaciones-lista">
              <div
                v-for="pub in publicacionesActivas"
                :key="pub.id"
                class="publicacion-item"
              >
                <div class="publicacion-tipo" :class="'publicacion-tipo--' + pub.tipo.toLowerCase()">
                  {{ pub.tipo === 'TALENTO' ? 'Talento' : 'Necesidad' }}
                </div>
                <div class="publicacion-info">
                  <div class="publicacion-estado">
                    <span class="estado-badge estado-badge--activa">Activa</span>
                  </div>
                  <h5>{{ pub.titulo }}</h5>
                  <p>{{ pub.descripcion }}</p>
                  <div class="publicacion-meta">
                    <span class="categoria">{{ pub.categoria }}</span>
                    <span class="urgencia" :class="'urgencia--' + pub.urgencia.toLowerCase()">
                      {{ pub.urgencia }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="publicacionesPausadas.length" class="perfil-seccion">
            <h4>Publicaciones Pausadas ({{ publicacionesPausadas.length }})</h4>
            <div class="publicaciones-lista">
              <div
                v-for="pub in publicacionesPausadas"
                :key="pub.id"
                class="publicacion-item publicacion-item--pausada"
              >
                <div class="publicacion-tipo" :class="'publicacion-tipo--' + pub.tipo.toLowerCase()">
                  {{ pub.tipo === 'TALENTO' ? 'Talento' : 'Necesidad' }}
                </div>
                <div class="publicacion-info">
                  <div class="publicacion-estado">
                    <span class="estado-badge estado-badge--pausada">Pausada</span>
                  </div>
                  <h5>{{ pub.titulo }}</h5>
                  <p>{{ pub.descripcion }}</p>
                  <div class="publicacion-meta">
                    <span class="categoria">{{ pub.categoria }}</span>
                    <span class="urgencia" :class="'urgencia--' + pub.urgencia.toLowerCase()">
                      {{ pub.urgencia }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="perfil-seccion">
            <h4> Reseñas Recibidas ({{ cantidadResenas }})</h4>
            <div v-if="!datosPerfil?.resenas_recibidas || datosPerfil.resenas_recibidas.length === 0" class="empty-state">
              No has recibido reseñas aún
            </div>
            <div v-else class="resenas-lista">
              <div v-for="resena in datosPerfil.resenas_recibidas" :key="resena.id" class="resena-item">
                <div class="resena-calificacion">
                  <span class="estrellas">{{ ''.repeat(resena.estrellas) }}</span>
                  <span class="calificador">por @{{ nombreCalificador(resena) }}</span>
                </div>
                <p class="resena-comentario">{{ resena.comentario }}</p>
              </div>
            </div>
          </div>

          <div class="perfil-seccion">
            <h4>Mis trueques ({{ misTrueques.length }}) | Trueques Múltiples ({{ misTruequesMultiples.length }})</h4>
            <div v-if="cargandoTrueques" class="loading-state">Cargando trueques...</div>
            <div v-else-if="!misTrueques.length && !misTruequesMultiples.length" class="empty-state">
              No tienes acuerdos de trueque ni trueques múltiples registrados.
            </div>

            <div v-else>
              <div v-if="misTruequesMultiples.length > 0" class="trueques-grid">
                <article v-for="tm in misTruequesMultiples" :key="'tm-' + tm.id" class="trueque-card">
                  <div class="trueque-card__header">
                    <strong>Trueque Múltiple #{{ tm.id }}</strong>
                    <span :class="['trueque-card__estado', claseEstado(tm.estado)]">{{ tm.estado }}</span>
                  </div>

                  <div class="trueque-card__pubs">
                    <div v-if="tm.publicacion_emisor1 || tm.publicacion_receptor1">
                      <div v-if="!tm.todos_aceptaron" style="margin-bottom: 4px;">
                        Usuario1 aceptado: <strong>{{ tm.usuario1_aceptado ? 'Sí' : 'No' }}</strong>
                      </div>
                      <div><strong>Par 1:</strong>
                        <span v-if="tm.publicacion_emisor1">Ofrezco: {{ tm.publicacion_emisor1.titulo }}</span>
                        <span v-if="tm.publicacion_receptor1"> | Recibo: {{ tm.publicacion_receptor1.titulo }}</span>
                      </div>
                    </div>
                    <div v-if="tm.publicacion_emisor2 || tm.publicacion_receptor2">
                      <div v-if="!tm.todos_aceptaron" style="margin-bottom: 4px;">
                        Usuario2 aceptado: <strong>{{ tm.usuario2_aceptado ? 'Sí' : 'No' }}</strong>
                      </div>
                      <div><strong>Par 2:</strong>
                        <span v-if="tm.publicacion_emisor2">Ofrezco: {{ tm.publicacion_emisor2.titulo }}</span>
                        <span v-if="tm.publicacion_receptor2"> | Recibo: {{ tm.publicacion_receptor2.titulo }}</span>
                      </div>
                    </div>
                    <div v-if="tm.publicacion_emisor3 || tm.publicacion_receptor3">
                      <div v-if="!tm.todos_aceptaron" style="margin-bottom: 4px;">
                        Usuario3 aceptado: <strong>{{ tm.usuario3_aceptado ? 'Sí' : 'No' }}</strong>
                      </div>
                      <div><strong>Par 3:</strong>
                        <span v-if="tm.publicacion_emisor3">Ofrezco: {{ tm.publicacion_emisor3.titulo }}</span>
                        <span v-if="tm.publicacion_receptor3"> | Recibo: {{ tm.publicacion_receptor3.titulo }}</span>
                      </div>
                    </div>
                  </div>

                  <div v-if="!tm.todos_aceptaron" class="trueque-card__meta" style="margin-top:8px;">
                    <div style="font-size:0.9rem; color:var(--text-muted);">
                      <div>Todos aceptaron: <strong>No</strong></div>
                    </div>
                  </div>

                  <div v-if="tm.todos_aceptaron" class="codigo-confirmacion-multiple" style="margin: 1rem 0;">
                    <div v-if="tm.codigo_par1" class="codigo-par-item">
                      <div v-if="esEmisorPar(tm, 1)" class="codigo-emisor">
                        <span class="codigo-label">Código para Par 1:</span>
                        <span class="codigo-valor">{{ tm.codigo_par1 }}</span>
                        <span class="codigo-instruccion">Comparte este código con {{ tm.receptor1_nombre }}</span>
                        <span v-if="tm.par1_confirmado" class="codigo-confirmado">✓ Confirmado</span>
                      </div>
                      <div v-else-if="esReceptorPar(tm, 1)" class="codigo-receptor">
                        <span v-if="tm.par1_confirmado" class="codigo-confirmado">✓ Código validado correctamente</span>
                        <span v-else class="codigo-instruccion">Ingresa el código que te compartió {{ tm.emisor1_nombre }}</span>
                        <div v-if="!tm.par1_confirmado && mostrandoInputCodigoPar === `${tm.id}-1`" class="codigo-input-container">
                          <input
                            v-model="codigoIngresadoPar1"
                            type="text"
                            class="codigo-input"
                            placeholder="Ingresa el código de 8 caracteres"
                            maxlength="8"
                            @keyup.enter="validarCodigoParMultiple(tm, 1)"
                          />
                          <button
                            class="button button--primary button--small"
                            type="button"
                            :disabled="procesandoTruequeId === tm.id"
                            @click="validarCodigoParMultiple(tm, 1)"
                          >
                            Validar
                          </button>
                          <button
                            class="button button--secondary button--small"
                            type="button"
                            @click="mostrandoInputCodigoPar = null; codigoIngresadoPar1 = ''"
                          >
                            Cancelar
                          </button>
                        </div>
                        <button
                          v-else-if="!tm.par1_confirmado"
                          class="button button--primary button--small"
                          type="button"
                          @click="mostrandoInputCodigoPar = `${tm.id}-1`"
                        >
                          Ingresar código
                        </button>
                      </div>
                    </div>
                    <div v-if="tm.codigo_par2" class="codigo-par-item">
                      <div v-if="esEmisorPar(tm, 2)" class="codigo-emisor">
                        <span class="codigo-label">Código para Par 2:</span>
                        <span class="codigo-valor">{{ tm.codigo_par2 }}</span>
                        <span class="codigo-instruccion">Comparte este código con {{ tm.receptor2_nombre }}</span>
                        <span v-if="tm.par2_confirmado" class="codigo-confirmado">✓ Confirmado</span>
                      </div>
                      <div v-else-if="esReceptorPar(tm, 2)" class="codigo-receptor">
                        <span v-if="tm.par2_confirmado" class="codigo-confirmado">✓ Código validado correctamente</span>
                        <span v-else class="codigo-instruccion">Ingresa el código que te compartió {{ tm.emisor2_nombre }}</span>
                        <div v-if="!tm.par2_confirmado && mostrandoInputCodigoPar === `${tm.id}-2`" class="codigo-input-container">
                          <input
                            v-model="codigoIngresadoPar2"
                            type="text"
                            class="codigo-input"
                            placeholder="Ingresa el código de 8 caracteres"
                            maxlength="8"
                            @keyup.enter="validarCodigoParMultiple(tm, 2)"
                          />
                          <button
                            class="button button--primary button--small"
                            type="button"
                            :disabled="procesandoTruequeId === tm.id"
                            @click="validarCodigoParMultiple(tm, 2)"
                          >
                            Validar
                          </button>
                          <button
                            class="button button--secondary button--small"
                            type="button"
                            @click="mostrandoInputCodigoPar = null; codigoIngresadoPar2 = ''"
                          >
                            Cancelar
                          </button>
                        </div>
                        <button
                          v-else-if="!tm.par2_confirmado"
                          class="button button--primary button--small"
                          type="button"
                          @click="mostrandoInputCodigoPar = `${tm.id}-2`"
                        >
                          Ingresar código
                        </button>
                      </div>
                    </div>
                    <div v-if="tm.codigo_par3" class="codigo-par-item">
                      <div v-if="esEmisorPar(tm, 3)" class="codigo-emisor">
                        <span class="codigo-label">Código para Par 3:</span>
                        <span class="codigo-valor">{{ tm.codigo_par3 }}</span>
                        <span class="codigo-instruccion">Comparte este código con {{ tm.receptor3_nombre }}</span>
                        <span v-if="tm.par3_confirmado" class="codigo-confirmado">✓ Confirmado</span>
                      </div>
                      <div v-else-if="esReceptorPar(tm, 3)" class="codigo-receptor">
                        <span v-if="tm.par3_confirmado" class="codigo-confirmado">✓ Código validado correctamente</span>
                        <span v-else class="codigo-instruccion">Ingresa el código que te compartió {{ tm.emisor3_nombre }}</span>
                        <div v-if="!tm.par3_confirmado && mostrandoInputCodigoPar === `${tm.id}-3`" class="codigo-input-container">
                          <input
                            v-model="codigoIngresadoPar3"
                            type="text"
                            class="codigo-input"
                            placeholder="Ingresa el código de 8 caracteres"
                            maxlength="8"
                            @keyup.enter="validarCodigoParMultiple(tm, 3)"
                          />
                          <button
                            class="button button--primary button--small"
                            type="button"
                            :disabled="procesandoTruequeId === tm.id"
                            @click="validarCodigoParMultiple(tm, 3)"
                          >
                            Validar
                          </button>
                          <button
                            class="button button--secondary button--small"
                            type="button"
                            @click="mostrandoInputCodigoPar = null; codigoIngresadoPar3 = ''"
                          >
                            Cancelar
                          </button>
                        </div>
                        <button
                          v-else-if="!tm.par3_confirmado"
                          class="button button--primary button--small"
                          type="button"
                          @click="mostrandoInputCodigoPar = `${tm.id}-3`"
                        >
                          Ingresar código
                        </button>
                      </div>
                    </div>
                  </div>

                  <div v-if="tm.todos_pares_confirmaron && tm.estado === 'FINALIZADO'" class="resenas-multiple" style="margin: 1rem 0; padding: 1rem; background: #f0f7ff; border-radius: 8px; border: 1px solid #b8daff;">
                    <h4 style="margin: 0 0 1rem 0; color: #004085;">Deja tu reseña</h4>
                    <div v-if="esReceptorPar(tm, 1)" class="resena-par-item" style="margin-bottom: 1rem;">
                      <div style="margin-bottom: 0.5rem;">
                        <strong>Reseña para {{ tm.emisor1_nombre }} (quien resolvió tu necesidad en Par 1):</strong>
                      </div>
                      <div v-if="mostrandoFormularioResena === `${tm.id}-1`">
                        <div style="margin-bottom: 0.5rem;">
                          <label style="margin-right: 0.5rem;">Calificación:</label>
                          <select v-model="resenaEstrellas" style="padding: 0.25rem;">
                            <option value="1">1 estrella</option>
                            <option value="2">2 estrellas</option>
                            <option value="3">3 estrellas</option>
                            <option value="4">4 estrellas</option>
                            <option value="5">5 estrellas</option>
                          </select>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                          <label style="display: block; margin-bottom: 0.25rem;">Comentario:</label>
                          <textarea
                            v-model="resenaComentario"
                            placeholder="Escribe tu comentario (opcional)"
                            maxlength="500"
                            style="width: 100%; padding: 0.5rem; border: 1px solid #ced4da; border-radius: 4px; resize: vertical; min-height: 60px;"
                          ></textarea>
                        </div>
                        <button
                          class="button button--primary button--small"
                          type="button"
                          :disabled="procesandoTruequeId === tm.id"
                          @click="enviarResenaMultiple(tm, tm.emisor1)"
                        >
                          Enviar reseña
                        </button>
                        <button
                          class="button button--secondary button--small"
                          type="button"
                          @click="mostrandoFormularioResena = null; resenaEstrellas = 5; resenaComentario = ''"
                        >
                          Cancelar
                        </button>
                      </div>
                      <button
                        v-else
                        class="button button--primary button--small"
                        type="button"
                        @click="mostrandoFormularioResena = `${tm.id}-1`"
                      >
                        Dejar reseña
                      </button>
                    </div>
                    <div v-if="esReceptorPar(tm, 2)" class="resena-par-item" style="margin-bottom: 1rem;">
                      <div style="margin-bottom: 0.5rem;">
                        <strong>Reseña para {{ tm.emisor2_nombre }} (quien resolvió tu necesidad en Par 2):</strong>
                      </div>
                      <div v-if="mostrandoFormularioResena === `${tm.id}-2`">
                        <div style="margin-bottom: 0.5rem;">
                          <label style="margin-right: 0.5rem;">Calificación:</label>
                          <select v-model="resenaEstrellas" style="padding: 0.25rem;">
                            <option value="1">1 estrella</option>
                            <option value="2">2 estrellas</option>
                            <option value="3">3 estrellas</option>
                            <option value="4">4 estrellas</option>
                            <option value="5">5 estrellas</option>
                          </select>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                          <label style="display: block; margin-bottom: 0.25rem;">Comentario:</label>
                          <textarea
                            v-model="resenaComentario"
                            placeholder="Escribe tu comentario (opcional)"
                            maxlength="500"
                            style="width: 100%; padding: 0.5rem; border: 1px solid #ced4da; border-radius: 4px; resize: vertical; min-height: 60px;"
                          ></textarea>
                        </div>
                        <button
                          class="button button--primary button--small"
                          type="button"
                          :disabled="procesandoTruequeId === tm.id"
                          @click="enviarResenaMultiple(tm, tm.emisor2)"
                        >
                          Enviar reseña
                        </button>
                        <button
                          class="button button--secondary button--small"
                          type="button"
                          @click="mostrandoFormularioResena = null; resenaEstrellas = 5; resenaComentario = ''"
                        >
                          Cancelar
                        </button>
                      </div>
                      <button
                        v-else
                        class="button button--primary button--small"
                        type="button"
                        @click="mostrandoFormularioResena = `${tm.id}-2`"
                      >
                        Dejar reseña
                      </button>
                    </div>
                    <div v-if="esReceptorPar(tm, 3)" class="resena-par-item" style="margin-bottom: 1rem;">
                      <div style="margin-bottom: 0.5rem;">
                        <strong>Reseña para {{ tm.emisor3_nombre }} (quien resolvió tu necesidad en Par 3):</strong>
                      </div>
                      <div v-if="mostrandoFormularioResena === `${tm.id}-3`">
                        <div style="margin-bottom: 0.5rem;">
                          <label style="margin-right: 0.5rem;">Calificación:</label>
                          <select v-model="resenaEstrellas" style="padding: 0.25rem;">
                            <option value="1">1 estrella</option>
                            <option value="2">2 estrellas</option>
                            <option value="3">3 estrellas</option>
                            <option value="4">4 estrellas</option>
                            <option value="5">5 estrellas</option>
                          </select>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                          <label style="display: block; margin-bottom: 0.25rem;">Comentario:</label>
                          <textarea
                            v-model="resenaComentario"
                            placeholder="Escribe tu comentario (opcional)"
                            maxlength="500"
                            style="width: 100%; padding: 0.5rem; border: 1px solid #ced4da; border-radius: 4px; resize: vertical; min-height: 60px;"
                          ></textarea>
                        </div>
                        <button
                          class="button button--primary button--small"
                          type="button"
                          :disabled="procesandoTruequeId === tm.id"
                          @click="enviarResenaMultiple(tm, tm.emisor3)"
                        >
                          Enviar reseña
                        </button>
                        <button
                          class="button button--secondary button--small"
                          type="button"
                          @click="mostrandoFormularioResena = null; resenaEstrellas = 5; resenaComentario = ''"
                        >
                          Cancelar
                        </button>
                      </div>
                      <button
                        v-else
                        class="button button--primary button--small"
                        type="button"
                        @click="mostrandoFormularioResena = `${tm.id}-3`"
                      >
                        Dejar reseña
                      </button>
                    </div>
                  </div>

                  <div class="trueque-card__actions">
                    <button
                      v-if="tm.puede_aceptar"
                      class="button button--primary button--small"
                      :disabled="procesandoTruequeId === tm.id"
                      @click="aceptarTruequeMultiple(tm)"
                    >
                      Aceptar trueque múltiple
                    </button>

                    <button v-else class="button button--secondary button--small" disabled>
                      {{ tm.todos_aceptaron ? 'Todos aceptaron' : 'Esperando aceptación' }}
                    </button>
                  </div>
                </article>
              </div>

              <div v-if="misTrueques.length > 0" class="trueques-grid">
                <article v-for="trueque in misTrueques" :key="trueque.id" class="trueque-card">
                  <div class="trueque-card__header">
                    <strong>{{ nombreContraparte(trueque) }}</strong>
                    <span :class="['trueque-card__estado', claseEstado(trueque.estado)]">
                      {{ trueque.estado }}
                    </span>
                  </div>
                  <div class="trueque-card__pubs">
                    <span v-if="trueque.es_intercambio_mutuo" class="trueque-mutuo-badge">
                      Intercambio equilibrado (0 horas netas)
                    </span>
                    <span v-if="etiquetaOfertaPropia(trueque)">
                      {{ etiquetaOfertaPropia(trueque) }}: {{ tituloOfertaPropia(trueque) }}
                    </span>
                    <span v-if="etiquetaOfertaContraparte(trueque)">
                      {{ etiquetaOfertaContraparte(trueque) }}: {{ tituloOfertaContraparte(trueque) }}
                    </span>
                    <span
                      v-if="!trueque.es_intercambio_mutuo && trueque.impacto_horas"
                      class="trueque-impacto"
                    >
                      Impacto en tus horas: {{ formatearImpacto(trueque.impacto_horas) }}
                    </span>
                  </div>
                  <p v-if="mensajeEspera(trueque)" class="trueque-espera">
                    {{ mensajeEspera(trueque) }}
                  </p>
                  <div v-if="trueque.estado === 'EN_CURSO' && trueque.codigo_confirmacion" class="codigo-confirmacion">
                    <div v-if="Number(trueque.emisor) === Number(datosPerfil?.usuario?.id)" class="codigo-emisor">
                      <span class="codigo-label">Código de confirmación:</span>
                      <span class="codigo-valor">{{ trueque.codigo_confirmacion }}</span>
                      <span class="codigo-instruccion">Comparte este código con {{ trueque.receptor_nombre }}</span>
                    </div>
                    <div v-else class="codigo-receptor">
                      <span class="codigo-instruccion">Ingresa el código que te compartió {{ trueque.emisor_nombre }}</span>
                      <div v-if="mostrandoInputCodigo === trueque.id" class="codigo-input-container">
                        <input
                          v-model="codigoIngresado"
                          type="text"
                          class="codigo-input"
                          placeholder="Ingresa el código de 8 caracteres"
                          maxlength="8"
                          @keyup.enter="validarCodigo(trueque)"
                        />
                        <button
                          class="button button--primary button--small"
                          type="button"
                          :disabled="procesandoTruequeId === trueque.id"
                          @click="validarCodigo(trueque)"
                        >
                          Validar
                        </button>
                        <button
                          class="button button--secondary button--small"
                          type="button"
                          @click="mostrandoInputCodigo = null; codigoIngresado = ''"
                        >
                          Cancelar
                        </button>
                      </div>
                      <button
                        v-else
                        class="button button--primary button--small"
                        type="button"
                        @click="mostrandoInputCodigo = trueque.id"
                      >
                        Ingresar código
                      </button>
                    </div>
                  </div>
                  <div class="trueque-card__actions">
                    <button
                      v-if="trueque.estado === 'PENDIENTE' && (!trueque.publicacion_emisor || !trueque.publicacion_receptor)"
                      class="button button--primary button--small"
                      type="button"
                      @click="completarPropuesta(trueque)"
                    >
                      {{ etiquetaPropuestaPendiente(trueque) }}
                    </button>
                    <button
                      v-if="trueque.puede_confirmar"
                      class="button button--primary button--small"
                      type="button"
                      :disabled="procesandoTruequeId === trueque.id"
                      @click="confirmarFinalizacion(trueque)"
                    >
                      Confirmar finalización
                    </button>
                    <button
                      v-if="trueque.pendiente_resena"
                      class="button button--secondary button--small"
                      type="button"
                      @click="abrirResena(trueque)"
                    >
                      Dejar reseña
                    </button>
                  </div>
                  <p
                    v-if="feedbackTrueque[trueque.id]"
                    :class="['alert', feedbackTruequeOk[trueque.id] ? 'alert--success' : 'alert--error']"
                  >
                    {{ feedbackTrueque[trueque.id] }}
                  </p>
                </article>
              </div>
            </div>
          </div>

          <div class="perfil-seccion">
            <h4>Actividad de Trueques</h4>
            <div class="trueques-info">
              <div class="trueque-stat">
                <span class="trueque-label">Propuestas enviadas:</span>
                <span class="trueque-valor">{{ datosPerfil.trueques_enviados_count }}</span>
              </div>
              <div class="trueque-stat">
                <span class="trueque-label">Propuestas recibidas:</span>
                <span class="trueque-valor">{{ datosPerfil.trueques_recibidos_count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, inject, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { usePerfilStore } from '../stores/perfil.js'
import { useTruequeStore } from '../stores/trueque.js'

const authStore = useAuthStore()
const perfilStore = usePerfilStore()
const truequeStore = useTruequeStore()
const hu4 = inject('hu4', null)
const datosPerfil = ref(null)
const cargando = ref(true)
const error = ref('')
const misTrueques = ref([])
const misTruequesMultiples = ref([])
const cargandoTrueques = ref(false)
const procesandoTruequeId = ref(null)
const feedbackTrueque = reactive({})
const feedbackTruequeOk = reactive({})
const usuarioActualId = ref(null)
const codigoIngresado = ref('')
const mostrandoInputCodigo = ref(null)
const codigoIngresadoPar1 = ref('')
const codigoIngresadoPar2 = ref('')
const codigoIngresadoPar3 = ref('')
const mostrandoInputCodigoPar = ref(null)
const mostrandoFormularioResena = ref(null)
const resenaEstrellas = ref(5)
const resenaComentario = ref('')

const publicacionesActivas = computed(() => {
  if (!datosPerfil.value) return []
  if (Array.isArray(datosPerfil.value.publicaciones_activas)) {
    return datosPerfil.value.publicaciones_activas
  }
  return (datosPerfil.value.publicaciones || []).filter((pub) => pub.esta_activa)
})

const publicacionesPausadas = computed(() => {
  if (!datosPerfil.value) return []
  if (Array.isArray(datosPerfil.value.publicaciones_pausadas)) {
    return datosPerfil.value.publicaciones_pausadas
  }
  return (datosPerfil.value.publicaciones || []).filter((pub) => !pub.esta_activa)
})

const esMiembroActivo = computed(() => {
  if (!datosPerfil.value) return false
  if (typeof datosPerfil.value.es_miembro_activo === 'boolean') {
    return datosPerfil.value.es_miembro_activo
  }
  const usuario = datosPerfil.value.usuario
  const publicaciones = datosPerfil.value.publicaciones || []
  return Boolean(usuario?.nombre_real?.trim() && publicaciones.length > 0)
})

const promedioEstrellas = computed(() => {
  if (!datosPerfil.value) return 5.0
  return datosPerfil.value.promedio_estrellas
    ?? datosPerfil.value.usuario?.promedio_estrellas
    ?? 5.0
})

const cantidadResenas = computed(() => {
  if (!datosPerfil.value) return 0
  if (typeof datosPerfil.value.cantidad_resenas === 'number') {
    return datosPerfil.value.cantidad_resenas
  }
  return datosPerfil.value.resenas_recibidas?.length ?? 0
})

const nombreCalificador = (resena) => {
  if (resena.calificador_username) return resena.calificador_username
  if (resena.calificador?.username) return resena.calificador.username
  if (resena.calificador_nombre) return resena.calificador_nombre
  return 'usuario'
}

const cargarPerfil = async () => {
  try {
    const response = await perfilStore.cargarMiPerfil()
    datosPerfil.value = response
  } catch (err) {
    error.value = 'Error al cargar el perfil: ' + (err.message || 'Error desconocido')
  } finally {
    cargando.value = false
  }
}

const cargarMisTrueques = async () => {
  cargandoTrueques.value = true
  try {
    const [truequesData, truequesMultiplesData] = await Promise.all([
      truequeStore.obtenerMisTrueques(),
      truequeStore.obtenerMisTruequesMultiples(),
    ])
    console.log('Datos completos:', { truequesData, truequesMultiplesData })
    console.log(`Trueques normales: ${truequesData.trueques.length}, Trueques múltiples: ${truequesMultiplesData.trueques_multiple.length}`)
    misTrueques.value = truequesData.trueques || []
    misTruequesMultiples.value = truequesMultiplesData.trueques_multiple || []
  } catch {
    misTrueques.value = []
    misTruequesMultiples.value = []
  } finally {
    cargandoTrueques.value = false
  }
}

const nombreContraparte = (trueque) => {
  if (Number(trueque.emisor) === Number(usuarioActualId.value)) return trueque.receptor_nombre
  return trueque.emisor_nombre
}

const tituloOfertaPropia = (trueque) => (
  trueque.oferta_propia_titulo
  || (Number(trueque.emisor) === Number(usuarioActualId.value)
    ? trueque.publicacion_emisor?.titulo
    : trueque.publicacion_receptor?.titulo)
  || ''
)

const tituloOfertaContraparte = (trueque) => (
  trueque.oferta_contraparte_titulo
  || (Number(trueque.emisor) === Number(usuarioActualId.value)
    ? trueque.publicacion_receptor?.titulo
    : trueque.publicacion_emisor?.titulo)
  || ''
)

const etiquetaOfertaPropia = (trueque) => (trueque.es_intercambio_mutuo ? 'Yo ofrezco' : 'Ofrezco')

const etiquetaOfertaContraparte = (trueque) => (
  trueque.es_intercambio_mutuo ? 'Recibo de contraparte' : 'Solicito'
)

const formatearImpacto = (impacto) => {
  if (impacto > 0) return `+${impacto.toFixed(1)} h`
  if (impacto < 0) return `${impacto.toFixed(1)} h`
  return '0 h'
}

const claseEstado = (estado) => {
  const mapa = {
    ACEPTADO: 'trueque-card__estado--aceptado',
    FINALIZADO: 'trueque-card__estado--finalizado',
    RECHAZADO: 'trueque-card__estado--rechazado',
    PENDIENTE: 'trueque-card__estado--pendiente',
  }
  return mapa[estado] || 'trueque-card__estado--pendiente'
}

const mensajeEspera = (trueque) => {
  if (trueque.estado !== 'ACEPTADO') return ''
  if (trueque.emisor === usuarioActualId.value && trueque.emisor_confirmado && !trueque.receptor_confirmado) {
    return `Esperando confirmación de ${trueque.receptor_nombre}`
  }
  if (trueque.receptor === usuarioActualId.value && trueque.receptor_confirmado && !trueque.emisor_confirmado) {
    return `Esperando confirmación de ${trueque.emisor_nombre}`
  }
  return ''
}

const confirmarFinalizacion = async (trueque) => {
  procesandoTruequeId.value = trueque.id
  feedbackTrueque[trueque.id] = ''
  feedbackTruequeOk[trueque.id] = false

  try {
    const resultado = await perfilStore.finalizarTrueque(trueque.id, authStore)
    feedbackTruequeOk[trueque.id] = true
    feedbackTrueque[trueque.id] = resultado.message || 'Confirmación registrada.'
    await cargarPerfil()

    if (resultado.habilitar_resena) {
      await cargarMisTrueques()
      const truequeActualizado = misTrueques.value.find((item) => item.id === trueque.id)
      if (truequeActualizado?.pendiente_resena && hu4?.abrirModalResenaPrioritario) {
        hu4.abrirModalResenaPrioritario(truequeActualizado)
      }
    } else {
      await cargarMisTrueques()
    }

    if (hu4?.refrescarDatosHu4) {
      await hu4.refrescarDatosHu4({ omitirModalesAutomaticos: resultado.habilitar_resena })
    }
  } catch (err) {
    feedbackTrueque[trueque.id] = err.message || 'No se pudo confirmar el trueque.'
  } finally {
    procesandoTruequeId.value = null
  }
}

const validarCodigo = async (trueque) => {
  if (!codigoIngresado.value) {
    feedbackTrueque[trueque.id] = 'Por favor ingresa el código de confirmación.'
    feedbackTruequeOk[trueque.id] = false
    return
  }

  procesandoTruequeId.value = trueque.id
  feedbackTrueque[trueque.id] = ''
  feedbackTruequeOk[trueque.id] = false

  try {
    const resultado = await truequeStore.validarCodigoTrueque(trueque.id, codigoIngresado.value)
    feedbackTruequeOk[trueque.id] = true
    feedbackTrueque[trueque.id] = resultado.message || 'Código validado correctamente.'
    codigoIngresado.value = ''
    mostrandoInputCodigo.value = null
    await cargarPerfil()
    await cargarMisTrueques()

    if (resultado.habilitar_resena) {
      const truequeActualizado = misTrueques.value.find((item) => item.id === trueque.id)
      if (truequeActualizado?.pendiente_resena && hu4?.abrirModalResenaPrioritario) {
        hu4.abrirModalResenaPrioritario(truequeActualizado)
      }
    }

    if (hu4?.refrescarDatosHu4) {
      await hu4.refrescarDatosHu4({ omitirModalesAutomaticos: resultado.habilitar_resena })
    }
  } catch (err) {
    feedbackTrueque[trueque.id] = err.message || 'Código inválido.'
  } finally {
    procesandoTruequeId.value = null
  }
}

const abrirResena = (trueque) => {
  if (hu4?.abrirModalResena) {
    hu4.abrirModalResena(trueque)
  }
}

const etiquetaPropuestaPendiente = (trueque) => {
  if (trueque.publicacion_emisor && trueque.publicacion_receptor) {
    return 'Completar propuesta'
  }
  return 'Realizar trueque'
}

const completarPropuesta = async (trueque) => {
  if (hu4?.abrirModalPropuestaDesdeTrueque) {
    await hu4.abrirModalPropuestaDesdeTrueque(trueque)
  }
}

const getInitials = () => {
  const nombre = datosPerfil.value?.usuario?.nombre_real || datosPerfil.value?.usuario?.username || 'U'
  return nombre.charAt(0).toUpperCase()
}

const getAvatarColor = () => {
  const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b', '#fa709a', '#fee140']
  const username = datosPerfil.value?.usuario?.username || ''
  const index = username.charCodeAt(0) % colors.length
  return colors[index]
}

const refrescarVistaPerfil = async () => {
  await Promise.all([cargarPerfil(), cargarMisTrueques()])
}

  const aceptarTruequeMultiple = async (truequeMultiple) => {
  procesandoTruequeId.value = truequeMultiple.id
  try {
    // Usar el método del store que existe: responderPropuestaMultiple
    const resultado = await truequeStore.responderPropuestaMultiple(truequeMultiple.id, 'aceptar')
    alert(resultado.mensaje || resultado.message || 'Trueque múltiple aceptado')
    await cargarMisTrueques()
  } catch (err) {
    alert(err.message || 'Error al aceptar trueque múltiple')
  } finally {
    procesandoTruequeId.value = null
  }
}

const esEmisorPar = (truequeMultiple, parNum) => {
  const uid = Number(usuarioActualId.value)
  if (parNum === 1) return Number(truequeMultiple.emisor1) === uid
  if (parNum === 2) return Number(truequeMultiple.emisor2) === uid
  if (parNum === 3) return Number(truequeMultiple.emisor3) === uid
  return false
}

const esReceptorPar = (truequeMultiple, parNum) => {
  const uid = Number(usuarioActualId.value)
  if (parNum === 1) return Number(truequeMultiple.receptor1) === uid
  if (parNum === 2) return Number(truequeMultiple.receptor2) === uid
  if (parNum === 3) return Number(truequeMultiple.receptor3) === uid
  return false
}

const validarCodigoParMultiple = async (truequeMultiple, parNum) => {
  let codigo = ''
  if (parNum === 1) codigo = codigoIngresadoPar1.value
  if (parNum === 2) codigo = codigoIngresadoPar2.value
  if (parNum === 3) codigo = codigoIngresadoPar3.value

  if (!codigo) {
    feedbackTrueque[truequeMultiple.id] = 'Por favor ingresa el código de confirmación.'
    feedbackTruequeOk[truequeMultiple.id] = false
    return
  }

  procesandoTruequeId.value = truequeMultiple.id
  feedbackTrueque[truequeMultiple.id] = ''
  feedbackTruequeOk[truequeMultiple.id] = false

  try {
    const resultado = await truequeStore.validarCodigoParMultiple(truequeMultiple.id, parNum, codigo)
    feedbackTruequeOk[truequeMultiple.id] = true
    feedbackTrueque[truequeMultiple.id] = resultado.message || 'Código validado correctamente.'

    // Limpiar el código ingresado
    if (parNum === 1) codigoIngresadoPar1.value = ''
    if (parNum === 2) codigoIngresadoPar2.value = ''
    if (parNum === 3) codigoIngresadoPar3.value = ''
    mostrandoInputCodigoPar.value = null

    await cargarPerfil()
    await cargarMisTrueques()

    if (hu4?.refrescarDatosHu4) {
      await hu4.refrescarDatosHu4()
    }
  } catch (err) {
    feedbackTrueque[truequeMultiple.id] = err.message || 'Código inválido.'
  } finally {
    procesandoTruequeId.value = null
  }
}

const enviarResenaMultiple = async (truequeMultiple, calificadoId) => {
  if (!resenaEstrellas.value || resenaEstrellas.value < 1 || resenaEstrellas.value > 5) {
    feedbackTrueque[truequeMultiple.id] = 'Por selecciona una calificación entre 1 y 5 estrellas.'
    feedbackTruequeOk[truequeMultiple.id] = false
    return
  }

  procesandoTruequeId.value = truequeMultiple.id
  feedbackTrueque[truequeMultiple.id] = ''
  feedbackTruequeOk[truequeMultiple.id] = false

  try {
    const resultado = await truequeStore.registrarResenaMultiple(
      truequeMultiple.id,
      calificadoId,
      resenaEstrellas.value,
      resenaComentario.value
    )
    feedbackTruequeOk[truequeMultiple.id] = true
    feedbackTrueque[truequeMultiple.id] = resultado.mensaje || resultado.message || 'Reseña enviada correctamente.'

    // Limpiar el formulario
    resenaEstrellas.value = 5
    resenaComentario.value = ''
    mostrandoFormularioResena.value = null

    await cargarPerfil()
    await cargarMisTrueques()

    if (hu4?.refrescarDatosHu4) {
      await hu4.refrescarDatosHu4()
    }
  } catch (err) {
    feedbackTrueque[truequeMultiple.id] = err.message || 'Error al enviar reseña.'
  } finally {
    procesandoTruequeId.value = null
  }
}

onMounted(async () => {
  await authStore.obtenerSesionActual()
  usuarioActualId.value = authStore.usuarioActual?.id ?? null
  if (hu4?.registrarRefrescarPerfil) {
    hu4.registrarRefrescarPerfil(refrescarVistaPerfil)
  }
  if (hu4?.registrarResenaEnviada) {
    hu4.registrarResenaEnviada(refrescarVistaPerfil)
  }
  await refrescarVistaPerfil()
})

onUnmounted(() => {
  if (hu4?.registrarRefrescarPerfil) {
    hu4.registrarRefrescarPerfil(null)
  }
})
</script>

<style scoped>
.perfil-page {
  padding: 1rem;
  max-width: 800px;
  margin: 0 auto;
}

.panel--compact {
  max-width: 100%;
  margin: 0 auto;
}

.perfil-info {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.perfil-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e0e0e0;
}

.perfil-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  font-weight: bold;
  color: white;
  flex-shrink: 0;
}

.perfil-nombre-fila {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 0.25rem;
}

.perfil-datos-principales h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #333;
}

.perfil-username {
  margin: 0 0 0.25rem 0;
  color: #666;
  font-weight: 500;
  font-size: 0.9rem;
}

.perfil-email {
  margin: 0;
  color: #888;
  font-size: 0.8rem;
}

.perfil-estadisticas {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.75rem;
}

.estadistica-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.estadistica-icon {
  font-size: 1.5rem;
}

.estadistica-valor {
  font-size: 1.2rem;
  font-weight: bold;
  color: #333;
}

.estadistica-label {
  color: #666;
  font-size: 0.8rem;
}

.perfil-seccion {
  margin-top: 1.5rem;
}

.perfil-seccion h4 {
  margin: 0 0 0.75rem 0;
  color: #333;
  font-size: 1.1rem;
}

.empty-state {
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
  color: #666;
  text-align: center;
  border: 1px dashed #ccc;
  font-size: 0.9rem;
}

.publicaciones-lista,
.resenas-lista {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.publicacion-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #667eea;
  font-size: 0.9rem;
}

.publicacion-item--pausada {
  opacity: 0.72;
  border-left-color: #adb5bd;
  background: #f1f3f5;
}

.publicacion-estado {
  margin-bottom: 0.35rem;
}

.estado-badge {
  display: inline-block;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
}

.estado-badge--activa {
  background: #e7f7f1;
  color: #175f49;
}

.estado-badge--pausada {
  background: #e9ecef;
  color: #5f6b7a;
}

.publicacion-tipo {
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-weight: bold;
  font-size: 0.7rem;
  white-space: nowrap;
}

.publicacion-tipo--talento {
  background: #d4edda;
  color: #155724;
}

.publicacion-tipo--necesidad {
  background: #fff3cd;
  color: #856404;
}

.publicacion-info h5 {
  margin: 0 0 0.25rem 0;
  color: #333;
  font-size: 1rem;
}

.publicacion-info p {
  margin: 0 0 0.25rem 0;
  color: #666;
  font-size: 0.85rem;
}

.publicacion-meta {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.categoria {
  padding: 0.25rem 0.5rem;
  background: #e9ecef;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #495057;
}

.urgencia {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: bold;
}

.urgencia--normal {
  background: #d4edda;
  color: #155724;
}

.urgencia--alta {
  background: #fff3cd;
  color: #856404;
}

.urgencia--critica {
  background: #f8d7da;
  color: #721c24;
}

.resena-item {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #ffc107;
}

.resena-calificacion {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.estrellas {
  color: #ffc107;
  font-size: 1.2rem;
}

.calificador {
  color: #666;
  font-weight: 500;
}

.resena-comentario {
  margin: 0;
  color: #333;
  font-style: italic;
}

.trueques-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.trueque-stat {
  display: flex;
  justify-content: space-between;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.trueque-label {
  color: #666;
}

.trueque-valor {
  font-weight: bold;
  color: #333;
  font-size: 1.2rem;
}

.codigo-confirmacion {
  margin: 1rem 0;
  padding: 1rem;
  background: #f0f7ff;
  border-radius: 8px;
  border: 1px solid #b8daff;
}

.codigo-emisor {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.codigo-receptor {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.codigo-label {
  font-weight: bold;
  color: #004085;
  font-size: 0.9rem;
}

.codigo-valor {
  font-family: 'Courier New', monospace;
  font-size: 1.5rem;
  font-weight: bold;
  color: #004085;
  letter-spacing: 0.2rem;
  padding: 0.5rem;
  background: white;
  border-radius: 4px;
  text-align: center;
  border: 2px solid #004085;
}

.codigo-instruccion {
  color: #6c757d;
  font-size: 0.85rem;
  font-style: italic;
}

.codigo-input-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.codigo-input {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 1rem;
  font-family: 'Courier New', monospace;
  text-align: center;
  letter-spacing: 0.1rem;
  text-transform: uppercase;
}

.codigo-confirmacion-multiple {
  padding: 1rem;
  background: #f0f7ff;
  border-radius: 8px;
  border: 1px solid #b8daff;
}

.codigo-par-item {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.codigo-par-item:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.codigo-confirmado {
  color: #28a745;
  font-weight: bold;
  margin-left: 0.5rem;
}
</style>
