import ApiClient from '../repositories/ApiClient.js'

export default class ImpactoSocialService {
  constructor(baseURL = '/api/') {
    this.apiClient = new ApiClient(baseURL)
    this.baseURL = this.apiClient.baseURL
  }

  async _request(endpoint, options = {}) {
    return this.apiClient.request(endpoint, options)
  }

  async obtenerSolicitudesAprobadas() {
    return await this._request('impacto-social/solicitudes/')
  }

  async crearSolicitud(categoria, titulo, descripcion) {
    return await this._request('impacto-social/solicitudes/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ categoria, titulo, descripcion }),
    })
  }

  async obtenerMisSolicitudes() {
    return await this._request('impacto-social/mis-solicitudes/')
  }

  async obtenerMisDonaciones() {
    return await this._request('impacto-social/mis-donaciones/')
  }

  async donarACausa(solicitudId, monto) {
    return await this._request('impacto-social/donar/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        solicitud_id: solicitudId,
        monto,
      }),
    })
  }

  async donarAFondo(monto) {
    return await this._request('impacto-social/donar-fondo/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ monto }),
    })
  }

  async obtenerSolicitudesPendientes() {
    return await this._request('admin/impacto-social/solicitudes-pendientes/')
  }

  async aprobarSolicitud(solicitudId) {
    return await this._request(`admin/impacto-social/solicitudes/${solicitudId}/aprobar/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
  }

  async rechazarSolicitud(solicitudId) {
    return await this._request(`admin/impacto-social/solicitudes/${solicitudId}/rechazar/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
  }

  async obtenerUsuariosAdmin() {
    return await this._request('admin/impacto-social/usuarios/')
  }

  async actualizarEstadoSocial(usuarioId, estadoSocial) {
    return await this._request(`admin/impacto-social/usuarios/${usuarioId}/estado-social/`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ estado_social: estadoSocial }),
    })
  }

  async obtenerSaldoFondo() {
    return await this._request('admin/impacto-social/fondo/')
  }

  async asignarDesdeFondo(usuarioId, solicitudId, monto) {
    return await this._request('admin/impacto-social/fondo/asignar/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        usuario_id: usuarioId,
        solicitud_id: solicitudId,
        monto,
      }),
    })
  }

  async activarNecesidadVinculada(solicitudId) {
    return await this._request(`impacto-social/solicitudes/${solicitudId}/activar-necesidad/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
  }
}
