class NotificacionController:
    """
    Controlador para la Historia de Usuario: Notificaciones.
    Cubre: listar notificaciones, marcar como leída (individual o por trueque).
    """

    def __init__(self, notificacion_service):
        self._notif_service = notificacion_service

    def listar_notificaciones(self, usuario_orm, incluir_leidas: bool = False) -> dict:
        """Retorna las notificaciones del usuario."""
        from comunidad.serializers import NotificacionSerializer

        notificaciones = self._notif_service.obtener_notificaciones_usuario(
            usuario_orm, incluir_leidas=incluir_leidas
        )
        data = NotificacionSerializer(
            notificaciones, many=True, context={"usuario": usuario_orm}
        ).data

        return {
            "notificaciones": data,
            "cantidad": len(data),
        }

    def marcar_leida(
        self,
        usuario_orm,
        notificacion_id: int = None,
        trueque_id: int = None,
    ) -> dict:
        """
        Marca notificaciones como leídas.
        Puede ser por ID individual o por trueque (marca todas del trueque).
        """
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

        self._notif_service.marcar_notificacion_leida(notificacion_id, usuario_orm)
        return {"mensaje": "Notificación marcada como leída."}
