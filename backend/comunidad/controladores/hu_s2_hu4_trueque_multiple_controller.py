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

        from backend.comunidad.models import AcuerdoTruequeMultiple as TMORM
        from backend.comunidad.serializers import AcuerdoTruequeMultipleSerializer
        from django.db.models import Q

        uid = usuario_orm.id
        qs = TMORM.objects.filter(
            Q(emisor1_id=uid) | Q(receptor1_id=uid) |
            Q(emisor2_id=uid) | Q(receptor2_id=uid) |
            Q(emisor3_id=uid) | Q(receptor3_id=uid)
        ).select_related(
            'emisor1', 'receptor1', 'emisor2', 'receptor2', 'emisor3', 'receptor3',
            'publicacion_emisor1', 'publicacion_emisor1__usuario',
            'publicacion_receptor1', 'publicacion_receptor1__usuario',
            'publicacion_emisor2', 'publicacion_emisor2__usuario',
            'publicacion_receptor2', 'publicacion_receptor2__usuario',
            'publicacion_emisor3', 'publicacion_emisor3__usuario',
            'publicacion_receptor3', 'publicacion_receptor3__usuario',
        )

        serializer_context = {'request': request} if request else {}
        data = AcuerdoTruequeMultipleSerializer(qs, many=True, context=serializer_context).data

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
