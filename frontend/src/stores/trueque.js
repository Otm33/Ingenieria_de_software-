import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import TruequeApiService from '../services/api/TruequeApiService.js'
import ResenaApiService from '../services/api/ResenaApiService.js'

/**
 * TruequeStore - Store de trueques y propuestas
 * Reemplaza a TruequeController para manejo de estado reactivo de trueques
 */
export const useTruequeStore = defineStore('trueque', () => {
  // Estado reactivo
  const matches = ref([])
  const mensajeMatches = ref('')
  const cantidadMatches = ref(0)
  const notificaciones = ref([])
  const cantidadNotificaciones = ref(0)
  const mostrarSelectorModo = ref(false)
  const modoPropuesta = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // API Services
  const truequeApiService = new TruequeApiService()
  const resenaApiService = new ResenaApiService()

  /**
   * Verifica coincidencias por título de publicación
   */
  async function verificarCoincidenciaPorTitulo(publicacionId) {
    loading.value = true
    error.value = null
    
    try {
      const resultado = await truequeApiService.verificarCoincidenciaPorTitulo(publicacionId)
      return resultado
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Obtiene los matches para el usuario
   */
  async function obtenerMatches(publicacionId = null, forceRefresh = false) {
    loading.value = true
    error.value = null
    
    try {
      const resultado = await truequeApiService.obtenerMatchesEnriquecidos(
        publicacionId,
        forceRefresh,
      )

      matches.value = resultado.matches
      mensajeMatches.value = resultado.mensaje
      cantidadMatches.value = resultado.cantidad

      return resultado
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Crea una propuesta de trueque
   */
  async function crearPropuesta(receptorId, publicacionEmisorId, publicacionReceptorId) {
    loading.value = true
    error.value = null
    
    try {
      if (!receptorId) {
        throw new Error('El receptor es requerido.')
      }

      const trueque = await truequeApiService.crearPropuesta(
        receptorId,
        publicacionEmisorId,
        publicacionReceptorId
      )
      
      // Invalidar caché de matches
      truequeApiService.invalidateMatches(publicacionEmisorId)
      truequeApiService.invalidateMatches()
      
      return trueque
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Responde a una propuesta de trueque
   */
  async function responderPropuesta(truequeId, accion) {
    loading.value = true
    error.value = null
    
    try {
      if (!['ACEPTAR', 'RECHAZAR'].includes(accion)) {
        throw new Error('La acción debe ser ACEPTAR o RECHAZAR.')
      }

      const resultado = await truequeApiService.responderPropuesta(truequeId, accion)
      
      // Invalidar caché
      truequeApiService.invalidateMisTrueques()
      resenaApiService.invalidateNotificaciones()
      
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
  async function finalizarTrueque(truequeId) {
    loading.value = true
    error.value = null
    
    try {
      const resultado = await truequeApiService.finalizarTrueque(truequeId)
      
      // Invalidar caché
      truequeApiService.invalidateMisTrueques()
      resenaApiService.invalidateNotificaciones()
      
      return resultado
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Carga las notificaciones del usuario
   */
  async function cargarNotificaciones(incluirLeidas = false, forceRefresh = false) {
    loading.value = true
    error.value = null
    
    try {
      const resultado = await resenaApiService.obtenerNotificaciones(
        incluirLeidas,
        forceRefresh
      )
      
      // Actualizar estado reactivo
      notificaciones.value = resultado.notificaciones
      cantidadNotificaciones.value = resultado.cantidad
      
      return resultado
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Marca una notificación como leída
   */
  async function marcarNotificacionLeida(notificacionId) {
    loading.value = true
    error.value = null
    
    try {
      await resenaApiService.marcarNotificacionLeida(notificacionId)
      
      // Actualizar estado local
      const notificacion = notificaciones.value.find(n => n.id === notificacionId)
      if (notificacion) {
        notificacion.estado = 'LEIDA'
        notificacion.leida_el = new Date().toISOString()
      }
      
      // Invalidar caché
      resenaApiService.invalidateNotificaciones()
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Marca todas las notificaciones de un trueque como leídas
   */
  async function marcarNotificacionesTruequeLeidas(truequeId) {
    loading.value = true
    error.value = null
    
    try {
      await resenaApiService.marcarNotificacionesTruequeLeidas(truequeId)
      
      // Actualizar estado local
      notificaciones.value = notificaciones.value.filter(
        n => n.trueque?.id !== truequeId || n.estado === 'LEIDA'
      )
      
      // Invalidar caché
      resenaApiService.invalidateNotificaciones()
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Abre el selector de modo de propuesta
   */
  function abrirSelectorModo() {
    mostrarSelectorModo.value = true
    modoPropuesta.value = null
  }

  /**
   * Cierra el selector de modo de propuesta
   */
  function cerrarSelectorModo() {
    mostrarSelectorModo.value = false
    modoPropuesta.value = null
  }

  /**
   * Elige el modo de propuesta
   */
  function elegirModoPropuesta(modo) {
    modoPropuesta.value = modo
    mostrarSelectorModo.value = false
  }

  async function validarCodigoTrueque(truequeId, codigo) {
    loading.value = true
    error.value = null
    
    try {
      const resultado = await truequeApiService.validarCodigo(truequeId, codigo)
      truequeApiService.invalidateMisTrueques()
      resenaApiService.invalidateNotificaciones()
      return resultado
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function obtenerMisTrueques(forceRefresh = false) {
    loading.value = true
    error.value = null
    
    try {
      return await truequeApiService.obtenerMisTrueques(forceRefresh)
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function responderPropuestaMultiple(truequeMultipleId, accion) {
    loading.value = true
    error.value = null
    
    try {
      const resultado = await truequeApiService.responderPropuestaMultiple(
        truequeMultipleId,
        accion,
      )
      resenaApiService.invalidateNotificaciones()
      return resultado
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function obtenerMisTruequesMultiples(forceRefresh = false) {
    loading.value = true
    error.value = null
    
    try {
      return await truequeApiService.obtenerMisTruequesMultiples(forceRefresh)
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function validarCodigoParMultiple(truequeMultipleId, par, codigo) {
    loading.value = true
    error.value = null
    
    try {
      return await truequeApiService.validarCodigoParMultiple(
        truequeMultipleId,
        par,
        codigo,
      )
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function registrarResenaMultiple(truequeMultipleId, calificadoId, estrellas, comentario) {
    loading.value = true
    error.value = null
    
    try {
      return await resenaApiService.registrarResenaMultiple(
        truequeMultipleId,
        calificadoId,
        estrellas,
        comentario,
      )
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Limpia el error
   */
  function clearError() {
    error.value = null
  }

  return {
    // Estado
    matches,
    mensajeMatches,
    cantidadMatches,
    notificaciones,
    cantidadNotificaciones,
    mostrarSelectorModo,
    modoPropuesta,
    loading,
    error,
    
    // Acciones
    verificarCoincidenciaPorTitulo,
    obtenerMatches,
    crearPropuesta,
    responderPropuesta,
    finalizarTrueque,
    cargarNotificaciones,
    marcarNotificacionLeida,
    marcarNotificacionesTruequeLeidas,
    abrirSelectorModo,
    cerrarSelectorModo,
    elegirModoPropuesta,
    validarCodigoTrueque,
    obtenerMisTrueques,
    responderPropuestaMultiple,
    obtenerMisTruequesMultiples,
    validarCodigoParMultiple,
    registrarResenaMultiple,
    clearError
  }
})
