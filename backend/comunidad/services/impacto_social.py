"""
Sprint 2 HU1: Servicio de Impacto Social — Donaciones solidarias de Horas de Vida.
Capa de Negocios / Lógica: sin conocimiento tecnológico directo.
Coordina repositorios y aplica reglas de negocio de impacto social.
"""
from django.db import transaction

from .base import BusinessError
from ..catalogo_causas_sociales import (
    es_titulo_causa_social_permitido,
    es_categoria_causa_social_permitida,
    categoria_para_titulo,
)
from ..interfaces.service_interfaces import ImpactoSocialInterface

# ── Mensajes de negocio (constantes, sin lógica) ─────────────────────────────
MSG_SALDO_POSITIVO_DONACION = "Necesitas saldo positivo para realizar donaciones solidarias"
MSG_TIEMPO_PRESTADO = "No puedes donar tiempo prestado"
MSG_MONTO_MINIMO_DONACION = "El monto mínimo de donación es 0.5 horas"
MSG_COMERCIO_NO_IMPACTO = "Los comercios no pueden realizar donaciones solidarias"
MSG_RECEPTOR_MAS_10_HORAS = "Usuarios con más de 10 horas no pueden recibir donaciones"
MSG_TOPE_HORAS_RECIBIDAS = "No se puede donar más de 10 horas a este usuario"
MSG_SOLO_VULNERABLE_CRITICO = "Solo se puede asignar a usuarios vulnerables o críticos"
MSG_DONACION_EXITOSA = "Donación Exitosa"
MSG_NO_DONAR_PROPIA_CAUSA = "No puedes donar horas a tu propia causa."
MSG_SOLICITUD_REQUERIDA = "Debes indicar la solicitud a la que asignar las horas."
MSG_SIN_SOLICITUD_APROBADA = "El usuario no tiene solicitudes aprobadas."
MSG_SOLICITUD_NO_PERTENECE = "La solicitud no pertenece al usuario receptor."
MSG_SOLICITUD_NO_APROBADA = "Solo puedes activar necesidades de solicitudes aprobadas."
MSG_NECESIDAD_YA_VINCULADA = "Esta solicitud ya tiene una necesidad vinculada."
MSG_NO_ACTIVAR_AJENA = "No puedes activar la necesidad de una solicitud ajena."
MSG_SIN_PERMISOS_ADMIN = "No tienes permisos de administrador."
MSG_TITULO_INVALIDO = "El título seleccionado no corresponde a una causa social permitida."
MSG_CATEGORIA_INVALIDA = "La categoría seleccionada no es válida para causas sociales."
MSG_CATEGORIA_TITULO_INCONSISTENTES = "El título no pertenece a la categoría seleccionada."
MSG_SOLICITANTE_VULNERABLE = "Solicitud aprobada. El solicitante fue catalogado como Usuario Vulnerable."


# ── Validaciones auxiliares (funciones puras) ─────────────────────────────────

def _validar_no_comercio(usuario):
    if getattr(usuario, 'es_comercio', False):
        raise BusinessError(MSG_COMERCIO_NO_IMPACTO, status_code=403)


def _validar_admin(usuario):
    if not (getattr(usuario, 'is_staff', False) or getattr(usuario, 'is_superuser', False)):
        raise BusinessError(MSG_SIN_PERMISOS_ADMIN, status_code=403)


def _validar_monto(monto) -> float:
    try:
        monto = float(monto)
    except (TypeError, ValueError):
        raise BusinessError(MSG_MONTO_MINIMO_DONACION)
    if monto < 0.5:
        raise BusinessError(MSG_MONTO_MINIMO_DONACION)
    return monto


def _validar_donante_puede_donar(donante_orm, monto: float):
    _validar_no_comercio(donante_orm)
    if donante_orm.horas_de_vida <= 0:
        raise BusinessError(MSG_SALDO_POSITIVO_DONACION)
    if donante_orm.horas_de_vida - monto < 0:
        raise BusinessError(MSG_TIEMPO_PRESTADO)


def _validar_receptor_puede_recibir(receptor_orm, monto: float):
    if getattr(receptor_orm, 'es_fondo_comunitario', False):
        return  # el fondo siempre puede recibir
    if receptor_orm.horas_de_vida > 10:
        raise BusinessError(MSG_RECEPTOR_MAS_10_HORAS)
    if receptor_orm.horas_recibidas_donacion + monto > 10:
        raise BusinessError(MSG_TOPE_HORAS_RECIBIDAS)


# ── ImpactoSocialService ──────────────────────────────────────────────────────

class ImpactoSocialService(ImpactoSocialInterface):
    """
    Sprint 2 HU1: Donaciones solidarias y gestión de apoyo social.
    Capa Negocios: orquesta repositorios, aplica reglas de dominio.
    Sin imports de models ni acceso directo a ORM.
    """

    def __init__(
        self,
        solicitud_repository=None,
        donacion_repository=None,
        usuario_repository=None,
        publicacion_repository=None,
        matchmaking_service=None,
        usuario_social_repository=None,
    ):
        # Importaciones tardías para evitar ciclos
        from ..repositorios_implementacion import (
            SolicitudApoyoSocialRepository,
            DonacionHorasRepository,
            UsuarioRepository,
            PublicacionRepository,
            UsuarioSocialRepository,
        )
        self._solicitud_repo = solicitud_repository or SolicitudApoyoSocialRepository()
        self._donacion_repo = donacion_repository or DonacionHorasRepository()
        self._usuario_repo = usuario_repository or UsuarioRepository()
        self._pub_repo = publicacion_repository or PublicacionRepository()
        self._matchmaking_service = matchmaking_service
        self._social_repo = usuario_social_repository or UsuarioSocialRepository()

    # ── Solicitudes ───────────────────────────────────────────────────────────

    def crear_solicitud(self, usuario_orm, datos: dict):
        """Crea una solicitud de apoyo social. Solo usuarios no-comercio."""
        _validar_no_comercio(usuario_orm)

        categoria = (datos.get("categoria") or "").strip()
        if not categoria or not es_categoria_causa_social_permitida(categoria):
            raise BusinessError(MSG_CATEGORIA_INVALIDA)

        titulo = (datos.get("titulo") or "").strip()
        if not titulo or not es_titulo_causa_social_permitido(titulo):
            raise BusinessError(MSG_TITULO_INVALIDO)

        if categoria_para_titulo(titulo) != categoria:
            raise BusinessError(MSG_CATEGORIA_TITULO_INCONSISTENTES)

        descripcion = (datos.get("descripcion") or "").strip()
        if not descripcion:
            raise BusinessError("Descripción es obligatoria.")

        return self._solicitud_repo.crear(usuario_orm.id, categoria, titulo, descripcion)

    def listar_solicitudes_aprobadas(self) -> list:
        """Lista solicitudes aprobadas con detalles del solicitante."""
        return self._solicitud_repo.listar_aprobadas()

    def listar_mis_solicitudes(self, usuario_orm) -> list:
        """Lista las solicitudes del usuario autenticado."""
        return self._solicitud_repo.listar_por_solicitante(usuario_orm.id)

    def activar_necesidad_vinculada(self, usuario_orm, solicitud_id: int):
        """
        Publica una NECESIDAD en cartelera vinculada a una solicitud aprobada.
        Las publicaciones es_causa_social=True no cuentan contra el límite de 3.
        """
        _validar_no_comercio(usuario_orm)

        solicitud_orm = self._solicitud_repo.obtener_orm(solicitud_id)
        if not solicitud_orm:
            raise BusinessError("Solicitud no encontrada.", status_code=404)

        if solicitud_orm.solicitante_id != usuario_orm.id:
            raise BusinessError(MSG_NO_ACTIVAR_AJENA)

        if solicitud_orm.estado != "APROBADA":
            raise BusinessError(MSG_SOLICITUD_NO_APROBADA)

        if solicitud_orm.publicacion_id is not None:
            raise BusinessError(MSG_NECESIDAD_YA_VINCULADA)

        with transaction.atomic():
            publicacion = self._pub_repo.crear_causa_social(
                usuario_id=usuario_orm.id,
                titulo=solicitud_orm.titulo,
                descripcion=solicitud_orm.descripcion,
                categoria=solicitud_orm.categoria,
            )
            self._solicitud_repo.vincular_publicacion(solicitud_id, publicacion.id)

        # Detección de matches (no falla si hay error)
        try:
            servicio = self._matchmaking_service
            if servicio is None:
                from .matchmaking import MatchmakingService
                servicio = MatchmakingService()
            servicio.detectar_y_notificar_matches(usuario_orm)
        except Exception:
            pass

        return self._solicitud_repo.obtener_orm(solicitud_id)

    # ── Admin: Gestión de solicitudes ─────────────────────────────────────────

    def listar_solicitudes_pendientes(self, admin_orm) -> list:
        """Admin: lista solicitudes pendientes de revisión."""
        _validar_admin(admin_orm)
        return self._solicitud_repo.listar_pendientes()

    def aprobar_solicitud(self, admin_orm, solicitud_id: int):
        """Admin: aprueba una solicitud y marca al solicitante como VULNERABLE si es NINGUNO."""
        _validar_admin(admin_orm)

        solicitud_orm = self._solicitud_repo.obtener_orm(solicitud_id)
        if not solicitud_orm:
            raise BusinessError("Solicitud no encontrada.", status_code=404)

        if solicitud_orm.estado != "PENDIENTE":
            raise BusinessError("Solo se pueden aprobar solicitudes pendientes.")

        with transaction.atomic():
            sol, marcado_vulnerable = self._solicitud_repo.aprobar(solicitud_id, admin_orm.id)

        sol.solicitante_marcado_vulnerable = marcado_vulnerable
        return sol

    def rechazar_solicitud(self, admin_orm, solicitud_id: int):
        """Admin: rechaza una solicitud pendiente."""
        _validar_admin(admin_orm)

        solicitud_orm = self._solicitud_repo.obtener_orm(solicitud_id)
        if not solicitud_orm:
            raise BusinessError("Solicitud no encontrada.", status_code=404)

        if solicitud_orm.estado != "PENDIENTE":
            raise BusinessError("Solo se pueden rechazar solicitudes pendientes.")

        return self._solicitud_repo.rechazar(solicitud_id, admin_orm.id)

    def actualizar_estado_social(self, admin_orm, usuario_id: int, estado_social: str):
        """Admin: cambia el estado social de un usuario (NINGUNO/VULNERABLE/CRITICO)."""
        _validar_admin(admin_orm)

        estados_validos = {"NINGUNO", "VULNERABLE", "CRITICO"}
        if estado_social not in estados_validos:
            raise BusinessError("Estado social inválido.")

        return self._social_repo.actualizar_estado_social(usuario_id, estado_social)

    def listar_usuarios_para_admin(self, admin_orm) -> list:
        """Admin: lista usuarios regulares para gestión de estado social."""
        _validar_admin(admin_orm)
        return self._social_repo.listar_usuarios_regulares()

    def obtener_saldo_fondo(self, admin_orm=None) -> dict:
        """Retorna el saldo actual del fondo comunitario."""
        if admin_orm is not None:
            _validar_admin(admin_orm)
        fondo = self._social_repo.obtener_fondo_comunitario()
        return {"saldo": fondo.horas_de_vida, "username": fondo.username}

    # ── Donaciones ────────────────────────────────────────────────────────────

    def donar_a_causa(self, donante_orm, solicitud_id: int, monto):
        """Dona horas directamente a la causa de un solicitante aprobado."""
        monto = _validar_monto(monto)

        solicitud = self._social_repo.obtener_receptor_para_donacion(solicitud_id)

        if solicitud.estado != "APROBADA":
            raise BusinessError("Solo se puede donar a solicitudes aprobadas.")

        if donante_orm.id == solicitud.solicitante_id:
            raise BusinessError(MSG_NO_DONAR_PROPIA_CAUSA)

        _validar_donante_puede_donar(donante_orm, monto)
        _validar_receptor_puede_recibir(solicitud.solicitante, monto)

        with transaction.atomic():
            resultado = self._donacion_repo.ejecutar_donacion_a_causa(
                donante_id=donante_orm.id,
                receptor_id=solicitud.solicitante_id,
                solicitud_id=solicitud_id,
                monto=monto,
            )

        return {
            "mensaje": MSG_DONACION_EXITOSA,
            "monto": monto,
            "tipo_destino": "CAUSA",
            "receptor_id": resultado["receptor_id"],
            "receptor_nombre": resultado["receptor_nombre"],
            "saldo_restante": resultado["donante_saldo"],
            "comprobante_id": resultado["comprobante_id"],
            "donacion_id": resultado["donacion_id"],
        }

    def donar_a_fondo(self, donante_orm, monto):
        """Dona horas al fondo comunitario."""
        monto = _validar_monto(monto)
        _validar_donante_puede_donar(donante_orm, monto)
        fondo = self._social_repo.obtener_fondo_comunitario()

        with transaction.atomic():
            resultado = self._donacion_repo.ejecutar_donacion_a_fondo(
                donante_id=donante_orm.id,
                fondo_id=fondo.id,
                monto=monto,
            )

        return {
            "mensaje": MSG_DONACION_EXITOSA,
            "monto": monto,
            "tipo_destino": "FONDO",
            "receptor_id": resultado["receptor_id"],
            "receptor_nombre": resultado["receptor_nombre"],
            "saldo_restante": resultado["donante_saldo"],
            "comprobante_id": resultado["comprobante_id"],
            "donacion_id": resultado["donacion_id"],
        }

    def asignar_desde_fondo(self, admin_orm, usuario_id: int, monto, solicitud_id=None):
        """Admin: transfiere horas del fondo comunitario a un usuario vulnerable/crítico."""
        _validar_admin(admin_orm)
        monto = _validar_monto(monto)

        receptor = self._social_repo.obtener_receptor_orm(usuario_id)

        if receptor.estado_social not in ("VULNERABLE", "CRITICO"):
            raise BusinessError(MSG_SOLO_VULNERABLE_CRITICO)

        # Resolver la solicitud destino
        solicitud = self._solicitud_repo.resolver_solicitud_asignacion(receptor.id, solicitud_id)
        _validar_receptor_puede_recibir(receptor, monto)

        fondo = self._social_repo.obtener_fondo_comunitario()

        with transaction.atomic():
            resultado = self._donacion_repo.ejecutar_asignacion_fondo(
                fondo_id=fondo.id,
                receptor_id=receptor.id,
                solicitud_id=solicitud.id,
                monto=monto,
            )

        return {
            "mensaje": "Asignación desde fondo realizada.",
            "monto": monto,
            "receptor_id": resultado["receptor_id"],
            "solicitud_id": resultado["solicitud_id"],
            "horas_solidarias_disponibles": resultado["horas_solidarias_disponibles"],
            "saldo_fondo": resultado["saldo_fondo"],
            "saldo_receptor": resultado["receptor_saldo"],
            "donacion_id": resultado["donacion_id"],
            "comprobante_id": resultado["comprobante_id"],
        }

    def listar_mis_donaciones_realizadas(self, usuario_orm):
        """Lista todas las donaciones realizadas por el usuario."""
        return self._donacion_repo.listar_por_donante(usuario_orm.id)

    def listar_mis_donaciones_recibidas(self, usuario_orm):
        """Lista todas las donaciones recibidas por el usuario."""
        return self._donacion_repo.listar_por_receptor(usuario_orm.id)
