from comunidad.dto.request_models import PropuestaRequest, ResponderPropuestaRequest


class ProponerTruequeController:
    """
    Controlador para la Historia de Usuario: Proponer Trueque.
    Cubre: crear propuesta, responder propuesta, listar mis trueques.
    """

    def __init__(self, trueque_service, trueque_repository):
        self._trueque_service = trueque_service
        self._trueque_repo = trueque_repository

    def crear_propuesta(self, emisor_orm, request: PropuestaRequest) -> dict:
        """Valida el DTO y crea la propuesta de trueque."""
        if not request.receptor_id:
            raise ValueError("Falta el ID del receptor.")

        propuesta = self._trueque_service.crear_propuesta(
            emisor=emisor_orm,
            receptor_id=request.receptor_id,
            publicacion_emisor_id=request.publicacion_emisor_id,
            publicacion_receptor_id=request.publicacion_receptor_id,
        )
        return {
            "mensaje": "Propuesta enviada con éxito.",
            "propuesta_id": propuesta.id,
        }

    def responder_propuesta(
        self,
        receptor_orm,
        trueque_id: int,
        request: ResponderPropuestaRequest,
    ) -> dict:
        """Acepta o rechaza una propuesta existente."""
        if request.accion not in ("ACEPTAR", "RECHAZAR"):
            raise ValueError("Acción inválida. Debe ser ACEPTAR o RECHAZAR.")

        mensaje = self._trueque_service.responder_propuesta(
            receptor_orm, trueque_id, request.accion
        )
        return {"mensaje": mensaje}

    def listar_mis_trueques(self, usuario_orm, request=None) -> dict:
        """Retorna todos los trueques del usuario (enviados y recibidos)."""
        from comunidad.serializers import AcuerdoTruequeSerializer

        # Usar la instancia de repositorio pasada al controlador
        trueques = self._trueque_repo.listar_por_usuario(usuario_orm)
        serializer = AcuerdoTruequeSerializer(trueques, many=True, context={"request": request})
        return {
            "trueques": serializer.data,
            "cantidad": len(serializer.data),
        }
