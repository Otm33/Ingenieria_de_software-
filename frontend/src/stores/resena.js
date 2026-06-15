import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import ResenaApiService from '../services/api/ResenaApiService.js'

/**
 * ResenaStore - Store de reseñas
 * Reemplaza a ResenaController para manejo de estado reactivo de reseñas
 */
export const useResenaStore = defineStore('resena', () => {
  // Estado reactivo
  const formularioResena = reactive({
    truequeId: null,
    estrellas: 5,
    comentario: ''
  })
  const mostrarModalResena = ref(false)
  const truequeSeleccionado = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // API Service
  const resenaApiService = new ResenaApiService()

  /**
   * Abre el modal de reseña para un trueque específico
   */
  function abrirResena(trueque) {
    truequeSeleccionado.value = trueque
    formularioResena.truequeId = trueque.id
    formularioResena.estrellas = 5
    formularioResena.comentario = ''
    mostrarModalResena.value = true
  }

  /**
   * Cierra el modal de reseña
   */
  function cerrarResena() {
    mostrarModalResena.value = false
    truequeSeleccionado.value = null
    limpiarFormulario()
  }

  /**
   * Registra una reseña
   */
  async function registrarResena(authStore) {
    loading.value = true
    error.value = null
    
    try {
      authStore.requireAuth()
      
      // Validaciones frontend
      if (!formularioResena.truequeId) {
        throw new Error('El trueque es requerido.')
      }

      if (!formularioResena.estrellas || formularioResena.estrellas < 1 || formularioResena.estrellas > 5) {
        throw new Error('La calificación debe estar entre 1 y 5 estrellas.')
      }

      if (!formularioResena.comentario?.trim()) {
        throw new Error('El comentario es requerido.')
      }

      if (formularioResena.comentario.length < 10) {
        throw new Error('El comentario debe tener al menos 10 caracteres.')
      }

      if (formularioResena.comentario.length > 500) {
        throw new Error('El comentario no puede exceder 500 caracteres.')
      }

      const resultado = await resenaApiService.registrarResena(
        formularioResena.truequeId,
        formularioResena.estrellas,
        formularioResena.comentario
      )
      
      // Invalidar caché
      resenaApiService.invalidateNotificaciones()
      
      // Cerrar modal y limpiar formulario
      cerrarResena()
      
      return resultado
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Actualiza el número de estrellas en el formulario
   */
  function actualizarEstrellas(estrellas) {
    formularioResena.estrellas = estrellas
  }

  /**
   * Actualiza el comentario en el formulario
   */
  function actualizarComentario(comentario) {
    formularioResena.comentario = comentario
  }

  /**
   * Limpia el formulario de reseña
   */
  function limpiarFormulario() {
    formularioResena.truequeId = null
    formularioResena.estrellas = 5
    formularioResena.comentario = ''
  }

  /**
   * Verifica si el formulario es válido
   */
  function formularioValido() {
    return (
      formularioResena.truequeId &&
      formularioResena.estrellas >= 1 &&
      formularioResena.estrellas <= 5 &&
      formularioResena.comentario?.trim().length >= 10 &&
      formularioResena.comentario.length <= 500
    )
  }

  /**
   * Retorna el número de caracteres del comentario
   */
  function getLongitudComentario() {
    return formularioResena.comentario?.length || 0
  }

  /**
   * Retorna el mensaje de longitud restante
   */
  function getMensajeLongitud() {
    const longitud = getLongitudComentario()
    return `${longitud}/500 caracteres`
  }

  async function registrarResenaDirecta(truequeId, estrellas, comentario) {
    loading.value = true
    error.value = null
    
    try {
      if (!truequeId) {
        throw new Error('El trueque es requerido.')
      }
      if (!estrellas || estrellas < 1 || estrellas > 5) {
        throw new Error('La calificación debe estar entre 1 y 5 estrellas.')
      }
      if (!comentario?.trim()) {
        throw new Error('El comentario es requerido.')
      }
      if (comentario.length < 10) {
        throw new Error('El comentario debe tener al menos 10 caracteres.')
      }
      if (comentario.length > 500) {
        throw new Error('El comentario no puede exceder 500 caracteres.')
      }

      return await resenaApiService.registrarResena(truequeId, estrellas, comentario)
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Invalida toda la caché de reseñas
   */
  function invalidateAllCache() {
    resenaApiService.invalidateAll()
  }

  /**
   * Limpia el error
   */
  function clearError() {
    error.value = null
  }

  return {
    // Estado
    formularioResena,
    mostrarModalResena,
    truequeSeleccionado,
    loading,
    error,
    
    // Acciones
    abrirResena,
    cerrarResena,
    registrarResena,
    actualizarEstrellas,
    actualizarComentario,
    limpiarFormulario,
    formularioValido,
    getLongitudComentario,
    getMensajeLongitud,
    registrarResenaDirecta,
    invalidateAllCache,
    clearError
  }
})
