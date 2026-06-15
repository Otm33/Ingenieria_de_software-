import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import UsuarioApiService from '../services/api/UsuarioApiService.js'
import PublicacionApiService from '../services/api/PublicacionApiService.js'
import TruequeApiService from '../services/api/TruequeApiService.js'
import ResenaApiService from '../services/api/ResenaApiService.js'

/**
 * PerfilStore - Store de perfil del usuario
 * Reemplaza a PerfilController para manejo de estado reactivo del perfil
 */
export const usePerfilStore = defineStore('perfil', () => {
  // Estado reactivo
  const datosPerfil = ref(null)
  const publicacionesActivas = ref([])
  const publicacionesPausadas = ref([])
  const misTrueques = ref([])
  const procesandoTruequeId = ref(null)
  const feedbackTrueque = reactive({})
  const feedbackTruequeOk = reactive({})
  const loading = ref(false)
  const error = ref(null)

  // API Services
  const usuarioApiService = new UsuarioApiService()
  const publicacionApiService = new PublicacionApiService()
  const truequeApiService = new TruequeApiService()
  const resenaApiService = new ResenaApiService()

  /**
   * Carga el perfil del usuario actual
   */
  async function cargarMiPerfil(forceRefresh = false) {
    loading.value = true
    error.value = null
    
    try {
      const perfil = await usuarioApiService.obtenerMiPerfil(forceRefresh)
      
      // Actualizar estado reactivo
      datosPerfil.value = perfil
      
      // Separar publicaciones por estado
      const publicaciones = perfil.publicaciones || []
      publicacionesActivas.value = publicaciones.filter(p => p.esta_activa)
      publicacionesPausadas.value = publicaciones.filter(p => !p.esta_activa)
      
      return perfil
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Carga los trueques del usuario actual
   */
  async function cargarMisTrueques(forceRefresh = false) {
    loading.value = true
    error.value = null
    
    try {
      const resultado = await truequeApiService.obtenerMisTrueques(forceRefresh)
      misTrueques.value = resultado.trueques
      return resultado
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Finaliza un trueque
   */
  async function finalizarTrueque(truequeId, authStore) {
    loading.value = true
    error.value = null
    
    try {
      if (authStore) {
        authStore.requireAuth()
      }
      
      procesandoTruequeId.value = truequeId
      feedbackTrueque[truequeId] = null
      
      try {
        const resultado = await truequeApiService.finalizarTrueque(truequeId)
        
        // Actualizar estado local
        const trueque = misTrueques.value.find(t => t.id === truequeId)
        if (trueque) {
          trueque.estado = 'FINALIZADO'
          trueque.emisor_confirmado = true
          trueque.receptor_confirmado = true
        }
        
        feedbackTrueque[truequeId] = resultado.mensaje
        feedbackTruequeOk[truequeId] = true
        
        // Invalidar caché
        truequeApiService.invalidateMisTrueques()
        
        return resultado
      } catch (err) {
        feedbackTrueque[truequeId] = err.message
        feedbackTruequeOk[truequeId] = false
        throw err
      } finally {
        procesandoTruequeId.value = null
      }
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Retorna las iniciales del usuario
   */
  function getInitials() {
    if (!datosPerfil.value?.usuario) return '??'
    const usuario = datosPerfil.value.usuario
    if (usuario.nombre_real) {
      return usuario.nombre_real
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    }
    return usuario.username.slice(0, 2).toUpperCase()
  }

  /**
   * Retorna un color de avatar
   */
  function getAvatarColor() {
    if (!datosPerfil.value?.usuario) return '#FF6B6B'
    const username = datosPerfil.value.usuario.username
    const colors = [
      '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
      '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    const index = username
      .split('')
      .reduce((acc, char) => acc + char.charCodeAt(0), 0)
    return colors[index % colors.length]
  }

  /**
   * Verifica si es miembro activo
   */
  function esMiembroActivo() {
    return datosPerfil.value?.es_miembro_activo || false
  }

  /**
   * Retorna el promedio de estrellas
   */
  function getPromedioEstrellas() {
    return datosPerfil.value?.usuario?.promedio_estrellas || 5.0
  }

  /**
   * Retorna el número de reseñas
   */
  function getCantidadResenas() {
    return (datosPerfil.value?.resenas_recibidas || []).length
  }

  /**
   * Retorna el nombre del calificador de una reseña
   */
  function nombreCalificador(resena) {
    return resena.calificador?.username || 'Usuario'
  }

  /**
   * Limpia el feedback de trueques
   */
  function limpiarFeedbackTrueque(truequeId) {
    delete feedbackTrueque[truequeId]
    delete feedbackTruequeOk[truequeId]
  }

  /**
   * Invalida toda la caché del perfil
   */
  function invalidateAllCache() {
    usuarioApiService.invalidateMiPerfil()
    publicacionApiService.invalidateMisPublicaciones()
    truequeApiService.invalidateMisTrueques()
  }

  /**
   * Limpia el error
   */
  function clearError() {
    error.value = null
  }

  return {
    // Estado
    datosPerfil,
    publicacionesActivas,
    publicacionesPausadas,
    misTrueques,
    procesandoTruequeId,
    feedbackTrueque,
    feedbackTruequeOk,
    loading,
    error,
    
    // Acciones
    cargarMiPerfil,
    cargarMisTrueques,
    finalizarTrueque,
    getInitials,
    getAvatarColor,
    esMiembroActivo,
    getPromedioEstrellas,
    getCantidadResenas,
    nombreCalificador,
    limpiarFeedbackTrueque,
    invalidateAllCache,
    clearError
  }
})
