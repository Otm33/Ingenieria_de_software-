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
  } = {}) {
    this.id = id
    this.username = username
    this.email = email
    this.nombreReal = nombre_real
    this.horasDeVida = Number(horas_de_vida)
    this.promedioEstrellas = Number(promedio_estrellas)
    this.esComercio = Boolean(es_comercio)
    // CAMBIO AUTH: estos campos controlan la visibilidad del menu administrativo.
    this.esStaff = Boolean(is_staff)
    this.esSuperusuario = Boolean(is_superuser)
  }

  get esAdmin() {
    return this.esStaff || this.esSuperusuario
  }

  // CAMBIO MODELO: centraliza el payload que exige el endpoint /api/registro/.
  static paraRegistro(formulario) {
    return {
      nombre_real: formulario.nombre_real?.trim(),
      email: formulario.email?.trim(),
      username: formulario.username?.trim(),
      password: formulario.password,
    }
  }
}
