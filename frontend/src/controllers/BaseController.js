export default class BaseController {
  async execute(operation) {
    try {
      return await operation()
    } catch (error) {
      throw error instanceof Error
        ? error
        : new Error(error?.message || 'No se pudo completar la solicitud.')
    }
  }
}
