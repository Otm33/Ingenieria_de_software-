import BaseController from './BaseController.js'
import PublicacionRepository from '../repositories/PublicacionRepository.js'
import { ref, reactive } from 'vue'
import { CATEGORIAS } from '../data/catalogoServicios.js'

/**
 * CarteleraController - Controlador para HU3: Cartelera y filtros
 * Maneja toda la lógica de negocio de la cartelera del frontend
 * con estado reactivo y caché en memoria
 */
export default class CarteleraController extends BaseController {
  constructor(publicacionRepository = null) {
    super()
    this.publicacionRepository = publicacionRepository || new PublicacionRepository()
    
    // Estado reactivo de la cartelera
    this.publicaciones = ref([])
    this.filtrosAplicados = reactive({
      categoria: '',
      urgencias: []
    })
    this.estaEnModoPublicar = ref(false)
    
    // Estado de publicación
    this.formularioPublicacion = reactive({
      tipo: 'TALENTO',
      titulo: '',
      descripcion: '',
      categoria: '',
      urgencia: 'NORMAL'
    })
    
    // Estado de mis publicaciones
    this.misPublicaciones = ref([])
    this.procesandoEstadoId = ref(null)
  }

  /**
   * Obtiene la cartelera con filtros aplicados
   * HU3: Visualizar publicaciones con filtros
   */
  async cargarCartelera(filtros = {}, forceRefresh = false) {
    return this.execute(async () => {
      const publicaciones = await this.publicacionRepository.obtenerCartelera(
        filtros,
        forceRefresh
      )
      
      // Actualizar estado reactivo
      this.publicaciones.value = publicaciones
      this.filtrosAplicados.categoria = filtros.categoria || ''
      this.filtrosAplicados.urgencias = filtros.urgencias || []
      
      return publicaciones
    })
  }

  /**
   * Aplica los filtros actuales a la cartelera
   */
  async aplicarFiltros() {
    const filtros = {
      categoria: this.filtrosAplicados.categoria || undefined,
      urgencias: this.filtrosAplicados.urgencias.length > 0 
        ? this.filtrosAplicados.urgencias 
        : undefined
    }
    
    return this.cargarCartelera(filtros, true) // forceRefresh para aplicar filtros
  }

  /**
   * Restablece los filtros a valores por defecto
   */
  async restablecerFiltros() {
    this.filtrosAplicados.categoria = ''
    this.filtrosAplicados.urgencias = []
    return this.cargarCartelera({}, true)
  }

  /**
   * Cambia al modo de publicación
   */
  activarModoPublicar() {
    this.estaEnModoPublicar.value = true
    this.limpiarFormularioPublicacion()
  }

  /**
   * Cambia al modo de visualización
   */
  desactivarModoPublicar() {
    this.estaEnModoPublicar.value = false
  }

  /**
   * Carga las publicaciones del usuario actual
   */
  async cargarMisPublicaciones(forceRefresh = false) {
    return this.execute(async () => {
      const publicaciones = await this.publicacionRepository.obtenerMisPublicaciones(forceRefresh)
      
      // Actualizar estado reactivo
      this.misPublicaciones.value = publicaciones
      
      return publicaciones
    })
  }

  /**
   * Crea una nueva publicación
   * HU3: Publicar talentos y necesidades
   */
  async crearPublicacion(authController) {
    return this.execute(async () => {
      // Requerir autenticación
      authController.requireAuth()
      
      // Validaciones frontend
      if (!this.formularioPublicacion.categoria) {
        throw new Error('La categoría es requerida.')
      }

      if (!this.formularioPublicacion.titulo) {
        throw new Error('El título es requerido.')
      }

      if (!this.formularioPublicacion.descripcion?.trim()) {
        throw new Error('La descripción es requerida.')
      }

      if (this.formularioPublicacion.descripcion.length < 10) {
        throw new Error('La descripción debe tener al menos 10 caracteres.')
      }

      // Validar categoría
      if (!CATEGORIAS.includes(this.formularioPublicacion.categoria)) {
        throw new Error('La categoría seleccionada no es válida.')
      }

      // Validar urgencia para talentos
      if (this.formularioPublicacion.tipo === 'TALENTO' && 
          this.formularioPublicacion.urgencia !== 'NORMAL') {
        throw new Error('Los talentos solo pueden tener urgencia Normal.')
      }

      const datos = {
        tipo: this.formularioPublicacion.tipo,
        titulo: this.formularioPublicacion.titulo,
        descripcion: this.formularioPublicacion.descripcion,
        categoria: this.formularioPublicacion.categoria,
        urgencia: this.formularioPublicacion.urgencia
      }

      const publicacion = await this.publicacionRepository.crearPublicacion(datos)
      
      // Actualizar caché local
      this.misPublicaciones.value.unshift(publicacion)
      
      // Invalidar caché de cartelera
      this.publicacionRepository.invalidateCartelera()
      
      // Salir del modo de publicación
      this.desactivarModoPublicar()
      
      return publicacion
    })
  }

  /**
   * Actualiza el estado de una publicación (pausar/reactivar)
   */
  async actualizarEstadoPublicacion(publicacionId, estaActiva) {
    return this.execute(async () => {
      this.procesandoEstadoId.value = publicacionId
      
      try {
        const publicacion = await this.publicacionRepository.actualizarEstadoPublicacion(
          publicacionId,
          estaActiva
        )
        
        // Actualizar estado local
        const index = this.misPublicaciones.value.findIndex(p => p.id === publicacionId)
        if (index !== -1) {
          this.misPublicaciones.value[index] = publicacion
        }
        
        // Invalidar caché
        this.publicacionRepository.invalidateCartelera()
        this.publicacionRepository.invalidateMisPublicaciones()
        
        return publicacion
      } finally {
        this.procesandoEstadoId.value = null
      }
    })
  }

  /**
   * Pausa una publicación
   */
  async pausarPublicacion(publicacionId) {
    return this.actualizarEstadoPublicacion(publicacionId, false)
  }

  /**
   * Reactiva una publicación
   */
  async reactivarPublicacion(publicacionId) {
    return this.actualizarEstadoPublicacion(publicacionId, true)
  }

  /**
   * Limpia el formulario de publicación
   */
  limpiarFormularioPublicacion() {
    this.formularioPublicacion.tipo = 'TALENTO'
    this.formularioPublicacion.titulo = ''
    this.formularioPublicacion.descripcion = ''
    this.formularioPublicacion.categoria = ''
    this.formularioPublicacion.urgencia = 'NORMAL'
  }

  /**
   * Retorna las categorías disponibles
   */
  getCategorias() {
    return CATEGORIAS
  }

  /**
   * Retorna el número de publicaciones críticas
   */
  getTotalCriticas() {
    return this.publicaciones.value.filter(p => p.esCritica()).length
  }

  /**
   * Retorna el número de talentos
   */
  getTotalTalentos() {
    return this.publicaciones.value.filter(p => p.esTalento()).length
  }

  async crearPublicacionDesdeDatos(formulario) {
    return this.execute(async () => {
      if (!formulario.categoria) {
        throw new Error('La categoría es requerida.')
      }
      if (!formulario.titulo) {
        throw new Error('El título es requerido.')
      }
      if (!formulario.descripcion?.trim()) {
        throw new Error('La descripción es requerida.')
      }
      if (formulario.descripcion.length < 10) {
        throw new Error('La descripción debe tener al menos 10 caracteres.')
      }
      if (formulario.tipo === 'TALENTO' && formulario.urgencia !== 'NORMAL') {
        throw new Error('Los talentos solo pueden tener urgencia Normal.')
      }

      const publicacion = await this.publicacionRepository.crearPublicacion(formulario)
      this.misPublicaciones.value.unshift(publicacion)
      this.publicacionRepository.invalidateCartelera()
      return publicacion
    })
  }

  async obtenerCartelera(filtros = {}, forceRefresh = false) {
    return this.cargarCartelera(filtros, forceRefresh)
  }

  async obtenerMisPublicaciones(forceRefresh = false) {
    return this.cargarMisPublicaciones(forceRefresh)
  }

  /**
   * Invalida toda la caché de publicaciones
   */
  invalidateAllCache() {
    this.publicacionRepository.invalidateAll()
  }
}
