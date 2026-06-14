import BaseController from './BaseController.js'

export default class ResenaController extends BaseController {
  constructor(service) {
    super()
    this.service = service
  }

  validarResena(truequeId, estrellas, comentario, estadoTrueque = '') {
    if (!truequeId) {
      throw new Error('No se identificó el trueque.')
    }
    if (estadoTrueque && estadoTrueque !== 'FINALIZADO') {
      throw new Error('Solo puedes dejar reseña de trueques finalizados.')
    }
    const valorEstrellas = Number(estrellas)
    if (!Number.isInteger(valorEstrellas) || valorEstrellas < 1 || valorEstrellas > 5) {
      throw new Error('Las estrellas deben estar entre 1 y 5.')
    }
    const texto = comentario?.trim()
    if (!texto) {
      throw new Error('El comentario es obligatorio.')
    }
    if (texto.length > 500) {
      throw new Error('El comentario no puede superar 500 caracteres.')
    }
    return { estrellas: valorEstrellas, comentario: texto }
  }

  async registrarResena(truequeId, estrellas, comentario, estadoTrueque = '') {
    return this.execute(async () => {
      const validado = this.validarResena(truequeId, estrellas, comentario, estadoTrueque)
      return await this.service.registrarResena(
        truequeId,
        validado.estrellas,
        validado.comentario,
      )
    })
  }
}
