import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import PublicacionApiService from '../services/api/PublicacionApiService.js'
import { CATEGORIAS } from '../data/catalogoServicios.js'

/**
 * CarteleraStore - Store de cartelera y publicaciones
 * Reemplaza a CarteleraController para manejo de estado reactivo de cartelera
 */
export const useCarteleraStore = defineStore('cartelera', () => {
  // Estado reactivo
  const publicaciones = ref([])
  const filtrosAplicados = reactive({
    categoria: '',
    urgencias: []
  })
  const estaEnModoPublicar = ref(false)
  const formularioPublicacion = reactive({
    tipo: 'TALENTO',
    titulo: '',
    descripcion: '',
    categoria: '',
    urgencia: 'NORMAL'
  })
  const misPublicaciones = ref([])
  const procesandoEstadoId = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // API Service
  const publicacionApiService = new PublicacionApiService()

  /**
   * Obtiene la cartelera con filtros aplicados
   */
  async function cargarCartelera(filtros = {}, forceRefresh = false) {
    loading.value = true
    error.value = null
    
    try {
      const publicacionesData = await publicacionApiService.obtenerCartelera(
        filtros,
        forceRefresh
      )
      
      // Actualizar estado reactivo
      publicaciones.value = publicacionesData
      filtrosAplicados.categoria = filtros.categoria || ''
      filtrosAplicados.urgencias = filtros.urgencias || []
      
      return publicacionesData
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Aplica los filtros actuales a la cartelera
   */
  async function aplicarFiltros() {
    const filtros = {
      categoria: filtrosAplicados.categoria || undefined,
      urgencias: filtrosAplicados.urgencias.length > 0 
        ? filtrosAplicados.urgencias 
        : undefined
    }
    
    return cargarCartelera(filtros, true)
  }

  /**
   * Restablece los filtros a valores por defecto
   */
  async function restablecerFiltros() {
    filtrosAplicados.categoria = ''
    filtrosAplicados.urgencias = []
    return cargarCartelera({}, true)
  }

  /**
   * Cambia al modo de publicación
   */
  function activarModoPublicar() {
    estaEnModoPublicar.value = true
    limpiarFormularioPublicacion()
  }

  /**
   * Cambia al modo de visualización
   */
  function desactivarModoPublicar() {
    estaEnModoPublicar.value = false
  }

  /**
   * Carga las publicaciones del usuario actual
   */
  async function cargarMisPublicaciones(forceRefresh = false) {
    loading.value = true
    error.value = null
    
    try {
      const publicacionesData = await publicacionApiService.obtenerMisPublicaciones(forceRefresh)
      
      // Actualizar estado reactivo
      misPublicaciones.value = publicacionesData
      
      return publicacionesData
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Crea una nueva publicación
   */
  async function crearPublicacion(authStore, formData = null) {
    loading.value = true
    error.value = null
    
    try {
      // Requerir autenticación
      authStore.requireAuth()
      
      // Usar formData proporcionado o formularioPublicacion por defecto
      const form = formData || formularioPublicacion
      
      // Validaciones frontend
      if (!form.categoria) {
        throw new Error('La categoría es requerida.')
      }

      if (!form.titulo) {
        throw new Error('El título es requerido.')
      }

      if (!form.descripcion?.trim()) {
        throw new Error('La descripción es requerida.')
      }

      if (form.descripcion.length < 10) {
        throw new Error('La descripción debe tener al menos 10 caracteres.')
      }

      // Validar categoría
      if (!CATEGORIAS.includes(form.categoria)) {
        throw new Error('La categoría seleccionada no es válida.')
      }

      // Validar urgencia para talentos
      if (form.tipo === 'TALENTO' && 
          formularioPublicacion.urgencia !== 'NORMAL') {
        throw new Error('Los talentos solo pueden tener urgencia Normal.')
      }

      const datos = {
        tipo: form.tipo,
        titulo: form.titulo,
        descripcion: form.descripcion,
        categoria: form.categoria,
        urgencia: form.urgencia
      }

      const publicacion = await publicacionApiService.crearPublicacion(datos)
      
      // Actualizar caché local
      misPublicaciones.value.unshift(publicacion)
      
      // Invalidar caché de cartelera
      publicacionApiService.invalidateCartelera()
      
      // Salir del modo de publicación
      desactivarModoPublicar()
      
      return publicacion
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Actualiza el estado de una publicación (pausar/reactivar)
   */
  async function actualizarEstadoPublicacion(publicacionId, estaActiva) {
    loading.value = true
    error.value = null
    procesandoEstadoId.value = publicacionId
    
    try {
      const publicacion = await publicacionApiService.actualizarEstadoPublicacion(
        publicacionId,
        estaActiva
      )
      
      // Actualizar estado local con nueva referencia para reactividad
      misPublicaciones.value = misPublicaciones.value.map(p => 
        p.id === publicacionId ? publicacion : p
      )
      
      // Invalidar caché
      publicacionApiService.invalidateCartelera()
      publicacionApiService.invalidateMisPublicaciones()
      
      return publicacion
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
      procesandoEstadoId.value = null
    }
  }

  /**
   * Pausa una publicación
   */
  async function pausarPublicacion(publicacionId) {
    return actualizarEstadoPublicacion(publicacionId, false)
  }

  /**
   * Reactiva una publicación
   */
  async function reactivarPublicacion(publicacionId) {
    return actualizarEstadoPublicacion(publicacionId, true)
  }

  /**
   * Limpia el formulario de publicación
   */
  function limpiarFormularioPublicacion() {
    formularioPublicacion.tipo = 'TALENTO'
    formularioPublicacion.titulo = ''
    formularioPublicacion.descripcion = ''
    formularioPublicacion.categoria = ''
    formularioPublicacion.urgencia = 'NORMAL'
  }

  /**
   * Retorna las categorías disponibles
   */
  function getCategorias() {
    return CATEGORIAS
  }

  /**
   * Retorna el número de publicaciones críticas
   */
  function getTotalCriticas() {
    return publicaciones.value.filter(p => p.esCritica()).length
  }

  /**
   * Retorna el número de talentos
   */
  function getTotalTalentos() {
    return publicaciones.value.filter(p => p.esTalento()).length
  }

  /**
   * Limpia el error
   */
  function clearError() {
    error.value = null
  }

  return {
    // Estado
    publicaciones,
    filtrosAplicados,
    estaEnModoPublicar,
    formularioPublicacion,
    misPublicaciones,
    procesandoEstadoId,
    loading,
    error,
    
    // Acciones
    cargarCartelera,
    aplicarFiltros,
    restablecerFiltros,
    activarModoPublicar,
    desactivarModoPublicar,
    cargarMisPublicaciones,
    crearPublicacion,
    actualizarEstadoPublicacion,
    pausarPublicacion,
    reactivarPublicacion,
    limpiarFormularioPublicacion,
    getCategorias,
    getTotalCriticas,
    getTotalTalentos,
    clearError
  }
})
