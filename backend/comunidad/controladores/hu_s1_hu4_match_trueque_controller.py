"""
Sprint 1 HU 4: Como usuario, quiero ser emparejado automáticamente (Match),
enviar/aceptar/rechazar propuestas de intercambio, recibir notificaciones
y calificar/dejar reseñas tras un trueque.
"""
from ..dto.request_models import (
    MatchmakingRequest,
    PropuestaRequest,
    ResenaRequest,
    ResponderPropuestaRequest,
)


class MatchTruequeController:
    """Controlador para Sprint 1 HU 4 — Match, propuestas, notificaciones y reseñas."""

    def __init__(
        self,
        matchmaking_service,
        publicacion_repository,
        trueque_service,
        trueque_repository,
        notificacion_service,
        resena_service,
    ):
        self._matchmaking_service = matchmaking_service
        self._pub_repo = publicacion_repository
        self._trueque_service = trueque_service
        self._trueque_repo = trueque_repository
        self._notif_service = notificacion_service
        self._resena_service = resena_service

    # --- Matchmaking ---

    def obtener_matches(self, usuario_orm, request: MatchmakingRequest) -> dict:
        publicacion_id = request.publicacion_id
        accion = request.accion

        if accion == "verificar_coincidencia" and publicacion_id:
            return self._matchmaking_service.verificar_coincidencia_por_titulo(
                usuario_orm, publicacion_id
            )

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

    # --- Propuestas de trueque ---

    def crear_propuesta(self, emisor_orm, request: PropuestaRequest) -> dict:
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
        if request.accion not in ("ACEPTAR", "RECHAZAR"):
            raise ValueError("Acción inválida. Debe ser ACEPTAR o RECHAZAR.")

        # Validación de permisos: verificar que el usuario es el receptor del trueque
        try:
            trueque_verificar = self._trueque_repo.obtener_por_receptor(trueque_id, receptor_orm.id)
        except Exception:
            raise ValueError("No tienes permiso para responder esta propuesta. Solo el receptor puede responder.")

        mensaje = self._trueque_service.responder_propuesta(
            receptor_orm, trueque_id, request.accion
        )
        return {"mensaje": mensaje}

    # --- Notificaciones ---

    def listar_notificaciones(self, usuario_orm, incluir_leidas: bool = False) -> dict:
        notificaciones = self._notif_service.obtener_notificaciones_usuario(
            usuario_orm, incluir_leidas=incluir_leidas
        )

        # Serializar objetos NotificacionDominio a dicts
        serializadas = []
        for n in notificaciones:
            serializadas.append({
                "id": n.id,
                "tipo": n.tipo,
                "destinatario_id": n.destinatario_id,
                "remitente_id": n.remitente_id,
                "trueque_id": n.trueque_id,
                "trueque_multiple_id": n.trueque_multiple_id,
                "publicacion_original_id": n.publicacion_original_id,
                "mensaje": n.mensaje,
                "estado": n.estado,
                "match_detalle": n.match_detalle,
            })

        return {
            "notificaciones": serializadas,
            "cantidad": len(serializadas),
        }

    def marcar_notificacion_leida(
        self,
        usuario_orm,
        notificacion_id: int = None,
        trueque_id: int = None,
    ) -> dict:
        if not notificacion_id and not trueque_id:
            raise ValueError("Falta notificacion_id o trueque_id.")

        if trueque_id:
            cantidad = self._notif_service.marcar_notificaciones_trueque_leidas(
                usuario_orm, trueque_id
            )
            return {
                "mensaje": "Notificaciones del trueque marcadas como leídas.",
                "cantidad": cantidad,
            }

        # Validación de permisos: verificar que la notificación pertenece al usuario
        # Nota: Esta validación está deshabilitada temporalmente porque el método obtener_notificacion_por_id
        # no existe en el servicio de notificaciones. Se puede habilitar cuando se implemente el método.
        # try:
        #     notificacion_verificar = self._notif_service.obtener_notificacion_por_id(notificacion_id)
        #     if notificacion_verificar.destinatario_id != usuario_orm.id:
        #         raise ValueError("No tienes permiso para marcar esta notificación. Solo el destinatario puede marcarla como leída.")
        # except Exception:
        #     # Si el método no existe o falla, permitir la operación (compatibilidad)
        #     pass

        self._notif_service.marcar_notificacion_leida(notificacion_id, usuario_orm)
        return {"mensaje": "Notificación marcada como leída."}

    # --- Reseñas ---

    def registrar_resena(self, usuario_orm, request: ResenaRequest) -> dict:
        # Validación de permisos: verificar que el usuario es parte del trueque
        try:
            trueque_verificar = self._trueque_repo.obtener_por_participante(request.trueque_id, usuario_orm.id)
        except Exception:
            raise ValueError("No tienes permiso para reseñar este trueque. Solo los participantes pueden reseñar.")

        data = {
            "trueque_id": request.trueque_id,
            "calificado_id": request.calificado_id,
            "estrellas": request.estrellas,
            "comentario": request.comentario,
        }
        mensaje_resultado = self._resena_service.registrar_resena(usuario_orm, data)
        return {"mensaje": mensaje_resultado}
