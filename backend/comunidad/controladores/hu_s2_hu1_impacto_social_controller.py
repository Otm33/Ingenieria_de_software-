"""
Sprint 2 HU1: Controladores de Impacto Social.
Capa Presentación — coordina el flujo entre Router y Servicio.
No contiene lógica de negocio: solo extrae datos del request y llama al servicio.
"""
from ..services import ImpactoSocialService
from ..serializers import (
    SolicitudApoyoSocialSerializer,
    DonacionHorasSerializer,
    UsuarioEstadoSocialSerializer,
)
from ..services.impacto_social import MSG_SOLICITANTE_VULNERABLE


class ImpactoSocialController:
    """
    Controlador principal de Sprint 2 HU1 — Impacto Social.
    Métodos públicos → retornan dicts serializables para el Router.
    """

    def __init__(self, servicio: ImpactoSocialService = None):
        self._servicio = servicio or ImpactoSocialService()

    # ── Solicitudes públicas ──────────────────────────────────────────────────

    def listar_solicitudes_aprobadas(self) -> dict:
        solicitudes = self._servicio.listar_solicitudes_aprobadas()
        return {"solicitudes": solicitudes, "cantidad": len(solicitudes)}

    def crear_solicitud(self, usuario_orm, datos: dict) -> dict:
        solicitud = self._servicio.crear_solicitud(usuario_orm, datos)
        return SolicitudApoyoSocialSerializer(solicitud).data

    def listar_mis_solicitudes(self, usuario_orm) -> dict:
        solicitudes = self._servicio.listar_mis_solicitudes(usuario_orm)
        data = SolicitudApoyoSocialSerializer(solicitudes, many=True).data
        return {"solicitudes": data, "cantidad": len(data)}

    def activar_necesidad_vinculada(self, usuario_orm, solicitud_id: int) -> dict:
        solicitud = self._servicio.activar_necesidad_vinculada(usuario_orm, solicitud_id)
        return {
            "solicitud": SolicitudApoyoSocialSerializer(solicitud).data,
            "publicacion_id": solicitud.publicacion_id,
        }

    # ── Donaciones ────────────────────────────────────────────────────────────

    def listar_mis_donaciones(self, usuario_orm) -> dict:
        realizadas = self._servicio.listar_mis_donaciones_realizadas(usuario_orm)
        recibidas = self._servicio.listar_mis_donaciones_recibidas(usuario_orm)
        realizadas_list = list(realizadas)
        recibidas_list = list(recibidas)
        return {
            "realizadas": DonacionHorasSerializer(realizadas_list, many=True).data,
            "recibidas": DonacionHorasSerializer(recibidas_list, many=True).data,
            "cantidad_realizadas": len(realizadas_list),
            "cantidad_recibidas": len(recibidas_list),
        }

    def donar_a_causa(self, donante_orm, solicitud_id: int, monto) -> dict:
        resultado = self._servicio.donar_a_causa(donante_orm, solicitud_id, monto)
        return {
            "message": resultado["mensaje"],
            "comprobante": {
                "comprobante_id": resultado["comprobante_id"],
                "donacion_id": resultado["donacion_id"],
                "monto": resultado["monto"],
            },
            "saldo_restante": resultado["saldo_restante"],
            "monto": resultado["monto"],
            "receptor_id": resultado["receptor_id"],
            "receptor_nombre": resultado["receptor_nombre"],
        }

    def donar_a_fondo(self, donante_orm, monto) -> dict:
        resultado = self._servicio.donar_a_fondo(donante_orm, monto)
        fondo = self._servicio.obtener_saldo_fondo()
        return {
            "message": resultado["mensaje"],
            "comprobante": {
                "comprobante_id": resultado["comprobante_id"],
                "donacion_id": resultado["donacion_id"],
                "monto": resultado["monto"],
            },
            "saldo_restante": resultado["saldo_restante"],
            "saldo_fondo": fondo["saldo"],
            "monto": resultado["monto"],
        }

    # ── Admin ─────────────────────────────────────────────────────────────────

    def listar_solicitudes_pendientes(self, admin_orm) -> dict:
        solicitudes = self._servicio.listar_solicitudes_pendientes(admin_orm)
        data = SolicitudApoyoSocialSerializer(solicitudes, many=True).data
        return {"solicitudes": data, "cantidad": len(data)}

    def aprobar_solicitud(self, admin_orm, solicitud_id: int) -> dict:
        solicitud = self._servicio.aprobar_solicitud(admin_orm, solicitud_id)
        data = SolicitudApoyoSocialSerializer(solicitud).data
        if getattr(solicitud, "solicitante_marcado_vulnerable", False):
            data["mensaje"] = MSG_SOLICITANTE_VULNERABLE
        else:
            data["mensaje"] = "Solicitud aprobada correctamente."
        return data

    def rechazar_solicitud(self, admin_orm, solicitud_id: int) -> dict:
        solicitud = self._servicio.rechazar_solicitud(admin_orm, solicitud_id)
        return SolicitudApoyoSocialSerializer(solicitud).data

    def listar_usuarios_para_admin(self, admin_orm) -> dict:
        usuarios = self._servicio.listar_usuarios_para_admin(admin_orm)
        data = UsuarioEstadoSocialSerializer(usuarios, many=True).data
        return {"usuarios": data, "cantidad": len(data)}

    def actualizar_estado_social(self, admin_orm, usuario_id: int, estado_social: str) -> dict:
        usuario = self._servicio.actualizar_estado_social(admin_orm, usuario_id, estado_social)
        return UsuarioEstadoSocialSerializer(usuario).data

    def obtener_saldo_fondo(self, admin_orm) -> dict:
        return self._servicio.obtener_saldo_fondo(admin_orm)

    def asignar_desde_fondo(self, admin_orm, usuario_id: int, monto, solicitud_id=None) -> dict:
        return self._servicio.asignar_desde_fondo(admin_orm, usuario_id, monto, solicitud_id)
