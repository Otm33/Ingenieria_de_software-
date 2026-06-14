from comunidad.dto.request_models import ValidarCodigoRequest


class FinalizarTruequeController:
    """
    Controlador para la Historia de Usuario: Finalizar Trueque.
    Cubre: confirmación bilateral y validación de código de finalización.
    """

    def __init__(self, trueque_service, trueque_repository):
        self._trueque_service = trueque_service
        self._trueque_repo = trueque_repository

    def confirmar_finalizacion(self, usuario_orm, trueque_id: int) -> dict:
        """
        Registra la confirmación del usuario.
        Si ambas partes confirmaron, transfiere horas de vida.
        """
        resultado = self._trueque_service.finalizar_trueque(usuario_orm, trueque_id)

        # Obtener estado actualizado del trueque para la respuesta usando el repositorio inyectado
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
        """Valida el código de confirmación y finaliza el trueque si es correcto."""
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
