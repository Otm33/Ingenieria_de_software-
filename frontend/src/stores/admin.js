import { defineStore } from 'pinia'
import { ref } from 'vue'
import AdminApiService from '../services/api/AdminApiService.js'

/**
 * AdminStore - Store administrativo
 * Reemplaza a AdminController para manejo de estado reactivo administrativo
 */
export const useAdminStore = defineStore('admin', () => {
  // Estado reactivo
  const archivoSeleccionado = ref(null)
  const resultadoCarga = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // API Service
  const adminApiService = new AdminApiService()

  /**
   * Selecciona un archivo CSV para carga
   */
  function seleccionarArchivo(event) {
    const file = event.target.files[0]
    
    // Limpiar estado anterior
    archivoSeleccionado.value = null
    resultadoCarga.value = null
    error.value = null
    
    if (!file) {
      return
    }

    // Validar extensión del archivo
    if (!file.name.toLowerCase().endsWith('.csv')) {
      error.value = 'Formato incorrecto. Solo se acepta .csv.'
      event.target.value = ''
      return
    }

    archivoSeleccionado.value = file
  }

  /**
   * Carga el archivo CSV de usuarios autorizados
   */
  async function cargarUsuariosAutorizados(authStore) {
    loading.value = true
    error.value = null
    
    try {
      // Verificar que el usuario sea administrador
      if (!authStore.haySesionActiva()) {
        throw new Error('Debes iniciar sesión para realizar esta acción.')
      }

      const usuario = authStore.usuarioActual
      if (!usuario?.esSuperusuario) {
        throw new Error('No tienes permisos de administrador.')
      }

      if (!archivoSeleccionado.value) {
        throw new Error('Debes seleccionar un archivo CSV antes de procesar.')
      }

      const resultado = await adminApiService.cargarUsuariosAutorizados(
        archivoSeleccionado.value
      )
      
      // Actualizar estado reactivo
      resultadoCarga.value = resultado
      
      // Limpiar selección de archivo
      archivoSeleccionado.value = null
      
      return resultado
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Limpia el resultado de carga
   */
  function limpiarResultado() {
    resultadoCarga.value = null
    error.value = null
  }

  async function cargarArchivoDirecto(archivo, authStore) {
    if (!archivo) {
      throw new Error('Debes seleccionar un archivo CSV antes de procesar.')
    }
    if (!archivo.name.toLowerCase().endsWith('.csv')) {
      throw new Error('Formato incorrecto. Solo se acepta .csv.')
    }

    archivoSeleccionado.value = archivo
    return cargarUsuariosAutorizados(authStore)
  }

  /**
   * Invalida toda la caché administrativa
   */
  function invalidateAllCache() {
    adminApiService.invalidateAll()
  }

  /**
   * Verifica si hay un archivo seleccionado
   */
  function hayArchivoSeleccionado() {
    return archivoSeleccionado.value !== null
  }

  /**
   * Retorna el nombre del archivo seleccionado
   */
  function getNombreArchivo() {
    return archivoSeleccionado.value?.name || ''
  }

  /**
   * Retorna el tamaño del archivo seleccionado en KB
   */
  function getTamanoArchivo() {
    if (!archivoSeleccionado.value) return 0
    return (archivoSeleccionado.value.size / 1024).toFixed(2)
  }

  /**
   * Limpia el error
   */
  function clearError() {
    error.value = null
  }

  return {
    // Estado
    archivoSeleccionado,
    resultadoCarga,
    loading,
    error,
    
    // Acciones
    seleccionarArchivo,
    cargarUsuariosAutorizados,
    limpiarResultado,
    cargarArchivoDirecto,
    invalidateAllCache,
    hayArchivoSeleccionado,
    getNombreArchivo,
    getTamanoArchivo,
    clearError
  }
})
