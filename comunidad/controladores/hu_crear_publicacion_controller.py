from comunidad.dto.request_models import CrearPublicacionRequest
from comunidad.repositorios_interfaces import IPublicacionRepository, IUsuarioRepository
from comunidad.dominio.entidades import PublicacionDominio
import logging

logger = logging.getLogger(__name__)

class CrearPublicacionController:
    """
    Controlador para la Historia de Usuario: Crear Publicación (Talento o Necesidad).
    """
    def __init__(self, publicacion_repository: IPublicacionRepository, usuario_repository: IUsuarioRepository):
        self.pub_repo = publicacion_repository
        self.usu_repo = usuario_repository

    def ejecutar(self, usuario_id: int, request_data: CrearPublicacionRequest) -> dict:
        logger.warning(f"CrearPublicacionController.ejecutar llamado para usuario {usuario_id}")

        # 1. Obtener usuario del repositorio (para validar reglas de negocio sobre el usuario)
        usuario = self.usu_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado.")

        # 2. Contar publicaciones activas actuales del mismo tipo
        conteo_actual = self.pub_repo.contar_activas_por_tipo(usuario_id, request_data.tipo)

        # 3. Construir entidad de dominio (sin BD)
        nueva_publicacion = PublicacionDominio(
            usuario_id=usuario_id,
            tipo=request_data.tipo,
            titulo=request_data.titulo,
            descripcion=request_data.descripcion,
            categoria=request_data.categoria,
            urgencia=request_data.urgencia,
            esta_activa=request_data.esta_activa
        )

        # 4. Validar reglas de negocio delegando en las entidades
        es_valido, mensaje = nueva_publicacion.validar_reglas_negocio(usuario, conteo_actual, es_nueva=True)
        if not es_valido:
            raise ValueError(mensaje)

        # 5. Guardar en persistencia
        pub_guardada = self.pub_repo.guardar(nueva_publicacion)

        logger.warning(f"Publicación guardada: ID={pub_guardada.id}, ejecutando detección de matches")

        # 6. Detección de matches (no falla si hay error)
        try:
            from comunidad.services import MatchmakingService
            from comunidad.models import Usuario
            matchmaking_service = MatchmakingService()
            # Obtener el modelo Django Usuario en lugar del UsuarioDominio
            usuario_django = Usuario.objects.get(id=usuario_id)
            matchmaking_service.detectar_y_notificar_matches(usuario_django)
            logger.warning(f"Detección de matches completada para usuario {usuario_id}")
        except Exception as e:
            logger.exception(f"Error en detección de matches después de crear publicación para usuario {usuario_id}: {e}")

        # 7. Retornar
        return {
            "id": pub_guardada.id,
            "titulo": pub_guardada.titulo,
            "tipo": pub_guardada.tipo,
            "mensaje": "Publicación creada exitosamente."
        }
