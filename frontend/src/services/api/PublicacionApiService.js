import ApiClient from './ApiClient.js'
import Publicacion from '../../models/Publicacion.js'

/**
 * PublicacionRepository - Repositorio para operaciones de publicaciones
 * Usa caché en memoria para cartelera y publicaciones del usuario
 */
export default class PublicacionRepository {
  constructor(apiClient = null) {
    this.apiClient = apiClient || new ApiClient()
    
    // Claves de caché
    this.cacheKeys = {
      cartelera: (filtros) => `cartelera:${JSON.stringify(filtros)}`,
      misPublicaciones: 'publicaciones:mis',
      publicacion: (id) => `publicacion:${id}`,
    }
  }

  /**
   * Obtiene la cartelera con filtros (con caché)
   */
  async obtenerCartelera(filtros = {}, forceRefresh = false) {
    const params = new URLSearchParams()
    if (filtros.categoria) params.append('categoria', filtros.categoria)
    if (Array.isArray(filtros.urgencias)) {
      filtros.urgencias.forEach((urgencia) => params.append('urgencia', urgencia))
    }

    const endpoint = params.toString() ? `cartelera/?${params.toString()}` : 'cartelera/'
    const data = await this.apiClient.get(
      endpoint,
      {},
      {
        enabled: true,
        key: this.cacheKeys.cartelera(filtros),
        forceRefresh,
      }
    )
    
    return data.map((publicacion) => new Publicacion(publicacion))
  }

  /**
   * Crea una nueva publicación
   */
  async crearPublicacion(formulario) {
    const data = await this.apiClient.post('publicaciones/', formulario)
    
    // Invalidar caché de cartelera y mis publicaciones
    this.apiClient.invalidate(this.cacheKeys.cartelera({}))
    this.apiClient.invalidate(this.cacheKeys.misPublicaciones)
    
    return new Publicacion(data)
  }

  /**
   * Obtiene las publicaciones del usuario actual (con caché)
   */
  async obtenerMisPublicaciones(forceRefresh = false) {
    const data = await this.apiClient.get(
      'mis-publicaciones/',
      {},
      {
        enabled: true,
        key: this.cacheKeys.misPublicaciones,
        forceRefresh,
      }
    )
    
    return (data.publicaciones || []).map((publicacion) => new Publicacion(publicacion))
  }

  /**
   * Actualiza el estado de una publicación
   */
  async actualizarEstadoPublicacion(id, estaActiva) {
    const data = await this.apiClient.patch(
      `publicaciones/${id}/`,
      { esta_activa: Boolean(estaActiva) }
    )
    
    // Invalidar todas las cachés relacionadas
    this.apiClient.invalidate(this.cacheKeys.cartelera({}))
    this.apiClient.invalidate(this.cacheKeys.misPublicaciones)
    this.apiClient.invalidate(this.cacheKeys.publicacion(id))
    
    return new Publicacion(data)
  }

  /**
   * Invalida toda la caché de publicaciones
   */
  invalidateAll() {
    this.apiClient.invalidateAll()
  }

  /**
   * Invalida la caché de la cartelera
   */
  invalidateCartelera(filtros = {}) {
    this.apiClient.invalidate(this.cacheKeys.cartelera(filtros))
  }

  /**
   * Invalida la caché de mis publicaciones
   */
  invalidateMisPublicaciones() {
    this.apiClient.invalidate(this.cacheKeys.misPublicaciones)
  }
}
