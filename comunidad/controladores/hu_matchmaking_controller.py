from comunidad.dto.request_models import MatchmakingRequest


class MatchmakingController:
    """
    Controlador para la Historia de Usuario: Matchmaking.
    Mientras menos sepa el controlador, mejor:
    delega la lógica compleja en MatchmakingService existente.
    """

    def __init__(self, matchmaking_service, publicacion_repository):
        self._matchmaking_service = matchmaking_service
        self._pub_repo = publicacion_repository

    def obtener_matches(self, usuario_orm, request: MatchmakingRequest) -> dict:
        """
        Obtiene los matches para el usuario.
        Si viene publicacion_id, filtra por esa publicación.
        Si viene accion=verificar_coincidencia, verifica coincidencia por título.
        """
        publicacion_id = request.publicacion_id
        accion = request.accion

        if accion == "verificar_coincidencia" and publicacion_id:
            resultado = self._matchmaking_service.verificar_coincidencia_por_titulo(
                usuario_orm, publicacion_id
            )
            return resultado

        if publicacion_id:
            matches = self._matchmaking_service.obtener_matches_por_publicacion(
                usuario_orm, publicacion_id
            )
            mensaje = "Se encontraron coincidencias para la publicación seleccionada."
        else:
            matches = self._matchmaking_service.obtener_matches(usuario_orm)
            mensaje = "Se encontraron coincidencias (Match)."

        return {
            "matches": matches,
            "mensaje": mensaje,
            "cantidad": len(matches),
        }
