from django.db import transaction
from .base import BusinessError, CATEGORIAS_PUBLICACION
from ..repositorios_implementacion import PublicacionRepository, UsuarioRepository
from ..negocio.validaciones import contiene_palabra_prohibida
from ..negocio.usuario import puede_publicar, puede_modificar_publicaciones
from ..negocio.publicacion import validar_reglas_negocio, puede_pausarse, puede_reactivarse
from .matchmaking import MatchmakingService
from .matchmaking_multiple import MatchmakingMultipleService
import logging

logger = logging.getLogger(__name__)


class PublicacionService:
    def __init__(self, publicacion_repository=None, usuario_repository=None, matchmaking_service=None, matchmaking_multiple_service=None):
        self.publicacion_repository = publicacion_repository or PublicacionRepository()
        self.usuario_repository = usuario_repository or UsuarioRepository()
        self.matchmaking_service = matchmaking_service
        self.matchmaking_multiple_service = matchmaking_multiple_service

    def _disparar_deteccion_matches(self, usuario):
        servicio = self.matchmaking_service or MatchmakingService()
        servicio.detectar_y_notificar_matches(usuario)
    
    def _disparar_deteccion_ciclos_multiples(self, usuario):
        servicio = self.matchmaking_multiple_service or MatchmakingMultipleService()
        logger.info(f"Disparando detección de ciclos múltiples para usuario {usuario.id}")
        servicio.detectar_y_notificar_ciclos(usuario)

    @transaction.atomic
    def crear_publicacion(self, usuario, datos):
        logger.warning(f"Iniciando crear_publicacion para usuario {usuario.id}")

        tipo = datos.get("tipo")
        titulo = datos.get("titulo")
        descripcion = datos.get("descripcion")
        categoria = datos.get("categoria")
        urgencia = datos.get("urgencia", "NORMAL")

        logger.warning(f"Datos recibidos - tipo={tipo}, titulo={titulo}")

        if not all([tipo, titulo, descripcion, categoria]):
            raise BusinessError("Faltan datos obligatorios para la publicacion.")

        if tipo not in ["TALENTO", "NECESIDAD"]:
            raise BusinessError("El tipo debe ser TALENTO o NECESIDAD.")

        if categoria not in CATEGORIAS_PUBLICACION:
            raise BusinessError("La categoria seleccionada no esta permitida.")

        if urgencia not in ["NORMAL", "ALTA", "CRITICA"]:
            raise BusinessError("La urgencia seleccionada no es valida.")

        # Usar método de negocio de Usuario para verificar si puede publicar
        conteo_actual = self.publicacion_repository.contar_activas_por_tipo(usuario.id, tipo)
        puede, mensaje = puede_publicar(usuario, tipo, conteo_actual)
        if not puede:
            raise BusinessError(mensaje)

        if contiene_palabra_prohibida(titulo) or contiene_palabra_prohibida(descripcion):
            raise BusinessError("La publicación contiene palabras no permitidas.")

        logger.warning(f"Validaciones básicas pasadas")

        conteo_actual = self.publicacion_repository.contar_activas_por_tipo(usuario.id, tipo)
        es_valido, mensaje_validacion = validar_reglas_negocio(usuario, tipo, titulo, descripcion, categoria, urgencia, True, conteo_actual, es_nueva=True)
        if not es_valido:
            logger.warning(f"Validación fallida: {mensaje_validacion}")
            raise BusinessError(mensaje_validacion)

        logger.warning(f"Validación de reglas de negocio pasada")

        publicacion = self.publicacion_repository.crear(usuario.id, {
            "tipo": tipo,
            "titulo": titulo,
            "descripcion": descripcion,
            "categoria": categoria,
            "urgencia": urgencia,
        })

        # Forzar refresh de la publicación y del usuario para asegurar que estén guardados en la base de datos
        publicacion = self.publicacion_repository.obtener_por_id(publicacion.id)
        usuario = self.usuario_repository.obtener_por_id(usuario.id)

        logger.warning(f"Publicación creada exitosamente: ID={publicacion.id}, tipo={tipo}, titulo={titulo}, usuario={usuario.id}")

        # Detección de matches (no falla si hay error)
        try:
            logger.warning(f"Iniciando detección de matches para usuario {usuario.id} después de crear publicación {publicacion.id}")
            self._disparar_deteccion_matches(usuario)
            logger.warning(f"Detección de matches completada para usuario {usuario.id}")
        except Exception as e:
            logger.exception(f"Error en detección de matches después de crear publicación para usuario {usuario.id}: {e}")

        # Detección de ciclos múltiples (no falla si hay error)
        try:
            logger.warning(f"Iniciando detección de ciclos múltiples para usuario {usuario.id} después de crear publicación {publicacion.id}")
            self._disparar_deteccion_ciclos_multiples(usuario)
            logger.warning(f"Detección de ciclos múltiples completada para usuario {usuario.id}")
        except Exception as e:
            logger.exception(f"Error en detección de ciclos múltiples después de crear publicación para usuario {usuario.id}: {e}")

        return publicacion

    def pausar_publicacion(self, usuario, publicacion_id):
        return self.actualizar_estado_publicacion(usuario, publicacion_id, esta_activa=False)

    def reactivar_publicacion(self, usuario, publicacion_id):
        return self.actualizar_estado_publicacion(usuario, publicacion_id, esta_activa=True)

    @transaction.atomic
    def actualizar_estado_publicacion(self, usuario, publicacion_id, esta_activa):
        # Usar método de negocio de Usuario para verificar si puede modificar publicaciones
        if not puede_modificar_publicaciones(usuario):
            raise BusinessError("Saldo crítico inferior a -10 horas. No puedes modificar ofertas.")

        publicacion = self.publicacion_repository.obtener_por_id_y_usuario(publicacion_id, usuario.id)
        if not publicacion:
            raise BusinessError("Publicación no encontrada.", status_code=404)

        # Usar métodos de negocio de Publicacion para validar
        if esta_activa and not publicacion.esta_activa:
            conteo_actual = self.publicacion_repository.contar_activas_por_tipo(usuario.id, publicacion.tipo)
            puede_reactivar, mensaje = puede_reactivarse(publicacion, usuario, conteo_actual)
            if not puede_reactivar:
                raise BusinessError(mensaje)
        elif not esta_activa and publicacion.esta_activa:
            puede_pausar, mensaje = puede_pausarse(publicacion)
            if not puede_pausar:
                raise BusinessError(mensaje)

        print(f"DEBUG: Attempting to update publication {publicacion_id} to esta_activa={esta_activa}")
        updated_count = self.publicacion_repository.actualizar_estado(publicacion_id, usuario.id, esta_activa)
        print(f"DEBUG: Updated publication {publicacion_id} to esta_activa={esta_activa}, rows affected: {updated_count}")
        logger.info(f"Updated publication {publicacion_id} to esta_activa={esta_activa}, rows affected: {updated_count}")
        
        # Recargar la publicación actualizada
        publicacion = self.publicacion_repository.obtener_por_id_y_usuario(publicacion_id, usuario.id)
        if esta_activa:
            # Detección de matches (no falla si hay error)
            try:
                self._disparar_deteccion_matches(usuario)
            except Exception as e:
                logger.exception(f"Error en detección de matches al reactivar publicación para usuario {usuario.id}: {e}")

            # Detección de ciclos múltiples (no falla si hay error)
            try:
                self._disparar_deteccion_ciclos_multiples(usuario)
            except Exception as e:
                logger.exception(f"Error en detección de ciclos múltiples al reactivar publicación para usuario {usuario.id}: {e}")
        return publicacion
