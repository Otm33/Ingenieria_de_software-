import BaseController from './BaseController.js'

export default class AdminController extends BaseController {
  constructor(service) {
    super()
    this.service = service
  }

  validarArchivoCsv(archivo) {
    if (!archivo) {
      throw new Error('Selecciona un archivo CSV antes de procesar.')
    }
    if (!archivo.name.toLowerCase().endsWith('.csv')) {
      throw new Error('Formato incorrecto. Solo se acepta .csv.')
    }
  }

  validarSeleccionArchivo(file) {
    if (!file) {
      return { archivo: null }
    }

    this.validarArchivoCsv(file)
    return { archivo: file }
  }

  async cargarUsuariosAutorizados(archivo) {
    return this.execute(async () => {
      this.validarArchivoCsv(archivo)
      return await this.service.cargarUsuariosAutorizados(archivo)
    })
  }
}
