import BaseController from './BaseController.js'
import TruequeRepository from '../repositories/TruequeRepository.js'
import ResenaRepository from '../repositories/ResenaRepository.js'
import { ref, reactive } from 'vue'

/**
 * TruequeController - Controlador para HU4: Trueques y propuestas
 * Maneja toda la lógica de negocio de trueques del frontend
 * con estado reactivo y caché en memoria
 */
export default class TruequeController extends BaseController {
  constructor(
    truequeRepository = null,
    resenaRepository = null
  ) {
    super()
    this.truequeRepository = truequeRepository || new TruequeRepository()
    this.resenaRepository = resenaRepository || new ResenaRepository()
    
    // Estado reactivo de trueques
    this.matches = ref([])
    this.mensajeMatches = ref('')
    this.cantidadMatches = ref(0)
    this.notificaciones = ref([])
    this.cantidadNotificaciones = ref(0)
    this.mostrarSelectorModo = ref(false)
    this.modoPropuesta = ref(null)
  }

  /**
   * Verifica coincidencias por título de publicación
   * HU4: Detección de matches
   */
  async verificarCoincidenciaPorTitulo(publicacionId) {
    return this.execute(async () => {
      const resultado = await this.truequeRepository.verificarCoincidenciaPorTitulo(publicacionId)
      return resultado
    })
  }

  /**
   * Obtiene los matches para el usuario
   * HU4: Verificar matches disponibles
   */
  async obtenerMatches(publicacionId = null, forceRefresh = false) {
    return this.execute(async () => {
      const resultado = await this.truequeRepository.obtenerMatchesEnriquecidos(
        publicacionId,
        forceRefresh,
      )

      this.matches.value = resultado.matches
      this.mensajeMatches.value = resultado.mensaje
      this.cantidadMatches.value = resultado.cantidad

      return resultado
    })
  }

  async obtenerMatchesEnriquecidos(publicacionId = null, forceRefresh = false) {
    return this.obtenerMatches(publicacionId, forceRefresh)
  }

  /**
   * Crea una propuesta de trueque
   * HU4: Enviar propuesta de trueque
   */
  async crearPropuesta(receptorId, publicacionEmisorId, publicacionReceptorId) {
    return this.execute(async () => {
      if (!receptorId) {
        throw new Error('El receptor es requerido.')
      }

      const trueque = await this.truequeRepository.crearPropuesta(
        receptorId,
        publicacionEmisorId,
        publicacionReceptorId
      )
      
      // Invalidar caché de matches
      this.truequeRepository.invalidateMatches(publicacionEmisorId)
      this.truequeRepository.invalidateMatches()
      
      return trueque
    })
  }

  /**
   * Responde a una propuesta de trueque
   * HU4: Aceptar o rechazar propuesta
   */
  async responderPropuesta(truequeId, accion) {
    return this.execute(async () => {
      if (!['ACEPTAR', 'RECHAZAR'].includes(accion)) {
        throw new Error('La acción debe ser ACEPTAR o RECHAZAR.')
      }

      const resultado = await this.truequeRepository.responderPropuesta(truequeId, accion)
      
      // Invalidar caché
      this.truequeRepository.invalidateMisTrueques()
      this.resenaRepository.invalidateNotificaciones()
      
      return resultado
    })
  }

  /**
   * Finaliza un trueque
   * HU4: Confirmar finalización de trueque
   */
  async finalizarTrueque(truequeId) {
    return this.execute(async () => {
      const resultado = await this.truequeRepository.finalizarTrueque(truequeId)
      
      // Invalidar caché
      this.truequeRepository.invalidateMisTrueques()
      this.resenaRepository.invalidateNotificaciones()
      
      return resultado
    })
  }

  /**
   * Carga las notificaciones del usuario
   * HU4: Ver notificaciones de propuestas
   */
  async cargarNotificaciones(incluirLeidas = false, forceRefresh = false) {
    return this.execute(async () => {
      const resultado = await this.resenaRepository.obtenerNotificaciones(
        incluirLeidas,
        forceRefresh
      )
      
      // Actualizar estado reactivo
      this.notificaciones.value = resultado.notificaciones
      this.cantidadNotificaciones.value = resultado.cantidad
      
      return resultado
    })
  }

  /**
   * Marca una notificación como leída
   */
  async marcarNotificacionLeida(notificacionId) {
    return this.execute(async () => {
      await this.resenaRepository.marcarNotificacionLeida(notificacionId)
      
      // Actualizar estado local
      const notificacion = this.notificaciones.value.find(n => n.id === notificacionId)
      if (notificacion) {
        notificacion.estado = 'LEIDA'
        notificacion.leida_el = new Date().toISOString()
      }
      
      // Invalidar caché
      this.resenaRepository.invalidateNotificaciones()
    })
  }

  /**
   * Marca todas las notificaciones de un trueque como leídas
   */
  async marcarNotificacionesTruequeLeidas(truequeId) {
    return this.execute(async () => {
      await this.resenaRepository.marcarNotificacionesTruequeLeidas(truequeId)
      
      // Actualizar estado local
      this.notificaciones.value = this.notificaciones.value.filter(
        n => n.trueque?.id !== truequeId || n.estado === 'LEIDA'
      )
      
      // Invalidar caché
      this.resenaRepository.invalidateNotificaciones()
    })
  }

  /**
   * Abre el selector de modo de propuesta
   */
  abrirSelectorModo() {
    this.mostrarSelectorModo.value = true
    this.modoPropuesta.value = null
  }

  /**
   * Cierra el selector de modo de propuesta
   */
  cerrarSelectorModo() {
    this.mostrarSelectorModo.value = false
    this.modoPropuesta.value = null
  }

  /**
   * Elige el modo de propuesta
   */
  elegirModoPropuesta(modo) {
    this.modoPropuesta.value = modo
    this.mostrarSelectorModo.value = false
  }

  async validarCodigoTrueque(truequeId, codigo) {
    return this.execute(async () => {
      const resultado = await this.truequeRepository.validarCodigo(truequeId, codigo)
      this.truequeRepository.invalidateMisTrueques()
      this.resenaRepository.invalidateNotificaciones()
      return resultado
    })
  }

  async obtenerMisTrueques(forceRefresh = false) {
    return this.execute(async () => {
      return await this.truequeRepository.obtenerMisTrueques(forceRefresh)
    })
  }

  async obtenerNotificaciones(incluirLeidas = false, forceRefresh = false) {
    return this.cargarNotificaciones(incluirLeidas, forceRefresh)
  }

  async responderPropuestaMultiple(truequeMultipleId, accion) {
    return this.execute(async () => {
      const resultado = await this.truequeRepository.responderPropuestaMultiple(
        truequeMultipleId,
        accion,
      )
      this.resenaRepository.invalidateNotificaciones()
      return resultado
    })
  }

  async obtenerMisTruequesMultiples(forceRefresh = false) {
    return this.execute(async () => {
      return await this.truequeRepository.obtenerMisTruequesMultiples(forceRefresh)
    })
  }

  async validarCodigoParMultiple(truequeMultipleId, par, codigo) {
    return this.execute(async () => {
      return await this.truequeRepository.validarCodigoParMultiple(
        truequeMultipleId,
        par,
        codigo,
      )
    })
  }

  async registrarResenaMultiple(truequeMultipleId, calificadoId, estrellas, comentario) {
    return this.execute(async () => {
      return await this.resenaRepository.registrarResenaMultiple(
        truequeMultipleId,
        calificadoId,
        estrellas,
        comentario,
      )
    })
  }

  /**
   * Invalida toda la caché de trueques
   */
  invalidateAllCache() {
    this.truequeRepository.invalidateAll()
    this.resenaRepository.invalidateAll()
  }
}
