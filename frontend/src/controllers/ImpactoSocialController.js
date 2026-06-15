import BaseController from './BaseController.js'
import {
  categoriaParaTitulo,
  esCategoriaCausaSocialPermitida,
  esTituloCausaSocialPermitido,
} from '../data/catalogoCausasSociales.js'

export const MENSAJE_SALDO_POSITIVO_DONACION = 'Necesitas saldo positivo para realizar donaciones solidarias'
export const MENSAJE_PENDIENTE_APROBACION = (
  'Tu solicitud quedó pendiente de aprobación. Si el administrador la aprueba, ' +
  'quedarás registrado como Usuario Vulnerable y podrás recibir donaciones solidarias.'
)
export const MENSAJE_SOLICITANTE_MARCADO_VULNERABLE = (
  'Solicitud aprobada. El solicitante fue catalogado como Usuario Vulnerable.'
)
export const MENSAJE_DONACION_EXITOSA = 'Donación Exitosa'
export const MENSAJE_SIN_PERMISOS_ADMIN = 'No tienes permisos de administrador.'
export const MENSAJE_SOLO_VULNERABLE_CRITICO = 'Solo se puede asignar a usuarios vulnerables o críticos'
export const MENSAJE_TITULO_CAUSA_INVALIDO = 'El título seleccionado no corresponde a una causa social permitida.'
export const MENSAJE_CATEGORIA_CAUSA_INVALIDA = 'La categoría seleccionada no es válida para causas sociales.'
export const MENSAJE_CATEGORIA_TITULO_INCONSISTENTES = 'El título no pertenece a la categoría seleccionada.'
export const MENSAJE_RECEPTOR_MAS_10_HORAS = 'Usuarios con más de 10 horas no pueden recibir donaciones'
export const MENSAJE_TOPE_HORAS_RECIBIDAS = 'No se puede donar más de 10 horas a este usuario'
export const MENSAJE_TOPE_USUARIO_ALCANZADO = (
  'Este usuario ya recibió el máximo de 10 h en donaciones solidarias (total acumulado).'
)
export const ETIQUETA_USUARIO_VULNERABLE = 'Usuario Vulnerable'
export const TOPE_HORAS_RECIBIDAS_DONACION = 10

export function etiquetaEstadoSocial(estado) {
  if (estado === 'VULNERABLE' || estado === 'CRITICO') return ETIQUETA_USUARIO_VULNERABLE
  return null
}

export function calcularHorasRestantesReceptor(horasRecibidasDonacion, horasDeVida) {
  if (horasDeVida > TOPE_HORAS_RECIBIDAS_DONACION) return 0
  return Math.max(0, TOPE_HORAS_RECIBIDAS_DONACION - horasRecibidasDonacion)
}

export function calcularHorasSolidariasTotales(solicitudes) {
  return (solicitudes || [])
    .filter((solicitud) => solicitud.estado === 'APROBADA')
    .reduce((suma, solicitud) => suma + Number(solicitud.horasSolidariasDisponibles || 0), 0)
}

export function calcularHorasRecibidasTotales(solicitudes) {
  return (solicitudes || [])
    .filter((solicitud) => solicitud.estado === 'APROBADA')
    .reduce((suma, solicitud) => suma + Number(solicitud.horasRecibidas || 0), 0)
}

export function calcularHorasSolidariasUtilizadasTotales(solicitudes) {
  return (solicitudes || [])
    .filter((solicitud) => solicitud.estado === 'APROBADA')
    .reduce((suma, solicitud) => suma + Number(solicitud.horasSolidariasUtilizadas || 0), 0)
}

export function calcularMontoDonacionesTotales(donaciones) {
  return (donaciones || [])
    .reduce((suma, donacion) => suma + Number(donacion.monto || 0), 0)
}

export function etiquetaTipoDonacion(tipoDestino) {
  if (tipoDestino === 'CAUSA') return 'Causa'
  if (tipoDestino === 'FONDO') return 'Fondo'
  if (tipoDestino === 'ASIGNACION') return 'Asignación'
  return tipoDestino
}

export default class ImpactoSocialController extends BaseController {
  constructor(service) {
    super()
    this.service = service
  }

  _validarTexto(valor, etiqueta) {
    const texto = (valor || '').trim()
    if (!texto) {
      throw new Error(`${etiqueta} es obligatorio.`)
    }
    return texto
  }

  _validarMontoDonacion(monto, saldoDonable) {
    const valor = Number(monto)
    if (!Number.isFinite(valor) || valor < 0.5) {
      throw new Error('El monto mínimo de donación es 0.5 horas')
    }
    if (saldoDonable <= 0) {
      throw new Error(MENSAJE_SALDO_POSITIVO_DONACION)
    }
    if (valor > saldoDonable) {
      throw new Error('No puedes donar tiempo prestado')
    }
    return valor
  }

  _validarMontoDonacionACausa(monto, saldoDonable, horasRecibidasDonacion, horasDeVidaSolicitante) {
    const montoValido = this._validarMontoDonacion(monto, saldoDonable)

    if (horasDeVidaSolicitante > TOPE_HORAS_RECIBIDAS_DONACION) {
      throw new Error(MENSAJE_RECEPTOR_MAS_10_HORAS)
    }

    const horasRestantesReceptor = calcularHorasRestantesReceptor(
      horasRecibidasDonacion,
      horasDeVidaSolicitante,
    )
    if (montoValido > horasRestantesReceptor) {
      throw new Error(MENSAJE_TOPE_HORAS_RECIBIDAS)
    }

    return montoValido
  }

  _mapSolicitudPublica(item) {
    return {
      id: item.id,
      categoria: item.categoria,
      titulo: item.titulo,
      descripcion: item.descripcion,
      horasRecibidas: Number(item.horas_recibidas || 0),
      estadoSocialSolicitante: item.estado_social_solicitante,
      solicitanteId: item.solicitante_id,
      solicitanteNombre: item.solicitante_nombre,
      horasRecibidasDonacionSolicitante: Number(item.horas_recibidas_donacion_solicitante || 0),
      horasDeVidaSolicitante: Number(item.horas_de_vida_solicitante || 0),
    }
  }

  _mapSolicitud(item) {
    return {
      id: item.id,
      categoria: item.categoria,
      titulo: item.titulo,
      descripcion: item.descripcion,
      estado: item.estado,
      horasRecibidas: Number(item.horas_recibidas || 0),
      horasSolidariasDisponibles: Number(item.horas_solidarias_disponibles || 0),
      horasSolidariasUtilizadas: Number(item.horas_solidarias_utilizadas || 0),
      publicacionId: item.publicacion_id ?? null,
      necesidadActiva: Boolean(item.necesidad_activa),
      estadoSocialSolicitante: item.estado_social_solicitante,
      solicitanteNombre: item.solicitante_nombre,
      creadoEl: item.creado_el,
    }
  }

  _mapUsuarioAdmin(item) {
    return {
      id: item.id,
      username: item.username,
      nombreReal: item.nombre_real,
      horasDeVida: Number(item.horas_de_vida || 0),
      estadoSocial: item.estado_social,
      horasRecibidasDonacion: Number(item.horas_recibidas_donacion || 0),
    }
  }

  _mapComprobante(comprobante) {
    if (!comprobante) return null

    return {
      id: comprobante.id,
      monto: Number(comprobante.monto),
      tipoDestino: comprobante.tipo_destino,
      receptorNombre: comprobante.receptor_nombre,
      comprobanteId: comprobante.comprobante_id,
      fecha: comprobante.fecha,
    }
  }

  _mapDonacionHistorial(item) {
    return {
      id: item.id,
      monto: Number(item.monto),
      tipoDestino: item.tipo_destino,
      fecha: item.fecha,
      comprobanteId: item.comprobante_id,
      donanteNombre: item.donante_nombre,
      receptorNombre: item.receptor_nombre,
      solicitudId: item.solicitud,
    }
  }

  _mapResultadoDonacion(data) {
    return {
      message: data?.message || '',
      monto: Number(data?.monto || 0),
      saldoRestante: Number(data?.saldo_restante ?? 0),
      receptorNombre: data?.receptor_nombre || '',
      saldoFondo: data?.saldo_fondo != null ? Number(data.saldo_fondo) : null,
      comprobante: this._mapComprobante(data?.comprobante),
    }
  }

  async obtenerSolicitudesAprobadas() {
    return this.execute(async () => {
      const data = await this.service.obtenerSolicitudesAprobadas()
      const solicitudes = (data?.solicitudes || []).map((item) => this._mapSolicitudPublica(item))

      return {
        solicitudes,
        cantidad: data?.cantidad ?? solicitudes.length,
      }
    })
  }

  async crearSolicitud(categoria, titulo, descripcion) {
    return this.execute(async () => {
      const categoriaValida = this._validarTexto(categoria, 'La categoría')
      const tituloValido = this._validarTexto(titulo, 'El título')
      const descripcionValida = this._validarTexto(descripcion, 'La descripción')

      if (!esCategoriaCausaSocialPermitida(categoriaValida)) {
        throw new Error(MENSAJE_CATEGORIA_CAUSA_INVALIDA)
      }
      if (!esTituloCausaSocialPermitido(tituloValido)) {
        throw new Error(MENSAJE_TITULO_CAUSA_INVALIDO)
      }
      if (categoriaParaTitulo(tituloValido) !== categoriaValida) {
        throw new Error(MENSAJE_CATEGORIA_TITULO_INCONSISTENTES)
      }

      const data = await this.service.crearSolicitud(categoriaValida, tituloValido, descripcionValida)

      return {
        solicitud: this._mapSolicitud(data),
        mensaje: MENSAJE_PENDIENTE_APROBACION,
      }
    })
  }

  async obtenerMisSolicitudes() {
    return this.execute(async () => {
      const data = await this.service.obtenerMisSolicitudes()
      const solicitudes = (data?.solicitudes || []).map((item) => this._mapSolicitud(item))

      return {
        solicitudes,
        cantidad: data?.cantidad ?? solicitudes.length,
      }
    })
  }

  async obtenerMisDonaciones() {
    return this.execute(async () => {
      const data = await this.service.obtenerMisDonaciones()
      const realizadas = (data?.realizadas || []).map((item) => this._mapDonacionHistorial(item))
      const recibidas = (data?.recibidas || []).map((item) => this._mapDonacionHistorial(item))

      return {
        realizadas,
        recibidas,
        cantidadRealizadas: data?.cantidad_realizadas ?? realizadas.length,
        cantidadRecibidas: data?.cantidad_recibidas ?? recibidas.length,
      }
    })
  }

  async activarNecesidadVinculada(solicitudId) {
    return this.execute(async () => {
      const id = Number(solicitudId)
      if (!Number.isInteger(id) || id <= 0) {
        throw new Error('Solicitud inválida.')
      }

      const data = await this.service.activarNecesidadVinculada(id)
      const solicitud = data?.solicitud ? this._mapSolicitud(data.solicitud) : null

      return {
        solicitud,
        publicacionId: data?.publicacion_id ?? solicitud?.publicacionId ?? null,
        mensaje: 'Necesidad activada en la cartelera.',
      }
    })
  }

  async donarACausa(solicitudId, monto, saldoDonable, horasRecibidasDonacion = 0, horasDeVidaSolicitante = 0) {
    return this.execute(async () => {
      const id = Number(solicitudId)
      if (!Number.isInteger(id) || id <= 0) {
        throw new Error('Debes seleccionar una causa válida.')
      }

      const montoValido = this._validarMontoDonacionACausa(
        monto,
        saldoDonable,
        horasRecibidasDonacion,
        horasDeVidaSolicitante,
      )
      const data = await this.service.donarACausa(id, montoValido)
      return this._mapResultadoDonacion(data)
    })
  }

  async donarAFondo(monto, saldoDonable) {
    return this.execute(async () => {
      const montoValido = this._validarMontoDonacion(monto, saldoDonable)
      const data = await this.service.donarAFondo(montoValido)
      return this._mapResultadoDonacion(data)
    })
  }

  _validarEstadoSocial(estadoSocial) {
    const estadosValidos = ['NINGUNO', 'VULNERABLE', 'CRITICO']
    if (!estadosValidos.includes(estadoSocial)) {
      throw new Error('Estado social inválido.')
    }
    return estadoSocial
  }

  _validarMontoAsignacion(monto, saldoFondo) {
    const valor = Number(monto)
    if (!Number.isFinite(valor) || valor < 0.5) {
      throw new Error('El monto mínimo de donación es 0.5 horas')
    }
    if (valor > saldoFondo) {
      throw new Error('El fondo comunitario no tiene saldo suficiente.')
    }
    return valor
  }

  async obtenerSolicitudesPendientesAdmin() {
    return this.execute(async () => {
      const data = await this.service.obtenerSolicitudesPendientes()
      const solicitudes = (data?.solicitudes || []).map((item) => this._mapSolicitud(item))

      return {
        solicitudes,
        cantidad: data?.cantidad ?? solicitudes.length,
      }
    })
  }

  async aprobarSolicitudAdmin(solicitudId) {
    return this.execute(async () => {
      const id = Number(solicitudId)
      if (!Number.isInteger(id) || id <= 0) {
        throw new Error('Solicitud inválida.')
      }

      const data = await this.service.aprobarSolicitud(id)
      return {
        solicitud: this._mapSolicitud(data),
        mensaje: data?.mensaje || MENSAJE_SOLICITANTE_MARCADO_VULNERABLE,
      }
    })
  }

  async rechazarSolicitudAdmin(solicitudId) {
    return this.execute(async () => {
      const id = Number(solicitudId)
      if (!Number.isInteger(id) || id <= 0) {
        throw new Error('Solicitud inválida.')
      }

      const data = await this.service.rechazarSolicitud(id)
      return {
        solicitud: this._mapSolicitud(data),
        mensaje: 'Solicitud rechazada correctamente.',
      }
    })
  }

  async obtenerUsuariosAdmin() {
    return this.execute(async () => {
      const data = await this.service.obtenerUsuariosAdmin()
      const usuarios = (data?.usuarios || []).map((item) => this._mapUsuarioAdmin(item))

      return {
        usuarios,
        cantidad: data?.cantidad ?? usuarios.length,
      }
    })
  }

  async actualizarEstadoSocialAdmin(usuarioId, estadoSocial) {
    return this.execute(async () => {
      const id = Number(usuarioId)
      if (!Number.isInteger(id) || id <= 0) {
        throw new Error('Usuario inválido.')
      }

      const estado = this._validarEstadoSocial(estadoSocial)
      const data = await this.service.actualizarEstadoSocial(id, estado)

      return {
        usuario: this._mapUsuarioAdmin(data),
        mensaje: `Estado social actualizado a ${estado}.`,
      }
    })
  }

  async obtenerSaldoFondoAdmin() {
    return this.execute(async () => {
      const data = await this.service.obtenerSaldoFondo()
      return {
        saldo: Number(data?.saldo || 0),
        username: data?.username || 'fondo_comunitario',
      }
    })
  }

  async asignarDesdeFondoAdmin(usuarioId, solicitudId, monto, saldoFondo) {
    return this.execute(async () => {
      const id = Number(usuarioId)
      if (!Number.isInteger(id) || id <= 0) {
        throw new Error('Debes seleccionar un usuario válido.')
      }

      const solicitud = Number(solicitudId)
      if (!Number.isInteger(solicitud) || solicitud <= 0) {
        throw new Error('Debes seleccionar una solicitud aprobada del receptor.')
      }

      const montoValido = this._validarMontoAsignacion(monto, saldoFondo)
      const data = await this.service.asignarDesdeFondo(id, solicitud, montoValido)

      return {
        mensaje: data?.mensaje || 'Asignación desde fondo realizada.',
        monto: Number(data?.monto || montoValido),
        saldoFondo: Number(data?.saldo_fondo ?? 0),
        saldoReceptor: Number(data?.saldo_receptor ?? 0),
        solicitudId: data?.solicitud_id ?? solicitud,
        horasSolidariasDisponibles: Number(data?.horas_solidarias_disponibles ?? 0),
        receptorId: data?.receptor_id,
      }
    })
  }
}
