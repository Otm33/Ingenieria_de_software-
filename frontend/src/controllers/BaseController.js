import { ref } from 'vue'

/**
 * BaseController - Clase base para todos los controladores del frontend
 * Proporciona manejo de errores, estado de carga y estado reactivo común
 * siguiendo el patrón MVC estricto con almacenamiento en memoria
 */
export default class BaseController {
  constructor() {
    // Estado reactivo compartido por todos los controladores
    this.loading = ref(false)
    this.error = ref(null)
    this.data = ref(null)
  }

  /**
   * Ejecuta una operación asíncrona con manejo automático de errores y estado de carga
   * @param {Function} operation - La operación asíncrona a ejecutar
   * @returns {Promise} - El resultado de la operación
   */
  async execute(operation) {
    this.loading.value = true
    this.error.value = null
    
    try {
      const result = await operation()
      this.data.value = result
      return result
    } catch (err) {
      this.error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      this.loading.value = false
    }
  }

  /**
   * Limpia el estado de error
   */
  clearError() {
    this.error.value = null
  }

  /**
   * Limpia todo el estado
   */
  clearState() {
    this.loading.value = false
    this.error.value = null
    this.data.value = null
  }

  /**
   * Valida que se tenga una sesión activa
   * @param {Object} usuario - El objeto de usuario actual
   * @throws {Error} - Si no hay sesión activa
   */
  requireAuth(usuario) {
    if (!usuario) {
      throw new Error('Debes iniciar sesión para realizar esta acción.')
    }
  }

  /**
   * Establece manualmente el estado de carga
   * @param {boolean} isLoading - Estado de carga
   */
  setLoading(isLoading) {
    this.loading.value = isLoading
  }

  /**
   * Establece manualmente un error
   * @param {string} errorMessage - Mensaje de error
   */
  setError(errorMessage) {
    this.error.value = errorMessage
  }

  /**
   * Establece manualmente los datos
   * @param {*} data - Datos a establecer
   */
  setData(data) {
    this.data.value = data
  }
}
