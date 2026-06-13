from django.core.exceptions import ObjectDoesNotExist

from .base import BusinessError
from ..repositories import NotificacionPropuestaRepository


class NotificacionService:
    def __init__(self, notificacion_repository=None):
        self.notificacion_repository = notificacion_repository or NotificacionPropuestaRepository()

    def crear_notificacion_propuesta(
        self,
        destinatario,
        remitente,
        trueque=None,
        publicacion_original=None,
        mensaje=None,
        tipo="PROPUESTA",
        match_detalle=None,
    ):
        return self.notificacion_repository.crear_notificacion(
            destinatario,
            remitente,
            trueque=trueque,
            publicacion_original=publicacion_original,
            mensaje=mensaje,
            tipo=tipo,
            match_detalle=match_detalle,
        )

    def actualizar_estado_propuesta(self, trueque, estado):
        return self.notificacion_repository.actualizar_estado_por_trueque(trueque, estado)
    
    def obtener_notificaciones_usuario(self, usuario, incluir_leidas=False):
        return self.notificacion_repository.obtener_notificaciones_usuario(
            usuario,
            incluir_leidas=incluir_leidas,
        )
    
    def marcar_notificacion_leida(self, notificacion_id, usuario):
        try:
            return self.notificacion_repository.marcar_como_leida(
                notificacion_id,
                destinatario=usuario,
            )
        except ObjectDoesNotExist:
            raise BusinessError("Notificación no encontrada.", status_code=404)

    def marcar_notificaciones_trueque_leidas(self, usuario, trueque_id):
        actualizadas = self.notificacion_repository.marcar_leidas_por_trueque(
            usuario,
            trueque_id,
        )
        return actualizadas
    
    def marcar_notificaciones_trueque_leidas_ambos_usuarios(self, trueque_id, tipos=None):
        """Marca todas las notificaciones de un trueque como leídas para ambos usuarios."""
        actualizadas = self.notificacion_repository.marcar_leidas_por_trueque_ambos_usuarios(
            trueque_id,
            tipos,
        )
        return actualizadas
