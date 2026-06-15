"""
Sprint 2 HU 5: Como usuario, quiero concretar los trueques mediante un código alfanumérico
único que le aparezca al emisor del trueque para que el receptor lo introduzca
en la opción "Código para Concluir Trueque".
"""
from comunidad.dto.request_models import ValidarCodigoRequest


class FinalizarTruequeController:
    """Controlador para Sprint 2 HU 5 — Finalización de trueque con código."""

    def __init__(self, trueque_service, trueque_repository):
        self._trueque_service = trueque_service
        self._trueque_repo = trueque_repository

    def confirmar_finalizacion(self, usuario_orm, trueque_id: int) -> dict:
        resultado = self._trueque_service.finalizar_trueque(usuario_orm, trueque_id)
        trueque = self._trueque_repo.obtener_por_participante(trueque_id, usuario_orm)

        return {
            "mensaje": resultado.get("mensaje", ""),
            "estado": trueque.estado,
            "emisor_confirmado": trueque.emisor_confirmado,
            "receptor_confirmado": trueque.receptor_confirmado,
            "saldo_transferido": resultado.get("saldo_transferido", False),
            "impacto_horas": resultado.get("impacto_horas", 0),
            "habilitar_resena": resultado.get("habilitar_resena", False),
        }

    def validar_codigo(
        self,
        usuario_orm,
        trueque_id: int,
        request: ValidarCodigoRequest,
    ) -> dict:
        if not request.codigo or not request.codigo.strip():
            raise ValueError("El código de confirmación es obligatorio.")

        resultado = self._trueque_service.validar_codigo_finalizacion(
            usuario_orm, trueque_id, request.codigo
        )

        trueque = self._trueque_repo.obtener_por_participante(trueque_id, usuario_orm)

        return {
            "mensaje": resultado.get("mensaje", ""),
            "estado": trueque.estado,
            "saldo_transferido": resultado.get("saldo_transferido", False),
            "impacto_horas": resultado.get("impacto_horas", 0),
            "habilitar_resena": resultado.get("habilitar_resena", False),
        }
