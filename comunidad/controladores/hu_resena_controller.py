from comunidad.dto.request_models import ResenaRequest, ResenaMultipleRequest
from comunidad.dominio.entidades import ResenaDominio


class ResenaController:
    """
    Controlador para la Historia de Usuario: Dejar Reseña.
    Cubre: reseñas de trueques simples y trueques múltiples.
    """

    def __init__(self, resena_service, resena_multiple_service):
        self._resena_service = resena_service
        self._resena_multiple_service = resena_multiple_service

    def registrar_resena(self, usuario_orm, request: ResenaRequest) -> dict:
        """
        Valida el DTO usando la entidad de dominio ResenaDominio
        y luego delega en ResenaService.
        """
        # Validar DTO con la entidad de dominio (sin BD)
        resena_dominio = ResenaDominio(
            trueque_id=request.trueque_id,
            calificador_id=usuario_orm.id,
            calificado_id=request.calificado_id,
            estrellas=request.estrellas,
            comentario=request.comentario,
        )
        es_valida, mensaje = resena_dominio.validar()
        if not es_valida:
            raise ValueError(mensaje)

        # Delegar en el service existente
        data = {
            "trueque_id": request.trueque_id,
            "calificado_id": request.calificado_id,
            "estrellas": request.estrellas,
            "comentario": request.comentario,
        }
        mensaje_resultado = self._resena_service.registrar_resena(usuario_orm, data)
        return {"mensaje": mensaje_resultado}

    def registrar_resena_multiple(self, usuario_orm, request: ResenaMultipleRequest) -> dict:
        """Valida y registra una reseña para un trueque múltiple."""
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
