/**
 * ApiClient - Cliente HTTP base con sistema de caché en memoria
 * Implementa almacenamiento en memoria opcional para reducir llamadas a la API
 * siguiendo los requisitos de guardado en memoria del MVC estricto
 */
export default class ApiClient {
  constructor(baseURL = '/api/') {
    this.baseURL = baseURL.endsWith('/') ? baseURL : `${baseURL}/`
    
    // Caché en memoria (Map para almacenar respuestas)
    this.cache = new Map()
    
    // Tiempo de vida de la caché en milisegundos (5 minutos por defecto)
    this.cacheTimeout = 5 * 60 * 1000
    
    // Contador de estadísticas de caché
    this.cacheStats = {
      hits: 0,
      misses: 0,
      invalidations: 0
    }
  }

  /**
   * Realiza una petición HTTP con soporte de caché opcional
   * @param {string} endpoint - El endpoint de la API
   * @param {Object} options - Opciones de fetch (method, headers, body, etc.)
   * @param {Object} cacheOptions - Opciones de caché (enabled, key, forceRefresh)
   * @returns {Promise<Object>} - La respuesta de la API
   */
  async request(endpoint, options = {}, cacheOptions = {}) {
    const { 
      enabled = false, 
      key = null, 
      forceRefresh = false 
    } = cacheOptions
    
    const cacheKey = key || this._generateCacheKey(endpoint, options)
    
    // Si la caché está habilitada y no forzamos refresco
    if (enabled && !forceRefresh) {
      const cachedData = this._getFromCache(cacheKey)
      if (cachedData !== null) {
        this.cacheStats.hits++
        return cachedData
      }
    }
    
    this.cacheStats.misses++
    
    // Realizar la petición HTTP
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      credentials: 'include',
      ...options,
    })
    
    const contentType = response.headers.get('content-type') || ''
    const data = contentType.includes('application/json') 
      ? await response.json() 
      : null
    
    if (!response.ok) {
      throw new Error(data?.error || data?.detail || 'No se pudo completar la solicitud.')
    }
    
    // Guardar en caché si está habilitada
    if (enabled && response.ok) {
      this._saveToCache(cacheKey, data)
    }
    
    return data
  }

  /**
   * GET request con soporte de caché
   */
  async get(endpoint, options = {}, cacheOptions = {}) {
    return this.request(endpoint, { ...options, method: 'GET' }, cacheOptions)
  }

  /**
   * POST request (siempre invalida caché relacionada)
   */
  async post(endpoint, data, options = {}) {
    const result = await this.request(endpoint, {
      ...options,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body: JSON.stringify(data),
    })
    
    // Invalidar caché después de una mutación
    this._invalidateRelatedCache(endpoint)
    
    return result
  }

  /**
   * PATCH request (siempre invalida caché relacionada)
   */
  async patch(endpoint, data, options = {}) {
    const result = await this.request(endpoint, {
      ...options,
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body: JSON.stringify(data),
    })
    
    // Invalidar caché después de una mutación
    this._invalidateRelatedCache(endpoint)
    
    return result
  }

  /**
   * DELETE request (siempre invalida caché relacionada)
   */
  async delete(endpoint, options = {}) {
    const result = await this.request(endpoint, {
      ...options,
      method: 'DELETE',
    })
    
    // Invalidar caché después de una mutación
    this._invalidateRelatedCache(endpoint)
    
    return result
  }

  /**
   * FormData POST (para archivos)
   */
  async postFormData(endpoint, formData, options = {}) {
    const result = await this.request(endpoint, {
      ...options,
      method: 'POST',
      body: formData,
    })
    
    this._invalidateRelatedCache(endpoint)
    return result
  }

  /**
   * Obtiene datos de la caché si están disponibles y no han expirado
   * @private
   */
  _getFromCache(key) {
    if (!this.cache.has(key)) {
      return null
    }
    
    const cached = this.cache.get(key)
    const now = Date.now()
    
    // Verificar si ha expirado
    if (now - cached.timestamp > this.cacheTimeout) {
      this.cache.delete(key)
      return null
    }
    
    return cached.data
  }

  /**
   * Guarda datos en la caché
   * @private
   */
  _saveToCache(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    })
  }

  /**
   * Genera una clave de caché basada en el endpoint y opciones
   * @private
   */
  _generateCacheKey(endpoint, options) {
    const method = options.method || 'GET'
    return `${method}:${endpoint}`
  }

  /**
   * Invalida entradas de caché relacionadas con un endpoint
   * @private
   */
  _invalidateRelatedCache(endpoint) {
    // Estrategia simple: invalidar todo cuando hay mutaciones
    // En una implementación más avanzada, se podría invalidar solo lo relacionado
    this.cache.clear()
    this.cacheStats.invalidations++
  }

  /**
   * Invalida una entrada específica de la caché
   */
  invalidate(key) {
    if (this.cache.has(key)) {
      this.cache.delete(key)
      this.cacheStats.invalidations++
    }
  }

  /**
   * Invalida toda la caché
   */
  invalidateAll() {
    this.cache.clear()
    this.cacheStats.invalidations++
  }

  /**
   * Limpia entradas expiradas de la caché
   */
  cleanExpired() {
    const now = Date.now()
    for (const [key, value] of this.cache.entries()) {
      if (now - value.timestamp > this.cacheTimeout) {
        this.cache.delete(key)
      }
    }
  }

  /**
   * Retorna estadísticas de uso de la caché
   */
  getCacheStats() {
    return {
      ...this.cacheStats,
      size: this.cache.size,
      hitRate: this.cacheStats.hits + this.cacheStats.misses > 0
        ? (this.cacheStats.hits / (this.cacheStats.hits + this.cacheStats.misses) * 100).toFixed(2)
        : 0
    }
  }

  /**
   * Establece el tiempo de vida de la caché
   */
  setCacheTimeout(timeoutMs) {
    this.cacheTimeout = timeoutMs
  }
}

/**
 * Instancia singleton compartida por todos los servicios.
 * Garantiza que toda la aplicación comparte la misma caché en memoria,
 * de modo que invalidar en un servicio (ej. ResenaApiService) también
 * afecta la caché de otro (ej. TruequeApiService).
 */
export const sharedApiClient = new ApiClient()

