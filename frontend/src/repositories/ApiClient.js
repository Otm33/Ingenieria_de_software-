export default class ApiClient {
  constructor(baseURL = '/api/') {
    this.baseURL = baseURL.endsWith('/') ? baseURL : `${baseURL}/`
  }

  async request(endpoint, options = {}) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      credentials: 'include',
      ...options,
    })
    const contentType = response.headers.get('content-type') || ''
    const data = contentType.includes('application/json') ? await response.json() : null

    if (!response.ok) {
      throw new Error(data?.error || data?.detail || 'No se pudo completar la solicitud.')
    }

    return data
  }
}
