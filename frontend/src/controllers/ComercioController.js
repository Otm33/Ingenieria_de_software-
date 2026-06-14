import BaseController from './BaseController.js'

export default class ComercioController extends BaseController {
  constructor(service) {
    super()
    this.service = service
  }

  _validarId(valor, etiqueta) {
    const id = Number(valor)
    if (!Number.isInteger(id) || id <= 0) {
      throw new Error(`Debes indicar un ${etiqueta} valido.`)
    }
    return id
  }

  _validarMonto(valor) {
    const monto = Number(valor)
    if (!Number.isFinite(monto) || monto <= 0) {
      throw new Error('El monto debe ser mayor a cero.')
    }
    return monto
  }

  _mapComercio(comercio) {
    return {
      id: comercio.id,
      username: comercio.username,
      nombreReal: comercio.nombre_real,
      email: comercio.email,
      esComercio: Boolean(comercio.es_comercio),
    }
  }

  _mapCliente(cliente) {
    return {
      id: cliente.id,
      username: cliente.username,
      nombreReal: cliente.nombre_real,
    }
  }

  _mapComprobante(comprobante) {
    if (!comprobante) return null

    return {
      id: comprobante.id,
      tipoMovimiento: comprobante.tipo_movimiento,
      monto: Number(comprobante.monto_excedente),
      valorProducto: comprobante.valor_producto != null ? Number(comprobante.valor_producto) : null,
      montoRecibido: comprobante.monto_recibido != null ? Number(comprobante.monto_recibido) : null,
      comercioId: comprobante.comercio,
      comercioNombre: comprobante.comercio_nombre,
      clienteId: comprobante.cliente,
      clienteNombre: comprobante.cliente_nombre,
      fecha: comprobante.fecha,
      fechaExpiracion: comprobante.fecha_expiracion,
    }
  }

  _mapSaldoComercial(data) {
    return {
      saldoActual: Number(data?.saldo_actual || 0),
      esComercio: Boolean(data?.es_comercio),
      movimientosComoCliente: data?.movimientos_como_cliente || [],
      movimientosComoComercio: data?.movimientos_como_comercio || [],
    }
  }

  _mapOperacionComercial(data) {
    return {
      message: data?.message || '',
      comprobante: this._mapComprobante(data?.comprobante),
      saldoCliente: data?.saldo_cliente != null ? Number(data.saldo_cliente) : null,
      saldoComercio: data?.saldo_comercio != null ? Number(data.saldo_comercio) : null,
      saldoRestante: data?.saldo_restante != null ? Number(data.saldo_restante) : null,
    }
  }

  async obtenerComercios() {
    return this.execute(async () => {
      const data = await this.service.obtenerComercios()
      const comercios = (Array.isArray(data) ? data : []).map((comercio) => this._mapComercio(comercio))

      return {
        comercios,
        cantidad: comercios.length,
      }
    })
  }

  async obtenerClientes(termino = '') {
    return this.execute(async () => {
      const data = await this.service.obtenerClientes(termino)
      const clientes = (Array.isArray(data) ? data : []).map((cliente) => this._mapCliente(cliente))

      return {
        clientes,
        cantidad: clientes.length,
      }
    })
  }

  async obtenerMiSaldoComercial() {
    return this.execute(async () => {
      const data = await this.service.obtenerMiSaldoComercial()
      return this._mapSaldoComercial(data)
    })
  }

  _calcularExcedente(valorProducto, montoRecibido) {
    const valor = Number(valorProducto)
    const recibido = Number(montoRecibido)

    if (!Number.isFinite(valor) || valor <= 0) {
      throw new Error('El valor del producto debe ser mayor a cero.')
    }
    if (!Number.isFinite(recibido) || recibido < 0) {
      throw new Error('El monto recibido debe ser cero o mayor.')
    }
    if (recibido <= valor) {
      throw new Error('El monto recibido debe ser mayor al valor del producto para emitir vuelto.')
    }

    const excedente = Math.round((recibido - valor) * 100) / 100
    if (excedente <= 0) {
      throw new Error('El excedente debe ser mayor a cero para emitir vuelto.')
    }

    return excedente
  }

  async emitirVuelto(clienteId, valorProducto, montoRecibido) {
    return this.execute(async () => {
      const clienteIdValido = this._validarId(clienteId, 'cliente')
      const excedente = this._calcularExcedente(valorProducto, montoRecibido)

      const data = await this.service.emitirVuelto(
        clienteIdValido,
        valorProducto,
        montoRecibido,
        excedente,
      )
      return this._mapOperacionComercial(data)
    })
  }

  async pagarConSaldo(comercioId, monto) {
    return this.execute(async () => {
      const comercioIdValido = this._validarId(comercioId, 'comercio')
      const montoValido = this._validarMonto(monto)

      const data = await this.service.pagarConSaldo(comercioIdValido, montoValido)
      return this._mapOperacionComercial(data)
    })
  }
}
