import BaseController from './BaseController.js'
import Publicacion from '../models/Publicacion.js'

export default class CarteleraController extends BaseController {
  constructor(service) {
    super()
    this.service = service
    this._publicaciones = []
  }

  validarFormularioPublicacion(form) {
    if (!form?.tipo || !['TALENTO', 'NECESIDAD'].includes(form.tipo)) {
      throw new Error('Selecciona un tipo de publicacion valido.')
    }
    if (!form.categoria?.trim()) {
      throw new Error('Selecciona una categoria.')
    }
    if (!form.titulo?.trim()) {
      throw new Error('Selecciona un titulo.')
    }
    if (!form.descripcion?.trim()) {
      throw new Error('La descripcion es obligatoria.')
    }
    if (form.tipo === 'NECESIDAD' && !form.urgencia) {
      throw new Error('Selecciona el nivel de urgencia.')
    }
  }

  _normalizarPayloadPublicacion(form) {
    const payload = {
      tipo: form.tipo,
      titulo: form.titulo?.trim(),
      descripcion: form.descripcion?.trim(),
      categoria: form.categoria?.trim(),
      urgencia: form.tipo === 'TALENTO' ? 'NORMAL' : form.urgencia,
    }
    this.validarFormularioPublicacion(payload)
    return payload
  }

  async obtenerCartelera(filtros = {}) {
    return this.execute(async () => {
      const data = await this.service.obtenerCartelera(filtros)
      this._publicaciones = data.map((publicacion) => new Publicacion(publicacion))
      return this._publicaciones
    })
  }

  async crearPublicacion(form) {
    return this.execute(async () => {
      const payload = this._normalizarPayloadPublicacion(form)
      const data = await this.service.crearPublicacion(payload)
      const publicacion = new Publicacion(data)
      this._publicaciones.unshift(publicacion)
      return publicacion
    })
  }

  async actualizarEstadoPublicacion(id, estaActiva) {
    return this.execute(async () => {
      const data = await this.service.actualizarEstadoPublicacion(id, estaActiva)
      return new Publicacion(data)
    })
  }

  async obtenerMisPublicaciones() {
    return this.execute(async () => {
      const data = await this.service.obtenerMisPublicaciones()
      return data.map((publicacion) => new Publicacion(publicacion))
    })
  }

  get publicaciones() {
    return this._publicaciones
  }
}
