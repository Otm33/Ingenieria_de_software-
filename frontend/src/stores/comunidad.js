import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import UsuarioApiService from '../services/api/UsuarioApiService.js'

/**
 * ComunidadStore - Store de comunidad y perfiles públicos
 * Reemplaza a ComunidadController para manejo de estado reactivo de comunidad
 */
export const useComunidadStore = defineStore('comunidad', () => {
  // Estado reactivo
  const miembros = ref([])
  const vistaActual = ref('directorio')
  const detallePerfil = ref(null)
  const miembroSeleccionado = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // API Service
  const usuarioApiService = new UsuarioApiService()

  /**
   * Carga la lista de miembros de la comunidad
   */
  async function cargarComunidad(forceRefresh = false) {
    loading.value = true
    error.value = null
    
    try {
      const comunidad = await usuarioApiService.obtenerComunidad(forceRefresh)
      
      // Actualizar estado reactivo
      miembros.value = comunidad.miembros || []
      vistaActual.value = 'directorio'
      
      return comunidad
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Carga el perfil público de un miembro específico
   */
  async function cargarPerfilUsuario(usuarioId, forceRefresh = false) {
    loading.value = true
    error.value = null
    
    try {
      const perfil = await usuarioApiService.obtenerPerfilUsuario(usuarioId, forceRefresh)
      
      // Actualizar estado reactivo
      detallePerfil.value = perfil
      vistaActual.value = 'detalle'
      miembroSeleccionado.value = perfil.usuario
      
      return perfil
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Cambia a la vista de detalle del miembro
   */
  function verDetalle(miembro) {
    miembroSeleccionado.value = miembro
    return cargarPerfilUsuario(miembro.usuario.id)
  }

  /**
   * Vuelve al directorio
   */
  function volverAlDirectorio() {
    vistaActual.value = 'directorio'
    detallePerfil.value = null
    miembroSeleccionado.value = null
  }

  /**
   * Retorna los talentos activos del perfil actual
   */
  function getTalentosActivos() {
    if (!detallePerfil.value) return []
    return (detallePerfil.value.publicaciones || [])
      .filter(p => p.tipo === 'TALENTO' && p.esta_activa)
  }

  /**
   * Retorna las necesidades activas del perfil actual
   */
  function getNecesidadesActivas() {
    if (!detallePerfil.value) return []
    return (detallePerfil.value.publicaciones || [])
      .filter(p => p.tipo === 'NECESIDAD' && p.esta_activa)
  }

  /**
   * Retorna las reseñas públicas del perfil actual
   */
  function getResenasPublicas() {
    if (!detallePerfil.value) return []
    return detallePerfil.value.resenas || []
  }

  /**
   * Retorna el número de miembros activos
   */
  function getTotalMiembrosActivos() {
    return miembros.value.filter(m => m.es_miembro_activo).length
  }

  /**
   * Verifica si se puede enviar una propuesta al miembro actual
   */
  function puedeEnviarPropuesta(authStore) {
    if (!authStore.haySesionActiva()) {
      return false
    }

    const usuarioActual = authStore.usuarioActual
    if (!usuarioActual) {
      return false
    }

    // No puede enviarse propuesta a sí mismo
    if (miembroSeleccionado.value?.id === usuarioActual.id) {
      return false
    }

    return true
  }

  /**
   * Invalida la caché de la comunidad
   */
  function invalidateComunidadCache() {
    usuarioApiService.invalidateComunidad()
  }

  /**
   * Invalida la caché de perfiles
   */
  function invalidatePerfilCache(usuarioId) {
    if (usuarioId) {
      usuarioApiService.invalidatePerfil(usuarioId)
    } else {
      usuarioApiService.invalidateAll()
    }
  }

  /**
   * Invalida toda la caché de usuarios
   */
  function invalidateAllCache() {
    usuarioApiService.invalidateAll()
  }

  /**
   * Retorna las iniciales de un nombre
   */
  function getInitials(nombreReal, username) {
    if (nombreReal) {
      return nombreReal
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    }
    return username ? username.slice(0, 2).toUpperCase() : '??'
  }

  /**
   * Retorna un color de avatar basado en el username
   */
  function getAvatarColor(username) {
    const colors = [
      '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
      '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    if (!username) return colors[0]
    const index = username
      .split('')
      .reduce((acc, char) => acc + char.charCodeAt(0), 0)
    return colors[index % colors.length]
  }

  /**
   * Formatea el promedio de estrellas
   */
  function formatearEstrellas(promedio) {
    return (promedio || 5.0).toFixed(1)
  }

  /**
   * Retorna el nombre del calificador de una reseña
   */
  function nombreCalificador(resena) {
    return resena.calificador?.username || 'Usuario'
  }

  /**
   * Limpia el error
   */
  function clearError() {
    error.value = null
  }

  return {
    // Estado
    miembros,
    vistaActual,
    detallePerfil,
    miembroSeleccionado,
    loading,
    error,
    
    // Acciones
    cargarComunidad,
    cargarPerfilUsuario,
    verDetalle,
    volverAlDirectorio,
    getTalentosActivos,
    getNecesidadesActivas,
    getResenasPublicas,
    getTotalMiembrosActivos,
    puedeEnviarPropuesta,
    invalidateComunidadCache,
    invalidatePerfilCache,
    invalidateAllCache,
    getInitials,
    getAvatarColor,
    formatearEstrellas,
    nombreCalificador,
    clearError
  }
})
