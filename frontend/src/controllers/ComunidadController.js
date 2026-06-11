import BaseController from './BaseController.js'
import UsuarioRepository from '../repositories/UsuarioRepository.js'
import { ref, reactive } from 'vue'

/**
 * ComunidadController - Controlador para HU2: Directorio y perfiles públicos
 * Maneja toda la lógica de negocio de la comunidad del frontend
 * con estado reactivo y caché en memoria
 */
export default class ComunidadController extends BaseController {
  constructor(usuarioRepository = null) {
    super()
    this.usuarioRepository = usuarioRepository || new UsuarioRepository()
    
    // Estado reactivo de la comunidad
    this.miembros = ref([])
    this.vistaActual = ref('directorio') // 'directorio' o 'detalle'
    this.detallePerfil = ref(null)
    this.miembroSeleccionado = ref(null)
  }

  /**
   * Carga la lista de miembros de la comunidad
   * HU2: Visualizar directorio de miembros
   */
  async cargarComunidad(forceRefresh = false) {
    return this.execute(async () => {
      const comunidad = await this.usuarioRepository.obtenerComunidad(forceRefresh)
      
      // Actualizar estado reactivo
      this.miembros.value = comunidad.miembros || []
      this.vistaActual.value = 'directorio'
      
      return comunidad
    })
  }

  /**
   * Carga el perfil público de un miembro específico
   * HU2: Ver perfil público de otro miembro
   */
  async cargarPerfilUsuario(usuarioId, forceRefresh = false) {
    return this.execute(async () => {
      const perfil = await this.usuarioRepository.obtenerPerfilUsuario(usuarioId, forceRefresh)
      
      // Actualizar estado reactivo
      this.detallePerfil.value = perfil
      this.vistaActual.value = 'detalle'
      this.miembroSeleccionado.value = perfil.usuario
      
      return perfil
    })
  }

  /**
   * Cambia a la vista de detalle del miembro
   */
  verDetalle(miembro) {
    this.miembroSeleccionado.value = miembro
    return this.cargarPerfilUsuario(miembro.usuario.id)
  }

  /**
   * Vuelve al directorio
   */
  volverAlDirectorio() {
    this.vistaActual.value = 'directorio'
    this.detallePerfil.value = null
    this.miembroSeleccionado.value = null
  }

  /**
   * Retorna los talentos activos del perfil actual
   */
  getTalentosActivos() {
    if (!this.detallePerfil.value) return []
    return (this.detallePerfil.value.publicaciones || [])
      .filter(p => p.tipo === 'TALENTO' && p.esta_activa)
  }

  /**
   * Retorna las necesidades activas del perfil actual
   */
  getNecesidadesActivas() {
    if (!this.detallePerfil.value) return []
    return (this.detallePerfil.value.publicaciones || [])
      .filter(p => p.tipo === 'NECESIDAD' && p.esta_activa)
  }

  /**
   * Retorna las reseñas públicas del perfil actual
   */
  getResenasPublicas() {
    if (!this.detallePerfil.value) return []
    return this.detallePerfil.value.resenas || []
  }

  /**
   * Retorna el número de miembros activos
   */
  getTotalMiembrosActivos() {
    return this.miembros.value.filter(m => m.es_miembro_activo).length
  }

  /**
   * Verifica si se puede enviar una propuesta al miembro actual
   */
  puedeEnviarPropuesta(authController) {
    if (!authController.haySesionActiva()) {
      return false
    }

    const usuarioActual = authController.getUsuarioActual()
    if (!usuarioActual) {
      return false
    }

    // No puede enviarse propuesta a sí mismo
    if (this.miembroSeleccionado.value?.id === usuarioActual.id) {
      return false
    }

    return true
  }

  /**
   * Invalida la caché de la comunidad
   */
  invalidateComunidadCache() {
    this.usuarioRepository.invalidateComunidad()
  }

  /**
   * Invalida la caché de perfiles
   */
  invalidatePerfilCache(usuarioId) {
    if (usuarioId) {
      this.usuarioRepository.invalidatePerfil(usuarioId)
    } else {
      this.usuarioRepository.invalidateAll()
    }
  }

  /**
   * Invalida toda la caché de usuarios
   */
  invalidateAllCache() {
    this.usuarioRepository.invalidateAll()
  }

  /**
   * Retorna las iniciales de un nombre
   */
  getInitials(nombreReal, username) {
    if (nombreReal) {
      return nombreReal
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    }
    return username ? username.slice(0, 2).toUpperCase() : '??'
  }

  /**
   * Retorna un color de avatar basado en el username
   */
  getAvatarColor(username) {
    const colors = [
      '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
      '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    if (!username) return colors[0]
    const index = username
      .split('')
      .reduce((acc, char) => acc + char.charCodeAt(0), 0)
    return colors[index % colors.length]
  }

  /**
   * Formatea el promedio de estrellas
   */
  formatearEstrellas(promedio) {
    return (promedio || 5.0).toFixed(1)
  }

  /**
   * Retorna el nombre del calificador de una reseña
   */
  nombreCalificador(resena) {
    return resena.calificador?.username || 'Usuario'
  }
}
