import UserService from '../models/UserService.js'

export default class UserController {
  // CAMBIO CONTROLADOR: recibe una instancia del servicio para separar vista, logica y datos.
  constructor(service) {
    this.service = service
  }

  async validarEmail(email, esComercio = false) {
    return await this.service.validarEmail(email, esComercio)
  }

  // CAMBIO CONTROLADOR: la vista llama este metodo, el servicio decide como hablar con la BD.
  async registrarUsuario(payload) {
    return await this.service.registrarUsuario(payload)
  }

  // CAMBIO AUTH: la app pregunta al controlador si existe sesion al cargar /.
  async obtenerSesionActual() {
    return await this.service.obtenerSesionActual()
  }

  // CAMBIO AUTH: la vista no autentica directo; delega al servicio instanciado.
  async iniciarSesion(credenciales) {
    return await this.service.iniciarSesion(credenciales)
  }

  // CAMBIO AUTH: centraliza el cierre de sesion.
  async cerrarSesion() {
    return await this.service.cerrarSesion()
  }

  // CAMBIO CONTROLADOR: encapsula la carga CSV para que AdminCSV.vue no use HTTP directo.
  async cargarUsuariosAutorizados(archivo) {
    return await this.service.cargarUsuariosAutorizados(archivo)
  }

  // CAMBIO CONTROLADOR: encapsula filtros de cartelera y devuelve modelos Publicacion.
  async obtenerCartelera(filtros = {}) {
    return await this.service.obtenerCartelera(filtros)
  }

  async crearPublicacion(payload) {
    return await this.service.crearPublicacion(payload)
  }

  async obtenerMiPerfil() {
    return await this.service.obtenerMiPerfil()
  }

  async obtenerComunidad() {
    return await this.service.obtenerComunidad()
  }

  async obtenerPerfilUsuario(id) {
    return await this.service.obtenerPerfilUsuario(id)
  }

  async obtenerMisPublicaciones() {
    return await this.service.obtenerMisPublicaciones()
  }

  async actualizarEstadoPublicacion(id, estaActiva) {
    return await this.service.actualizarEstadoPublicacion(id, estaActiva)
  }

  async verificarCoincidenciaPorTitulo(publicacionId) {
    return await this.service.verificarCoincidenciaPorTitulo(publicacionId)
  }

  async obtenerMatches(publicacionId = null) {
    return await this.service.obtenerMatches(publicacionId)
  }

  get users() {
    return this.service.users
  }

  get publicaciones() {
    return this.service.publicaciones
  }
}
