"""
Sprint 2 HU 4: Como usuario, quiero poder realizar Trueques con usuarios que necesitan
servicios que yo tengo para que otros me den los servicios que yo necesito a cambio.
"""
from ..dto.request_models import ResenaMultipleRequest
import logging

logger = logging.getLogger(__name__)


class TruequeMultipleController:
    """Controlador para Sprint 2 HU 4 — Trueques múltiples."""

    def __init__(self, trueque_multiple_service, resena_multiple_service):
        self._service = trueque_multiple_service
        self._resena_multiple_service = resena_multiple_service

    def aceptar_propuesta(self, usuario_orm, trueque_multiple_id: int) -> dict:
        mensaje = self._service.aceptar_propuesta_multiple(usuario_orm, trueque_multiple_id)
        return {"mensaje": mensaje}

    def rechazar_propuesta(self, usuario_orm, trueque_multiple_id: int) -> dict:
        mensaje = self._service.rechazar_propuesta_multiple(usuario_orm, trueque_multiple_id)
        return {"mensaje": mensaje}

    def validar_codigo_par(
        self,
        usuario_orm,
        trueque_multiple_id: int,
        codigo: str,
        par: int = None,
    ) -> dict:
        if not codigo or not codigo.strip():
            raise ValueError("El código de validación es obligatorio.")

        mensaje = self._service.validar_codigo_par(usuario_orm, trueque_multiple_id, codigo, par)
        return {"mensaje": mensaje}

    def finalizar_par(self, usuario_orm, trueque_multiple_id: int) -> dict:
        mensaje = self._service.finalizar_par(usuario_orm, trueque_multiple_id)
        return {"mensaje": mensaje}

    def listar_mis_trueques_multiples(self, usuario_orm, request=None) -> dict:
        logger.info(f"Listando trueques múltiples para usuario {usuario_orm.id}")

        trueques = self._service.listar_por_usuario(usuario_orm)

        data = [
            {
                "id": t.id,
                "estado": t.estado,
                "fecha_creacion": t.fecha_creacion.isoformat() if t.fecha_creacion else None,
            }
            for t in trueques
        ]

        return {
            "trueques_multiple": data,
            "cantidad": len(data),
        }

    def registrar_resena_multiple(self, usuario_orm, request: ResenaMultipleRequest) -> dict:
        data = {
            "trueque_multiple_id": request.trueque_multiple_id,
            "calificado_id": request.calificado_id,
            "estrellas": request.estrellas,
            "comentario": request.comentario,
        }
        mensaje_resultado = self._resena_multiple_service.registrar_resena_multiple(usuario_orm, data)
        return {"mensaje": mensaje_resultado}
