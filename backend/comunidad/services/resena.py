from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .base import BusinessError
from ..interfaces.service_interfaces import ResenaInterface
from ..repositorios_implementacion import TruequeRepository, ResenaRepository, UsuarioRepository
from ..negocio.trueque import es_participante, esta_finalizado, contraparte
from ..dominio.entidades import ResenaDominio
from ..negocio.resena import validar as validar_resena


class ResenaService(ResenaInterface):
    def __init__(self, trueque_repository=None, resena_repository=None, usuario_repository=None):
        self.trueque_repository = trueque_repository or TruequeRepository()
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

            if not trueque:
                raise BusinessError("Trueque no encontrado.", status_code=404)

            # Usar método de negocio de AcuerdoTrueque para verificar participación
            if not es_participante(trueque, usuario):
                raise BusinessError("No eres parte de este trueque.", status_code=403)

            if not esta_finalizado(trueque):
                raise BusinessError("Solo se pueden dejar reseñas de trueques finalizados.", status_code=400)

            # Verificar si ya existe una reseña de este usuario para este trueque
            if self.resena_repository.existe_resena(trueque.id, usuario.id):
                raise BusinessError("Ya has dejado una reseña para este trueque.", status_code=400)

            calificado_id = contraparte(trueque, usuario)
            if not calificado_id:
                raise BusinessError("No se pudo identificar a la contraparte.", status_code=400)

            # contraparte siempre retorna un int (ID), obtener el usuario del repositorio
            calificado = self.usuario_repository.obtener_por_id(calificado_id)
            if not calificado:
                raise BusinessError("No se pudo identificar a la contraparte.", status_code=400)
            
            # Crear reseña temporal para validar usando métodos de negocio
            resena_temp = ResenaDominio(
                trueque_id=trueque.id,
                calificador_id=usuario.id,
                calificado_id=calificado.id,
                estrellas=estrellas,
                comentario=comentario
            )
            
            # Usar método de negocio de Resena para validar
            es_valida, mensaje = validar_resena(resena_temp)
            if not es_valida:
                raise BusinessError(mensaje)

            self.resena_repository.crear(trueque.id, usuario.id, calificado.id, estrellas, comentario)

        return "Resena registrada correctamente."
