from django.core.exceptions import ObjectDoesNotExist

from .base import BusinessError
from ..repositorios_implementacion import NotificacionRepository


class NotificacionService:
    def __init__(self, notificacion_repository=None):
        self.notificacion_repository = notificacion_repository or NotificacionRepository()

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
        dest_id = getattr(destinatario, 'id', destinatario)
        rem_id = getattr(remitente, 'id', remitente)
        t_id = getattr(trueque, 'id', trueque)
        pub_orig_id = getattr(publicacion_original, 'id', publicacion_original)
        return self.notificacion_repository.crear_notificacion(
            dest_id,
            rem_id,
            trueque_id=t_id,
            publicacion_original_id=pub_orig_id,
            mensaje=mensaje,
            tipo=tipo,
            match_detalle=match_detalle,
        )

    def actualizar_estado_propuesta(self, trueque, estado):
        t_id = getattr(trueque, 'id', trueque)
        return self.notificacion_repository.actualizar_estado_por_trueque(t_id, estado)
    
    def obtener_notificaciones_usuario(self, usuario, incluir_leidas=False):
        u_id = getattr(usuario, 'id', usuario)
        return self.notificacion_repository.listar_por_destinatario(
            u_id,
            incluir_leidas=incluir_leidas,
        )
    
    def marcar_notificacion_leida(self, notificacion_id, usuario):
        u_id = getattr(usuario, 'id', usuario)
        try:
            return self.notificacion_repository.marcar_como_leida(
                notificacion_id,
                usuario_id=u_id,
            )
        except ObjectDoesNotExist:
            raise BusinessError("Notificación no encontrada.", status_code=404)

    def marcar_notificaciones_trueque_leidas(self, usuario, trueque_id):
        u_id = getattr(usuario, 'id', usuario)
        t_id = getattr(trueque_id, 'id', trueque_id)
        actualizadas = self.notificacion_repository.marcar_leidas_por_trueque(
            u_id,
            t_id,
        )
        return actualizadas
    
    def marcar_notificaciones_trueque_leidas_ambos_usuarios(self, trueque_id, tipos=None):
        """Marca todas las notificaciones de un trueque como leídas para ambos usuarios."""
        t_id = getattr(trueque_id, 'id', trueque_id)
        actualizadas = self.notificacion_repository.marcar_leidas_por_trueque_ambos_usuarios(
            t_id,
            tipos,
        )
        return actualizadas

    def crear_notificacion_resena(self, destinatario, remitente, trueque=None, trueque_multiple=None, mensaje=None):
        """Crea una notificación de solicitud de reseña."""
        dest_id = getattr(destinatario, 'id', destinatario)
        rem_id = getattr(remitente, 'id', remitente)
        t_id = getattr(trueque, 'id', trueque) if trueque else None
        tm_id = getattr(trueque_multiple, 'id', trueque_multiple) if trueque_multiple else None
        
        return self.notificacion_repository.crear_notificacion(
            dest_id,
            rem_id,
            trueque_id=t_id,
            mensaje=mensaje,
            tipo="RESENA",
            match_detalle={"trueque_multiple": tm_id} if tm_id else None,
        )
