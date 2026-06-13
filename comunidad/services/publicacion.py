from .base import BusinessError, CATEGORIAS_PUBLICACION
from ..repositories import PublicacionRepository
from ..validators import contiene_palabra_prohibida
from .matchmaking import MatchmakingService
from .matchmaking_multiple import MatchmakingMultipleService
import logging

logger = logging.getLogger(__name__)


class PublicacionService:
    def __init__(self, publicacion_repository=None, matchmaking_service=None, matchmaking_multiple_service=None):
        self.publicacion_repository = publicacion_repository or PublicacionRepository()
        self.matchmaking_service = matchmaking_service
        self.matchmaking_multiple_service = matchmaking_multiple_service

    def _disparar_deteccion_matches(self, usuario):
        servicio = self.matchmaking_service or MatchmakingService()
        servicio.detectar_y_notificar_matches(usuario)
    
    def _disparar_deteccion_ciclos_multiples(self, usuario):
        servicio = self.matchmaking_multiple_service or MatchmakingMultipleService()
        logger.debug("Disparando detección de ciclos múltiples para usuario %s", usuario.id)
        servicio.detectar_y_notificar_ciclos(usuario)

    def crear_publicacion(self, usuario, datos):
        tipo = datos.get("tipo")
        titulo = datos.get("titulo")
        descripcion = datos.get("descripcion")
        categoria = datos.get("categoria")
        urgencia = datos.get("urgencia", "NORMAL")

        if not all([tipo, titulo, descripcion, categoria]):
            raise BusinessError("Faltan datos obligatorios para la publicacion.")

        if tipo not in ["TALENTO", "NECESIDAD"]:
            raise BusinessError("El tipo debe ser TALENTO o NECESIDAD.")

        if categoria not in CATEGORIAS_PUBLICACION:
            raise BusinessError("La categoria seleccionada no esta permitida.")

        if urgencia not in ["NORMAL", "ALTA", "CRITICA"]:
            raise BusinessError("La urgencia seleccionada no es valida.")

        # Usar método de negocio de Usuario para verificar si puede publicar
        puede_publicar, mensaje = usuario.puede_publicar(tipo)
        if not puede_publicar:
            raise BusinessError(mensaje)

        if contiene_palabra_prohibida(titulo) or contiene_palabra_prohibida(descripcion):
            raise BusinessError("La publicación contiene palabras no permitidas.")

        # Crear publicación temporal para validar reglas de negocio
        from ..models import Publicacion
        publicacion_temp = Publicacion(
            usuario=usuario,
            tipo=tipo,
            titulo=titulo,
            descripcion=descripcion,
            categoria=categoria,
            urgencia=urgencia,
            esta_activa=True
        )
        
        # Usar método de negocio de Publicacion para validar reglas
        es_valido, mensaje_validacion = publicacion_temp.validar_reglas_negocio()
        if not es_valido:
            raise BusinessError(mensaje_validacion)

        publicacion = self.publicacion_repository.crear(usuario, {
            "tipo": tipo,
            "titulo": titulo,
            "descripcion": descripcion,
            "categoria": categoria,
            "urgencia": urgencia,
        })
        
        # Detección de matches (no falla si hay error)
        try:
            self._disparar_deteccion_matches(usuario)
        except Exception as e:
            # No fallar la publicación si la detección falla
            pass
        
        # Detección de ciclos múltiples (no falla si hay error)
        try:
            self._disparar_deteccion_ciclos_multiples(usuario)
        except Exception as e:
            # No fallar la publicación si la detección falla
            logger.exception("Error en detección de ciclos múltiples después de crear publicación para usuario %s", usuario.id)
        
        return publicacion

    def pausar_publicacion(self, usuario, publicacion_id):
        return self.actualizar_estado_publicacion(usuario, publicacion_id, esta_activa=False)

    def reactivar_publicacion(self, usuario, publicacion_id):
        return self.actualizar_estado_publicacion(usuario, publicacion_id, esta_activa=True)

    def actualizar_estado_publicacion(self, usuario, publicacion_id, esta_activa):
        from ..models import Publicacion

        # Usar método de negocio de Usuario para verificar si puede modificar publicaciones
        if not usuario.puede_modificar_publicaciones():
            raise BusinessError("Saldo crítico inferior a -10 horas. No puedes modificar ofertas.")

        try:
            publicacion = self.publicacion_repository.obtener_por_id_y_usuario(publicacion_id, usuario)
        except Publicacion.DoesNotExist:
            raise BusinessError("Publicación no encontrada.", status_code=404)

        # Usar métodos de negocio de Publicacion para validar
        if esta_activa and not publicacion.esta_activa:
            puede_reactivar, mensaje = publicacion.puede_reactivarse()
            if not puede_reactivar:
                raise BusinessError(mensaje)
        elif not esta_activa and publicacion.esta_activa:
            puede_pausar, mensaje = publicacion.puede_pausarse()
            if not puede_pausar:
                raise BusinessError(mensaje)


        # Usar update() directo para evitar validaciones del modelo save()

        Publicacion.objects.filter(id=publicacion_id, usuario=usuario).update(esta_activa=esta_activa)
        
        # Recargar la publicación actualizada
        publicacion = self.publicacion_repository.obtener_por_id_y_usuario(publicacion_id, usuario)
        if esta_activa:
            # Detección de matches (no falla si hay error)
            try:
                self._disparar_deteccion_matches(usuario)
            except Exception as e:
                pass
            
            # Detección de ciclos múltiples (no falla si hay error)
            try:
                self._disparar_deteccion_ciclos_multiples(usuario)
            except Exception as e:
                logger.exception("Error en detección de ciclos múltiples al reactivar publicación para usuario %s", usuario.id)
        return publicacion
