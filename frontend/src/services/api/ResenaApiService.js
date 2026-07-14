import ApiClient, { sharedApiClient } from './ApiClient.js'

/**
 * ResenaRepository - Repositorio para operaciones de reseñas
 * Usa caché limitado para notificaciones
 */
export default class ResenaRepository {
  constructor(apiClient = null) {
    this.apiClient = apiClient || sharedApiClient

    // Claves de caché
    this.cacheKeys = {
      notificaciones: 'notificaciones',
    }
  }

  /**
   * Registra una reseña
   */
  async registrarResena(truequeId, estrellas, comentario) {
    const result = await this.apiClient.post('resenas/', {
      trueque_id: truequeId,
      estrellas,
      comentario,
    })

    // Invalidar caché de notificaciones Y de mis-trueques
    // (mis-trueques contiene el campo pendiente_resena que cambia al registrar reseña)
    this.apiClient.invalidate(this.cacheKeys.notificaciones)
    this.apiClient.invalidate('trueques:mis')

    return result
  }

  /**
   * Obtiene las notificaciones del usuario (con caché)
   */
  async obtenerNotificaciones(incluirLeidas = false, forceRefresh = false) {
    const query = incluirLeidas ? '?incluir_leidas=true' : ''
    const data = await this.apiClient.get(
      `notificaciones/${query}`,
      {},
      {
        enabled: true,
        key: this.cacheKeys.notificaciones,
        forceRefresh,
      }
    )

    const notificaciones = (data.notificaciones || []).map((notificacion) => ({
      ...notificacion,
      match_detalle: this._normalizarMatchDetalle(notificacion.match_detalle),
    }))

    return {
      notificaciones,
      cantidad: data.cantidad ?? notificaciones.length,
    }
  }

  /**
   * Marca una notificación como leída
   */
  async marcarNotificacionLeida(notificacionId) {
    const result = await this.apiClient.post('notificaciones/marcar-leida/', {
      notificacion_id: notificacionId,
      accion: 'marcar_leida',
    })

    // Invalidar caché de notificaciones
    this.apiClient.invalidate(this.cacheKeys.notificaciones)

    return result
  }

  /**
   * Marca todas las notificaciones de un trueque como leídas
   */
  async marcarNotificacionesTruequeLeidas(truequeId) {
    const result = await this.apiClient.post('notificaciones/marcar-leida/', {
      trueque_id: truequeId,
      accion: 'marcar_leidas_trueque',
    })

    // Invalidar caché de notificaciones
    this.apiClient.invalidate(this.cacheKeys.notificaciones)

    return result
  }

  /**
   * Normaliza el detalle de match de una notificación
   * @private
   */
  _normalizarMatchDetalle(matchDetalle) {
    if (!matchDetalle) {
      return null
    }

    if (!Array.isArray(matchDetalle)) {
      // Es un objeto (ej. trueque múltiple), retornarlo tal cual
      return matchDetalle
    }

    return matchDetalle.map((entrada) => ({
      rol: entrada.rol || '',
      mi_titulo: entrada.mi_titulo || '',
      mi_tipo: entrada.mi_tipo || '',
      su_titulo: entrada.su_titulo || '',
      su_tipo: entrada.su_tipo || '',
    }))
  }

  /**
   * Registra una reseña en trueque múltiple
   */
  async registrarResenaMultiple(truequeMultipleId, calificadoId, estrellas, comentario) {
    const result = await this.apiClient.post('resenas-multiples/', {
      trueque_multiple_id: truequeMultipleId,
      calificado_id: calificadoId,
      estrellas,
      comentario,
    })

    this.apiClient.invalidate(this.cacheKeys.notificaciones)

    return result
  }

  /**
   * Invalida la caché de notificaciones
   */
  invalidateNotificaciones() {
    this.apiClient.invalidate(this.cacheKeys.notificaciones)
  }

  /**
   * Invalida toda la caché de reseñas
   */
  invalidateAll() {
    this.apiClient.invalidateAll()
  }
}
