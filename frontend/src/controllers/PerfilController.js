import BaseController from './BaseController.js'
import UsuarioRepository from '../repositories/UsuarioRepository.js'
import PublicacionRepository from '../repositories/PublicacionRepository.js'
import TruequeRepository from '../repositories/TruequeRepository.js'
import ResenaRepository from '../repositories/ResenaRepository.js'
import { ref, reactive } from 'vue'

/**
 * PerfilController - Controlador para HU2: Mi perfil
 * Maneja toda la lógica de negocio del perfil del usuario actual
 * con estado reactivo y caché en memoria
 */
export default class PerfilController extends BaseController {
  constructor(
    usuarioRepository = null,
    publicacionRepository = null,
    truequeRepository = null,
    resenaRepository = null
  ) {
    super()
    this.usuarioRepository = usuarioRepository || new UsuarioRepository()
    this.publicacionRepository = publicacionRepository || new PublicacionRepository()
    this.truequeRepository = truequeRepository || new TruequeRepository()
    this.resenaRepository = resenaRepository || new ResenaRepository()
    
    // Estado reactivo del perfil
    this.datosPerfil = ref(null)
    this.publicacionesActivas = ref([])
    this.publicacionesPausadas = ref([])
    this.misTrueques = ref([])
    this.procesandoTruequeId = ref(null)
    this.feedbackTrueque = reactive({})
    this.feedbackTruequeOk = reactive({})
  }

  /**
   * Carga el perfil del usuario actual
   * HU2: Visualizar mi perfil
   */
  async cargarMiPerfil(forceRefresh = false) {
    return this.execute(async () => {
      const perfil = await this.usuarioRepository.obtenerMiPerfil(forceRefresh)
      
      // Actualizar estado reactivo
      this.datosPerfil.value = perfil
      
      // Separar publicaciones por estado
      const publicaciones = perfil.publicaciones || []
      this.publicacionesActivas.value = publicaciones.filter(p => p.esta_activa)
      this.publicacionesPausadas.value = publicaciones.filter(p => !p.esta_activa)
      
      return perfil
    })
  }

  /**
   * Carga los trueques del usuario actual
   * HU4: Visualizar mis trueques
   */
  async cargarMisTrueques(forceRefresh = false) {
    return this.execute(async () => {
      const resultado = await this.truequeRepository.obtenerMisTrueques(forceRefresh)
      this.misTrueques.value = resultado.trueques
      return resultado
    })
  }

  /**
   * Finaliza un trueque
   * HU4: Confirmar finalización de trueque
   */
  async finalizarTrueque(truequeId, authController = null) {
    return this.execute(async () => {
      if (authController) {
        authController.requireAuth()
      }
      
      this.procesandoTruequeId.value = truequeId
      this.feedbackTrueque[truequeId] = null
      
      try {
        const resultado = await this.truequeRepository.finalizarTrueque(truequeId)
        
        // Actualizar estado local
        const trueque = this.misTrueques.value.find(t => t.id === truequeId)
        if (trueque) {
          trueque.estado = 'FINALIZADO'
          trueque.emisor_confirmado = true
          trueque.receptor_confirmado = true
        }
        
        this.feedbackTrueque[truequeId] = resultado.mensaje
        this.feedbackTruequeOk[truequeId] = true
        
        // Invalidar caché
        this.truequeRepository.invalidateMisTrueques()
        
        return resultado
      } catch (error) {
        this.feedbackTrueque[truequeId] = error.message
        this.feedbackTruequeOk[truequeId] = false
        throw error
      } finally {
        this.procesandoTruequeId.value = null
      }
    })
  }

  /**
   * Retorna las iniciales del usuario
   */
  getInitials() {
    if (!this.datosPerfil.value?.usuario) return '??'
    const usuario = this.datosPerfil.value.usuario
    if (usuario.nombre_real) {
      return usuario.nombre_real
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    }
    return usuario.username.slice(0, 2).toUpperCase()
  }

  /**
   * Retorna un color de avatar
   */
  getAvatarColor() {
    if (!this.datosPerfil.value?.usuario) return '#FF6B6B'
    const username = this.datosPerfil.value.usuario.username
    const colors = [
      '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
      '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    const index = username
      .split('')
      .reduce((acc, char) => acc + char.charCodeAt(0), 0)
    return colors[index % colors.length]
  }

  /**
   * Verifica si es miembro activo
   */
  esMiembroActivo() {
    return this.datosPerfil.value?.es_miembro_activo || false
  }

  /**
   * Retorna el promedio de estrellas
   */
  getPromedioEstrellas() {
    return this.datosPerfil.value?.usuario?.promedio_estrellas || 5.0
  }

  /**
   * Retorna el número de reseñas
   */
  getCantidadResenas() {
    return (this.datosPerfil.value?.resenas_recibidas || []).length
  }

  /**
   * Retorna el nombre del calificador de una reseña
   */
  nombreCalificador(resena) {
    return resena.calificador?.username || 'Usuario'
  }

  async obtenerMiPerfil(forceRefresh = false) {
    return this.cargarMiPerfil(forceRefresh)
  }

  /**
   * Invalida toda la caché del perfil
   */
  invalidateAllCache() {
    this.usuarioRepository.invalidateMiPerfil()
    this.publicacionRepository.invalidateMisPublicaciones()
    this.truequeRepository.invalidateMisTrueques()
  }

  /**
   * Limpia el feedback de trueques
   */
  limpiarFeedbackTrueque(truequeId) {
    delete this.feedbackTrueque[truequeId]
    delete this.feedbackTruequeOk[truequeId]
  }
}
