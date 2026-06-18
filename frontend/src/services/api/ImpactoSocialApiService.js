/**
 * ImpactoSocialApiService — Sprint 2 HU1
 * Servicio HTTP para endpoints de Impacto Social.
 * Sigue el patrón de los otros ApiService del proyecto.
 */
import ApiClient from './ApiClient.js'

export default class ImpactoSocialApiService {
  constructor(baseURL = '/api/') {
    this.apiClient = new ApiClient(baseURL)
  }

  // ── Solicitudes públicas ──────────────────────────────────────────

  async obtenerSolicitudesAprobadas() {
    return await this.apiClient.request('impacto-social/solicitudes/')
  }

  async crearSolicitud(categoria, titulo, descripcion) {
    return await this.apiClient.request('impacto-social/solicitudes/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ categoria, titulo, descripcion }),
    })
  }

  async obtenerMisSolicitudes() {
    return await this.apiClient.request('impacto-social/mis-solicitudes/')
  }

  async activarNecesidadVinculada(solicitudId) {
    return await this.apiClient.request(
      `impacto-social/solicitudes/${solicitudId}/activar-necesidad/`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' } },
    )
  }

  // ── Donaciones ────────────────────────────────────────────────────

  async obtenerMisDonaciones() {
    return await this.apiClient.request('impacto-social/mis-donaciones/')
  }

  async donarACausa(solicitudId, monto) {
    return await this.apiClient.request('impacto-social/donar/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ solicitud_id: solicitudId, monto }),
    })
  }

  async donarAFondo(monto) {
    return await this.apiClient.request('impacto-social/donar-fondo/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ monto }),
    })
  }

  // ── Admin ─────────────────────────────────────────────────────────

  async obtenerSolicitudesPendientes() {
    return await this.apiClient.request('admin/impacto-social/solicitudes-pendientes/')
  }

  async aprobarSolicitud(solicitudId) {
    return await this.apiClient.request(
      `admin/impacto-social/solicitudes/${solicitudId}/aprobar/`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' } },
    )
  }

  async rechazarSolicitud(solicitudId) {
    return await this.apiClient.request(
      `admin/impacto-social/solicitudes/${solicitudId}/rechazar/`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' } },
    )
  }

  async obtenerUsuariosAdmin() {
    return await this.apiClient.request('admin/impacto-social/usuarios/')
  }

  async actualizarEstadoSocial(usuarioId, estadoSocial) {
    return await this.apiClient.request(
      `admin/impacto-social/usuarios/${usuarioId}/estado-social/`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ estado_social: estadoSocial }),
      },
    )
  }

  async obtenerSaldoFondo() {
    return await this.apiClient.request('admin/impacto-social/fondo/')
  }

  async asignarDesdeFondo(usuarioId, solicitudId, monto) {
    return await this.apiClient.request('admin/impacto-social/fondo/asignar/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usuario_id: usuarioId, solicitud_id: solicitudId, monto }),
    })
  }
}
