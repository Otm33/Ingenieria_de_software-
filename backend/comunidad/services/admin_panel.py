"""
Capa de Servicios — Panel de Administracion (Sprint 2 HU3).

Orquesta CRUD completo sobre todas las entidades del sistema.
Cada metodo valida que el usuario sea administrador antes de ejecutar.
"""
from ..negocio.admin import (
    validar_es_administrador,
    validar_puede_eliminar_usuario,
    validar_puede_cambiar_rol,
    validar_busqueda,
)
from ..interfaces.service_interfaces import AdminPanelInterface
from ..repositorios_implementacion import (
    UsuarioRepository,
    PublicacionRepository,
    TruequeRepository,
    ResenaRepository,
    TruequeMultipleRepository,
    SaldoComercialRepository,
    ResenaMultipleRepository,
)


class AdminPanelService(AdminPanelInterface):
    """Implementacion del servicio de administracion completo."""

    def __init__(
        self,
        usuario_repo=None,
        publicacion_repo=None,
        trueque_repo=None,
        resena_repo=None,
        trueque_multiple_repo=None,
        saldo_repo=None,
        resena_multiple_repo=None,
    ):
        self.usuario_repo = usuario_repo or UsuarioRepository()
        self.publicacion_repo = publicacion_repo or PublicacionRepository()
        self.trueque_repo = trueque_repo or TruequeRepository()
        self.resena_repo = resena_repo or ResenaRepository()
        self.trueque_multiple_repo = trueque_multiple_repo or TruequeMultipleRepository()
        self.saldo_repo = saldo_repo or SaldoComercialRepository()
        self.resena_multiple_repo = resena_multiple_repo or ResenaMultipleRepository()

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def obtener_dashboard(self, admin):
        validar_es_administrador(admin)
        from backend.comunidad.models import (
            Publicacion, AcuerdoTrueque, Resena,
            AcuerdoTruequeMultiple, ResenaMultiple, SaldoComercial,
        )
        stats_usuarios = self.usuario_repo.contar_estadisticas()
        return {
            'usuarios': stats_usuarios,
            'publicaciones': {
                'total': Publicacion.objects.count(),
                'activas': Publicacion.objects.filter(esta_activa=True).count(),
            },
            'trueques': {
                'total': AcuerdoTrueque.objects.count(),
                'finalizados': AcuerdoTrueque.objects.filter(estado='FINALIZADO').count(),
                'pendientes': AcuerdoTrueque.objects.filter(estado='PENDIENTE').count(),
            },
            'trueques_multiples': {
                'total': AcuerdoTruequeMultiple.objects.count(),
                'finalizados': AcuerdoTruequeMultiple.objects.filter(estado='FINALIZADO').count(),
            },
            'resenas': {
                'total': Resena.objects.count(),
            },
            'resenas_multiples': {
                'total': ResenaMultiple.objects.count(),
            },
            'saldos': {
                'total_movimientos': SaldoComercial.objects.count(),
            },
        }

    # ── Usuarios ──────────────────────────────────────────────────────────────

    def listar_usuarios(self, admin, busqueda=None):
        validar_es_administrador(admin)
        termino = validar_busqueda(busqueda)
        return self.usuario_repo.listar_todos(termino)

    def toggle_usuario(self, admin, usuario_id):
        validar_es_administrador(admin)
        usuario = self.usuario_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError('Usuario no encontrado.')
        return self.usuario_repo.actualizar_estado(usuario_id, not usuario.is_active)

    def cambiar_rol(self, admin, usuario_id, is_staff):
        validar_es_administrador(admin)
        validar_puede_cambiar_rol(admin)
        usuario = self.usuario_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError('Usuario no encontrado.')
        return self.usuario_repo.actualizar_rol(usuario_id, is_staff)

    def eliminar_usuario(self, admin, usuario_id):
        validar_es_administrador(admin)
        validar_puede_eliminar_usuario(admin.id, usuario_id)
        usuario = self.usuario_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError('Usuario no encontrado.')
        self.usuario_repo.eliminar(usuario_id)
        return {'eliminado': True}

    # ── Publicaciones ─────────────────────────────────────────────────────────

    def listar_publicaciones(self, admin, busqueda=None):
        validar_es_administrador(admin)
        termino = validar_busqueda(busqueda)
        return self.publicacion_repo.listar_todas(termino)

    def crear_publicacion_admin(self, admin, datos):
        validar_es_administrador(admin)
        if not datos.get('titulo'):
            raise ValueError('El titulo es requerido.')
        if not datos.get('descripcion'):
            raise ValueError('La descripcion es requerida.')
        if not datos.get('categoria'):
            raise ValueError('La categoria es requerida.')
        return self.publicacion_repo.crear(admin.id, {
            'tipo': datos.get('tipo', 'TALENTO'),
            'titulo': datos['titulo'],
            'descripcion': datos['descripcion'],
            'categoria': datos['categoria'],
            'urgencia': datos.get('urgencia', 'NORMAL'),
            'esta_activa': datos.get('esta_activa', True),
        })

    def moderar_publicacion(self, admin, publicacion_id, esta_activa):
        validar_es_administrador(admin)
        return self.publicacion_repo.actualizar_estado_admin(publicacion_id, esta_activa)

    def eliminar_publicacion(self, admin, publicacion_id):
        validar_es_administrador(admin)
        pub = self.publicacion_repo.obtener_por_id(publicacion_id)
        if not pub:
            raise ValueError('Publicacion no encontrada.')
        self.publicacion_repo.eliminar(publicacion_id)
        return {'eliminado': True}

    # ── Trueques ──────────────────────────────────────────────────────────────

    def listar_trueques(self, admin, busqueda=None):
        validar_es_administrador(admin)
        termino = validar_busqueda(busqueda)
        return self.trueque_repo.listar_todos(termino)

    def actualizar_estado_trueque(self, admin, trueque_id, estado):
        validar_es_administrador(admin)
        estados_validos = ['PENDIENTE', 'ACEPTADO', 'RECHAZADO', 'EN_CURSO', 'FINALIZADO']
        if estado not in estados_validos:
            raise ValueError(f'Estado invalido. Debe ser uno de: {", ".join(estados_validos)}')
        return self.trueque_repo.actualizar_estado_admin(trueque_id, estado)

    def eliminar_trueque(self, admin, trueque_id):
        validar_es_administrador(admin)
        trueque = self.trueque_repo.obtener_por_id(trueque_id)
        if not trueque:
            raise ValueError('Trueque no encontrado.')
        self.trueque_repo.eliminar(trueque_id)
        return {'eliminado': True}

    # ── Trueques Multiples ────────────────────────────────────────────────────

    def listar_trueques_multiples(self, admin, busqueda=None):
        validar_es_administrador(admin)
        termino = validar_busqueda(busqueda)
        return self.trueque_multiple_repo.listar_todos(termino)

    def actualizar_estado_trueque_multiple(self, admin, trueque_id, estado):
        validar_es_administrador(admin)
        estados_validos = ['PENDIENTE', 'ACEPTADO', 'RECHAZADO', 'EN_CURSO', 'FINALIZADO', 'EXPIRADO']
        if estado not in estados_validos:
            raise ValueError(f'Estado invalido. Debe ser uno de: {", ".join(estados_validos)}')
        return self.trueque_multiple_repo.actualizar_estado_admin(trueque_id, estado)

    def eliminar_trueque_multiple(self, admin, trueque_id):
        validar_es_administrador(admin)
        tm = self.trueque_multiple_repo.obtener_por_id(trueque_id)
        if not tm:
            raise ValueError('Trueque multiple no encontrado.')
        self.trueque_multiple_repo.eliminar(trueque_id)
        return {'eliminado': True}

    # ── Resenas ───────────────────────────────────────────────────────────────

    def listar_resenas(self, admin, busqueda=None):
        validar_es_administrador(admin)
        termino = validar_busqueda(busqueda)
        return self.resena_repo.listar_todas(termino)

    def eliminar_resena(self, admin, resena_id):
        validar_es_administrador(admin)
        self.resena_repo.eliminar(resena_id)
        return {'eliminado': True}

    # ── Resenas Multiples ─────────────────────────────────────────────────────

    def listar_resenas_multiples(self, admin, busqueda=None):
        validar_es_administrador(admin)
        termino = validar_busqueda(busqueda)
        return self.resena_multiple_repo.listar_todas(termino)

    def eliminar_resena_multiple(self, admin, resena_id):
        validar_es_administrador(admin)
        self.resena_multiple_repo.eliminar(resena_id)
        return {'eliminado': True}

    # ── Saldos Comerciales ────────────────────────────────────────────────────

    def listar_saldos(self, admin, busqueda=None):
        validar_es_administrador(admin)
        termino = validar_busqueda(busqueda)
        return self.saldo_repo.listar_todos(termino)
