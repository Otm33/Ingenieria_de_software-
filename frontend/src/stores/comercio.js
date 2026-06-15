import { defineStore } from 'pinia'
import { ref } from 'vue'
import ComercioApiService from '../services/api/ComercioApiService.js'

/**
 * ComercioStore - Store de operaciones comerciales
 * Reemplaza a ComercioController para manejo de estado reactivo de comercio
 */
export const useComercioStore = defineStore('comercio', () => {
  // Estado reactivo
  const comercios = ref([])
  const clientes = ref([])
  const saldoComercial = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // API Service
  const comercioApiService = new ComercioApiService()

  function _validarId(valor, etiqueta) {
    const id = Number(valor)
    if (!Number.isInteger(id) || id <= 0) {
      throw new Error(`Debes indicar un ${etiqueta} válido.`)
    }
    return id
  }

  function _validarMonto(valor) {
    const monto = Number(valor)
    if (!Number.isFinite(monto) || monto <= 0) {
      throw new Error('El monto debe ser mayor a cero.')
    }
    return monto
  }

  function _mapComercio(comercio) {
    return {
      id: comercio.id,
      username: comercio.username,
      nombreReal: comercio.nombre_real,
      email: comercio.email,
      esComercio: Boolean(comercio.es_comercio),
    }
  }

  function _mapCliente(cliente) {
    return {
      id: cliente.id,
      username: cliente.username,
      nombreReal: cliente.nombre_real,
    }
  }

  function _mapComprobante(comprobante) {
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

  function _mapSaldoComercial(data) {
    return {
      saldoActual: Number(data?.saldo_actual || 0),
      esComercio: Boolean(data?.es_comercio),
      movimientosComoCliente: data?.movimientos_como_cliente || [],
      movimientosComoComercio: data?.movimientos_como_comercio || [],
    }
  }

  function _mapOperacionComercial(data) {
    return {
      message: data?.message || '',
      comprobante: _mapComprobante(data?.comprobante),
      saldoCliente: data?.saldo_cliente != null ? Number(data.saldo_cliente) : null,
      saldoComercio: data?.saldo_comercio != null ? Number(data.saldo_comercio) : null,
      saldoRestante: data?.saldo_restante != null ? Number(data.saldo_restante) : null,
    }
  }

  async function obtenerComercios() {
    loading.value = true
    error.value = null

    try {
      const data = await comercioApiService.obtenerComercios()
      const comerciosArray = Array.isArray(data) ? data : (data?.comercios || [])
      const comerciosData = comerciosArray.map((comercio) => _mapComercio(comercio))

      comercios.value = comerciosData

      return {
        comercios: comerciosData,
        cantidad: comerciosData.length,
      }
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function obtenerClientes(termino = '') {
    loading.value = true
    error.value = null

    try {
      const data = await comercioApiService.obtenerClientes(termino)
      const clientesArray = Array.isArray(data) ? data : (data?.clientes || [])
      const clientesData = clientesArray.map((cliente) => _mapCliente(cliente))

      clientes.value = clientesData

      return {
        clientes: clientesData,
        cantidad: clientesData.length,
      }
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function obtenerMiSaldoComercial() {
    loading.value = true
    error.value = null
    
    try {
      const data = await comercioApiService.obtenerMiSaldoComercial()
      const saldoData = _mapSaldoComercial(data)
      saldoComercial.value = saldoData
      return saldoData
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  function _calcularExcedente(valorProducto, montoRecibido) {
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

  async function emitirVuelto(clienteId, valorProducto, montoRecibido) {
    loading.value = true
    error.value = null
    
    try {
      const clienteIdValido = _validarId(clienteId, 'cliente')
      const excedente = _calcularExcedente(valorProducto, montoRecibido)

      const data = await comercioApiService.emitirVuelto(
        clienteIdValido,
        valorProducto,
        montoRecibido,
        excedente,
      )
      return _mapOperacionComercial(data)
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function pagarConSaldo(comercioId, monto) {
    loading.value = true
    error.value = null
    
    try {
      const comercioIdValido = _validarId(comercioId, 'comercio')
      const montoValido = _validarMonto(monto)

      const data = await comercioApiService.pagarConSaldo(comercioIdValido, montoValido)
      return _mapOperacionComercial(data)
    } catch (err) {
      error.value = err.message || 'Error desconocido'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Limpia el error
   */
  function clearError() {
    error.value = null
  }

  return {
    // Estado
    comercios,
    clientes,
    saldoComercial,
    loading,
    error,
    
    // Acciones
    obtenerComercios,
    obtenerClientes,
    obtenerMiSaldoComercial,
    emitirVuelto,
    pagarConSaldo,
    clearError
  }
})
