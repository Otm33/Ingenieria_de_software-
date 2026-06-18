/**
 * Modelo de Dominio Frontend — Publicación (Talento o Necesidad).
 *
 * Capa: models/ (Dominio del frontend)
 *
 * Representa una publicación de la cartelera. Normaliza los datos
 * snake_case del backend a camelCase para Vue.
 *
 * Tipos: TALENTO (lo que ofrezco) | NECESIDAD (lo que busco)
 * Urgencias: NORMAL | ALTA | CRITICA
 *
 * Métodos de negocio espejo del backend:
 * - esTalento() / esNecesidad(): clasificación del tipo
 * - esUrgente() / esCritica(): prioridad de la publicación
 * - etiquetaTipo(), claseBadgeUrgencia(): helpers para renderizado UI
 * - coincideConCategoria(), coincideConUrgencia(): filtrado local
 *
 * Flujo: PublicacionApiService obtiene JSON → new Publicacion(data) → Store → Vista
 */
export default class Publicacion {
  // CAMBIO MODELO: normaliza cada publicacion recibida desde la BD via API Django.
  constructor({
    id = null,
    usuario = null,
    usuario_nombre_real = '',
    usuario_estrellas = 5,
    tipo = '',
    titulo = '',
    descripcion = '',
    categoria = '',
    urgencia = 'NORMAL',
    esta_activa = true,
  } = {}) {
    this.id = id
    this.usuario = usuario
    this.usuarioNombreReal = usuario_nombre_real
    this.usuarioEstrellas = Number(usuario_estrellas || 5)
    this.tipo = tipo
    this.titulo = titulo
    this.descripcion = descripcion
    this.categoria = categoria
    this.urgencia = urgencia
    this.estaActiva = Boolean(esta_activa)
  }

  // ===== MÉTODOS DE NEGOCIO =====

  /**
   * Verifica si esta publicación es un talento
   */
  esTalento() {
    return this.tipo === 'TALENTO'
  }

  /**
   * Verifica si esta publicación es una necesidad
   */
  esNecesidad() {
    return this.tipo === 'NECESIDAD'
  }

  /**
   * Verifica si la publicación tiene urgencia alta o crítica
   */
  esUrgente() {
    return this.urgencia === 'ALTA' || this.urgencia === 'CRITICA'
  }

  /**
   * Verifica si la publicación es crítica
   */
  esCritica() {
    return this.urgencia === 'CRITICA'
  }

  /**
   * Retorna la etiqueta de tipo para mostrar en UI
   */
  etiquetaTipo() {
    return this.esTalento() ? 'Talento' : 'Necesidad'
  }

  /**
   * Retorna la etiqueta de urgencia para mostrar en UI
   */
  etiquetaUrgencia() {
    const etiquetas = {
      'NORMAL': 'Normal',
      'ALTA': 'Urgencia Alta',
      'CRITICA': 'Necesidad Crítica'
    }
    return etiquetas[this.urgencia] || this.urgencia
  }

  /**
   * Retorna la clase CSS para el badge de urgencia
   */
  claseBadgeUrgencia() {
    const clases = {
      'NORMAL': 'badge--normal',
      'ALTA': 'badge--alta',
      'CRITICA': 'badge--critica'
    }
    return clases[this.urgencia] || 'badge--normal'
  }

  /**
   * Retorna la clase CSS para la tarjeta según urgencia
   */
  clasePorUrgencia() {
    const clases = {
      'NORMAL': '',
      'ALTA': 'service-card--urgente',
      'CRITICA': 'service-card--critica'
    }
    return clases[this.urgencia] || ''
  }

  /**
   * Verifica si la publicación coincide con la categoría dada
   */
  coincideConCategoria(categoria) {
    return this.categoria === categoria
  }

  /**
   * Verifica si la publicación coincide con alguna de las urgencias dadas
   */
  coincideConUrgencia(urgencias) {
    return urgencias.includes(this.urgencia)
  }
}
