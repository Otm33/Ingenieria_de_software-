import BaseController from './BaseController.js'
import User from '../models/User.js'
import Publicacion from '../models/Publicacion.js'
import Trueque from '../models/Trueque.js'

export default class TruequeController extends BaseController {
  constructor(service) {
    super()
    this.service = service
  }

  validarCombinacionPropuesta({
    receptorId,
    modoPropuesta,
    publicacionEmisor,
    publicacionReceptor,
  }) {
    if (!receptorId) {
      throw new Error('Falta el receptor de la propuesta.')
    }
    if (!publicacionEmisor || !publicacionReceptor) {
      throw new Error('Selecciona ambas publicaciones para continuar.')
    }

    const esModoComunidad = modoPropuesta === 'pedir_ayuda' || modoPropuesta === 'ofrecer_ayuda'
    if (!esModoComunidad) {
      return
    }

    if (modoPropuesta === 'pedir_ayuda') {
      if (publicacionEmisor.tipo !== 'NECESIDAD' || publicacionReceptor.tipo !== 'TALENTO') {
        throw new Error('En este modo debes elegir tu necesidad y un talento del vecino.')
      }
    }

    if (modoPropuesta === 'ofrecer_ayuda') {
      if (publicacionEmisor.tipo !== 'TALENTO' || publicacionReceptor.tipo !== 'NECESIDAD') {
        throw new Error('En este modo debes elegir tu talento y una necesidad del vecino.')
      }
    }
  }

  _normalizarMatchDetalle(matchDetalle) {
    if (!Array.isArray(matchDetalle) || !matchDetalle.length) {
      return null
    }

    return matchDetalle.map((entrada) => ({
      rol: entrada.rol || '',
      mi_titulo: entrada.mi_titulo || '',
      mi_tipo: entrada.mi_tipo || '',
      su_titulo: entrada.su_titulo || '',
      su_tipo: entrada.su_tipo || '',
    }))
  }

  _mapNotificacion(notificacion) {
    return {
      ...notificacion,
      match_detalle: this._normalizarMatchDetalle(notificacion.match_detalle),
    }
  }

  _mapMatchEnriquecido(match) {
    return {
      usuario: new User(match.usuario),
      talentosCoincidentes: (match.talentos_coincidentes || []).map(
        (publicacion) => new Publicacion(publicacion),
      ),
      necesidadesCoincidentes: (match.necesidades_coincidentes || []).map(
        (publicacion) => new Publicacion(publicacion),
      ),
      publicacionesSugeridas: match.publicaciones_sugeridas || [],
    }
  }

  filtrarNotificacionesAccionables(notificaciones) {
    return (notificaciones || []).filter((notif) => notif.estado === 'PENDIENTE')
  }

  async verificarCoincidenciaPorTitulo(publicacionId) {
    return this.execute(() => this.service.verificarCoincidenciaPorTitulo(publicacionId))
  }

  async obtenerMatches(publicacionId = null) {
    return this.execute(async () => {
      const data = await this.service.obtenerMatchesEnriquecidos(publicacionId)
      return (data.matches || []).map((match) => new User(match.usuario))
    })
  }

  async obtenerMatchesEnriquecidos(publicacionId = null) {
    return this.execute(async () => {
      const data = await this.service.obtenerMatchesEnriquecidos(publicacionId)
      const matches = (data.matches || []).map((match) => this._mapMatchEnriquecido(match))

      return {
        matches,
        mensaje: data.mensaje || '',
        cantidad: data.cantidad ?? matches.length,
      }
    })
  }

  async crearPropuesta(receptorId, publicacionEmisorId, publicacionReceptorId, contextoValidacion = null) {
    return this.execute(async () => {
      if (contextoValidacion) {
        this.validarCombinacionPropuesta(contextoValidacion)
      }
      if (!publicacionEmisorId || !publicacionReceptorId) {
        throw new Error('Selecciona ambas publicaciones para continuar.')
      }

      return await this.service.crearPropuesta(
        receptorId,
        publicacionEmisorId,
        publicacionReceptorId,
      )
    })
  }

  async responderPropuesta(truequeId, accion) {
    return this.execute(() => this.service.responderPropuesta(truequeId, accion))
  }

  async finalizarTrueque(truequeId) {
    return this.execute(() => this.service.finalizarTrueque(truequeId))
  }

  async obtenerNotificaciones(incluirLeidas = false) {
    return this.execute(async () => {
      const data = await this.service.obtenerNotificaciones(incluirLeidas)
      const notificaciones = (data.notificaciones || []).map((notificacion) => (
        this._mapNotificacion(notificacion)
      ))

      return {
        notificaciones,
        cantidad: data.cantidad ?? notificaciones.length,
      }
    })
  }

  async marcarNotificacionLeida(notificacionId) {
    return this.execute(() => this.service.marcarNotificacionLeida(notificacionId))
  }

  async marcarNotificacionesTruequeLeidas(truequeId) {
    return this.execute(() => this.service.marcarNotificacionesTruequeLeidas(truequeId))
  }

  async obtenerMisTrueques() {
    return this.execute(async () => {
      const data = await this.service.obtenerMisTrueques()
      const trueques = (data.trueques || []).map((trueque) => Trueque.fromApi(trueque))

      return {
        trueques,
        cantidad: data.cantidad ?? trueques.length,
      }
    })
  }

  async cargarDatosHu4(carteleraController) {
    return this.execute(async () => {
      const [notificacionesData, truequesData, misPublicaciones] = await Promise.all([
        this.service.obtenerNotificaciones(false).then((data) => ({
          notificaciones: (data.notificaciones || []).map((notificacion) => (
            this._mapNotificacion(notificacion)
          )),
        })),
        this.service.obtenerMisTrueques().then((data) => ({
          trueques: (data.trueques || []).map((trueque) => Trueque.fromApi(trueque)),
        })),
        carteleraController.obtenerMisPublicaciones(),
      ])

      return {
        notificaciones: this.filtrarNotificacionesAccionables(notificacionesData.notificaciones),
        trueques: truequesData.trueques,
        misPublicaciones,
      }
    })
  }
}
