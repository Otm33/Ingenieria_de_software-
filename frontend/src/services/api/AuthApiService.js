import ApiClient, { sharedApiClient } from './ApiClient.js'

/**
 * AuthRepository - Repositorio para operaciones de autenticación
 * Usa caché en memoria para sesión actual y reduce llamadas API
 */
export default class AuthRepository {
  constructor(apiClient = null) {
    this.apiClient = apiClient || sharedApiClient
    // La sesión actual se cachea por más tiempo (15 minutos)
    this.sessionCacheKey = 'session:current'
  }

  /**
   * Valida si un email está autorizado para registro
   */
  async validarEmail(email, esComercio = false) {
    return this.apiClient.post('registro/validar-email/', {
      email: email?.trim(),
      es_comercio: Boolean(esComercio),
    })
  }

  /**
   * Registra un nuevo usuario
   */
  async registrarUsuario(formulario) {
    return this.apiClient.post('registro/', formulario)
  }

  /**
   * Obtiene la sesión actual (con caché)
   */
  async obtenerSesionActual(forceRefresh = false) {
    const data = await this.apiClient.get(
      'sesion/',
      {},
      {
        enabled: true,
        key: this.sessionCacheKey,
        forceRefresh,
      }
    )
    
    return data.autenticado ? data.usuario : null
  }

  /**
   * Inicia sesión
   */
  async iniciarSesion(credenciales) {
    const data = await this.apiClient.post('login/', credenciales)
    
    // Invalidar caché de sesión después de login
    this.apiClient.invalidate(this.sessionCacheKey)

    return data.usuario
  }

  /**
   * Cierra sesión
   */
  async cerrarSesion() {
    await this.apiClient.post('logout/', {})
    
    // Invalidar toda la caché al cerrar sesión
    this.apiClient.invalidateAll()
  }

  /**
   * Invalida la caché de sesión
   */
  invalidateSessionCache() {
    this.apiClient.invalidate(this.sessionCacheKey)
  }
}
