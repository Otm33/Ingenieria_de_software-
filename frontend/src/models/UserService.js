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
    if (filtros.categoria) params.set('categoria', filtros.categoria)
    if (filtros.urgencia) params.set('urgencia', filtros.urgencia)

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

  async obtenerMisPublicaciones() {
    const data = await this._request('mis-publicaciones/')
    return data.publicaciones || []
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
    const params = new URLSearchParams()
    if (publicacionId) {
      params.set('publicacion_id', publicacionId)
    }

    const endpoint = params.toString() ? `matchmaking/?${params.toString()}` : 'matchmaking/'
    const data = await this._request(endpoint)
    return data.matches || []
  }

  get users() {
    return this._usuarios
  }

  get publicaciones() {
    return this._publicaciones
  }
}
