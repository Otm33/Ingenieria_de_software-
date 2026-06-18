from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .base import BusinessError
from ..repositorios_implementacion import TruequeMultipleRepository, ResenaMultipleRepository, UsuarioRepository
from ..negocio.trueque_multiple import es_participante, esta_finalizado, obtener_pares_del_usuario


class ResenaMultipleService:
    def __init__(self, trueque_multiple_repository=None, resena_multiple_repository=None, usuario_repository=None):
        self.trueque_multiple_repository = trueque_multiple_repository or TruequeMultipleRepository()
        self.resena_multiple_repository = resena_multiple_repository or ResenaMultipleRepository()
        self.usuario_repository = usuario_repository or UsuarioRepository()
    
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
            
            if not trueque_multiple:
                raise BusinessError("Trueque múltiple no encontrado.", status_code=404)
            
            # Verificar que el usuario es parte del trueque
            if not es_participante(trueque_multiple, usuario):
                raise BusinessError("No eres parte de este trueque múltiple.", status_code=403)
            
            # Verificar que el trueque esté finalizado
            if not esta_finalizado(trueque_multiple):
                raise BusinessError("Solo se pueden dejar reseñas de trueques múltiples finalizados.", status_code=400)
            
            # Obtener el calificado
            try:
                calificado = self.usuario_repository.obtener_por_id(calificado_id)
            except ObjectDoesNotExist:
                raise BusinessError("Usuario calificado no encontrado.", status_code=404)
            
            if not calificado:
                raise BusinessError("Usuario calificado no encontrado.", status_code=404)
            
            # Verificar que calificado es parte del trueque
            if not es_participante(trueque_multiple, calificado):
                raise BusinessError("El usuario calificado no es parte de este trueque.", status_code=400)
            
            # Verificar que calificador y calificado sean parte del mismo par
            pares_usuario = obtener_pares_del_usuario(trueque_multiple, usuario)
            pares_calificado = obtener_pares_del_usuario(trueque_multiple, calificado)
            
            # Deben compartir al menos un par
            if not set(pares_usuario) & set(pares_calificado):
                raise BusinessError("Solo puedes calificar a usuarios con los que compartiste un par en el trueque.", status_code=400)
            
            # Verificar si ya existe una reseña
            if self.resena_multiple_repository.existe_resena(trueque_multiple.id, usuario.id, calificado.id):
                raise BusinessError("Ya has dejado una reseña para este usuario en este trueque.", status_code=400)

            # Validar datos de reseña
            if estrellas < 1 or estrellas > 5:
                raise BusinessError("Las estrellas deben estar entre 1 y 5.")

            # Crear reseña
            self.resena_multiple_repository.crear(
                trueque_multiple.id, usuario.id, calificado.id, estrellas, comentario
            )
        
        return "Resena múltiple registrada correctamente."
