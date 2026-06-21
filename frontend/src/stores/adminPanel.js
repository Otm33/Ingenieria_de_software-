/**
 * Pinia Store — Panel de Administracion (Sprint 2 HU3).
 *
 * Capa: stores/ (Estado del frontend)
 *
 * Gestiona el estado del panel admin: dashboard, listas de entidades,
 * seccion activa, termino de busqueda y operaciones CRUD.
 *
 * Flujo: AdminPanel.vue -> useAdminPanelStore -> AdminPanelRepository -> Backend
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import AdminPanelRepository from '../services/api/AdminPanelApiService.js'

export const useAdminPanelStore = defineStore('adminPanel', () => {
  const api = new AdminPanelRepository()

  // Estado reactivo
  const dashboard = ref(null)
  const usuarios = ref([])
  const publicaciones = ref([])
  const trueques = ref([])
  const truequesMultiples = ref([])
  const resenas = ref([])
  const resenasMultiples = ref([])
  const saldos = ref([])
  const loading = ref(false)
  const error = ref('')

  // Dashboard
  async function cargarDashboard() {
    loading.value = true
    error.value = ''
    try {
      dashboard.value = await api.obtenerDashboard()
      return dashboard.value
    } catch (err) {
      error.value = err.message || 'Error al cargar dashboard.'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Usuarios
  async function cargarUsuarios(busqueda = '') {
    loading.value = true
    error.value = ''
    try {
      const data = await api.obtenerUsuarios(busqueda)
      usuarios.value = data.usuarios || []
      return data
    } catch (err) {
      error.value = err.message || 'Error al cargar usuarios.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function toggleUsuario(usuarioId) {
    try {
      const data = await api.toggleUsuario(usuarioId)
      const idx = usuarios.value.findIndex((u) => u.id === usuarioId)
      if (idx !== -1 && data.usuario) usuarios.value[idx] = data.usuario
      return data
    } catch (err) {
      error.value = err.message || 'Error al cambiar estado del usuario.'
      throw err
    }
  }

  async function cambiarRol(usuarioId, isStaff) {
    try {
      const data = await api.cambiarRol(usuarioId, isStaff)
      const idx = usuarios.value.findIndex((u) => u.id === usuarioId)
      if (idx !== -1 && data.usuario) usuarios.value[idx] = data.usuario
      return data
    } catch (err) {
      error.value = err.message || 'Error al cambiar rol.'
      throw err
    }
  }

  async function eliminarUsuario(usuarioId) {
    try {
      const data = await api.eliminarUsuario(usuarioId)
      usuarios.value = usuarios.value.filter((u) => u.id !== usuarioId)
      return data
    } catch (err) {
      error.value = err.message || 'Error al eliminar usuario.'
      throw err
    }
  }

  async function editarUsuario(usuarioId, datos) {
    try {
      const data = await api.editarUsuario(usuarioId, datos)
      const idx = usuarios.value.findIndex((u) => u.id === usuarioId)
      if (idx !== -1 && data.usuario) usuarios.value[idx] = data.usuario
      return data
    } catch (err) {
      error.value = err.message || 'Error al editar usuario.'
      throw err
    }
  }

  // Publicaciones
  async function cargarPublicaciones(busqueda = '') {
    loading.value = true
    error.value = ''
    try {
      const data = await api.obtenerPublicaciones(busqueda)
      publicaciones.value = data.publicaciones || []
      return data
    } catch (err) {
      error.value = err.message || 'Error al cargar publicaciones.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function crearPublicacion(datos) {
    try {
      const data = await api.crearPublicacion(datos)
      if (data.publicacion) publicaciones.value.unshift(data.publicacion)
      return data
    } catch (err) {
      error.value = err.message || 'Error al crear publicacion.'
      throw err
    }
  }

  async function moderarPublicacion(publicacionId, estaActiva) {
    try {
      const data = await api.moderarPublicacion(publicacionId, estaActiva)
      const idx = publicaciones.value.findIndex((p) => p.id === publicacionId)
      if (idx !== -1 && data.publicacion) publicaciones.value[idx] = data.publicacion
      return data
    } catch (err) {
      error.value = err.message || 'Error al moderar publicacion.'
      throw err
    }
  }

  async function eliminarPublicacion(publicacionId) {
    try {
      const data = await api.eliminarPublicacion(publicacionId)
      publicaciones.value = publicaciones.value.filter((p) => p.id !== publicacionId)
      return data
    } catch (err) {
      error.value = err.message || 'Error al eliminar publicacion.'
      throw err
    }
  }

  async function editarPublicacion(publicacionId, datos) {
    try {
      const data = await api.editarPublicacion(publicacionId, datos)
      const idx = publicaciones.value.findIndex((p) => p.id === publicacionId)
      if (idx !== -1 && data.publicacion) publicaciones.value[idx] = data.publicacion
      return data
    } catch (err) {
      error.value = err.message || 'Error al editar publicacion.'
      throw err
    }
  }

  // Trueques
  async function cargarTrueques(busqueda = '') {
    loading.value = true
    error.value = ''
    try {
      const data = await api.obtenerTrueques(busqueda)
      trueques.value = data.trueques || []
      return data
    } catch (err) {
      error.value = err.message || 'Error al cargar trueques.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function actualizarEstadoTrueque(truequeId, estado) {
    try {
      const data = await api.actualizarEstadoTrueque(truequeId, estado)
      const idx = trueques.value.findIndex((t) => t.id === truequeId)
      if (idx !== -1 && data.trueque) trueques.value[idx] = data.trueque
      return data
    } catch (err) {
      error.value = err.message || 'Error al actualizar estado.'
      throw err
    }
  }

  async function eliminarTrueque(truequeId) {
    try {
      const data = await api.eliminarTrueque(truequeId)
      trueques.value = trueques.value.filter((t) => t.id !== truequeId)
      return data
    } catch (err) {
      error.value = err.message || 'Error al eliminar trueque.'
      throw err
    }
  }

  // Trueques Multiples
  async function cargarTruequesMultiples(busqueda = '') {
    loading.value = true
    error.value = ''
    try {
      const data = await api.obtenerTruequesMultiples(busqueda)
      truequesMultiples.value = data.trueques_multiples || []
      return data
    } catch (err) {
      error.value = err.message || 'Error al cargar trueques multiples.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function actualizarEstadoTruequeMultiple(truequeId, estado) {
    try {
      const data = await api.actualizarEstadoTruequeMultiple(truequeId, estado)
      const idx = truequesMultiples.value.findIndex((t) => t.id === truequeId)
      if (idx !== -1 && data.trueque_multiple) truequesMultiples.value[idx] = data.trueque_multiple
      return data
    } catch (err) {
      error.value = err.message || 'Error al actualizar estado.'
      throw err
    }
  }

  async function eliminarTruequeMultiple(truequeId) {
    try {
      const data = await api.eliminarTruequeMultiple(truequeId)
      truequesMultiples.value = truequesMultiples.value.filter((t) => t.id !== truequeId)
      return data
    } catch (err) {
      error.value = err.message || 'Error al eliminar trueque multiple.'
      throw err
    }
  }

  // Resenas
  async function cargarResenas(busqueda = '') {
    loading.value = true
    error.value = ''
    try {
      const data = await api.obtenerResenas(busqueda)
      resenas.value = data.resenas || []
      return data
    } catch (err) {
      error.value = err.message || 'Error al cargar resenas.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function eliminarResena(resenaId) {
    try {
      const data = await api.eliminarResena(resenaId)
      resenas.value = resenas.value.filter((r) => r.id !== resenaId)
      return data
    } catch (err) {
      error.value = err.message || 'Error al eliminar resena.'
      throw err
    }
  }

  // Resenas Multiples
  async function cargarResenasMultiples(busqueda = '') {
    loading.value = true
    error.value = ''
    try {
      const data = await api.obtenerResenasMultiples(busqueda)
      resenasMultiples.value = data.resenas_multiples || []
      return data
    } catch (err) {
      error.value = err.message || 'Error al cargar resenas multiples.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function eliminarResenaMultiple(resenaId) {
    try {
      const data = await api.eliminarResenaMultiple(resenaId)
      resenasMultiples.value = resenasMultiples.value.filter((r) => r.id !== resenaId)
      return data
    } catch (err) {
      error.value = err.message || 'Error al eliminar resena multiple.'
      throw err
    }
  }

  // Saldos
  async function cargarSaldos(busqueda = '') {
    loading.value = true
    error.value = ''
    try {
      const data = await api.obtenerSaldos(busqueda)
      saldos.value = data.saldos || []
      return data
    } catch (err) {
      error.value = err.message || 'Error al cargar saldos.'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    dashboard, usuarios, publicaciones, trueques, truequesMultiples,
    resenas, resenasMultiples, saldos, loading, error,
    cargarDashboard, cargarUsuarios, toggleUsuario, cambiarRol, eliminarUsuario, editarUsuario,
    cargarPublicaciones, crearPublicacion, moderarPublicacion, eliminarPublicacion, editarPublicacion,
    cargarTrueques, actualizarEstadoTrueque, eliminarTrueque,
    cargarTruequesMultiples, actualizarEstadoTruequeMultiple, eliminarTruequeMultiple,
    cargarResenas, eliminarResena,
    cargarResenasMultiples, eliminarResenaMultiple,
    cargarSaldos,
  }
})
