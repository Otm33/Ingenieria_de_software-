import { defineStore } from 'pinia'
import { ref } from 'vue'
import AuthApiService from '../services/api/AuthApiService.js'

/**
 * AuthStore - Store de autenticación
 * Reemplaza a AuthController para manejo de estado reactivo de autenticación
 */
export const useAuthStore = defineStore('auth', () => {
  // Estado reactivo
  const usuarioActual = ref(null)
  const estaAutenticado = ref(false)
  const loading = ref(false)
  const error = ref(null)

  // API Service
  const authApiService = new AuthApiService()

  /**
   * Valida si un email está autorizado para registro
   */
  async function validarEmail(email, esComercio = false) {
    loading.value = true
    error.value = null
    
    try {
      if (!email || !email.trim()) {
        throw new Error('El correo electrónico es requerido.')
      }

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(email)) {
        throw new Error('El formato del correo electrónico no es válido.')
      }

      return await authApiService.validarEmail(email, esComercio)
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Registra un nuevo usuario
   */
  async function registrarUsuario(formulario) {
    loading.value = true
    error.value = null
    
    try {
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

      const usuario = await authApiService.registrarUsuario(formulario)
      
      // Actualizar estado reactivo
      usuarioActual.value = usuario
      estaAutenticado.value = true
      
      return usuario
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Obtiene la sesión actual del usuario
   */
  async function obtenerSesionActual(forceRefresh = false) {
    loading.value = true
    error.value = null
    
    try {
      const usuario = await authApiService.obtenerSesionActual(forceRefresh)
      
      // Actualizar estado reactivo
      usuarioActual.value = usuario
      estaAutenticado.value = usuario !== null
      
      return usuario
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Inicia sesión
   */
  async function iniciarSesion(credenciales) {
    loading.value = true
    error.value = null
    
    try {
      // Validaciones frontend
      if (!credenciales.username?.trim()) {
        throw new Error('El nombre de usuario es requerido.')
      }

      if (!credenciales.password) {
        throw new Error('La contraseña es requerida.')
      }

      const usuario = await authApiService.iniciarSesion(credenciales)
      
      // Actualizar estado reactivo
      usuarioActual.value = usuario
      estaAutenticado.value = true
      
      return usuario
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Cierra sesión
   */
  async function cerrarSesion() {
    loading.value = true
    error.value = null
    
    try {
      await authApiService.cerrarSesion()
      
      // Limpiar estado reactivo
      usuarioActual.value = null
      estaAutenticado.value = false
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Verifica si hay una sesión activa
   */
  function haySesionActiva() {
    return estaAutenticado.value
  }

  /**
   * Requiere autenticación, lanza error si no hay sesión
   */
  function requireAuth() {
    if (!haySesionActiva()) {
      throw new Error('Debes iniciar sesión para realizar esta acción.')
    }
    return usuarioActual.value
  }

  /**
   * Limpia el error
   */
  function clearError() {
    error.value = null
  }

  return {
    // Estado
    usuarioActual,
    estaAutenticado,
    loading,
    error,
    
    // Acciones
    validarEmail,
    registrarUsuario,
    obtenerSesionActual,
    iniciarSesion,
    cerrarSesion,
    haySesionActiva,
    requireAuth,
    clearError
  }
})
