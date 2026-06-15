import ApiClient from './ApiClient.js'
import User from '../models/User.js'
import Publicacion from '../models/Publicacion.js'

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
      misTruequesMultiples: 'trueques-multiples:mis',
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
   * Valida el código de confirmación y finaliza el trueque
   */
  async validarCodigo(truequeId, codigo) {
    const result = await this.apiClient.post(
      `trueques/${truequeId}/validar-codigo/`,
      { codigo }
    )
    
    // Invalidar caché de trueques y notificaciones
    this.apiClient.invalidate(this.cacheKeys.misTrueques)
    this.apiClient.invalidate(this.cacheKeys.notificaciones)
    
    return result
  }

  /**
   * Obtiene matches enriquecidos con modelos de dominio
   */
  async obtenerMatchesEnriquecidos(publicacionId = null, forceRefresh = false) {
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

    const matches = (data.matches || []).map((match) => ({
      usuario: new User(match.usuario),
      talentosCoincidentes: (match.talentos_coincidentes || []).map(
        (publicacion) => new Publicacion(publicacion),
      ),
      necesidadesCoincidentes: (match.necesidades_coincidentes || []).map(
        (publicacion) => new Publicacion(publicacion),
      ),
      publicacionesSugeridas: match.publicaciones_sugeridas || [],
    }))

    return {
      matches,
      mensaje: data.mensaje || '',
      cantidad: data.cantidad ?? matches.length,
    }
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

    return {
      trueques: data.trueques || [],
      cantidad: data.cantidad ?? (data.trueques || []).length,
    }
  }

  /**
   * Responde a una propuesta de trueque múltiple
   */
  async responderPropuestaMultiple(truequeMultipleId, accion) {
    const accionLower = String(accion || '').toLowerCase()
    const endpointAction = accionLower === 'aceptar' ? 'aceptar' : 'rechazar'
    const result = await this.apiClient.post(
      `trueques-multiples/${truequeMultipleId}/${endpointAction}/`,
      {},
    )

    this.apiClient.invalidate(this.cacheKeys.misTruequesMultiples)
    this.apiClient.invalidate(this.cacheKeys.notificaciones)

    return result
  }

  /**
   * Obtiene los trueques múltiples del usuario actual
   */
  async obtenerMisTruequesMultiples(forceRefresh = false) {
    const data = await this.apiClient.get(
      'mis-trueques-multiples/',
      {},
      {
        enabled: true,
        key: this.cacheKeys.misTruequesMultiples,
        forceRefresh,
      }
    )

    return {
      trueques_multiple: data.trueques_multiple || [],
      cantidad: data.cantidad ?? (data.trueques_multiple || []).length,
    }
  }

  /**
   * Valida el código de un par en trueque múltiple
   */
  async validarCodigoParMultiple(truequeMultipleId, par, codigo) {
    const result = await this.apiClient.post(
      `trueques-multiples/${truequeMultipleId}/validar-codigo/`,
      { codigo, par },
    )

    this.apiClient.invalidate(this.cacheKeys.misTruequesMultiples)
    this.apiClient.invalidate(this.cacheKeys.notificaciones)

    return result
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
