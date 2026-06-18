import { defineStore } from 'pinia'
import { ref } from 'vue'
import ImpactoSocialApiService from '../services/api/ImpactoSocialApiService.js'

/**
 * ImpactoSocialStore — Sprint 2 HU1
 * Pinia store para Impacto Social (Donaciones solidarias de Horas de Vida).
 * Sigue el patrón de los otros stores del proyecto.
 */
export const useImpactoSocialStore = defineStore('impactoSocial', () => {
  const loading = ref(false)
  const error = ref(null)
  const api = new ImpactoSocialApiService()

  // ── Solicitudes públicas ──────────────────────────────────────────

  async function obtenerSolicitudesAprobadas() {
    loading.value = true
    error.value = null
    try {
      return await api.obtenerSolicitudesAprobadas()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function crearSolicitud(categoria, titulo, descripcion) {
    loading.value = true
    error.value = null
    try {
      return await api.crearSolicitud(categoria, titulo, descripcion)
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function obtenerMisSolicitudes() {
    loading.value = true
    error.value = null
    try {
      return await api.obtenerMisSolicitudes()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function activarNecesidadVinculada(solicitudId) {
    loading.value = true
    error.value = null
    try {
      return await api.activarNecesidadVinculada(solicitudId)
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // ── Donaciones ────────────────────────────────────────────────────

  async function obtenerMisDonaciones() {
    loading.value = true
    error.value = null
    try {
      return await api.obtenerMisDonaciones()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function donarACausa(solicitudId, monto) {
    loading.value = true
    error.value = null
    try {
      return await api.donarACausa(solicitudId, monto)
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function donarAFondo(monto) {
    loading.value = true
    error.value = null
    try {
      return await api.donarAFondo(monto)
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // ── Admin ─────────────────────────────────────────────────────────

  async function obtenerSolicitudesPendientes() {
    loading.value = true
    error.value = null
    try {
      return await api.obtenerSolicitudesPendientes()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function aprobarSolicitud(solicitudId) {
    loading.value = true
    error.value = null
    try {
      return await api.aprobarSolicitud(solicitudId)
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function rechazarSolicitud(solicitudId) {
    loading.value = true
    error.value = null
    try {
      return await api.rechazarSolicitud(solicitudId)
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function obtenerUsuariosAdmin() {
    loading.value = true
    error.value = null
    try {
      return await api.obtenerUsuariosAdmin()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function actualizarEstadoSocial(usuarioId, estadoSocial) {
    loading.value = true
    error.value = null
    try {
      return await api.actualizarEstadoSocial(usuarioId, estadoSocial)
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function obtenerSaldoFondo() {
    loading.value = true
    error.value = null
    try {
      return await api.obtenerSaldoFondo()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function asignarDesdeFondo(usuarioId, solicitudId, monto) {
    loading.value = true
    error.value = null
    try {
      return await api.asignarDesdeFondo(usuarioId, solicitudId, monto)
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    obtenerSolicitudesAprobadas,
    crearSolicitud,
    obtenerMisSolicitudes,
    activarNecesidadVinculada,
    obtenerMisDonaciones,
    donarACausa,
    donarAFondo,
    obtenerSolicitudesPendientes,
    aprobarSolicitud,
    rechazarSolicitud,
    obtenerUsuariosAdmin,
    actualizarEstadoSocial,
    obtenerSaldoFondo,
    asignarDesdeFondo,
  }
})
