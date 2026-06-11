import ApiClient from './ApiClient.js'

/**
 * TruequeRepository - Repositorio para operaciones de trueques
 * Usa caché en memoria para matches y trueques del usuario
 */
export default class TruequeRepository {
  constructor(apiClient = null) {
    this.apiClient = apiClient || new ApiClient()
    
    // Claves de caché
    this.cacheKeys = {
      matches: (publicacionId) => `matches:${publicacionId || 'all'}`,
      misTrueques: 'trueques:mis',
      notificaciones: 'notificaciones',
    }
  }

  /**
   * Verifica coincidencias por título de publicación
   */
  async verificarCoincidenciaPorTitulo(publicacionId) {
    const params = new URLSearchParams()
    params.set('publicacion_id', publicacionId)
    params.set('accion', 'verificar_coincidencia')

    const endpoint = `matchmaking/?${params.toString()}`
    return this.apiClient.get(endpoint)
  }

  /**
   * Obtiene matches (con caché)
   */
  async obtenerMatches(publicacionId = null, forceRefresh = false) {
    const params = new URLSearchParams()
    if (publicacionId) {
      params.set('publicacion_id', publicacionId)
    }

    const endpoint = params.toString() ? `matchmaking/?${params.toString()}` : 'matchmaking/'
    const data = await this.apiClient.get(
      endpoint,
      {},
      {
        enabled: true,
        key: this.cacheKeys.matches(publicacionId),
        forceRefresh,
      }
    )
    
    return {
      matches: (data.matches || []).map((match) => ({
        usuario: match.usuario,
        talentosCoincidentes: match.talentos_coincidentes || [],
        necesidadesCoincidentes: match.necesidades_coincidentes || [],
        publicacionesSugeridas: match.publicaciones_sugeridas || [],
      })),
      mensaje: data.mensaje || '',
      cantidad: data.cantidad ?? 0,
    }
  }

  /**
   * Crea una propuesta de trueque
   */
  async crearPropuesta(receptorId, publicacionEmisorId, publicacionReceptorId) {
    const result = await this.apiClient.post('trueques/propuestas/crear/', {
      receptor_id: receptorId,
      publicacion_emisor_id: publicacionEmisorId,
      publicacion_receptor_id: publicacionReceptorId,
    })
    
    // Invalidar caché de matches
    this.apiClient.invalidate(this.cacheKeys.matches(null))
    this.apiClient.invalidate(this.cacheKeys.matches(publicacionEmisorId))
    
    return result
  }

  /**
   * Responde a una propuesta de trueque
   */
  async responderPropuesta(truequeId, accion) {
    const result = await this.apiClient.post(
      `trueques/${truequeId}/responder/`,
      { accion }
    )
    
    // Invalidar caché de trueques y notificaciones
    this.apiClient.invalidate(this.cacheKeys.misTrueques)
    this.apiClient.invalidate(this.cacheKeys.notificaciones)
    
    return result
  }

  /**
   * Finaliza un trueque
   */
  async finalizarTrueque(truequeId) {
    const result = await this.apiClient.post(`trueques/${truequeId}/finalizar/`)
    
    // Invalidar caché de trueques y notificaciones
    this.apiClient.invalidate(this.cacheKeys.misTrueques)
    this.apiClient.invalidate(this.cacheKeys.notificaciones)
    
    return result
  }

  /**
   * Obtiene los trueques del usuario actual (con caché)
   */
  async obtenerMisTrueques(forceRefresh = false) {
    const data = await this.apiClient.get(
      'mis-trueques/',
      {},
      {
        enabled: true,
        key: this.cacheKeys.misTrueques,
        forceRefresh,
      }
    )
    
    return data.trueques || []
  }

  /**
   * Invalida la caché de matches
   */
  invalidateMatches(publicacionId = null) {
    this.apiClient.invalidate(this.cacheKeys.matches(publicacionId))
  }

  /**
   * Invalida la caché de mis trueques
   */
  invalidateMisTrueques() {
    this.apiClient.invalidate(this.cacheKeys.misTrueques)
  }

  /**
   * Invalida toda la caché de trueques
   */
  invalidateAll() {
    this.apiClient.invalidateAll()
  }
}
