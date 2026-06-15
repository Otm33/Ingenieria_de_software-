<template>
  <section class="page">
    <div class="page-header">
      <div>
        <p class="eyebrow">Red Comercial</p>
        <h2 class="page-title">{{ esComercio ? 'Operaciones comerciales' : 'Saldo a favor comercial' }}</h2>
        <p class="page-description">
          <template v-if="esComercio">
            Emite vuelto comercial y consulta tu balance. Independiente de las Horas de Vida.
          </template>
          <template v-else>
            Usa tu saldo en comercios afiliados de la red. Independiente de las Horas de Vida.
          </template>
        </p>
      </div>
    </div>

    <p class="alert alert--info">
      Este saldo no es convertible a dinero en efectivo. Solo puede utilizarse en comercios afiliados activos.
    </p>

    <p v-if="!esComercio" class="alert alert--info alert--interop">
      Tu saldo a favor es valido en cualquier comercio afiliado de la red, aunque lo hayas recibido como vuelto en otro comercio.
    </p>

    <p v-if="esComercio && balanceComercial < 0" class="alert alert--info">
      Tu balance comercial es negativo porque asumiste deuda al emitir vuelto. Se compensa cuando los clientes pagan con saldo en tu comercio.
    </p>

    <div v-if="cargando" class="loading-state">Cargando red comercial...</div>
    <p v-else-if="error" class="alert alert--error">{{ error }}</p>

    <template v-else>
      <div class="metric-row metric-row--comunidad">
        <article v-if="!esComercio" class="metric">
          <span class="metric__value">{{ saldoActual.toFixed(2) }}</span>
          <span class="metric__label">Saldo a favor comercial</span>
        </article>
        <article v-if="esComercio" class="metric">
          <span
            class="metric__value"
            :class="{ 'metric__value--negativo': balanceComercial < 0 }"
          >
            {{ balanceComercial.toFixed(2) }}
          </span>
          <span class="metric__label">Balance comercial del comercio</span>
        </article>
        <article class="metric">
          <span class="metric__value">{{ comerciosFiltrados.length }}</span>
          <span class="metric__label">Comercios afiliados</span>
        </article>
      </div>

      <section class="panel">
        <div class="panel__header">
          <h3 class="panel__title">Historial de movimientos</h3>
          <p class="panel__hint panel__hint--inline">
            {{ esComercio
              ? 'Operaciones emitidas o cobradas por tu comercio.'
              : 'Emisiones recibidas y pagos realizados en la red.' }}
          </p>
        </div>
        <div class="panel__body">
          <div v-if="movimientosVisibles.length" class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th>{{ esComercio ? 'Cliente' : 'Comercio' }}</th>
                  <th>Valor</th>
                  <th>Recibido</th>
                  <th>Excedente / Monto</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="mov in movimientosVisibles" :key="mov.id">
                  <td>{{ formatearFecha(mov.fecha) }}</td>
                  <td>
                    <span :class="['mov-badge', claseTipoMovimiento(mov.tipo_movimiento)]">
                      {{ etiquetaTipoMovimiento(mov.tipo_movimiento) }}
                    </span>
                  </td>
                  <td>{{ contraparteHistorial(mov) }}</td>
                  <td>{{ formatearMontoOpcional(mov.valor_producto) }}</td>
                  <td>{{ formatearMontoOpcional(mov.monto_recibido) }}</td>
                  <td>{{ Number(mov.monto_excedente).toFixed(2) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-state">Sin movimientos comerciales registrados.</div>
        </div>
      </section>

      <section v-if="esComercio" class="panel">
        <div class="panel__header">
          <h3 class="panel__title">Emitir vuelto por falta de cambio</h3>
        </div>
        <div class="panel__body">
          <p class="panel__hint">
            Indica el valor del producto o servicio y cuanto te pago el cliente en efectivo. El vuelto comercial es la diferencia cuando pago de mas y no tienes cambio fisico.
          </p>
          <form class="form-grid" @submit.prevent="emitirVuelto">
            <div v-if="clientes.length" class="form-group form-group--full">
              <label for="buscar_cliente">Buscar cliente</label>
              <input
                id="buscar_cliente"
                v-model="filtroBusquedaClientes"
                class="input"
                type="search"
                placeholder="Filtrar por nombre o usuario"
              />
            </div>
            <div class="form-group form-group--full">
              <label for="cliente_id">Cliente</label>
              <select
                v-if="clientesFiltrados.length"
                id="cliente_id"
                v-model.number="formEmision.clienteId"
                class="input"
                required
              >
                <option disabled :value="null">Selecciona un cliente</option>
                <option
                  v-for="cliente in clientesFiltrados"
                  :key="cliente.id"
                  :value="cliente.id"
                >
                  {{ cliente.nombreReal }} (@{{ cliente.username }})
                </option>
              </select>
              <div v-else class="empty-state">
                {{ clientes.length
                  ? 'No hay clientes que coincidan con la busqueda.'
                  : 'No hay clientes registrados en la comunidad.'
                }}
              </div>
            </div>
            <div class="form-group">
              <label for="valor_producto">Valor del producto o servicio</label>
              <input
                id="valor_producto"
                v-model="formEmision.valorProducto"
                class="input"
                type="number"
                min="0.01"
                step="0.01"
                required
              />
            </div>
            <div class="form-group">
              <label for="monto_recibido">Monto recibido en efectivo</label>
              <input
                id="monto_recibido"
                v-model="formEmision.montoRecibido"
                class="input"
                type="number"
                min="0"
                step="0.01"
                required
              />
              <p v-if="formEmision.montoRecibido && !recibidoSuperaValor" class="alert alert--error">
                El monto recibido debe ser mayor al valor del producto ({{ Number(formEmision.valorProducto).toFixed(2) }}) para emitir vuelto.
              </p>
            </div>
            <div class="form-group">
              <label for="excedente_calculado">Excedente (vuelto comercial)</label>
              <output id="excedente_calculado" class="input input--readonly" aria-live="polite">
                {{ excedenteCalculado.toFixed(2) }}
              </output>
              <p v-if="formEmision.valorProducto && formEmision.montoRecibido && !excedenteValido" class="alert alert--error">
                El excedente debe ser mayor a cero para emitir vuelto.
              </p>
            </div>
            <div class="form-actions">
              <button
                class="button button--primary"
                type="submit"
                :disabled="procesandoEmision || !puedeEmitirVuelto"
              >
                {{ procesandoEmision ? 'Emitiendo...' : 'Emitir' }}
              </button>
            </div>
          </form>

          <p v-if="errorEmision" class="alert alert--error">{{ errorEmision }}</p>

          <div v-if="comprobanteEmision" class="comprobante comprobante--success">
            <p class="comprobante__titulo">Vuelto emitido correctamente</p>
            <dl class="comprobante__grid">
              <div v-if="comprobanteEmision.clienteNombre" class="comprobante__item">
                <dt>Cliente</dt>
                <dd>{{ comprobanteEmision.clienteNombre }}</dd>
              </div>
              <div v-if="comprobanteEmision.valorProducto != null" class="comprobante__item">
                <dt>Valor producto</dt>
                <dd>{{ comprobanteEmision.valorProducto.toFixed(2) }}</dd>
              </div>
              <div v-if="comprobanteEmision.montoRecibido != null" class="comprobante__item">
                <dt>Monto recibido</dt>
                <dd>{{ comprobanteEmision.montoRecibido.toFixed(2) }}</dd>
              </div>
              <div class="comprobante__item">
                <dt>Excedente emitido</dt>
                <dd>{{ comprobanteEmision.monto.toFixed(2) }}</dd>
              </div>
              <div class="comprobante__item">
                <dt>Comprobante</dt>
                <dd>#{{ comprobanteEmision.id }}</dd>
              </div>
              <div class="comprobante__item">
                <dt>Fecha</dt>
                <dd>{{ formatearFecha(comprobanteEmision.fecha) }}</dd>
              </div>
            </dl>
            <p class="comprobante__balance">
              Balance comercial actualizado:
              <strong :class="{ 'comprobante__balance--negativo': balanceComercial < 0 }">
                {{ balanceComercial.toFixed(2) }}
              </strong>
              <span v-if="balanceComercial < 0"> (deuda comercial asumida)</span>
            </p>
          </div>
        </div>
      </section>

      <section v-if="!esComercio" class="panel">
        <div class="panel__header">
          <h3 class="panel__title">Pagar con saldo comercial</h3>
        </div>
        <div class="panel__body">
          <p v-if="saldoActual <= 0" class="alert alert--info">
            No tienes saldo comercial disponible. Recibelo como vuelto en cualquier comercio afiliado.
          </p>
          <form class="form-grid" @submit.prevent="pagarConSaldo">
            <div class="form-group">
              <label for="comercio_id">Comercio destino</label>
              <select id="comercio_id" v-model.number="formPago.comercioId" class="input" required>
                <option disabled :value="null">Selecciona un comercio</option>
                <option
                  v-for="comercio in comerciosParaPago"
                  :key="comercio.id"
                  :value="comercio.id"
                >
                  {{ comercio.nombreReal }} (@{{ comercio.username }})
                </option>
              </select>
            </div>
            <div class="form-group">
              <label for="monto_pago">Monto a pagar</label>
              <input
                id="monto_pago"
                v-model="formPago.monto"
                class="input"
                type="number"
                min="0.01"
                step="0.01"
                :max="saldoActual > 0 ? saldoActual : undefined"
                required
              />
              <p v-if="formPago.monto && !montoPagoValido" class="alert alert--error">
                El monto no puede superar tu saldo disponible ({{ saldoActual.toFixed(2) }}).
              </p>
            </div>
            <div class="form-actions">
              <button
                class="button button--primary"
                type="submit"
                :disabled="procesandoPago || !puedeEnviarPago"
              >
                {{ procesandoPago ? 'Procesando...' : 'Pagar' }}
              </button>
            </div>
          </form>

          <p v-if="errorPago" class="alert alert--error">{{ errorPago }}</p>

          <div v-if="resultadoPago" class="comprobante comprobante--success">
            <p class="comprobante__titulo">Pago registrado con saldo comercial</p>
            <dl class="comprobante__grid">
              <div v-if="resultadoPago.comercioNombre" class="comprobante__item">
                <dt>Comercio</dt>
                <dd>{{ resultadoPago.comercioNombre }}</dd>
              </div>
              <div class="comprobante__item">
                <dt>Monto pagado</dt>
                <dd>{{ resultadoPago.monto.toFixed(2) }}</dd>
              </div>
              <div v-if="resultadoPago.comprobante" class="comprobante__item">
                <dt>Comprobante</dt>
                <dd>#{{ resultadoPago.comprobante.id }}</dd>
              </div>
              <div class="comprobante__item">
                <dt>Saldo restante</dt>
                <dd>{{ resultadoPago.saldoRestante.toFixed(2) }}</dd>
              </div>
            </dl>
            <p class="comprobante__nota">
              Puedes usar el saldo restante en cualquier otro comercio afiliado de la red.
            </p>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="panel__header">
          <h3 class="panel__title">Catalogo de comercios afiliados</h3>
        </div>
        <div class="panel__body">
          <div class="form-group">
            <label for="buscar_comercio">Buscar comercio</label>
            <input
              id="buscar_comercio"
              v-model="filtroBusqueda"
              class="input"
              type="search"
              placeholder="Filtrar por nombre o email"
            />
          </div>

          <div v-if="comerciosFiltrados.length" class="member-grid">
            <article v-for="comercio in comerciosFiltrados" :key="comercio.id" class="member-card">
              <div class="member-card__header">
                <div class="member-avatar" :style="{ backgroundColor: getAvatarColor(comercio.username) }">
                  {{ getInitials(comercio.nombreReal, comercio.username) }}
                </div>
                <div class="member-card__info">
                  <h3 class="member-card__name">{{ comercio.nombreReal }}</h3>
                  <p class="member-card__stars">@{{ comercio.username }}</p>
                  <p class="member-card__vacio">{{ comercio.email }}</p>
                </div>
              </div>
              <div class="member-card__badges">
                <span class="badge badge--activa">Comercio afiliado</span>
              </div>
            </article>
          </div>
          <div v-else class="empty-state">
            No hay comercios que coincidan con la busqueda.
          </div>
        </div>
      </section>
    </template>
  </section>
</template>

<script setup>
import { computed, inject, onMounted, reactive, ref } from 'vue'
import ComercioController from '../controllers/ComercioController.js'
import ComercioRepository from '../repositories/ComercioRepository.js'

const authController = inject('authController')

const repository = new ComercioRepository()
const controller = new ComercioController(repository)

const AVATAR_COLORS = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b', '#fa709a', '#fee140']

const cargando = ref(true)
const error = ref('')
const saldoActual = ref(0)
const balanceComercial = ref(0)
const esComercio = ref(false)
const usuarioId = ref(null)
const comercios = ref([])
const clientes = ref([])
const movimientosCliente = ref([])
const movimientosComercio = ref([])
const filtroBusqueda = ref('')
const filtroBusquedaClientes = ref('')

const formEmision = reactive({ clienteId: null, valorProducto: '', montoRecibido: '' })
const formPago = reactive({ comercioId: null, monto: '' })
const procesandoEmision = ref(false)
const procesandoPago = ref(false)
const errorEmision = ref('')
const errorPago = ref('')
const comprobanteEmision = ref(null)
const resultadoPago = ref(null)

const movimientosVisibles = computed(() => {
  const comoCliente = movimientosCliente.value || []
  const comoComercio = movimientosComercio.value || []
  const lista = esComercio.value
    ? (comoComercio.length ? comoComercio : comoCliente)
    : (comoCliente.length ? comoCliente : comoComercio)
  return [...lista].sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
})

const comerciosFiltrados = computed(() => {
  const termino = filtroBusqueda.value.trim().toLowerCase()
  if (!termino) return comercios.value

  return comercios.value.filter((comercio) => {
    const nombre = (comercio.nombreReal || '').toLowerCase()
    const email = (comercio.email || '').toLowerCase()
    const username = (comercio.username || '').toLowerCase()
    return nombre.includes(termino) || email.includes(termino) || username.includes(termino)
  })
})

const comerciosParaPago = computed(() => {
  if (!usuarioId.value) return comercios.value
  return comercios.value.filter((comercio) => comercio.id !== usuarioId.value)
})

const clientesFiltrados = computed(() => {
  const termino = filtroBusquedaClientes.value.trim().toLowerCase()
  if (!termino) return clientes.value

  return clientes.value.filter((cliente) => {
    const nombre = (cliente.nombreReal || '').toLowerCase()
    const username = (cliente.username || '').toLowerCase()
    return nombre.includes(termino) || username.includes(termino)
  })
})

const redondearMonto = (valor) => Math.round(Number(valor) * 100) / 100

const excedenteCalculado = computed(() => {
  const valor = Number(formEmision.valorProducto)
  const recibido = Number(formEmision.montoRecibido)
  if (!Number.isFinite(valor) || !Number.isFinite(recibido)) return 0
  return Math.max(0, redondearMonto(recibido - valor))
})

const valorProductoValido = computed(() => {
  const valor = Number(formEmision.valorProducto)
  return Number.isFinite(valor) && valor > 0
})

const montoRecibidoValido = computed(() => {
  const recibido = Number(formEmision.montoRecibido)
  return Number.isFinite(recibido) && recibido >= 0
})

const recibidoSuperaValor = computed(() => {
  if (!valorProductoValido.value || !montoRecibidoValido.value) return true
  return Number(formEmision.montoRecibido) > Number(formEmision.valorProducto)
})

const excedenteValido = computed(() => excedenteCalculado.value > 0)

const puedeEmitirVuelto = computed(() => {
  return Boolean(formEmision.clienteId)
    && valorProductoValido.value
    && montoRecibidoValido.value
    && recibidoSuperaValor.value
    && excedenteValido.value
    && clientesFiltrados.value.length > 0
})

const montoPagoValido = computed(() => {
  const monto = Number(formPago.monto)
  return Number.isFinite(monto) && monto > 0 && monto <= saldoActual.value
})

const puedeEnviarPago = computed(() => {
  return Boolean(formPago.comercioId) && montoPagoValido.value && saldoActual.value > 0
})

const getInitials = (nombreReal, username) => (nombreReal || username || 'C').charAt(0).toUpperCase()

const getAvatarColor = (username) => {
  const index = (username || 'c').charCodeAt(0) % AVATAR_COLORS.length
  return AVATAR_COLORS[index]
}

const formatearFecha = (valor) => {
  if (!valor) return '—'
  return new Date(valor).toLocaleString('es-ES')
}

const formatearMontoOpcional = (valor) => {
  if (valor == null || valor === '') return '—'
  return Number(valor).toFixed(2)
}

const etiquetaTipoMovimiento = (tipo) => (tipo === 'EMISION' ? 'Emision' : 'Pago')

const claseTipoMovimiento = (tipo) => (
  tipo === 'EMISION' ? 'mov-badge--emision' : 'mov-badge--pago'
)

const contraparteHistorial = (mov) => {
  if (esComercio.value) {
    return mov.cliente_nombre || '—'
  }
  return mov.comercio_nombre || '—'
}

const nombreComercioPorId = (comercioId) => {
  const comercio = comercios.value.find((item) => item.id === comercioId)
  return comercio?.nombreReal || null
}

const cargarDatos = async () => {
  cargando.value = true
  error.value = ''

  try {
    const [catalogo, saldo, sesion] = await Promise.all([
      controller.obtenerComercios(),
      controller.obtenerMiSaldoComercial(),
      authController.obtenerSesionActual(),
    ])

    comercios.value = catalogo.comercios || []
    esComercio.value = Boolean(saldo?.esComercio || sesion?.usuario?.es_comercio)
    const montoSaldo = Number(saldo?.saldoActual || 0)
    if (esComercio.value) {
      balanceComercial.value = montoSaldo
      saldoActual.value = 0
    } else {
      saldoActual.value = montoSaldo
      balanceComercial.value = 0
    }
    usuarioId.value = sesion?.usuario?.id ?? null
    movimientosCliente.value = saldo?.movimientosComoCliente || []
    movimientosComercio.value = saldo?.movimientosComoComercio || []

    if (esComercio.value) {
      const listaClientes = await controller.obtenerClientes()
      clientes.value = listaClientes.clientes || []
    } else {
      clientes.value = []
    }
  } catch (err) {
    error.value = err.message || 'No se pudo cargar la red comercial.'
  } finally {
    cargando.value = false
  }
}

const emitirVuelto = async () => {
  if (!puedeEmitirVuelto.value) {
    if (!recibidoSuperaValor.value) {
      errorEmision.value = 'El monto recibido debe ser mayor al valor del producto para emitir vuelto.'
    } else if (!excedenteValido.value) {
      errorEmision.value = 'El excedente debe ser mayor a cero para emitir vuelto.'
    } else {
      errorEmision.value = 'Completa cliente, valor del producto y monto recibido.'
    }
    return
  }

  procesandoEmision.value = true
  errorEmision.value = ''
  comprobanteEmision.value = null

  try {
    const respuesta = await controller.emitirVuelto(
      formEmision.clienteId,
      formEmision.valorProducto,
      formEmision.montoRecibido,
    )
    comprobanteEmision.value = respuesta?.comprobante || null
    if (respuesta?.saldoComercio != null) {
      balanceComercial.value = Number(respuesta.saldoComercio)
    }
    formEmision.clienteId = null
    formEmision.valorProducto = ''
    formEmision.montoRecibido = ''
    await cargarDatos()
  } catch (err) {
    errorEmision.value = err.message || 'No se pudo emitir el vuelto.'
  } finally {
    procesandoEmision.value = false
  }
}

const pagarConSaldo = async () => {
  if (!montoPagoValido.value) {
    errorPago.value = `El monto no puede superar tu saldo disponible (${saldoActual.value.toFixed(2)}).`
    return
  }

  procesandoPago.value = true
  errorPago.value = ''
  resultadoPago.value = null

  try {
    const respuesta = await controller.pagarConSaldo(formPago.comercioId, formPago.monto)
    resultadoPago.value = {
      message: respuesta?.message || 'Pago procesado correctamente.',
      comprobante: respuesta?.comprobante || null,
      comercioNombre: respuesta?.comprobante?.comercioNombre
        || nombreComercioPorId(formPago.comercioId),
      monto: Number(formPago.monto),
      saldoRestante: Number(respuesta?.saldoRestante ?? saldoActual.value),
    }
    saldoActual.value = resultadoPago.value.saldoRestante
    formPago.comercioId = null
    formPago.monto = ''
    await cargarDatos()
  } catch (err) {
    errorPago.value = err.message || 'No se pudo procesar el pago.'
  } finally {
    procesandoPago.value = false
  }
}

onMounted(cargarDatos)
</script>

<style scoped>
.metric__value--negativo {
  color: #c0392b;
}

.input--readonly {
  display: block;
  background: #f1f3f5;
  color: #333;
  font-weight: 600;
  cursor: default;
}

.panel__hint--inline {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
  color: #666;
}

.mov-badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
}

.mov-badge--emision {
  background: #e7f1ff;
  color: #1e4f91;
}

.mov-badge--pago {
  background: #e7f7f1;
  color: #175f49;
}

.comprobante {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #c3e6cb;
  background: #f4fbf6;
}

.comprobante__titulo {
  margin: 0 0 0.75rem;
  font-weight: 700;
  color: #155724;
}

.comprobante__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin: 0 0 0.75rem;
}

.comprobante__item {
  margin: 0;
}

.comprobante__item dt {
  margin: 0 0 0.15rem;
  font-size: 0.75rem;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.comprobante__item dd {
  margin: 0;
  font-weight: 600;
  color: #333;
}

.comprobante__balance,
.comprobante__nota {
  margin: 0;
  font-size: 0.9rem;
  color: #444;
}

.comprobante__balance--negativo {
  color: #c0392b;
}
</style>
