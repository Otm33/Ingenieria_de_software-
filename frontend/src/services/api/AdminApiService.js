import ApiClient, { sharedApiClient } from './ApiClient.js'

/**
 * AdminRepository - Repositorio para operaciones administrativas
 * Usa caché limitado ya que las operaciones de admin suelen requerir datos frescos
 */
export default class AdminRepository {
  constructor(apiClient = null) {
    this.apiClient = apiClient || sharedApiClient
    
    // Claves de caché
    this.cacheKeys = {
      cargaCSV: 'admin:carga_csv',
    }
  }

  /**
   * Carga usuarios autorizados desde archivo CSV
   * Nota: No se usa caché para esta operación ya que los resultados deben ser frescos
   */
  async cargarUsuariosAutorizados(archivo) {
    const formData = new FormData()
    formData.append('archivo_csv', archivo)

    return this.apiClient.postFormData('cargar-csv/', formData)
  }

  /**
   * Invalida toda la caché administrativa
   */
  invalidateAll() {
    this.apiClient.invalidateAll()
  }
}
