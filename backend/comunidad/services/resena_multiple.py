from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .base import BusinessError
from ..repositories_legado import AcuerdoTruequeMultipleRepository, ResenaMultipleRepository


class ResenaMultipleService:
    def __init__(self, trueque_multiple_repository=None, resena_multiple_repository=None):
        self.trueque_multiple_repository = trueque_multiple_repository or AcuerdoTruequeMultipleRepository()
        self.resena_multiple_repository = resena_multiple_repository or ResenaMultipleRepository()
    
    def registrar_resena_multiple(self, usuario, datos):
        """Registra reseña solo al usuario que dio servicio directamente."""
        trueque_multiple_id = datos.get("trueque_multiple_id")
        calificado_id = datos.get("calificado_id")
        comentario = datos.get("comentario", "")
        
        try:
            estrellas = int(datos.get("estrellas"))
        except (TypeError, ValueError):
            raise BusinessError("Las estrellas deben ser un numero entero.")
        
        if len(comentario) > 500:
            raise BusinessError("El comentario no puede superar los 500 caracteres.")
        
        with transaction.atomic():
            try:
                trueque_multiple = self.trueque_multiple_repository.obtener_bloqueado(trueque_multiple_id)
            except ObjectDoesNotExist:
                raise BusinessError("Trueque múltiple no encontrado.", status_code=404)
            
            # Verificar que el usuario es parte del trueque
            if not trueque_multiple.participante(usuario):
                raise BusinessError("No eres parte de este trueque múltiple.", status_code=403)
            
            # Verificar que el trueque esté finalizado
            if not trueque_multiple.esta_finalizado():
                raise BusinessError("Solo se pueden dejar reseñas de trueques múltiples finalizados.", status_code=400)
            
            # Obtener el calificado
            try:
                from ..models import Usuario
                calificado = Usuario.objects.get(id=calificado_id)
            except Usuario.DoesNotExist:
                raise BusinessError("Usuario calificado no encontrado.", status_code=404)
            
            # Verificar que calificado es parte del trueque
            if not trueque_multiple.participante(calificado):
                raise BusinessError("El usuario calificado no es parte de este trueque.", status_code=400)
            
            # Verificar que calificador y calificado sean parte del mismo par
            pares_usuario = trueque_multiple.obtener_pares_del_usuario(usuario)
            pares_calificado = trueque_multiple.obtener_pares_del_usuario(calificado)
            
            # Deben compartir al menos un par
            if not set(pares_usuario) & set(pares_calificado):
                raise BusinessError("Solo puedes calificar a usuarios con los que compartiste un par en el trueque.", status_code=400)
            
            # Verificar si ya existe una reseña
            if self.resena_multiple_repository.existe_resena(trueque_multiple, usuario, calificado):
                raise BusinessError("Ya has dejado una reseña para este usuario en este trueque.", status_code=400)
            
            # Crear reseña temporal para validar
            from ..models import ResenaMultiple
            resena_temp = ResenaMultiple(
                trueque_multiple=trueque_multiple,
                calificador=usuario,
                calificado=calificado,
                estrellas=estrellas,
                comentario=comentario
            )
            
            # Validar reseña
            es_valida, mensaje = resena_temp.validar_resena()
            if not es_valida:
                raise BusinessError(mensaje)
            
            # Crear reseña
            self.resena_multiple_repository.crear(
                trueque_multiple, usuario, calificado, estrellas, comentario
            )
        
        return "Resena múltiple registrada correctamente."
