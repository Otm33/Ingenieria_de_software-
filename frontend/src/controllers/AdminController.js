import BaseController from './BaseController.js'
import AdminRepository from '../repositories/AdminRepository.js'
import { ref } from 'vue'

/**
 * AdminController - Controlador para HU1: Carga de usuarios autorizados
 * Maneja toda la lógica de negocio administrativa del frontend
 * con estado reactivo y validaciones
 */
export default class AdminController extends BaseController {
  constructor(adminRepository = null) {
    super()
    this.adminRepository = adminRepository || new AdminRepository()
    
    // Estado reactivo administrativo
    this.archivoSeleccionado = ref(null)
    this.resultadoCarga = ref(null)
  }

  /**
   * Selecciona un archivo CSV para carga
   * HU1: Carga de usuarios autorizados via CSV
   */
  seleccionarArchivo(event) {
    const file = event.target.files[0]
    
    // Limpiar estado anterior
    this.archivoSeleccionado.value = null
    this.resultadoCarga.value = null
    this.clearError()
    
    if (!file) {
      return
    }

    // Validar extensión del archivo
    if (!file.name.toLowerCase().endsWith('.csv')) {
      this.setError('Formato incorrecto. Solo se acepta .csv.')
      event.target.value = ''
      return
    }

    this.archivoSeleccionado.value = file
  }

  /**
   * Carga el archivo CSV de usuarios autorizados
   * HU1: Procesar lista de usuarios autorizados
   */
  async cargarUsuariosAutorizados(authController) {
    return this.execute(async () => {
      // Verificar que el usuario sea administrador
      if (!authController.haySesionActiva()) {
        throw new Error('Debes iniciar sesión para realizar esta acción.')
      }

      const usuario = authController.getUsuarioActual()
      if (!usuario?.esSuperusuario) {
        throw new Error('No tienes permisos de administrador.')
      }

      if (!this.archivoSeleccionado.value) {
        throw new Error('Debes seleccionar un archivo CSV antes de procesar.')
      }

      const resultado = await this.adminRepository.cargarUsuariosAutorizados(
        this.archivoSeleccionado.value
      )
      
      // Actualizar estado reactivo
      this.resultadoCarga.value = resultado
      
      // Limpiar selección de archivo
      this.archivoSeleccionado.value = null
      
      return resultado
    })
  }

  /**
   * Limpia el resultado de carga
   */
  limpiarResultado() {
    this.resultadoCarga.value = null
    this.clearError()
  }

  async cargarArchivoDirecto(archivo, authController) {
    if (!archivo) {
      throw new Error('Debes seleccionar un archivo CSV antes de procesar.')
    }
    if (!archivo.name.toLowerCase().endsWith('.csv')) {
      throw new Error('Formato incorrecto. Solo se acepta .csv.')
    }

    this.archivoSeleccionado.value = archivo
    return this.cargarUsuariosAutorizados(authController)
  }

  /**
   * Invalida toda la caché administrativa
   */
  invalidateAllCache() {
    this.adminRepository.invalidateAll()
  }

  /**
   * Verifica si hay un archivo seleccionado
   */
  hayArchivoSeleccionado() {
    return this.archivoSeleccionado.value !== null
  }

  /**
   * Retorna el nombre del archivo seleccionado
   */
  getNombreArchivo() {
    return this.archivoSeleccionado.value?.name || ''
  }

  /**
   * Retorna el tamaño del archivo seleccionado en KB
   */
  getTamanoArchivo() {
    if (!this.archivoSeleccionado.value) return 0
    return (this.archivoSeleccionado.value.size / 1024).toFixed(2)
  }
}
