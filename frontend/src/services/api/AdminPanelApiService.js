/**
 * AdminPanelRepository — Servicio API para el Panel de Administracion (S2 HU3).
 *
 * Capa: services/api/ (Presentacion del frontend)
 *
 * Encapsula todas las llamadas HTTP al backend para CRUD de:
 * Usuarios, Publicaciones, Trueques, Trueques Multiples,
 * Resenas, Resenas Multiples y Saldos Comerciales.
 *
 * Flujo: useAdminPanelStore (Pinia) -> AdminPanelRepository -> ApiClient -> Backend
 */
import ApiClient from './ApiClient.js'

export default class AdminPanelRepository {
  constructor(baseURL = '/api/') {
    this.apiClient = new ApiClient(baseURL)
    this.baseURL = this.apiClient.baseURL
  }

  async _request(endpoint, options = {}) {
    return this.apiClient.request(endpoint, options)
  }

  // Dashboard
  async obtenerDashboard() {
    return await this._request('admin/panel/dashboard/')
  }

  // Usuarios
  async obtenerUsuarios(busqueda = '') {
    const query = busqueda ? `?q=${encodeURIComponent(busqueda)}` : ''
    return await this._request(`admin/panel/usuarios/${query}`)
  }

  async toggleUsuario(usuarioId) {
    return await this._request(`admin/panel/usuarios/${usuarioId}/toggle/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
  }

  async cambiarRol(usuarioId, isStaff) {
    return await this._request(`admin/panel/usuarios/${usuarioId}/rol/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_staff: isStaff }),
    })
  }

  async eliminarUsuario(usuarioId) {
    return await this._request(`admin/panel/usuarios/${usuarioId}/`, {
      method: 'DELETE',
    })
  }

  // Publicaciones
  async obtenerPublicaciones(busqueda = '') {
    const query = busqueda ? `?q=${encodeURIComponent(busqueda)}` : ''
    return await this._request(`admin/panel/publicaciones/${query}`)
  }

  async crearPublicacion(datos) {
    return await this._request('admin/panel/publicaciones/crear/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datos),
    })
  }

  async moderarPublicacion(publicacionId, estaActiva) {
    return await this._request(`admin/panel/publicaciones/${publicacionId}/moderar/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ esta_activa: estaActiva }),
    })
  }

  async eliminarPublicacion(publicacionId) {
    return await this._request(`admin/panel/publicaciones/${publicacionId}/`, {
      method: 'DELETE',
    })
  }

  // Trueques
  async obtenerTrueques(busqueda = '') {
    const query = busqueda ? `?q=${encodeURIComponent(busqueda)}` : ''
    return await this._request(`admin/panel/trueques/${query}`)
  }

  async actualizarEstadoTrueque(truequeId, estado) {
    return await this._request(`admin/panel/trueques/${truequeId}/estado/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ estado }),
    })
  }

  async eliminarTrueque(truequeId) {
    return await this._request(`admin/panel/trueques/${truequeId}/`, {
      method: 'DELETE',
    })
  }

  // Trueques Multiples
  async obtenerTruequesMultiples(busqueda = '') {
    const query = busqueda ? `?q=${encodeURIComponent(busqueda)}` : ''
    return await this._request(`admin/panel/trueques-multiples/${query}`)
  }

  async actualizarEstadoTruequeMultiple(truequeId, estado) {
    return await this._request(`admin/panel/trueques-multiples/${truequeId}/estado/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ estado }),
    })
  }

  async eliminarTruequeMultiple(truequeId) {
    return await this._request(`admin/panel/trueques-multiples/${truequeId}/`, {
      method: 'DELETE',
    })
  }

  // Resenas
  async obtenerResenas(busqueda = '') {
    const query = busqueda ? `?q=${encodeURIComponent(busqueda)}` : ''
    return await this._request(`admin/panel/resenas/${query}`)
  }

  async eliminarResena(resenaId) {
    return await this._request(`admin/panel/resenas/${resenaId}/`, {
      method: 'DELETE',
    })
  }

  // Resenas Multiples
  async obtenerResenasMultiples(busqueda = '') {
    const query = busqueda ? `?q=${encodeURIComponent(busqueda)}` : ''
    return await this._request(`admin/panel/resenas-multiples/${query}`)
  }

  async eliminarResenaMultiple(resenaId) {
    return await this._request(`admin/panel/resenas-multiples/${resenaId}/`, {
      method: 'DELETE',
    })
  }

  // Saldos Comerciales
  async obtenerSaldos(busqueda = '') {
    const query = busqueda ? `?q=${encodeURIComponent(busqueda)}` : ''
    return await this._request(`admin/panel/saldos/${query}`)
  }
}
