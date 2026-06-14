class TruequeMultipleController:
    """
    Controlador para la Historia de Usuario: Trueque Múltiple.
    Cubre: aceptar/rechazar propuesta múltiple, validar código par, finalizar par,
    y listar mis trueques múltiples.
    """

    def __init__(self, trueque_multiple_service):
        self._service = trueque_multiple_service

    def aceptar_propuesta(self, usuario_orm, trueque_multiple_id: int) -> dict:
        """Acepta la propuesta de trueque múltiple para el usuario actual."""
        mensaje = self._service.aceptar_propuesta_multiple(usuario_orm, trueque_multiple_id)
        return {"mensaje": mensaje}

    def rechazar_propuesta(self, usuario_orm, trueque_multiple_id: int) -> dict:
        """Rechaza la propuesta de trueque múltiple."""
        mensaje = self._service.rechazar_propuesta_multiple(usuario_orm, trueque_multiple_id)
        return {"mensaje": mensaje}

    def validar_codigo_par(
        self,
        usuario_orm,
        trueque_multiple_id: int,
        codigo: str,
        par: int = None,
    ) -> dict:
        """Valida el código de confirmación para un par del trueque múltiple."""
        if not codigo or not codigo.strip():
            raise ValueError("El código de validación es obligatorio.")

        mensaje = self._service.validar_codigo_par(usuario_orm, trueque_multiple_id, codigo, par)
        return {"mensaje": mensaje}

    def finalizar_par(self, usuario_orm, trueque_multiple_id: int) -> dict:
        """Confirma la finalización del par del trueque múltiple."""
        mensaje = self._service.finalizar_par(usuario_orm, trueque_multiple_id)
        return {"mensaje": mensaje}

    def listar_mis_trueques_multiples(self, usuario_orm, request=None) -> dict:
        """Retorna todos los trueques múltiples donde participa el usuario."""
        from comunidad.repositories import AcuerdoTruequeMultipleRepository
        from comunidad.serializers import AcuerdoTruequeMultipleSerializer
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Listando trueques múltiples para usuario {usuario_orm.id}")
        
        try:
            trueques = AcuerdoTruequeMultipleRepository().listar_por_usuario(usuario_orm)
            logger.info(f"Trueques múltiples del repositorio: {len(trueques)}")
        except Exception as e:
            logger.exception(f"Error al obtener trueques múltiples del repositorio: {e}")
            return {
                "trueques_multiple": [],
                "cantidad": 0,
            }
        
        try:
            data = AcuerdoTruequeMultipleSerializer(
                trueques, many=True, context={"request": request, "usuario": usuario_orm}
            ).data
            logger.info(f"Trueques múltiples serializados: {len(data)}")
        except Exception as e:
            logger.exception(f"Error al serializar trueques múltiples: {e}")
            return {
                "trueques_multiple": [],
                "cantidad": 0,
            }
        
        return {
            "trueques_multiple": data,
            "cantidad": len(data),
        }
