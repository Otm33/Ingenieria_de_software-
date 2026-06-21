import ApiClient, { sharedApiClient } from './ApiClient.js'

/**
 * UsuarioRepository - Repositorio para operaciones de usuarios
 * Usa caché en memoria para perfiles y comunidad
 */
export default class UsuarioRepository {
  constructor(apiClient = null) {
    this.apiClient = apiClient || sharedApiClient
    
    // Claves de caché
    this.cacheKeys = {
      miPerfil: 'perfil:mi',
      perfil: (id) => `perfil:${id}`,
      comunidad: 'comunidad',
    }
  }

  /**
   * Obtiene el perfil del usuario actual (con caché)
   */
  async obtenerMiPerfil(forceRefresh = false) {
    const data = await this.apiClient.get(
      'mi-perfil/',
      {},
      {
        enabled: true,
        key: this.cacheKeys.miPerfil,
        forceRefresh,
      }
    )
    
    return data
  }

  /**
   * Obtiene el perfil de un usuario específico (con caché)
   */
  async obtenerPerfilUsuario(id, forceRefresh = false) {
    const data = await this.apiClient.get(
      `perfil/${id}/`,
      {},
      {
        enabled: true,
        key: this.cacheKeys.perfil(id),
        forceRefresh,
      }
    )
    
    return data
  }

  /**
   * Obtiene la lista de miembros de la comunidad (con caché)
   */
  async obtenerComunidad(forceRefresh = false) {
    const data = await this.apiClient.get(
      'comunidad/',
      {},
      {
        enabled: true,
        key: this.cacheKeys.comunidad,
        forceRefresh,
      }
    )
    
    return data
  }

  /**
   * Invalida la caché del perfil del usuario actual
   */
  invalidateMiPerfil() {
    this.apiClient.invalidate(this.cacheKeys.miPerfil)
  }

  /**
   * Invalida la caché de un perfil específico
   */
  invalidatePerfil(id) {
    this.apiClient.invalidate(this.cacheKeys.perfil(id))
  }

  /**
   * Invalida la caché de la comunidad
   */
  invalidateComunidad() {
    this.apiClient.invalidate(this.cacheKeys.comunidad)
  }

  /**
   * Invalida toda la caché de usuarios
   */
  invalidateAll() {
    this.apiClient.invalidateAll()
  }
}
