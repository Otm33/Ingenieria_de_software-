import User from './User.js'
import Publicacion from './Publicacion.js'

export default class UserService {
  // CAMBIO MODELO/SERVICIO: esta clase concentra la comunicacion frontend -> API -> BD.
  constructor(baseURL = '/api/') {
    this.baseURL = baseURL.endsWith('/') ? baseURL : `${baseURL}/`
    this._usuarios = []
    this._publicaciones = []
  }

  // CAMBIO MODELO/SERVICIO: metodo base reutilizable para no repetir fetch en las vistas.
  async _request(endpoint, options = {}) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      credentials: 'include',
      ...options,
    })
    const contentType = response.headers.get('content-type') || ''
    const data = contentType.includes('application/json') ? await response.json() : null

    if (!response.ok) {
      throw new Error(data?.error || data?.detail || 'No se pudo completar la solicitud.')
    }

    return data
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

  // CAMBIO MODELO/SERVICIO: registra usuarios reales en la BD mediante /api/registro/.
  async registrarUsuario(formulario) {
    const data = await this._request('registro/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(User.paraRegistro(formulario)),
    })

    const usuario = new User(data)
    this._usuarios.push(usuario)
    return usuario
  }

  // CAMBIO AUTH: consulta si Django ya tiene una sesion abierta.
  async obtenerSesionActual() {
    const data = await this._request('sesion/')
    return data.autenticado ? new User(data.usuario) : null
  }

  // CAMBIO AUTH: inicia sesion en Django y devuelve el usuario autenticado.
  async iniciarSesion(credenciales) {
    const data = await this._request('login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credenciales),
    })

    return new User(data.usuario)
  }

  // CAMBIO AUTH: cierra la sesion Django.
  async cerrarSesion() {
    await this._request('logout/', { method: 'POST' })
    this._usuarios = []
    this._publicaciones = []
  }

  // CAMBIO MODELO/SERVICIO: envia el CSV al backend, que lo persiste con UsuarioAutorizado.
  async cargarUsuariosAutorizados(archivo) {
    const formData = new FormData()
    formData.append('archivo_csv', archivo)

    return await this._request('cargar-csv/', {
      method: 'POST',
      body: formData,
    })
  }

  // CAMBIO MODELO/SERVICIO: consulta la cartelera real guardada en la BD.
  async obtenerCartelera(filtros = {}) {
    const params = new URLSearchParams()
    if (filtros.categoria) params.append('categoria', filtros.categoria)
    if (Array.isArray(filtros.urgencias)) {
      filtros.urgencias.forEach((urgencia) => params.append('urgencia', urgencia))
    }

    const endpoint = params.toString() ? `cartelera/?${params.toString()}` : 'cartelera/'
    const data = await this._request(endpoint)
    this._publicaciones = data.map((publicacion) => new Publicacion(publicacion))
    return this._publicaciones
  }

  async crearPublicacion(formulario) {
    const data = await this._request('publicaciones/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formulario),
    })

    const publicacion = new Publicacion(data)
    this._publicaciones.unshift(publicacion)
    return publicacion
  }

  async obtenerMiPerfil() {
    const data = await this._request('mi-perfil/')
    return data
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
    const data = await this._request(`publicaciones/${id}/`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ esta_activa: Boolean(estaActiva) }),
    })

    return new Publicacion(data)
  }

  async verificarCoincidenciaPorTitulo(publicacionId) {
    const params = new URLSearchParams()
    params.set('publicacion_id', publicacionId)
    params.set('accion', 'verificar_coincidencia')

    const endpoint = `matchmaking/?${params.toString()}`
    const data = await this._request(endpoint)
    return data
  }

  async obtenerMatches(publicacionId = null) {
    const { matches } = await this.obtenerMatchesEnriquecidos(publicacionId)
    return matches.map((match) => match.usuario)
  }

  async obtenerMatchesEnriquecidos(publicacionId = null) {
    const params = new URLSearchParams()
    if (publicacionId) {
      params.set('publicacion_id', publicacionId)
    }

    const endpoint = params.toString() ? `matchmaking/?${params.toString()}` : 'matchmaking/'
    const data = await this._request(endpoint)

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

  async responderPropuestaMultiple(truequeMultipleId, accion) {
    const accionLower = String(accion || '').toLowerCase()
    const endpointAction = accionLower === 'aceptar' || accionLower === 'aceptar' ? 'aceptar' : 'rechazar'
    return await this._request(`trueques-multiples/${truequeMultipleId}/${endpointAction}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
  }

  async finalizarTrueque(truequeId) {
    return await this._request(`trueques/${truequeId}/finalizar/`, {
      method: 'POST',
    })
  }

  async validarCodigoTrueque(truequeId, codigo) {
    return await this._request(`trueques/${truequeId}/validar-codigo/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ codigo }),
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

  _normalizarMatchDetalle(matchDetalle) {
    if (!Array.isArray(matchDetalle) || !matchDetalle.length) {
      return null
    }

    return matchDetalle.map((entrada) => ({
      rol: entrada.rol || '',
      mi_titulo: entrada.mi_titulo || '',
      mi_tipo: entrada.mi_tipo || '',
      su_titulo: entrada.su_titulo || '',
      su_tipo: entrada.su_tipo || '',
    }))
  }

  _mapNotificacion(notificacion) {
    const matchDetalle = this._normalizarMatchDetalle(notificacion.match_detalle)

    return {
      ...notificacion,
      match_detalle: matchDetalle,
    }
  }

  async obtenerNotificaciones(incluirLeidas = false) {
    const query = incluirLeidas ? '?incluir_leidas=true' : ''
    const data = await this._request(`notificaciones/${query}`)
    const notificaciones = (data.notificaciones || []).map((notificacion) => (
      this._mapNotificacion(notificacion)
    ))

    return {
      notificaciones,
      cantidad: data.cantidad ?? notificaciones.length,
    }
  }

  async marcarNotificacionLeida(notificacionId) {
    return await this._request('notificaciones/marcar-leida/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notificacion_id: notificacionId }),
    })
  }

  async marcarNotificacionesTruequeLeidas(truequeId) {
    return await this._request('notificaciones/marcar-leida/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trueque_id: truequeId }),
    })
  }

  async obtenerMisTrueques() {
    const data = await this._request('mis-trueques/')
    return {
      trueques: data.trueques || [],
      cantidad: data.cantidad ?? (data.trueques || []).length,
    }
  }

  async obtenerMisTruequesMultiples() {
    const data = await this._request('mis-trueques-multiples/')
    return {
      trueques_multiple: data.trueques_multiple || [],
      cantidad: data.cantidad ?? (data.trueques_multiple || []).length,
    }
  }

  async validarCodigoParMultiple(truequeMultipleId, par, codigo) {
    return await this._request(`trueques-multiples/${truequeMultipleId}/validar-codigo/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ codigo, par }),
    })
  }

  async registrarResenaMultiple(truequeMultipleId, calificadoId, estrellas, comentario) {
    return await this._request('resenas-multiples/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        trueque_multiple_id: truequeMultipleId,
        calificado_id: calificadoId,
        estrellas,
        comentario,
      }),
    })
  }

  get users() {
    return this._usuarios
  }

  get publicaciones() {
    return this._publicaciones
  }
}
