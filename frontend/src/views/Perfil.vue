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
              <h3>{{ datosPerfil.usuario.nombre_real }}</h3>
              <p class="perfil-username">@{{ datosPerfil.usuario.username }}</p>
              <p class="perfil-email">{{ datosPerfil.usuario.email }}</p>
            </div>
          </div>

          <div class="perfil-estadisticas">
            <div class="estadistica-card">
              <div class="estadistica-icon">ESTRELLAS</div>
              <div class="estadistica-info">
                <div class="estadistica-valor">{{ datosPerfil.usuario.promedio_estrellas.toFixed(1) }}</div>
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
            <div class="estadistica-card">
              <div class="estadistica-icon">DINERO</div>
              <div class="estadistica-info">
                <div class="estadistica-valor">${{ datosPerfil.saldo_comercial.toFixed(2) }}</div>
                <div class="estadistica-label">Saldo Comercial</div>
              </div>
            </div>
          </div>

          <div class="perfil-seccion">
            <h4>📋 Publicaciones Activas ({{ datosPerfil.cantidad_publicaciones }})</h4>
            <div v-if="datosPerfil.publicaciones.length === 0" class="empty-state">
              No tienes publicaciones activas
            </div>
            <div v-else class="publicaciones-lista">
              <div v-for="pub in datosPerfil.publicaciones" :key="pub.id" class="publicacion-item">
                <div class="publicacion-tipo" :class="'publicacion-tipo--' + pub.tipo.toLowerCase()">
                  {{ pub.tipo === 'TALENTO' ? ' Talento' : ' Necesidad' }}
                </div>
                <div class="publicacion-info">
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
            <h4>⭐ Reseñas Recibidas ({{ datosPerfil?.cantidad_resenas || 0 }})</h4>
            <div v-if="!datosPerfil?.resenas_recibidas || datosPerfil.resenas_recibidas.length === 0" class="empty-state">
              No has recibido reseñas aún
            </div>
            <div v-else class="resenas-lista">
              <div v-for="resena in datosPerfil.resenas_recibidas" :key="resena.id" class="resena-item">
                <div class="resena-calificacion">
                  <span class="estrellas">{{ '⭐'.repeat(resena.estrellas) }}</span>
                  <span class="calificador">por @{{ resena.calificador?.username || 'usuario' }}</span>
                </div>
                <p class="resena-comentario">{{ resena.comentario }}</p>
              </div>
            </div>
          </div>

          <div class="perfil-seccion">
            <h4> Actividad de Trueques</h4>
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
import { inject, onMounted, ref } from 'vue'

const userController = inject('userController')
const datosPerfil = ref(null)
const cargando = ref(true)
const error = ref('')

const cargarPerfil = async () => {
  try {
    // Usar el patrón del proyecto - agregar el método al UserController
    const response = await userController.obtenerMiPerfil()
    datosPerfil.value = response
  } catch (err) {
    error.value = 'Error al cargar el perfil: ' + (err.message || 'Error desconocido')
  } finally {
    cargando.value = false
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

onMounted(cargarPerfil)
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

.perfil-datos-principales h3 {
  margin: 0 0 0.25rem 0;
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
</style>
