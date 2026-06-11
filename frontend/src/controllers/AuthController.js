import BaseController from './BaseController.js'
import AuthRepository from '../repositories/AuthRepository.js'
import { ref } from 'vue'

/**
 * AuthController - Controlador para HU2: Autenticación y registro
 * Maneja toda la lógica de negocio de autenticación del frontend
 * con estado reactivo y validaciones
 */
export default class AuthController extends BaseController {
  constructor(authRepository = null) {
    super()
    this.authRepository = authRepository || new AuthRepository()
    
    // Estado reactivo específico de autenticación
    this.usuarioActual = ref(null)
    this.estaAutenticado = ref(false)
  }

  /**
   * Valida si un email está autorizado para registro
   * HU2: Validación antes del registro
   */
  async validarEmail(email, esComercio = false) {
    return this.execute(async () => {
      if (!email || !email.trim()) {
        throw new Error('El correo electrónico es requerido.')
      }

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(email)) {
        throw new Error('El formato del correo electrónico no es válido.')
      }

      return await this.authRepository.validarEmail(email, esComercio)
    })
  }

  /**
   * Registra un nuevo usuario
   * HU2: Registro de usuarios y comercios
   */
  async registrarUsuario(formulario) {
    return this.execute(async () => {
      // Validaciones frontend
      if (!formulario.nombre_real?.trim()) {
        throw new Error('El nombre real es requerido.')
      }

      if (!formulario.email?.trim()) {
        throw new Error('El correo electrónico es requerido.')
      }

      if (!formulario.username?.trim()) {
        throw new Error('El nombre de usuario es requerido.')
      }

      if (!formulario.password || formulario.password.length < 8) {
        throw new Error('La contraseña debe tener al menos 8 caracteres.')
      }

      if (formulario.password !== formulario.password_confirm) {
        throw new Error('Las contraseñas no coinciden.')
      }

      const usuario = await this.authRepository.registrarUsuario(formulario)
      
      // Actualizar estado reactivo
      this.usuarioActual.value = usuario
      this.estaAutenticado.value = true
      
      return usuario
    })
  }

  /**
   * Obtiene la sesión actual del usuario
   * HU2: Verificar sesión al cargar la aplicación
   */
  async obtenerSesionActual(forceRefresh = false) {
    return this.execute(async () => {
      const usuario = await this.authRepository.obtenerSesionActual(forceRefresh)
      
      // Actualizar estado reactivo
      this.usuarioActual.value = usuario
      this.estaAutenticado.value = usuario !== null
      
      return usuario
    })
  }

  /**
   * Inicia sesión
   * HU2: Login de usuarios
   */
  async iniciarSesion(credenciales) {
    return this.execute(async () => {
      // Validaciones frontend
      if (!credenciales.username?.trim()) {
        throw new Error('El nombre de usuario es requerido.')
      }

      if (!credenciales.password) {
        throw new Error('La contraseña es requerida.')
      }

      const usuario = await this.authRepository.iniciarSesion(credenciales)
      
      // Actualizar estado reactivo
      this.usuarioActual.value = usuario
      this.estaAutenticado.value = true
      
      return usuario
    })
  }

  /**
   * Cierra sesión
   * HU2: Logout de usuarios
   */
  async cerrarSesion() {
    return this.execute(async () => {
      await this.authRepository.cerrarSesion()
      
      // Limpiar estado reactivo
      this.usuarioActual.value = null
      this.estaAutenticado.value = false
      this.clearState()
    })
  }

  /**
   * Verifica si hay una sesión activa
   */
  haySesionActiva() {
    return this.estaAutenticado.value
  }

  /**
   * Obtiene el usuario actual
   */
  getUsuarioActual() {
    return this.usuarioActual.value
  }

  /**
   * Requiere autenticación, lanza error si no hay sesión
   */
  requireAuth() {
    if (!this.haySesionActiva()) {
      throw new Error('Debes iniciar sesión para realizar esta acción.')
    }
    return this.usuarioActual.value
  }

  /**
   * Limpia el estado de autenticación
   */
  clearAuthState() {
    this.usuarioActual.value = null
    this.estaAutenticado.value = false
  }
}
