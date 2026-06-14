import ApiClient from './ApiClient.js'

export default class ComercioRepository {
  constructor(baseURL = '/api/') {
    this.apiClient = new ApiClient(baseURL)
    this.baseURL = this.apiClient.baseURL
  }

  async _request(endpoint, options = {}) {
    return this.apiClient.request(endpoint, options)
  }

  async obtenerComercios() {
    return await this._request('comercios/')
  }

  async obtenerClientes(termino = '') {
    const query = termino ? `?q=${encodeURIComponent(termino)}` : ''
    return await this._request(`clientes/${query}`)
  }

  async obtenerMiSaldoComercial() {
    return await this._request('mi-saldo-comercial/')
  }

  async emitirVuelto(clienteId, valorProducto, montoRecibido, montoExcedente) {
    return await this._request('comercio/emitir-vuelto/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cliente_id: clienteId,
        valor_producto: valorProducto,
        monto_recibido: montoRecibido,
        monto_excedente: montoExcedente,
      }),
    })
  }

  async pagarConSaldo(comercioId, monto) {
    return await this._request('comercio/pagar/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        comercio_id: comercioId,
        monto,
      }),
    })
  }
}
