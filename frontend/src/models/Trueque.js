import Publicacion from './Publicacion.js'

export default class Trueque {
  constructor(data = {}) {
    this.id = data.id ?? null
    this.emisor = data.emisor ?? null
    this.receptor = data.receptor ?? null
    this.emisor_nombre = data.emisor_nombre ?? ''
    this.receptor_nombre = data.receptor_nombre ?? ''
    this.estado = data.estado ?? 'PENDIENTE'
    this.publicacion_emisor = data.publicacion_emisor
      ? new Publicacion(data.publicacion_emisor)
      : null
    this.publicacion_receptor = data.publicacion_receptor
      ? new Publicacion(data.publicacion_receptor)
      : null
    this.emisor_confirmado = Boolean(data.emisor_confirmado)
    this.receptor_confirmado = Boolean(data.receptor_confirmado)
    this.puede_confirmar = Boolean(data.puede_confirmar)
    this.pendiente_resena = Boolean(data.pendiente_resena)
    this.es_intercambio_mutuo = Boolean(data.es_intercambio_mutuo)
    this.impacto_horas = data.impacto_horas ?? 0
    this.oferta_propia_titulo = data.oferta_propia_titulo ?? null
    this.oferta_contraparte_titulo = data.oferta_contraparte_titulo ?? null
    this.creado_el = data.creado_el ?? null
    this.actualizado_el = data.actualizado_el ?? null
  }

  static fromApi(data) {
    return new Trueque(data)
  }

  estaPendiente() {
    return this.estado === 'PENDIENTE'
  }

  estaAceptado() {
    return this.estado === 'ACEPTADO'
  }

  estaFinalizado() {
    return this.estado === 'FINALIZADO'
  }

  estaRechazado() {
    return this.estado === 'RECHAZADO'
  }

  etiquetaEstado() {
    const etiquetas = {
      PENDIENTE: 'Pendiente',
      ACEPTADO: 'Aceptado',
      RECHAZADO: 'Rechazado',
      FINALIZADO: 'Finalizado',
    }
    return etiquetas[this.estado] || this.estado
  }

  claseEstado() {
    const clases = {
      ACEPTADO: 'trueque-card__estado--aceptado',
      FINALIZADO: 'trueque-card__estado--finalizado',
      RECHAZADO: 'trueque-card__estado--rechazado',
      PENDIENTE: 'trueque-card__estado--pendiente',
    }
    return clases[this.estado] || 'trueque-card__estado--pendiente'
  }

  nombreContraparte(usuarioId) {
    if (Number(this.emisor) === Number(usuarioId)) {
      return this.receptor_nombre
    }
    return this.emisor_nombre
  }
}
