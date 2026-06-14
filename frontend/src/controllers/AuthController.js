import BaseController from './BaseController.js'
import User from '../models/User.js'
import Publicacion from '../models/Publicacion.js'

export default class AuthController extends BaseController {
  constructor(service) {
    super()
    this.service = service
  }

  validarCredencialesLogin(credenciales) {
    if (!credenciales?.username?.trim()) {
      throw new Error('El usuario es obligatorio.')
    }
    if (!credenciales?.password) {
      throw new Error('La contrasena es obligatoria.')
    }
  }

  validarPaso2(form) {
    if (form.password !== form.password_confirm) {
      throw new Error('Las contrasenas no coinciden.')
    }
    if (!form.password || form.password.length < 8) {
      throw new Error('La contrasena debe tener al menos 8 caracteres.')
    }
  }

  validarPasoPerfilComercial(form) {
    const nombre = form.nombre_real?.trim()
    if (!nombre || nombre.length < 2) {
      throw new Error('El nombre del comercio es obligatorio (minimo 2 caracteres).')
    }
  }

  validarPasoPerfilVecino(form) {
    if (!form.categoria?.trim()) {
      throw new Error('La categoria del talento es obligatoria.')
    }
    if (!form.titulo?.trim()) {
      throw new Error('El titulo del talento es obligatorio.')
    }
    if (!form.descripcion?.trim()) {
      throw new Error('La descripcion del talento es obligatoria.')
    }
    if (!form.nombre_real?.trim()) {
      throw new Error('El nombre real es obligatorio.')
    }
  }

  async validarEmail(email, esComercio = false) {
    return this.execute(() => this.service.validarEmail(email, esComercio))
  }

  async validarPasoCredenciales(form) {
    return this.execute(async () => {
      this.validarPaso2(form)
      return { ok: true }
    })
  }

  async registrarUsuario(payload) {
    return this.execute(async () => {
      const data = await this.service.registrarUsuario(User.paraRegistro(payload))
      return new User(data)
    })
  }

  async obtenerSesionActual() {
    return this.execute(async () => {
      const data = await this.service.obtenerSesionActual()
      return data.autenticado ? new User(data.usuario) : null
    })
  }

  async iniciarSesion(credenciales) {
    return this.execute(async () => {
      this.validarCredencialesLogin(credenciales)
      const data = await this.service.iniciarSesion({
        username: credenciales.username?.trim(),
        password: credenciales.password,
      })
      return new User(data.usuario)
    })
  }

  async cerrarSesion() {
    return this.execute(() => this.service.cerrarSesion())
  }

  async procesarSesionPostRegistro(credenciales) {
    return this.execute(async () => {
      if (credenciales.esNuevoMiembro) {
        const sesion = await this.service.obtenerSesionActual()
        if (sesion.autenticado) {
          return new User(sesion.usuario)
        }
        this.validarCredencialesLogin(credenciales)
        const data = await this.service.iniciarSesion({
          username: credenciales.username?.trim(),
          password: credenciales.password,
        })
        return new User(data.usuario)
      }

      this.validarCredencialesLogin(credenciales)
      const data = await this.service.iniciarSesion({
        username: credenciales.username?.trim(),
        password: credenciales.password,
      })
      return new User(data.usuario)
    })
  }

  async _registrarCuenta(form, esComercio) {
    await this.service.registrarUsuario(User.paraRegistro({
      nombre_real: form.nombre_real,
      email: form.email,
      username: form.username,
      password: form.password,
      es_comercio: esComercio,
    }))

    const loginData = await this.service.iniciarSesion({
      username: form.username?.trim(),
      password: form.password,
    })
    return new User(loginData.usuario)
  }

  async completarRegistroNuevoMiembro(form, esComercio, carteleraController) {
    return this.execute(async () => {
      if (esComercio) {
        this.validarPasoPerfilComercial(form)
        return this._registrarCuenta(form, true)
      }

      this.validarPasoPerfilVecino(form)
      const usuario = await this._registrarCuenta(form, false)

      await carteleraController.crearPublicacion({
        tipo: 'TALENTO',
        titulo: form.titulo,
        descripcion: form.descripcion,
        categoria: form.categoria,
        urgencia: 'NORMAL',
      })

      return usuario
    })
  }

  async obtenerMiPerfil() {
    return this.execute(async () => {
      const data = await this.service.obtenerMiPerfil()
      return this._mapearPerfil(data)
    })
  }

  async obtenerPerfilUsuario(id) {
    return this.execute(async () => {
      const data = await this.service.obtenerPerfilUsuario(id)
      return this._mapearPerfil(data)
    })
  }

  _mapearPerfil(data) {
    if (!data) return data

    const publicaciones = Array.isArray(data.publicaciones)
      ? data.publicaciones.map((publicacion) => new Publicacion(publicacion))
      : data.publicaciones

    return {
      ...data,
      publicaciones,
    }
  }
}
