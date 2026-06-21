/**
 * Modelo de Dominio Frontend — Trueque (Acuerdo de intercambio).
 *
 * Capa: models/ (Dominio del frontend)
 *
 * Representa un acuerdo de intercambio entre dos usuarios.
 * Normaliza los datos snake_case del backend a camelCase para Vue.
 *
 * Contiene métodos de negocio duplicados del backend para validación local:
 * - Estados: PENDIENTE → EN_CURSO → ACEPTADO → FINALIZADO (o RECHAZADO)
 * - Verificar si el usuario puede confirmar la finalización
 * - Calcular el impacto en horas de vida para cada participante
 * - Generar etiquetas y clases CSS según el estado
 *
 * Flujo: TruequeApiService obtiene JSON → new Trueque(data) → Pinia Store → Vista
 */
export default class Trueque {
  constructor({
    id = null,
    emisor = null,
    receptor = null,
    estado = 'PENDIENTE',
    publicacion_emisor = null,
    publicacion_receptor = null,
    emisor_confirmado = false,
    receptor_confirmado = false,
    creado_el = null,
    actualizado_el = null,
  } = {}) {
    this.id = id
    this.emisor = emisor
    this.receptor = receptor
    this.estado = estado
    this.publicacionEmisor = publicacion_emisor
    this.publicacionReceptor = publicacion_receptor
    this.emisorConfirmado = emisor_confirmado
    this.receptorConfirmado = receptor_confirmado
    this.creadoEl = creado_el
    this.actualizadoEl = actualizado_el
  }

  // ===== MÉTODOS DE NEGOCIO =====

  /**
   * Verifica si el trueque está en estado pendiente
   */
  estaPendiente() {
    return this.estado === 'PENDIENTE'
  }

  /**
   * Verifica si el trueque ha sido aceptado
   */
  estaAceptado() {
    return this.estado === 'ACEPTADO'
  }

  /**
   * Verifica si el trueque ha sido rechazado
   */
  estaRechazado() {
    return this.estado === 'RECHAZADO'
  }

  /**
   * Verifica si el trueque está en curso
   */
  estaEnCurso() {
    return this.estado === 'EN_CURSO'
  }

  /**
   * Verifica si el trueque está finalizado
   */
  estaFinalizado() {
    return this.estado === 'FINALIZADO'
  }

  /**
   * Verifica si ambas partes han confirmado
   */
  ambasPartesConfirmaron() {
    return this.emisorConfirmado && this.receptorConfirmado
  }

  /**
   * Verifica si es un intercambio mutuo
   */
  esIntercambioMutuo() {
    if (!this.publicacionEmisor || !this.publicacionReceptor) {
      return false
    }
    return this.publicacionEmisor.tipo === this.publicacionReceptor.tipo
  }

  /**
   * Calcula el impacto en horas para un usuario
   */
  calcularImpactoHoras(usuarioId) {
    if (this.esIntercambioMutuo()) {
      return 0
    }

    if (usuarioId === this.emisor?.id) {
      if (this.publicacionEmisor?.tipo === 'NECESIDAD') {
        return -1
      } else if (this.publicacionEmisor?.tipo === 'TALENTO') {
        return 1
      }
    }

    if (usuarioId === this.receptor?.id) {
      if (this.publicacionReceptor?.tipo === 'TALENTO') {
        return 1
      } else if (this.publicacionReceptor?.tipo === 'NECESIDAD') {
        return -1
      }
    }

    return 0
  }

  /**
   * Retorna la etiqueta de estado para mostrar en UI
   */
  etiquetaEstado() {
    const etiquetas = {
      'PENDIENTE': 'Pendiente',
      'EN_CURSO': 'En Curso',
      'ACEPTADO': 'Aceptado',
      'RECHAZADO': 'Rechazado',
      'FINALIZADO': 'Finalizado'
    }
    return etiquetas[this.estado] || this.estado
  }

  /**
   * Retorna la clase CSS para el estado
   */
  claseEstado() {
    const clases = {
      'PENDIENTE': 'trueque-card--pendiente',
      'ACEPTADO': 'trueque-card--aceptado',
      'RECHAZADO': 'trueque-card--rechazado',
      'EN_CURSO': 'trueque-card--en-curso',
      'FINALIZADO': 'trueque-card--finalizado'
    }
    return clases[this.estado] || ''
  }

  /**
   * Verifica si el usuario puede confirmar la finalización
   */
  puedeConfirmar(usuarioId) {
    return this.estado === 'EN_CURSO'
  }

  /**
   * Verifica si el trueque está en estado aceptado (código ingresado, pendiente de reseñas)
   */
  estaAceptado() {
    return this.estado === 'ACEPTADO'
  }

  /**
   * Verifica si el trueque tiene una reseña pendiente para el usuario
   */
  pendienteResena(usuarioId) {
    return this.estaAceptado() && !this.emisorConfirmado
  }

  /**
   * Retorna el título de la publicación del emisor
   */
  tituloPublicacionEmisor() {
    return this.publicacionEmisor?.titulo || 'Sin publicación'
  }

  /**
   * Retorna el título de la publicación del receptor
   */
  tituloPublicacionReceptor() {
    return this.publicacionReceptor?.titulo || 'Sin publicación'
  }

  /**
   * Retorna la etiqueta para la oferta propia
   */
  etiquetaOfertaPropia(usuarioId) {
    if (usuarioId === this.emisor?.id && this.publicacionEmisor) {
      return this.publicacionEmisor.tipo === 'TALENTO' ? 'Ofrezco' : 'Necesito'
    }
    if (usuarioId === this.receptor?.id && this.publicacionReceptor) {
      return this.publicacionReceptor.tipo === 'TALENTO' ? 'Ofrezco' : 'Necesito'
    }
    return null
  }

  /**
   * Retorna la etiqueta para la oferta de la contraparte
   */
  etiquetaOfertaContraparte(usuarioId) {
    if (usuarioId === this.emisor?.id && this.publicacionReceptor) {
      return this.publicacionReceptor.tipo === 'TALENTO' ? 'Ofrece' : 'Necesita'
    }
    if (usuarioId === this.receptor?.id && this.publicacionEmisor) {
      return this.publicacionEmisor.tipo === 'TALENTO' ? 'Ofrece' : 'Necesita'
    }
    return null
  }
}
