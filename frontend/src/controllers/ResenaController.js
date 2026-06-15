import BaseController from './BaseController.js'
import ResenaRepository from '../repositories/ResenaRepository.js'
import { ref, reactive } from 'vue'

/**
 * ResenaController - Controlador para HU4: Calificaciones y reseñas
 * Maneja toda la lógica de negocio de reseñas del frontend
 * con estado reactivo y validaciones
 */
export default class ResenaController extends BaseController {
  constructor(resenaRepository = null) {
    super()
    this.resenaRepository = resenaRepository || new ResenaRepository()
    
    // Estado reactivo de reseñas
    this.formularioResena = reactive({
      truequeId: null,
      estrellas: 5,
      comentario: ''
    })
    this.mostrarModalResena = ref(false)
    this.truequeSeleccionado = ref(null)
  }

  /**
   * Abre el modal de reseña para un trueque específico
   */
  abrirResena(trueque) {
    this.truequeSeleccionado.value = trueque
    this.formularioResena.truequeId = trueque.id
    this.formularioResena.estrellas = 5
    this.formularioResena.comentario = ''
    this.mostrarModalResena.value = true
  }

  /**
   * Cierra el modal de reseña
   */
  cerrarResena() {
    this.mostrarModalResena.value = false
    this.truequeSeleccionado.value = null
    this.limpiarFormulario()
  }

  /**
   * Registra una reseña
   * HU4: Dejar reseña después de un trueque
   */
  async registrarResena(authController) {
    return this.execute(async () => {
      authController.requireAuth()
      
      // Validaciones frontend
      if (!this.formularioResena.truequeId) {
        throw new Error('El trueque es requerido.')
      }

      if (!this.formularioResena.estrellas || this.formularioResena.estrellas < 1 || this.formularioResena.estrellas > 5) {
        throw new Error('La calificación debe estar entre 1 y 5 estrellas.')
      }

      if (!this.formularioResena.comentario?.trim()) {
        throw new Error('El comentario es requerido.')
      }

      if (this.formularioResena.comentario.length < 10) {
        throw new Error('El comentario debe tener al menos 10 caracteres.')
      }

      if (this.formularioResena.comentario.length > 500) {
        throw new Error('El comentario no puede exceder 500 caracteres.')
      }

      const resultado = await this.resenaRepository.registrarResena(
        this.formularioResena.truequeId,
        this.formularioResena.estrellas,
        this.formularioResena.comentario
      )
      
      // Invalidar caché
      this.resenaRepository.invalidateNotificaciones()
      
      // Cerrar modal y limpiar formulario
      this.cerrarResena()
      
      return resultado
    })
  }

  /**
   * Actualiza el número de estrellas en el formulario
   */
  actualizarEstrellas(estrellas) {
    this.formularioResena.estrellas = estrellas
  }

  /**
   * Actualiza el comentario en el formulario
   */
  actualizarComentario(comentario) {
    this.formularioResena.comentario = comentario
  }

  /**
   * Limpia el formulario de reseña
   */
  limpiarFormulario() {
    this.formularioResena.truequeId = null
    this.formularioResena.estrellas = 5
    this.formularioResena.comentario = ''
  }

  /**
   * Verifica si el formulario es válido
   */
  formularioValido() {
    return (
      this.formularioResena.truequeId &&
      this.formularioResena.estrellas >= 1 &&
      this.formularioResena.estrellas <= 5 &&
      this.formularioResena.comentario?.trim().length >= 10 &&
      this.formularioResena.comentario.length <= 500
    )
  }

  /**
   * Retorna el número de caracteres del comentario
   */
  getLongitudComentario() {
    return this.formularioResena.comentario?.length || 0
  }

  /**
   * Retorna el mensaje de longitud restante
   */
  getMensajeLongitud() {
    const longitud = this.getLongitudComentario()
    return `${longitud}/500 caracteres`
  }

  async registrarResena(truequeId, estrellas, comentario) {
    return this.execute(async () => {
      if (!truequeId) {
        throw new Error('El trueque es requerido.')
      }
      if (!estrellas || estrellas < 1 || estrellas > 5) {
        throw new Error('La calificación debe estar entre 1 y 5 estrellas.')
      }
      if (!comentario?.trim()) {
        throw new Error('El comentario es requerido.')
      }
      if (comentario.length < 10) {
        throw new Error('El comentario debe tener al menos 10 caracteres.')
      }
      if (comentario.length > 500) {
        throw new Error('El comentario no puede exceder 500 caracteres.')
      }

      return await this.resenaRepository.registrarResena(truequeId, estrellas, comentario)
    })
  }

  /**
   * Invalida toda la caché de reseñas
   */
  invalidateAllCache() {
    this.resenaRepository.invalidateAll()
  }
}
