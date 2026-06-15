"""
Sprint 2 HU 4: Como usuario, quiero poder realizar Trueques con usuarios que necesitan
servicios que yo tengo para que otros me den los servicios que yo necesito a cambio.
"""
from comunidad.dto.request_models import ResenaMultipleRequest
from comunidad.dominio.entidades import ResenaDominio
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
        from comunidad.repositories_legado import AcuerdoTruequeMultipleRepository
        from comunidad.serializers import AcuerdoTruequeMultipleSerializer

        logger.info(f"Listando trueques múltiples para usuario {usuario_orm.id}")

        try:
            trueques = AcuerdoTruequeMultipleRepository().listar_por_usuario(usuario_orm)
        except Exception as e:
            logger.exception(f"Error al obtener trueques múltiples: {e}")
            return {"trueques_multiple": [], "cantidad": 0}

        try:
            data = AcuerdoTruequeMultipleSerializer(
                trueques, many=True, context={"request": request, "usuario": usuario_orm}
            ).data
        except Exception as e:
            logger.exception(f"Error al serializar trueques múltiples: {e}")
            return {"trueques_multiple": [], "cantidad": 0}

        return {
            "trueques_multiple": data,
            "cantidad": len(data),
        }

    def registrar_resena_multiple(self, usuario_orm, request: ResenaMultipleRequest) -> dict:
        resena_dominio = ResenaDominio(
            calificador_id=usuario_orm.id,
            calificado_id=request.calificado_id,
            estrellas=request.estrellas,
            comentario=request.comentario,
        )
        es_valida, mensaje = resena_dominio.validar()
        if not es_valida:
            raise ValueError(mensaje)

        data = {
            "trueque_multiple_id": request.trueque_multiple_id,
            "calificado_id": request.calificado_id,
            "estrellas": request.estrellas,
            "comentario": request.comentario,
        }
        mensaje_resultado = self._resena_multiple_service.registrar_resena_multiple(usuario_orm, data)
        return {"mensaje": mensaje_resultado}
