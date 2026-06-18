/**
 * Modelo de Dominio Frontend — Usuario.
 *
 * Capa: models/ (Dominio del frontend)
 *
 * Representa al usuario autenticado con sus datos del backend Django.
 * Normaliza campos snake_case (horas_de_vida) a camelCase (horasDeVida).
 *
 * Métodos de negocio espejo del backend:
 * - tieneSaldoCritico(): verifica si horasDeVida < -10 (restricción de publicación)
 * - esComercioActivo(): verifica si es comercio + staff
 * - getIniciales() / getAvatarColor(): para renderizar avatares en la UI
 *
 * Método estático paraRegistro(): genera el payload para POST /api/registro/
 *
 * Flujo: AuthApiService obtiene JSON → new User(data) → useAuthStore → Vistas
 */
export default class User {
  // CAMBIO MODELO: esta clase representa el usuario que llega desde Django, no datos simulados.
  constructor({
    id = null,
    username = '',
    email = '',
    nombre_real = '',
    horas_de_vida = 0,
    promedio_estrellas = 5,
    es_comercio = false,
    is_staff = false,
    is_superuser = false,
    esStaff = false,
    esSuperusuario = false,
  } = {}) {
    this.id = id
    this.username = username
    this.email = email
    this.nombreReal = nombre_real
    this.horasDeVida = Number(horas_de_vida)
    this.promedioEstrellas = Number(promedio_estrellas)
    this.esComercio = Boolean(es_comercio)
    // CAMBIO AUTH: estos campos controlan la visibilidad del menu administrativo.
    // Soporta ambos nombres: is_staff/is_superuser (formato Django) y esStaff/esSuperusuario (formato backend)
    this.esStaff = Boolean(esStaff !== undefined ? esStaff : is_staff)
    this.esSuperusuario = Boolean(esSuperusuario !== undefined ? esSuperusuario : is_superuser)
  }

  get esAdmin() {
    return this.esStaff || this.esSuperusuario
  }

  // ===== MÉTODOS DE NEGOCIO =====

  /**
   * Verifica si el usuario tiene saldo crítico (< -10 horas)
   */
  tieneSaldoCritico() {
    return this.horasDeVida < -10.0
  }

  /**
   * Verifica si el usuario puede modificar publicaciones
   */
  puedeModificarPublicaciones() {
    return !this.tieneSaldoCritico()
  }

  /**
   * Verifica si es un comercio activo
   */
  esComercioActivo() {
    return this.esComercio && this.esStaff
  }

  /**
   * Verifica si puede realizar trueques
   */
  puedeRealizarTrueque() {
    return !this.tieneSaldoCritico()
  }

  /**
   * Retorna las iniciales del nombre para el avatar
   */
  getIniciales() {
    if (this.nombreReal) {
      return this.nombreReal
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    }
    return this.username.slice(0, 2).toUpperCase()
  }

  /**
   * Retorna un color de avatar basado en el username
   */
  getAvatarColor() {
    const colors = [
      '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
      '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    const index = this.username
      .split('')
      .reduce((acc, char) => acc + char.charCodeAt(0), 0)
    return colors[index % colors.length]
  }

  /**
   * Formatea el promedio de estrellas
   */
  formatearEstrellas() {
    return this.promedioEstrellas.toFixed(1)
  }

  // CAMBIO MODELO: centraliza el payload que exige el endpoint /api/registro/.
  static paraRegistro(formulario) {
    return {
      nombre_real: formulario.nombre_real?.trim(),
      email: formulario.email?.trim(),
      username: formulario.username?.trim(),
      password: formulario.password,
      es_comercio: Boolean(formulario.es_comercio),
    }
  }
}
