from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .base import BusinessError
from ..interfaces import ResenaInterface
from ..repositories import AcuerdoTruequeRepository, ResenaRepository, UsuarioRepository


class ResenaService(ResenaInterface):
    def __init__(self, trueque_repository=None, resena_repository=None, usuario_repository=None):
        self.trueque_repository = trueque_repository or AcuerdoTruequeRepository()
        self.resena_repository = resena_repository or ResenaRepository()
        self.usuario_repository = usuario_repository or UsuarioRepository()

    def registrar_resena(self, usuario, datos):
        trueque_id = datos.get("trueque_id")
        comentario = datos.get("comentario", "")

        try:
            estrellas = int(datos.get("estrellas"))
        except (TypeError, ValueError):
            raise BusinessError("Las estrellas deben ser un numero entero.")

        if len(comentario) > 500:
            raise BusinessError("El comentario no puede superar los 500 caracteres.")

        with transaction.atomic():
            try:
                trueque = self.trueque_repository.obtener_bloqueado(trueque_id)
            except ObjectDoesNotExist:
                raise BusinessError("Trueque no encontrado.", status_code=404)

            # Usar método de negocio de AcuerdoTrueque para verificar participación
            if not trueque.participante(usuario):
                raise BusinessError("No eres parte de este trueque.", status_code=403)

            if not trueque.esta_finalizado():
                raise BusinessError("Solo se pueden dejar reseñas de trueques finalizados.", status_code=400)

            # Verificar si ya existe una reseña de este usuario para este trueque
            try:
                from ..models import Resena
                Resena.objects.get(trueque=trueque, calificador=usuario)
                raise BusinessError("Ya has dejado una reseña para este trueque.", status_code=400)
            except Resena.DoesNotExist:
                pass  # No hay reseña previa, podemos continuar

            calificado = trueque.contraparte(usuario)
            
            # Crear reseña temporal para validar usando métodos de negocio
            resena_temp = Resena(
                trueque=trueque,
                calificador=usuario,
                calificado=calificado,
                estrellas=estrellas,
                comentario=comentario
            )
            
            # Usar método de negocio de Resena para validar
            es_valida, mensaje = resena_temp.validar_resena()
            if not es_valida:
                raise BusinessError(mensaje)

            self.resena_repository.crear(trueque, usuario, calificado, estrellas, comentario)

        return "Resena registrada correctamente."
