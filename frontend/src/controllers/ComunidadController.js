import BaseController from './BaseController.js'

export default class ComunidadController extends BaseController {
  constructor(service) {
    super()
    this.service = service
  }

  async obtenerComunidad() {
    return this.execute(() => this.service.obtenerComunidad())
  }
}
