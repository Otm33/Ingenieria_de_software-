import ApiClient from '../repositories/ApiClient.js'

export default class UserService {
  constructor(baseURL = '/api/') {
    this.apiClient = new ApiClient(baseURL)
    this.baseURL = this.apiClient.baseURL
  }

  async _request(endpoint, options = {}) {
    return this.apiClient.request(endpoint, options)
  }

  async validarEmail(email, esComercio = false) {
    return await this._request('registro/validar-email/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email?.trim(),
        es_comercio: Boolean(esComercio),
      }),
    })
  }

  async registrarUsuario(payloadRegistro) {
    return await this._request('registro/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payloadRegistro),
    })
  }

  async obtenerSesionActual() {
    return await this._request('sesion/')
  }

  async iniciarSesion(credenciales) {
    return await this._request('login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credenciales),
    })
  }

  async cerrarSesion() {
    await this._request('logout/', { method: 'POST' })
  }

  async cargarUsuariosAutorizados(archivo) {
    const formData = new FormData()
    formData.append('archivo_csv', archivo)

    return await this._request('cargar-csv/', {
      method: 'POST',
      body: formData,
    })
  }

  async obtenerCartelera(filtros = {}) {
    const params = new URLSearchParams()
    if (filtros.categoria) params.append('categoria', filtros.categoria)
    if (Array.isArray(filtros.urgencias)) {
      filtros.urgencias.forEach((urgencia) => params.append('urgencia', urgencia))
    }

    const endpoint = params.toString() ? `cartelera/?${params.toString()}` : 'cartelera/'
    return await this._request(endpoint)
  }

  async crearPublicacion(formulario) {
    return await this._request('publicaciones/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formulario),
    })
  }

  async obtenerMiPerfil() {
    return await this._request('mi-perfil/')
  }

  async obtenerComunidad() {
    return await this._request('comunidad/')
  }

  async obtenerPerfilUsuario(id) {
    return await this._request(`perfil/${id}/`)
  }

  async obtenerMisPublicaciones() {
    const data = await this._request('mis-publicaciones/')
    return data.publicaciones || []
  }

  async actualizarEstadoPublicacion(id, estaActiva) {
    return await this._request(`publicaciones/${id}/`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ esta_activa: Boolean(estaActiva) }),
    })
  }

  async verificarCoincidenciaPorTitulo(publicacionId) {
    const params = new URLSearchParams()
    params.set('publicacion_id', publicacionId)
    params.set('accion', 'verificar_coincidencia')

    const endpoint = `matchmaking/?${params.toString()}`
    return await this._request(endpoint)
  }

  async obtenerMatchesEnriquecidos(publicacionId = null) {
    const params = new URLSearchParams()
    if (publicacionId) {
      params.set('publicacion_id', publicacionId)
    }

    const endpoint = params.toString() ? `matchmaking/?${params.toString()}` : 'matchmaking/'
    return await this._request(endpoint)
  }

  async crearPropuesta(receptorId, publicacionEmisorId, publicacionReceptorId) {
    return await this._request('trueques/propuestas/crear/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        receptor_id: receptorId,
        publicacion_emisor_id: publicacionEmisorId,
        publicacion_receptor_id: publicacionReceptorId,
      }),
    })
  }

  async responderPropuesta(truequeId, accion) {
    return await this._request(`trueques/${truequeId}/responder/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ accion }),
    })
  }

  async finalizarTrueque(truequeId) {
    return await this._request(`trueques/${truequeId}/finalizar/`, {
      method: 'POST',
    })
  }

  async registrarResena(truequeId, estrellas, comentario) {
    return await this._request('resenas/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        trueque_id: truequeId,
        estrellas,
        comentario,
      }),
    })
  }

  async obtenerNotificaciones(incluirLeidas = false) {
    const query = incluirLeidas ? '?incluir_leidas=true' : ''
    return await this._request(`notificaciones/${query}`)
  }

  async marcarNotificacionLeida(notificacionId) {
    return await this._request('notificaciones/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notificacion_id: notificacionId }),
    })
  }

  async marcarNotificacionesTruequeLeidas(truequeId) {
    return await this._request('notificaciones/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trueque_id: truequeId }),
    })
  }

  async obtenerMisTrueques() {
    return await this._request('mis-trueques/')
  }
}
